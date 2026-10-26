"""Public evaluate() coverage for composed damage calculations with existing fixtures."""

from api581 import evaluate
from test_clad_thinning import clad
from test_lining import history, request as lining_request
from test_co2_corrosion import request as co2_request
from test_oxidation import lookup as oxidation_lookup, assessment as oxidation_assessment


def test_damage_clad_and_lining_public_boundaries():
    clad_result = evaluate("damage/thinning-clad", clad().model_dump())
    age_result = evaluate("damage/lining-effective-age", history())
    lining_result = evaluate("damage/lining-assessment", lining_request().model_dump())
    assert clad_result["outputs"]["thinning_damage_factor"] >= 0.0
    assert age_result["outputs"]["effective_age_years"] >= 0.0
    assert lining_result["outputs"]["governing_thinning_damage_factor"] >= 0.0


def test_damage_co2_and_oxidation_public_boundaries():
    co2_result = evaluate("damage/co2-corrosion-assessment", co2_request().model_dump())
    oxidation_result = evaluate("damage/oxidation-rate", oxidation_lookup(
        material="carbon_steel", unit_basis="printed_si", maximum_metal_temperature_k=649.0 + 273.15,
        lookup_policy="linear_between_nodes"))
    assert co2_result["outputs"]["corrosion_rate_m_year"] >= 0.0
    assert oxidation_result["outputs"]["corrosion_rate_m_year"] > 0.0


def test_damage_oxidation_assessment_and_thinning_public_boundaries():
    assessment_result = evaluate("damage/oxidation-assessment", oxidation_assessment())
    strength = {"method": "design_thickness_eq2_17", "allowable_stress_pa": 50e6,
                "weld_efficiency": 1.0, "flow_stress_pa": 150e6, "starting_thickness_m": 0.02,
                "minimum_required_thickness_m": 0.006, "minimum_structural_thickness_m": 0.007,
                "design_thickness_basis": "Qualified public high-temperature design fixture"}
    conditions = {"monitoring": {"row": {"mechanism": "other"}, "methods": [],
                                  "organized_monitoring_plan": False},
                  "injection": {"component_scope": "piping", "injection_or_mix_point_present": False,
                                "highly_effective_targeted_inspection": False},
                  "deadleg": {"component_scope": "piping", "deadleg_present": False,
                              "highly_effective_targeted_inspection": False}}
    thinning_result = evaluate("damage/oxidation-thinning-assessment", {
        "corrosion": oxidation_assessment(), "starting_thickness_m": 0.02, "elapsed_years": 5.0,
        "strength": strength, "inspections": {"confidence": "high", "inspections_a": 1},
        "conditions": conditions,
        "qualification_basis": "Qualified public oxidation thinning fixture",
    })
    assert assessment_result["outputs"]["corrosion_rate_m_year"] > 0.0
    assert thinning_result["outputs"]["thinning_damage_factor"] > 0.0

