"""Framework-neutral digital-twin exchange contracts.

These models intentionally perform no I/O and do not define a transport
protocol.  A host can serialize them to its event bus, database or adapter,
then call one of the typed :mod:`api581.api` functions with ``to_context()``.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Literal, Sequence
from uuid import uuid4

from pydantic import ConfigDict, Field, field_validator, model_validator

from .core import CODE_FINGERPRINT, VERSION, Context, Model, NonNegative, REGISTRY, ensure, evaluate
from .evidence import ValidationEvidence

__all__ = [
    "TwinMeasurement", "TwinCalculationRequest", "TwinCalculationResponse",
    "TwinBatchShard", "TwinBatchPlan", "partition_requests", "build_batch_plan",
    "merge_batch_responses", "execute_request", "execute_requests", "execute_batch_plan",
    "execute_batch_shard",
]


class _FrozenDict(dict):
    """JSON-compatible recursively immutable mapping used by twin envelopes."""
    def _blocked(self, *args, **kwargs):
        raise TypeError("digital-twin envelope mappings are immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _blocked

    def __reduce__(self):
        return (_restore_frozen_dict, (tuple(self.items()),))


class _FrozenList(list):
    """JSON-compatible recursively immutable sequence used by twin envelopes."""
    def _blocked(self, *args, **kwargs):
        raise TypeError("digital-twin envelope sequences are immutable")

    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = reverse = sort = _blocked

    def __reduce__(self):
        return (_restore_frozen_list, (tuple(self),))


def _restore_frozen_dict(items):
    result = dict.__new__(_FrozenDict)
    for key, value in items:
        dict.__setitem__(result, key, value)
    return result


def _restore_frozen_list(items):
    result = list.__new__(_FrozenList)
    list.extend(result, items)
    return result


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return _FrozenDict({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return _FrozenList([_freeze(item) for item in value])
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


class TwinMeasurement(Model):
    model_config = ConfigDict(frozen=True)
    measurement_id: str = Field(min_length=1, max_length=200)
    quantity: str = Field(min_length=1, max_length=200)
    value: float
    unit: str = Field(min_length=1, max_length=50)
    measured_at: datetime
    source: str = Field(min_length=1, max_length=500)
    quality: Literal["measured", "estimated", "simulated"]
    uncertainty: NonNegative | None = None

    @model_validator(mode="after")
    def aware_timestamp(self):
        if self.measured_at.utcoffset() is None:
            raise ValueError("measured_at requires a timezone offset")
        return self


class TwinCalculationRequest(Model):
    """Immutable calculation request envelope supplied by a twin host."""
    model_config = ConfigDict(frozen=True)
    request_id: str = Field(min_length=1, max_length=200)
    calculation_id: str = Field(min_length=1, max_length=200)
    asset_id: str = Field(min_length=1, max_length=200)
    component_id: str = Field(min_length=1, max_length=200)
    observed_at: datetime
    source_revision: str = Field(min_length=1, max_length=200)
    correlation_id: str = Field(min_length=1, max_length=200)
    inputs: dict[str, Any]
    measurements: list[TwinMeasurement] = Field(default_factory=list, max_length=10000)
    contract_version: Literal["api581-twin-1"] = "api581-twin-1"

    @field_validator("inputs", mode="after")
    @classmethod
    def freeze_inputs(cls, value):
        return _freeze(value)

    @field_validator("measurements", mode="after")
    @classmethod
    def freeze_measurements(cls, value):
        return _freeze(value)

    @model_validator(mode="after")
    def validate_envelope(self):
        if self.observed_at.utcoffset() is None:
            raise ValueError("observed_at requires a timezone offset")
        ids = [m.measurement_id for m in self.measurements]
        if len(ids) != len(set(ids)):
            raise ValueError("measurement_id values must be unique within a request")
        return self

    def to_context(self) -> Context:
        """Convert the envelope identity to the engine's calculation context."""
        return Context(asset_id=self.asset_id, component_id=self.component_id,
                       observed_at=self.observed_at, correlation_id=self.correlation_id,
                       source_revision=self.source_revision)

    def measurement_snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a deterministic, lossless measurement index for adapters.

        Calculation inputs remain explicit in ``inputs``; this method does not
        silently inject sensor values into a model.  It gives a digital-twin
        adapter a stable lookup keyed by measurement ID while preserving the
        quantity, unit, timestamp, quality and uncertainty metadata.
        """
        return {
            measurement.measurement_id: {
                "quantity": measurement.quantity,
                "value": measurement.value,
                "unit": measurement.unit,
                "measured_at": measurement.measured_at.isoformat(),
                "source": measurement.source,
                "quality": measurement.quality,
                "uncertainty": measurement.uncertainty,
            }
            for measurement in self.measurements
        }

    def input_hash(self) -> str:
        """Return the engine input snapshot hash expected for this request."""
        ensure(self.calculation_id in REGISTRY,
               f"Unknown calculation: {self.calculation_id}", "unknown_calculation")
        parsed = REGISTRY[self.calculation_id].model.model_validate(self.inputs)
        snapshot = {
            "inputs": parsed.model_dump(mode="json"),
            "context": self.to_context().model_dump(mode="json"),
            "calculation_id": self.calculation_id,
            "engine_version": VERSION,
            "code_fingerprint": CODE_FINGERPRINT,
        }
        return sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class TwinCalculationResponse(Model):
    """Reproducible result envelope returned to a twin host."""
    model_config = ConfigDict(frozen=True)
    contract_version: Literal["api581-twin-1"] = "api581-twin-1"
    request_id: str = Field(min_length=1, max_length=200)
    run_id: str = Field(min_length=1, max_length=200)
    calculation_id: str = Field(min_length=1, max_length=200)
    asset_id: str = Field(min_length=1, max_length=200)
    component_id: str = Field(min_length=1, max_length=200)
    observed_at: datetime
    input_hash: str = Field(min_length=1, max_length=200)
    engine_version: str = Field(min_length=1, max_length=100)
    standard_edition: str = Field(min_length=1, max_length=100)
    code_fingerprint: str = Field(min_length=1, max_length=200)
    outputs: dict[str, Any]
    references: list[str]
    limitations: list[str]
    validation_evidence: list[ValidationEvidence] = Field(default_factory=list)
    software_test_modules: list[str] = Field(default_factory=list)
    direct_public_test_modules: list[str] = Field(default_factory=list)
    validation_level: Literal["software_tested_only", "native_engine_fixture_verified"] = "software_tested_only"
    validation_status: str = Field(min_length=1, max_length=200)

    @field_validator("outputs", "references", "limitations", "validation_evidence", "software_test_modules", "direct_public_test_modules", mode="after")
    @classmethod
    def freeze_payload(cls, value):
        return _freeze(value)

    @model_validator(mode="after")
    def aware_timestamp(self):
        if self.observed_at.utcoffset() is None:
            raise ValueError("observed_at requires a timezone offset")
        return self

    @classmethod
    def from_result(cls, request: TwinCalculationRequest, result: Any) -> "TwinCalculationResponse":
        """Project a typed ``CalculationResult`` into the twin envelope."""
        ensure(result.calculation_id == request.calculation_id,
               "Result calculation_id does not match request", "twin_contract_mismatch")
        from .catalog import calculation_evidence
        evidence = calculation_evidence(request.calculation_id)
        ensure(result.validation_level == evidence["validation_level"],
               "Result validation_level does not match calculation evidence",
               "twin_contract_mismatch")
        ensure(list(result.direct_public_test_modules) == list(evidence["direct_public_test_modules"]),
               "Result direct_public_test_modules do not match calculation evidence",
               "twin_contract_mismatch")
        return cls(request_id=request.request_id, run_id=result.run_id,
                   calculation_id=result.calculation_id, asset_id=request.asset_id,
                   component_id=request.component_id, observed_at=request.observed_at,
                   input_hash=result.input_hash, engine_version=result.engine_version,
                   standard_edition=result.standard_edition,
                   code_fingerprint=result.code_fingerprint,
                   outputs=result.outputs.model_dump(mode="json"),
                   references=list(result.references), limitations=list(result.limitations),
                   validation_evidence=list(result.validation_evidence),
                   software_test_modules=list(result.software_test_modules),
                   direct_public_test_modules=list(result.direct_public_test_modules),
                   validation_level=result.validation_level,
                   validation_status=result.validation_status)


def execute_request(request: TwinCalculationRequest) -> TwinCalculationResponse:
    """Execute a request through the normal typed registry boundary.

    This is deliberately a local pure-Python bridge: transport, retries,
    authentication and persistence remain the twin host's responsibility.
    """
    ensure(request.calculation_id in REGISTRY,
           f"Unknown calculation: {request.calculation_id}", "unknown_calculation")
    payload = evaluate(request.calculation_id, request.inputs, request.to_context())
    from .catalog import calculation_evidence
    evidence = calculation_evidence(request.calculation_id)
    return TwinCalculationResponse(
        request_id=request.request_id, run_id=payload["run_id"],
        calculation_id=payload["calculation_id"], asset_id=request.asset_id,
        component_id=request.component_id, observed_at=request.observed_at,
        input_hash=payload["input_hash"], engine_version=payload["engine_version"],
        standard_edition=payload["standard_edition"],
        code_fingerprint=payload["code_fingerprint"], outputs=payload["outputs"],
        references=payload["references"], limitations=payload["limitations"],
        validation_evidence=evidence["validation_evidence"],
        software_test_modules=evidence["software_test_modules"],
        direct_public_test_modules=evidence["direct_public_test_modules"],
        validation_level=evidence["validation_level"],
        validation_status=payload["validation_status"])


class TwinBatchShard(Model):
    """Deterministic work partition that a host may submit to an HPC queue."""
    model_config = ConfigDict(frozen=True)
    shard_id: str = Field(min_length=1, max_length=200)
    ordinal: int = Field(ge=0)
    request_ids: tuple[str, ...] = Field(min_length=1, max_length=100000)
    payload_hash: str = Field(min_length=64, max_length=64)


class TwinBatchPlan(Model):
    """Scheduler-neutral manifest for replayable digital-twin batches."""
    model_config = ConfigDict(frozen=True)
    contract_version: Literal["api581-batch-1"] = "api581-batch-1"
    batch_id: str = Field(min_length=1, max_length=200)
    request_count: int = Field(ge=0)
    shard_size: int = Field(gt=0)
    request_ids: tuple[str, ...]
    shards: tuple[TwinBatchShard, ...]
    plan_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_manifest_shape(self):
        """Reject structurally inconsistent manifests before scheduler use.

        The payload digest is checked when the original requests are supplied
        to :meth:`verify_requests`; this validator covers the request-free
        portion of the contract so a worker cannot accept a manifest whose
        shard IDs, ordinals, or request count disagree with one another.
        """
        request_ids = tuple(self.request_ids)
        ensure(self.request_count == len(request_ids),
               "Batch request_count does not match request_ids", "batch_plan_mismatch")
        ensure(len(request_ids) == len(set(request_ids)),
               "Batch request_ids must be unique", "batch_plan_mismatch")
        shard_ids = tuple(shard.shard_id for shard in self.shards)
        ensure(len(shard_ids) == len(set(shard_ids)),
               "Batch shard_id values must be unique", "batch_plan_mismatch")
        ordinals = tuple(shard.ordinal for shard in self.shards)
        ensure(ordinals == tuple(range(len(self.shards))),
               "Batch shard ordinals must be contiguous and ordered", "batch_plan_mismatch")
        flattened = tuple(request_id for shard in self.shards for request_id in shard.request_ids)
        ensure(flattened == request_ids,
               "Batch shards do not cover request_ids in order", "batch_plan_mismatch")
        return self

    def verify_requests(self, requests: Sequence[TwinCalculationRequest]) -> None:
        """Verify that queued request payloads still match this manifest."""
        groups = partition_requests(requests, shard_size=self.shard_size)
        items = tuple(item for group in groups for item in group)
        actual_ids = tuple(item.request_id for item in items)
        ensure(actual_ids == self.request_ids,
               "Batch requests do not match manifest request order", "batch_plan_mismatch")
        actual_shards = tuple(
            tuple(item.request_id for item in group) for group in groups
        )
        expected_shards = tuple(shard.request_ids for shard in self.shards)
        ensure(actual_shards == expected_shards,
               "Batch requests do not match manifest shards", "batch_plan_mismatch")
        actual_hashes = tuple(
            _request_manifest_hash(group) for group in groups
        )
        expected_hashes = tuple(shard.payload_hash for shard in self.shards)
        ensure(actual_hashes == expected_hashes,
               "Batch request shard payload hash does not match manifest", "batch_plan_mismatch")
        digest = _request_manifest_hash(items)
        ensure(digest == self.plan_hash,
               "Batch request payload hash does not match manifest", "batch_plan_mismatch")


def partition_requests(
    requests: Sequence[TwinCalculationRequest], *, shard_size: int,
) -> tuple[tuple[TwinCalculationRequest, ...], ...]:
    """Partition requests without changing order or request-level provenance."""
    ensure(shard_size >= 1, "shard_size must be at least one", "invalid_batch_shard_size")
    items = tuple(requests)
    ids = [item.request_id for item in items]
    ensure(len(ids) == len(set(ids)), "request_id values must be unique within a batch", "duplicate_batch_request")
    return tuple(items[index:index + shard_size] for index in range(0, len(items), shard_size))


def _request_manifest_hash(items: Sequence[TwinCalculationRequest]) -> str:
    manifest = [item.model_dump(mode="json") for item in items]
    return sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build_batch_plan(
    requests: Sequence[TwinCalculationRequest], *, shard_size: int,
    batch_id: str | None = None,
) -> TwinBatchPlan:
    """Build a deterministic manifest; scheduler submission remains host-owned."""
    groups = partition_requests(requests, shard_size=shard_size)
    items = tuple(item for group in groups for item in group)
    request_ids = tuple(item.request_id for item in items)
    digest = _request_manifest_hash(items)
    resolved_batch_id = batch_id or str(uuid4())
    shards = tuple(
        TwinBatchShard(
            shard_id=f"{resolved_batch_id}-{ordinal:06d}",
            ordinal=ordinal,
            request_ids=tuple(item.request_id for item in group),
            payload_hash=_request_manifest_hash(group),
        )
        for ordinal, group in enumerate(groups)
    )
    return TwinBatchPlan(
        batch_id=resolved_batch_id,
        request_count=len(items),
        shard_size=shard_size,
        request_ids=request_ids,
        shards=shards,
        plan_hash=digest,
    )


def merge_batch_responses(
    responses: Sequence[TwinCalculationResponse], *, request_order: Sequence[str],
    requests: Sequence[TwinCalculationRequest] | None = None,
) -> list[TwinCalculationResponse]:
    """Reassemble independently completed shards and reject identity mismatches.

    When ``requests`` is supplied, response calculation/asset/component and
    observation identity are checked against the original immutable request;
    this prevents a scheduler retry from attaching a valid response from a
    different component to the same request ID.
    """
    order = tuple(request_order)
    ensure(len(order) == len(set(order)), "request_order values must be unique", "duplicate_batch_request")
    response_map: dict[str, TwinCalculationResponse] = {}
    for response in responses:
        ensure(response.request_id not in response_map, "duplicate response request_id", "duplicate_batch_response")
        response_map[response.request_id] = response
    ensure(set(response_map) == set(order), "batch responses do not match request_order", "incomplete_batch_response")
    if requests is not None:
        request_map = {request.request_id: request for request in requests}
        ensure(tuple(request_map) == order,
               "batch requests do not match request_order", "batch_plan_mismatch")
        for request_id, response in response_map.items():
            request = request_map[request_id]
            ensure(
                response.calculation_id == request.calculation_id
                and response.asset_id == request.asset_id
                and response.component_id == request.component_id
                and response.observed_at == request.observed_at,
                "batch response identity does not match request",
                "batch_response_mismatch",
            )
            ensure(response.input_hash == request.input_hash(),
                   "batch response input_hash does not match request",
                   "batch_response_mismatch")
    return [response_map[request_id] for request_id in order]


def execute_requests(
    requests: Sequence[TwinCalculationRequest], *, max_workers: int = 1,
    execution_mode: Literal["serial", "thread", "process"] = "serial",
    chunksize: int = 1,
) -> list[TwinCalculationResponse]:
    """Execute independent twin requests while preserving input order.

    The helper is transport- and storage-neutral.  Serial execution is the
    deterministic default; ``thread`` is useful for I/O-bound adapters and
    ``process`` provides a GIL-independent CPU boundary for large scenario
    batches or an HPC launcher. Input order and request-level provenance are
    preserved in every mode. Native SLABx calls still retain their own process
    isolation inside each request.
    """
    ensure(max_workers >= 1, "max_workers must be at least one", "invalid_batch_workers")
    ensure(chunksize >= 1, "chunksize must be at least one", "invalid_batch_chunksize")
    ensure(execution_mode in {"serial", "thread", "process"},
           "execution_mode must be serial, thread or process", "invalid_batch_execution_mode")
    request_list = list(requests)
    ids = [item.request_id for item in request_list]
    ensure(len(ids) == len(set(ids)), "request_id values must be unique within a batch", "duplicate_batch_request")
    if execution_mode == "serial" or max_workers == 1 or len(request_list) < 2:
        return [execute_request(item) for item in request_list]
    executor_type = ProcessPoolExecutor if execution_mode == "process" else ThreadPoolExecutor
    with executor_type(max_workers=max_workers) as pool:
        # ``chunksize`` materially reduces IPC overhead for large process
        # batches.  ThreadPoolExecutor accepts the argument for API
        # compatibility but intentionally ignores it, matching stdlib
        # semantics.  Serial execution above avoids creating an executor.
        return list(pool.map(execute_request, request_list, chunksize=chunksize))


def execute_batch_plan(
    plan: TwinBatchPlan,
    requests: Sequence[TwinCalculationRequest], *,
    max_workers: int = 1,
    execution_mode: Literal["serial", "thread", "process"] = "serial",
    chunksize: int = 1,
) -> list[TwinCalculationResponse]:
    """Verify and execute a replayable batch plan, returning manifest order.

    The plan is checked before any calculation starts.  This makes scheduler
    retries safe: a worker cannot accidentally run a changed payload under an
    old shard manifest.  The returned responses are ordered exactly like the
    plan, regardless of the selected execution backend.
    """
    request_list = tuple(requests)
    ensure(len(request_list) == plan.request_count,
           "Batch request count does not match plan", "batch_plan_mismatch")
    plan.verify_requests(request_list)
    responses = execute_requests(
        request_list, max_workers=max_workers, execution_mode=execution_mode,
        chunksize=chunksize,
    )
    return merge_batch_responses(responses, request_order=plan.request_ids, requests=request_list)


def execute_batch_shard(
    plan: TwinBatchPlan,
    shard_id: str,
    requests: Sequence[TwinCalculationRequest], *,
    max_workers: int = 1,
    execution_mode: Literal["serial", "thread", "process"] = "serial",
    chunksize: int = 1,
) -> list[TwinCalculationResponse]:
    """Verify and execute one scheduler-owned shard of a batch plan.

    Workers need only receive the requests assigned to their shard.  The
    shard-local request IDs and payload hash are checked against the immutable
    plan before any calculation starts; the host can merge returned responses
    with :func:`merge_batch_responses` after all workers complete.
    """
    shard = next((item for item in plan.shards if item.shard_id == shard_id), None)
    ensure(shard is not None, "Unknown batch shard", "batch_plan_mismatch")
    request_list = tuple(requests)
    actual_ids = tuple(item.request_id for item in request_list)
    ensure(actual_ids == shard.request_ids,
           "Shard requests do not match manifest order", "batch_plan_mismatch")
    ensure(_request_manifest_hash(request_list) == shard.payload_hash,
           "Shard request payload hash does not match manifest", "batch_plan_mismatch")
    responses = execute_requests(
        request_list, max_workers=max_workers, execution_mode=execution_mode,
        chunksize=chunksize,
    )
    return merge_batch_responses(responses, request_order=shard.request_ids, requests=request_list)
