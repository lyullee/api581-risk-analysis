"""Pressure units, kmol amount, independent energy arithmetic and NFNT weighting."""
import math
from decimal import Decimal, localcontext
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import effects, release, consequence


def fit():
    return effects.BlastFitDomainInput(minimum_scaled_distance_m_kg13=1.5,maximum_scaled_distance_m_kg13=1000,
        engineering_basis="Illustrative numerical interval, not experimental validity")


def test_physical_tnt_matches_decimal_source_in_kpa():
    result=effects.physical_explosion_tnt(effects.PhysicalExplosionTntInput(
        vapor_volume_m3=10,burst_pressure_pa_abs=1e7,ambient_pressure_pa_abs=101325,heat_capacity_ratio=1.4)).outputs
    with localcontext() as ctx:
        ctx.prec=60
        source=Decimal('4.303e-4')*Decimal(10)*(Decimal(10000)-Decimal('101.325'))/Decimal('.4')
    assert result.tnt_equivalent_mass_kg == pytest.approx(float(source),rel=1e-14)
    assert result.vapor_stored_energy_j == pytest.approx(10*(1e7-101325)/.4)
    assert result.tnt_equivalent_mass_kg == pytest.approx(result.vapor_stored_energy_j*4.303e-7)


def test_bleve_expansion_matches_high_precision_kmol_and_natural_log():
    result=effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=100,
        storage_temperature_k=400,burst_pressure_pa_abs=2e6,ambient_pressure_pa_abs=1e5)).outputs
    with localcontext() as ctx:
        ctx.prec=60
        energy=Decimal(100)*Decimal(8314)*Decimal(400)*Decimal(20).ln()
        tnt=Decimal('9.76e-8')*energy
    assert result.liquid_expansion_energy_j == pytest.approx(float(energy),rel=1e-14)
    assert result.tnt_equivalent_mass_kg == pytest.approx(float(tnt),rel=1e-14)


def test_flashed_amount_uses_liquid_fraction_and_kg_per_kmol():
    result=release.bleve_flashed_amount(release.BleveFlashedAmountInput(stored_liquid_mass_kg=1000,
        liquid_flash_mass_fraction=.2,molecular_weight_kg_kmol=20)).outputs
    assert result.flashed_liquid_mass_kg == 200
    assert result.flashed_amount_kmol == 10


@pytest.mark.parametrize("mass,fraction",[(0,.2),(1000,0)])
def test_zero_flashed_amount_is_allowed(mass,fraction):
    result=release.bleve_flashed_amount(release.BleveFlashedAmountInput(stored_liquid_mass_kg=mass,
        liquid_flash_mass_fraction=fraction,molecular_weight_kg_kmol=20)).outputs
    assert result.flashed_amount_kmol == result.flashed_liquid_mass_kg == 0


@pytest.mark.parametrize("gamma",[1,.9,0])
def test_heat_capacity_ratio_requires_strictly_above_one(gamma):
    with pytest.raises(ValidationError):
        effects.PhysicalExplosionTntInput(vapor_volume_m3=1,burst_pressure_pa_abs=1e6,heat_capacity_ratio=gamma)


def test_pressure_below_ambient_is_rejected_by_both_energy_models():
    with pytest.raises(DomainError):
        effects.physical_explosion_tnt(effects.PhysicalExplosionTntInput(vapor_volume_m3=1,
            burst_pressure_pa_abs=1e5,ambient_pressure_pa_abs=2e5,heat_capacity_ratio=1.4))
    with pytest.raises(DomainError):
        effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=1,
            storage_temperature_k=400,burst_pressure_pa_abs=1e5,ambient_pressure_pa_abs=2e5))


def test_zero_overpressure_releases_no_expansion_energy():
    a=effects.physical_explosion_tnt(effects.PhysicalExplosionTntInput(vapor_volume_m3=10,
        burst_pressure_pa_abs=1e5,ambient_pressure_pa_abs=1e5,heat_capacity_ratio=1.4)).outputs
    b=effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=100,storage_temperature_k=400,
        burst_pressure_pa_abs=1e5,ambient_pressure_pa_abs=1e5)).outputs
    assert a.tnt_equivalent_mass_kg == b.tnt_equivalent_mass_kg == 0


def test_tiny_overpressure_log1p_retains_expansion_energy():
    ambient=1e5
    pressure=math.nextafter(ambient,math.inf)
    result=effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=1,
        storage_temperature_k=400,burst_pressure_pa_abs=pressure,ambient_pressure_pa_abs=ambient)).outputs
    expected=8314*400*math.log1p((pressure-ambient)/ambient)
    assert result.liquid_expansion_energy_j > 0
    assert result.liquid_expansion_energy_j == expected


def test_pressure_ratio_overflow_is_avoided():
    result=effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=1,
        storage_temperature_k=400,burst_pressure_pa_abs=1e300,ambient_pressure_pa_abs=1e-100)).outputs
    assert result.liquid_expansion_energy_j == pytest.approx(8314*400*400*math.log(10))


def physical_request(**updates):
    values=dict(hole="rupture",fit_domain=fit(),vapor_volume_m3=10,heat_capacity_ratio=1.4,
        burst_pressure_pa_abs=2e6,ambient_pressure_pa_abs=1e5)
    return effects.PhysicalExplosionConsequenceInput(**(values|updates))


def bleve_request(**updates):
    values=dict(hole="rupture",fit_domain=fit(),flashed_amount_kmol=100,storage_temperature_k=400,
        burst_pressure_pa_abs=2e6,ambient_pressure_pa_abs=1e5,
        stored_vapor=effects.VaporPortionInput(vapor_volume_m3=10,heat_capacity_ratio=1.4))
    return effects.BleveConsequenceInput(**(values|updates))


def test_physical_consequence_reconstructs_tnt_and_distance_primitives():
    result=effects.physical_explosion_consequence(physical_request()).outputs
    energy=effects.physical_explosion_tnt(effects.PhysicalExplosionTntInput(vapor_volume_m3=10,
        heat_capacity_ratio=1.4,burst_pressure_pa_abs=2e6,ambient_pressure_pa_abs=1e5)).outputs
    assert result.potential_tnt_equivalent_mass_kg == energy.tnt_equivalent_mass_kg
    assert result.event_tnt_equivalent_mass_kg == energy.tnt_equivalent_mass_kg
    assert result.personnel_building_collapse_probability == .5
    assert result.personnel_threshold_overpressure_pa == pytest.approx(math.exp(28.8/2.92))
    for label,threshold in [("personnel",result.personnel_threshold_overpressure_pa),("equipment",34500)]:
        area=effects.vce_blast_distance(effects.VceBlastDistanceInput(tnt_equivalent_mass_kg=energy.tnt_equivalent_mass_kg,
            fit_domain=fit(),threshold_overpressure_pa=threshold)).outputs
        assert getattr(result,label+"_area_m2") == area.consequence_area_m2
        assert getattr(result,label+"_safe_distance_m") == area.safe_distance_m


def test_two_phase_bleve_adds_vapor_and_liquid_tnt_not_areas_or_uniform_energy_coefficient():
    combined=effects.bleve_consequence(bleve_request()).outputs
    liquid=effects.bleve_consequence(bleve_request(stored_vapor=None)).outputs
    vapor=effects.physical_explosion_consequence(physical_request()).outputs
    assert combined.liquid_tnt_equivalent_mass_kg == liquid.potential_tnt_equivalent_mass_kg
    assert combined.vapor_tnt_equivalent_mass_kg == vapor.potential_tnt_equivalent_mass_kg
    assert combined.potential_tnt_equivalent_mass_kg == liquid.potential_tnt_equivalent_mass_kg+vapor.potential_tnt_equivalent_mass_kg
    ratio=combined.potential_tnt_equivalent_mass_kg/liquid.potential_tnt_equivalent_mass_kg
    assert combined.personnel_area_m2 == pytest.approx(liquid.personnel_area_m2*ratio**(2/3),rel=1e-6)


@pytest.mark.parametrize("hole",["small","medium","large"])
def test_only_rupture_produces_physical_or_bleve_area(hole):
    for result in [effects.physical_explosion_consequence(physical_request(hole=hole)).outputs,
                   effects.bleve_consequence(bleve_request(hole=hole)).outputs]:
        assert result.potential_tnt_equivalent_mass_kg > 0
        assert result.event_tnt_equivalent_mass_kg == 0
        assert result.personnel_area_m2 == result.equipment_area_m2 == 0
        assert result.personnel_status == result.equipment_status == "not_rupture"


def test_zero_energy_rupture_is_distinct_from_non_rupture():
    a=effects.physical_explosion_consequence(physical_request(vapor_volume_m3=0)).outputs
    b=effects.bleve_consequence(bleve_request(flashed_amount_kmol=0,stored_vapor=None)).outputs
    assert a.personnel_status == b.personnel_status == "no_explosion"
    assert a.event_tnt_equivalent_mass_kg == b.event_tnt_equivalent_mass_kg == 0


def test_vapor_only_bleve_composition_retains_vapor_energy():
    result=effects.bleve_consequence(bleve_request(flashed_amount_kmol=0)).outputs
    assert result.liquid_tnt_equivalent_mass_kg == 0
    assert result.event_tnt_equivalent_mass_kg == result.vapor_tnt_equivalent_mass_kg > 0


def test_nfnt_case_takes_max_then_non_ignition_weight_once():
    result=consequence.level2_nfnt_case(consequence.Level2NfntCaseInput(hole="rupture",non_ignition_probability=.6,
        physical_equipment_area_m2=100,physical_personnel_area_m2=300,bleve_equipment_area_m2=200,
        bleve_personnel_area_m2=400,steam_chemical_personnel_area_m2=500)).outputs
    assert result.equipment_area_m2 == 120
    assert result.personnel_area_m2 == 300


def test_nfnt_rejects_explosion_area_outside_rupture():
    with pytest.raises(DomainError):
        consequence.level2_nfnt_case(consequence.Level2NfntCaseInput(hole="small",non_ignition_probability=0,
            physical_equipment_area_m2=1))


def frequency_cases():
    cases=[]
    for i,hole in enumerate(["small","medium","large","rupture"],start=1):
        values=dict(hole=hole,non_ignition_probability=.5,generic_frequency_per_year=i,steam_chemical_personnel_area_m2=i*10)
        if hole == "rupture":
            values.update(physical_equipment_area_m2=100,physical_personnel_area_m2=80,
                bleve_equipment_area_m2=120,bleve_personnel_area_m2=90)
        cases.append(consequence.NfntFrequencyCaseInput(**values))
    return cases


def test_nfnt_four_hole_probability_and_gff_average():
    result=consequence.level2_nfnt_summary(consequence.Level2NfntSummaryInput(cases=frequency_cases())).outputs
    assert result.total_generic_frequency_per_year == 10
    assert result.equipment_area_m2 == 24
    assert result.personnel_area_m2 == 25
    assert result.by_hole_personnel_area_m2 == dict(small=5,medium=10,large=15,rupture=45)
    # Uniform frequency multiplication leaves average areas unchanged.
    doubled=[c.model_copy(update={"generic_frequency_per_year":2*c.generic_frequency_per_year}) for c in frequency_cases()]
    assert consequence.level2_nfnt_summary(consequence.Level2NfntSummaryInput(cases=doubled)).outputs.personnel_area_m2 == 25


def test_nfnt_requires_all_four_holes_and_positive_total_frequency():
    cases=frequency_cases()
    with pytest.raises(ValidationError):
        consequence.Level2NfntSummaryInput(cases=cases[:3])
    with pytest.raises(DomainError):
        consequence.level2_nfnt_summary(consequence.Level2NfntSummaryInput(cases=[cases[0],cases[0],cases[2],cases[3]]))
    with pytest.raises(DomainError):
        consequence.level2_nfnt_summary(consequence.Level2NfntSummaryInput(cases=[c.model_copy(update={"generic_frequency_per_year":0}) for c in cases]))


@pytest.mark.parametrize("which",["physical","bleve","amount"])
def test_energy_and_amount_underflow_are_not_silently_zero(which):
    with pytest.raises(DomainError) as exc:
        if which == "physical":
            effects.physical_explosion_tnt(effects.PhysicalExplosionTntInput(vapor_volume_m3=1e-320,
                burst_pressure_pa_abs=2e-300,ambient_pressure_pa_abs=1e-300,heat_capacity_ratio=1.4))
        elif which == "bleve":
            effects.bleve_liquid_tnt(effects.BleveLiquidTntInput(flashed_amount_kmol=1e-320,storage_temperature_k=1e-300,
                burst_pressure_pa_abs=2e5,ambient_pressure_pa_abs=1e5))
        else:
            release.bleve_flashed_amount(release.BleveFlashedAmountInput(stored_liquid_mass_kg=1e-300,
                liquid_flash_mass_fraction=1e-300,molecular_weight_kg_kmol=20))
    assert exc.value.code == "numerical_failure"
