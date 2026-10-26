"""Extract the Part 1 definitions/acronyms tables into package metadata.

This is a source-data build step, not a calculation implementation.  The PDF
is intentionally read only while generating the checked-in JSON; the runtime
package has no PDF dependency.
"""
from __future__ import annotations

import json
from hashlib import sha256
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "API-581-2016.pdf"
OUTPUT = ROOT / "src/api581/data/standard-metadata.json"
HEADER = re.compile(r"(?:RISK-BAS[K-]ED|API RECOMMENDED PRACTICE).*", re.I)
ITEM = re.compile(r"^3\.1\.(\d+)\s*$")
REFERENCE = re.compile(r"^(\d+)\.\s+(.+)$")


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split()).strip()
        if not line or HEADER.fullmatch(line) or line.isdigit():
            continue
        lines.append(line)
    return lines


def extract_definitions(reader: PdfReader) -> list[dict[str, object]]:
    text = "\n".join((reader.pages[index].extract_text() or "") for index in range(16, 24))
    lines = _clean_lines(text)
    starts = [index for index, line in enumerate(lines) if ITEM.match(line)]
    result: list[dict[str, object]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        match = ITEM.match(lines[start])
        assert match is not None
        number = int(match.group(1))
        body = lines[start + 1:end]
        if not body:
            continue
        term = body.pop(0)
        acronym = None
        if body and re.fullmatch(r"[A-Z][A-Z0-9/& -]{1,19}", body[0]) and len(body[0].split()) == 1:
            acronym = body.pop(0)
        definition = " ".join(body).strip()
        if not definition:
            raise ValueError(f"definition {number} has no text")
        source_page = (5 if number <= 7 else 6 if number <= 18 else 7 if number <= 28
                       else 8 if number <= 39 else 9 if number <= 51 else 10
                       if number <= 62 else 11 if number <= 73 else 12)
        result.append({
            "clause": f"Part 1 §3.1.{number}",
            "term": term,
            "acronym": acronym,
            "definition": definition,
            "source_page": source_page,
        })
    if len(result) != 80:
        raise ValueError(f"expected 80 definitions, got {len(result)}")
    return result


def extract_acronyms(reader: PdfReader) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for page_index in range(24, 27):
        lines = (reader.pages[page_index].extract_text() or "").splitlines()
        header_index = next(index for index, line in enumerate(lines) if "RISK-B" in line or "API RECOMMENDED" in line)
        left = [" ".join(line.split()) for line in lines[:header_index] if line.strip() and not line.strip().isdigit()]
        right = [" ".join(line.split()) for line in lines[header_index + 1:] if line.strip() and not line.strip().isdigit()]
        if len(left) != len(right):
            raise ValueError(f"acronym columns differ on PDF page {page_index + 1}: {len(left)} != {len(right)}")
        result.extend({"acronym": key, "expansion": value, "source_page": page_index + 1}
                      for key, value in zip(left, right))
    lines = _clean_lines(reader.pages[27].extract_text() or "")
    for line in lines:
        match = re.match(r"^([A-Z][A-Z0-9/&-]*)\s+(.+)$", line)
        if match and match.group(1) not in {"API", "RISK"}:
            result.append({"acronym": match.group(1), "expansion": match.group(2), "source_page": 16})
    if len(result) < 100:
        raise ValueError(f"expected acronym table, got only {len(result)} entries")
    return result


def extract_references(reader: PdfReader) -> list[dict[str, object]]:
    text = "\n".join((reader.pages[index].extract_text() or "") for index in (15, 16))
    start_match = re.search(r"2\.1.*?Normative", text, re.S)
    end_match = re.search(r"3\s+Definitions", text)
    if not start_match or not end_match:
        raise ValueError("could not locate Part 1 §2 reference table")
    text = text[start_match.start() : end_match.start()]
    lines = _clean_lines(text)
    result: list[dict[str, object]] = []
    category = None
    starts: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        if line == "Normative":
            category = "normative"
            continue
        if line == "Informative" or line.endswith("Informative"):
            category = "informative"
            continue
        match = REFERENCE.match(line)
        if match and category:
            starts.append((index, int(match.group(1)), category))
    for position, (start, number, category) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        citation = " ".join(lines[start:end])
        citation = REFERENCE.sub(r"\2", citation, count=1)
        citation = citation.replace("2.2 Informative", "").strip()
        source_page = 4 if category == "normative" or number <= 16 else 5
        result.append({"category": category, "number": number, "citation": citation, "source_page": source_page})
    if len(result) != 22 or sum(item["category"] == "normative" for item in result) != 1:
        raise ValueError(f"expected 1 normative and 21 informative references, got {len(result)}")
    return result


def main() -> None:
    reader = PdfReader(str(PDF))
    payload = {
        "standard_edition": "API-RP-581-2016-3rd-base",
        "source": "API-581-2016.pdf, Part 1 §§2-3",
        "source_sha256": sha256(PDF.read_bytes()).hexdigest(),
        "references": extract_references(reader),
        "definitions": extract_definitions(reader),
        "acronyms": extract_acronyms(reader),
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(payload['definitions'])} definitions and {len(payload['acronyms'])} acronyms")


if __name__ == "__main__":
    main()
