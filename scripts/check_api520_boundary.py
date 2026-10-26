"""Verify the API 520 sizing boundary and its qualified calculation surface."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from api581 import REGISTRY, scope_boundaries  # noqa: E402


def main() -> None:
    forbidden = [identifier for identifier in REGISTRY if "api520" in identifier.lower() or "capacity-sizing" in identifier.lower()]
    expected = {"api520/critical-pressure-ratio", "api520/flow-coefficient-c", "api520/relieving-pressure",
                "api520/gas-critical-area", "api520/gas-subcritical-area", "api520/liquid-area",
                "api520/liquid-viscosity-factor"}
    assert expected.issubset(forbidden), f"API 520 calculation surface incomplete: {sorted(expected - set(forbidden))}"
    evidence = json.loads((ROOT / "docs" / "release-evidence.json").read_text(encoding="utf-8"))
    assert "prd/api520-capacity-sizing" not in evidence["scope_boundary_ids"]
    print(json.dumps({"status": "passed", "registry_api520_calculations": sorted(forbidden),
                      "qualification_required": "cross-standard fixture verification"}, indent=2))


if __name__ == "__main__":
    main()
