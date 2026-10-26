import json
from pathlib import Path


def test_every_supporting_text_clause_has_explicit_disposition_policy():
    root = Path(__file__).parents[1]
    report = json.loads((root / "src/api581/data/supporting-text-review.json").read_text(encoding="utf-8"))
    policies = {
        "metadata_reference_review",
        "metadata_terminology_review",
        "workflow_scope_review",
        "engineering_damage_review",
    }
    assert len(report["clauses"]) == 76
    assert all(item["classification"] in policies for item in report["clauses"])
    assert all(
        item["source_locator"] and item["evidence_target"] and item["next_action"]
        and not item["calculation_ids"]
        for item in report["clauses"]
    )
