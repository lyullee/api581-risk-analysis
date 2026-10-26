"""Validate that remaining non-calculation clauses are explicitly queued.

This gate prevents documentary references, nomenclature, scope and overview
clauses from being mistaken for missing calculation implementations. It does
not mark those clauses complete; it checks that each has a review category and
an actionable next-evidence description.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = json.loads((ROOT / "docs" / "remaining-work.json").read_text(encoding="utf-8"))
    clauses = payload.get("clauses", [])
    pending = [item for item in clauses if item.get("status") == "not_implemented"]
    errors: list[str] = []
    for item in pending:
        clause_id = item.get("id", "<unknown>")
        if item.get("review_category") != "supporting_text_review":
            errors.append(f"{clause_id}: not_implemented is not supporting_text_review")
        if item.get("calculation_ids") or item.get("assigned_calculation_ids") or item.get("descendant_calculation_ids"):
            errors.append(f"{clause_id}: pending documentary clause has calculation links")
        if not str(item.get("next_evidence_needed", "")).strip():
            errors.append(f"{clause_id}: next_evidence_needed is blank")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({"status": "passed", "pending_supporting_text_clauses": len(pending),
                      "calculation_implementation_gaps": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
