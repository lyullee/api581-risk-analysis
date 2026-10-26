from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_native_jet_documentation_matches_buoyant_vertical_evidence():
    text = (ROOT / "docs" / "NATIVE_JET_VALIDATION.md").read_text(encoding="utf-8")
    evidence = (ROOT / "docs" / "NATIVE_ENGINE_EVIDENCE.json").read_text(encoding="utf-8")

    assert "Briggs effective-source" in text
    assert "수직 부력 Briggs effective-source native 배열 일치" in text
    assert "부력 상승 분기는 네이티브 미구현" not in text
    assert "buoyant_vertical_native_exact_arrays" in evidence

