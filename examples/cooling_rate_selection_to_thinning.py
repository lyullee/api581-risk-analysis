"""Source-priority example: treated screening bound versus measured local rate."""
from api581 import Context
from api581.api import damage

treatment = dict(material="carbon_steel",system="closed_recirculating",qualified_effective_treatment_program=True,
    actual_ph=8.,effective_microbiological_control=True,no_deposits_or_local_low_flow=True,
    qualification_basis="Illustrative qualified treatment, MIC control and no deposit/local-low-flow conditions")
selection = dict(material="carbon_steel",assessment_distribution="local",
    selection_basis="Illustrative qualified local thinning and source representativeness",
    fallback=dict(kind="treated",treatment=treatment,rate_policy="screen_at_strict_upper_bound",
        rate_selection_basis="Conservative screening at15mpy bound; not a measured or predicted exact rate"))

args = dict(starting_thickness_m=.01,elapsed_years=5.,
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,
        flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative unclad non-AST piping baseline and local inspection coverage")
context = Context(asset_id="DEMO-TREATED-COOLING-001",source_revision="rate-selection-fixture-v1")
screen = damage.cooling_water_selected_thinning(damage.CoolingWaterSelectedThinningInput(selection=selection,**args),context=context).outputs
measured = damage.cooling_water_selected_thinning(damage.CoolingWaterSelectedThinningInput(selection=selection|dict(measurement=dict(
    measurement_type="component_local",measured_rate_m_year=.00008,representative_for_assessed_component=True,
    representativeness_basis="Illustrative qualified component-local measurement covering expected attack")),**args),context=context).outputs
assert screen.selected_rate_is_screening_bound
assert not measured.selected_rate_is_screening_bound and measured.fallback_ignored_due_to_measurement
assert measured.corrosion_rate_m_year == .00008
print("Treated screening source / rate / DF:",screen.selection_source,screen.corrosion_rate_m_year,screen.thinning_damage_factor)
print("Measured priority source / rate / DF:",measured.selection_source,measured.corrosion_rate_m_year,measured.thinning_damage_factor)
print("Strict-bound equality is a declared conservative screening choice, not the source's exact prediction.")
