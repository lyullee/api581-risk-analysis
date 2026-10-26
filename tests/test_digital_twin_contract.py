from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from api581 import digital_twin
from api581.core import DomainError
from api581.api import release


TS = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


def request(**changes):
    return digital_twin.TwinCalculationRequest(**({
        'request_id': 'req-001', 'calculation_id': 'release/orifice-area',
        'asset_id': 'asset-01', 'component_id': 'pipe-01', 'observed_at': TS,
        'source_revision': 'twin-rev-7', 'correlation_id': 'corr-01',
        'inputs': {'diameter_m': .01},
        'measurements': [{
            'measurement_id': 'm-01', 'quantity': 'diameter', 'value': .01,
            'unit': 'm', 'measured_at': TS, 'source': 'inspection',
            'quality': 'measured'}]
    } | changes))


def test_request_context_preserves_twin_identity():
    context = request().to_context()
    assert context.asset_id == 'asset-01'
    assert context.component_id == 'pipe-01'
    assert context.source_revision == 'twin-rev-7'
    assert context.observed_at == TS


def test_measurement_snapshot_is_lossless_and_keyed_by_measurement_id():
    snapshot = request().measurement_snapshot()
    assert snapshot == {
        'm-01': {
            'quantity': 'diameter', 'value': .01, 'unit': 'm',
            'measured_at': TS.isoformat(), 'source': 'inspection',
            'quality': 'measured', 'uncertainty': None,
        }
    }


def test_response_projects_typed_result_and_provenance():
    req = request()
    result = release.orifice_area(release.OrificeAreaInput(**req.inputs), context=req.to_context())
    response = digital_twin.TwinCalculationResponse.from_result(req, result)
    assert response.request_id == req.request_id
    assert response.input_hash == result.input_hash
    assert response.outputs['area_m2'] > 0
    assert response.validation_status == 'software_tested_not_independently_certified'
    assert response.validation_evidence == []
    assert response.software_test_modules
    assert response.direct_public_test_modules == []
    assert response.validation_level == 'software_tested_only'


def test_response_rejects_result_validation_level_mismatch():
    req = request()
    result = release.orifice_area(release.OrificeAreaInput(**req.inputs), context=req.to_context())
    forged = result.model_copy(update={'validation_level': 'native_engine_fixture_verified'})
    with pytest.raises(DomainError) as error:
        digital_twin.TwinCalculationResponse.from_result(req, forged)
    assert error.value.code == 'twin_contract_mismatch'


def test_response_rejects_forged_public_test_provenance():
    req = request(request_id='req-public', calculation_id='risk/portfolio', inputs={
        'components': [{'component_id': 'A', 'annual_failure_frequency': 0.1,
                        'equipment_area_risk_m2_per_year': 1.0,
                        'personnel_area_risk_m2_per_year': 2.0,
                        'financial_risk_per_year': 3.0}],
        'currency': 'USD', 'disjointness_basis': 'owner partition',
    })
    from api581.api import risk
    result = risk.portfolio(risk.PortfolioInput(**req.inputs), context=req.to_context())
    forged = result.model_copy(update={'direct_public_test_modules': []})
    with pytest.raises(DomainError) as error:
        digital_twin.TwinCalculationResponse.from_result(req, forged)
    assert error.value.code == 'twin_contract_mismatch'


def test_native_probe_response_carries_packaged_validation_evidence():
    req = request(
        calculation_id='dispersion/native-engine-capabilities',
        inputs={'requested_engines': ['slabx']},
    )
    response = digital_twin.execute_request(req)
    assert response.validation_evidence == [{
        'manifest': 'docs/NATIVE_ENGINE_EVIDENCE.json',
        'packaged_manifest': 'api581/data/native-engine-evidence.json',
        'verification_scripts': ['verify_native_dispersion.py'],
    }]
    assert response.validation_level == 'native_engine_fixture_verified'


def test_execute_request_uses_registry_without_transport_side_effects():
    response = digital_twin.execute_request(request())
    assert response.calculation_id == 'release/orifice-area'
    assert response.asset_id == 'asset-01'
    assert response.outputs['area_m2'] > 0


def test_execute_requests_preserves_order_and_supports_parallel_batch():
    requests = [
        request(request_id='req-b', inputs={'diameter_m': .02}),
        request(request_id='req-a', inputs={'diameter_m': .01}),
    ]
    responses = digital_twin.execute_requests(requests, max_workers=2)
    assert [item.request_id for item in responses] == ['req-b', 'req-a']
    assert [item.outputs['area_m2'] for item in responses] == pytest.approx([
        3.141592653589793e-4, 7.853981633974483e-5,
    ])


def test_execute_requests_rejects_duplicate_request_ids():
    with pytest.raises(Exception, match='unique within a batch'):
        digital_twin.execute_requests([request(), request()], max_workers=2)


def test_execute_requests_process_mode_preserves_order():
    requests = [request(request_id='req-1'), request(request_id='req-2')]
    responses = digital_twin.execute_requests(
        requests, max_workers=2, execution_mode='process', chunksize=2,
    )
    assert [item.request_id for item in responses] == ['req-1', 'req-2']


def test_execute_requests_rejects_invalid_process_chunksize():
    with pytest.raises(DomainError) as error:
        digital_twin.execute_requests([request()], chunksize=0)
    assert error.value.code == 'invalid_batch_chunksize'


def test_twin_envelopes_are_immutable_after_provenance_capture():
    req = request()
    with pytest.raises(ValidationError):
        req.asset_id = 'changed'
    with pytest.raises(ValidationError):
        req.inputs = {'diameter_m': .02}
    with pytest.raises(TypeError):
        req.inputs['diameter_m'] = .02
    with pytest.raises(TypeError):
        req.measurements.append(req.measurements[0])


def test_immutable_envelopes_remain_json_serializable():
    response = digital_twin.execute_request(request())
    dumped = response.model_dump(mode='json')
    assert dumped['outputs']['area_m2'] > 0
    assert isinstance(dumped['references'], list)


def test_duplicate_measurement_ids_are_rejected():
    with pytest.raises(ValidationError):
        request(measurements=[
            {'measurement_id': 'same', 'quantity': 'x', 'value': 1., 'unit': 'm',
             'measured_at': TS, 'source': 'a', 'quality': 'measured'},
            {'measurement_id': 'same', 'quantity': 'y', 'value': 2., 'unit': 'm',
             'measured_at': TS, 'source': 'b', 'quality': 'estimated'}])


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValidationError):
        request(observed_at=datetime(2026, 10, 25, 12, 0))


def test_hpc_batch_plan_is_ordered_and_replayable():
    requests = [
        request(request_id='req-1', inputs={'diameter_m': .01}),
        request(request_id='req-2', inputs={'diameter_m': .02}),
        request(request_id='req-3', inputs={'diameter_m': .03}),
    ]
    groups = digital_twin.partition_requests(requests, shard_size=2)
    assert [[item.request_id for item in group] for group in groups] == [['req-1', 'req-2'], ['req-3']]
    plan = digital_twin.build_batch_plan(requests, shard_size=2, batch_id='batch-1')
    assert plan.request_ids == ('req-1', 'req-2', 'req-3')
    assert [shard.shard_id for shard in plan.shards] == ['batch-1-000000', 'batch-1-000001']
    assert plan.model_dump(mode='json')['contract_version'] == 'api581-batch-1'
    plan.verify_requests(requests)
    with pytest.raises(DomainError) as error:
        plan.verify_requests([requests[0], request(request_id='req-2', inputs={'diameter_m': .03}), requests[2]])
    assert error.value.code == 'batch_plan_mismatch'


def test_hpc_batch_merge_restores_input_order():
    requests = [request(request_id='req-1'), request(request_id='req-2')]
    responses = digital_twin.execute_requests(requests)
    merged = digital_twin.merge_batch_responses(list(reversed(responses)), request_order=['req-1', 'req-2'])
    assert [item.request_id for item in merged] == ['req-1', 'req-2']


def test_execute_batch_plan_verifies_manifest_before_hpc_execution():
    requests = [
        request(request_id='req-1', inputs={'diameter_m': .01}),
        request(request_id='req-2', inputs={'diameter_m': .02}),
    ]
    plan = digital_twin.build_batch_plan(requests, shard_size=1, batch_id='batch-safe')
    responses = digital_twin.execute_batch_plan(plan, requests, max_workers=2)
    assert [item.request_id for item in responses] == ['req-1', 'req-2']
    with pytest.raises(DomainError) as error:
        digital_twin.execute_batch_plan(
            plan,
            [requests[0], request(request_id='req-2', inputs={'diameter_m': .03})],
        )
    assert error.value.code == 'batch_plan_mismatch'


def test_execute_batch_shard_is_independently_replayable():
    requests = [
        request(request_id='req-1', inputs={'diameter_m': .01}),
        request(request_id='req-2', inputs={'diameter_m': .02}),
        request(request_id='req-3', inputs={'diameter_m': .03}),
    ]
    plan = digital_twin.build_batch_plan(requests, shard_size=2, batch_id='batch-shards')
    shard = plan.shards[1]
    assert len(shard.payload_hash) == 64
    responses = digital_twin.execute_batch_shard(
        plan, shard.shard_id, requests[2:], max_workers=2,
    )
    assert [item.request_id for item in responses] == ['req-3']
    with pytest.raises(DomainError) as error:
        digital_twin.execute_batch_shard(
            plan, shard.shard_id,
            [request(request_id='req-3', inputs={'diameter_m': .04})],
        )
    assert error.value.code == 'batch_plan_mismatch'


def test_batch_plan_rejects_structurally_inconsistent_manifest():
    shard = digital_twin.TwinBatchShard(
        shard_id='batch-000000', ordinal=0, request_ids=('req-1',),
        payload_hash='0' * 64,
    )
    with pytest.raises(ValidationError, match='request_count'):
        digital_twin.TwinBatchPlan(
            batch_id='batch', request_count=2, shard_size=1,
            request_ids=('req-1',), shards=(shard,), plan_hash='0' * 64,
        )
    with pytest.raises(ValidationError, match='ordinals'):
        digital_twin.TwinBatchPlan(
            batch_id='batch', request_count=1, shard_size=1,
            request_ids=('req-1',),
            shards=(shard.model_copy(update={'ordinal': 1}),),
            plan_hash='0' * 64,
        )


def test_hpc_batch_merge_rejects_missing_response():
    requests = [request(request_id='req-1'), request(request_id='req-2')]
    responses = digital_twin.execute_requests(requests)
    with pytest.raises(DomainError) as error:
        digital_twin.merge_batch_responses(responses[:1], request_order=['req-1', 'req-2'])
    assert error.value.code == 'incomplete_batch_response'


def test_hpc_batch_merge_rejects_response_identity_mismatch():
    requests = [request(request_id='req-1')]
    response = digital_twin.execute_requests(requests)[0]
    forged = response.model_copy(update={'component_id': 'other-component'})
    with pytest.raises(DomainError) as error:
        digital_twin.merge_batch_responses(
            [forged], request_order=['req-1'], requests=requests,
        )
    assert error.value.code == 'batch_response_mismatch'


def test_hpc_batch_merge_rejects_response_input_hash_mismatch():
    requests = [request(request_id='req-1')]
    response = digital_twin.execute_requests(requests)[0]
    forged = response.model_copy(update={'input_hash': 'f' * 64})
    with pytest.raises(DomainError) as error:
        digital_twin.merge_batch_responses(
            [forged], request_order=['req-1'], requests=requests,
        )
    assert error.value.code == 'batch_response_mismatch'


def test_published_digital_twin_schema_tracks_runtime_models():
    import json
    from pathlib import Path

    schema = json.loads((Path(__file__).parents[1] / 'docs' / 'digital-twin.schema.json').read_text(encoding='utf-8'))
    assert set(schema) == {
        'TwinMeasurement', 'TwinCalculationRequest', 'TwinCalculationResponse',
        'TwinBatchShard', 'TwinBatchPlan',
    }
    assert schema['TwinBatchPlan']['properties']['contract_version']['const'] == 'api581-batch-1'
    assert schema['TwinCalculationRequest']['properties']['contract_version']['const'] == 'api581-twin-1'
