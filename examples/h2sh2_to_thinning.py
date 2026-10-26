"""High-temperature hydrogen sulfidation -> same-rate qualified thinning."""
from api581 import Context
from api581.api import damage

service=dict(material="cr5_0p5mo", unit_basis="printed_si", h2s_mole_fraction=.003,
    maximum_temperature_k=413+273.15, stream_case="gas_oil", lookup_policy="exact_nodes_only",
    hydrogen_sulfidation_environment_qualified=True,
    material_and_stream_qualification_basis="Illustrative qualified hydroprocessing hydrogen environment, material and gas-oil curve")
corrosion=dict(h2s_h2_service_present=True, applicability_basis="Illustrative high-temperature hydrogen-sulfidation service", service_model=service)
result=damage.h2sh2_thinning_assessment(damage.H2sh2ThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="general",
    distribution_qualification_basis="Illustrative actual general distribution and representative inspection",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="high_temperature_h2s_h2"), methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative common non-AST unclad baseline"),
    context=Context(asset_id="DEMO-H2SH2-001", source_revision="h2sh2-fixture-v1"))
o=result.outputs
assert abs(o.corrosion_rate_m_year-.00185)<1e-12
assert abs(o.wall_loss_fraction-.185)<1e-12
print("Table / curve / monitoring:",o.source_table_id,o.selected_hydrocarbon_curve,o.monitoring_row)
print("Rate / loss fraction / DF:",o.corrosion_rate_m_year,o.wall_loss_fraction,o.thinning_damage_factor)
