"""Registry-wide public-boundary smoke tests.

These tests deliberately do not invent engineering inputs.  For each API with
required fields, an empty request must be rejected by the typed public
``evaluate`` boundary before the calculation function runs.  This proves
contract wiring without presenting arbitrary values as equation validation.
"""
import importlib

import pytest
from pydantic import ValidationError

from api581 import DomainError, evaluate
from api581.core import REGISTRY


def test_every_registry_entry_has_public_boundary_and_rejects_missing_required_inputs():
    checked = 0
    default_only = []
    for identifier, calculation in REGISTRY.items():
        domain, name = identifier.split("/", 1)
        function = getattr(importlib.import_module(f"api581.api.{domain}"), name.replace("-", "_"))
        assert callable(function), identifier
        required = [field for field in calculation.model.model_fields.values() if field.is_required()]
        if not required:
            default_only.append(identifier)
            continue
        checked += 1
        with pytest.raises((ValidationError, DomainError)):
            evaluate(identifier, {})
    assert checked + len(default_only) == len(REGISTRY)
    # Default-only APIs are intentionally not invoked: some are optional
    # native capability probes and must not be turned into environment tests.
    assert default_only
