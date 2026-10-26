"""Run a scheduler-neutral digital-twin batch through shard boundaries.

The example deliberately owns no transport, queue or persistence.  A real
HPC host can submit each ``TwinBatchShard`` independently and use the same
verification calls before merging worker responses.
"""
import _bootstrap  # noqa: F401
from datetime import datetime, timezone
import json

from api581.digital_twin import (
    TwinCalculationRequest,
    build_batch_plan,
    execute_batch_shard,
    merge_batch_responses,
)


def request(request_id: str, diameter_m: float) -> TwinCalculationRequest:
    timestamp = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
    return TwinCalculationRequest(
        request_id=request_id,
        calculation_id="release/orifice-area",
        asset_id="asset-demo",
        component_id=f"pipe-{request_id}",
        observed_at=timestamp,
        source_revision="demo-revision",
        correlation_id="demo-batch",
        inputs={"diameter_m": diameter_m},
    )


def main() -> None:
    requests = (request("req-001", 0.01), request("req-002", 0.02))
    plan = build_batch_plan(requests, shard_size=1, batch_id="demo-batch")
    responses = []
    for shard in plan.shards:
        assigned = tuple(item for item in requests if item.request_id in shard.request_ids)
        responses.extend(execute_batch_shard(plan, shard.shard_id, assigned))
    merged = merge_batch_responses(
        responses, request_order=plan.request_ids, requests=requests,
    )
    print(json.dumps({
        "batch_id": plan.batch_id,
        "request_ids": [item.request_id for item in merged],
        "validation_levels": [item.validation_level for item in merged],
        "areas_m2": [item.outputs["area_m2"] for item in merged],
    }, indent=2))


if __name__ == "__main__":
    main()
