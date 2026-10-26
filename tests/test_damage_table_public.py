"""Public regressions for additional chemistry table/selection primitives."""

from api581 import evaluate


def test_damage_table_and_selection_primitives_are_publicly_regressed():
    cases = [
        ("damage/sulfidic-table-axes", {"material": "cr5_0p5mo", "unit_basis": "printed_si"}),
        ("damage/sulfidic-thinning-classification", {"tan_mg_koh_g": 1.75}),
        ("damage/hcl-ph-rate", {"material": "carbon_steel", "ph": 5.0, "maximum_temperature_k": 325.15, "unit_basis": "printed_si", "lookup_policy": "bilinear"}),
        ("damage/hf-carbon-rate", {"velocity_m_s": 10.0, "velocity_basis": "printed_si", "hf_mass_fraction": 0.50, "concentrated_extension_policy": "reject_above_81wt_percent", "maximum_temperature_k": 350.0, "unit_basis": "printed_si", "lookup_policy": "bilinear"}),
        ("damage/amine-loading-selection", {"acid_gas_loading_mol_mol": 0.05, "loading_gap_policy": "reject_unassigned_0p10_to_0p15"}),
        ("damage/alkaline-sour-water-velocity-selection", {"phase_regime": "two_phase", "vapor_velocity_m_s": 10.0, "liquid_velocity_m_s": 1.0, "qualification_basis": "fixture"}),
        ("damage/alkaline-sour-water-pressure-adjustment", {"baseline_corrosion_rate_m_year": 1e-4, "h2s_partial_pressure_pa_abs": 1000.0, "equation_basis": "printed_si"}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

