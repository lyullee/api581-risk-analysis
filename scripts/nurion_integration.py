"""Run the API 581 integration gates in a cluster-friendly, machine-readable form.

This runner intentionally has no site-specific assumptions.  A Nurion Slurm job
can invoke it with the same source checkout and an optional native Python
environment containing SLABx/SLABx-LH2/CoolProp.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, command: list[str], *, env: dict[str, str]) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(
        command, cwd=ROOT, env=env, text=True, capture_output=True,
    )
    return {
        "label": label,
        "command": command,
        "returncode": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "started_at": started,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the gates")
    parser.add_argument("--native-python", help="optional Python with native SLABx/CoolProp packages")
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-native", action="store_true")
    parser.add_argument("--pytest-k", default=None, help="optional pytest -k expression for site-optional tests")
    parser.add_argument("--pytest-ignore", action="append", default=[], help="pytest path to ignore")
    parser.add_argument("--pytest-target", action="append", default=[], help="explicit pytest path")
    args = parser.parse_args()
    python_path = Path(args.python)
    python = str(python_path.resolve()) if python_path.exists() else args.python
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        item for item in (os.environ.get("PYTHONPATH"), str(ROOT / "src")) if item
    )
    commands: list[tuple[str, list[str]]] = []
    if not args.skip_pytest:
        pytest_command = [python, "-m", "pytest", "-q"]
        if args.pytest_k:
            pytest_command.extend(["-k", args.pytest_k])
        for ignored in args.pytest_ignore:
            pytest_command.extend(["--ignore", ignored])
        pytest_command.extend(args.pytest_target)
        commands.append(("pytest", pytest_command))
    commands.extend([
        ("release_contracts", [python, "scripts/verify_release.py"]),
        ("reference_fixtures", [python, "scripts/verify_reference_fixtures.py"]),
        ("digital_twin_example", [python, "examples/digital_twin_hpc_batch.py"]),
    ])
    native_python = args.native_python or python
    if not args.skip_native:
        commands.append(("native_suite", [native_python, "scripts/verify_native_suite.py"]))
    report: dict[str, object] = {
        "runner": "api581.nurion_integration",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": python,
        "native_python": native_python if not args.skip_native else None,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
        "git_revision": _git_revision(),
        "sbatch": shutil.which("sbatch"),
        "steps": [],
    }
    steps = report["steps"]
    assert isinstance(steps, list)
    for label, command in commands:
        item = _run(label, command, env=env)
        steps.append(item)
        if item["returncode"]:
            break
    report["status"] = "passed" if steps and all(item["returncode"] == 0 for item in steps) else "failed"
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["status"] == "passed" else 1


def _git_revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
