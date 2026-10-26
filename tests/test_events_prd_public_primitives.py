"""Public API smoke/regression cases for event trees and PRD risk primitives."""

from api581 import evaluate


def test_event_tree_primitives_are_publicly_regressed():
    assert evaluate("events/single-phase-tree", {
        "phase": "vapor", "release_type": "continuous", "case_type": "leakage",
        "ignition_probability": 0.4, "immediate_given_ignition": 0.5,
        "vce_given_delayed": 0.2, "branch_probability_source": "fixture",
    })["outputs"]
    assert evaluate("events/single-phase-ignition", {
        "reference_basis": "api581_printed_c16", "reference_source": "fixture",
        "phase": "vapor", "flammable_rate_kg_s": 1.0,
        "flash_point_temperature_k": 300.0, "correlation_basis_source": "fixture",
        "release_type": "continuous", "case_type": "leakage",
        "molecular_weight_kg_kmol": 28.0,
        "storage_temperature_k": 320.0, "autoignition_temperature_k": 400.0,
    })["outputs"]
    assert evaluate("events/two-phase-tree", {
        "release_type": "continuous", "case_type": "leakage",
        "ignition_probability": 0.4, "immediate_given_ignition": 0.5,
        "vce_given_delayed": 0.2, "branch_probability_source": "fixture",
    })["outputs"]
    assert evaluate("events/two-phase-ignition", {
        "reference_basis": "api581_printed_c16", "reference_source": "fixture",
        "release_type": "continuous", "case_type": "leakage",
        "adjusted_mass_rate_kg_s": 1.0, "flammable_mass_fraction": 0.8,
        "flash_mass_fraction": 0.2, "liquid_flash_point_temperature_k": 300.0,
        "vapor_flash_point_temperature_k": 250.0, "vapor_molecular_weight_kg_kmol": 20.0,
        "storage_temperature_k": 320.0, "autoignition_temperature_k": 400.0,
        "correlation_basis_source": "fixture", "mixing_basis": "api581_printed_liquid_weight",
        "weighting_source": "fixture",
    })["outputs"]


def test_prd_leakage_and_risk_primitives_are_publicly_regressed():
    common = {"currency": "USD", "cost_basis_year": 2020}
    cases = [
        ("prd/leakage-rates", {"operating_capacity_kg_s": 2.0}),
        ("prd/leakage-duration", {"inlet_size_nps": 2.0, "discharge": "atmosphere"}),
        ("prd/inventory-loss-factor", {"discharge": "flare", "flare_recovery_installed": True}),
        ("prd/inventory-loss", {**common, "leakage_rate_kg_s": 0.1, "duration_s": 60.0, "fluid_cost_per_kg": 2.0, "inventory_loss_factor": 0.5}),
        ("prd/repair-cost", {**common, "inlet_size_nps": 2.0, "price_index_multiplier": 1.0, "output_currency_per_usd": 1.0}),
        ("prd/production-loss", {**common, "daily_production_margin": 1000.0, "shutdown_duration_days": 2.0, "leak_case": "stuck_open", "mild_leak_tolerated_or_online_repair": False}),
        ("prd/leakage-consequence", {**common, "operating_capacity_kg_s": 2.0, "inlet_size_nps": 2.0, "discharge": "atmosphere", "fluid_cost_per_kg": 2.0, "environmental_cost": 10.0, "repair_cost": 100.0, "daily_production_margin": 1000.0, "shutdown_duration_days": 2.0, "mild_leak_tolerated_or_online_repair": False, "model_basis": "two_case_equations"}),
        ("prd/multiple-device-pressure", {"analyzed_orifice_area_m2": 0.01, "total_installed_orifice_area_m2": 0.04, "scenario_pressure_pa_gauge": 1000000.0}),
        ("prd/fail-risk", {**common, "protected_equipment": [{"equipment_id": "vessel-1", "cases": [{"case_id": "small", "annual_failure_frequency": 1e-4, "financial_consequence": 1000.0}]}]}),
        ("prd/leakage-risk", {**common, "leakage_measure": 1e-4, "financial_consequence": 1000.0, "measure_basis": "annual_frequency"}),
        ("prd/total-risk", {**common, "fail_risk_per_year": 0.1, "leakage_risk_value": 0.2, "leakage_measure_basis": "annual_frequency"}),
        ("prd/risk-assessment", {**common, "protected_equipment": [{"equipment_id": "vessel-1", "cases": [{"case_id": "small", "annual_failure_frequency": 1e-4, "financial_consequence": 1000.0}]}], "leakage_measure": 1e-4, "leakage_financial_consequence": 1000.0, "leakage_measure_basis": "annual_frequency"}),
        ("prd/service-age", {"installation_date": "2010-01-01", "evaluation_date": "2020-01-01", "events": [{"event_date": "2018-01-01", "event_type": "overhaul"}]}),
    ]
    for calculation_id, inputs in cases:
        result = evaluate(calculation_id, inputs)
        assert result["calculation_id"] == calculation_id
        assert result["outputs"]

