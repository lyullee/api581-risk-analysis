"""Direct public evaluate() coverage for screened assessment workflows."""

import runpy

from api581 import evaluate
from test_amine_screening import request as amine_request


def test_damage_screened_assessments_public_boundaries():
    groundwater_request = runpy.run_path("examples/groundwater_to_thinning.py")["request"]()
    groundwater_assessment = evaluate("damage/groundwater-assessment", groundwater_request.corrosion.model_dump())
    groundwater_thinning = evaluate("damage/groundwater-thinning-assessment", groundwater_request.model_dump())
    caustic_request = runpy.run_path("examples/caustic_screened_assessment.py")["request"]()
    caustic = evaluate("damage/caustic-screened-assessment", caustic_request.model_dump())
    amine = evaluate("damage/amine-cracking-screened-assessment", amine_request().model_dump())
    assert groundwater_assessment["outputs"]
    assert groundwater_thinning["outputs"]
    assert caustic["outputs"]
    assert amine["outputs"]

