"""Deterministic digital-twin batch throughput/merge stress gate."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

# Keep the stress gate independently runnable from a source checkout; PBS
# payloads still use the installed wheel and therefore take this branch as a
# no-op.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from api581.digital_twin import (
    TwinCalculationRequest,
    build_batch_plan,
    execute_batch_plan,
)


def main() -> None:
    count = 1000
    timestamp = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
    requests = tuple(
        TwinCalculationRequest(
            request_id=f"stress-{index:04d}",
            calculation_id="release/orifice-area",
            asset_id="stress-asset",
            component_id=f"pipe-{index:04d}",
            observed_at=timestamp,
            source_revision="stress-revision",
            correlation_id="stress-batch",
            inputs={"diameter_m": 0.005 + index * 1e-6},
        )
        for index in range(count)
    )
    started = time.perf_counter()
    plan = build_batch_plan(requests, shard_size=25, batch_id="stress-batch")
    # Use one process pool for the whole replay: constructing a pool per shard
    # hides the scheduler-style parallelism behind process startup overhead.
    # The plan still validates every shard manifest before any work begins and
    # the returned order remains the immutable plan order.
    merged = execute_batch_plan(
        plan, requests, max_workers=8, execution_mode="process", chunksize=16,
    )
    elapsed = time.perf_counter() - started
    assert len(plan.shards) == 40
    assert len(merged) == count
    assert [item.request_id for item in merged] == list(plan.request_ids)
    assert all(item.outputs["area_m2"] > 0 for item in merged)
    print(json.dumps({
        "status": "passed",
        "request_count": count,
        "shard_count": len(plan.shards),
        "execution_mode": "process",
        "max_workers": 8,
        "chunksize": 16,
        "elapsed_seconds": elapsed,
        "requests_per_second": count / elapsed if elapsed else None,
    }, indent=2))


if __name__ == "__main__":
    main()
