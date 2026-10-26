"""Verify that every documentary supporting-text clause has an explicit disposition policy."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "src" / "api581" / "data" / "supporting-text-review.json"

POLICIES = {
    "metadata_reference_review": "standard-metadata.references",
    "metadata_terminology_review": "standard-metadata.definitions/acronyms",
    "workflow_scope_review": "catalog.scope_boundaries and integration workflows",
    "engineering_damage_review": "damage screening/assessment APIs plus independent engineering review",
}


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    clauses = report["clauses"]
    missing = [c["clause_id"] for c in clauses if c.get("classification") not in POLICIES]
    if missing:
        raise SystemExit(f"missing disposition policy: {missing}")
    incomplete = [
        c["clause_id"] for c in clauses
        if not c.get("source_locator") or not c.get("evidence_target")
        or not c.get("next_action") or c.get("calculation_ids")
    ]
    if incomplete:
        raise SystemExit(f"incomplete documentary disposition record: {incomplete}")
    counts = {key: sum(c.get("classification") == key for c in clauses) for key in POLICIES}
    print(json.dumps({"status": "passed", "clause_count": len(clauses), "classification_counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
