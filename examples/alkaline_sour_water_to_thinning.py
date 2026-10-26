"""Qualified two-phase NH4HS corrosion, sour-water routing and local thinning."""
from api581 import Context
from api581.api import damage, properties

pressure = properties.h2s_partial_pressure(properties.H2sPartialPressureInput(
    total_pressure_pa_abs=10e6, h2s_mole_fraction=.0621)).outputs
corrosion = dict(material="carbon_steel", free_water_present=True, ph=8.,
    h2s_ammonia_service_qualified=True, applicability_basis="Illustrative qualified alkaline aqueous carbon-steel service",
    wet_model=dict(concentration=dict(method="supplied", nh4hs_mass_fraction=.1,
        qualification_basis="Illustrative ionic-model condensed-water concentration"),
        velocity=dict(phase_regime="two_phase", vapor_velocity_m_s=7.62, liquid_velocity_m_s=1.,
            qualification_basis="Illustrative separate phase velocities"),
        h2s_partial_pressure_pa_abs=pressure.h2s_partial_pressure_pa_abs,
        baseline_unit_basis="printed_si", pressure_equation_basis="printed_si",
        lookup_policy="exact_nodes_only", thinning_threshold_basis="printed_si",
        qualification_basis="Illustrative NH4HS pressure and concentration applicability"))
screening = dict(free_water_present=True, ph=8., chlorides_present=False,
    chloride_policy="figure_any_presence_routes_hcl", neutral_ph_policy="detailed_body_inclusive",
    qualification_basis="Illustrative separated-water pH screening")
routed = damage.sour_water_assessment(damage.SourWaterAssessmentInput(
    screening=screening, alkaline_model=corrosion)).outputs
result = damage.alkaline_sour_water_thinning_assessment(damage.AlkalineSourWaterThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="local",
    distribution_qualification_basis="Illustrative qualified local inspection coverage",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6,
        diameter_m=.5, flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="sour_water", velocity_m_s=7.62),
        methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative qualified non-AST unclad baseline"),
    context=Context(asset_id="DEMO-ALKALINE-SOUR-001", source_revision="nh4hs-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.00218) < 1e-12
assert abs(o.wall_loss_fraction-.218) < 1e-12
assert routed.corrosion_rate_m_year == o.corrosion_rate_m_year
assert o.selected_velocity_phase == "vapor" and o.source_thinning_type == "local"
print("Route / phase:", routed.corrosion_route, o.selected_velocity_phase)
print("Baseline / pressure factor:", o.baseline_corrosion_rate_m_year, o.pressure_correction_factor)
print("Rate / wall-loss fraction / DF:", o.corrosion_rate_m_year, o.wall_loss_fraction, o.thinning_damage_factor)
