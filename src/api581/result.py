"""Typed calculation results and the shared Python execution boundary."""
from typing import Any, Generic, TypeVar
from pydantic import Field
from .core import Context, Model, REGISTRY, ensure, evaluate
from .evidence import ValidationEvidence

OutputT = TypeVar("OutputT", bound=Model)


class CalculationResult(Model, Generic[OutputT]):
    run_id: str
    calculation_id: str
    engine_version: str
    standard_edition: str
    code_fingerprint: str
    calculated_at: str
    context: Context
    input_hash: str
    normalized_inputs: dict[str, Any]
    outputs: OutputT
    method_origin: str
    references: list[str]
    limitations: list[str]
    validation_evidence: list[ValidationEvidence] = Field(default_factory=list)
    software_test_modules: list[str] = Field(default_factory=list)
    direct_public_test_modules: list[str] = Field(default_factory=list)
    validation_level: str = Field(
        default="software_tested_only",
        pattern=r"^(software_tested_only|native_engine_fixture_verified)$",
    )
    validation_status: str


def calculate(identifier: str, inputs: Model, *, output_type: type[OutputT],
              context: Context | None = None) -> CalculationResult[OutputT]:
    """Execute without I/O. Domain functions supply the matching output type."""
    ensure(identifier in REGISTRY, f"Unknown calculation: {identifier}", "unknown_calculation")
    if not isinstance(inputs, REGISTRY[identifier].model):
        raise TypeError(f"{identifier} requires {REGISTRY[identifier].model.__name__}")
    from .outputs import OUTPUT_MODELS
    if OUTPUT_MODELS[identifier] is not output_type:
        raise TypeError("output_type must match the registered calculation")
    payload = evaluate(identifier, inputs.model_dump(mode="python"), context)
    from .catalog import calculation_evidence
    evidence = calculation_evidence(identifier)
    payload["validation_evidence"] = evidence["validation_evidence"]
    payload["software_test_modules"] = evidence["software_test_modules"]
    payload["direct_public_test_modules"] = evidence["direct_public_test_modules"]
    payload["validation_level"] = evidence["validation_level"]
    return CalculationResult[output_type].model_validate(payload)
