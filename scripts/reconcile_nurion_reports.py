"""Merge a primary PBS array receipt with terminal retry receipts.

PBS stage-out can lose a shard receipt even when the computation itself passed.
This tool preserves the primary receipt, replaces only explicitly retried shard
indices, and refuses to emit a green report unless all 64 indices are green.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--retry", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    primary = load(args.primary)
    shards = {str(item["index"]): item for item in primary["shards"]}
    replaced: list[str] = []
    for retry_path in args.retry:
        retry = load(retry_path)
        for item in retry["shards"]:
            index = str(item["index"])
            if item.get("status") == "passed" and index in shards:
                shards[index] = item
                replaced.append(index)
    ordered = [shards[str(index)] for index in range(64)]
    statuses = [item.get("status") for item in ordered]
    summary = {
        "total": 64,
        "passed": statuses.count("passed"),
        "failed": statuses.count("failed"),
        "timed_out": statuses.count("timed_out"),
        "running": statuses.count("running"),
    }
    if summary != {"total": 64, "passed": 64, "failed": 0, "timed_out": 0, "running": 0}:
        raise SystemExit(f"reconciled report is not terminal-green: {summary}")
    report = {
        "collector": "api581.nurion_reconcile",
        "run_id": primary.get("run_id", "") + "-reconciled",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "primary_report": str(args.primary),
        "retry_reports": [str(path) for path in args.retry],
        "replaced_shard_indices": sorted(set(replaced), key=int),
        "shards": ordered,
        "summary": summary,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(args.output), "summary": summary,
                      "replaced_shard_indices": report["replaced_shard_indices"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
