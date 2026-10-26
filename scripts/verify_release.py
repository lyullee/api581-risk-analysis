"""Verify generated public contracts and packaged source coverage before release."""
from __future__ import annotations

import json
import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
# Allow the gate to run from a fresh checkout before an editable install exists.
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import api581


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-evidence", action="store_true",
        help="write the deterministic release evidence manifest",
    )
    args = parser.parse_args()
    schema = json.loads((ROOT / "docs/python-api.schema.json").read_text(encoding="utf-8"))
    twin_schema_path = ROOT / "docs/digital-twin.schema.json"
    standard_schema_path = ROOT / "docs/standard.schema.json"
    scope_schema_path = ROOT / "docs/scope-boundaries.schema.json"
    packaged_schema_path = ROOT / "src/api581/data/python-api.schema.json"
    packaged_twin_schema_path = ROOT / "src/api581/data/digital-twin.schema.json"
    packaged_standard_schema_path = ROOT / "src/api581/data/standard.schema.json"
    packaged_scope_schema_path = ROOT / "src/api581/data/scope-boundaries.schema.json"
    software_test_evidence_path = ROOT / "docs/software-test-evidence.json"
    packaged_software_test_evidence_path = ROOT / "src/api581/data/software-test-evidence.json"
    reference_fixture_evidence_path = ROOT / "docs/reference-fixture-evidence.json"
    packaged_reference_fixture_evidence_path = ROOT / "src/api581/data/reference-fixture-evidence.json"
    native_evidence_path = ROOT / "docs/NATIVE_ENGINE_EVIDENCE.json"
    packaged_native_evidence_path = ROOT / "src/api581/data/native-engine-evidence.json"
    standard_metadata_path = ROOT / "src/api581/data/standard-metadata.json"
    completion_audit_path = ROOT / "docs/COMPLETION_AUDIT.md"
    supporting_disposition_path = ROOT / "docs/SUPPORTING_TEXT_DISPOSITIONS.md"
    supporting_review_path = ROOT / "src/api581/data/supporting-text-review.json"
    twin_schema = json.loads(twin_schema_path.read_text(encoding="utf-8"))
    standard_schema = json.loads(standard_schema_path.read_text(encoding="utf-8"))
    scope_schema = json.loads(scope_schema_path.read_text(encoding="utf-8"))
    software_test_evidence = json.loads(software_test_evidence_path.read_text(encoding="utf-8"))
    reference_fixture_evidence = json.loads(reference_fixture_evidence_path.read_text(encoding="utf-8"))
    standard_metadata = json.loads(standard_metadata_path.read_text(encoding="utf-8"))
    supporting_review = json.loads(supporting_review_path.read_text(encoding="utf-8"))
    disposition_classes = {
        "metadata_reference_review", "metadata_terminology_review",
        "workflow_scope_review", "engineering_damage_review",
    }
    if not supporting_disposition_path.is_file() or len(supporting_review.get("clauses", [])) != 76:
        raise SystemExit("Supporting-text disposition ledger is missing or stale")
    if any(item.get("classification") not in disposition_classes for item in supporting_review["clauses"]):
        raise SystemExit("Supporting-text disposition contains an unknown classification")
    if any(
        not item.get("source_locator")
        or not item.get("evidence_target")
        or not item.get("next_action")
        or item.get("calculation_ids")
        for item in supporting_review["clauses"]
    ):
        raise SystemExit("Supporting-text disposition contains an incomplete documentary record")
    expected_standard_models = {
        "StandardDefinition", "StandardAcronym", "StandardReference", "StandardSection", "DocumentaryCoverage",
    }
    if set(standard_schema) != expected_standard_models:
        raise SystemExit("Generated standard schema IDs do not match runtime contract IDs")
    if set(scope_schema) != {"ScopeBoundary"}:
        raise SystemExit("Generated scope-boundary schema IDs do not match runtime contract IDs")
    expected_twin_models = {
        "TwinMeasurement", "TwinCalculationRequest", "TwinCalculationResponse",
        "TwinBatchShard", "TwinBatchPlan",
    }
    if set(twin_schema) != expected_twin_models:
        raise SystemExit("Generated digital-twin schema IDs do not match runtime contract IDs")
    if _sha256(packaged_schema_path) != _sha256(ROOT / "docs/python-api.schema.json"):
        raise SystemExit("Packaged Python API schema is out of sync with docs schema")
    if _sha256(packaged_twin_schema_path) != _sha256(twin_schema_path):
        raise SystemExit("Packaged digital-twin schema is out of sync with docs schema")
    if _sha256(packaged_standard_schema_path) != _sha256(standard_schema_path):
        raise SystemExit("Packaged standard schema is out of sync with docs schema")
    if _sha256(packaged_scope_schema_path) != _sha256(scope_schema_path):
        raise SystemExit("Packaged scope-boundary schema is out of sync with docs schema")
    if _sha256(packaged_software_test_evidence_path) != _sha256(software_test_evidence_path):
        raise SystemExit("Packaged software-test evidence is out of sync with docs evidence")
    if _sha256(packaged_reference_fixture_evidence_path) != _sha256(reference_fixture_evidence_path):
        raise SystemExit("Packaged reference-fixture evidence is out of sync with docs evidence")
    if software_test_evidence.get("calculation_count") != len(api581.list_calculations()):
        raise SystemExit("Software-test evidence calculation count is stale")
    if set(software_test_evidence.get("calculations", {})) != {
        item.identifier for item in api581.list_calculations()
    }:
        raise SystemExit("Software-test evidence IDs do not match runtime calculation IDs")
    reference_fixture_ids = set(reference_fixture_evidence.get("fixtures", {}))
    if not reference_fixture_ids <= {item.identifier for item in api581.list_calculations()}:
        raise SystemExit("Reference-fixture evidence contains unknown calculation IDs")
    reference_fixture_count = sum(len(items) for items in reference_fixture_evidence.get("fixtures", {}).values())
    direct_test_reference_count = sum(
        bool(paths) for paths in software_test_evidence["calculations"].values()
    )
    direct_public_test_reference_count = sum(
        bool(paths) for paths in software_test_evidence.get("direct_public_test_calculations", {}).values()
    )
    if standard_metadata.get("standard_edition") != "API-RP-581-2016-3rd-base":
        raise SystemExit("Standard metadata edition is not API-RP-581-2016-3rd-base")
    if (len(standard_metadata.get("definitions", [])) != 80
            or len(standard_metadata.get("acronyms", [])) != 125
            or len(standard_metadata.get("references", [])) != 22):
        raise SystemExit("Standard metadata table counts do not match the qualified source extraction")
    try:
        native_evidence = json.loads(native_evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Native engine evidence manifest is unreadable: {native_evidence_path}") from exc
    if _sha256(packaged_native_evidence_path) != _sha256(native_evidence_path):
        raise SystemExit("Packaged native engine evidence is out of sync with docs evidence")
    if not completion_audit_path.is_file():
        raise SystemExit("Completion audit document is missing")
    required_native_versions = {"slabx": "1.0.8", "slabx-lh2": "0.2.0", "CoolProp": "8.0.0"}
    if native_evidence.get("environment", {}) != {
        **required_native_versions,
        "numpy": "2.5.3",
        "scipy": "1.18.1",
    }:
        raise SystemExit("Native engine evidence environment does not match the qualified fixture")
    fingerprints = native_evidence.get("engine_source_fingerprints", {})
    if set(fingerprints) != {"slabx", "slabx-lh2"} or any(
        not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in fingerprints.values()
    ):
        raise SystemExit("Native engine evidence source fingerprints are incomplete or malformed")
    runs = native_evidence.get("runs", {})
    expected_native_runs = {
        "verify_native_dispersion.py", "verify_native_jet.py",
        "verify_native_footprint.py", "verify_native_toxic.py",
        "verify_native_saturation.py", "verify_native_flash.py",
        "verify_native_flash_pool.py", "verify_native_flashed_pool_footprint.py",
        "verify_native_flashed_pool_risk.py",
    }
    if set(runs) != expected_native_runs or any(item.get("status") != "passed" for item in runs.values()):
        raise SystemExit("Native engine evidence contains an incomplete or failed run")
    calculations = api581.list_calculations()
    audit = api581.audit_coverage()
    if set(schema) != {item.identifier for item in calculations}:
        raise SystemExit("Generated schema IDs do not match runtime calculation IDs")
    if not audit["ok"]:
        raise SystemExit(f"Coverage audit failed: {audit}")
    summary = api581.coverage_summary()
    documentary = api581.standard.documentary_coverage()
    if (documentary.metadata_covered_count != 6
            or documentary.supporting_review_count != 170
            or documentary.unimplemented_supporting_count != 76):
        raise SystemExit("Documentary coverage counts do not match the qualified source extraction")
    unimplemented_sections = api581.standard.sections(status="not_implemented")
    if len(unimplemented_sections) != 76 or any(
        item.review_category != "supporting_text_review" for item in unimplemented_sections
    ):
        raise SystemExit("Not-implemented source sections must remain supporting-text review items")
    scope_total = sum(sum(bucket.values()) for bucket in summary["scope_status_counts"].values())
    if scope_total != summary["section_count"]:
        raise SystemExit("Scope status counts do not sum to the packaged section count")
    domain_total = sum(
        bucket["native_engine_fixture_verified"] + bucket["software_tested_only"]
        for bucket in summary["validation_by_domain"].values()
    )
    if domain_total != summary["calculation_count"]:
        raise SystemExit("Domain validation counts do not sum to the packaged calculation count")
    validation_counts = dict(Counter(
        item["validation_level"] for item in api581.validation_queue()
    ))
    scope_boundary_ids = [item.boundary_id for item in api581.scope_boundaries()]
    source_pdf = ROOT / "API-581-2016.pdf"
    source_document = None
    if source_pdf.exists():
        source_document = {
            "path": source_pdf.name,
            "size_bytes": source_pdf.stat().st_size,
            "sha256": _sha256(source_pdf),
        }
        if source_document["sha256"] != summary["source_sha256"]:
            raise SystemExit(
                "Source PDF fingerprint does not match packaged coverage inventory"
            )
        if standard_metadata.get("source_sha256") != source_document["sha256"]:
            raise SystemExit("Standard metadata fingerprint does not match source PDF")
    evidence = {
        "standard_edition": summary["standard_edition"],
        "calculation_count": len(calculations),
        "schema_count": len(schema),
        "digital_twin_schema_count": len(twin_schema),
        "standard_schema_count": len(standard_schema),
        "scope_schema_count": len(scope_schema),
        "section_count": summary["section_count"],
        "status_counts": summary["status_counts"],
        "scope_status_counts": summary["scope_status_counts"],
        "documentary_coverage": documentary.model_dump(mode="json"),
        "supporting_text_disposition": {
            "path": supporting_disposition_path.name,
            "clause_count": len(supporting_review["clauses"]),
            "classification_counts": dict(sorted(Counter(item["classification"] for item in supporting_review["clauses"]).items())),
        },
        "validation_counts": validation_counts,
        "validation_by_domain": summary["validation_by_domain"],
        "direct_test_counts": summary["direct_test_counts"],
        "software_test_direct_reference_count": direct_test_reference_count,
        "direct_public_test_reference_count": direct_public_test_reference_count,
        "direct_public_test_counts": summary["direct_public_test_counts"],
        "reference_fixture_count": reference_fixture_count,
        "scope_boundary_count": len(scope_boundary_ids),
        "unreferenced_calculation_ids": summary["unreferenced_calculation_ids"],
        "scope_boundary_ids": scope_boundary_ids,
        "unlinked_calculation_ids": summary["unlinked_calculation_ids"],
        "audit": audit,
        "artifact_sha256": {
            "python_api_schema": _sha256(ROOT / "docs/python-api.schema.json"),
            "digital_twin_schema": _sha256(twin_schema_path),
            "coverage": _sha256(ROOT / "src/api581/data/coverage.json"),
            "packaged_python_api_schema": _sha256(packaged_schema_path),
            "packaged_digital_twin_schema": _sha256(packaged_twin_schema_path),
            "standard_schema": _sha256(standard_schema_path),
            "packaged_standard_schema": _sha256(packaged_standard_schema_path),
            "scope_boundaries_schema": _sha256(scope_schema_path),
            "packaged_scope_boundaries_schema": _sha256(packaged_scope_schema_path),
            "software_test_evidence": _sha256(software_test_evidence_path),
            "packaged_software_test_evidence": _sha256(packaged_software_test_evidence_path),
            "reference_fixture_evidence": _sha256(reference_fixture_evidence_path),
            "packaged_reference_fixture_evidence": _sha256(packaged_reference_fixture_evidence_path),
            "standard_metadata": _sha256(standard_metadata_path),
            "native_engine_evidence": _sha256(native_evidence_path),
            "packaged_native_engine_evidence": _sha256(packaged_native_evidence_path),
            "completion_audit": _sha256(completion_audit_path),
            "supporting_text_review": _sha256(supporting_review_path),
            "supporting_text_dispositions": _sha256(supporting_disposition_path),
        },
        "source_document": source_document,
        "source_hash_matches_coverage": (
            source_document is None
            or source_document["sha256"] == summary["source_sha256"]
        ),
        "native_engine_evidence": {
            "path": native_evidence_path.name,
            "run_count": len(runs),
            "engine_source_fingerprints": native_evidence["engine_source_fingerprints"],
        },
    }
    if args.write_evidence:
        (ROOT / "docs/release-evidence.json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({
        "calculation_count": len(calculations),
        "schema_count": len(schema),
        "digital_twin_schema_count": len(twin_schema),
        "standard_schema_count": len(standard_schema),
        "scope_schema_count": len(scope_schema),
        "section_count": summary["section_count"],
        "status_counts": summary["status_counts"],
        "scope_status_counts": summary["scope_status_counts"],
        "documentary_coverage": {
            "metadata_covered_count": documentary.metadata_covered_count,
            "supporting_review_count": documentary.supporting_review_count,
            "unimplemented_supporting_count": documentary.unimplemented_supporting_count,
        },
        "validation_counts": validation_counts,
        "validation_by_domain": summary["validation_by_domain"],
        "direct_test_counts": summary["direct_test_counts"],
        "software_test_direct_reference_count": direct_test_reference_count,
        "direct_public_test_reference_count": direct_public_test_reference_count,
        "direct_public_test_counts": summary["direct_public_test_counts"],
        "reference_fixture_count": reference_fixture_count,
        "scope_boundary_count": len(scope_boundary_ids),
        "unreferenced_calculation_ids": summary["unreferenced_calculation_ids"],
        "unlinked_calculation_ids": summary["unlinked_calculation_ids"],
        "audit_ok": audit["ok"],
        "source_hash_matches_coverage": evidence["source_hash_matches_coverage"],
        "native_evidence_run_count": len(runs),
        "evidence_written": args.write_evidence,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
