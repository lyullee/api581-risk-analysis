"""Run the independent API-581 release audit and write one JSON report."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "final-audit-latest.json")
    parser.add_argument("--skip-tests", action="store_true", help="skip the full pytest run")
    args = parser.parse_args()
    # Provenance is intentionally run after this report is written: its
    # manifest check hash-pins this file and therefore cannot be a child
    # check of the file it validates without a circular dependency.
    commands = [
        ["scripts/verify_release.py"],
        ["scripts/verify_completion_matrix.py"],
        ["scripts/verify_reference_fixtures.py"],
        ["scripts/verify_supporting_text_dispositions.py"],
        ["scripts/verify_supporting_text_data_review.py"],
        ["scripts/verify_engineering_damage_review_draft.py"],
        ["scripts/check_unimplemented_bodies.py"],
        ["scripts/check_doc_api_paths.py"],
    ]
    if not args.skip_tests:
        commands.append(["-m", "pytest", "-q"])
    results = []
    for command in commands:
        display = [sys.executable, *command]
        completed = subprocess.run(display, cwd=ROOT, text=True, capture_output=True)
        results.append({
            "command": display,
            "return_code": completed.returncode,
            "status": "passed" if completed.returncode == 0 else "failed",
            "stdout_tail": completed.stdout.splitlines()[-20:],
            "stderr_tail": completed.stderr.splitlines()[-20:],
        })
        if completed.returncode != 0:
            break
    report = {
        "report": "api581-final-audit-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if results and all(item["status"] == "passed" for item in results) and len(results) == len(commands) else "failed",
        "checks": results,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output), "checks": len(results)}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
