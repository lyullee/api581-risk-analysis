"""Public regression cases for damage mechanism selection/axis primitives."""

from api581 import evaluate


def test_damage_selection_primitives_are_publicly_regressed():
    cases = [
        ("damage/amine-acid-gas-loading", {"h2s_amount_mol": 1.0, "co2_amount_mol": 2.0, "active_amine_amount_mol": 10.0, "common_sample_basis": "fixture"}),
        ("damage/amine-strength-factor", {"amine_type": "mea", "amine_mass_fraction": 0.20}),
        ("damage/h2sh2-table-axes", {"material": "carbon_steel", "unit_basis": "printed_si"}),
        ("damage/sulfidic-material-selection", {"material": "ss_316"}),
        ("damage/sulfidic-velocity-factor", {"velocity_m_s": 31.0, "boundary_interpretation": "body_strictly_above_100ft_s", "qualification_basis": "fixture"}),
        ("damage/sulfuric-table-axes", {"material": "ss_316", "unit_basis": "printed_si"}),
        ("damage/groundwater-tks", {"chloride_mg_l": 10.0, "sulfate_mg_l": 5.0, "dissolved_co2_mg_l": 2.0, "bicarbonate_mg_l": 20.0, "carbonate_mg_l": 1.0, "sulfide_mg_l": 0.1, "ammonia_mg_l": 0.5, "concentration_basis": "common analytical fixture"}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

