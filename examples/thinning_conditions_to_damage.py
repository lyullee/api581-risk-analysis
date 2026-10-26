"""Independent qualified monitoring/piping factors and composed thinning DF."""
from api581 import Context
from api581.api import damage

monitoring = dict(row=dict(mechanism="hydrochloric_acid"),
    methods=["key_process_variables","electrical_resistance_probes"],organized_monitoring_plan=True,
    qualification_basis="Demonstration specialist-qualified plan, HCl variables and monitoring intervals",
    key_variables_probe_conjunction_confirmed=True)
conditions = dict(monitoring=monitoring,
    injection=dict(component_scope="piping",injection_or_mix_point_present=True,
        highly_effective_targeted_inspection=False),
    deadleg=dict(component_scope="piping",deadleg_present=True,highly_effective_targeted_inspection=False))

fom = damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring))
assert fom.outputs.online_monitoring_factor == 20
adjusted = damage.thinning_conditional_adjustment(damage.ThinningConditionalAdjustmentInput(
    assessment_scope="non_ast",base_damage_factor=100.,conditions=conditions))
assert adjusted.outputs.thinning_damage_factor == 100*3*3/20

result = damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(
    assessment_scope="non_ast_unclad",qualification_basis="Demonstration qualified internal-pressure piping fixture",
    wall=dict(starting_thickness_m=.01,corrosion_rate_m_year=.0002,elapsed_years=10.),
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,
        flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),conditions=conditions),
    context=Context(asset_id="DEMO-PIPE-001",source_revision="monitoring-fixture-v1"))
o = result.outputs
assert abs(o.thinning_damage_factor-max(o.base_damage_factor*3*3/20,.1))<1e-12
print("Monitoring row / candidates:",o.monitoring_row,o.candidate_method_factors)
print("Applied FOM / FIP / FDL:",o.online_monitoring_factor,o.injection_point_factor,o.deadleg_factor)
print("Base / adjusted thinning DF:",o.base_damage_factor,o.thinning_damage_factor)
print("Demonstration conditions only; not automatic sensor-plan qualification or total all-mechanism DF.")
