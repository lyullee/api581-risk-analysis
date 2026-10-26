"""Annex2.B soil table anchors, ambiguity and rate-to-thinning composition."""
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def soil(**changes):
    return damage.SoilCorrosionRateInput(**(dict(material="carbon_steel",in_contact_with_soil=True,
        applicability_basis="Qualified buried non-AST carbon-steel soil exposure fixture",
        base_corrosion_rate_m_year=.00013,base_rate_source="Table2.B.12.2 printed SI profile fixture",
        resistivity_application="apply",resistivity=dict(soil_resistivity_ohm_m=50.),
        temperature=dict(equipment_temperature_k=343.15,threshold_basis="printed_si"),
        cathodic_protection=dict(protection_category="annual_polarized_or_instant_off_entire_structure"),
        coating=dict(coating_type="mill_pe_tape_mastic",coating_age_years=30.,
            rated_temperature_occasionally_exceeded=True,maintenance_rare_or_none=True))|changes))


@pytest.mark.parametrize("profile,si,us",[("dry_inland_sand",.03,1.),("variable_industrial_silt",.13,5.),("saturated_coastal_clay",.25,10.)])
@pytest.mark.parametrize("basis",["printed_si","printed_us_mpy"])
def test_base_profiles_preserve_rounded_si_and_us(profile,si,us,basis):
    r = damage.soil_base_rate_table(damage.SoilBaseRateTableInput(condition_profile=profile,unit_basis=basis)).outputs
    assert r.printed_si_rate_mm_year == si and r.printed_us_rate_mpy == us
    assert r.corrosion_rate_m_year == pytest.approx(si/1000 if basis == "printed_si" else us*.0000254)


@pytest.mark.parametrize("resistance,factor",[(1.,1.5),(5.,1.25),(9.,1.25),(15.,1.),(50.,.83),(100.,.83),(101.,.6)])
def test_resistivity_uses_ohm_m_not_ohm_cm(resistance,factor):
    r = damage.soil_resistivity_factor(damage.SoilResistivityFactorInput(soil_resistivity_ohm_m=resistance)).outputs
    assert r.resistivity_factor == factor


@pytest.mark.parametrize("resistance,lower,higher",[(10.,1.25,1.),(20.,1.,.83)])
def test_shared_resistivity_endpoints_require_explicit_choice(resistance,lower,higher):
    with pytest.raises(DomainError) as exc:
        damage.soil_resistivity_factor(damage.SoilResistivityFactorInput(soil_resistivity_ohm_m=resistance))
    assert exc.value.code == "ambiguous_soil_resistivity_boundary"
    for basis,expected in [("lower_resistivity_interval",lower),("higher_resistivity_interval",higher)]:
        r = damage.soil_resistivity_factor(damage.SoilResistivityFactorInput(soil_resistivity_ohm_m=resistance,shared_boundary_basis=basis)).outputs
        assert r.resistivity_factor == expected


@pytest.mark.parametrize("kelvin,factor",[(322.14,1.),(322.15,2.),(377.15,2.),(377.16,1.)])
def test_si_temperature_closed_middle_band(kelvin,factor):
    r = damage.soil_temperature_factor(damage.SoilTemperatureFactorInput(equipment_temperature_k=kelvin,threshold_basis="printed_si")).outputs
    assert r.temperature_factor == factor


@pytest.mark.parametrize("kelvin",[322.1,377.3])
def test_paired_si_us_temperature_rounding_changes_selected_band(kelvin):
    a = damage.soil_temperature_factor(damage.SoilTemperatureFactorInput(equipment_temperature_k=kelvin,threshold_basis="printed_si")).outputs
    b = damage.soil_temperature_factor(damage.SoilTemperatureFactorInput(equipment_temperature_k=kelvin,threshold_basis="printed_us_converted")).outputs
    assert a.temperature_factor == 1. and b.temperature_factor == 2.


@pytest.mark.parametrize("category,factor",[("unprotected_adjacent_cp_stray_current",10.),("no_cp",1.),
    ("not_annual_or_partly_noncompliant",.8),("annual_on_potential_entire_structure",.4),
    ("annual_polarized_or_instant_off_entire_structure",.05)])
def test_cp_table_full_categories(category,factor):
    assert damage.soil_cp_factor(damage.SoilCpFactorInput(protection_category=category)).outputs.cathodic_protection_factor == factor


@pytest.mark.parametrize("coating,expected",[("fusion_bonded_epoxy",1.815),("liquid_epoxy",1.815),
    ("asphalt_enamel",1.815),("asphalt_mastic",1.815),("coal_tar_enamel",3.6),
    ("extruded_pe_mastic_or_rubber",5.4),("mill_pe_tape_mastic",8.1),("field_pe_tape_mastic",18.),("three_layer_pe_pp",2.88)])
def test_all_merged_and_individual_coating_table_rows(coating,expected):
    r = damage.soil_coating_factor(damage.SoilCoatingFactorInput(coating_type=coating,coating_age_years=30.,
        rated_temperature_occasionally_exceeded=True,maintenance_rare_or_none=True)).outputs
    assert r.coating_effectiveness_factor == pytest.approx(expected)
    if coating == "mill_pe_tape_mastic":
        assert r.printed_example_reported_factor == 13.5 and r.printed_example_discrepancy_applies


def test_coating_age_strictly_greater_than_twenty_and_bare_conditions():
    r = damage.soil_coating_factor(damage.SoilCoatingFactorInput(coating_type="mill_pe_tape_mastic",coating_age_years=20.,
        rated_temperature_occasionally_exceeded=False,maintenance_rare_or_none=False)).outputs
    assert r.coating_effectiveness_factor == 1.5 and r.age_factor == 1.
    r = damage.soil_coating_factor(damage.SoilCoatingFactorInput(coating_type="bare",coating_age_years=30.,
        rated_temperature_occasionally_exceeded=False,maintenance_rare_or_none=False)).outputs
    assert r.coating_effectiveness_factor == 1.
    with pytest.raises(DomainError):
        damage.soil_coating_factor(damage.SoilCoatingFactorInput(coating_type="bare",coating_age_years=30.,
            rated_temperature_occasionally_exceeded=True,maintenance_rare_or_none=False))


@pytest.mark.parametrize("age,abuse,rare,expected",[(21.,False,False,1.8),(20.,True,False,4.5),(20.,False,True,2.25)])
def test_nonapplicable_coating_multipliers_are_independent(age,abuse,rare,expected):
    r = damage.soil_coating_factor(damage.SoilCoatingFactorInput(coating_type="mill_pe_tape_mastic",coating_age_years=age,
        rated_temperature_occasionally_exceeded=abuse,maintenance_rare_or_none=rare)).outputs
    assert r.coating_effectiveness_factor == pytest.approx(expected)


def test_soil_rate_hand_anchor_and_no_double_resistivity_adjustment():
    r = damage.soil_corrosion_rate(soil()).outputs
    assert r.corrosion_rate_m_year == pytest.approx(.000087399)
    assert r.thinning_type == "local" and r.coating_example_discrepancy_applies
    b = damage.soil_corrosion_rate(soil(resistivity_application="already_in_base",resistivity=None,
        resistivity_omission_basis="Included in comparable observed base rate")).outputs
    assert b.resistivity_factor == 1. and b.corrosion_rate_m_year == pytest.approx(r.corrosion_rate_m_year/.83)


@pytest.mark.parametrize("changes",[
    dict(in_contact_with_soil=False),dict(applicability_basis="   "),dict(base_rate_source="   "),
    dict(resistivity_application="already_in_base"),dict(resistivity_application="omitted_by_qualification",resistivity=None),
    dict(resistivity=None),dict(resistivity_omission_basis="Should not coexist with applied factor")])
def test_screening_and_optional_resistivity_are_explicit(changes):
    with pytest.raises(DomainError):
        damage.soil_corrosion_rate(soil(**changes))


def test_material_screen_not_automatically_extended_to_other_alloys():
    with pytest.raises(ValidationError):
        soil(material="stainless_steel")


def test_equation_zero_base_and_numeric_range():
    values = dict(base_corrosion_rate_m_year=0.,resistivity_factor=1.5,temperature_factor=2.,
        cathodic_protection_factor=10.,coating_effectiveness_factor=18.)
    assert damage.soil_rate_equation(damage.SoilRateEquationInput(**values)).outputs.corrosion_rate_m_year == 0.
    with pytest.raises(DomainError):
        damage.soil_rate_equation(damage.SoilRateEquationInput(**(values|dict(base_corrosion_rate_m_year=1e308))))


def test_soil_to_thinning_matches_independent_existing_kernel():
    rate = damage.soil_corrosion_rate(soil()).outputs.corrosion_rate_m_year
    strength = dict(differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder")
    inspections = dict(confidence="high",inspections_a=1)
    combined = damage.soil_thinning_assessment(damage.SoilThinningAssessmentInput(soil=soil(),elapsed_years=10.,
        strength=strength,inspections=inspections,online_monitoring_factor=1.,assessment_scope="unclad_internal_pressure_governed_non_ast")).outputs
    direct = damage.thinning_unclad(damage.ThinningUncladInput(wall=dict(starting_thickness_m=.01,corrosion_rate_m_year=rate,elapsed_years=10.),
        strength=strength,inspections=inspections,injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=1.)).outputs
    assert combined.wall_loss_fraction == pytest.approx(.087399)
    assert combined.thinning_damage_factor == direct.thinning_damage_factor
    assert combined.reliability_indices == direct.reliability_indices
