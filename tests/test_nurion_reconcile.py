import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).parents[1]


def _report(path: Path, *, statuses: dict[int, str], collector: str = "api581.nurion_parallel_collect"):
    shards = [{"index": str(i), "status": statuses.get(i, "running")} for i in range(64)]
    payload = {"collector": collector, "run_id": "primary", "shards": shards,
               "summary": {"total": 64, "passed": sum(v == "passed" for v in statuses.values()),
                            "failed": sum(v == "failed" for v in statuses.values()),
                            "timed_out": 0, "running": 64 - len(statuses)}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_reconcile_replaces_only_passed_retry_indices(tmp_path):
    primary = tmp_path / "primary.json"
    retry = tmp_path / "retry.json"
    output = tmp_path / "reconciled.json"
    _report(primary, statuses={i: "passed" for i in range(64) if i not in {31, 45}})
    _report(retry, statuses={31: "passed", 45: "passed"}, collector="api581.nurion_reconcile")
    completed = subprocess.run(
        [sys.executable, "scripts/reconcile_nurion_reports.py", "--primary", str(primary),
         "--retry", str(retry), "--output", str(output)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert '"passed": 64' in completed.stdout
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["summary"] == {"total": 64, "passed": 64, "failed": 0, "timed_out": 0, "running": 0}
    assert result["replaced_shard_indices"] == ["31", "45"]
