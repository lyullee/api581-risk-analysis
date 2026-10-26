"""Build the packaged mapping from calculation IDs to direct test modules.

The mapping is deliberately evidence-only: a textual reference proves that a
test module addresses an API, but does not claim independent engineering
certification or that every branch is exercised.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    from api581.core import REGISTRY

    tests_root = ROOT / "tests"
    mapping = {}
    public_mapping = {}
    # This is a distinct contract layer: it exercises the public evaluate
    # boundary's validation behavior for every registry entry, but does not
    # claim that the engineering equation has a representative numeric case.
    contract_mapping = {identifier: ["tests/test_registry_contract.py"] for identifier in REGISTRY}
    for identifier in REGISTRY:
        modules = []
        public_modules = []
        # Match a complete calculation ID, not a prefix of another ID
        # (e.g. detection-isolation inside detection-isolation-rating).
        direct_reference = re.compile(
            rf"(?<![A-Za-z0-9_/-]){re.escape(identifier)}(?![A-Za-z0-9_/-])"
        )
        public_call = re.compile(
            rf"(?:\bevaluate|\bapi581\.evaluate)\(\s*['\"]{re.escape(identifier)}['\"]"
        )
        for path in sorted(tests_root.glob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            if direct_reference.search(text):
                modules.append(path.relative_to(ROOT).as_posix())
            if public_call.search(text):
                public_modules.append(path.relative_to(ROOT).as_posix())
        mapping[identifier] = modules
        public_mapping[identifier] = public_modules
    payload = {
        "description": "Direct textual test-module references by calculation ID; not independent certification.",
        "calculation_count": len(mapping),
        "calculations": mapping,
        "direct_public_test_calculations": public_mapping,
        "registry_contract_test_calculations": contract_mapping,
    }
    for destination in (
        ROOT / "src/api581/data/software-test-evidence.json",
        ROOT / "docs/software-test-evidence.json",
    ):
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "calculation_count": len(mapping),
        "direct_test_reference_count": sum(bool(v) for v in mapping.values()),
        "direct_public_test_reference_count": sum(bool(v) for v in public_mapping.values()),
    }))


if __name__ == "__main__":
    main()
