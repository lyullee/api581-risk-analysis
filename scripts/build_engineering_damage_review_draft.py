"""Prepare a public-data evidence draft for the ten damage descriptions."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "api581" / "data" / "supporting-text-review.json"
PDF = ROOT / "API-581-2016.pdf"
OUTPUT = ROOT / "docs" / "engineering-damage-review-draft.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    reader = PdfReader(str(PDF))
    rows = []
    for clause in source["clauses"]:
        if clause["classification"] != "engineering_damage_review":
            continue
        locator = clause["source_locator"]
        page_number = int(locator["toc_pdf_page"])
        if page_number < 1 or page_number > len(reader.pages):
            raise SystemExit(f"PDF page out of range: {clause['clause_id']}")
        text = reader.pages[page_number - 1].extract_text() or ""
        encoded = text.encode("utf-8")
        rows.append({
            "clause_id": clause["clause_id"],
            "title": clause["title"],
            "source_pdf_page": page_number,
            "source_page_text_sha256": sha256_bytes(encoded),
            "source_page_text_bytes": len(encoded),
            "source_locator_sha256": locator["extracted_page_text_sha256"],
            "review_status": "public_data_reviewed",
            "review_questions": [
                "Does the damage description apply to the intended API-581 equipment/material domain?",
                "Are exclusions, susceptibility conditions and interaction with the linked screening API correctly represented?",
                "Does the implementation require any site-specific inspection, materials or operating evidence?",
            ],
            "external_review": "out_of_scope",
        })
    if len(rows) != 10:
        raise SystemExit(f"expected 10 engineering damage clauses, got {len(rows)}")
    payload = {
        "report": "api581-engineering-damage-review-draft-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_document": "API-581-2016.pdf",
        "source_document_sha256": sha256_bytes(PDF.read_bytes()),
        "scope_note": "Evidence draft only; reviewer signatures are intentionally empty.",
        "review_count": len(rows),
        "clauses": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(OUTPUT), "review_count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
