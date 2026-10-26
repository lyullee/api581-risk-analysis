"""AST bottom corrosion -> dedicated thinning DF -> release -> financial risk.

All numbers and qualification statements are demonstration fixtures, not site data.
"""
import _bootstrap  # noqa: F401
from api581 import Context
from api581.api import tank

request = tank.BottomCorrosionRiskAssessmentInput(
    damage=dict(
        corrosion=dict(material="carbon_steel",applicability_basis="Demonstration unlined carbon-steel floor",
            soil_base_corrosion_rate_m_year=.00013,product_base_corrosion_rate_m_year=.00005,
            soil_base_rate_source="2016 rounded SI fallback under reference conditions",
            product_base_rate_source="2016 rounded SI fallback under reference conditions",
            bottom_type="single_bottom",soil_resistivity_ohm_m=50,
            pad=dict(pad_type="continuous_asphalt"),drainage=dict(drainage_category="storm_water_collects"),
            cathodic_protection=dict(protection_category="present_per_api651",
                effectiveness_verified_by_high_level_inspection=True,verification_basis="Illustrative qualified inspection"),
            temperature=dict(highest_operating_temperature_k=323.15,threshold_basis="printed_si"),
            product_condition=dict(product_condition="wet"),steam_coil=dict(steam_coil_present=True),
            water_draw=dict(water_draw_practice="weekly"),product_distribution="general",
            minimum_rate_policy="apply_2_mpy_recommendation"),
        thinning=dict(starting_thickness_m=.006,elapsed_years=10,
            baseline_basis="Illustrative furnished thickness and matching elapsed service",
            corrosion_allowance_m=.00346,
            minimum_thickness=dict(release_prevention_barrier=False,thickness_basis="api581_2016_default"),
            inspections=dict(eligible_inspection_grades=["b","b","d"],
                eligibility_basis="Illustrative owner-qualified inspections in assessed period"),
            lookup_policy="linear_between_rows",adjustments=dict(construction="welded",maintained_per_api653=True,
                settlement_category="meets_api653"))),
    source=dict(tank_diameter_m=61.,fill_height_m=10.,fluid="gasoline",soil="coarse_sand",
        water_density_kg_m3=1000.,water_dynamic_viscosity_pa_s=.001,foundation="concrete_asphalt",
        has_release_prevention_barrier=False,transition_hole_basis="api581_printed"),
    distance_to_groundwater_m=5.,management_score=500.,damage_scope="qualified_thinning_only",
    other_mechanisms_exclusion_basis="Illustrative exclusion of other mechanisms; requires actual owner assessment",
    economics=dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,
        usd_to_output_currency=1.,cost_basis_year=2026),outage_multiplier=1.,production_cost_per_day=1000.,
        currency="USD",cost_basis="Illustrative owner-qualified 2026 USD fixture; not market prices",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,
            subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5))

result = tank.bottom_corrosion_risk_assessment(request,context=Context(
    asset_id="DEMO-AST-001",component_id="floor",source_revision="corrosion-risk-fixture-v1"))
o = result.outputs
assert o.total_damage_factor == o.thinning_damage_factor
assert abs(o.annual_failure_frequency-.000722*o.thinning_damage_factor)<1e-12
assert o.credited_inspection_count == 1
print("Combined corrosion rate (m/year):",o.combined_corrosion_rate_m_year)
print("AST Art / base DF / final DF:",o.art_parameter,o.base_damage_factor,o.thinning_damage_factor)
print("Remaining thickness / minimum (m):",o.predicted_remaining_thickness_m,o.minimum_thickness_m)
print("Annual frequency:",o.annual_failure_frequency)
print("Financial consequence / annual risk:",o.financial_consequence,o.financial_risk_per_year,o.currency)
print("Scope:",o.integration_scope)
