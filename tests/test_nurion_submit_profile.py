from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "nurion_parallel_submit.py"


def test_efficient_profile_rejects_redundant_array_without_network_access():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", "efficient", "--array", "0-10"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 2
    assert "efficient profile only permits specialized shards 0-9" in completed.stderr


def test_exhaustive_profile_help_exposes_explicit_opt_in():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert "--profile {efficient,exhaustive}" in completed.stdout
