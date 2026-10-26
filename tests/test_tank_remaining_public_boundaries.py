"""Direct public evaluate() coverage for remaining AST composition nodes."""

from api581 import evaluate
from api581.api import tank

from test_tank_thinning import corrosion, basis, risk_request
from test_tank_shell import case, pool


def test_tank_corrosion_thinning_and_risk_public_boundaries():
    damage = tank.BottomCorrosionThinningAssessmentInput(corrosion=corrosion(), thinning=basis())
    combined = evaluate("tank/bottom-corrosion-thinning-assessment", damage.model_dump())
    risk = evaluate("tank/bottom-corrosion-risk-assessment", risk_request().model_dump())
    assert combined["outputs"]["combined_corrosion_rate_m_year"] > 0.0
    assert combined["outputs"]["thinning_damage_factor"] > 0.0
    assert risk["outputs"]["financial_risk_per_year"] >= 0.0


def test_tank_shell_level2_case_and_summary_public_boundaries():
    one = evaluate("tank/shell-level2-case", case().model_dump())
    summary_input = tank.ShellLevel2SummaryInput(cases=[case(hole=h) for h in ("small", "medium", "large", "rupture")])
    summary = evaluate("tank/shell-level2-summary", summary_input.model_dump())
    assert one["outputs"]["flammable_personnel_area_m2"] > 0.0
    assert summary["outputs"]["consequence_area_m2"] > 0.0


def test_tank_diked_pool_consequence_public_boundary():
    result = evaluate("tank/diked-pool-consequence", pool().model_dump())
    assert result["outputs"]["pool_area_m2"] > 0.0
    assert result["outputs"]["personnel_area_m2"] >= 0.0

