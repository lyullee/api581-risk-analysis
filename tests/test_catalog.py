from api581 import audit_coverage, calculation_evidence, clause_evidence, coverage, coverage_summary, describe, list_calculations, review_queue, validation_queue, scope_boundaries, DomainError
from api581.api import release
from hashlib import sha256
import json
from pathlib import Path
import pytest


def test_catalog_exposes_public_types_and_domain_filter():
    info = describe("release/gas")
    assert info.python_path == "api581.api.release.gas"
    assert info.input_type is release.GasInput
    assert info.output_type is release.GasOutput
    assert info.references and info.limitations
    assert all(item.identifier.startswith("release/") for item in list_calculations("release"))
    assert list_calculations("missing") == ()
    with pytest.raises(DomainError) as error:
        describe("missing")
    assert error.value.code == "unknown_calculation"


def test_coverage_is_packaged_and_not_shared_mutable_state():
    original = coverage()
    assert original
    original.clear()
    assert coverage()


def test_coverage_summary_exposes_review_status_without_claiming_certification():
    summary = coverage_summary()
    assert summary['calculation_count'] == len(list_calculations())
    assert summary['section_count'] == 861
    assert summary['status_counts']['partial'] > 0
    assert summary['status_counts']['not_implemented'] > 0
    assert summary['category_status_counts']
    assert summary['scope_status_counts']['Part 2']['partial'] == 277
    assert summary['scope_status_counts']['Part 2']['not_implemented'] == 27
    assert summary['unlinked_calculation_count'] == 10
    assert summary['unlinked_calculation_ids'] == sorted([
        'api520/critical-pressure-ratio', 'api520/flow-coefficient-c',
        'api520/gas-critical-area', 'api520/gas-subcritical-area',
        'api520/liquid-area', 'api520/liquid-viscosity-factor',
        'api520/relieving-pressure', 'api520/gas-critical-capacity',
        'api520/gas-subcritical-capacity', 'api520/liquid-capacity',
    ])
    assert summary['validation_counts'] == {
        'software_tested_only': 492,
            'native_engine_fixture_verified': 17,
    }
    assert summary['direct_test_counts'] == {
                            'with_direct_test': 509,
                                'without_direct_test': 0,
    }
    assert summary['direct_public_test_count'] == 323
    assert summary['direct_public_test_counts'] == {
                'with_public_test': 323, 'without_public_test': 186,
    }
    assert summary['validation_by_domain']['dispersion']['native_engine_fixture_verified'] == 12
    assert summary['validation_by_domain']['risk']['with_direct_test'] == 7
    assert summary['validation_by_domain']['risk']['with_public_test'] == 6
    assert sum(item['with_public_test'] for item in summary['validation_by_domain'].values()) == 323
    assert summary['documentary_coverage']['metadata_covered_count'] == 6
    assert summary['documentary_coverage']['unimplemented_supporting_count'] == 76
    assert summary['reference_fixture_count'] == 108
    assert len(validation_queue(domain='dispersion', validation_level='native_engine_fixture_verified')) == 12
    assert all(item['calculation_id'].startswith('dispersion/') for item in validation_queue(domain='dispersion'))
    with pytest.raises(DomainError) as error:
        validation_queue(domain=123)
    assert error.value.code == 'invalid_domain_filter'
    assert summary['scope_boundary_count'] == 0
    assert summary['unreferenced_calculation_ids'] == []
    audit = audit_coverage()
    assert audit['checks']['calculations_have_limitations'] is True
    assert audit['calculations_without_limitations'] == []
    assert audit['checks']['unreferenced_calculations_are_utilities'] is True
    evidence = calculation_evidence('release/gas')
    assert 'tests/test_calculations.py' in evidence['software_test_modules']
    assert evidence['direct_public_test_modules'] == ['tests/test_python_api.py']
    assert calculation_evidence('risk/portfolio')['direct_public_test_modules'] == ['tests/test_python_api.py']
    assert calculation_evidence('properties/pure-fluid-flash')['validation_level'] == 'native_engine_fixture_verified'
    assert [item['calculation_id'] for item in summary['unlinked_calculation_details']] == summary['unlinked_calculation_ids']


def test_clause_evidence_returns_direct_and_next_evidence_fields():
    item = clause_evidence('Part 2 Annex B §14.2.1')
    assert item['assigned_calculation_ids'] == ['tank/bottom-soil-rate-equation']
    assert item['status'] == 'partial'
    assert item['next_evidence_needed']
    assert item['calculation_count'] == 1
    assert item['software_tested_calculation_ids'] == ['tank/bottom-soil-rate-equation']
    assert item['native_engine_calculation_ids'] == []
    assert item['direct_test_module_count'] >= 1
    with pytest.raises(DomainError) as error:
        clause_evidence('missing clause')
    assert error.value.code == 'unknown_clause'


def test_review_queue_supporting_not_implemented_and_scope_filters():
    items = review_queue(status='not_implemented', review_category='supporting_text_review')
    assert len(items) == 76
    assert all(item['status'] == 'not_implemented' for item in items)
    part_two = review_queue(scope='Part 2', status='not_implemented')
    assert part_two
    assert all(item['id'].startswith('Part 2') for item in part_two)


def test_review_queue_rejects_unknown_filter_values():
    with pytest.raises(DomainError):
        review_queue(status='missing')
    with pytest.raises(DomainError):
        review_queue(review_category='missing')


def test_calculation_evidence_exposes_reverse_clause_links():
    item = calculation_evidence('tank/bottom-soil-rate-equation')
    assert item['clause_count'] >= 1
    assert 'Part 2 Annex B §14.2.1' in item['clause_ids']
    assert 'Part 2 Annex B §14.2.1' in item['direct_clause_ids']
    assert item['validation_status'] == 'software_tested_not_independently_certified'
    assert item['validation_level'] == 'software_tested_only'
    with pytest.raises(DomainError):
        calculation_evidence('missing')


def test_native_calculation_evidence_links_to_checked_in_engine_manifest():
    item = calculation_evidence('dispersion/native-pool-centreline')
    assert item['validation_evidence'] == [{
        'manifest': 'docs/NATIVE_ENGINE_EVIDENCE.json',
        'packaged_manifest': 'api581/data/native-engine-evidence.json',
        'verification_scripts': ['verify_native_dispersion.py'],
    }]
    assert item['validation_level'] == 'native_engine_fixture_verified'
    assert calculation_evidence('release/gas')['validation_evidence'] == []
    integrated = calculation_evidence('risk/flashed-pool-flash-fire-contribution')
    assert integrated['validation_evidence'][0]['verification_scripts'] == [
        'verify_native_flashed_pool_risk.py'
    ]


def test_validation_queue_distinguishes_native_fixture_from_software_only():
    native = validation_queue(validation_level='native_engine_fixture_verified')
    software = validation_queue(validation_level='software_tested_only')
    assert native
    assert software
    assert all(item['validation_level'] == 'native_engine_fixture_verified' for item in native)
    assert all(item['validation_level'] == 'software_tested_only' for item in software)
    assert len(native) + len(software) == len(list_calculations())
    direct = validation_queue(direct_test=True)
    indirect = validation_queue(direct_test=False)
    assert direct
    assert not indirect
    assert len(direct) + len(indirect) == len(list_calculations())
    assert all(item['software_test_modules'] for item in direct)
    assert all(not item['software_test_modules'] for item in indirect)
    public = validation_queue(public_test=True)
    non_public = validation_queue(public_test=False)
    assert len(public) == 323
    assert len(public) + len(non_public) == len(list_calculations())
    assert all(item['direct_public_test_modules'] for item in public)
    with pytest.raises(DomainError) as error:
        validation_queue(public_test='yes')
    assert error.value.code == 'invalid_public_test_filter'
    with pytest.raises(DomainError) as error:
        validation_queue(validation_level='independently_certified')
    assert error.value.code == 'invalid_validation_level'


def test_scope_boundaries_are_explicit_and_copy_safe():
    boundaries = scope_boundaries()
    assert boundaries == ()


def test_vertical_rise_is_native_verified_without_scope_boundary():
    assert scope_boundaries() == ()
    evidence = calculation_evidence('dispersion/native-jet-centreline')
    assert evidence['validation_level'] == 'native_engine_fixture_verified'
    assert evidence['validation_evidence'][0]['manifest'] == 'docs/NATIVE_ENGINE_EVIDENCE.json'
    assert evidence['validation_evidence'][0]['verification_scripts']
    assert not any('unsupported' in limitation.lower() for limitation in evidence['limitations'])


def test_audit_coverage_passes_structural_inventory_checks():
    audit = audit_coverage()
    assert audit['ok'] is True
    assert all(audit['checks'].values())
    assert audit['technical_scope_missing'] == []
    assert audit['technical_scope_without_calculation'] == []
    assert audit['invalid_review_categories'] == []
    assert audit['native_calculations_without_evidence'] == []
    assert audit['unimplemented_without_next_evidence'] == []


def test_release_evidence_matches_current_packaged_contracts():
    root = Path(__file__).parents[1]
    evidence = json.loads((root / 'docs' / 'release-evidence.json').read_text(encoding='utf-8'))
    summary = coverage_summary()
    assert evidence['calculation_count'] == len(list_calculations())
    assert evidence['section_count'] == summary['section_count']
    assert evidence['audit']['ok'] is True
    for key, relative in {
        'python_api_schema': 'docs/python-api.schema.json',
        'digital_twin_schema': 'docs/digital-twin.schema.json',
        'coverage': 'src/api581/data/coverage.json',
    }.items():
        digest = sha256((root / relative).read_bytes()).hexdigest()
        assert evidence['artifact_sha256'][key] == digest
    assert evidence['artifact_sha256']['packaged_python_api_schema'] == evidence['artifact_sha256']['python_api_schema']
    assert evidence['artifact_sha256']['packaged_digital_twin_schema'] == evidence['artifact_sha256']['digital_twin_schema']
    assert len(evidence['artifact_sha256']['standard_metadata']) == 64
    assert evidence['artifact_sha256']['completion_audit'] == sha256(
        (root / 'docs' / 'COMPLETION_AUDIT.md').read_bytes()
    ).hexdigest()
    assert evidence['source_hash_matches_coverage'] is True
    assert evidence['validation_counts']['software_tested_only'] > 0
    assert evidence['validation_counts']['native_engine_fixture_verified'] > 0
    assert sum(evidence['validation_counts'].values()) == len(list_calculations())
    assert evidence['validation_by_domain'] == summary['validation_by_domain']
    assert evidence['scope_boundary_count'] == 0
    assert set(evidence['scope_boundary_ids']) == set()


def test_registry_contract_evidence_covers_all_registered_calculations():
    records = validation_queue()
    assert len(records) == 509
    assert all(item['registry_contract_test_modules'] == ['tests/test_registry_contract.py'] for item in records)


def test_empty_clause_references_are_limited_to_declared_utilities():
    empty = {item.identifier for item in list_calculations() if not item.references}
    assert empty == set()
