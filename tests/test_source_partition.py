"""Pressure boundaries, source branches, explicit entrainment bases, mass closure."""
import math
import pytest
from api581 import DomainError
from api581.api import release


@pytest.mark.parametrize("ps,pv,phase,status",[(1e6,2e6,"vapor","classified"),(1e6,5e5,"two_phase","classified"),
    (1e6,5e4,"liquid","classified"),(1e6,1e6,None,"saturation_storage_boundary"),
    (1e6,1e5,None,"saturation_ambient_boundary"),(1e5,5e4,None,"no_driving_pressure")])
def test_printed_phase_pressure_conditions_and_boundaries(ps,pv,phase,status):
    r=release.level2_release_phase(release.Level2ReleasePhaseInput(storage_pressure_pa_abs=ps,
        saturation_pressure_at_storage_pa_abs=pv,ambient_pressure_pa_abs=1e5)).outputs
    assert r.release_phase == phase and r.status == status


def test_storage_pressure_below_ambient_rejected():
    with pytest.raises(DomainError):
        release.level2_release_phase(release.Level2ReleasePhaseInput(storage_pressure_pa_abs=1e4,saturation_pressure_at_storage_pa_abs=5e3))


def orifice(**updates):
    return release.Level2OrificeRateInput(**(dict(diameter_m=.0254,storage_pressure_pa_abs=1e6,
        saturation_pressure_at_storage_pa_abs=5e5,ambient_pressure_pa_abs=1e5,liquid_density_kg_m3=700)|updates))


@pytest.mark.parametrize("pv,phase,method",[(5e4,"liquid","liquid"),(5e5,"two_phase","liquid_conservative_two_phase")])
def test_liquid_and_source_permitted_conservative_two_phase_match_existing_liquid_equation(pv,phase,method):
    r=release.level2_orifice_rate(orifice(saturation_pressure_at_storage_pa_abs=pv)).outputs
    old=release.liquid(release.LiquidInput(diameter_m=.0254,upstream_pressure_pa_abs=1e6,
        downstream_pressure_pa_abs=1e5,density_kg_m3=700)).outputs
    assert r.release_phase == phase and r.rate_method == method
    assert r.mass_rate_kg_s == old.mass_rate_kg_s
    assert r.mass_rate_kg_s == pytest.approx(.61*math.pi*.0254**2/4*math.sqrt(2*700*9e5))


def test_vapor_selection_matches_existing_ideal_gas_source():
    r=release.level2_orifice_rate(orifice(saturation_pressure_at_storage_pa_abs=2e6,
        gas_temperature_k=300,gas_molecular_weight_kg_kmol=44,gas_heat_capacity_ratio=1.15)).outputs
    old=release.gas(release.GasInput(diameter_m=.0254,upstream_pressure_pa_abs=1e6,
        downstream_pressure_pa_abs=1e5,temperature_k=300,molecular_weight_kg_kmol=44,heat_capacity_ratio=1.15)).outputs
    assert r.release_phase == "vapor" and r.rate_method == "ideal_gas"
    assert r.mass_rate_kg_s == old.mass_rate_kg_s


def test_boundary_requires_qualified_override_and_keeps_basis():
    with pytest.raises(DomainError) as exc:
        release.level2_orifice_rate(orifice(saturation_pressure_at_storage_pa_abs=1e6))
    assert exc.value.code == "phase_boundary_requires_qualification"
    r=release.level2_orifice_rate(orifice(saturation_pressure_at_storage_pa_abs=1e6,
        qualified_boundary_phase="two_phase",boundary_phase_source="Owner-qualified saturated-liquid boundary fixture")).outputs
    assert r.phase_basis == "qualified_boundary" and r.release_phase == "two_phase"


@pytest.mark.parametrize("updates",[{"qualified_boundary_phase":"liquid"},
    {"qualified_boundary_phase":"liquid","boundary_phase_source":" "},
    {"qualified_boundary_phase":"vapor","boundary_phase_source":"Cannot override classified two-phase"},
    {"liquid_density_kg_m3":None}])
def test_inconsistent_phase_override_or_missing_properties_rejected(updates):
    with pytest.raises(DomainError):
        release.level2_orifice_rate(orifice(**updates))


def test_zero_driving_pressure_returns_zero_and_no_invented_phase():
    r=release.level2_orifice_rate(orifice(storage_pressure_pa_abs=1e5)).outputs
    assert r.mass_rate_kg_s == 0 and r.release_phase is None
    assert r.rate_method == "no_driving_pressure"


@pytest.mark.parametrize("flash,expected",[(0,1),(.1,.8),(.25,.5),(.499,.002),(.5,0),(.75,0),(1,0)])
def test_kletz_source_anchors_and_branch(flash,expected):
    r=release.kletz_rainout_fraction(release.KletzRainoutFractionInput(flash_mass_fraction=flash)).outputs
    assert r.rainout_mass_fraction == pytest.approx(expected,abs=1e-15)


@pytest.mark.parametrize("rainout",[0,.2,.5,1])
def test_pool_and_aerosol_jet_rate_closure(rainout):
    r=release.rainout_rate_split(release.RainoutRateSplitInput(adjusted_mass_rate_kg_s=100,rainout_mass_fraction=rainout)).outputs
    assert r.pool_liquid_rate_kg_s == pytest.approx(100*rainout)
    assert r.pool_liquid_rate_kg_s+r.jet_total_rate_kg_s == pytest.approx(100)


def test_printed_product_and_mass_balance_are_explicitly_distinct():
    printed=release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(rainout_mass_fraction=0,
        equation_basis="api581_printed",stored_liquid_mass_fraction=1,flash_mass_fraction=.8))
    balanced=release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(rainout_mass_fraction=0,
        equation_basis="post_flash_mass_balance",post_flash_vapor_mass_fraction=.8))
    assert printed.outputs.entrained_liquid_mass_fraction == .8
    assert balanced.outputs.entrained_liquid_mass_fraction == pytest.approx(.2)
    assert printed.input_hash != balanced.input_hash


def test_unphysical_printed_fraction_is_diagnostic_but_cannot_define_source():
    values=dict(rainout_mass_fraction=.8,equation_basis="api581_printed",stored_liquid_mass_fraction=1,flash_mass_fraction=.8)
    r=release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(**values)).outputs
    assert r.entrained_liquid_mass_fraction == pytest.approx(4)
    assert not r.physical_range and r.jet_vapor_mass_fraction is None
    with pytest.raises(DomainError) as exc:
        release.level2_source_partition(release.Level2SourcePartitionInput(**values,adjusted_mass_rate_kg_s=10,released_mass_kg=100,
            rainout_basis_source="Explicit diagnostic fixture",flash_property_source="Not a physical EOS fixture"))
    assert exc.value.code == "invalid_entrainment_fraction"


def test_inconsistent_post_flash_mass_and_mixed_basis_fields_rejected():
    with pytest.raises(DomainError):
        release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(rainout_mass_fraction=.6,
            equation_basis="post_flash_mass_balance",post_flash_vapor_mass_fraction=.5))
    with pytest.raises(DomainError):
        release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(rainout_mass_fraction=.5,
            equation_basis="post_flash_mass_balance",post_flash_vapor_mass_fraction=.25,flash_mass_fraction=.25))


def partition(**updates):
    return release.Level2SourcePartitionInput(**(dict(rainout_mass_fraction=.5,equation_basis="post_flash_mass_balance",
        post_flash_vapor_mass_fraction=.25,adjusted_mass_rate_kg_s=10,released_mass_kg=100,
        rainout_basis_source="Kletz demonstration",flash_property_source="Qualified demonstration post-flash vapor fraction")|updates))


def test_source_rate_and_mass_closure_including_aerosol():
    r=release.level2_source_partition(partition()).outputs
    assert r.pool_liquid_rate_kg_s == r.jet_total_rate_kg_s == 5
    assert r.jet_liquid_rate_kg_s == r.jet_vapor_rate_kg_s == 2.5
    assert r.pool_liquid_mass_kg == r.jet_total_mass_kg == 50
    assert r.jet_liquid_mass_kg == r.jet_vapor_mass_kg == 25
    assert r.pool_liquid_mass_kg+r.jet_liquid_mass_kg+r.jet_vapor_mass_kg == 100
    assert r.jet_vapor_mass_fraction == r.entrained_liquid_mass_fraction == .5


def test_all_pool_has_no_defined_jet_composition():
    r=release.level2_source_partition(partition(rainout_mass_fraction=1,post_flash_vapor_mass_fraction=0)).outputs
    assert r.pool_liquid_rate_kg_s == 10 and r.pool_liquid_mass_kg == 100
    assert r.jet_total_rate_kg_s == r.jet_liquid_rate_kg_s == r.jet_vapor_rate_kg_s == 0
    assert not r.jet_fraction_nonzero and r.jet_vapor_mass_fraction is r.entrained_liquid_mass_fraction is None
    with pytest.raises(DomainError):
        release.level2_source_partition(partition(rainout_mass_fraction=1,post_flash_vapor_mass_fraction=1e-300))


def test_all_vapor_and_zero_total_source_limits():
    vapor=release.level2_source_partition(partition(rainout_mass_fraction=0,post_flash_vapor_mass_fraction=1)).outputs
    assert vapor.jet_vapor_rate_kg_s == 10 and vapor.jet_liquid_rate_kg_s == vapor.pool_liquid_rate_kg_s == 0
    zero=release.level2_source_partition(partition(adjusted_mass_rate_kg_s=0,released_mass_kg=0)).outputs
    assert zero.pool_liquid_rate_kg_s == zero.jet_total_rate_kg_s == zero.jet_total_mass_kg == 0


def test_mass_boundary_roundoff_and_required_provenance():
    r=release.jet_liquid_entrainment(release.JetLiquidEntrainmentInput(rainout_mass_fraction=.9,
        equation_basis="post_flash_mass_balance",post_flash_vapor_mass_fraction=.1)).outputs
    assert r.jet_vapor_mass_fraction == 1 and r.entrained_liquid_mass_fraction == 0
    with pytest.raises(DomainError):
        release.level2_source_partition(partition(rainout_basis_source=" "))
