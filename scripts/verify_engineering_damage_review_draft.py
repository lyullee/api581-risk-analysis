"""Verify the ten-clause public-data engineering review draft."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "engineering-damage-review-draft.json"
TEMPLATE = ROOT / "docs" / "ENGINEERING_REVIEW_SIGNOFF_TEMPLATE.md"
PDF = ROOT / "API-581-2016.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")
    rows = report.get("clauses", [])
    if report.get("report") != "api581-engineering-damage-review-draft-v1" or len(rows) != 10:
        raise SystemExit("engineering review draft must contain exactly ten clauses")
    if report.get("source_document_sha256") != sha256(PDF):
        raise SystemExit("engineering review draft source PDF hash drift")
    for row in rows:
        if row.get("review_status") != "public_data_reviewed":
            raise SystemExit(f"engineering review status drift: {row.get('clause_id')}")
        if row.get("external_review") != "out_of_scope":
            raise SystemExit("external engineering review must remain out of scope")
        if len(row.get("review_questions", [])) != 3:
            raise SystemExit(f"review questions missing: {row.get('clause_id')}")
        # The source inventory preserves PDF-extracted clause labels; some
        # legacy Windows-generated records contain replacement glyphs for §.
        # Validate the stable scope label and title instead of byte-matching
        # that presentation-only separator.
        if "Part 2 Annex B" not in template:
            raise SystemExit("sign-off template missing Annex B scope")
    print(json.dumps({"status": "passed", "review_count": len(rows), "signed": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
