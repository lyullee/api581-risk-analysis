"""Verify release-manifest hashes and the selected terminal verification receipts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_wheel_data(wheel_path: Path) -> None:
    """Ensure the distributable wheel embeds the exact current evidence data."""
    expected = (
        "python-api.schema.json", "digital-twin.schema.json",
        "standard.schema.json", "scope-boundaries.schema.json",
        "standard-metadata.json", "native-engine-evidence.json",
        "software-test-evidence.json", "reference-fixture-evidence.json",
        "direct-test-queue.json",
    )
    try:
        with zipfile.ZipFile(wheel_path) as archive:
            names = set(archive.namelist())
            for filename in expected:
                member = f"api581/data/{filename}"
                source = ROOT / "src/api581/data" / filename
                if member not in names or archive.read(member) != source.read_bytes():
                    raise SystemExit(f"wheel packaged data drift: {filename}")
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"wheel is not a readable zip archive: {wheel_path}") from exc


def main() -> int:
    manifest = json.loads((ROOT / "docs/release-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("manifest") != "api581-release-provenance-v1":
        raise SystemExit("unsupported release manifest")
    report_rel = next(item["path"] for item in manifest["evidence_artifacts"]
                      if item["path"].startswith("tmp/nurion-parallel-"))
    report = json.loads((ROOT / report_rel).read_text(encoding="utf-8"))
    expected = {"total": 64, "passed": 64, "failed": 0, "timed_out": 0, "running": 0}
    if report.get("collector") != "api581.nurion_reconcile" or not str(report.get("run_id", "")).endswith("-reconciled") or report.get("summary") != expected:
        raise SystemExit("release manifest does not point to a terminal-green reconciled receipt")
    shards = report.get("shards", [])
    if len(shards) != 64 or sorted((str(x.get("index")) for x in shards), key=int) != [str(i) for i in range(64)] or any(x.get("status") != "passed" for x in shards):
        raise SystemExit("reconciled receipt is missing passed shard indices")
    efficient_entries = [
        item for item in manifest["evidence_artifacts"]
        if item["path"].startswith("tmp/nurion-efficient-") and item["path"].endswith(".json")
    ]
    if not efficient_entries:
        raise SystemExit("release manifest is missing the efficient Nurion receipt")
    efficient = json.loads((ROOT / efficient_entries[-1]["path"]).read_text(encoding="utf-8"))
    efficient_expected = {"total": 10, "passed": 10, "failed": 0, "timed_out": 0, "running": 0}
    if efficient.get("collector") != "api581.nurion_parallel_collect" or efficient.get("summary") != efficient_expected:
        raise SystemExit("efficient Nurion receipt is not terminal-green")
    audit_entries = [item for item in manifest["evidence_artifacts"] if item["path"] == "tmp/final-audit-latest.json"]
    if not audit_entries:
        raise SystemExit("release manifest is missing the final audit report")
    final_audit = json.loads((ROOT / audit_entries[0]["path"]).read_text(encoding="utf-8"))
    if final_audit.get("report") != "api581-final-audit-v1" or final_audit.get("status") != "passed":
        raise SystemExit("final audit report is not green")
    for entry in manifest["package_artifacts"] + manifest["evidence_artifacts"]:
        path = ROOT / entry["path"]
        if not path.is_file() or path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise SystemExit(f"release manifest hash/size mismatch: {entry['path']}")
    wheels = [ROOT / entry["path"] for entry in manifest["package_artifacts"] if entry["path"].endswith(".whl")]
    if len(wheels) != 1:
        raise SystemExit("release manifest must contain exactly one wheel artifact")
    verify_wheel_data(wheels[0])
    native = json.loads((ROOT / "docs/NATIVE_ENGINE_EVIDENCE.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "src/api581/data/native-engine-evidence.json").read_text(encoding="utf-8"))
    if native != packaged:
        raise SystemExit("packaged native evidence differs from source manifest")
    # Supporting-text evidence must point to the same canonical PDF and
    # standard metadata fingerprint used by the source inventory.  The report
    # is hash-pinned above; this check also validates its internal provenance
    # fields rather than trusting the filename alone.
    supporting = json.loads((ROOT / "docs/supporting-text-review.json").read_text(encoding="utf-8"))
    data_review = json.loads((ROOT / "docs/supporting-text-data-review.json").read_text(encoding="utf-8"))
    if (data_review.get("report") != "api581-supporting-text-data-review-v1"
            or data_review.get("summary") != {"total": 76, "machine_reviewed": 66, "public_data_reviewed": 10}):
        raise SystemExit("supporting-text data review receipt is not the expected 66/10 public-data split")
    damage_draft = json.loads((ROOT / "docs/engineering-damage-review-draft.json").read_text(encoding="utf-8"))
    if (damage_draft.get("report") != "api581-engineering-damage-review-draft-v1"
            or damage_draft.get("review_count") != 10
            or any(item.get("review_status") != "public_data_reviewed" or item.get("external_review") != "out_of_scope"
                   for item in damage_draft.get("clauses", []))):
        raise SystemExit("engineering damage review draft is not an explicit public-data 10-clause receipt")
    signoff_template = (ROOT / "docs/ENGINEERING_REVIEW_SIGNOFF_TEMPLATE.md").read_text(encoding="utf-8")
    template_lower = signoff_template.lower()
    if "external evaluation" not in template_lower or "out of scope" not in template_lower:
        raise SystemExit("engineering review scope template does not exclude external evaluation")
    metadata = json.loads((ROOT / "src/api581/data/standard-metadata.json").read_text(encoding="utf-8"))
    source_pdf = ROOT / "API-581-2016.pdf"
    if not source_pdf.is_file():
        raise SystemExit("canonical API-581 source PDF is missing")
    source_hash = sha256(source_pdf)
    source_info = supporting.get("source_document", {})
    if (source_info.get("filename") != source_pdf.name
            or source_info.get("bytes") != source_pdf.stat().st_size
            or source_info.get("sha256") != source_hash
            or source_info.get("sha256") != metadata.get("source_sha256")
            or source_info.get("fingerprint_matches_standard_metadata") is not True):
        raise SystemExit("supporting-text source fingerprint does not match canonical metadata")
    suite = json.loads((ROOT / "tmp/native-suite-latest.json").read_text(encoding="utf-8"))
    if suite.get("status") != "passed" or len(suite.get("scripts", [])) != 9 or any(x.get("status") != "passed" for x in suite["scripts"]):
        raise SystemExit("native suite receipt is not 9/9 passed")
    matrix = json.loads((ROOT / "docs/completion-matrix.json").read_text(encoding="utf-8"))
    required = {"nurion_parallel_regression", "nurion_efficient_regression", "slabx_native_contracts", "release_artifacts"}
    rows = {x["requirement"]: x for x in matrix["requirements"]}
    if any(rows.get(key, {}).get("status") != "passed" for key in required):
        raise SystemExit("completion matrix verification requirements are not passed")
    # The handoff packet is itself a traceability artifact.  Ensure it names
    # the exact receipt and package selected above and keeps the external
    # certification disclaimer/checklist visible to an independent reviewer.
    packet_path = ROOT / "docs/INDEPENDENT_ENGINEERING_REVIEW_PACKET.md"
    checklist_path = ROOT / "docs/INDEPENDENT_ENGINEERING_REVIEW_CHECKLIST.md"
    packet = packet_path.read_text(encoding="utf-8")
    if not checklist_path.is_file():
        raise SystemExit("independent engineering review checklist is missing")
    if report_rel not in packet:
        raise SystemExit("review packet does not reference the selected reconciled receipt")
    package_dir = Path(manifest["package_artifacts"][0]["path"]).parent.as_posix()
    if package_dir not in packet:
        raise SystemExit("review packet does not reference the selected package artifact directory")
    if "software_verified_external_review_out_of_scope" not in packet:
        raise SystemExit("review packet must preserve the external-review-out-of-scope status")
    print(json.dumps({"status": "passed", "nurion_run_id": report["run_id"], "shards": 64, "native_scripts": 9}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
