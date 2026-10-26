import pytest

from api581 import DomainError, evaluate


def test_four_hole_financial_rollup_preserves_components_and_frequency_weighting():
    holes = [
        {"hole": "small", "generic_frequency_per_year": 1, "component_repair_cost": 1,
         "surrounding_equipment_cost": 2, "business_interruption_cost": 3, "injury_cost": 4,
         "environmental_cost": 5},
        {"hole": "medium", "generic_frequency_per_year": 2, "component_repair_cost": 10,
         "surrounding_equipment_cost": 20, "business_interruption_cost": 30, "injury_cost": 40,
         "environmental_cost": 50},
        {"hole": "large", "generic_frequency_per_year": 3, "component_repair_cost": 100,
         "surrounding_equipment_cost": 200, "business_interruption_cost": 300, "injury_cost": 400,
         "environmental_cost": 500},
        {"hole": "rupture", "generic_frequency_per_year": 4, "component_repair_cost": 1000,
         "surrounding_equipment_cost": 2000, "business_interruption_cost": 3000, "injury_cost": 4000,
         "environmental_cost": 5000},
    ]
    out = evaluate("financial/hole-total", {"holes": holes, "currency": "KRW", "cost_basis_year": 2026})["outputs"]
    assert out["total_generic_frequency_per_year"] == 10
    assert out["per_hole"][0]["financial_consequence"] == 15
    assert out["per_hole"][-1]["financial_consequence"] == 15000
    assert out["annual_financial_risk"] == pytest.approx(1 * 15 + 2 * 150 + 3 * 1500 + 4 * 15000)
    assert out["frequency_weighted_financial_consequence"] == pytest.approx(out["annual_financial_risk"] / 10)


def test_four_hole_financial_rollup_rejects_missing_hole_or_zero_frequency():
    row = {"hole": "small", "generic_frequency_per_year": 1, "component_repair_cost": 0,
           "surrounding_equipment_cost": 0, "business_interruption_cost": 0, "injury_cost": 0,
           "environmental_cost": 0}
    with pytest.raises(DomainError):
        evaluate("financial/hole-total", {"holes": [row] * 4, "currency": "KRW", "cost_basis_year": 2026})
    with pytest.raises(DomainError):
        evaluate("financial/hole-total", {"holes": [{**row, "hole": hole, "generic_frequency_per_year": 0}
            for hole in ("small", "medium", "large", "rupture")], "currency": "KRW", "cost_basis_year": 2026})
