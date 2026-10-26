"""Reject accidental empty calculation bodies in the public API package.

The two allowlisted ``pass`` statements are inheritance-only Pydantic models;
they are not calculation functions.  This is a structural guard, not a claim
that every calculation is independently certified.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "api581"
ALLOWLIST = {
    ("level1.py", "ReleaseToSteam"),
    ("physical_explosion.py", "PhysicalConsequence"),
}


def main() -> None:
    violations: list[str] = []
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(isinstance(item, ast.Pass) for item in ast.walk(node)):
                    violations.append(f"{path.relative_to(SOURCE)}:{node.lineno} function {node.name} contains pass")
            elif isinstance(node, ast.ClassDef):
                if (path.name, node.name) in ALLOWLIST:
                    continue
                if any(isinstance(item, ast.Pass) for item in node.body):
                    violations.append(f"{path.relative_to(SOURCE)}:{node.lineno} class {node.name} contains pass")
    if violations:
        raise SystemExit("Unimplemented bodies detected:\n" + "\n".join(violations))
    print(f"Checked {len(tuple(SOURCE.rglob('*.py')))} Python source files; no unimplemented bodies")


if __name__ == "__main__":
    main()
