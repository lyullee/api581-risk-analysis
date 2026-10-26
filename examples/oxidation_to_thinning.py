"""Source oxidation rate -> general thinning with qualified hot-design strength.

Numerical fixture only: no creep/fitness-for-service or material-suitability conclusion.
"""
from api581 import Context, DomainError
from api581.api import damage

row = damage.oxidation_table_row(damage.OxidationTableRowInput(material="carbon_steel",unit_basis="printed_si")).outputs
assert row.native_rates[8] is None  # Printed dash at718C; not a zero rate.
corrosion = dict(oxidation=dict(material="carbon_steel",unit_basis="printed_si",maximum_metal_temperature_k=635+273.15,
    lookup_policy="exact_nodes_only",below_table_policy="reject_below_table"),oxygen_present=True,screening_threshold_basis="printed_si",
    applicability_basis="Illustrative material/oxygen and actual maximum exposed-metal-temperature fixture")
result = damage.oxidation_thinning_assessment(damage.OxidationThinningAssessmentInput(corrosion=corrosion,
    starting_thickness_m=.02,elapsed_years=5.,
    strength=dict(method="design_thickness_eq2_17",allowable_stress_pa=50e6,weld_efficiency=1.,flow_stress_pa=150e6,
        starting_thickness_m=.02,minimum_required_thickness_m=.006,minimum_structural_thickness_m=.007,
        design_thickness_basis="Illustrative qualified governing-design-temperature properties and code/load minima"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative common baseline and general-oxidation inspection, no claim of service suitability"),
    context=Context(asset_id="DEMO-HOT-TUBE-001",source_revision="oxidation-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.00056)<1e-12
assert abs(o.wall_loss_fraction-.14)<1e-12
print("General oxidation rate (m/year):",o.corrosion_rate_m_year)
print("Loss fraction / design strength ratio / DF:",o.wall_loss_fraction,o.strength_ratio,o.thinning_damage_factor)
try:
    damage.oxidation_rate(damage.OxidationRateInput(**(corrosion["oxidation"]|dict(maximum_metal_temperature_k=718+273.15))))
except DomainError as error:
    assert error.code == "oxidation_rate_unavailable"
    print("Source dash cell:",error.code)
