"""Export Python API catalog and JSON Schemas without a web framework."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api581 import list_calculations
from api581.digital_twin import (
    TwinBatchPlan, TwinBatchShard, TwinCalculationRequest,
    TwinCalculationResponse, TwinMeasurement,
)
from api581.standard import DocumentaryCoverage, StandardAcronym, StandardDefinition, StandardReference, StandardSection
from api581 import ScopeBoundary


def main():
    calculations = list_calculations()
    contracts = {}
    lines = ["# 독립 Python 계산 API 목록", "", "자동 생성: `scripts/export_contracts.py`.",
             "입력 모델을 생성해 함수에 전달한다. 반환값은 `CalculationResult[Output]`이며 `result.outputs.<필드>`로 계산값을 읽는다.",
             "", f"현재 {len(calculations)}개. 함수 개수는 API 581 전체 구현률을 뜻하지 않는다.", ""]
    for c in calculations:
        contracts[c.identifier] = {
            "python_path": c.python_path, "title": c.title,
            "input_schema": c.input_type.model_json_schema(),
            "output_schema": c.output_type.model_json_schema(),
            "references": c.references, "method_origin": c.origin, "limitations": c.limitations}
        lines += [f"## `{c.python_path}`", "", c.title, "", f"계산 ID: `{c.identifier}`", "",
                  f"출처: {'; '.join(c.references) or '공학 보조 계산'}", "",
                  "| 입력 | 필수 | 타입 |", "|---|---|---|"]
        for name, field in c.input_type.model_fields.items():
            lines.append(f"| `{name}` | {'예' if field.is_required() else '기본값/선택'} | `{field.annotation}` |")
        lines += ["", "출력: " + ", ".join(f"`{field}`" for field in c.output_type.model_fields), ""]
        if c.limitations:
            lines += ["적용 범위: " + " ".join(c.limitations), ""]
    python_schema_text = json.dumps(contracts, ensure_ascii=False, indent=2)
    (ROOT / "docs/python-api.schema.json").write_text(python_schema_text, encoding="utf-8")
    (ROOT / "src/api581/data/python-api.schema.json").write_text(python_schema_text, encoding="utf-8")
    twin_models = {
        "TwinMeasurement": TwinMeasurement,
        "TwinCalculationRequest": TwinCalculationRequest,
        "TwinCalculationResponse": TwinCalculationResponse,
        "TwinBatchShard": TwinBatchShard,
        "TwinBatchPlan": TwinBatchPlan,
    }
    twin_schema = {
        name: model.model_json_schema(ref_template="#/$defs/{model}")
        for name, model in twin_models.items()
    }
    twin_schema_text = json.dumps(twin_schema, ensure_ascii=False, indent=2)
    (ROOT / "docs/digital-twin.schema.json").write_text(twin_schema_text, encoding="utf-8")
    (ROOT / "src/api581/data/digital-twin.schema.json").write_text(twin_schema_text, encoding="utf-8")
    standard_models = {
        "StandardDefinition": StandardDefinition,
        "StandardAcronym": StandardAcronym,
        "StandardReference": StandardReference,
        "StandardSection": StandardSection,
        "DocumentaryCoverage": DocumentaryCoverage,
    }
    standard_schema = {
        name: model.model_json_schema(ref_template="#/$defs/{model}")
        for name, model in standard_models.items()
    }
    standard_schema_text = json.dumps(standard_schema, ensure_ascii=False, indent=2)
    (ROOT / "docs/standard.schema.json").write_text(standard_schema_text, encoding="utf-8")
    (ROOT / "src/api581/data/standard.schema.json").write_text(standard_schema_text, encoding="utf-8")
    scope_schema = {"ScopeBoundary": ScopeBoundary.model_json_schema(ref_template="#/$defs/{model}")}
    scope_schema_text = json.dumps(scope_schema, ensure_ascii=False, indent=2)
    (ROOT / "docs/scope-boundaries.schema.json").write_text(scope_schema_text, encoding="utf-8")
    (ROOT / "src/api581/data/scope-boundaries.schema.json").write_text(scope_schema_text, encoding="utf-8")
    native_evidence = ROOT / "docs/NATIVE_ENGINE_EVIDENCE.json"
    if native_evidence.exists():
        (ROOT / "src/api581/data/native-engine-evidence.json").write_text(
            native_evidence.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
    (ROOT / "docs/MODULE_CATALOG.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(calculations)} Python calculation contracts")


if __name__ == "__main__":
    main()
