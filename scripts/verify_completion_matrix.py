"""Validate the committed requirement completion matrix semantics."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"passed", "pending_review", "pending_external", "failed"}
EXTERNAL = set()


def main() -> int:
    payload = json.loads((ROOT / "docs" / "completion-matrix.json").read_text(encoding="utf-8"))
    rows = payload.get("requirements", [])
    ids = {row.get("requirement") for row in rows}
    errors: list[str] = []
    if payload.get("certification_status") != "software_verified_external_review_out_of_scope":
        errors.append("certification status must explicitly exclude external review")
    if len(rows) != 11 or len(ids) != len(rows):
        errors.append("matrix must contain 11 unique requirements")
    for row in rows:
        if row.get("status") not in ALLOWED:
            errors.append(f"invalid status for {row.get('requirement')}")
        evidence = str(row.get("evidence", "")).strip()
        if not evidence:
            errors.append(f"missing evidence for {row.get('requirement')}")
            continue
        # Evidence strings may include a short parenthetical description. If
        # their leading token names a JSON receipt, require that exact file to
        # exist. This prevents a stale/nonexistent path from being treated as
        # traceability evidence (the previous matrix builder emitted one).
        token = evidence.split()[0]
        if token.endswith(".json"):
            candidate = Path(token)
            if not candidate.is_absolute():
                if token in {"release-evidence.json", "release-manifest.json", "completion-matrix.json"}:
                    candidate = ROOT / "docs" / token
                else:
                    candidate = ROOT / candidate
            if not candidate.is_file():
                errors.append(f"evidence file does not exist for {row.get('requirement')}: {token}")
    review_row = next((row for row in rows if row.get("requirement") == "supporting_text_review_queue"), None)
    if review_row is None or review_row.get("status") != "passed":
        errors.append("supporting_text_review_queue must be passed from the public-data review receipt")
    for requirement in EXTERNAL:
        row = next((item for item in rows if item.get("requirement") == requirement), None)
        if row is None or row.get("status") != "pending_external":
            errors.append(f"external requirement {requirement} must remain pending_external")
    if errors:
        raise SystemExit("\n".join(errors))
    print(json.dumps({
        "status": "passed",
        "requirement_count": len(rows),
        "external_pending": len(EXTERNAL),
        "pending_review": sum(row.get("status") == "pending_review" for row in rows),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
