"""Qualified soil-table/factors -> non-AST pressure-component thinning DF."""
from api581 import Context
from api581.api import damage

base = damage.soil_base_rate_table(damage.SoilBaseRateTableInput(
    condition_profile="variable_industrial_silt",unit_basis="printed_si")).outputs
conditions = damage.SoilCorrosionRateInput(material="carbon_steel",in_contact_with_soil=True,
    applicability_basis="Owner-qualified illustrative buried carbon-steel pipe; no dynamic stray-current condition",
    base_corrosion_rate_m_year=base.corrosion_rate_m_year,
    base_rate_source="Qualified Table2.B.12.2 full profile; printed SI.13mm/year fixture",
    resistivity_application="apply",resistivity=dict(soil_resistivity_ohm_m=50.),
    temperature=dict(equipment_temperature_k=343.15,threshold_basis="printed_si"),
    cathodic_protection=dict(protection_category="annual_polarized_or_instant_off_entire_structure"),
    coating=dict(coating_type="mill_pe_tape_mastic",coating_age_years=30.,
        rated_temperature_occasionally_exceeded=True,maintenance_rare_or_none=True))
rate = damage.soil_corrosion_rate(conditions).outputs
result = damage.soil_thinning_assessment(damage.SoilThinningAssessmentInput(soil=conditions,elapsed_years=10.,
    strength=dict(differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),online_monitoring_factor=1.,
    assessment_scope="unclad_internal_pressure_governed_non_ast"),
    context=Context(asset_id="buried-pipe-001",source_revision="qualified-soil-fixture-v1"))
print("Soil rate m/year:",rate.corrosion_rate_m_year)
print("Coating product/basis:",rate.coating_effectiveness_factor,rate.coating_calculation_basis)
print("Printed worked-example discrepancy:",rate.coating_example_discrepancy_applies)
print("Wall loss fraction:",result.outputs.wall_loss_fraction)
print("Soil-only thinning DF:",result.outputs.thinning_damage_factor)
print("Not a total all-mechanism DF or inspection acceptance.")
