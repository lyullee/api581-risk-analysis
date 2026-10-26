"""Sulfuric source rate and distinct thinning/monitoring velocity thresholds."""
from api581 import Context
from api581.api import damage

corrosion=dict(sulfuric_service_present=True, applicability_basis="Illustrative qualified sulfuric process service",
    rate_model=dict(method="source_table", table=dict(material="ss_316",unit_basis="printed_si",
        acid_mass_fraction=.98, maximum_temperature_k=40+273.15, velocity_m_s=.61, lookup_policy="exact_nodes_only"),
        table_conditions_and_passivity_qualified=True, qualification_basis="Illustrative material, local conditions and passivity review"),
    classification=dict(material_group="stainless_steel", velocity_m_s=.61, threshold_basis="overview_printed_si", equality_policy="reject_ambiguous_boundary"))
result=damage.sulfuric_thinning_assessment(damage.SulfuricThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="general",
    distribution_qualification_basis="Illustrative representative general-thinning coverage",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="sulfuric_acid", sulfuric_material_group="stainless_steel", velocity_m_s=.61),
        methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative common non-AST unclad baseline"),
    context=Context(asset_id="DEMO-SULFURIC-001", source_revision="sulfuric-fixture-v1"))
o=result.outputs
assert abs(o.corrosion_rate_m_year-.00038)<1e-12
assert abs(o.wall_loss_fraction-.038)<1e-12
assert o.source_table_id=="2.B.5.4M" and o.rate_source=="source_maximum_estimate"
print("Source / type / monitoring:",o.source_table_id,o.source_thinning_type,o.monitoring_row)
print("Rate / loss fraction / DF:",o.corrosion_rate_m_year,o.wall_loss_fraction,o.thinning_damage_factor)

# Explicitly qualified SI carbon velocity interpretation; no automatic header repair.
carbon=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(material="carbon_steel", unit_basis="printed_si",
    acid_mass_fraction=.98, maximum_temperature_k=15+273.15, velocity_m_s=.3048, lookup_policy="exact_nodes_only",
    carbon_si_velocity_policy="qualified_us_ft_s_header",
    carbon_si_velocity_qualification_basis="Illustrative owner review of SI/US repeated velocity headings")).outputs
assert abs(carbon.corrosion_rate_m_year-.00025)<1e-12
print("Declared carbon header interpretation:",carbon.carbon_si_velocity_interpretation)
