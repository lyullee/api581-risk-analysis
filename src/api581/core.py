"""Registry shared by typed Python, batch and composed calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Annotated, Any, Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

VERSION = "0.1.0"
EDITION = "API-RP-581-2016-3rd-base"


def code_fingerprint():
    digest = sha256()
    root = Path(__file__).parent
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


CODE_FINGERPRINT = code_fingerprint()
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False, strict=True)]
Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False, strict=True)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_default=True)


class Context(Model):
    asset_id: str | None = Field(default=None, max_length=200)
    component_id: str | None = Field(default=None, max_length=200)
    observed_at: datetime | None = None
    correlation_id: str | None = Field(default=None, max_length=200)
    source_revision: str | None = Field(default=None, max_length=200)
    standard_edition: Literal["API-RP-581-2016-3rd-base"] = EDITION

    @field_validator("observed_at")
    @classmethod
    def aware(cls, value):
        if value is not None and value.utcoffset() is None:
            raise ValueError("observed_at requires a timezone offset")
        return value


class DomainError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Calculation:
    id: str
    title: str
    model: type[Model]
    function: Callable
    references: tuple[str, ...]
    origin: str
    limitations: tuple[str, ...]


REGISTRY: dict[str, Calculation] = {}


def calculation(id, title, model, references=(), origin="api581_equation", limitations=()):
    def register(fn):
        if id in REGISTRY:
            raise RuntimeError(f"duplicate calculation: {id}")
        resolved_limitations = tuple(limitations) or (
            "Primitive or utility calculation with no additional clause-specific limitation; "
            "caller must qualify API 581 applicability, input basis and engineering use.",
        )
        REGISTRY[id] = Calculation(id, title, model, fn, tuple(references), origin, resolved_limitations)
        return fn
    return register


def ensure(condition: bool, message: str, code="outside_model_domain"):
    if not condition:
        raise DomainError(code, message)


def finite_tree(value):
    if isinstance(value, float):
        ensure(math.isfinite(value), "Non-finite calculation result", "numerical_failure")
    elif isinstance(value, dict):
        for x in value.values():
            finite_tree(x)
    elif isinstance(value, (list, tuple)):
        for x in value:
            finite_tree(x)


def evaluate(id: str, inputs: dict[str, Any], context: Context | None = None):
    ensure(id in REGISTRY, f"Unknown calculation: {id}", "unknown_calculation")
    c = REGISTRY[id]
    parsed = c.model.model_validate(inputs)
    try:
        output = c.function(parsed)
        finite_tree(output)
    except (OverflowError, ZeroDivisionError) as exc:
        raise DomainError("numerical_failure", "Inputs exceed numerical domain") from exc
    from .contracts import OUTPUT_MODELS
    try:
        output = OUTPUT_MODELS[id].model_validate(output).model_dump(mode="json", exclude_unset=True)
    except ValidationError as exc:
        raise DomainError("output_contract_violation", f"Calculation {id} returned an invalid output contract") from exc
    ctx = context or Context()
    snapshot = {"inputs": parsed.model_dump(mode="json"), "context": ctx.model_dump(mode="json"),
                "calculation_id": id, "engine_version": VERSION, "code_fingerprint": CODE_FINGERPRINT}
    digest = sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {"run_id": str(uuid4()), "calculation_id": id, "engine_version": VERSION,
            "standard_edition": EDITION, "code_fingerprint": snapshot["code_fingerprint"], "calculated_at": datetime.now(timezone.utc).isoformat(),
            "context": ctx.model_dump(mode="json"), "input_hash": digest,
            "normalized_inputs": snapshot["inputs"], "outputs": output,
            "method_origin": c.origin, "references": list(c.references),
            "limitations": list(c.limitations), "validation_status": "software_tested_not_independently_certified"}
