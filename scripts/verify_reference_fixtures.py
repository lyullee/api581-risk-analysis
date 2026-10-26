"""Execute hand-calculated reference fixtures against the public registry."""
from __future__ import annotations

import json
import math
from importlib.resources import files
from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import api581


def _assert_value(actual, expected, path: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise AssertionError(f"{path}: expected mapping, got {type(actual).__name__}")
        for key, value in expected.items():
            if key not in actual:
                raise AssertionError(f"{path}/{key}: missing from actual output")
            _assert_value(actual[key], value, f"{path}/{key}")
        return
    if isinstance(expected, bool) or isinstance(actual, bool):
        if actual is not expected:
            raise AssertionError(f"{path}: {actual!r} != {expected!r}")
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise AssertionError(f"{path}: {actual!r} != {expected!r}")
    elif actual != expected:
        raise AssertionError(f"{path}: {actual!r} != {expected!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-optional-missing", action="store_true",
                        help="skip fixtures whose optional engine is unavailable, reporting the count")
    args = parser.parse_args()
    manifest = json.loads(files("api581").joinpath("data/reference-fixture-evidence.json").read_text(encoding="utf-8"))
    checked = 0
    optional_skipped = 0
    for identifier, fixtures in manifest["fixtures"].items():
        for fixture in fixtures:
            try:
                result = api581.evaluate(identifier, fixture["inputs"])
            except api581.DomainError as exc:
                if args.allow_optional_missing and exc.code == "optional_engine_missing":
                    optional_skipped += 1
                    continue
                raise
            outputs = result["outputs"]
            for name, expected in fixture["expected_outputs"].items():
                _assert_value(outputs[name], expected, f"{identifier}/{fixture['case_id']}/{name}")
            checked += 1
    print(json.dumps({"fixture_count": checked, "optional_skipped_count": optional_skipped,
                      "status": "passed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
