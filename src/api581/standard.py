"""Read-only API 581 Part 1 standard metadata.

The metadata is extracted from the supplied 2016 PDF during the source-data
build and packaged as JSON.  These helpers are deliberately documentary: they
do not infer applicability, replace engineering qualification, or act as
calculation inputs.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

from pydantic import ConfigDict, Field

from .core import Model, ensure

__all__ = [
    "StandardDefinition", "StandardAcronym", "StandardReference", "StandardSection", "SupportingTextLocator", "SupportingTextReview", "DocumentaryCoverage", "standard_metadata",
    "definitions", "definition", "acronyms", "acronym",
    "references", "reference", "sections", "section", "supporting_text_review", "documentary_coverage",
]


class StandardDefinition(Model):
    model_config = ConfigDict(frozen=True)
    clause: str = Field(min_length=1)
    term: str = Field(min_length=1)
    acronym: str | None = None
    definition: str = Field(min_length=1)
    source_page: int = Field(gt=0)


class StandardAcronym(Model):
    model_config = ConfigDict(frozen=True)
    acronym: str = Field(min_length=1)
    expansion: str = Field(min_length=1)
    source_page: int = Field(gt=0)


class StandardReference(Model):
    model_config = ConfigDict(frozen=True)
    category: str = Field(pattern=r"^(normative|informative)$")
    number: int = Field(gt=0)
    citation: str = Field(min_length=1)
    source_page: int = Field(gt=0)


class StandardSection(Model):
    """Typed view of one source-heading ledger entry."""
    model_config = ConfigDict(extra="ignore", frozen=True)
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(pattern=r"^(partial|not_implemented)$")
    review_category: str = Field(pattern=r"^(technical_scope_review|supporting_text_review)$")
    scope: str = Field(min_length=1)
    calculation_ids: tuple[str, ...] = ()
    next_evidence_needed: str = Field(min_length=1)


class SupportingTextLocator(Model):
    """Immutable source locator and extracted-page fingerprint."""
    model_config = ConfigDict(extra="ignore", frozen=True)
    pdf: str = Field(min_length=1)
    toc_pdf_page: int | None = Field(default=None, ge=1)
    printed_page_in_part: str | None = None
    extracted_page_text_sha256: str = Field(min_length=64, max_length=64)
    extracted_page_text_bytes: int = Field(ge=0)


class SupportingTextReview(Model):
    """Typed provenance record for a non-calculational source heading."""
    model_config = ConfigDict(extra="ignore", frozen=True)
    clause_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    source_locator: SupportingTextLocator
    review_category: str = Field(pattern=r"^(technical_scope_review|supporting_text_review)$")
    classification: str = Field(min_length=1)
    evidence_target: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    calculation_ids: tuple[str, ...] = ()


class DocumentaryCoverage(Model):
    """Typed documentary-evidence boundary for the source heading ledger."""
    model_config = ConfigDict(frozen=True)
    standard_edition: str = Field(min_length=1)
    source_sha256: str = Field(min_length=64, max_length=64)
    metadata_sources: dict[str, str]
    metadata_covered_section_ids: tuple[str, ...]
    metadata_covered_count: int = Field(ge=0)
    supporting_review_section_ids: tuple[str, ...]
    supporting_review_count: int = Field(ge=0)
    unimplemented_supporting_section_ids: tuple[str, ...]
    unimplemented_supporting_count: int = Field(ge=0)


@lru_cache(maxsize=1)
def _metadata() -> dict[str, Any]:
    resource = files("api581").joinpath("data/standard-metadata.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def standard_metadata() -> dict[str, str | int]:
    """Return edition and source identifiers without exposing mutable tables."""
    payload = _metadata()
    coverage = json.loads(files("api581").joinpath("data/coverage.json").read_text(encoding="utf-8"))
    return {"standard_edition": payload["standard_edition"], "source": payload["source"],
            "source_sha256": payload["source_sha256"],
            "definition_count": len(payload["definitions"]), "acronym_count": len(payload["acronyms"]),
            "reference_count": len(payload["references"]), "section_count": len(coverage["sections"])}


@lru_cache(maxsize=1)
def _definitions() -> tuple[StandardDefinition, ...]:
    return tuple(StandardDefinition.model_validate(item) for item in _metadata()["definitions"])


@lru_cache(maxsize=1)
def _acronyms() -> tuple[StandardAcronym, ...]:
    return tuple(StandardAcronym.model_validate(item) for item in _metadata()["acronyms"])


@lru_cache(maxsize=1)
def _references() -> tuple[StandardReference, ...]:
    return tuple(StandardReference.model_validate(item) for item in _metadata()["references"])


@lru_cache(maxsize=1)
def _sections() -> tuple[StandardSection, ...]:
    resource = files("api581").joinpath("data/coverage.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    normalized = []
    for item in payload["sections"]:
        row = dict(item)
        row["scope"] = row["id"].split(" §", 1)[0]
        normalized.append(row)
    return tuple(StandardSection.model_validate(item) for item in normalized)


@lru_cache(maxsize=1)
def _supporting_text_reviews() -> tuple[SupportingTextReview, ...]:
    resource = files("api581").joinpath("data/supporting-text-review.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    return tuple(SupportingTextReview.model_validate(item) for item in payload["clauses"])


def definitions(query: str | None = None) -> tuple[StandardDefinition, ...]:
    """List definitions, optionally matching term, acronym, clause, or text."""
    items = _definitions()
    if query is None:
        return items
    needle = query.strip().casefold()
    ensure(needle, "query must not be blank", "invalid_standard_query")
    return tuple(item for item in items if needle in " ".join(
        value for value in (item.term, item.acronym or "", item.clause, item.definition)
    ).casefold())


def definition(term_or_clause: str) -> StandardDefinition:
    """Return one exact definition or raise a typed documentary error."""
    needle = term_or_clause.strip().casefold()
    ensure(needle, "term_or_clause must not be blank", "invalid_standard_query")
    matches = tuple(item for item in _definitions()
                    if item.term.casefold() == needle or item.clause.casefold() == needle)
    ensure(len(matches) == 1, "No unique API 581 definition matched the query", "standard_definition_not_found")
    return matches[0]


def acronyms(prefix: str | None = None) -> tuple[StandardAcronym, ...]:
    """List acronyms, optionally by case-insensitive prefix."""
    items = _acronyms()
    if prefix is None:
        return items
    needle = prefix.strip().casefold()
    ensure(needle, "prefix must not be blank", "invalid_standard_query")
    return tuple(item for item in items if item.acronym.casefold().startswith(needle))


def acronym(key: str) -> StandardAcronym:
    """Return one exact acronym expansion or raise a typed documentary error."""
    needle = key.strip().casefold()
    ensure(needle, "key must not be blank", "invalid_standard_query")
    matches = tuple(item for item in _acronyms() if item.acronym.casefold() == needle)
    ensure(len(matches) == 1, "No unique API 581 acronym matched the query", "standard_acronym_not_found")
    return matches[0]


def references(category: str | None = None) -> tuple[StandardReference, ...]:
    """List Part 1 §2 references, optionally filtered by category."""
    items = _references()
    if category is None:
        return items
    needle = category.strip().casefold()
    ensure(needle in {"normative", "informative"},
           "category must be normative or informative", "invalid_standard_query")
    return tuple(item for item in items if item.category == needle)


def reference(number: int, *, category: str = "informative") -> StandardReference:
    """Return one Part 1 §2 reference by category and source number."""
    matches = tuple(item for item in references(category) if item.number == number)
    ensure(len(matches) == 1, "No unique API 581 reference matched the query", "standard_reference_not_found")
    return matches[0]


def sections(*, status: str | None = None, review_category: str | None = None,
             scope: str | None = None) -> tuple[StandardSection, ...]:
    """List source headings from the packaged coverage ledger with filters."""
    if status is not None:
        ensure(status in {"partial", "not_implemented"},
               "status must be partial or not_implemented", "invalid_standard_query")
    if review_category is not None:
        ensure(review_category in {"technical_scope_review", "supporting_text_review"},
               "review_category is not recognized", "invalid_standard_query")
    if scope is not None:
        ensure(isinstance(scope, str) and bool(scope.strip()),
               "scope must be a non-empty string or None", "invalid_standard_query")
    return tuple(item for item in _sections()
                 if (status is None or item.status == status)
                 and (review_category is None or item.review_category == review_category)
                 and (scope is None or item.scope.casefold() == scope.strip().casefold()))


def section(section_id: str) -> StandardSection:
    """Return one source heading and its next evidence requirement."""
    needle = section_id.strip().casefold()
    ensure(needle, "section_id must not be blank", "invalid_standard_query")
    matches = tuple(item for item in _sections() if item.id.casefold() == needle)
    ensure(len(matches) == 1, "No unique API 581 source section matched the query", "standard_section_not_found")
    return matches[0]


def supporting_text_review(clause_id: str | None = None) -> tuple[SupportingTextReview, ...]:
    """Return source-locator and evidence-routing records for supporting headings."""
    items = _supporting_text_reviews()
    if clause_id is None:
        return items
    needle = clause_id.strip().casefold()
    ensure(needle, "clause_id must not be blank", "invalid_standard_query")
    matches = tuple(item for item in items if item.clause_id.casefold() == needle)
    ensure(matches, "No supporting-text review matched the clause", "standard_section_not_found")
    return matches


def documentary_coverage() -> DocumentaryCoverage:
    """Summarize source headings covered by extracted documentary metadata.

    Part 1 §2 (references) and Part 1 §3 (definitions/acronyms) are not
    numerical calculation clauses, but their source data is packaged and
    queryable through this module.  The remaining supporting-text headings
    stay explicitly listed so metadata extraction is not mistaken for full
    clause interpretation.
    """
    source_sections = _sections()
    metadata_prefixes = ("Part 1 §2", "Part 1 §3")
    covered = tuple(item.id for item in source_sections
                    if item.id.startswith(metadata_prefixes))
    supporting_review = tuple(item.id for item in source_sections
                              if item.review_category == "supporting_text_review"
                              and item.id not in covered)
    unimplemented = tuple(item.id for item in source_sections
                          if item.status == "not_implemented")
    metadata = standard_metadata()
    return DocumentaryCoverage.model_validate({
        "standard_edition": metadata["standard_edition"],
        "source_sha256": metadata["source_sha256"],
        "metadata_sources": {
            "references": "standard-metadata.json:references",
            "definitions": "standard-metadata.json:definitions",
            "acronyms": "standard-metadata.json:acronyms",
        },
        "metadata_covered_section_ids": covered,
        "metadata_covered_count": len(covered),
        "supporting_review_section_ids": supporting_review,
        "supporting_review_count": len(supporting_review),
        "unimplemented_supporting_section_ids": unimplemented,
        "unimplemented_supporting_count": len(unimplemented),
    })
