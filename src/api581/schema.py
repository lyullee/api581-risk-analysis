"""Read-only accessors for packaged Python and digital-twin JSON contracts."""
from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
import json
from typing import Any


def _read(name: str) -> dict[str, Any]:
    resource = files("api581").joinpath("data", name)
    return json.loads(resource.read_text(encoding="utf-8"))


def python_api_schema() -> dict[str, Any]:
    """Return a fresh mapping of the packaged calculation contracts."""
    return _read("python-api.schema.json")


def digital_twin_schema() -> dict[str, Any]:
    """Return a fresh mapping of the packaged twin and batch contracts."""
    return _read("digital-twin.schema.json")


def standard_schema() -> dict[str, Any]:
    """Return the packaged standard metadata and coverage contracts."""
    return _read("standard.schema.json")


def packaged_schema_hash(schema: str) -> str:
    """Return the SHA-256 of a packaged schema by its public name."""
    names = {
        "python_api": "python-api.schema.json",
        "digital_twin": "digital-twin.schema.json",
        "standard": "standard.schema.json",
    }
    try:
        name = names[schema]
    except KeyError as exc:
        raise ValueError(f"Unknown packaged schema: {schema}") from exc
    resource = files("api581").joinpath("data", name)
    return sha256(resource.read_bytes()).hexdigest()


__all__ = ["python_api_schema", "digital_twin_schema", "standard_schema", "packaged_schema_hash"]
