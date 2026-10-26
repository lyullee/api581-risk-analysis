"""2016 CO2 wet model -> correction -> qualified non-AST thinning DF.

All properties, wetting and inhibitor statements are demonstration qualifications.
"""
from api581 import Context
from api581.api import damage

corrosion = dict(material="carbon_steel",temperature_k=333.15,co2_partial_pressure_pa_abs=1e5,
    free_liquid_water_present=True,applicability_basis="Illustrative qualified free-liquid-water carbon-steel CO2 service",
    wet_model=dict(ph=dict(method="supplied",ph=5.,qualification_basis="Illustrative known water pH"),
        flow=dict(method="supplied",shear_stress_pa=19.,qualification_basis="Illustrative qualified wall shear, not inferred EOS"),
        lookup_policy="exact_nodes_only",jump_policy="reject_cross_80_90",temperature_denominator_basis="printed_celsius_plus_273",
        simple_upstream_mixture_and_wetting_basis="Illustrative simple crude/water/natural-gas stream with steel wetted by free water",
        glycol=dict(composition_percent=50.,composition_basis="equation_g_percent"),inhibitor_factor=.2,
        inhibitor_effectiveness_basis="Illustrative independently determined inhibitor reduction, not installation-only credit"))
result = damage.co2_thinning_assessment(damage.Co2ThinningAssessmentInput(corrosion=corrosion,
    starting_thickness_m=.02,elapsed_years=1.,
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,
        flow_stress_pa=250e6,starting_thickness_m=.02,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative qualified unclad non-AST piping, inspection scope and common baseline"),
    context=Context(asset_id="DEMO-CO2-PIPE-001",source_revision="co2-corrosion-fixture-v1"))
o = result.outputs
assert o.applied_reduction_factor == .2
assert o.applied_shear_stress_pa == 19
print("Model branch / pH / f(T,pH):",o.calculation_branch,o.model_ph,o.temperature_ph_factor)
print("Fugacity (Pa) / glycol / inhibitor:",o.fugacity_pa,o.glycol_factor,o.inhibitor_factor)
print("Base / final corrosion (m/year):",o.base_corrosion_rate_m_year,o.corrosion_rate_m_year)
print("Wall-loss fraction / thinning DF:",o.wall_loss_fraction,o.thinning_damage_factor)

dry = damage.co2_corrosion_assessment(damage.Co2CorrosionAssessmentInput(**(corrosion|dict(free_liquid_water_present=False,wet_model=None))))
assert dry.outputs.corrosion_rate_m_year == 0 and dry.outputs.model_ph is None
print("Qualified no-free-water branch:",dry.outputs.calculation_branch,"(CO2-specific rate only)")
