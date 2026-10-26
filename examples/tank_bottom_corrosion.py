"""Independent AST base-rate calls and integrated two-sided floor corrosion."""
from api581 import Context
from api581.api import tank

soil = tank.bottom_base_corrosion_rate(tank.BottomBaseCorrosionRateInput(side="soil",unit_basis="printed_si"))
product = tank.bottom_base_corrosion_rate(tank.BottomBaseCorrosionRateInput(side="product",unit_basis="printed_si"))
assessment = tank.bottom_corrosion_assessment(tank.BottomCorrosionAssessmentInput(
    material="carbon_steel",applicability_basis="Demonstration carbon-steel AST floor, not site validation",
    soil_base_corrosion_rate_m_year=soil.outputs.base_corrosion_rate_m_year,
    product_base_corrosion_rate_m_year=product.outputs.base_corrosion_rate_m_year,
    soil_base_rate_source="2016 SI fallback for reference conditions",
    product_base_rate_source="2016 SI fallback for reference conditions",
    bottom_type="single_bottom",soil_resistivity_ohm_m=50,
    pad=dict(pad_type="continuous_asphalt"),drainage=dict(drainage_category="storm_water_collects"),
    cathodic_protection=dict(protection_category="present_per_api651",
        effectiveness_verified_by_high_level_inspection=True,verification_basis="Demonstration High Level inspection basis"),
    temperature=dict(highest_operating_temperature_k=323.15,threshold_basis="printed_si"),
    product_condition=dict(product_condition="wet"),steam_coil=dict(steam_coil_present=True),
    water_draw=dict(water_draw_practice="weekly"),product_distribution="general",
    minimum_rate_policy="apply_2_mpy_recommendation"), context=Context(asset_id="DEMO-AST-001"))
assert abs(assessment.outputs.soil_corrosion_rate_m_year-.0000783354)<1e-14
assert abs(assessment.outputs.product_corrosion_rate_m_year-.0001106875)<1e-14
assert abs(assessment.outputs.combined_corrosion_rate_m_year-.0001890229)<1e-14
print(assessment.outputs.model_dump())
