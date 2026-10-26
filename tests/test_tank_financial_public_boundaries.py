"""Direct public evaluate() coverage for AST financial and integrated workflows."""

from api581 import evaluate
from api581.api import tank

from test_tank_financial import bottom as financial_bottom, shell as financial_shell
from test_tank_source_composition import bottom as source_bottom, economics as bottom_economics
from test_tank_shell import case as shell_case, source as shell_source, economics as shell_economics


def test_tank_financial_and_risk_public_boundaries():
    bottom = evaluate("tank/bottom-financial-consequence", financial_bottom().model_dump())
    shell = evaluate("tank/shell-financial-consequence", financial_shell().model_dump())
    bottom_risk = evaluate("tank/bottom-risk-assessment", tank.BottomRiskAssessmentInput(
        financial=financial_bottom(), management_score=500.0, total_damage_factor=1.0,
        damage_factor_source="public fixture").model_dump())
    shell_risk = evaluate("tank/shell-risk-assessment", tank.ShellRiskAssessmentInput(
        financial=financial_shell(), management_score=500.0, total_damage_factor=1.0,
        damage_factor_source="public fixture").model_dump())
    assert bottom["outputs"]["financial_consequence"] > 0.0
    assert shell["outputs"]["financial_consequence"] > 0.0
    assert bottom_risk["outputs"]["financial_risk_per_year"] >= 0.0
    assert shell_risk["outputs"]["financial_risk_per_year"] >= 0.0


def test_tank_integrated_workflows_public_boundaries():
    bottom = evaluate("tank/bottom-integrated-assessment", tank.BottomIntegratedAssessmentInput(
        source=source_bottom(), distance_to_groundwater_m=5.0, economics=bottom_economics(),
        management_score=500.0, total_damage_factor=1.0, damage_factor_source="public fixture").model_dump())
    cases = [shell_case(hole=h) for h in ("small", "medium", "large", "rupture")]
    shell = evaluate("tank/shell-integrated-assessment", tank.ShellIntegratedAssessmentInput(
        source=shell_source(), cases=cases, economics=shell_economics(), management_score=500.0,
        total_damage_factor=1.0, damage_factor_source="public fixture").model_dump())
    assert bottom["outputs"]["financial_risk_per_year"] >= 0.0
    assert shell["outputs"]["financial_risk_per_year"] >= 0.0

