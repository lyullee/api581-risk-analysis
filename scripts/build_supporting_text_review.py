"""Classify supporting-text clauses without pretending they are calculations.

The source ledger intentionally retains reference, nomenclature, overview and
damage-description headings.  This report makes the next evidence action
machine-readable and checks that every currently unimplemented supporting
heading has a review route.
"""
from __future__ import annotations

import json
from hashlib import sha256
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "docs" / "remaining-work.json"
METADATA = ROOT / "src" / "api581" / "data" / "standard-metadata.json"
SOURCE_PDF = ROOT / "API-581-2016.pdf"
SOURCE_TEXT = ROOT / "tmp" / "pdfs" / "API-581-2016.txt"
OUTPUT = ROOT / "docs" / "supporting-text-review.json"
PACKAGED_OUTPUT = ROOT / "src" / "api581" / "data" / "supporting-text-review.json"


def source_page_text() -> dict[int, str]:
    """Return canonical extracted text by PDF page for reproducible locators."""
    if not SOURCE_TEXT.is_file():
        return {}
    chunks = SOURCE_TEXT.read_text(encoding="utf-8").split("=== PDF PAGE ")
    pages: dict[int, str] = {}
    for chunk in chunks[1:]:
        header, _, body = chunk.partition(" ===")
        try:
            pages[int(header.strip())] = body.strip()
        except ValueError:
            continue
    return pages


def classify(title: str) -> tuple[str, str, str]:
    normalized = title.strip().lower()
    if normalized in {"references", "normative", "informative"}:
        return (
            "metadata_reference_review",
            "standard-metadata.references",
            "Map cited edition and normative/informative role; do not create a calculation API from a reference heading.",
        )
    if normalized in {"nomenclature", "definitions", "definitions and acronyms", "acronyms"}:
        return (
            "metadata_terminology_review",
            "standard-metadata.definitions/acronyms",
            "Reconcile terms and units with packaged metadata; create a typed API only when a calculation-affecting requirement is identified.",
        )
    if normalized in {"scope", "overview"}:
        return (
            "workflow_scope_review",
            "catalog.scope_boundaries and integration workflows",
            "Record applicability and exclusions, then link actionable requirements to an existing API or explicit boundary.",
        )
    if normalized == "description of damage":
        return (
            "engineering_damage_review",
            "damage screening/assessment APIs plus public worked-example data",
            "Compare mechanism description with screening and assessment coverage; unsupported mechanisms require explicit engineering disposition.",
        )
    return (
        "manual_source_review",
        "API-RP-581 source text",
        "Review the source clause before deciding whether metadata, workflow, calculation, or boundary evidence is needed.",
    )


def main() -> int:
    ledger = json.loads(INPUT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    pages = source_page_text()
    clauses = [c for c in ledger["clauses"] if c.get("status") == "not_implemented"]
    records = []
    for clause in clauses:
        category, evidence, action = classify(clause["title"])
        page = clause.get("toc_pdf_page")
        excerpt = pages.get(int(page), "") if page is not None else ""
        records.append({
            "clause_id": clause["id"],
            "title": clause["title"],
            "scope": clause.get("scope"),
            "source_locator": {
                "pdf": SOURCE_PDF.name,
                "toc_pdf_page": clause.get("toc_pdf_page"),
                "printed_page_in_part": clause.get("printed_page_in_part"),
                "extracted_page_text_sha256": sha256(excerpt.encode("utf-8")).hexdigest(),
                "extracted_page_text_bytes": len(excerpt.encode("utf-8")),
            },
            "review_category": clause.get("review_category"),
            "classification": category,
            "evidence_target": evidence,
            "next_action": action,
            "calculation_ids": clause.get("calculation_ids", []),
        })
    counts = Counter(r["classification"] for r in records)
    report = {
        "standard_edition": metadata["standard_edition"],
        "source_sha256": metadata["source_sha256"],
        "source_document": {
            "filename": SOURCE_PDF.name,
            "bytes": SOURCE_PDF.stat().st_size,
            "sha256": sha256(SOURCE_PDF.read_bytes()).hexdigest(),
            "fingerprint_matches_standard_metadata": sha256(SOURCE_PDF.read_bytes()).hexdigest() == metadata["source_sha256"],
            "locator_basis": "coverage.json toc_pdf_page and printed_page_in_part; page numbers are source-navigation evidence, not extracted calculation equations",
            "text_locator_basis": "SHA-256 of the canonical extracted text for toc_pdf_page; empty text is represented by the SHA-256 of an empty string",
        },
        "supporting_not_implemented_count": len(records),
        "classification_counts": dict(sorted(counts.items())),
        "metadata_inventory": {
            "references": len(metadata["references"]),
            "definitions": len(metadata["definitions"]),
            "acronyms": len(metadata["acronyms"]),
        },
        "interpretation": "Classification is an evidence-routing aid, not an implementation percentage or certification claim.",
        "clauses": records,
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    OUTPUT.write_text(encoded, encoding="utf-8")
    PACKAGED_OUTPUT.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": "passed", "count": len(records), "classification_counts": dict(sorted(counts.items()))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
