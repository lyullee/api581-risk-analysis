"""Bounded declarative composition, with no eval, arbitrary imports or shell commands."""
from typing import Any
from pydantic import Field
from .core import Model, Context, DomainError, evaluate, ensure


class Step(Model):
    step_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
    calculation_id: str
    inputs: dict[str, Any]


class Workflow(Model):
    context: Context = Field(default_factory=Context)
    steps: list[Step] = Field(min_length=1, max_length=50)


def run_workflow(workflow: Workflow):
    """References are {"$ref": "previous_step.outputs.field"}. Forward refs are rejected."""
    results = {}

    def resolve(value, depth=0):
        ensure(depth <= 30, "Workflow input nesting exceeds 30", "invalid_workflow")
        if isinstance(value, dict):
            if "$ref" in value:
                ensure(set(value) == {"$ref"} and isinstance(value["$ref"], str), "Invalid reference", "invalid_workflow")
                path = value["$ref"].split(".")
                ensure(len(path) >= 3 and path[0] in results and path[1] == "outputs", "References must target outputs of earlier steps", "invalid_workflow")
                cursor = results[path[0]]
                for key in path[1:]:
                    ensure(isinstance(cursor, dict) and key in cursor, "Missing reference field", "invalid_workflow")
                    cursor = cursor[key]
                return cursor
            return {k: resolve(v, depth + 1) for k, v in value.items()}
        if isinstance(value, list):
            return [resolve(v, depth + 1) for v in value]
        return value

    for step in workflow.steps:
        ensure(step.step_id not in results, "Duplicate step_id", "invalid_workflow")
        results[step.step_id] = evaluate(step.calculation_id, resolve(step.inputs), workflow.context)
    return {"status": "succeeded", "scope": "explicit_user_composed_calculations", "steps": results}
