"""Packaged verification evidence accessors for installed consumers."""
from __future__ import annotations

from hashlib import sha256
from importlib.resources import files
from typing import Any, TypedDict
import json


_RESOURCE = "native-engine-evidence.json"
_SOFTWARE_TEST_RESOURCE = "software-test-evidence.json"
_REFERENCE_FIXTURE_RESOURCE = "reference-fixture-evidence.json"


class ValidationEvidence(TypedDict):
    """Stable JSON shape linking a calculation to its verification record."""
    manifest: str
    packaged_manifest: str
    verification_scripts: list[str]


def native_engine_evidence() -> dict[str, Any]:
    """Return a fresh copy of the packaged native-engine evidence manifest."""
    resource = files("api581").joinpath("data", _RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


def native_engine_evidence_hash() -> str:
    """Return the SHA-256 of the packaged native-engine evidence manifest."""
    resource = files("api581").joinpath("data", _RESOURCE)
    return sha256(resource.read_bytes()).hexdigest()


def software_test_evidence() -> dict[str, Any]:
    """Return the packaged calculation-to-test-module evidence manifest."""
    resource = files("api581").joinpath("data", _SOFTWARE_TEST_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


def software_test_evidence_hash() -> str:
    """Return the SHA-256 of the packaged software-test evidence manifest."""
    resource = files("api581").joinpath("data", _SOFTWARE_TEST_RESOURCE)
    return sha256(resource.read_bytes()).hexdigest()


def reference_fixture_evidence() -> dict[str, Any]:
    """Return deterministic hand-calculated reference fixtures."""
    resource = files("api581").joinpath("data", _REFERENCE_FIXTURE_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


def reference_fixture_evidence_hash() -> str:
    resource = files("api581").joinpath("data", _REFERENCE_FIXTURE_RESOURCE)
    return sha256(resource.read_bytes()).hexdigest()


def calculation_test_modules(identifier: str) -> list[str]:
    """Return direct test-module references for one registered calculation."""
    from .catalog import calculation_evidence
    return list(calculation_evidence(identifier)["software_test_modules"])


def calculation_public_test_modules(identifier: str) -> list[str]:
    """Return test modules that invoke the public ``evaluate`` boundary."""
    from .catalog import calculation_evidence
    return list(calculation_evidence(identifier)["direct_public_test_modules"])


def calculation_validation_evidence(identifier: str) -> list[ValidationEvidence]:
    """Return validation-manifest links for one registered calculation ID."""
    from .catalog import calculation_evidence
    return calculation_evidence(identifier)["validation_evidence"]


__all__ = [
    "ValidationEvidence", "native_engine_evidence", "native_engine_evidence_hash",
    "software_test_evidence", "software_test_evidence_hash", "calculation_test_modules",
    "calculation_public_test_modules",
    "reference_fixture_evidence", "reference_fixture_evidence_hash",
    "calculation_validation_evidence",
]
