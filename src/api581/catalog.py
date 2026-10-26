"""Read-only discovery for Python clients; no service or database required."""
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
import json
from copy import deepcopy
from collections import Counter
from typing import Literal
from pydantic import Field
from .core import Model, REGISTRY, ensure


_NATIVE_VALIDATION_EVIDENCE = {
    "dispersion/native-engine-capabilities": ["verify_native_dispersion.py"],
    "dispersion/native-pool-centreline": ["verify_native_dispersion.py"],
    "dispersion/native-pool-footprint": ["verify_native_footprint.py"],
    "dispersion/native-pool-flash-fire": ["verify_native_footprint.py"],
    "dispersion/native-jet-centreline": ["verify_native_jet.py"],
    "dispersion/native-jet-footprint": ["verify_native_jet.py"],
    "dispersion/native-pool-toxic-consequence": ["verify_native_toxic.py"],
    "dispersion/partitioned-jet-centreline": ["verify_native_jet.py"],
    "dispersion/partitioned-jet-footprint": ["verify_native_jet.py"],
    "dispersion/flashed-boiling-pool-centreline": ["verify_native_flash_pool.py"],
    "dispersion/flashed-boiling-pool-footprint": ["verify_native_flashed_pool_footprint.py"],
    "dispersion/flashed-boiling-pool-flash-fire": ["verify_native_flashed_pool_footprint.py"],
    "risk/flashed-pool-flash-fire-contribution": ["verify_native_flashed_pool_risk.py"],
    "properties/pure-fluid-flash": ["verify_native_flash.py"],
    "release/pure-liquid-flash-partition": ["verify_native_flash.py"],
    "properties/pure-fluid-saturation-pressure": ["verify_native_saturation.py"],
    "properties/pure-fluid-saturation-temperature": ["verify_native_saturation.py"],
}


def _software_test_evidence() -> dict[str, tuple[str, ...]]:
    try:
        payload = json.loads(files("api581").joinpath("data/software-test-evidence.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {identifier: tuple(paths) for identifier, paths in payload.get("calculations", {}).items()}


_SOFTWARE_TEST_EVIDENCE = _software_test_evidence()


def _public_test_evidence() -> dict[str, tuple[str, ...]]:
    try:
        payload = json.loads(files("api581").joinpath("data/software-test-evidence.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {identifier: tuple(paths) for identifier, paths in payload.get("direct_public_test_calculations", {}).items()}


_PUBLIC_TEST_EVIDENCE = _public_test_evidence()


def _registry_contract_test_evidence() -> dict[str, tuple[str, ...]]:
    try:
        payload = json.loads(files("api581").joinpath("data/software-test-evidence.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {identifier: tuple(paths) for identifier, paths in payload.get("registry_contract_test_calculations", {}).items()}


_REGISTRY_CONTRACT_TEST_EVIDENCE = _registry_contract_test_evidence()


def _reference_fixture_evidence() -> dict[str, tuple[dict, ...]]:
    try:
        payload = json.loads(files("api581").joinpath("data/reference-fixture-evidence.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {identifier: tuple(fixtures) for identifier, fixtures in payload.get("fixtures", {}).items()}


_REFERENCE_FIXTURE_EVIDENCE = _reference_fixture_evidence()

_SCOPE_BOUNDARIES = (
)


@dataclass(frozen=True)
class CalculationInfo:
    identifier: str
    python_path: str
    title: str
    input_type: type[Model]
    output_type: type[Model]
    references: tuple[str, ...]
    origin: str
    limitations: tuple[str, ...]


class ScopeBoundary(Model):
    """Typed record for an intentionally unsupported calculation boundary."""
    boundary_id: str = Field(min_length=1, max_length=200)
    status: Literal["not_implemented"]
    category: Literal["external_reference_scope", "native_engine_scope"]
    reason: str = Field(min_length=1, max_length=1000)
    next_evidence_needed: str = Field(min_length=1, max_length=1000)
    related_calculation_ids: tuple[str, ...] = Field(min_length=1, max_length=20)


def describe(identifier: str) -> CalculationInfo:
    from .outputs import OUTPUT_MODELS
    ensure(identifier in REGISTRY, f"Unknown calculation: {identifier}", "unknown_calculation")
    item = REGISTRY[identifier]
    domain, name = identifier.split("/")
    return CalculationInfo(identifier, f"api581.api.{domain}.{name.replace('-', '_')}",
                           item.title, item.model, OUTPUT_MODELS[identifier],
                           item.references, item.origin, item.limitations)


def list_calculations(domain: str | None = None) -> tuple[CalculationInfo, ...]:
    """Return all calculations, optionally selecting one engineering domain."""
    return tuple(describe(identifier) for identifier in REGISTRY
                 if domain is None or identifier.split("/")[0] == domain)


@lru_cache(maxsize=1)
def _coverage_source() -> dict:
    """Load the immutable packaged ledger once per interpreter."""
    return json.loads(files("api581").joinpath("data/coverage.json").read_text(encoding="utf-8"))


def coverage() -> dict:
    """Return a copy of the source-heading inventory.

    The packaged ledger is cached for repeated QA/catalog queries, while each
    caller receives an independent copy so mutations cannot leak between
    callers. Partial headings do not imply full compliance.
    """
    return deepcopy(_coverage_source())


@lru_cache(maxsize=1)
def _coverage_sections() -> tuple[dict, ...]:
    """Return the cached section records for internal read-only queries."""
    return tuple(_coverage_source()["sections"])


def coverage_summary() -> dict:
    """Return a compact immutable-source implementation-status summary.

    The counts describe registered heading links and review evidence, not a
    certification or a claim that every standard paragraph is implemented.
    """
    data = coverage()
    sections = data["sections"]
    status_counts = dict(Counter(item["status"] for item in sections))
    category_status_counts: dict[str, dict[str, int]] = {}
    scope_status_counts: dict[str, dict[str, int]] = {}
    for item in sections:
        category = item.get("review_category", "uncategorized")
        bucket = category_status_counts.setdefault(category, {})
        status = item["status"]
        bucket[status] = bucket.get(status, 0) + 1
        scope = item["id"].split(" §", 1)[0]
        scope_bucket = scope_status_counts.setdefault(scope, {})
        scope_bucket[status] = scope_bucket.get(status, 0) + 1
    linked_calculations = {identifier for item in sections
                           for identifier in item.get("calculation_ids", [])}
    unlinked_calculations = sorted(set(REGISTRY) - linked_calculations)
    unreferenced_calculations = sorted(
        identifier for identifier, calculation in REGISTRY.items()
        if not calculation.references
    )
    unlinked_details = []
    for identifier in unlinked_calculations:
        origin = REGISTRY[identifier].origin
        reason = "adapter_contract" if origin.startswith("optional_native_") else "engineering_utility"
        unlinked_details.append({"calculation_id": identifier, "origin": origin, "reason": reason})
    validation_counts = dict(Counter(
        "native_engine_fixture_verified" if identifier in _NATIVE_VALIDATION_EVIDENCE
        else "software_tested_only"
        for identifier in REGISTRY
    ))
    with_direct_test = sum(bool(_SOFTWARE_TEST_EVIDENCE.get(identifier, ())) for identifier in REGISTRY)
    direct_test_counts = {
        "with_direct_test": with_direct_test,
        "without_direct_test": len(REGISTRY) - with_direct_test,
    }
    direct_public_test_count = sum(bool(_PUBLIC_TEST_EVIDENCE.get(identifier, ())) for identifier in REGISTRY)
    direct_public_test_counts = {
        "with_public_test": direct_public_test_count,
        "without_public_test": len(REGISTRY) - direct_public_test_count,
    }
    validation_by_domain: dict[str, dict[str, int]] = {}
    for identifier in REGISTRY:
        domain = identifier.split("/", 1)[0]
        bucket = validation_by_domain.setdefault(domain, {
            "native_engine_fixture_verified": 0,
            "software_tested_only": 0,
            "with_direct_test": 0,
            "without_direct_test": 0,
            "with_public_test": 0,
            "without_public_test": 0,
        })
        level = "native_engine_fixture_verified" if identifier in _NATIVE_VALIDATION_EVIDENCE else "software_tested_only"
        bucket[level] += 1
        bucket["with_direct_test" if _SOFTWARE_TEST_EVIDENCE.get(identifier, ()) else "without_direct_test"] += 1
        bucket["with_public_test" if _PUBLIC_TEST_EVIDENCE.get(identifier, ()) else "without_public_test"] += 1
    from .standard import documentary_coverage
    documentary = documentary_coverage().model_dump(mode="json")
    reference_fixture_count = sum(len(items) for items in _REFERENCE_FIXTURE_EVIDENCE.values())
    return {"standard_edition": data["standard_edition"],
        "source_sha256": data["source_sha256"],
        "calculation_count": data["calculation_count"],
        "section_count": data["section_count"],
        "status_counts": status_counts,
        "category_status_counts": category_status_counts,
        "scope_status_counts": scope_status_counts,
        "validation_counts": validation_counts,
        "direct_test_counts": direct_test_counts,
        "direct_public_test_count": direct_public_test_count,
        "direct_public_test_counts": direct_public_test_counts,
        "validation_by_domain": validation_by_domain,
        "documentary_coverage": documentary,
        "reference_fixture_count": reference_fixture_count,
        "scope_boundary_count": len(_SCOPE_BOUNDARIES),
        "unreferenced_calculation_ids": unreferenced_calculations,
        "unlinked_calculation_count": len(unlinked_calculations),
        "unlinked_calculation_ids": unlinked_calculations,
        "unlinked_calculation_details": unlinked_details}


def clause_evidence(clause_id: str) -> dict:
    """Return one clause's status and calculation evidence from the source ledger."""
    ensure(bool(clause_id.strip()), "clause_id must not be blank", "invalid_clause_id")
    item = next((section for section in _coverage_sections() if section["id"] == clause_id), None)
    ensure(item is not None, f"Unknown clause: {clause_id}", "unknown_clause")
    result = dict(item)
    result.setdefault("next_evidence_needed",
                     "Read the source clause and attach an independent equation/table or engineering validation record.")
    calculation_ids = tuple(item.get("calculation_ids", ()))
    evidence = [calculation_evidence(identifier) for identifier in calculation_ids]
    result["calculation_count"] = len(calculation_ids)
    result["native_engine_calculation_ids"] = [
        record["calculation_id"] for record in evidence
        if record["validation_level"] == "native_engine_fixture_verified"
    ]
    result["software_tested_calculation_ids"] = [
        record["calculation_id"] for record in evidence
        if record["validation_level"] == "software_tested_only"
    ]
    result["direct_test_module_count"] = len({
        module for record in evidence for module in record["software_test_modules"]
    })
    return result


def review_queue(*, status: str | None = None,
                 review_category: str | None = None,
                 scope: str | None = None) -> tuple[dict, ...]:
    """Return source-clause review items using explicit composable filters.

    This is a read-only evidence index, not a compliance assertion. Filters
    are validated so misspelled values cannot silently produce an empty queue.
    """
    allowed_statuses = {"partial", "not_implemented"}
    allowed_categories = {"technical_scope_review", "supporting_text_review"}
    if status is not None:
        ensure(status in allowed_statuses, f"Unknown review status: {status}", "invalid_review_status")
    if review_category is not None:
        ensure(review_category in allowed_categories,
               f"Unknown review category: {review_category}", "invalid_review_category")
    if scope is not None:
        ensure(scope.strip(), "scope must not be blank", "invalid_review_scope")
    selected = []
    for item in _coverage_sections():
        if status is not None and item["status"] != status:
            continue
        if review_category is not None and item.get("review_category") != review_category:
            continue
        if scope is not None and not item["id"].startswith(scope):
            continue
        selected.append(dict(item))
    return tuple(selected)


def calculation_evidence(identifier: str) -> dict:
    """Return the reverse traceability record for one registered calculation.

    Clause links are evidence of source mapping only; they do not assert that
    every paragraph or engineering assumption has been independently
    certified.
    """
    info = describe(identifier)
    linked = [item for item in _coverage_sections()
              if identifier in item.get("calculation_ids", [])]
    direct = [item["id"] for item in linked
              if identifier in item.get("assigned_calculation_ids", [])]
    descendant_only = [item["id"] for item in linked
                       if identifier not in item.get("assigned_calculation_ids", [])]
    native_evidence = identifier in _NATIVE_VALIDATION_EVIDENCE
    return {
        "calculation_id": info.identifier,
        "python_path": info.python_path,
        "title": info.title,
        "references": list(info.references),
        "method_origin": info.origin,
        "limitations": list(info.limitations),
        "clause_ids": [item["id"] for item in linked],
        "clause_count": len(linked),
        "direct_clause_ids": direct,
        "descendant_evidence_clause_ids": descendant_only,
        "review_categories": sorted({item.get("review_category", "uncategorized") for item in linked}),
        "validation_evidence": [
            {
                "manifest": "docs/NATIVE_ENGINE_EVIDENCE.json",
                "packaged_manifest": "api581/data/native-engine-evidence.json",
                "verification_scripts": _NATIVE_VALIDATION_EVIDENCE.get(identifier, []),
            }
        ] if native_evidence else [],
        "software_test_modules": list(_SOFTWARE_TEST_EVIDENCE.get(identifier, ())),
        "direct_public_test_modules": list(_PUBLIC_TEST_EVIDENCE.get(identifier, ())),
        "registry_contract_test_modules": list(_REGISTRY_CONTRACT_TEST_EVIDENCE.get(identifier, ())),
        "reference_fixture_evidence": list(_REFERENCE_FIXTURE_EVIDENCE.get(identifier, ())),
        "validation_level": "native_engine_fixture_verified" if native_evidence else "software_tested_only",
        "validation_status": "software_tested_not_independently_certified",
    }


def validation_queue(*, validation_level: str | None = None,
                     direct_test: bool | None = None,
                     public_test: bool | None = None,
                     domain: str | None = None) -> tuple[dict, ...]:
    """Return calculation validation records for QA and release pipelines.

    ``software_tested_only`` is the default state for calculations without a
    native-engine fixture. ``native_engine_fixture_verified`` means the
    checked-in SLABx/CoolProp fixture and verification script were rerun; it
    still does not constitute independent engineering certification. The
    optional ``domain`` filter narrows the queue to one engineering domain,
    and may be combined with ``validation_level``, ``direct_test`` and
    ``public_test``. ``public_test`` specifically means a test invokes the
    public ``evaluate`` boundary, not merely that the ID appears in a test.
    """
    allowed = {"software_tested_only", "native_engine_fixture_verified"}
    if validation_level is not None:
        ensure(validation_level in allowed,
               f"Unknown validation_level: {validation_level}",
               "invalid_validation_level")
    if direct_test is not None:
        ensure(isinstance(direct_test, bool),
               "direct_test must be boolean or None", "invalid_direct_test_filter")
    if public_test is not None:
        ensure(isinstance(public_test, bool),
               "public_test must be boolean or None", "invalid_public_test_filter")
    if domain is not None:
        ensure(isinstance(domain, str) and bool(domain.strip()),
               "domain must be a non-empty string or None", "invalid_domain_filter")
    records = []
    for identifier in REGISTRY:
        if domain is not None and identifier.split("/", 1)[0] != domain:
            continue
        item = calculation_evidence(identifier)
        if validation_level is None or item["validation_level"] == validation_level:
            has_direct_test = bool(item["software_test_modules"])
            if direct_test is None or has_direct_test == direct_test:
                has_public_test = bool(item["direct_public_test_modules"])
                if public_test is None or has_public_test == public_test:
                    records.append(item)
    return tuple(records)


def scope_boundaries() -> tuple[ScopeBoundary, ...]:
    """Return explicit calculation scope boundaries and next evidence needs."""
    return tuple(ScopeBoundary.model_validate(item) for item in _SCOPE_BOUNDARIES)


def audit_coverage() -> dict:
    """Run structural integrity checks over the packaged source ledger.

    A passing audit proves internal inventory consistency only; it is not a
    claim of API 581 compliance or independent engineering validation.
    """
    data = coverage()
    sections = data["sections"]
    ids = [item["id"] for item in sections]
    linked = {identifier for item in sections for identifier in item.get("calculation_ids", [])}
    technical_missing = [item["id"] for item in sections
                         if item["status"] == "not_implemented"
                         and item.get("review_category") == "technical_scope_review"]
    technical_without_links = [item["id"] for item in sections
                               if item.get("review_category") == "technical_scope_review"
                               and not item.get("calculation_ids")]
    valid_categories = {"technical_scope_review", "supporting_text_review"}
    invalid_categories = [item["id"] for item in sections
                          if item.get("review_category") not in valid_categories]
    unknown_links = sorted(linked - set(REGISTRY))
    unlinked = sorted(set(REGISTRY) - linked)
    classified_unlinked = all(
        REGISTRY[identifier].origin == "engineering_utility"
        or REGISTRY[identifier].origin.startswith("optional_native_")
        for identifier in unlinked
    )
    native_without_evidence = [
        identifier for identifier, calculation in REGISTRY.items()
        if calculation.origin.startswith("optional_native_")
        and identifier not in _NATIVE_VALIDATION_EVIDENCE
    ]
    calculations_without_limitations = [
        identifier for identifier, calculation in REGISTRY.items()
        if not calculation.limitations
    ]
    unreferenced_nonutilities = [
        identifier for identifier, calculation in REGISTRY.items()
        if not calculation.references and calculation.origin != "engineering_utility"
    ]
    unimplemented_without_next_evidence = [
        item["id"] for item in sections
        if item["status"] == "not_implemented"
        and not str(item.get("next_evidence_needed", "")).strip()
    ]
    checks = {
        "section_count_matches": len(sections) == data["section_count"],
        "calculation_count_matches": len(REGISTRY) == data["calculation_count"],
        "unique_section_ids": len(ids) == len(set(ids)),
        "all_links_registered": not unknown_links,
        "no_unimplemented_technical_scope": not technical_missing,
        "technical_scope_has_calculation_link": not technical_without_links,
        "review_categories_valid": not invalid_categories,
        "unlinked_calculations_classified": classified_unlinked,
        "native_calculations_have_evidence": not native_without_evidence,
        "calculations_have_limitations": not calculations_without_limitations,
        "unreferenced_calculations_are_utilities": not unreferenced_nonutilities,
        "unimplemented_items_have_next_evidence": not unimplemented_without_next_evidence,
    }
    return {"ok": all(checks.values()), "checks": checks,
            "unknown_calculation_links": unknown_links,
            "technical_scope_missing": technical_missing,
            "technical_scope_without_calculation": technical_without_links,
            "invalid_review_categories": invalid_categories,
            "unlinked_calculation_ids": unlinked,
            "native_calculations_without_evidence": native_without_evidence,
            "calculations_without_limitations": calculations_without_limitations,
            "unreferenced_calculation_ids": [
                identifier for identifier, calculation in REGISTRY.items()
                if not calculation.references
            ],
            "unreferenced_nonutilities": unreferenced_nonutilities,
            "unimplemented_without_next_evidence": unimplemented_without_next_evidence}
