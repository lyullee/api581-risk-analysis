"""Direct public evaluate() coverage for mechanism-specific damage compositions."""

from api581 import evaluate

from test_acid_sour_water import request as acid_sour_request
from test_alkaline_sour_water import request as alkaline_sour_request
from test_hydrochloric_acid import assessment as hcl_assessment
from test_hydrofluoric_acid import request as hf_request
from test_sulfuric_acid import request as sulfuric_request
from test_h2sh2_corrosion import request as h2sh2_request
from test_sulfidic_corrosion import request as sulfidic_request


def test_damage_mechanism_assessment_public_boundaries():
    assert evaluate("damage/acid-sour-water-assessment", acid_sour_request().model_dump())["outputs"]
    assert evaluate("damage/alkaline-sour-water-assessment", alkaline_sour_request().model_dump())["outputs"]
    assert evaluate("damage/hcl-assessment", hcl_assessment().model_dump())["outputs"]
    assert evaluate("damage/hf-assessment", hf_request().model_dump())["outputs"]
    assert evaluate("damage/sulfuric-corrosion-assessment", sulfuric_request().model_dump())["outputs"]
    assert evaluate("damage/h2sh2-corrosion-assessment", h2sh2_request().model_dump())["outputs"]
    assert evaluate("damage/sulfidic-corrosion-assessment", sulfidic_request().model_dump())["outputs"]

