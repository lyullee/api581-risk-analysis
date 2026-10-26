"""Build the explicit queue of calculations without a direct test module.

The queue is evidence routing only. It never treats registry-contract coverage
as a numeric engineering test and never invents input fixtures.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    import api581

    records = []
    for item in api581.validation_queue(direct_test=False):
        identifier = item["calculation_id"]
        domain = identifier.split("/", 1)[0]
        records.append({
            "calculation_id": identifier,
            "domain": domain,
            "title": item["title"],
            "python_path": item["python_path"],
            "references": item["references"],
            "limitations": item["limitations"],
            "validation_level": item["validation_level"],
            "registry_contract_test_modules": item["registry_contract_test_modules"],
            "next_action": "Add an independently meaningful numeric/branch fixture; do not count registry-contract validation as direct engineering coverage.",
        })
    payload = {
        "description": "Calculations lacking a direct numeric/branch test-module reference; registry contracts remain separate evidence.",
        "calculation_count": len(api581.list_calculations()),
        "direct_test_gap_count": len(records),
        "domain_counts": dict(sorted(Counter(item["domain"] for item in records).items())),
        "calculations": records,
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in (ROOT / "docs/direct-test-queue.json", ROOT / "src/api581/data/direct-test-queue.json"):
        path.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": "passed", "direct_test_gap_count": len(records), "domain_counts": payload["domain_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

