import api581


def test_hydrogen_partial_pressure_ideal_mixture():
    result = api581.evaluate(
        "properties/hydrogen-partial-pressure",
        {"total_pressure_pa_abs": 2_000_000.0, "hydrogen_mole_fraction": 0.25},
    )
    assert result["outputs"] == {"hydrogen_partial_pressure_pa_abs": 500_000.0}

