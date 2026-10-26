"""Public sampled-grid dispersion boundary regression."""

from api581 import evaluate


def test_dispersion_threshold_grid_area_public_boundary():
    result = evaluate("dispersion/threshold-grid-area", {
        "downwind_coordinates_m": [0.0, 10.0, 20.0],
        "crosswind_coordinates_m": [-5.0, 0.0, 5.0],
        "volume_fraction_by_crosswind_then_downwind": [
            [0.0, 0.0, 0.0],
            [0.02, 0.08, 0.02],
            [0.0, 0.0, 0.0],
        ],
        "threshold_volume_fraction": 0.05,
        "sampling_basis": "qualified sampled SLABx grid fixture",
    })
    assert result["outputs"]["sampled_exceedance_area_m2"] >= 0.0

