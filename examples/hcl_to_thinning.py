"""Separated acid pH -> HCl source rate -> qualified local thinning; no server."""
from api581 import Context
from api581.api import damage

corrosion = dict(free_water_present=True, dilute_hcl_service_qualified=True,
    applicability_basis="Illustrative dilute HCl aqueous service",
    wet_model=dict(model_family="ph_table", material="ss_316",
        acidity=dict(method="supplied_ph", ph=3.25, qualification_basis="Illustrative separated acid-phase pH"),
        maximum_temperature_k=79+273.15, unit_basis="printed_si", lookup_policy="exact_nodes_only",
        qualification_basis="Illustrative maximum local temperature and qualified stainless grade"))
route = damage.sour_water_assessment(damage.SourWaterAssessmentInput(
    screening=dict(free_water_present=True, ph=3.25, chlorides_present=True,
        chloride_policy="figure_any_presence_routes_hcl", neutral_ph_policy="detailed_body_inclusive",
        qualification_basis="Illustrative same separated aqueous phase"),
    hcl_model=corrosion, hcl_shared_phase_qualification_basis="Illustrative shared separated acid-phase review")).outputs
result = damage.hcl_thinning_assessment(damage.HclThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="local",
    distribution_qualification_basis="Illustrative local inspection and pit coverage review",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="hydrochloric_acid"), methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative non-AST unclad component baseline"),
    context=Context(asset_id="DEMO-HCL-001", source_revision="hcl-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.00127) < 1e-12
assert abs(o.wall_loss_fraction-.127) < 1e-12
assert o.localized_pitting_already_included
assert route.corrosion_rate_m_year == o.corrosion_rate_m_year
print("Route / table:", route.corrosion_route, o.source_table_id)
print("Rate / wall-loss fraction / DF:", o.corrosion_rate_m_year, o.wall_loss_fraction, o.thinning_damage_factor)
print("Stainless pitting allowance already included:", o.localized_pitting_already_included)

interval = damage.hcl_chloride_interval_from_ph(damage.HclChlorideIntervalFromPhInput(
    ph=.5, no_alkaline_agents_qualified=True, qualification_basis="Illustrative no neutralizing agents")).outputs
assert interval.chloride_band_lower_wppm == 3601 and interval.chloride_band_upper_wppm == 12000
print("Inverse chloride interval (wppm):", interval.chloride_band_lower_wppm, interval.chloride_band_upper_wppm)
