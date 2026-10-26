"""Public evaluate-boundary smoke checks for composed AST calculations."""

from api581 import evaluate
from api581.api import tank

from test_tank_source_composition import bottom as source_bottom, shell as source_shell
from test_tank_corrosion import fixture as corrosion_fixture
from test_tank_thinning import basis as thinning_basis
from test_tank_financial import bottom as financial_bottom


def test_tank_composed_source_assessments_public_boundary():
    bottom = evaluate("tank/bottom-source-assessment", source_bottom().model_dump())
    shell = evaluate("tank/shell-source-assessment", source_shell().model_dump())
    assert bottom["outputs"]["generic_total_per_year"] > 0.0
    assert shell["outputs"]["generic_total_per_year"] > 0.0


def test_tank_composed_damage_assessments_public_boundary():
    corrosion = evaluate("tank/bottom-corrosion-assessment", corrosion_fixture())
    thinning_input = tank.BottomThinningAssessmentInput(
        **thinning_basis(), corrosion_rate_m_year=0.0002, corrosion_rate_basis="public fixture"
    )
    thinning = evaluate("tank/bottom-thinning-assessment", thinning_input.model_dump())
    assert corrosion["outputs"]["combined_corrosion_rate_m_year"] > 0.0
    assert thinning["outputs"]["thinning_damage_factor"] >= 0.0


def test_tank_composed_risk_assessment_public_boundary():
    risk_input = tank.BottomRiskAssessmentInput(
        financial=financial_bottom(),
        management_score=500.0,
        total_damage_factor=1.0,
        damage_factor_source="public fixture",
    )
    result = evaluate("tank/bottom-risk-assessment", risk_input.model_dump())
    assert result["outputs"]["financial_risk_per_year"] >= 0.0

