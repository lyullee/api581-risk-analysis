"""Public regression cases for chemistry damage primitive APIs."""

from api581 import evaluate


def test_acid_sour_hf_and_hcl_primitives_are_publicly_regressed():
    cases = [
        ("damage/acid-sour-water-route", {"free_water_present": True, "ph": 5.0, "chlorides_present": True, "chloride_concentration_ppm": 100.0, "chloride_policy": "figure_any_presence_routes_hcl", "neutral_ph_policy": "detailed_body_inclusive", "qualification_basis": "fixture"}),
        ("damage/acid-sour-water-base-rate", {"ph": 5.0, "maximum_water_temperature_k": 325.15, "unit_basis": "printed_si", "lookup_policy": "bilinear", "ph_edge_policy": "reject_unprinted_ph"}),
        ("damage/acid-sour-water-oxygen-factor", {"oxygen_content_ppb": 20.0}),
        ("damage/acid-sour-water-velocity-factor", {"velocity_m_s": 1.0, "equation_basis": "printed_si"}),
        ("damage/acid-sour-water-rate-equation", {"base_corrosion_rate_m_year": 1e-4, "oxygen_factor": 1.0, "velocity_factor": 1.0}),
        ("damage/hf-concentration-selection", {"hf_mass_fraction": 0.50, "concentrated_extension_policy": "reject_above_81wt_percent"}),
        ("damage/hf-carbon-velocity-band", {"velocity_m_s": 10.0, "velocity_basis": "printed_si"}),
        ("damage/hcl-ph-from-chloride", {"chloride_mass_fraction": 100.0 / 1e6, "no_alkaline_agents_qualified": True, "qualification_basis": "fixture"}),
        ("damage/hcl-chloride-interval-from-ph", {"ph": 3.0, "no_alkaline_agents_qualified": True, "qualification_basis": "fixture"}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

