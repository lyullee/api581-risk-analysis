import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def test_supporting_text_review_covers_every_unimplemented_supporting_clause():
    subprocess.run([sys.executable, "scripts/build_supporting_text_review.py"], cwd=ROOT, check=True)
    def read_json_stable(path: Path):
        # PBS workers may observe a short-lived zero-length file while a
        # sibling documentary gate is replacing generated evidence. Retry
        # the read instead of turning that filesystem race into a numerical
        # regression failure.
        for attempt in range(5):
            try:
                text = path.read_text(encoding="utf-8")
                if text.strip():
                    return json.loads(text)
            except (OSError, json.JSONDecodeError):
                pass
            time.sleep(0.02 * (attempt + 1))
        return json.loads(path.read_text(encoding="utf-8"))

    report = read_json_stable(ROOT / "docs/supporting-text-review.json")
    remaining = read_json_stable(ROOT / "docs/remaining-work.json")
    expected = {c["id"] for c in remaining["clauses"] if c.get("status") == "not_implemented"}
    actual = {c["clause_id"] for c in report["clauses"]}
    assert actual == expected
    assert report["supporting_not_implemented_count"] == 76
    assert report["source_document"]["fingerprint_matches_standard_metadata"] is True
    assert all(item["source_locator"]["pdf"] == "API-581-2016.pdf" for item in report["clauses"])
    assert set(report["classification_counts"]) == {
        "engineering_damage_review", "metadata_reference_review",
        "metadata_terminology_review", "workflow_scope_review",
    }
    assert all(len(item["source_locator"]["extracted_page_text_sha256"]) == 64 for item in report["clauses"])
    assert all(item["source_locator"]["extracted_page_text_bytes"] >= 0 for item in report["clauses"])


def test_packaged_supporting_text_review_is_queryable_and_bidirectionally_traced():
    from api581.standard import supporting_text_review
    items = supporting_text_review()
    assert len(items) == 76
    assert len({item.clause_id for item in items}) == 76
    item = supporting_text_review("Part 2 §6.8")[0]
    assert item.review_category == "supporting_text_review"
    assert item.source_locator.pdf == "API-581-2016.pdf"
    assert len(item.source_locator.extracted_page_text_sha256) == 64
