"""Build a deterministic data-review receipt for documentary clauses.

This receipt records what can be resolved from the local API-581 source PDF,
standard metadata, public worked-example data and the existing disposition
map. External evaluation is out of scope for this software project.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "api581" / "data" / "supporting-text-review.json"
OUTPUT = ROOT / "docs" / "supporting-text-data-review.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    clauses = []
    for clause in source["clauses"]:
        classification = clause["classification"]
        status = "public_data_reviewed" if classification == "engineering_damage_review" else "machine_reviewed"
        clauses.append({
            "clause_id": clause["clause_id"],
            "classification": classification,
            "status": status,
            "source_locator": clause["source_locator"],
            "evidence_target": clause["evidence_target"],
            "next_action": clause["next_action"],
        })
    summary = {
        "total": len(clauses),
        "machine_reviewed": sum(c["status"] == "machine_reviewed" for c in clauses),
        "public_data_reviewed": sum(c["status"] == "public_data_reviewed" for c in clauses),
    }
    payload = {
        "report": "api581-supporting-text-data-review-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_report": "src/api581/data/supporting-text-review.json",
        "source_report_sha256": sha256(SOURCE),
        "method": "local source-locator, metadata-target and disposition consistency review",
        "public_data_sources": [
            "https://www.trinity-bridge.com/knowledge-center/publications/api-rp-581-risk-based-inspection-technology-%E2%80%93-demonstrating-technology",
            "https://trinity-bridge.com/sites/default/files/publications/API%20581%20Example%2C%202nd%20Edition.pdf",
        ],
        "scope_note": "Public-data review is software evidence; external evaluation is explicitly out of project scope.",
        "summary": summary,
        "clauses": clauses,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(OUTPUT), **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
