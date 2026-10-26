"""Direct public evaluate() coverage for thinning composition routes."""

from api581 import evaluate
from api581.api import damage

from test_clad_thinning import clad
from test_thinning_conditions import conditions


def test_thinning_conditional_and_clad_qualified_public_boundaries():
    conditional = evaluate("damage/thinning-conditional-adjustment", {
        "assessment_scope": "non_ast",
        "base_damage_factor": 100.0,
        "conditions": conditions(),
    })
    clad_input = damage.ThinningCladQualifiedInput(
        assessment_scope="non_ast_pressure_vessel_sequential_cladding",
        qualification_basis="Qualified pressure vessel public fixture",
        wall=clad().wall.model_dump(), strength=clad().strength.model_dump(),
        inspections=clad().inspections.model_dump(), conditions=conditions("non_piping"),
    )
    clad_result = evaluate("damage/thinning-clad-qualified", clad_input.model_dump())
    assert conditional["outputs"]["thinning_damage_factor"] > 0.0
    assert clad_result["outputs"]["thinning_damage_factor"] > 0.0


def test_thinning_unclad_design_public_boundary():
    result = evaluate("damage/thinning-unclad-design", {
        "assessment_scope": "non_ast_unclad_design_thickness_governed",
        "qualification_basis": "Qualified code public fixture",
        "wall": {"starting_thickness_m": 0.01, "corrosion_rate_m_year": 0.0002, "elapsed_years": 10.0},
        "strength": {"allowable_stress_pa": 100e6,
                     "weld_efficiency": 1.0, "flow_stress_pa": 250e6, "starting_thickness_m": 0.01,
                     "minimum_required_thickness_m": 0.005, "minimum_structural_thickness_m": 0.006,
                     "design_thickness_basis": "Qualified code public fixture"},
        "inspections": {"confidence": "high", "inspections_a": 1},
        "injection_point_factor": 1.0, "deadleg_factor": 1.0, "online_monitoring_factor": 1.0,
    })
    assert result["outputs"]["thinning_damage_factor"] > 0.0

