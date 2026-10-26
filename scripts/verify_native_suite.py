"""Run the optional SLABx/CoolProp verification suite as one reproducible job.

The dependency-free CI suite intentionally does not invoke this script.  Pass
the Python executable from a qualified native environment, for example the
preserved ``tmp/dispersion-native`` environment, and optionally write the
captured run report to ``tmp``.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "verify_native_dispersion.py",
    "verify_native_jet.py",
    "verify_native_footprint.py",
    "verify_native_toxic.py",
    "verify_native_saturation.py",
    "verify_native_flash.py",
    "verify_native_flash_pool.py",
    "verify_native_flashed_pool_footprint.py",
    "verify_native_flashed_pool_risk.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python", dest="python_executable", default=sys.executable,
        help="qualified Python executable containing the optional native packages",
    )
    parser.add_argument(
        "--write-report", type=Path,
        help="write a JSON report at this path in addition to printing it",
    )
    parser.add_argument(
        "--timeout-seconds", type=float, default=300.0,
        help="maximum runtime for each native verification script",
    )
    args = parser.parse_args()
    report = {
        "python": str(Path(args.python_executable).resolve()),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scripts": [],
    }
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    for name in SCRIPTS:
        try:
            completed = subprocess.run(
                [args.python_executable, str(ROOT / "scripts" / name)],
                cwd=ROOT, env=environment, text=True, capture_output=True,
                timeout=args.timeout_seconds,
            )
            item = {
                "script": name,
                "returncode": completed.returncode,
                "status": "passed" if completed.returncode == 0 else "failed",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            item = {
                "script": name,
                "returncode": 124,
                "status": "timed_out",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "timeout_seconds": args.timeout_seconds,
            }
        report["scripts"].append(item)
        if completed.returncode:
            report["status"] = "failed"
            break
    else:
        report["status"] = "passed"
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
