import pytest

from api581 import standard
from api581.core import DomainError


def test_packaged_standard_metadata_is_source_indexed():
    metadata = standard.standard_metadata()
    assert metadata["standard_edition"] == "API-RP-581-2016-3rd-base"
    assert metadata["definition_count"] == 80
    assert metadata["acronym_count"] == 125
    assert metadata["reference_count"] == 22
    assert metadata["section_count"] == 861
    assert len(metadata["source_sha256"]) == 64


def test_definition_and_acronym_exact_lookup():
    risk = standard.definition("risk")
    assert risk.clause == "Part 1 §3.1.62"
    assert "probability" in risk.definition
    assert standard.definition("Part 1 §3.1.62").term == "risk"
    assert standard.acronym("GFF").expansion == "Generic Failure Frequency"
    assert standard.reference(1, category="normative").citation.startswith("API Recommended Practice 580")
    assert len(standard.references("informative")) == 21
    assert standard.reference(16).source_page == 4
    assert standard.reference(17).source_page == 5


def test_standard_search_is_case_insensitive_and_bounded():
    assert any(item.term == "aerosol" for item in standard.definitions("AEROSOL"))
    assert [item.acronym for item in standard.acronyms("gff")] == ["GFF"]
    with pytest.raises(DomainError) as error:
        standard.definition("does-not-exist")
    assert error.value.code == "standard_definition_not_found"
    with pytest.raises(DomainError):
        standard.definitions(" ")


def test_typed_source_section_ledger_preserves_review_state():
    item = standard.section("Part 1 §1")
    assert item.scope == "Part 1"
    assert item.status == "partial"
    assert item.next_evidence_needed
    assert len(standard.sections(status="not_implemented")) == 76
    assert all(item.review_category == "supporting_text_review"
               for item in standard.sections(review_category="supporting_text_review",
                                              status="not_implemented"))
    assert standard.sections(scope="part 1")
    with pytest.raises(DomainError) as error:
        standard.sections(scope=123)
    assert error.value.code == "invalid_standard_query"


def test_documentary_coverage_distinguishes_extracted_metadata_from_review_queue():
    coverage = standard.documentary_coverage()
    assert coverage.metadata_covered_count == 6
    assert coverage.supporting_review_count == 170
    assert coverage.unimplemented_supporting_count == 76
    assert "Part 1 §2" in coverage.metadata_covered_section_ids
    assert "Part 1 §3.1" in coverage.metadata_covered_section_ids
    assert "Part 1 §4.1.1" in coverage.supporting_review_section_ids
    assert "Part 1 §2" in coverage.unimplemented_supporting_section_ids
    assert coverage.source_sha256 == standard.standard_metadata()["source_sha256"]


def test_standard_schema_is_packaged():
    from api581 import schema

    contract = schema.standard_schema()
    assert set(contract) == {
        "StandardDefinition", "StandardAcronym", "StandardReference", "StandardSection", "DocumentaryCoverage",
    }
    assert schema.packaged_schema_hash("standard")
