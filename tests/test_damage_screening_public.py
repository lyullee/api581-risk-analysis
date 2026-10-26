"""Public regression cases for simple API 581 damage screening branches."""

from api581 import evaluate


def test_damage_screening_and_table_boundaries_are_publicly_regressed():
    cases = [
        ("damage/thinning-type", {"effective_inspection_types": ["general"], "applicable_mechanism_types": ["localized"], "qualification_basis": "fixture"}),
        ("damage/oxidation-screen", {"maximum_metal_temperature_k": 800.0, "oxygen_present": True, "threshold_basis": "printed_si"}),
        ("damage/oxidation-table-row", {"material": "carbon_steel", "unit_basis": "printed_si"}),
        ("damage/caustic-screening", {"material": "carbon_steel", "caustic_present": True, "screening_basis": "fixture"}),
        ("damage/amine-cracking-screening", {"material": "carbon_steel", "acid_gas_treating_amine_present": True, "screening_basis": "fixture"}),
        ("damage/ssc-screening", {"material": "carbon_steel", "water_present": True, "h2s_present": True, "exposure_basis": "fixture"}),
        ("damage/hic-h2s-screening", {"material": "carbon_steel", "water_present": True, "h2s_present": True, "exposure_basis": "fixture"}),
        ("damage/acscc-screening", {"material": "carbon_steel", "water_present": True, "water_ph": 8.0, "fccu_feed_sulfur_reduced": True, "fccu_feed_nitrogen_increased": False, "screening_basis": "fixture"}),
        ("damage/pascc-screening", {"material": "austenitic_stainless_steel", "sulfur_bearing_compounds_exposure": True, "exposure_basis": "fixture"}),
        ("damage/clscc-screening", {"material": "austenitic_stainless_steel", "actual_or_potential_wet_chloride_exposure": True, "operating_temperature_k": 350.0, "temperature_basis": "printed_si", "exposure_basis": "fixture"}),
        ("damage/groundwater-rate-classification", {"corrosion_rate_m_year": 0.00025, "unit_basis": "printed_si", "shared_boundary_policy": "lower_severity"}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

