import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_direct_test_queue_is_complete_and_packaged():
    docs = json.loads((ROOT / "docs/direct-test-queue.json").read_text(encoding="utf-8"))
    packaged = json.loads((ROOT / "src/api581/data/direct-test-queue.json").read_text(encoding="utf-8"))
    assert docs == packaged
    assert docs["calculation_count"] == 509
    assert docs["direct_test_gap_count"] == len(docs["calculations"])
    assert all(item["registry_contract_test_modules"] for item in docs["calculations"])
    assert all(item["next_action"] for item in docs["calculations"])

