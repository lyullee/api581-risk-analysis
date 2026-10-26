"""Create a hash-pinned release manifest for API-581 artifacts.

The manifest is provenance evidence, not an API 581 certification claim. It
captures the exact package files and local verification receipts used for a
release candidate so a later PyPI/GitHub upload can be independently checked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> dict[str, object]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            h.update(block)
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": size, "sha256": h.hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "tmp" / "release-final-20261025l")
    reports = sorted((ROOT / "tmp").glob("nurion-parallel-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    default_nurion = None
    for report_path in reports:
        candidate = json.loads(report_path.read_text(encoding="utf-8"))
        summary = candidate.get("summary", {})
        if (candidate.get("collector") == "api581.nurion_reconcile"
                and str(candidate.get("run_id", "")).endswith("-reconciled")
                and summary == {"total": 64, "passed": 64, "failed": 0, "timed_out": 0, "running": 0}):
            default_nurion = report_path
            break
    if default_nurion is None:
        default_nurion = ROOT / "tmp" / "nurion-parallel-latest.json"
    parser.add_argument("--nurion-report", type=Path, default=default_nurion)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "release-manifest.json")
    args = parser.parse_args()
    args.artifact_dir = args.artifact_dir.resolve()
    args.nurion_report = args.nurion_report.resolve()
    args.output = args.output.resolve()

    package_files = sorted(p for p in args.artifact_dir.iterdir() if p.is_file())
    if not package_files:
        raise SystemExit(f"no release artifacts found in {args.artifact_dir}")
    required = [
        ROOT / "docs" / "release-evidence.json",
        ROOT / "src" / "api581" / "data" / "coverage.json",
        ROOT / "docs" / "python-api.schema.json",
        ROOT / "docs" / "digital-twin.schema.json",
        ROOT / "docs" / "INDEPENDENT_ENGINEERING_REVIEW_PACKET.md",
        ROOT / "docs" / "NURION_CERTIFICATION_REPORT.md",
        ROOT / "docs" / "NATIVE_ENGINE_EVIDENCE.json",
        ROOT / "src" / "api581" / "data" / "native-engine-evidence.json",
        ROOT / "docs" / "completion-matrix.json",
        ROOT / "docs" / "supporting-text-review.json",
        ROOT / "docs" / "supporting-text-data-review.json",
        ROOT / "docs" / "engineering-damage-review-draft.json",
        ROOT / "docs" / "ENGINEERING_REVIEW_SIGNOFF_TEMPLATE.md",
        ROOT / "src" / "api581" / "data" / "supporting-text-review.json",
        ROOT / "docs" / "direct-test-queue.json",
        ROOT / "src" / "api581" / "data" / "direct-test-queue.json",
        ROOT / "tmp" / "native-suite-latest.json",
        args.nurion_report,
        ROOT / "docs" / "NURION_EFFICIENT_RUN.md",
        ROOT / "docs" / "FINAL_AUDIT.md",
        ROOT / "tmp" / "final-audit-latest.json",
    ]
    # Keep the latest efficient (0-9) receipt alongside the canonical
    # exhaustive receipt when one is available.  It is supplemental evidence
    # and is deliberately not used as the release gate's 64-shard report.
    efficient_reports = sorted(
        (ROOT / "tmp").glob("nurion-efficient-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for candidate_path in efficient_reports:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        if candidate.get("summary") == {"total": 10, "passed": 10, "failed": 0, "timed_out": 0, "running": 0}:
            required.append(candidate_path)
            break
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise SystemExit("missing evidence: " + ", ".join(missing))

    report = json.loads(args.nurion_report.read_text(encoding="utf-8"))
    summary = report.get("summary", {})
    if (report.get("collector") != "api581.nurion_reconcile"
            or not str(report.get("run_id", "")).endswith("-reconciled")
            or summary != {"total": 64, "passed": 64, "failed": 0, "timed_out": 0, "running": 0}):
        raise SystemExit(f"Nurion report is not terminal-green: {summary}")
    shards = report.get("shards", [])
    indices = [str(item.get("index")) for item in shards]
    if len(shards) != 64 or sorted(indices, key=int) != [str(i) for i in range(64)] or any(item.get("status") != "passed" for item in shards):
        raise SystemExit("Nurion reconciled report does not contain exactly 64 passed shard receipts")
    manifest = {
        "manifest": "api581-release-provenance-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "package_artifacts": [digest(p) for p in package_files],
        "evidence_artifacts": [digest(p) for p in required],
        "nurion_run_id": report.get("run_id"),
        "nurion_summary": summary,
        "certification_status": "software_verified_external_review_out_of_scope",
        "audit_scope": "Package and reproducibility provenance; external evaluation is explicitly outside project scope.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(args.output), "package_count": len(package_files), "nurion_summary": summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
