"""Direct public evaluate() coverage for thinning and cooling-water selection APIs."""

from api581 import evaluate
from api581.api import damage

from test_cooling_selection import treated, measurement, select
from test_thinning_selection import choice
from test_thinning_history import history


def test_cooling_water_selection_primitives_public_boundaries():
    bounds = evaluate("damage/cooling-water-treatment-bounds", treated())
    other = evaluate("damage/cooling-water-other-material-estimate", {
        "material": "other_material", "qualified_for_resistant_material_nominal_estimate": True,
        "other_degradation_assessed": True, "applicability_basis": "Qualified public alloy fixture",
    })
    measured = evaluate("damage/cooling-water-measured-rate", {
        "assessment_distribution": "local", "measurement": measurement(),
    })
    selection = evaluate("damage/cooling-water-rate-selection", select().model_dump())
    system = evaluate("damage/cooling-water-system-type", {
        "system": "closed_recirculated", "water_source": "fresh", "reuses_heated_water": True,
        "continual_makeup_required": False, "blowdown_or_evaporation_loss": False,
        "qualification_basis": "Qualified public closed-loop fixture",
    })
    assert bounds["outputs"]["general_upper_bound_m_year"] > 0.0
    assert other["outputs"]["nominal_corrosion_rate_m_year"] > 0.0
    assert measured["outputs"]["corrosion_rate_m_year"] >= 0.0
    assert selection["outputs"]["corrosion_rate_m_year"] >= 0.0
    assert system["outputs"]["requires_continual_makeup"] is False


def test_thinning_selection_and_history_public_boundaries():
    selected = evaluate("damage/thinning-rate-selection", choice().model_dump())
    history_result = evaluate("damage/thinning-inspection-history", history().model_dump())
    period_values = history().model_dump(include=set(damage.ThinningAssessmentPeriodInput.model_fields))
    period = evaluate("damage/thinning-assessment-period", period_values)
    assert selected["outputs"]["corrosion_rate_m_year"] >= 0.0
    assert history_result["outputs"]["elapsed_years"] >= 0.0
    assert period["outputs"]["elapsed_years"] >= 0.0

