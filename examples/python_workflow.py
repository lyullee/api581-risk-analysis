"""Execute declarative composition from Python, without HTTP."""
import _bootstrap  # noqa: F401
from pathlib import Path
import json
from api581 import Workflow, run_workflow


def main():
    source = Path(__file__).with_name("gas_jet_workflow.json")
    result = run_workflow(Workflow.model_validate_json(source.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
