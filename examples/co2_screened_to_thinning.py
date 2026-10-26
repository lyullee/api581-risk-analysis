"""CO2 figure screening and qualified dew point -> same-source thinning DF."""
from api581 import Context
from api581.api import damage

screened = dict(temperature_k=333.15,pressure=dict(total_pressure_pa_abs=1e6,co2_mole_fraction=.1),
    material=dict(material_category="carbon_steel",interpretation="table_resistant_alloys",qualification_basis="Illustrative qualified carbon-steel identity"),
    hydrocarbon_wetting=dict(liquid_hydrocarbons_present=False,qualification_basis="Illustrative gas service with no liquid hydrocarbons"),
    moisture=dict(temperature_k=333.15,evidence="qualified_dew_point",dew_point_temperature_k=343.15,dew_point_uncertainty_k=2.,
        equality_policy="indeterminate_at_saturation",qualification_basis="Illustrative qualified dew point and2K uncertainty, not the source approximate fit"),
    wet_model=dict(ph=dict(method="supplied",ph=5.,qualification_basis="Illustrative water pH"),
        flow=dict(method="supplied",shear_stress_pa=19.,qualification_basis="Illustrative known wall shear"),lookup_policy="exact_nodes_only",
        jump_policy="reject_cross_80_90",temperature_denominator_basis="printed_celsius_plus_273",
        simple_upstream_mixture_and_wetting_basis="Illustrative qualified water-wetted upstream mixture",
        inhibitor_factor=.2,inhibitor_effectiveness_basis="Illustrative independently determined inhibitor factor"),
    qualification_basis="Illustrative source screening and positive water evidence; not site validation")
result = damage.co2_screened_thinning(damage.Co2ScreenedThinningInput(corrosion=screened,starting_thickness_m=.02,elapsed_years=1.,
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.02,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative common baseline and qualified non-AST inspection coverage"),
    context=Context(asset_id="DEMO-CO2-SCREENED-001",source_revision="co2-screened-fixture-v1"))
o = result.outputs
assert o.co2_partial_pressure_pa_abs == 1e5
assert o.free_water_screen_state == "present" and not o.free_water_assumed_from_missing_data
print("Screen / water / partial pressure (Pa):",o.screened_calculation_branch,o.free_water_screen_state,o.co2_partial_pressure_pa_abs)
print("CO2 rate / thinning DF:",o.corrosion_rate_m_year,o.thinning_damage_factor)

# Separate legacy figure exemption; explicitly qualified, not evidence of actual metal wetting.
exempt = damage.co2_screened_assessment(damage.Co2ScreenedAssessmentInput(**(screened|dict(
    hydrocarbon_wetting=dict(liquid_hydrocarbons_present=True,water_cut_policy="explicit_qualified_percent",water_content_percent=19.,
        water_content_basis="Illustrative qualified liquid water-cut definition",mixture_velocity_m_s=1.1,
        qualification_basis="Illustrative application of source figure exemption"),moisture=None,wet_model=None)))).outputs
assert exempt.screened_calculation_branch == "figure_hydrocarbon_exemption" and exempt.corrosion_rate_m_year == 0
print("Separate source exemption:",exempt.screened_calculation_branch,"(CO2-specific only)")
