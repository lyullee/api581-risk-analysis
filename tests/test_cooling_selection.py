"""Figure11.1 measured priority, treated strict bounds and nominal alloy branch."""
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def treated(**changes):
    return dict(material="carbon_steel",system="open_recirculating",qualified_effective_treatment_program=True,actual_ph=8.,
        effective_microbiological_control=True,no_deposits_or_local_low_flow=True,qualification_basis="Qualified effective treatment and water-system scope fixture")|changes


def measurement(**changes):
    return dict(measurement_type="component_local",measured_rate_m_year=.0001,representative_for_assessed_component=True,
        representativeness_basis="Qualified same-component/local-damage rate fixture")|changes


def screening(**changes):
    return dict(kind="treated",treatment=treated(),rate_policy="screen_at_strict_upper_bound",rate_selection_basis="Qualified conservative strict-bound screening fixture")|changes


def select(**changes):
    return damage.CoolingWaterRateSelectionInput(**(dict(material="carbon_steel",assessment_distribution="local",selection_basis="Qualified rate source and local coverage fixture",
        fallback=screening())|changes))


@pytest.mark.parametrize("system",["open_recirculating","closed_recirculating"])
def test_treated_source_bounds_not_point_rates(system):
    r=damage.cooling_water_treatment_bounds(damage.CoolingWaterTreatmentBoundsInput(**treated(system=system))).outputs
    assert r.general_upper_bound_m_year==3*.0000254 and r.pitting_upper_bound_m_year==15*.0000254
    assert r.source_rate_relation=="strictly_less_than"


@pytest.mark.parametrize("changes",[dict(qualified_effective_treatment_program=False),dict(effective_microbiological_control=False),
    dict(no_deposits_or_local_low_flow=False),dict(qualification_basis=" "),dict(once_through_interpretation="qualified_figure_treatment")])
def test_treatment_qualification_gates(changes):
    with pytest.raises(DomainError):
        damage.cooling_water_treatment_bounds(damage.CoolingWaterTreatmentBoundsInput(**treated(**changes)))


def test_once_through_text_figure_conflict_requires_explicit_basis():
    for interpretation in [None,"body_untreated_only"]:
        with pytest.raises(DomainError) as error:
            damage.cooling_water_treatment_bounds(damage.CoolingWaterTreatmentBoundsInput(**treated(system="once_through_fresh",once_through_interpretation=interpretation)))
        assert error.value.code=="ambiguous_source"
    r=damage.cooling_water_treatment_bounds(damage.CoolingWaterTreatmentBoundsInput(**treated(system="once_through_fresh",once_through_interpretation="qualified_figure_treatment"))).outputs
    assert r.general_upper_bound_m_year==3*.0000254


def test_half_mpy_is_other_material_nominal_branch():
    r=damage.cooling_water_other_material_estimate(damage.CoolingWaterOtherMaterialEstimateInput(material="other_material",
        qualified_for_resistant_material_nominal_estimate=True,other_degradation_assessed=True,applicability_basis="Qualified alloy nominal applicability and separate SCC/dealloying review")).outputs
    assert r.nominal_corrosion_rate_m_year==.5*.0000254
    with pytest.raises(DomainError):
        damage.cooling_water_other_material_estimate(damage.CoolingWaterOtherMaterialEstimateInput(material="other_material",
            qualified_for_resistant_material_nominal_estimate=True,other_degradation_assessed=False,applicability_basis="fixture"))


@pytest.mark.parametrize("distribution,kind,multiplier,value,source",[("local","component_local",None,.0001,"component_measurement"),
    ("general","component_general",None,.0001,"component_measurement"),("general","coupon_weight_loss_general",None,.0001,"coupon_general"),
    ("local","coupon_weight_loss_general",7.,.0007,"coupon_pitting_rule")])
def test_independent_measured_rate_distribution_and_coupon_rule(distribution,kind,multiplier,value,source):
    r=damage.cooling_water_measured_rate(damage.CoolingWaterMeasuredRateInput(assessment_distribution=distribution,
        measurement=measurement(measurement_type=kind,pitting_multiplier=multiplier))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(value) and r.selection_source==source


@pytest.mark.parametrize("changes",[dict(measurement_type="component_general"),dict(pitting_multiplier=5.),
    dict(measurement_type="coupon_weight_loss_general"),dict(representative_for_assessed_component=False),dict(representativeness_basis=" ")])
def test_measured_mismatch_or_missing_qualification_not_silently_used(changes):
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(measurement=measurement(**changes)))


def test_measurement_priority_zero_not_missing_and_fallback_not_executed():
    # Fallback request is structurally valid but outside model velocity domain; it must not execute.
    fallback=dict(kind="seawater_model",model=dict(material="carbon_steel",velocity_m_s=100.,equation_basis="printed_si",applicability_basis="not used"))
    r=damage.cooling_water_rate_selection(select(measurement=measurement(measured_rate_m_year=0.),fallback=fallback)).outputs
    assert r.corrosion_rate_m_year==0 and r.selection_source=="component_measurement" and r.fallback_ignored_due_to_measurement
    assert r.source_strict_upper_bound_m_year is None and not r.selected_rate_is_screening_bound
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(fallback=fallback))


@pytest.mark.parametrize("distribution,bound",[("general",3*.0000254),("local",15*.0000254)])
def test_screening_at_bound_explicit_not_exact_prediction(distribution,bound):
    r=damage.cooling_water_rate_selection(select(assessment_distribution=distribution)).outputs
    assert r.corrosion_rate_m_year==r.source_strict_upper_bound_m_year==bound
    assert r.selected_rate_is_screening_bound and r.selection_source=="treated_screening_bound"
    owner=damage.cooling_water_rate_selection(select(assessment_distribution=distribution,fallback=screening(rate_policy="qualified_rate_below_bound",owner_rate_m_year=bound/2))).outputs
    assert owner.corrosion_rate_m_year==bound/2 and not owner.selected_rate_is_screening_bound
    assert owner.selection_source=="treated_owner_rate"


@pytest.mark.parametrize("changes",[dict(rate_policy="qualified_rate_below_bound",owner_rate_m_year=15*.0000254),
    dict(rate_policy="qualified_rate_below_bound",owner_rate_m_year=.001),dict(rate_policy="qualified_rate_below_bound"),
    dict(owner_rate_m_year=.0001),dict(rate_selection_basis=" ")])
def test_strict_bound_and_inconsistent_owner_point(changes):
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(fallback=screening(**changes)))


def test_no_source_material_mismatch_and_other_material_path():
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(fallback=None))
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(material="low_alloy_steel"))
    choice=dict(kind="other_material_nominal",model=dict(material="other_material",qualified_for_resistant_material_nominal_estimate=True,
        other_degradation_assessed=True,applicability_basis="Qualified non-carbon/low-alloy nominal estimate"))
    r=damage.cooling_water_rate_selection(select(material="other_material",fallback=choice)).outputs
    assert r.corrosion_rate_m_year==.5*.0000254 and r.selection_source=="other_material_nominal"
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(fallback=choice))


def test_fresh_and_seawater_model_fallbacks_match_independent_kernels():
    sea=dict(material="carbon_steel",velocity_m_s=1.,equation_basis="printed_si",applicability_basis="Qualified seawater fixture")
    r=damage.cooling_water_rate_selection(select(fallback=dict(kind="seawater_model",model=sea))).outputs
    assert r.corrosion_rate_m_year==damage.cooling_water_seawater_rate(damage.CoolingWaterSeawaterRateInput(**sea)).outputs.corrosion_rate_m_year
    water=dict(material="carbon_steel",applicability_basis="Qualified water fixture",actual_ph=8.,saturation_ph=7.,saturation_ph_basis="Qualified measured pHs",
        chloride_ppm=100.,velocity_m_s=1.5,system="open_recirculating",effective_microbiological_control=True,no_deposits_or_local_low_flow=True,
        no_corrosion_inhibitor_model_credit=True,condition_interpretation="body_rsi6_velocity2_44",rate_unit_basis="printed_si",velocity_equation_basis="printed_si",
        temperature=dict(metal_temperature_k=333.15,system="open",temperature_basis="printed_si",argument_policy="table_operating_temperature",
            duplicate_row_policy="reject_unresolved_row",lookup_policy="exact_rows_only"),chloride_lookup_policy="exact_rows_only")
    r=damage.cooling_water_rate_selection(select(fallback=dict(kind="freshwater_model",model=water))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00011)


def test_selected_screening_rate_to_thinning_matches_independent_api_and_keeps_bound_flag():
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    r=damage.cooling_water_selected_thinning(damage.CoolingWaterSelectedThinningInput(selection=select(),starting_thickness_m=.01,elapsed_years=5.,
        strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,qualification_basis="Qualified bound screening and local inspection fixture")).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",
        wall=dict(starting_thickness_m=.01,elapsed_years=5.,corrosion_rate_m_year=15*.0000254),strength=strength,
        inspections=dict(confidence="high",inspections_a=1),conditions=conditions)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor and r.selected_rate_is_screening_bound
    assert r.wall_loss_fraction==pytest.approx(.1905)


@pytest.mark.parametrize("value",[4.9,10.1,0.,float("nan"),True])
def test_multiplier_and_type_validation(value):
    with pytest.raises(ValidationError):
        damage.CoolingWaterMeasuredRateInput(assessment_distribution="local",measurement=measurement(measurement_type="coupon_weight_loss_general",pitting_multiplier=value))


def test_pH_source_scope_validation_and_blank_selection_basis():
    with pytest.raises(ValidationError):
        damage.CoolingWaterTreatmentBoundsInput(**treated(actual_ph=6.))
    with pytest.raises(DomainError):
        damage.cooling_water_rate_selection(select(selection_basis=" "))


def test_cooling_system_type_validates_annex_definitions():
    closed = damage.cooling_water_system_type(damage.CoolingWaterSystemTypeInput(
        system="closed_recirculated", water_source="fresh", reuses_heated_water=True,
        continual_makeup_required=False, blowdown_or_evaporation_loss=False,
        qualification_basis="Closed loop operating record")).outputs
    assert closed.requires_continual_makeup is False
    with pytest.raises(DomainError):
        damage.cooling_water_system_type(damage.CoolingWaterSystemTypeInput(
            system="open_recirculated", water_source="fresh", reuses_heated_water=True,
            continual_makeup_required=False, blowdown_or_evaporation_loss=True,
            qualification_basis="Contradictory fixture"))
