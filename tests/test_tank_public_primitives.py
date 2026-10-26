"""Public evaluate() coverage for AST/tank primitive calculation APIs.

These are intentionally small, deterministic cases: they exercise the public
registry envelope and keep the individual Part 3 tank calculations callable
without requiring a full integrated tank scenario.
"""

from api581 import evaluate


def test_tank_geometry_and_property_primitives_are_publicly_regressed():
    cases = [
        ("tank/fluid-table", {"fluid": "gasoline"}),
        ("tank/soil-table", {"soil": "coarse_sand"}),
        ("tank/soil-water-conductivity", {"printed_lower_bound_cm_s": 1e-4, "printed_upper_bound_cm_s": 2e-4}),
        ("tank/fluid-conductivity", {"water_hydraulic_conductivity_m_day": 0.1, "liquid_density_kg_m3": 750.0, "dynamic_viscosity_pa_s": 0.002, "water_density_kg_m3": 1000.0, "water_dynamic_viscosity_pa_s": 0.001}),
        ("tank/seepage-velocity", {"product_hydraulic_conductivity_m_day": 0.1, "porosity": 0.35}),
        ("tank/bottom-hole-count", {"tank_diameter_m": 45.0}),
        ("tank/bottom-inventory", {"tank_diameter_m": 45.0, "fill_height_m": 10.0, "liquid_density_kg_m3": 750.0}),
        ("tank/shell-course-inventory", {"tank_diameter_m": 45.0, "fill_height_m": 10.0, "liquid_density_kg_m3": 750.0, "course_index": 2, "course_height_m": 2.0}),
        ("tank/shell-flow", {"hole_diameter_m": 0.00635, "liquid_head_m": 4.0, "liquid_density_kg_m3": 750.0}),
        ("tank/bottom-flow", {"hole_diameter_m": 0.0127, "liquid_height_m": 10.0, "product_hydraulic_conductivity_m_day": 0.1, "liquid_density_kg_m3": 750.0, "number_of_holes": 1, "has_release_prevention_barrier": False, "transition_hole_basis": "api581_printed"}),
        ("tank/shell-detection-time", {"hole_diameter_m": 0.003175, "diameter_boundary_basis": "inch_0_125"}),
        ("tank/bottom-detection-time", {"foundation": "concrete_asphalt", "has_release_prevention_barrier": False}),
        ("tank/release-volume", {"release_case": "leak", "native_rate_bbl_day": 100.0, "available_volume_m3": 1000.0, "liquid_density_kg_m3": 750.0, "detection_time_days": 2.0}),
        ("tank/environment-cost-table", {"sensitivity": "medium"}),
        ("tank/surface-spill-partition", {"released_volume_bbl": 100.0, "fraction_leaving_dike": 0.3, "fraction_on_site": 0.5, "fraction_off_site": 0.2}),
        ("tank/groundwater-arrival", {"distance_to_groundwater_m": 5.0, "seepage_velocity_m_day": 0.1}),
        ("tank/subsurface-spill-partition", {"leaked_volume_bbl": 100.0, "detection_time_days": 30.0, "groundwater_arrival_time_days": 10.0}),
        ("tank/shell-hole-sizes", {"tank_diameter_m": 45.0}),
        ("tank/bottom-hole-sizes", {"tank_diameter_m": 45.0, "has_release_prevention_barrier": False}),
        ("tank/generic-frequency", {"component_type": "TANKBOTTOM"}),
        ("tank/component-outage", {"generic_frequency_by_hole_per_year": {"small": 1e-4, "medium": 2e-5, "large": 1e-5, "rupture": 1e-6}, "component_type": "TANKBOTTOM", "outage_multiplier": 1.0, "override_days": {"small": 2.0, "medium": 3.0, "large": 5.0, "rupture": 10.0}}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

