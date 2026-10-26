"""Public regression cases for remaining AST thinning/consequence primitives."""

from api581 import evaluate


def test_tank_thinning_and_consequence_primitives_are_publicly_regressed():
    cases = [
        ("tank/bottom-thinning-base", {"art_parameter": 0.5, "inspection_grade": "c", "lookup_policy": "linear_between_rows"}),
        ("tank/bottom-thinning-adjustment-factors", {"construction": "welded", "maintained_per_api653": True, "settlement_category": "meets_api653"}),
        ("tank/bottom-repair-cost", {"generic_frequency_by_hole_per_year": {"small": 1e-4, "medium": 2e-5, "large": 1e-5, "rupture": 1e-6}, "tank_diameter_m": 45.0, "repair_cost_by_hole": {"small": 1000.0, "medium": 2000.0, "large": 5000.0, "rupture": 20000.0}, "material_factor": 1.0, "currency": "USD", "cost_basis": "fixture"}),
        ("tank/shell-environment-cost", {"generic_frequency_by_hole_per_year": {"small": 1e-4, "medium": 2e-5, "large": 1e-5, "rupture": 1e-6}, "cost_by_location_per_bbl": {"in_dike": 1.0, "surface_on_site": 2.0, "surface_off_site": 3.0, "subsoil": 4.0, "groundwater": 5.0, "surface_water": 6.0}, "currency": "USD", "cost_basis": "fixture", "fraction_leaving_dike": 0.3, "fraction_on_site": 0.5, "fraction_off_site": 0.2, "released_volume_by_hole_bbl": {"small": 10.0, "medium": 20.0, "large": 30.0, "rupture": 40.0}}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

