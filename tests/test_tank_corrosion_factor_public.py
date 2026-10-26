"""Public regressions for AST bottom corrosion factor primitives."""

from api581 import evaluate


def test_tank_bottom_corrosion_factor_primitives_are_publicly_regressed():
    cases = [
        ("tank/bottom-base-corrosion-rate", {"side": "soil", "unit_basis": "printed_si"}),
        ("tank/bottom-product-rate-equation", {"base_corrosion_rate_m_year": 1e-4, "product_condition_factor": 1.0, "temperature_factor": 1.0, "steam_coil_factor": 1.0, "water_draw_factor": 1.0}),
        ("tank/bottom-soil-resistivity-factor", {"release_prevention_barrier": False, "soil_resistivity_ohm_m": 100.0}),
        ("tank/bottom-pad-factor", {"pad_type": "native_soil"}),
        ("tank/bottom-drainage-factor", {"drainage_category": "no_storm_water_collects"}),
        ("tank/bottom-cp-factor", {"protection_category": "present_per_api651", "effectiveness_verified_by_high_level_inspection": True, "verification_basis": "fixture"}),
        ("tank/bottom-type-factor", {"bottom_type": "single_bottom"}),
        ("tank/bottom-temperature-factor", {"highest_operating_temperature_k": 320.0, "threshold_basis": "printed_si"}),
        ("tank/bottom-product-condition-factor", {"product_condition": "wet"}),
        ("tank/bottom-steam-coil-factor", {"steam_coil_present": False}),
        ("tank/bottom-water-draw-factor", {"water_draw_practice": "weekly"}),
        ("tank/bottom-corrosion-rate-combine", {"soil_corrosion_rate_m_year": 1e-4, "product_corrosion_rate_m_year": 2e-4, "product_distribution": "general", "minimum_rate_policy": "apply_2_mpy_recommendation"}),
        ("tank/bottom-minimum-thickness", {"release_prevention_barrier": False, "thickness_basis": "api581_2016_default"}),
        ("tank/bottom-wall-parameter", {"starting_thickness_m": 0.02, "corrosion_rate_m_year": 1e-4, "elapsed_years": 5.0, "minimum_thickness_m": 0.005, "corrosion_allowance_m": 0.002}),
        ("tank/bottom-inspection-selection", {"eligible_inspection_grades": ["c", "a"], "eligibility_basis": "fixture"}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

