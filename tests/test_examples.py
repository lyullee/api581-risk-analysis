"""Source-checkout example smoke tests."""
import json
from pathlib import Path
import subprocess
import sys


def test_digital_twin_hpc_example_bootstraps_source_checkout():
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, "examples/digital_twin_hpc_batch.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["batch_id"] == "demo-batch"
    assert payload["request_ids"] == ["req-001", "req-002"]
    assert len(payload["areas_m2"]) == 2
