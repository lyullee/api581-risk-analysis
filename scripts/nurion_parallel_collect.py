"""Collect machine-readable receipts from a Nurion API-581 PBS array.

The collector is intentionally read-only on the remote payload.  It turns the
per-shard ``.status``/``.meta``/``.out``/``.err`` files into one local JSON
report suitable for release evidence and CI artifacts.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex

from nurion_pbs_submit import run_wsl, ssh


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", help="parallel submit run id, e.g. 20261025T074247Z-parallel")
    parser.add_argument("--remote-root", default="/scratch/r1021a02/api581_parallel")
    parser.add_argument("--shards", type=int, default=64)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pbs-job", help="PBS array id; defaults to the local submission receipt")
    args = parser.parse_args()
    if args.shards < 1 or args.shards > 64:
        parser.error("--shards must be between 1 and 64")

    payload = f"{args.remote_root.rstrip('/')}/{args.run_id}/nurion-api581-{args.run_id}"
    python_source = r'''
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
count = int(sys.argv[2])
shards = []
for index in range(count):
    item = {"index": index}
    status = root / f"shard-{index}.status"
    meta = root / f"shard-{index}.meta"
    out = root / f"shard-{index}.out"
    err = root / f"shard-{index}.err"
    item["status"] = status.read_text().strip() if status.exists() else "running"
    if meta.exists():
        for line in meta.read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                item[key] = value
    item["stdout_tail"] = out.read_text(errors="replace").splitlines()[-12:] if out.exists() else []
    item["stderr_tail"] = err.read_text(errors="replace").splitlines()[-12:] if err.exists() else []
    shards.append(item)
print(json.dumps({"remote_payload": str(root), "shards": shards}, ensure_ascii=False))
'''
    encoded_source = base64.b64encode(python_source.encode()).decode("ascii")
    command = (
        f"printf %s {encoded_source} | base64 -d | python3 - "
        f"{shlex.quote(payload)} {args.shards}"
    )
    raw = ssh(command, timeout=120)
    remote_report = json.loads(raw.strip().splitlines()[-1])
    pbs_job = args.pbs_job
    submission_path = Path(__file__).resolve().parents[1] / "tmp" / f"nurion-parallel-{args.run_id}.submission.json"
    if not pbs_job and submission_path.is_file():
        pbs_job = json.loads(submission_path.read_text(encoding="utf-8")).get("pbs_job")
    pbs_terminal = {}
    if pbs_job:
        try:
            qstat = ssh(f"qstat -xf -t {shlex.quote(pbs_job)}", timeout=60)
            current = None
            for line in qstat.splitlines():
                match = re.match(r"^\s*(?:Job Id:\s*)?(\d+)\[(\d+)\]\.pbs", line.strip())
                if match:
                    current = match.group(2)
                    pbs_terminal[current] = {}
                    continue
                if current is None:
                    continue
                key_value = re.match(r"^\s*(job_state|Exit_status|Stageout_status)\s*=\s*(.*)$", line)
                if key_value:
                    pbs_terminal[current][key_value.group(1)] = key_value.group(2).strip()
        except Exception:
            pbs_terminal = {}
    for item in remote_report["shards"]:
        terminal = pbs_terminal.get(str(item["index"]))
        if item["status"] == "running" and terminal and terminal.get("job_state") == "F":
            item["status"] = "failed" if terminal.get("Exit_status", "1") != "0" or terminal.get("Stageout_status", "0") != "0" else "passed"
            item.update({f"pbs_{key.lower()}": value for key, value in terminal.items()})
    statuses = [item["status"] for item in remote_report["shards"]]
    report = {
        "collector": "api581.nurion_parallel_collect",
        "run_id": args.run_id,
        "pbs_job": pbs_job,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        **remote_report,
        "summary": {
            "total": len(statuses),
            "passed": statuses.count("passed"),
            "failed": statuses.count("failed"),
            "timed_out": statuses.count("timed_out"),
            "running": statuses.count("running"),
        },
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report["summary"]["failed"] == 0 and report["summary"]["timed_out"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
