"""Acid sour water pH/oxygen/velocity -> qualified local thinning review and DF."""
from api581 import Context
from api581.api import damage

screening = dict(free_water_present=True,ph=5.75,chlorides_present=False,chloride_policy="figure_any_presence_routes_hcl",
    neutral_ph_policy="detailed_body_inclusive",qualification_basis="Illustrative free water and lowest separated aqueous-phase pH")
corrosion = dict(screening=screening,material="carbon_steel",primary_h2s_and_insignificant_other_corrosives_qualified=True,
    applicability_basis="Illustrative primary H2S, insignificant NH3/CO2/cyanides and other-corrosive qualification",
    carbon_model=dict(maximum_water_temperature_k=79+273.15,unit_basis="printed_si",lookup_policy="exact_nodes_only",ph_edge_policy="reject_unprinted_ph",
        oxygen_content_ppb=60.,velocity_m_s=3.,velocity_equation_basis="printed_si",qualification_basis="Illustrative qualified maximum water temperature and separated-phase pH"))
result = damage.acid_sour_water_thinning_assessment(damage.AcidSourWaterThinningAssessmentInput(corrosion=corrosion,
    assessment_distribution="local",localized_attack_review_basis="Illustrative high oxygen/velocity localized-attack and inspection review",
    starting_thickness_m=.01,elapsed_years=10.,
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="sour_water",velocity_m_s=3.),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative non-AST unclad component, common baseline and local inspection coverage"),
    context=Context(asset_id="DEMO-ACID-SOUR-001",source_revision="acid-sour-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.000196)<1e-12
assert o.localized_attack_review_required
print("Route / base rate (m/year):",o.corrosion_route,o.base_corrosion_rate_m_year)
print("Oxygen / velocity factors:",o.oxygen_factor,o.velocity_factor)
print("Rate / wall-loss fraction / thinning DF:",o.corrosion_rate_m_year,o.wall_loss_fraction,o.thinning_damage_factor)

routed = damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**(screening|dict(ph=4.)))).outputs
assert routed.corrosion_route == "hydrochloric_acid"
print("Separate lower-pH route:",routed.corrosion_route,"(acid-sour rate must not be reused)")
