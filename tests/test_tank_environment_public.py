"""Public regression for AST bottom environmental consequence aggregation."""

from api581 import evaluate


def test_tank_bottom_environment_cost_public_boundary():
    result = evaluate("tank/bottom-environment-cost", {
        "generic_frequency_by_hole_per_year": {"small": 1e-4, "medium": 2e-5, "large": 1e-5, "rupture": 1e-6},
        "cost_by_location_per_bbl": {"in_dike": 1.0, "surface_on_site": 2.0, "surface_off_site": 3.0, "subsoil": 4.0, "groundwater": 5.0, "surface_water": 6.0},
        "currency": "USD",
        "cost_basis": "fixture",
        "fraction_leaving_dike": 0.3,
        "fraction_on_site": 0.5,
        "fraction_off_site": 0.2,
        "leaked_volume_by_hole_bbl": {"small": 10.0, "medium": 20.0, "large": 30.0},
        "total_tank_volume_bbl": 1000.0,
        "detection_time_days": 30.0,
        "groundwater_arrival_time_days": 10.0,
    })
    assert result["outputs"]["environment_cost"] >= 0.0

