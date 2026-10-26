"""CO2 Figure13.1 thresholds, uncertain moisture and same-source composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage, properties


def wet():
    return dict(ph=dict(method="supplied",ph=5.,qualification_basis="Qualified pH fixture"),
        flow=dict(method="supplied",shear_stress_pa=19.,qualification_basis="Qualified wall shear fixture"),lookup_policy="exact_nodes_only",
        jump_policy="reject_cross_80_90",temperature_denominator_basis="printed_celsius_plus_273",
        simple_upstream_mixture_and_wetting_basis="Qualified upstream water-wetted metal fixture")


def hydrocarbon(**changes):
    return dict(liquid_hydrocarbons_present=True,water_cut_policy="explicit_qualified_percent",water_content_percent=19.,
        water_content_basis="Qualified liquid-system water-cut percent fixture",mixture_velocity_m_s=1.1,qualification_basis="Qualified figure13.1 applicability fixture")|changes


def moisture(**changes):
    return dict(temperature_k=333.15,evidence="source_missing_moisture_assume_wet",qualification_basis="Explicit source wet assumption for missing gas moisture")|changes


def request(**changes):
    return damage.Co2ScreenedAssessmentInput(**(dict(temperature_k=333.15,pressure=dict(total_pressure_pa_abs=1e6,co2_mole_fraction=.1),
        material=dict(material_category="carbon_steel",interpretation="table_resistant_alloys",qualification_basis="Qualified carbon-steel identity"),
        hydrocarbon_wetting=dict(liquid_hydrocarbons_present=False,qualification_basis="Qualified gas-service/no liquid hydrocarbon fixture"),
        moisture=moisture(),wet_model=wet(),qualification_basis="Qualified common source and screened CO2 applicability fixture")|changes))


@pytest.mark.parametrize("fraction,value",[(0.,0.),(.1,1e5),(1.,1e6)])
def test_co2_partial_pressure_absolute_fraction(fraction,value):
    r=properties.co2_partial_pressure(properties.Co2PartialPressureInput(total_pressure_pa_abs=1e6,co2_mole_fraction=fraction)).outputs
    assert r.co2_partial_pressure_pa_abs==value


def test_mass_flow_reynolds_matches_velocity_form_without_double_area_normalization():
    r=damage.co2_reynolds_mass_flow(damage.Co2ReynoldsMassFlowInput(diameter_m=.1,cross_sectional_area_m2=.01,mass_flow_kg_s=16.,mixture_viscosity_pa_s=.001)).outputs
    direct=damage.co2_reynolds(damage.Co2ReynoldsInput(diameter_m=.1,mixture_density_kg_m3=800.,mixture_velocity_m_s=2.,mixture_viscosity_pa_s=.001)).outputs
    assert r.mass_flux_kg_m2_s==1600 and r.reynolds_number==direct.reynolds_number


@pytest.mark.parametrize("category,decision",[("carbon_steel","evaluate_co2"),("low_alloy_steel","evaluate_co2"),
    ("stainless_steel","source_assumed_resistant"),("copper_alloy","source_assumed_resistant"),("other","not_covered")])
def test_named_material_table_screen(category,decision):
    r=damage.co2_material_screen(damage.Co2MaterialScreenInput(material_category=category,interpretation="table_resistant_alloys",qualification_basis="Qualified material category")).outputs
    assert r.material_screen_decision==decision


@pytest.mark.parametrize("chromium,decision",[(math.nextafter(.13,0),"evaluate_co2"),(.13,"source_assumed_resistant"),(math.nextafter(.13,1),"source_assumed_resistant")])
def test_figure_chromium_threshold_is_strict_less(chromium,decision):
    r=damage.co2_material_screen(damage.Co2MaterialScreenInput(material_category="low_alloy_steel",interpretation="figure_13cr_ferrous",chromium_mass_fraction=chromium,qualification_basis="Qualified actual chromium fixture")).outputs
    assert r.material_screen_decision==decision


def test_material_figure_not_extended_to_copper_zero_chromium_or_guessed_alloy():
    r=damage.co2_material_screen(damage.Co2MaterialScreenInput(material_category="copper_alloy",interpretation="figure_13cr_ferrous",qualification_basis="Figure applicability unresolved")).outputs
    assert r.material_screen_decision=="not_covered"
    with pytest.raises(DomainError):
        damage.co2_material_screen(damage.Co2MaterialScreenInput(material_category="low_alloy_steel",interpretation="figure_13cr_ferrous",qualification_basis="fixture"))


@pytest.mark.parametrize("water,velocity,exempt",[(19.,1.1,True),(20.,1.1,False),(19.,1.,False),(19.,math.nextafter(1.,2.),True),
    (math.nextafter(20.,0),1.1,True),(20.01,1.1,False)])
def test_hydrocarbon_water_velocity_strict_boundaries(water,velocity,exempt):
    r=damage.co2_hydrocarbon_wetting_screen(damage.Co2HydrocarbonWettingScreenInput(**hydrocarbon(water_content_percent=water,mixture_velocity_m_s=velocity))).outputs
    assert (r.wetting_screen_decision=="figure_low_water_high_velocity_exemption")==exempt


def test_default30_never_creates_immunity_and_missing_velocity_not_assumed():
    r=damage.co2_hydrocarbon_wetting_screen(damage.Co2HydrocarbonWettingScreenInput(**hydrocarbon(water_cut_policy="source_default_30_percent",water_content_percent=None,
        water_content_basis=None,mixture_velocity_m_s=None))).outputs
    assert r.water_content_percent_used==30 and r.source_water_default_used and r.wetting_screen_decision=="proceed_to_water_check"
    with pytest.raises(DomainError):
        damage.co2_hydrocarbon_wetting_screen(damage.Co2HydrocarbonWettingScreenInput(**hydrocarbon(mixture_velocity_m_s=None)))


@pytest.mark.parametrize("delta,state",[(-2.1,"present"),(-2.,"indeterminate"),(0.,"indeterminate"),(2.,"indeterminate"),(2.1,"absent")])
def test_dew_point_uncertainty_interval_does_not_assert_dry(delta,state):
    r=damage.co2_moisture_screen(damage.Co2MoistureScreenInput(**moisture(temperature_k=333.15+delta,evidence="qualified_dew_point",dew_point_temperature_k=333.15,
        dew_point_uncertainty_k=2.,equality_policy="indeterminate_at_saturation"))).outputs
    assert r.free_water_screen_state==state


@pytest.mark.parametrize("policy,state",[("figure_strict_less","absent"),("indeterminate_at_saturation","indeterminate")])
def test_exact_saturation_interpretation_explicit(policy,state):
    r=damage.co2_moisture_screen(damage.Co2MoistureScreenInput(**moisture(evidence="qualified_dew_point",dew_point_temperature_k=333.15,
        dew_point_uncertainty_k=0.,equality_policy=policy))).outputs
    assert r.free_water_screen_state==state


def test_qualified_present_absent_and_missing_wet_default_differ():
    for evidence,state,assumed in [("qualified_free_water_present","present",False),("qualified_no_free_water","absent",False),
        ("source_missing_moisture_assume_wet","present",True)]:
        r=damage.co2_moisture_screen(damage.Co2MoistureScreenInput(**moisture(evidence=evidence))).outputs
        assert r.free_water_screen_state==state and r.free_water_assumed_from_missing_data==assumed
    with pytest.raises(DomainError):
        damage.co2_moisture_screen(damage.Co2MoistureScreenInput(**moisture(evidence="qualified_dew_point",dew_point_temperature_k=333.15)))


def test_screened_wet_assessment_matches_prior_independent_kernel_and_preserves_default():
    r=damage.co2_screened_assessment(request()).outputs
    direct=damage.co2_corrosion_assessment(damage.Co2CorrosionAssessmentInput(material="carbon_steel",temperature_k=333.15,co2_partial_pressure_pa_abs=1e5,
        free_liquid_water_present=True,applicability_basis="same fixture",wet_model=wet())).outputs
    assert r.corrosion_rate_m_year==direct.corrosion_rate_m_year
    assert r.screened_calculation_branch=="wet_carbonic_acid_model" and r.free_water_assumed_from_missing_data
    assert r.co2_partial_pressure_pa_abs==1e5


def test_screened_material_and_hydrocarbon_exemptions_leave_uncomputed_diagnostics_null():
    material=dict(material_category="stainless_steel",interpretation="table_resistant_alloys",qualification_basis="Qualified source material assumption")
    r=damage.co2_screened_assessment(request(material=material,hydrocarbon_wetting=None,moisture=None,wet_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.source_material_resistance_assumed and r.free_water_screen_state is None
    r=damage.co2_screened_assessment(request(hydrocarbon_wetting=hydrocarbon(),moisture=None,wet_model=None)).outputs
    assert r.screened_calculation_branch=="figure_hydrocarbon_exemption" and r.corrosion_rate_m_year==0 and r.model_ph is None


def test_no_co2_or_qualified_dry_water_branches():
    r=damage.co2_screened_assessment(request(pressure=dict(total_pressure_pa_abs=1e6,co2_mole_fraction=0.),hydrocarbon_wetting=None,moisture=None,wet_model=None)).outputs
    assert r.screened_calculation_branch=="no_co2" and r.corrosion_rate_m_year==0
    r=damage.co2_screened_assessment(request(moisture=moisture(evidence="qualified_no_free_water"),wet_model=None)).outputs
    assert r.screened_calculation_branch=="qualified_no_free_water" and not r.free_water_assumed_from_missing_data


def test_unresolved_moisture_never_returns_zero_and_low_cr_stainless_not_reclassified():
    unresolved=moisture(evidence="qualified_dew_point",dew_point_temperature_k=333.15,dew_point_uncertainty_k=5.,equality_policy="indeterminate_at_saturation")
    with pytest.raises(DomainError) as error:
        damage.co2_screened_assessment(request(moisture=unresolved))
    assert error.value.code=="co2_moisture_indeterminate"
    with pytest.raises(DomainError):
        damage.co2_screened_assessment(request(material=dict(material_category="stainless_steel",interpretation="figure_13cr_ferrous",chromium_mass_fraction=.12,qualification_basis="Qualified low-Cr stainless identity")))


@pytest.mark.parametrize("changes",[dict(qualification_basis=" "),dict(hydrocarbon_wetting=None),dict(moisture=None),
    dict(moisture=moisture(temperature_k=334.15)),dict(wet_model=None),
    dict(hydrocarbon_wetting=hydrocarbon()),dict(material=dict(material_category="other",interpretation="table_resistant_alloys",qualification_basis="unknown"))])
def test_source_scope_and_unused_input_gates(changes):
    with pytest.raises(DomainError):
        damage.co2_screened_assessment(request(**changes))


def test_turbulent_screen_and_model_velocity_must_agree():
    model=wet()|dict(flow=dict(method="turbulent_flow",diameter_m=.1,mixture_density_kg_m3=800.,mixture_velocity_m_s=2.,mixture_viscosity_pa_s=.001,
        relative_roughness=.0001,qualification_basis="Qualified effective turbulent properties"))
    with pytest.raises(DomainError):
        damage.co2_screened_assessment(request(hydrocarbon_wetting=hydrocarbon(water_content_percent=30.,mixture_velocity_m_s=3.),wet_model=model))


def test_screened_rate_to_thinning_keeps_specific_zero_separate_from_df_floor():
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.02,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    r=damage.co2_screened_thinning(damage.Co2ScreenedThinningInput(corrosion=request(moisture=moisture(evidence="qualified_no_free_water"),wet_model=None),
        starting_thickness_m=.02,elapsed_years=1.,strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,qualification_basis="Qualified common baseline")).outputs
    assert r.corrosion_rate_m_year==0 and r.wall_loss_fraction==0 and r.thinning_damage_factor >= .1
    assert r.screened_calculation_branch=="qualified_no_free_water"


@pytest.mark.parametrize("fraction",[-.01,1.01,True,float("nan")])
def test_fraction_numeric_contract(fraction):
    with pytest.raises(ValidationError):
        properties.Co2PartialPressureInput(total_pressure_pa_abs=1e6,co2_mole_fraction=fraction)
