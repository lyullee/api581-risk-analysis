"""Check concrete api581 references in user-facing Markdown documentation."""
from __future__ import annotations

import importlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

TOKEN = re.compile(r"api581(?:\.[A-Za-z_]\w*)+")
FILES = (
    ROOT / "README.md",
    ROOT / "docs" / "VERIFICATION_COMMANDS.md",
    ROOT / "docs" / "MODULE_CATALOG.md",
)


def _resolve(token: str) -> None:
    parts = token.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            value = importlib.import_module(".".join(parts[:cut]))
        except ModuleNotFoundError:
            continue
        for name in parts[cut:]:
            value = getattr(value, name)
        return
    raise ImportError(token)


def main() -> None:
    checked: set[str] = set()
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for token in TOKEN.findall(text):
            if token in checked or "<" in token:
                continue
            _resolve(token)
            checked.add(token)
    print(f"Checked {len(checked)} concrete api581 documentation paths")


if __name__ == "__main__":
    main()
