"""Verify the machine-review receipt without treating it as certification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "supporting-text-data-review.json"
SOURCE = ROOT / "src" / "api581" / "data" / "supporting-text-review.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    clauses = report.get("clauses", [])
    source_ids = {item["clause_id"] for item in source.get("clauses", [])}
    report_ids = {item.get("clause_id") for item in clauses}
    if report.get("report") != "api581-supporting-text-data-review-v1":
        raise SystemExit("unsupported supporting-text data review report")
    if report.get("source_report_sha256") != sha256(SOURCE):
        raise SystemExit("supporting-text data review source hash drift")
    if report_ids != source_ids or len(clauses) != 76:
        raise SystemExit("supporting-text data review clause set drift")
    for clause in clauses:
        if clause.get("status") not in {"machine_reviewed", "public_data_reviewed"}:
            raise SystemExit(f"invalid data review status: {clause.get('clause_id')}")
        if not clause.get("source_locator") or not clause.get("evidence_target") or not clause.get("next_action"):
            raise SystemExit(f"incomplete data review evidence: {clause.get('clause_id')}")
    expected = {
        "total": 76,
        "machine_reviewed": 66,
        "public_data_reviewed": 10,
    }
    if report.get("summary") != expected:
        raise SystemExit(f"unexpected data review summary: {report.get('summary')}")
    print(json.dumps({"status": "passed", **expected}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
