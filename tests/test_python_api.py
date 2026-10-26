import importlib
import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError
from api581 import Context, DomainError, Step, Workflow, ValidationEvidence, calculation_evidence, evaluate, run_workflow
from api581 import schema as packaged_schema
from api581 import evidence as packaged_evidence
from api581.api import frequency, effects, damage, properties, dispersion as typed_dispersion
from api581.core import REGISTRY
from api581.outputs import OUTPUT_MODELS
from api581.storage import RunStore
from api581 import dispersion


def _evaluate_optional_engine(calculation_id, inputs):
    """Run an optional-engine fixture, skipping only when the engine is absent."""
    try:
        return evaluate(calculation_id, inputs)
    except DomainError as error:
        if error.code == "optional_engine_missing":
            pytest.skip(f"optional engine unavailable for {calculation_id}")
        raise


def test_generated_json_schema_matches_runtime_registry():
    schema_path = Path(__file__).parents[1] / 'docs' / 'python-api.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    assert set(schema) == set(REGISTRY)
    assert len(schema) == len(REGISTRY) == 509
    for entry in schema.values():
        module_name, function_name = entry['python_path'].rsplit('.', 1)
        function = getattr(importlib.import_module(module_name), function_name)
        assert callable(function)


def test_packaged_schema_accessors_are_read_only_contract_snapshots():
    python_schema = packaged_schema.python_api_schema()
    twin_schema = packaged_schema.digital_twin_schema()
    assert len(python_schema) == 509
    assert set(twin_schema) == {
        'TwinMeasurement', 'TwinCalculationRequest', 'TwinCalculationResponse',
        'TwinBatchShard', 'TwinBatchPlan',
    }
    assert packaged_schema.packaged_schema_hash('python_api')
    assert packaged_schema.packaged_schema_hash('digital_twin')
    python_schema.clear()
    assert len(packaged_schema.python_api_schema()) == 509
    with pytest.raises(ValueError):
        packaged_schema.packaged_schema_hash('missing')


def test_packaged_native_evidence_accessor_is_read_only():
    manifest = packaged_evidence.native_engine_evidence()
    assert manifest['environment']['slabx'] == '1.0.8'
    assert len(manifest['runs']) == 9
    assert len(packaged_evidence.native_engine_evidence_hash()) == 64
    manifest.clear()
    assert packaged_evidence.native_engine_evidence()['runs']
    assert packaged_evidence.calculation_validation_evidence(
        'dispersion/native-pool-centreline'
    )[0]['verification_scripts'] == ['verify_native_dispersion.py']
    assert ValidationEvidence.__required_keys__ == frozenset({
        'manifest', 'packaged_manifest', 'verification_scripts'
    })


def test_every_calculation_has_a_typed_public_function_and_matching_output():
    import typing
    assert set(REGISTRY) == set(OUTPUT_MODELS)
    for identifier, calculation in REGISTRY.items():
        domain, name = identifier.split("/")
        module = importlib.import_module("api581.api." + domain)
        function = getattr(module, name.replace("-", "_"))
        hints = typing.get_type_hints(function)
        assert hints["inputs"] is calculation.model
        assert hints["return"].model_fields["outputs"].annotation is OUTPUT_MODELS[identifier]
        assert calculation.model.model_json_schema()["type"] == "object"
        assert OUTPUT_MODELS[identifier].model_json_schema()["type"] == "object"


def test_nested_request_models_are_publicly_importable():
    from api581.api.bundle import LifeRecordInput, WeibayesHistoryInput
    from api581.api.prd import DemandCaseInput, DemandRateInput
    request=WeibayesHistoryInput(shape=3,cycles=[LifeRecordInput(duration_years=10,failed=True),
        LifeRecordInput(duration_years=20,failed=False)])
    assert request.cycles[1].duration_years == 20
    assert DemandRateInput(cases=[DemandCaseInput(initiating_event_frequency_per_year=.1,
        demand_rate_reduction_factor=.2)]).cases[0].demand_rate_reduction_factor == .2


def test_typed_calls_provenance_and_opt_in_storage(tmp_path):
    context = Context(asset_id="pipe-001", observed_at="2026-10-24T14:00:00+09:00")
    a = frequency.management_factor(frequency.ManagementFactorInput(score=500), context=context)
    b = frequency.management_factor(frequency.ManagementFactorInput(score=500), context=context)
    assert a.outputs.management_factor == 1
    assert a.context.asset_id == "pipe-001"
    assert a.input_hash == b.input_hash
    assert a.run_id != b.run_id
    assert a.references and a.code_fingerprint
    store = RunStore(str(tmp_path / "runs.sqlite3"))
    for item in (a, b):
        store.save(item.model_dump(mode="json"))
    assert store.get(a.run_id) == a.model_dump(mode="json")
    assert len(store.list("pipe-001", 10)) == 2
    assert store.get("missing") is None


def test_calculation_result_carries_validation_evidence():
    ordinary = frequency.management_factor(frequency.ManagementFactorInput(score=500))
    native = typed_dispersion.native_engine_capabilities(
        typed_dispersion.NativeEngineCapabilitiesInput(requested_engines=['slabx'])
    )
    assert ordinary.validation_evidence == []
    assert 'tests/test_calculations.py' in ordinary.software_test_modules
    assert ordinary.validation_level == 'software_tested_only'
    assert native.validation_evidence[0]['manifest'] == 'docs/NATIVE_ENGINE_EVIDENCE.json'
    assert native.validation_level == 'native_engine_fixture_verified'
    assert ordinary.direct_public_test_modules == ['tests/test_python_api.py']


def test_packaged_software_test_evidence_accessor():
    from api581.evidence import calculation_public_test_modules, calculation_test_modules, software_test_evidence, software_test_evidence_hash
    manifest = software_test_evidence()
    assert manifest['calculation_count'] == 509
    assert sum(bool(value) for value in manifest['direct_public_test_calculations'].values()) == 323
    assert len(software_test_evidence_hash()) == 64
    assert 'tests/test_calculations.py' in calculation_test_modules('release/gas')
    assert calculation_public_test_modules('risk/portfolio') == ['tests/test_python_api.py']


def test_packaged_reference_fixture_evidence_accessor():
    from api581.evidence import reference_fixture_evidence, reference_fixture_evidence_hash
    manifest = reference_fixture_evidence()
    assert set(manifest['fixtures']) == {
        'frequency/management-factor', 'frequency/adjusted', 'frequency/generic',
        'reliability/weibull',
        'reliability/poisson-probability', 'release/integrate-profile',
        'release/orifice-area', 'release/type', 'effects/flash-fire', 'consequence/final-area',
        'release/hole-size-selection',
        'release/detection-isolation-rating',
        'release/level2-release-phase',
        'release/level2-orifice-rate',
        'release/kletz-rainout-fraction',
        'release/rainout-rate-split',
        'release/jet-liquid-entrainment',
        'release/level2-source-partition',
        'release/pool-evaporation-regime',
        'release/boiling-pool-radius',
        'release/boiling-pool-evaporation',
        'release/boiling-pool-steady-source',
        'release/nonboiling-pool-evaporation',
        'release/nonboiling-pool-steady-source',
        'release/flammable-phase-rates',
        'release/bleve-flashed-amount',
        'release/level2-toxic-duration',
        'release/detection-isolation',
        'release/controlled-scenario',
        'damage/measured-corrosion-rate',
        'damage/thinning-wall-loss', 'damage/thinning-strength-ratio',
        'damage/thinning-prior-selection', 'damage/thinning-adjust',
        'level1/hf-h2s-toxic-coefficients', 'level1/hf-h2s-toxic-area',
        'level1/misc-toxic-coefficients', 'level1/misc-toxic-area',
        'level1/toxic-cutoff', 'level1/toxic-mitigation',
        'properties/water-partial-pressure', 'properties/co2-partial-pressure',
        'properties/h2s-partial-pressure', 'properties/pure-fluid-saturation-pressure',
        'properties/pure-fluid-saturation-temperature',
        'properties/acid-caustic-representative-fluid',
        'consequence/toxic-mixture-limit',
        'properties/toxic-impact-table', 'properties/pool-surface-interaction',
        'properties/mixture-representative-fluid', 'properties/representative-fluid',
        'effects/atmospheric-transmissivity', 'effects/fireball-mass',
        'effects/fireball-view-factor', 'effects/vce-scaled-distance',
        'effects/physical-explosion-tnt', 'effects/bleve-liquid-tnt',
        'effects/pool-mixture-burning-rate', 'effects/pool-flame-geometry',
        'effects/pool-surface-emissive-power', 'effects/pool-cylinder-view-factor',
        'effects/blast-building-probit', 'effects/blast-building-pressure-threshold',
        'effects/toxic-species-probit', 'effects/toxic-species-threshold',
        'effects/toxic-dose-profile', 'effects/vce-scaled-overpressure',
        'effects/vce-blast-overpressure',
        'effects/fireball-radiation-flux', 'effects/pool-radiation-flux',
        'effects/vce-blast-distance',
        'effects/fireball-distance', 'effects/pool-fire-distance',
        'effects/vce-blast-consequence', 'effects/physical-explosion-consequence',
        'effects/bleve-consequence',
        'effects/fireball-consequence', 'effects/pool-fire-consequence',
        'consequence/level2-nfnt-case', 'consequence/select-toxic-criterion',
        'level2/consequence-summary',
        'level2/flammable-case',
        'consequence/level2-toxic-case', 'consequence/level2-toxic-summary',
        'consequence/level2-nfnt-summary',
        'level2/scenario-consequence',
        'level2/scenario-summary',
        'level2/assessment',
        'risk/portfolio', 'risk/assessment', 'risk/assessment-from-damage', 'risk/matrix', 'bundle/material-factor',
        'level2/correlated-jet-pool', 'bundle/replacement-cost',
                'level2/final-area', 'frequency/pof-method-selection', 'inspection/effectiveness-summary',
                'inspection/effectiveness-category', 'inspection/thinning-effectiveness', 'inspection/scc-effectiveness',
                'inspection/tube-bundle-uncertainty', 'inspection/external-effectiveness', 'inspection/buried-effectiveness',
                'inspection/prd-effectiveness', 'inspection/lining-effectiveness', 'inspection/ast-effectiveness',
                'properties/hydrogen-partial-pressure'
    }
    assert len(reference_fixture_evidence_hash()) == 64
    assert calculation_evidence('reliability/poisson-probability')['reference_fixture_evidence']


def test_bundle_and_level2_reference_paths_are_directly_regressed():
    material = evaluate('bundle/material-factor', {'material': 'Carbon Steel'})
    assert material['outputs']['material_factor'] == 1.0
    final_area = evaluate('level2/final-area', {
        'flammable_equipment_area_m2': 1.0,
        'flammable_personnel_area_m2': 2.0,
        'toxic_personnel_area_m2': 3.0,
        'nfnt_equipment_area_m2': 4.0,
        'nfnt_personnel_area_m2': 5.0,
    })
    assert final_area['outputs']['consequence_area_m2'] == 7.0
    replacement = evaluate('bundle/replacement-cost', {
        'shell_inside_diameter_m': 2.0,
        'tube_length_m': 5.0,
        'material_factor': 2.0,
        'reference_bundle_cost_usd': 22000.0,
        'price_index_multiplier': 1.5,
        'output_currency_per_usd': 1.2,
        'output_currency': 'USD',
        'output_cost_basis_year': 2020,
    })
    assert replacement['outputs']['replacement_cost'] == pytest.approx(412490.28210263856)
    combined = evaluate('level2/correlated-jet-pool', {
        'probability': 0.25,
        'jet_equipment_area_m2': 10.0,
        'jet_personnel_area_m2': 20.0,
        'pool_equipment_area_m2': 30.0,
        'pool_personnel_area_m2': 40.0,
        'consequence_source': 'test',
    })
    assert combined['outputs']['governing_personnel'] == 'pool'


def test_damage_to_risk_composition_is_directly_regressed():
    result = evaluate('risk/assessment-from-damage', {
        'component_type': 'PIPE-8', 'management_score': 500.0,
        'damage': {
            'thinning': 2.0, 'lining': None, 'external': [0.5], 'scc': [0.25],
            'htha': 0.1, 'fatigue': 0.2, 'brittle_fracture': 0.0,
            'temper_embrittlement': 0.0, 'embrittlement_885f': 0.0,
            'sigma_embrittlement': 0.0, 'thinning_external_distribution': 'local',
        },
        'damage_factor_source': 'test',
        'consequences': [
            {'hole': 'small', 'equipment_area_m2': 1.0, 'personnel_area_m2': 2.0, 'financial_consequence': 10.0},
            {'hole': 'medium', 'equipment_area_m2': 2.0, 'personnel_area_m2': 3.0, 'financial_consequence': 20.0},
            {'hole': 'large', 'equipment_area_m2': 3.0, 'personnel_area_m2': 4.0, 'financial_consequence': 30.0},
            {'hole': 'rupture', 'equipment_area_m2': 4.0, 'personnel_area_m2': 5.0, 'financial_consequence': 40.0},
        ],
        'consequence_source': 'test', 'currency': 'USD',
    })
    assert result['outputs']['damage_factor']['total_damage_factor'] == pytest.approx(2.55)
    assert result['outputs']['risk']['financial_risk_per_year'] == pytest.approx(0.0014382)


def test_thinning_and_level1_toxic_primitives_have_public_numeric_fixtures():
    wall_loss = evaluate('damage/thinning-wall-loss', {
        'starting_thickness_m': 0.01, 'corrosion_rate_m_year': 0.0005,
        'elapsed_years': 2.0,
    })
    assert wall_loss['outputs']['wall_loss_fraction'] == pytest.approx(0.1)

    strength = evaluate('damage/thinning-strength-ratio', {
        'differential_pressure_pa': 1_000_000.0, 'diameter_m': 1.0,
        'flow_stress_pa': 200_000_000.0, 'starting_thickness_m': 0.02,
        'shape': 'cylinder',
    })
    assert strength['outputs']['strength_ratio'] == pytest.approx(0.125)

    prior = evaluate('damage/thinning-prior-selection', {'confidence': 'medium'})
    assert prior['outputs']['prior_probabilities'] == pytest.approx([0.7, 0.2, 0.1])

    adjustment = evaluate('damage/thinning-adjust', {
        'base_damage_factor': 10.0, 'injection_point_factor': 2.0,
        'deadleg_factor': 1.5, 'welded_construction_factor': 1.0,
        'maintenance_factor': 0.8, 'settlement_factor': 1.0,
        'online_monitoring_factor': 0.9,
    })
    assert adjustment['outputs']['thinning_damage_factor'] == pytest.approx(26.666666666666664)

    h2s_coeff = evaluate('level1/hf-h2s-toxic-coefficients', {
        'fluid': 'h2s', 'release_type': 'continuous', 'duration_s': 300.0,
    })
    assert h2s_coeff['outputs']['c'] == pytest.approx(1.2411)
    h2s_area = evaluate('level1/hf-h2s-toxic-area', {
        'fluid': 'h2s', 'release_type': 'continuous', 'duration_s': 300.0,
        'toxic_rate_kg_s': 0.1, 'toxic_mass_kg': 30.0,
        'nonignition_probability': 1.0,
    })
    assert h2s_area['outputs']['personnel_area_m2'] == pytest.approx(132.34883408106103)

    misc_coeff = evaluate('level1/misc-toxic-coefficients', {
        'fluid': 'co', 'release_phase': 'gas', 'duration_s': 300.0,
    })
    assert misc_coeff['outputs']['e'] == pytest.approx(60.09)
    misc_area = evaluate('level1/misc-toxic-area', {
        'fluid': 'co', 'release_phase': 'gas', 'duration_s': 300.0,
        'release_type': 'continuous', 'toxic_rate_kg_s': 0.1,
        'nonignition_probability': 1.0,
    })
    assert misc_area['outputs']['personnel_area_m2'] == pytest.approx(5.233620212046088)

    cutoff = evaluate('level1/toxic-cutoff', {
        'fluid': 'h2s', 'concentration_ppm_on_idlh_basis': 100.0,
    })
    assert cutoff['outputs']['requires_toxic_evaluation'] is False
    mitigation = evaluate('level1/toxic-mitigation', {
        'rate_reduction_fraction': 0.2, 'duration_reduction_fraction': 0.3,
        'mass_reduction_fraction': 0.1, 'toxic_rate_kg_s': 10.0,
        'toxic_mass_kg': 100.0, 'duration_s': 50.0,
    })
    assert mitigation['outputs'] == {
        'toxic_rate_kg_s': 8.0, 'toxic_mass_kg': 90.0, 'duration_s': 35.0,
    }


def test_property_and_toxic_mixture_primitives_have_public_fixtures():
    water = evaluate('properties/water-partial-pressure', {
        'ambient_temperature_k': 300.0, 'relative_humidity_fraction': 0.5,
        'ambient_pressure_pa_abs': 101325.0,
    })
    assert water['outputs']['water_partial_pressure_pa'] == pytest.approx(1779.5121090521502)
    co2 = evaluate('properties/co2-partial-pressure', {
        'total_pressure_pa_abs': 1_000_000.0, 'co2_mole_fraction': 0.1,
    })
    assert co2['outputs']['co2_partial_pressure_pa_abs'] == pytest.approx(100_000.0)
    h2s = evaluate('properties/h2s-partial-pressure', {
        'total_pressure_pa_abs': 1_000_000.0, 'h2s_mole_fraction': 0.01,
    })
    assert h2s['outputs']['h2s_partial_pressure_pa_abs'] == pytest.approx(10_000.0)
    sat_p = _evaluate_optional_engine('properties/pure-fluid-saturation-pressure', {
        'fluid': 'benzene', 'qualification_basis': 'fixture',
        'pressure_pa_abs': 101325.0,
    })
    assert sat_p['outputs']['molecular_weight_kg_kmol'] == pytest.approx(78.1118)
    sat_t = _evaluate_optional_engine('properties/pure-fluid-saturation-temperature', {
        'fluid': 'benzene', 'qualification_basis': 'fixture',
        'temperature_k': 350.0,
    })
    assert sat_t['outputs']['saturation_pressure_pa_abs'] == pytest.approx(91672.37395923355)
    representative = evaluate('properties/acid-caustic-representative-fluid', {
        'is_acid_or_caustic': True, 'is_flammable': False,
        'is_toxic': True, 'personnel_contact_hazard': True,
    })
    assert representative['outputs']['selection'] == 'not_applicable'
    mixture = evaluate('consequence/toxic-mixture-limit', {
        'pure_component_limit_ppm': 100.0, 'toxic_mole_fraction': 0.5,
    })
    assert mixture['outputs']['modified_mixture_limit_ppm'] == pytest.approx(200.0)


def test_representative_property_tables_have_public_fixtures():
    impact = evaluate('properties/toxic-impact-table', {'fluid': 'ammonia'})
    assert impact['outputs']['probit_intercept'] == pytest.approx(-35.9)
    surface = evaluate('properties/pool-surface-interaction', {'surface': 'concrete'})
    assert surface['outputs']['thermal_conductivity_w_m_k'] == pytest.approx(0.92)
    mixture = evaluate('properties/mixture-representative-fluid', {
        'components': [
            {'fluid': 'C1-C2', 'mole_fraction': 0.7},
            {'fluid': 'C5', 'mole_fraction': 0.3},
        ],
    })
    assert mixture['outputs']['selected_fluid'] == 'C1-C2'
    assert mixture['outputs']['molecular_weight_kg_kmol'] == pytest.approx(37.7)
    representative = evaluate('properties/representative-fluid', {
        'fluid': 'C3-C4', 'temperature_k': 300.0,
    })
    assert representative['outputs']['ambient_state'] == 'Gas'
    assert representative['outputs']['molecular_weight_kg_kmol'] == pytest.approx(51.0)


def test_effects_energy_and_geometry_primitives_have_public_fixtures():
    transmissivity = evaluate('effects/atmospheric-transmissivity', {
        'water_partial_pressure_pa': 1000.0, 'path_length_m': 10.0,
    })
    assert transmissivity['outputs']['transmissivity'] == pytest.approx(0.8819211100380477)
    fireball_mass = evaluate('effects/fireball-mass', {
        'available_mass_kg': 1000.0, 'flammable_mass_fraction': 0.4,
    })
    assert fireball_mass['outputs']['flammable_mass_kg'] == pytest.approx(400.0)
    view_factor = evaluate('effects/fireball-view-factor', {
        'diameter_m': 10.0, 'distance_m': 20.0,
        'geometry_basis': 'api581_printed',
    })
    assert view_factor['outputs']['view_factor'] == pytest.approx(0.2)
    scaled = evaluate('effects/vce-scaled-distance', {
        'distance_m': 100.0, 'tnt_equivalent_mass_kg': 1000.0,
    })
    assert scaled['outputs']['scaled_distance_m_kg13'] == pytest.approx(10.0)
    physical = evaluate('effects/physical-explosion-tnt', {
        'burst_pressure_pa_abs': 1_000_000.0, 'ambient_pressure_pa_abs': 101325.0,
        'vapor_volume_m3': 10.0, 'heat_capacity_ratio': 1.4,
    })
    assert physical['outputs']['tnt_equivalent_mass_kg'] == pytest.approx(9.6674963125)
    bleve = evaluate('effects/bleve-liquid-tnt', {
        'burst_pressure_pa_abs': 1_000_000.0, 'ambient_pressure_pa_abs': 101325.0,
        'flashed_amount_kmol': 10.0, 'storage_temperature_k': 300.0,
    })
    assert bleve['outputs']['tnt_equivalent_mass_kg'] == pytest.approx(5.573229979121053)


def test_pool_fire_geometry_primitives_have_public_fixtures():
    mixture = evaluate('effects/pool-mixture-burning-rate', {
        'components': [
            {'mole_fraction': 0.6, 'burning_rate_kg_m2_s': 0.1},
            {'mole_fraction': 0.4, 'burning_rate_kg_m2_s': 0.2},
        ],
    })
    assert mixture['outputs']['burning_rate_kg_m2_s'] == pytest.approx(0.14)
    geometry = evaluate('effects/pool-flame-geometry', {
        'pool_radius_m': 5.0, 'burning_rate_kg_m2_s': 0.1,
        'air_density_kg_m3': 1.2, 'vapor_density_kg_m3': 2.0,
        'wind_speed_m_s': 2.0, 'gravity_m_s2': 9.81,
    })
    assert geometry['outputs']['flame_length_m'] == pytest.approx(21.63626161966045)
    emissive = evaluate('effects/pool-surface-emissive-power', {
        'pool_radius_m': 5.0, 'flame_length_m': 10.0,
        'burning_rate_kg_m2_s': 0.1, 'heat_of_combustion_j_kg': 40_000_000.0,
        'radiative_fraction': 0.35,
    })
    assert emissive['outputs']['surface_emissive_power_w_m2'] == pytest.approx(280000.0)
    view_factor = evaluate('effects/pool-cylinder-view-factor', {
        'length_radius_ratio': 2.0, 'distance_radius_ratio': 3.0,
        'flame_tilt_rad': 0.0, 'equation_basis': 'api581_printed',
    })
    assert view_factor['outputs']['maximum_view_factor'] == pytest.approx(0.15355628567075566)


def test_blast_and_toxic_effects_have_public_fixtures():
    blast = evaluate('effects/blast-building-probit', {
        'side_on_overpressure_pa': 34500.0,
    })
    assert blast['outputs']['building_collapse_probability'] == pytest.approx(0.9563898628636933)
    threshold = evaluate('effects/blast-building-pressure-threshold', {
        'building_collapse_probability': 0.5,
    })
    assert threshold['outputs']['side_on_overpressure_pa'] == pytest.approx(19206.68546346703)
    toxic = evaluate('effects/toxic-species-probit', {
        'fluid': 'ammonia', 'concentration_ppm': 100.0,
        'exposure_duration_s': 60.0,
    })
    assert toxic['outputs']['fatality_probability'] == pytest.approx(6.170539949007119e-60)
    toxic_threshold = evaluate('effects/toxic-species-threshold', {
        'fluid': 'ammonia', 'exposure_duration_s': 60.0,
        'target_fatality_probability': 0.5,
    })
    assert toxic_threshold['outputs']['concentration_ppm'] == pytest.approx(8159.039828371583)


def test_toxic_profile_and_vce_fit_primitives_have_public_fixtures():
    dose = evaluate('effects/toxic-dose-profile', {
        'fluid': 'ammonia',
        'profile': [
            {'time_s': 0.0, 'concentration_ppm': 0.0},
            {'time_s': 10.0, 'concentration_ppm': 100.0},
            {'time_s': 20.0, 'concentration_ppm': 100.0},
        ],
        'interpolation': 'linear', 'profile_source': 'fixture',
    })
    assert dose['outputs']['dose_ppm_power_n_s'] == pytest.approx(133333.33333333346)
    scaled = evaluate('effects/vce-scaled-overpressure', {
        'scaled_distance_m_kg13': 5.0,
        'fit_domain': {
            'minimum_scaled_distance_m_kg13': 2.0,
            'maximum_scaled_distance_m_kg13': 10.0,
            'engineering_basis': 'fixture blast fit',
        },
    })
    assert scaled['outputs']['side_on_overpressure_pa'] == pytest.approx(50351.036773496395)
    blast = evaluate('effects/vce-blast-overpressure', {
        'distance_m': 100.0, 'tnt_equivalent_mass_kg': 1000.0,
        'fit_domain': {
            'minimum_scaled_distance_m_kg13': 2.0,
            'maximum_scaled_distance_m_kg13': 10.0,
            'engineering_basis': 'fixture blast fit',
        },
    })
    assert blast['outputs']['side_on_overpressure_pa'] == pytest.approx(16083.410140547974)


def test_radiation_flux_and_blast_distance_have_public_fixtures():
    atmosphere = {'transmissivity_model': 'constant', 'constant_transmissivity': 0.8}
    fireball = evaluate('effects/fireball-radiation-flux', {
        'diameter_m': 10.0, 'surface_emissive_power_w_m2': 200000.0,
        'atmosphere': atmosphere, 'geometry_basis': 'api581_printed',
        'distance_m': 20.0,
    })
    assert fireball['outputs']['received_flux_w_m2'] == pytest.approx(32000.0)
    pool = evaluate('effects/pool-radiation-flux', {
        'pool_radius_m': 5.0, 'flame_length_m': 10.0, 'flame_tilt_rad': 0.0,
        'surface_emissive_power_w_m2': 280000.0, 'atmosphere': atmosphere,
        'equation_basis': 'api581_printed',
        'distance_convention': 'printed_surface_ratio', 'surface_distance_m': 20.0,
    })
    assert pool['outputs']['received_flux_w_m2'] == pytest.approx(21452.39796350253)
    distance = evaluate('effects/vce-blast-distance', {
        'tnt_equivalent_mass_kg': 1000.0,
        'threshold_overpressure_pa': 16083.410140547974,
        'fit_domain': {
            'minimum_scaled_distance_m_kg13': 2.0,
            'maximum_scaled_distance_m_kg13': 10.0,
            'engineering_basis': 'fixture blast fit',
        },
    })
    assert distance['outputs']['safe_distance_m'] == pytest.approx(100.0)


def test_fireball_and_pool_fire_distance_inversions_have_public_fixtures():
    atmosphere = {'transmissivity_model': 'constant', 'constant_transmissivity': 0.8}
    fireball = evaluate('effects/fireball-distance', {
        'diameter_m': 10.0, 'surface_emissive_power_w_m2': 200000.0,
        'atmosphere': atmosphere, 'geometry_basis': 'api581_printed',
        'threshold_w_m2': 32000.0, 'maximum_distance_m': 100.0,
    })
    assert fireball['outputs']['safe_distance_m'] == pytest.approx(20.000004768371582)
    pool = evaluate('effects/pool-fire-distance', {
        'pool_radius_m': 5.0, 'flame_length_m': 10.0, 'flame_tilt_rad': 0.0,
        'surface_emissive_power_w_m2': 280000.0, 'atmosphere': atmosphere,
        'equation_basis': 'api581_printed',
        'distance_convention': 'printed_surface_ratio',
        'threshold_w_m2': 21452.39796350253,
        'maximum_surface_distance_m': 100.0,
    })
    assert pool['outputs']['consequence_area_m2'] == pytest.approx(1963.4962109350167)


def test_explosion_consequence_integrations_have_public_fixtures():
    fit_domain = {
        'minimum_scaled_distance_m_kg13': 2.0,
        'maximum_scaled_distance_m_kg13': 10.0,
        'engineering_basis': 'fixture blast fit',
    }
    vce = evaluate('effects/vce-blast-consequence', {
        'flammable_cloud_mass_kg': 1000.0, 'combustion_heat_j_kg': 40_000_000.0,
        'explosion_yield': 0.1, 'tnt_heat_j_kg': 4_184_000.0,
        'tnt_heat_source': 'fixture', 'mass_basis': 'between_flammability_limits',
        'yield_engineering_basis': 'fixture',
        'personnel_building_collapse_probability': 0.5,
        'equipment_threshold_overpressure_pa': 34500.0,
        'fit_domain': fit_domain,
    })
    assert vce['outputs']['personnel_area_m2'] == pytest.approx(24328.955976838348)
    physical = evaluate('effects/physical-explosion-consequence', {
        'hole': 'rupture', 'fit_domain': fit_domain,
        'personnel_building_collapse_probability': 0.5,
        'equipment_threshold_overpressure_pa': 34500.0,
        'burst_pressure_pa_abs': 1_000_000.0,
        'ambient_pressure_pa_abs': 101325.0,
        'vapor_volume_m3': 10.0, 'heat_capacity_ratio': 1.4,
    })
    assert physical['outputs']['personnel_area_m2'] == pytest.approx(1137.6817490384847)
    bleve = evaluate('effects/bleve-consequence', {
        'hole': 'rupture', 'fit_domain': fit_domain,
        'personnel_building_collapse_probability': 0.5,
        'equipment_threshold_overpressure_pa': 34500.0,
        'burst_pressure_pa_abs': 1_000_000.0,
        'ambient_pressure_pa_abs': 101325.0,
        'flashed_amount_kmol': 10.0, 'storage_temperature_k': 300.0,
        'stored_vapor': None,
    })
    assert bleve['outputs']['personnel_area_m2'] == pytest.approx(788.0421080107839)


def test_pool_and_fireball_consequence_integrations_have_public_fixtures():
    atmosphere = {'transmissivity_model': 'constant', 'constant_transmissivity': 0.8}
    fireball = evaluate('effects/fireball-consequence', {
        'available_mass_kg': 1000.0, 'flammable_mass_fraction': 0.4,
        'heat_of_combustion_j_kg': 40_000_000.0,
        'burst_pressure_pa_abs': 1_000_000.0, 'atmosphere': atmosphere,
        'geometry_basis': 'api581_printed', 'maximum_distance_m': 200.0,
        'personnel_threshold_w_m2': 12600.0,
        'equipment_threshold_w_m2': 37800.0,
    })
    assert fireball['outputs']['personnel_area_m2'] == pytest.approx(77162.24697966594)
    pool = evaluate('effects/pool-fire-consequence', {
        'burning': {
            'heat_of_combustion_j_kg': 40_000_000.0,
            'latent_heat_j_kg': 300_000.0, 'boiling': False,
            'specific_heat_j_kg_k': 2000.0, 'boiling_temperature_k': 350.0,
            'ambient_temperature_k': 300.0,
        },
        'liquid_rate_kg_s': 1.0, 'available_liquid_mass_kg': 1000.0,
        'liquid_density_kg_m3': 700.0, 'pool_depth_m': 0.005,
        'site_maximum_area_m2': 1000.0, 'air_density_kg_m3': 1.2,
        'vapor_density_kg_m3': 2.0, 'wind_speed_m_s': 2.0,
        'radiative_fraction': 0.35, 'atmosphere': atmosphere,
        'equation_basis': 'geometry_checked',
        'distance_convention': 'surface_to_axis',
        'maximum_surface_distance_m': 100.0,
        'personnel_threshold_w_m2': 12600.0,
        'equipment_threshold_w_m2': 37800.0,
    })
    assert pool['outputs']['personnel_area_m2'] == pytest.approx(337.47392463580735)


def test_level2_consequence_selection_and_summary_have_public_fixtures():
    nfnt = evaluate('consequence/level2-nfnt-case', {
        'hole': 'rupture', 'non_ignition_probability': 0.2,
        'physical_equipment_area_m2': 10.0, 'physical_personnel_area_m2': 20.0,
        'bleve_equipment_area_m2': 30.0, 'bleve_personnel_area_m2': 40.0,
        'steam_chemical_personnel_area_m2': 50.0,
    })
    assert nfnt['outputs']['equipment_area_m2'] == pytest.approx(6.0)
    criterion = evaluate('consequence/select-toxic-criterion', {
        'fluid_id': 'ammonia', 'exposure_duration_s': 60.0,
        'use_printed_table': True, 'additional_candidates': [],
        'excluded_candidate_ids': {}, 'selected_criterion_id': None,
        'toxic_mole_fraction': 1.0, 'candidate_availability_basis': 'fixture',
    })
    assert criterion['outputs']['selected_criterion_id'] == 'printed:probit50'
    summary = evaluate('level2/consequence-summary', {
        'holes': [
            {'flammable_equipment_area_m2': 1.0, 'flammable_personnel_area_m2': 2.0, 'toxic_personnel_area_m2': 3.0, 'nfnt_equipment_area_m2': 4.0, 'nfnt_personnel_area_m2': 5.0, 'hole': 'small', 'generic_frequency_per_year': 0.00001},
            {'flammable_equipment_area_m2': 2.0, 'flammable_personnel_area_m2': 3.0, 'toxic_personnel_area_m2': 4.0, 'nfnt_equipment_area_m2': 5.0, 'nfnt_personnel_area_m2': 6.0, 'hole': 'medium', 'generic_frequency_per_year': 0.00002},
            {'flammable_equipment_area_m2': 3.0, 'flammable_personnel_area_m2': 4.0, 'toxic_personnel_area_m2': 5.0, 'nfnt_equipment_area_m2': 6.0, 'nfnt_personnel_area_m2': 7.0, 'hole': 'large', 'generic_frequency_per_year': 0.00003},
            {'flammable_equipment_area_m2': 4.0, 'flammable_personnel_area_m2': 5.0, 'toxic_personnel_area_m2': 6.0, 'nfnt_equipment_area_m2': 7.0, 'nfnt_personnel_area_m2': 8.0, 'hole': 'rupture', 'generic_frequency_per_year': 0.00004},
        ],
    })
    assert summary['outputs']['consequence_area_m2'] == pytest.approx(11.0)


def test_level2_flammable_event_tree_has_public_fixture():
    result = evaluate('level2/flammable-case', {
        'hole': 'medium', 'release_type': 'continuous',
        'outcomes': [
            {'event': 'pool_fire', 'probability': 0.25, 'equipment_area_m2': 10.0, 'personnel_area_m2': 20.0},
            {'event': 'jet_fire', 'probability': 0.25, 'equipment_area_m2': 20.0, 'personnel_area_m2': 30.0},
            {'event': 'fireball', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'vce', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'flash_fire', 'probability': 0.25, 'equipment_area_m2': 50.0, 'personnel_area_m2': 60.0},
        ],
        'non_ignition_probability': 0.25,
        'event_tree_source': 'fixture event tree',
        'consequence_source': 'fixture consequence',
        'fireball_applicability_basis': 'rupture_only_text',
        'correlated_jet_pool': None,
    })
    assert result['outputs']['flammable_personnel_area_m2'] == pytest.approx(27.5)


def test_level2_toxic_case_and_summary_have_public_fixtures():
    toxic_case = evaluate('consequence/level2-toxic-case', {
        'components': [
            {'component_id': 'NH3', 'selected_criterion_source': 'fixture', 'cloud_area_m2': 100.0},
            {'component_id': 'H2S', 'selected_criterion_source': 'fixture', 'cloud_area_m2': 200.0},
        ], 'non_ignition_probability': 0.25,
    })
    assert toxic_case['outputs']['personnel_area_m2'] == pytest.approx(50.0)
    cases = []
    for hole, area, frequency in [('small', 100.0, 0.00001), ('medium', 200.0, 0.00002), ('large', 300.0, 0.00003), ('rupture', 400.0, 0.00004)]:
        cases.append({'components': [{'component_id': 'NH3', 'selected_criterion_source': 'fixture', 'cloud_area_m2': area}], 'non_ignition_probability': 0.2, 'hole': hole, 'generic_frequency_per_year': frequency})
    summary = evaluate('consequence/level2-toxic-summary', {'cases': cases})
    assert summary['outputs']['personnel_area_m2'] == pytest.approx(60.0)


def test_level2_nfnt_summary_has_public_fixture():
    cases = []
    for hole, frequency in [('small', 0.00001), ('medium', 0.00002), ('large', 0.00003), ('rupture', 0.00004)]:
        cases.append({
            'hole': hole, 'non_ignition_probability': 0.2,
            'physical_equipment_area_m2': 1.0 if hole == 'rupture' else 0.0,
            'physical_personnel_area_m2': 2.0 if hole == 'rupture' else 0.0,
            'bleve_equipment_area_m2': 3.0 if hole == 'rupture' else 0.0,
            'bleve_personnel_area_m2': 4.0 if hole == 'rupture' else 0.0,
            'steam_chemical_personnel_area_m2': 5.0,
            'generic_frequency_per_year': frequency,
        })
    result = evaluate('consequence/level2-nfnt-summary', {'cases': cases})
    assert result['outputs']['equipment_area_m2'] == pytest.approx(0.24)
    assert result['outputs']['personnel_area_m2'] == pytest.approx(1.0)


def test_level2_combined_scenario_consequence_has_public_fixture():
    result = evaluate('level2/scenario-consequence', {
        'hole': 'medium', 'release_type': 'continuous',
        'outcomes': [
            {'event': 'pool_fire', 'probability': 0.25, 'equipment_area_m2': 10.0, 'personnel_area_m2': 20.0},
            {'event': 'jet_fire', 'probability': 0.25, 'equipment_area_m2': 20.0, 'personnel_area_m2': 30.0},
            {'event': 'fireball', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'vce', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'flash_fire', 'probability': 0.25, 'equipment_area_m2': 50.0, 'personnel_area_m2': 60.0},
        ],
        'non_ignition_probability': 0.25,
        'event_tree_source': 'fixture event tree', 'consequence_source': 'fixture consequence',
        'fireball_applicability_basis': 'rupture_only_text', 'correlated_jet_pool': None,
        'toxic_components': [{'component_id': 'NH3', 'selected_criterion_source': 'fixture', 'cloud_area_m2': 100.0}],
        'toxic_applicability': 'evaluated', 'toxic_applicability_source': 'fixture',
        'nfnt': {'physical_equipment_area_m2': 0.0, 'physical_personnel_area_m2': 0.0, 'bleve_equipment_area_m2': 0.0, 'bleve_personnel_area_m2': 0.0, 'steam_chemical_personnel_area_m2': 3.0, 'consequence_source': 'fixture'},
    })
    assert result['outputs']['toxic_personnel_area_m2'] == pytest.approx(25.0)
    assert result['outputs']['nfnt_personnel_area_m2'] == pytest.approx(0.75)


def test_level2_scenario_summary_has_public_fixture():
    outcomes = [
        {'event': 'pool_fire', 'probability': 0.25, 'equipment_area_m2': 10.0, 'personnel_area_m2': 20.0},
        {'event': 'jet_fire', 'probability': 0.25, 'equipment_area_m2': 20.0, 'personnel_area_m2': 30.0},
        {'event': 'fireball', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
        {'event': 'vce', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
        {'event': 'flash_fire', 'probability': 0.25, 'equipment_area_m2': 50.0, 'personnel_area_m2': 60.0},
    ]
    cases = []
    for hole, frequency in [('small', 0.00001), ('medium', 0.00002), ('large', 0.00003), ('rupture', 0.00004)]:
        cases.append({'hole': hole, 'release_type': 'continuous', 'outcomes': outcomes, 'non_ignition_probability': 0.25, 'event_tree_source': 'fixture event tree', 'consequence_source': 'fixture consequence', 'fireball_applicability_basis': 'rupture_only_text', 'correlated_jet_pool': None, 'toxic_components': [{'component_id': 'NH3', 'selected_criterion_source': 'fixture', 'cloud_area_m2': 100.0}], 'toxic_applicability': 'evaluated', 'toxic_applicability_source': 'fixture', 'nfnt': {'physical_equipment_area_m2': 0.0, 'physical_personnel_area_m2': 0.0, 'bleve_equipment_area_m2': 0.0, 'bleve_personnel_area_m2': 0.0, 'steam_chemical_personnel_area_m2': 3.0, 'consequence_source': 'fixture'}, 'generic_frequency_per_year': frequency})
    result = evaluate('level2/scenario-summary', {'cases': cases})
    assert result['outputs']['consequence_area_m2'] == pytest.approx(52.5)
    assert result['outputs']['governing_non_ignition_personnel_mechanism'] == 'toxic'


def test_level2_assessment_has_public_fixture():
    outcomes = [
        {'event': 'pool_fire', 'probability': 0.1, 'equipment_area_m2': 300.0, 'personnel_area_m2': 400.0},
        {'event': 'jet_fire', 'probability': 0.2, 'equipment_area_m2': 100.0, 'personnel_area_m2': 200.0},
        {'event': 'fireball', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
        {'event': 'vce', 'probability': 0.1, 'equipment_area_m2': 1000.0, 'personnel_area_m2': 2000.0},
        {'event': 'flash_fire', 'probability': 0.1, 'equipment_area_m2': 50.0, 'personnel_area_m2': 100.0},
    ]
    cases = []
    for hole, scale in [('small', 1), ('medium', 2), ('large', 3), ('rupture', 4)]:
        rows = outcomes if hole != 'rupture' else [
            {'event': 'pool_fire', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'jet_fire', 'probability': 0.0, 'equipment_area_m2': 0.0, 'personnel_area_m2': 0.0},
            {'event': 'fireball', 'probability': 0.3, 'equipment_area_m2': 800.0, 'personnel_area_m2': 1600.0},
            {'event': 'vce', 'probability': 0.1, 'equipment_area_m2': 4000.0, 'personnel_area_m2': 8000.0},
            {'event': 'flash_fire', 'probability': 0.1, 'equipment_area_m2': 200.0, 'personnel_area_m2': 400.0},
        ]
        if hole != 'rupture':
            rows = [{**r, 'equipment_area_m2': r['equipment_area_m2'] * scale, 'personnel_area_m2': r['personnel_area_m2'] * scale} for r in rows]
        cases.append({'hole': hole, 'release_type': 'instantaneous' if hole == 'rupture' else 'continuous', 'outcomes': rows,
                      'non_ignition_probability': 0.5, 'event_tree_source': 'fixture', 'consequence_source': 'fixture',
                      'toxic_components': [{'component_id': 'h2s', 'cloud_area_m2': 1000.0 * scale, 'selected_criterion_source': 'fixture'}, {'component_id': 'co', 'cloud_area_m2': 2000.0 * scale, 'selected_criterion_source': 'fixture'}],
                      'toxic_applicability': 'evaluated', 'toxic_applicability_source': 'fixture',
                      'nfnt': {'physical_equipment_area_m2': 1200.0 if hole == 'rupture' else 0.0, 'physical_personnel_area_m2': 2000.0 if hole == 'rupture' else 0.0,
                               'bleve_equipment_area_m2': 1600.0 if hole == 'rupture' else 0.0, 'bleve_personnel_area_m2': 2400.0 if hole == 'rupture' else 0.0,
                               'steam_chemical_personnel_area_m2': 600.0 * scale, 'consequence_source': 'fixture'}})
    result = evaluate('level2/assessment', {'component_type': 'DRUM', 'management_score': 500.0, 'total_damage_factor': 10.0,
        'damage_factor_source': 'Illustrative owner-qualified DF', 'cases': cases,
        'financial': {'repair': {'component_type': 'DRUM', 'material_id': 'carbon_steel', 'price_factor_since_2001': 2.0, 'usd_to_output_currency': 1.0, 'cost_basis_year': 2026, 'currency': 'USD'},
                      'outage': {'component_type': 'DRUM', 'outage_multiplier': 1.0, 'override_days': {'small': 1.0, 'medium': 2.0, 'large': 3.0, 'rupture': 4.0}},
                      'equipment_cost_per_m2': 1000.0, 'production_cost_per_day': 10000.0, 'population_density_per_m2': 0.001, 'cost_per_injury': 1e6, 'weighted_cleanup_volume_m3': 20.0, 'cleanup_cost_per_m3': 200.0}})
    assert result['outputs']['financial_risk_per_year'] == pytest.approx(852.4069561369835)
    assert result['outputs']['governing_non_ignition_personnel_mechanism'] == 'toxic'


def test_level1_toxic_and_controlled_release_paths_are_publicly_regressed():
    toxic = evaluate('level1/toxic-component-consequence', {
        'fluid': 'h2s', 'release_phase': 'gas', 'release_type': 'continuous',
        'theoretical_rate_kg_s': 10.0, 'released_mass_kg': 1000.0,
        'toxic_mass_fraction': 0.1, 'available_mass_kg': 12000.0,
        'detection_maximum_duration_s': 1800.0, 'nonignition_probability': 0.7,
    })
    assert toxic['outputs']['toxic_rate_kg_s'] == pytest.approx(1.0)
    mixture = evaluate('level1/toxic-mixture-consequence', {
        'components': [{'component_id': 'h2s', 'personnel_area_m2': 120.0}, {'component_id': 'hf', 'personnel_area_m2': 80.0}],
    })
    assert mixture['outputs']['critical_component_id'] == 'h2s'
    summary = evaluate('level1/toxic-hole-summary', {'cases': [
        {'hole': h, 'generic_frequency_per_year': f, 'components': [{'component_id': 'h2s', 'personnel_area_m2': a}]}
        for h, f, a in [('small', 1.0, 10.0), ('medium', 2.0, 20.0), ('large', 3.0, 30.0), ('rupture', 4.0, 40.0)]
    ]})
    assert summary['outputs']['personnel_area_m2'] == pytest.approx(30.0)
    liquid = {'diameter_m': 0.0064, 'upstream_pressure_pa_abs': 300000.0, 'downstream_pressure_pa_abs': 101325.0, 'density_kg_m3': 1000.0}
    gas = {'diameter_m': 0.0064, 'upstream_pressure_pa_abs': 500000.0, 'downstream_pressure_pa_abs': 101325.0, 'temperature_k': 300.0, 'molecular_weight_kg_kmol': 34.0, 'heat_capacity_ratio': 1.3}
    acid = evaluate('level1/release-to-acid', {'source': liquid, 'operating_temperature_k': 300.0, 'component_mass_kg': 1000.0, 'inventory_group_mass_kg': 2000.0, 'detection': 'A', 'isolation': 'A', 'duration_hole': 'small', 'differential_pressure_pa': 200000.0})
    steam = evaluate('level1/release-to-steam', {'source': {**gas, 'temperature_k': 450.0, 'molecular_weight_kg_kmol': 18.0}, 'operating_temperature_k': 450.0, 'component_mass_kg': 1000.0, 'inventory_group_mass_kg': 2000.0, 'detection': 'A', 'isolation': 'A', 'duration_hole': 'small'})
    release = evaluate('level1/release-to-toxic', {'source': gas, 'operating_temperature_k': 300.0, 'component_mass_kg': 1000.0, 'inventory_group_mass_kg': 2000.0, 'detection': 'A', 'isolation': 'A', 'duration_hole': 'small', 'fluid': 'h2s', 'release_phase': 'gas', 'toxic_mass_fraction': 0.5, 'nonignition_probability': 1.0})
    assert acid['outputs']['release_phase'] == 'liquid'
    assert steam['outputs']['release_phase'] == 'gas'
    assert release['outputs']['toxic_rate_kg_s'] > 0


def test_level1_type1_flammable_paths_are_publicly_regressed():
    area = evaluate('level1/type1-flammable-area', {
        'fluid': 'CO', 'release_phase': 'gas', 'effect': 'equipment', 'release_type': 'continuous',
        'autoignition': 'not_likely', 'adjusted_rate_kg_s': 1.0, 'released_mass_kg': 1000.0, 'mitigation_fraction': 0.0,
    })
    consequence = evaluate('level1/type1-flammable-consequence', {
        'fluid': 'CO', 'release_phase': 'gas', 'release_type': 'continuous', 'autoignition': 'not_likely',
        'adjusted_rate_kg_s': 1.0, 'released_mass_kg': 1000.0, 'mitigation_fraction': 0.0,
    })
    controlled = evaluate('level1/release-to-type1-flammable', {
        'source': {'diameter_m': 0.0254, 'upstream_pressure_pa_abs': 1e6, 'temperature_k': 300.0, 'molecular_weight_kg_kmol': 28.0, 'heat_capacity_ratio': 1.4},
        'operating_temperature_k': 300.0, 'component_mass_kg': 1000.0, 'inventory_group_mass_kg': 2000.0,
        'detection': 'A', 'isolation': 'A', 'duration_hole': 'medium', 'fluid': 'CO', 'final_release_phase': 'gas',
        'autoignition': 'not_likely', 'mitigation_fraction': 0.0,
    })
    assert area['outputs']['area_m2'] == pytest.approx(0.04)
    assert consequence['outputs']['personnel_area_m2'] == pytest.approx(5.491)
    assert controlled['outputs']['release_type'] == 'continuous'


def test_risk_area_contribution_and_flash_partition_boundaries_are_publicly_regressed():
    contribution = evaluate('risk/area-event-contribution', {
        'annual_release_frequency_per_year': 0.01, 'weather_probability_given_release': 0.25,
        'event_probability_given_release_weather': 0.2, 'equipment_area_m2': 20.0,
        'personnel_area_m2': 80.0, 'probability_source': 'Qualified conditional weather/event fixture',
    })
    assert contribution['outputs']['personnel_area_risk_contribution_m2_per_year'] == pytest.approx(0.04)
    partition = _evaluate_optional_engine('release/pure-liquid-flash-partition', {
            'fluid': 'Propane', 'storage_pressure_pa_abs': 1e6, 'storage_temperature_k': 300.0,
            'final_pressure_pa_abs': 101325.0, 'method': 'isentropic', 'qualification_basis': 'Qualified pure-fluid reference',
            'adjusted_mass_rate_kg_s': 1.0, 'released_mass_kg': 10.0,
            'equation_basis': 'post_flash_mass_balance', 'atmospheric_partition_basis': 'qualified fixture',
        })
    assert partition['outputs']['flashed_phase'] == 'twophase'


def test_bundle_lifecycle_and_financial_paths_are_publicly_regressed():
    cycles = [{'duration_years': 18.0, 'failed': True}, {'duration_years': 22.0, 'failed': True}, {'duration_years': 16.0, 'failed': False}]
    history = evaluate('bundle/weibayes-history', {'shape': 2.568, 'cycles': cycles})
    updated = evaluate('bundle/condition-update', {'shape': 2.568, 'cycles': cycles, 'predicted_failure_life_years': 44.1})
    thickness = evaluate('bundle/thickness-life', {'original_thickness_m': 0.12 * 0.0254, 'measured_thickness_m': 0.104 * 0.0254, 'service_duration_years': 11.75, 'remaining_wall_failure_fraction': 0.5, 'formula_basis': 'printed_eq_1_72'})
    estimated = evaluate('bundle/estimated-life', {'service_duration_years': 10.0, 'estimated_remaining_life_years': 5.0})
    extension = evaluate('bundle/life-extension', {'age_at_action_years': 10.0, 'life_extension_factor': 0.4, 'years_since_action': 3.0})
    consequence = evaluate('bundle/consequence', {'daily_production_margin': 100000.0, 'production_rate_reduction_fraction': 0.25, 'shutdown_days': 4.0, 'environmental_cost': 0.0, 'replacement_cost': 25000.0, 'maintenance_cost': 25000.0, 'currency': 'USD', 'cost_basis_year': 2016})
    target = evaluate('bundle/target-age', {'shape': 2.568, 'characteristic_life_years': 20.45, 'target_probability_weighted_consequence': 75000.0, 'financial_consequence': 150000.0})
    risk = evaluate('bundle/risk', {'shape': 2.568, 'characteristic_life_years': 20.45, 'age_years': target['outputs']['target_age_years'], 'financial_consequence': 150000.0, 'currency': 'USD'})
    deferral = evaluate('bundle/deferral-decision', {'shape': 1.0, 'characteristic_life_years': 10.0, 'first_turnaround_age_years': 10.0, 'second_turnaround_age_years': 20.0, 'financial_consequence': 100000.0, 'inspection_cost': 5000.0, 'replacement_cost': 80000.0, 'maintenance_cost': 5000.0, 'hurdle_rate': 0.1, 'currency': 'USD'})
    replacement = evaluate('bundle/replacement-optimization', {'shape': 1.0, 'characteristic_life_years': 10.0, 'unplanned_failure_consequence': 150000.0, 'planned_replacement_consequence': 50000.0, 'step_days': 7.0, 'maximum_replacement_age_years': 20.0, 'currency': 'USD'})
    factor = evaluate('bundle/life-extension-factor', {'method': 'plug_tubes'})
    categories = evaluate('bundle/categories', {'cumulative_failure_probability': 0.2, 'financial_consequence_usd': 50000.0, 'consequence_basis': 'printed_table_USD_basis'})
    assert history['outputs']['failure_count'] == 2 and updated['outputs']['record_count'] == 4
    assert thickness['outputs']['remaining_life_years'] > 0 and estimated['outputs']['predicted_bundle_life_years'] == 15.0
    assert extension['outputs']['effective_age_years'] == 9.0 and consequence['outputs']['financial_consequence'] == 150000.0
    assert risk['outputs']['probability_weighted_consequence'] == pytest.approx(75000.0)
    assert deferral['outputs']['inspection_economically_justified'] and replacement['outputs']['samples']
    assert factor['outputs']['life_extension_factor'] == pytest.approx(0.1)
    assert categories['outputs']['probability_category'] == 2


def test_damage_cracking_and_fatigue_screening_paths_are_publicly_regressed():
    cracking = {'susceptibility': 'medium', 'confirmed_cracking': False, 'unrepaired_cracks': False,
                'years_since_qualifying_inspection': 2.0, 'inspections': {'a': 1, 'b': 0, 'c': 0, 'd': 0}}
    outputs = {name: evaluate(name, cracking)['outputs'] for name in [
        'damage/caustic', 'damage/ssc', 'damage/acscc', 'damage/clscc', 'damage/hsc-hf']}
    hic = evaluate('damage/hic-sohic-hf', cracking | {'monitoring': 'both'})
    fatigue = evaluate('damage/fatigue-base', {'previous_failure_count': 0, 'shaking_severity': 'minor', 'shaking_duration_band': 'less_than_2_weeks', 'cyclic_loading': 'none'})
    adjustment = evaluate('damage/fatigue-adjustments', {'corrective_action': 'none', 'total_pipe_fittings': 2,
        'damaged_or_improper_supports': False, 'broken_or_directly_welded_gussets': False,
        'branch_design': 'tee_or_weldolet', 'any_branch_above_nps_2': False})
    mechanical = evaluate('damage/mechanical-fatigue', {'base': {'previous_failure_count': 0, 'shaking_severity': 'minor', 'shaking_duration_band': 'less_than_2_weeks', 'cyclic_loading': 'none'}, 'adjustments': {'corrective_action': 'none', 'total_pipe_fittings': 2, 'damaged_or_improper_supports': False, 'broken_or_directly_welded_gussets': False, 'branch_design': 'tee_or_weldolet', 'any_branch_above_nps_2': False}})
    htha = evaluate('damage/htha-factor', {'susceptibility': 'medium'})
    assert all(item['damage_factor'] > 0 for item in outputs.values())
    assert hic['outputs']['monitoring_factor'] == pytest.approx(4.0)
    assert fatigue['outputs']['base_damage_factor'] == pytest.approx(1.0)
    assert adjustment['outputs']['combined_adjustment_factor'] == pytest.approx(0.2)
    assert mechanical['outputs']['damage_factor'] == pytest.approx(0.2)
    assert htha['outputs']['damage_factor'] == pytest.approx(2000.0)


def test_event_tree_ignition_probability_primitives_are_publicly_regressed():
    ambient = evaluate('events/ambient-ignition', {'phase': 'vapor', 'flammable_rate_kg_s': 1.0, 'flash_point_temperature_k': 300.0, 'correlation_basis_source': 'fixture'})
    maximum = evaluate('events/ait-ignition-maximum', {'phase': 'vapor', 'molecular_weight_kg_kmol': 28.0})
    temperature = evaluate('events/probability-temperature', {'reference_basis': 'api581_printed_c16', 'reference_source': 'fixture', 'probability_at_reference': 0.1, 'probability_at_ait': 0.3, 'storage_temperature_k': 300.0, 'autoignition_temperature_k': 400.0})
    table = evaluate('events/conditional-table', {'phase': 'vapor', 'release_type': 'continuous'})
    two_phase = evaluate('events/two-phase-probability', {'liquid_probability': 0.4, 'vapor_probability': 0.6, 'flash_mass_fraction': 0.2, 'mixing_basis': 'api581_printed_liquid_weight', 'weighting_source': 'fixture'})
    fireball = evaluate('events/fireball-given-immediate', {'phase': 'two_phase', 'release_type': 'instantaneous', 'case_type': 'rupture', 'applicability_basis': 'rupture_only_text'})
    assert 0 < ambient['outputs']['ambient_ignition_probability'] < 1
    assert maximum['outputs']['maximum_ignition_probability'] > 0
    assert 0 < temperature['outputs']['probability'] < 1
    assert table['outputs']['immediate_at_reference'] == pytest.approx(0.5)
    assert two_phase['outputs']['probability'] == pytest.approx(0.56)
    assert fireball['outputs']['fireball_given_immediate'] == pytest.approx(1.0)


def test_prd_reliability_and_protection_paths_are_publicly_regressed():
    defaults = {'device_type': 'conventional', 'failure_mode': 'fail_to_open', 'severity': 'severe'}
    environment = {'device_type': 'conventional', 'failure_mode': 'fail_to_open', 'operating_temperature_k': 300.0,
                   'operating_to_set_pressure_ratio': 0.8, 'installed_piping_vibration': False,
                   'pulsating_or_cyclic_service': False, 'actuations_per_year': 0.0, 'history_of_chatter': False}
    weibull = evaluate('prd/default-weibull', defaults)
    env = evaluate('prd/environment-factor', environment)
    set_pressure = evaluate('prd/set-pressure-factor', {'device_type': 'conventional', 'operating_to_set_pressure_ratio': 0.45})
    overpressure = evaluate('prd/overpressure-factor', {'overpressure_to_set_pressure_ratio': 2.65})
    demand = evaluate('prd/demand-rate', {'cases': [{'initiating_event_frequency_per_year': 0.004, 'demand_rate_reduction_factor': 0.1}, {'initiating_event_frequency_per_year': 0.02, 'demand_rate_reduction_factor': 1.0}]})
    inspection = evaluate('prd/inspection-update', {'shape': 1.8, 'prior_characteristic_life_years': 17.6, 'duration_years': 6.0, 'effectiveness': 'highly', 'result': 'pass'})
    protected = evaluate('prd/protected-equipment', {'generic_frequencies_per_year': {'small': 1e-5, 'medium': 2e-5, 'large': 3e-5, 'rupture': 4e-5}, 'total_damage_factor': 1.0, 'management_factor': 1.0, 'overpressure_to_mawp_ratio': 1.0})
    base = evaluate('prd/base-reliability', {'defaults': defaults, 'environment': environment, 'age_years': 6.0, 'overpressure_to_set_pressure_ratio': 2.65})
    frequency = evaluate('prd/fail-frequency', {'failure_on_demand_probability': base['outputs']['scenario_adjusted_probability'], 'demand_rate_per_year': 0.01, 'protected_equipment_loc_probability': 0.2})
    assert weibull['outputs']['default_characteristic_life_years'] == pytest.approx(17.6)
    assert env['outputs']['environment_factor'] == pytest.approx(1.0)
    assert set_pressure['outputs']['set_pressure_factor'] == pytest.approx(0.5)
    assert overpressure['outputs']['overpressure_factor'] == pytest.approx(0.6)
    assert demand['outputs']['total_demand_rate_per_year'] == pytest.approx(0.0204)
    assert inspection['outputs']['updated_characteristic_life_years'] > 0
    assert protected['outputs']['normal_failure_frequency_per_year'] == pytest.approx(1e-4)
    assert frequency['outputs']['annual_failure_frequency'] > 0


def test_brittle_embrittlement_and_temper_paths_are_publicly_regressed():
    reference = {'material_group': 'carbon_steel', 'minimum_yield_strength_pa': 40.0 * 6894757.293168, 'exemption_curve': 'B', 'interpolation': 'exact'}
    service = {'component_thickness_m': 0.0508, 'nominal_uncorroded_thickness_m': 0.0508, 'equipment_type': 'pressure_vessel', 'p1_or_p3_steel': True, 'design_temperature_k': 616.15, 'construction_code_satisfied': True, 'stable_conditions_no_more_severe_future': True, 'cet_at_mawp_k': 244.15, 'cyclic_fatigue_or_vibration_design_service': False, 'environmental_cracking': False, 'shock_chilling': False}
    htha = evaluate('damage/htha-carbon-screen', {'material_group': 'carbon_steel', 'exposure_temperature_k': 500.0, 'hydrogen_partial_pressure_pa_abs': 500000.0, 'damage_history': 'none'})
    ref = evaluate('damage/brittle-reference-temperature', reference)
    service_result = evaluate('damage/brittle-service-factor', service)
    base = evaluate('damage/brittle-base', {'component_thickness_m': 0.0508, 'cet_minus_reference_k': 0.0, 'post_weld_heat_treated': False, 'interpolation': 'exact'})
    fracture = evaluate('damage/brittle-fracture', {'reference': reference, 'service': service, 'critical_exposure_temperature_k': ref['outputs']['reference_temperature_k'], 'post_weld_heat_treated': False, 'interpolation': 'exact'})
    emb = evaluate('damage/embrittlement-885f', {'minimum_evaluation_temperature_k': 301.15, 'interpolation': 'exact'})
    sigma_content = evaluate('damage/sigma-content', {'sigma_fraction': 0.05})
    sigma = evaluate('damage/sigma-embrittlement', {'evaluation_temperature_k': 311.15, 'sigma_category': 'medium', 'interpolation': 'exact'})
    temper_j = evaluate('damage/temper-j-factor', {'silicon_weight_percent': 0.3, 'manganese_weight_percent': 0.5, 'phosphorus_weight_percent': 0.01, 'tin_weight_percent': 0.02})
    xbar = evaluate('damage/temper-xbar', {'phosphorus_weight_percent': 0.01, 'antimony_weight_percent': 0.002, 'tin_weight_percent': 0.005, 'arsenic_weight_percent': 0.001})
    shift = evaluate('damage/temper-xbar-shift', {'xbar_factor': 20.0})
    generation = evaluate('damage/temper-generation-shift', {'fabrication_year': 1980, 'source_basis': 'printed_C'})
    temper = evaluate('damage/temper-embrittlement', {'reference': {'material_group': 'low_alloy_steel', 'minimum_yield_strength_pa': 40.0 * 6894757.293168, 'exemption_curve': 'A', 'interpolation': 'exact'}, 'minimum_pressurization_temperature_k': 365.15, 'delta_fatt_k': 20.0, 'component_thickness_m': 0.0508, 'post_weld_heat_treated': True, 'interpolation': 'linear'})
    assert htha['outputs']['damage_factor'] > 0 and ref['outputs']['reference_temperature_k'] > 0
    assert service_result['outputs']['service_experience_factor'] > 0 and base['outputs']['base_damage_factor'] > 0
    assert fracture['outputs']['damage_factor'] > 0 and emb['outputs']['damage_factor'] > 0
    assert sigma_content['outputs']['sigma_category'] == 'medium' and sigma['outputs']['damage_factor'] > 0
    assert temper_j['outputs']['j_factor'] == pytest.approx(240.0)
    assert xbar['outputs']['xbar_factor'] == pytest.approx(13.1)
    assert shift['outputs']['delta_fatt_k'] == pytest.approx(82.525)
    assert generation['outputs']['generation'] == 2 and temper['outputs']['damage_factor'] >= 0


def test_soil_and_cladding_thinning_primitives_are_publicly_regressed():
    profile = evaluate('damage/soil-base-rate-table', {'condition_profile': 'dry_inland_sand', 'unit_basis': 'printed_si'})
    resistivity = evaluate('damage/soil-resistivity-factor', {'soil_resistivity_ohm_m': 50.0})
    temperature = evaluate('damage/soil-temperature-factor', {'equipment_temperature_k': 343.15, 'threshold_basis': 'printed_si'})
    cathodic = evaluate('damage/soil-cp-factor', {'protection_category': 'annual_polarized_or_instant_off_entire_structure'})
    coating = evaluate('damage/soil-coating-factor', {'coating_type': 'mill_pe_tape_mastic', 'coating_age_years': 30.0, 'rated_temperature_occasionally_exceeded': True, 'maintenance_rare_or_none': True})
    equation = evaluate('damage/soil-rate-equation', {'base_corrosion_rate_m_year': 0.00013, 'resistivity_factor': 0.83, 'temperature_factor': 2.0, 'cathodic_protection_factor': 0.05, 'coating_effectiveness_factor': 8.1})
    soil = evaluate('damage/soil-corrosion-rate', {'material': 'carbon_steel', 'in_contact_with_soil': True, 'applicability_basis': 'Qualified buried non-AST carbon-steel soil exposure fixture', 'base_corrosion_rate_m_year': 0.00013, 'base_rate_source': 'Table2.B.12.2 printed SI profile fixture', 'resistivity_application': 'apply', 'resistivity': {'soil_resistivity_ohm_m': 50.0}, 'temperature': {'equipment_temperature_k': 343.15, 'threshold_basis': 'printed_si'}, 'cathodic_protection': {'protection_category': 'annual_polarized_or_instant_off_entire_structure'}, 'coating': {'coating_type': 'mill_pe_tape_mastic', 'coating_age_years': 30.0, 'rated_temperature_occasionally_exceeded': True, 'maintenance_rare_or_none': True}})
    wall = {'starting_total_thickness_m': 0.012, 'original_base_material_thickness_m': 0.01, 'cladding_corrosion_rate_m_year': 0.0002, 'base_corrosion_rate_m_year': 0.0005, 'elapsed_years': 15.0}
    life = evaluate('damage/cladding-remaining-life', {k: wall[k] for k in ['starting_total_thickness_m', 'original_base_material_thickness_m', 'cladding_corrosion_rate_m_year']})
    loss = evaluate('damage/thinning-clad-wall-loss', wall)
    strength = evaluate('damage/thinning-design-strength-ratio', {'allowable_stress_pa': 120e6, 'weld_efficiency': 0.85, 'flow_stress_pa': 300e6, 'starting_thickness_m': 0.012, 'minimum_required_thickness_m': 0.004, 'minimum_structural_thickness_m': 0.006, 'design_thickness_basis': 'Qualified code/load-combination minimum fixture'})
    assert profile['outputs']['corrosion_rate_m_year'] > 0 and resistivity['outputs']['resistivity_factor'] == pytest.approx(0.83)
    assert temperature['outputs']['temperature_factor'] == pytest.approx(2.0) and cathodic['outputs']['cathodic_protection_factor'] == pytest.approx(0.05)
    assert coating['outputs']['coating_effectiveness_factor'] == pytest.approx(8.1) and equation['outputs']['corrosion_rate_m_year'] > 0
    assert soil['outputs']['corrosion_rate_m_year'] == pytest.approx(0.000087399)
    assert life['outputs']['cladding_depletion_age_years'] == pytest.approx(10.0)
    assert loss['outputs']['wall_loss_fraction'] == pytest.approx(0.375)
    assert strength['outputs']['strength_ratio'] == pytest.approx(0.17)


def test_cooling_water_rate_and_factor_paths_are_publicly_regressed():
    factors = evaluate('damage/cooling-water-rate-factors', {'process_temperature_k': 333.15})
    coeff = evaluate('damage/cooling-water-ph-coefficients', {'total_dissolved_solids_mg_l': 400.0, 'water_temperature_k': 297.15, 'temperature_basis': 'printed_si', 'calcium_hardness_mg_caco3_l': 99.0, 'methyl_orange_alkalinity_mg_caco3_l': 99.5, 'lookup_policy': 'exact_rows_only', 'c4_source_policy': 'reject_ambiguous_cells'})
    indices = evaluate('damage/cooling-water-stability-indices', {'actual_ph': 8.0, 'saturation_ph': 7.8})
    saturation = evaluate('damage/cooling-water-saturation-ph', {'c1': 0.1, 'c2': 2.0, 'c3': 1.6, 'c4': 2.0})
    base = evaluate('damage/cooling-water-base-rate', {'chloride_ppm': 100.0, 'ryznar_stability_index': 6.0, 'velocity_m_s': 1.0, 'condition_interpretation': 'body_rsi6_velocity2_44', 'rate_unit_basis': 'printed_si', 'lookup_policy': 'exact_rows_only'})
    temperature = evaluate('damage/cooling-water-temperature-factor', {'metal_temperature_k': 333.15, 'system': 'open', 'temperature_basis': 'printed_si', 'argument_policy': 'table_operating_temperature', 'duplicate_row_policy': 'reject_unresolved_row', 'lookup_policy': 'exact_rows_only'})
    velocity = evaluate('damage/cooling-water-velocity-factor', {'velocity_m_s': 1.0, 'equation_basis': 'printed_si'})
    equation = evaluate('damage/cooling-water-rate-equation', {'base_corrosion_rate_m_year': 0.00005, 'temperature_factor': 2.2, 'velocity_factor': 1.0})
    seawater = evaluate('damage/cooling-water-seawater-rate', {'material': 'carbon_steel', 'velocity_m_s': 1.0, 'equation_basis': 'printed_si', 'applicability_basis': 'Qualified seawater fixture'})
    coupon = evaluate('damage/cooling-water-coupon-pitting-rate', {'coupon_general_corrosion_rate_m_year': 0.00002, 'pitting_multiplier': 7.0, 'representativeness_basis': 'Qualified coupon fixture'})
    assert factors['outputs']['factor_flags'] == [] and coeff['outputs']['c1'] == pytest.approx(0.1)
    assert indices['outputs']['ryznar_stability_index'] == pytest.approx(7.6) and saturation['outputs']['saturation_ph'] == pytest.approx(7.8)
    assert base['outputs']['base_corrosion_rate_m_year'] == pytest.approx(0.00005)
    assert temperature['outputs']['temperature_factor'] == pytest.approx(2.2) and velocity['outputs']['velocity_factor'] == pytest.approx(1.0)
    assert equation['outputs']['corrosion_rate_m_year'] == pytest.approx(0.00011)
    assert seawater['outputs']['corrosion_rate_m_year'] > 0 and coupon['outputs']['pitting_corrosion_rate_m_year'] == pytest.approx(0.00014)


def test_thinning_condition_and_lining_factor_paths_are_publicly_regressed():
    row = evaluate('damage/thinning-monitoring-row', {'mechanism': 'sour_water', 'velocity_m_s': 6.096})
    table = evaluate('damage/thinning-monitoring-table-factor', {'monitoring_row': 'hydrochloric_acid', 'monitoring_method': 'key_process_variables'})
    online = evaluate('damage/thinning-online-monitoring-factor', {'row': {'mechanism': 'hydrochloric_acid'}, 'methods': ['key_process_variables', 'electrical_resistance_probes'], 'organized_monitoring_plan': True, 'qualification_basis': 'fixture', 'key_variables_probe_conjunction_confirmed': True})
    injection = evaluate('damage/thinning-injection-point-factor', {'component_scope': 'piping', 'injection_or_mix_point_present': True, 'highly_effective_targeted_inspection': False})
    deadleg = evaluate('damage/thinning-deadleg-factor', {'component_scope': 'piping', 'deadleg_present': True, 'highly_effective_targeted_inspection': False})
    lining = evaluate('damage/lining-base-factor', {'lining_type': 'glass_lined', 'age_years': 2.0, 'lookup_policy': 'exact_rows_only', 'first_year_policy': 'reject_below_first_year'})
    condition = evaluate('damage/lining-condition-factor', {'condition': 'average'})
    monitoring = evaluate('damage/lining-monitoring-factor', {'monitoring_used': True, 'known_effective_for_lining_deterioration': True, 'effectiveness_basis': 'fixture'})
    governing = evaluate('damage/lining-governing-thinning', {'base_material_thinning_damage_factor': 50.0, 'lining_damage_factor': 1.8})
    assert row['outputs']['monitoring_row'] == 'sour_water_low_velocity' and table['outputs']['table_monitoring_factor'] == 10.0
    assert online['outputs']['online_monitoring_factor'] == 20.0 and injection['outputs']['injection_point_factor'] == 3.0
    assert deadleg['outputs']['deadleg_factor'] == 3.0 and lining['outputs']['base_damage_factor'] == 4.0
    assert condition['outputs']['condition_factor'] == 2.0 and monitoring['outputs']['monitoring_factor'] == pytest.approx(0.1)
    assert governing['outputs']['governing_source'] == 'lining'


def test_co2_corrosion_primitives_are_publicly_regressed():
    humidity = evaluate('damage/co2-relative-humidity', {'water_mass_fraction': 0.1, 'total_pressure_pa_abs': 1e6, 'water_saturation_pressure_pa_abs': 1e4})
    dew = evaluate('damage/co2-dew-point', {'water_mass_fraction': 0.1, 'total_pressure_pa_abs': 100.0 * 6894.757293168})
    ph_factor = evaluate('damage/co2-temperature-ph-factor', {'temperature_k': 298.15, 'ph': 5.25, 'lookup_policy': 'bilinear', 'jump_policy': 'reject_cross_80_90'})
    ph = evaluate('damage/co2-ph-estimate', {'temperature_k': 333.15, 'co2_partial_pressure_pa_abs': 1e5, 'water_case': 'condensate', 'approximation_basis': 'same fixture'})
    fugacity = evaluate('damage/co2-fugacity', {'temperature_k': 333.15, 'co2_partial_pressure_pa_abs': 1e6, 'temperature_denominator_basis': 'kelvin_exact'})
    reynolds = evaluate('damage/co2-reynolds', {'diameter_m': 0.1, 'mixture_density_kg_m3': 800.0, 'mixture_velocity_m_s': 2.0, 'mixture_viscosity_pa_s': 0.001})
    friction = evaluate('damage/co2-friction-factor', {'reynolds_number': reynolds['outputs']['reynolds_number'], 'relative_roughness': 0.0001})
    shear = evaluate('damage/co2-shear-stress', {'friction_factor': friction['outputs']['friction_factor'], 'mixture_density_kg_m3': 800.0, 'mixture_velocity_m_s': 2.0})
    base = evaluate('damage/co2-base-rate', {'temperature_ph_factor': 7.18, 'fugacity_pa': 2e5, 'shear_stress_pa': shear['outputs']['shear_stress_pa']})
    glycol = evaluate('damage/co2-glycol-factor', {'composition_percent': 20.0, 'composition_basis': 'equation_g_percent'})
    adjusted = evaluate('damage/co2-rate-adjustment', {'base_corrosion_rate_m_year': 0.01, 'inhibitor_factor': 0.2, 'inhibitor_effectiveness_basis': 'fixture'})
    assert humidity['outputs']['relative_humidity_fraction'] > 0 and dew['outputs']['dew_point_temperature_k'] > 0
    assert ph_factor['outputs']['temperature_ph_factor'] > 0 and ph['outputs']['estimated_ph'] > 0
    assert fugacity['outputs']['fugacity_pa'] > 0 and reynolds['outputs']['reynolds_number'] == pytest.approx(160000.0)
    assert friction['outputs']['friction_factor'] > 0 and shear['outputs']['shear_stress_pa'] > 0
    assert base['outputs']['base_corrosion_rate_m_year'] > 0 and glycol['outputs']['glycol_factor'] > 0
    assert adjusted['outputs']['corrosion_rate_m_year'] == pytest.approx(0.002)


def test_co2_screening_and_mass_flow_paths_are_publicly_regressed():
    material = evaluate('damage/co2-material-screen', {'material_category': 'carbon_steel', 'interpretation': 'table_resistant_alloys', 'qualification_basis': 'Qualified material category'})
    wetting = evaluate('damage/co2-hydrocarbon-wetting-screen', {'liquid_hydrocarbons_present': True, 'water_cut_policy': 'explicit_qualified_percent', 'water_content_percent': 19.0, 'water_content_basis': 'Qualified liquid-system water-cut percent fixture', 'mixture_velocity_m_s': 1.1, 'qualification_basis': 'Qualified figure13.1 applicability fixture'})
    moisture = evaluate('damage/co2-moisture-screen', {'temperature_k': 333.15, 'evidence': 'source_missing_moisture_assume_wet', 'qualification_basis': 'Explicit source wet assumption for missing gas moisture'})
    mass_flow = evaluate('damage/co2-reynolds-mass-flow', {'diameter_m': 0.1, 'cross_sectional_area_m2': 0.01, 'mass_flow_kg_s': 16.0, 'mixture_viscosity_pa_s': 0.001})
    screened = evaluate('damage/co2-screened-assessment', {'temperature_k': 333.15, 'pressure': {'total_pressure_pa_abs': 1e6, 'co2_mole_fraction': 0.1}, 'material': {'material_category': 'carbon_steel', 'interpretation': 'table_resistant_alloys', 'qualification_basis': 'Qualified carbon-steel identity'}, 'hydrocarbon_wetting': {'liquid_hydrocarbons_present': False, 'qualification_basis': 'Qualified gas-service/no liquid hydrocarbon fixture'}, 'moisture': {'temperature_k': 333.15, 'evidence': 'source_missing_moisture_assume_wet', 'qualification_basis': 'Explicit source wet assumption for missing gas moisture'}, 'wet_model': {'ph': {'method': 'supplied', 'ph': 5.0, 'qualification_basis': 'Qualified pH fixture'}, 'flow': {'method': 'supplied', 'shear_stress_pa': 19.0, 'qualification_basis': 'Qualified wall shear fixture'}, 'lookup_policy': 'exact_nodes_only', 'jump_policy': 'reject_cross_80_90', 'temperature_denominator_basis': 'printed_celsius_plus_273', 'simple_upstream_mixture_and_wetting_basis': 'Qualified upstream water-wetted metal fixture'}, 'qualification_basis': 'Qualified common source and screened CO2 applicability fixture'})
    assert material['outputs']['material_screen_decision'] == 'evaluate_co2'
    assert wetting['outputs']['wetting_screen_decision'] == 'figure_low_water_high_velocity_exemption'
    assert moisture['outputs']['free_water_screen_state'] == 'present' and moisture['outputs']['free_water_assumed_from_missing_data']
    assert mass_flow['outputs']['reynolds_number'] == pytest.approx(160000.0)
    assert screened['outputs']['screened_calculation_branch'] == 'wet_carbonic_acid_model'


def test_remaining_utility_and_adapter_paths_are_directly_regressed():
    poisson = evaluate('reliability/poisson-probability', {
        'annual_failure_frequency': 2.0,
        'duration_years': 0.5,
    })
    assert poisson['outputs']['period_failure_probability'] == pytest.approx(0.6321205588285577)

    integrated = evaluate('release/integrate-profile', {
        'points': [
            {'time_s': 0.0, 'rate_kg_s': 2.0},
            {'time_s': 10.0, 'rate_kg_s': 4.0},
        ],
        'available_mass_kg': 100.0,
    })
    assert integrated['outputs'] == {'released_mass_kg': 30.0, 'duration_s': 10.0}

    portfolio = evaluate('risk/portfolio', {
        'components': [
            {'component_id': 'A', 'annual_failure_frequency': 0.1,
             'equipment_area_risk_m2_per_year': 2.0,
             'personnel_area_risk_m2_per_year': 3.0,
             'financial_risk_per_year': 4.0},
            {'component_id': 'B', 'annual_failure_frequency': 0.2,
             'equipment_area_risk_m2_per_year': 1.0,
             'personnel_area_risk_m2_per_year': 5.0,
             'financial_risk_per_year': 6.0},
        ],
        'currency': 'USD',
        'disjointness_basis': 'components mutually exclusive',
    })
    assert portfolio['outputs']['component_count'] == 2
    assert portfolio['outputs']['financial_risk_per_year'] == pytest.approx(10.0)

    capabilities = evaluate('dispersion/native-engine-capabilities', {
        'requested_engines': ['slabx', 'slabx-lh2'],
    })
    status = capabilities['outputs']['engine_status']
    assert set(status) == {'slabx', 'slabx-lh2'}
    # Native engines are optional dependencies.  A dependency-free package
    # must report them as missing; a qualified native profile must report both
    # as available.  This keeps the same public contract valid in both CI
    # profiles without masking version/importability failures.
    expected = {
        'slabx': 'available' if importlib.util.find_spec('slabx') else 'missing',
        'slabx-lh2': 'available' if importlib.util.find_spec('slabx_lh2') else 'missing',
    }
    assert status == expected


def test_core_public_risk_inputs_are_directly_regressed():
    management = evaluate('frequency/management-factor', {'score': 500})
    assert management['outputs']['management_factor'] == pytest.approx(1.0)

    corrosion = evaluate('damage/measured-corrosion-rate', {
        'initial_thickness_m': 0.020,
        'current_thickness_m': 0.018,
        'elapsed_years': 4.0,
        'measurement_basis': 'UT survey',
    })
    assert corrosion['outputs']['corrosion_rate_m_year'] == pytest.approx(0.0005)

    gas = evaluate('release/gas', {
        'diameter_m': 0.01,
        'upstream_pressure_pa_abs': 202650.0,
        'downstream_pressure_pa_abs': 101325.0,
        'temperature_k': 300.0,
        'molecular_weight_kg_kmol': 28.0134,
        'heat_capacity_ratio': 1.4,
    })
    assert gas['outputs']['mass_rate_kg_s'] > 0

    hole = evaluate('release/hole-size-selection', {
        'hole_diameter_m': 0.025,
        'component_diameter_m': 0.8,
        'diameter_basis': 'printed_si',
    })
    assert hole['outputs']['selected_hole'] == 'medium'
    assert hole['outputs']['representative_diameter_m'] == pytest.approx(0.025)

    rating = evaluate('release/detection-isolation-rating', {
        'detection_type': 'process_instrumentation',
        'isolation_type': 'manual_valve',
        'qualification_basis': 'Qualified plant instrumentation and isolation procedure',
    })
    assert rating['outputs']['detection_rating'] == 'A'
    assert rating['outputs']['isolation_rating'] == 'C'

    phase = evaluate('release/level2-release-phase', {
        'storage_pressure_pa_abs': 1_000_000.0,
        'saturation_pressure_at_storage_pa_abs': 2_000_000.0,
        'ambient_pressure_pa_abs': 100_000.0,
    })
    assert phase['outputs']['release_phase'] == 'vapor'
    assert phase['outputs']['status'] == 'classified'

    source = evaluate('release/level2-orifice-rate', {
        'diameter_m': 0.0254,
        'storage_pressure_pa_abs': 1_000_000.0,
        'saturation_pressure_at_storage_pa_abs': 50_000.0,
        'ambient_pressure_pa_abs': 100_000.0,
        'liquid_density_kg_m3': 700.0,
    })
    assert source['outputs']['release_phase'] == 'liquid'
    assert source['outputs']['mass_rate_kg_s'] == pytest.approx(10.971662055304723)

    rainout = evaluate('release/kletz-rainout-fraction', {'flash_mass_fraction': 0.25})
    assert rainout['outputs']['rainout_mass_fraction'] == pytest.approx(0.5)

    split = evaluate('release/rainout-rate-split', {
        'adjusted_mass_rate_kg_s': 100.0,
        'rainout_mass_fraction': 0.2,
    })
    assert split['outputs']['pool_liquid_rate_kg_s'] == pytest.approx(20.0)
    assert split['outputs']['jet_total_rate_kg_s'] == pytest.approx(80.0)

    entrainment = evaluate('release/jet-liquid-entrainment', {
        'rainout_mass_fraction': 0.5,
        'equation_basis': 'post_flash_mass_balance',
        'post_flash_vapor_mass_fraction': 0.25,
    })
    assert entrainment['outputs']['entrained_liquid_mass_fraction'] == pytest.approx(0.5)
    assert entrainment['outputs']['jet_vapor_mass_fraction'] == pytest.approx(0.5)

    partition = evaluate('release/level2-source-partition', {
        'rainout_mass_fraction': 0.5,
        'equation_basis': 'post_flash_mass_balance',
        'post_flash_vapor_mass_fraction': 0.25,
        'adjusted_mass_rate_kg_s': 10.0,
        'released_mass_kg': 100.0,
        'rainout_basis_source': 'Kletz demonstration',
        'flash_property_source': 'Qualified demonstration post-flash vapor fraction',
    })
    assert partition['outputs']['jet_liquid_mass_kg'] == pytest.approx(25.0)
    assert partition['outputs']['jet_vapor_mass_kg'] == pytest.approx(25.0)

    regime = evaluate('release/pool-evaporation-regime', {
        'bubble_temperature_k': 350.0,
        'ground_temperature_k': 300.0,
    })
    assert regime['outputs']['regime'] == 'non_boiling'

    radius = evaluate('release/boiling-pool-radius', {
        'vapor_volumetric_rate_m3_s': 0.5,
        'time_to_steady_s': 2.0,
    })
    assert radius['outputs']['pool_radius_m'] == pytest.approx(2.581497142901288)

    evaporation = evaluate('release/boiling-pool-evaporation', {
        'bubble_temperature_k': 250.0,
        'ground_temperature_k': 300.0,
        'latent_heat_j_kg': 300000.0,
        'surface': {
            'thermal_conductivity_w_m_k': 0.92,
            'thermal_diffusivity_m2_s': 4.16e-7,
            'roughness_factor': 1.0,
        },
        'gravity_m_s2': 9.81,
        'vapor_volumetric_rate_m3_s': 0.5,
        'time_to_steady_s': 2.0,
    })
    assert evaporation['outputs']['evaporation_rate_kg_s'] == pytest.approx(4.678474683102527)

    steady = evaluate('release/boiling-pool-steady-source', {
        'bubble_temperature_k': 250.0,
        'ground_temperature_k': 300.0,
        'latent_heat_j_kg': 300000.0,
        'surface': {
            'thermal_conductivity_w_m_k': 0.92,
            'thermal_diffusivity_m2_s': 4.16e-7,
            'roughness_factor': 1.0,
        },
        'gravity_m_s2': 9.81,
        'liquid_feed_rate_kg_s': 1.0,
        'pool_vapor_density_kg_m3': 2.0,
        'supply_duration_s': 100.0,
        'maximum_pool_area_m2': 1000.0,
    })
    assert steady['outputs']['support_status'] == 'supported'
    assert steady['outputs']['vapor_source_rate_kg_s'] == pytest.approx(1.0)

    nonboiling = evaluate('release/nonboiling-pool-evaporation', {
        'bubble_temperature_k': 350.0,
        'ground_temperature_k': 300.0,
        'storage_temperature_k': 310.0,
        'bubble_pressure_at_ground_pa_abs': 10000.0,
        'ambient_pressure_pa_abs': 101325.0,
        'molecular_weight_kg_kmol': 100.0,
        'wind_speed_m_s': 2.0,
        'pool_radius_m': 5.0,
    })
    assert nonboiling['outputs']['evaporation_rate_kg_s'] == pytest.approx(0.06537242357723806)

    nonboiling_source = evaluate('release/nonboiling-pool-steady-source', {
        'bubble_temperature_k': 350.0,
        'ground_temperature_k': 300.0,
        'bubble_pressure_at_ground_pa_abs': 10000.0,
        'ambient_pressure_pa_abs': 101325.0,
        'molecular_weight_kg_kmol': 100.0,
        'storage_temperature_k': 310.0,
        'wind_speed_m_s': 2.0,
        'liquid_feed_rate_kg_s': 0.05,
        'maximum_pool_area_m2': 1000.0,
    })
    assert nonboiling_source['outputs']['support_status'] == 'supported'
    assert nonboiling_source['outputs']['pool_radius_m'] == pytest.approx(4.338800650133383)

    rates = evaluate('release/flammable-phase-rates', {
        'adjusted_mass_rate_kg_s': 10.0,
        'flammable_mass_fraction': 0.8,
        'flash_mass_fraction': 0.25,
    })
    assert rates['outputs']['flammable_rate_kg_s'] == pytest.approx(8.0)
    assert rates['outputs']['flammable_vapor_rate_kg_s'] == pytest.approx(2.0)

    flashed = evaluate('release/bleve-flashed-amount', {
        'stored_liquid_mass_kg': 1000.0,
        'liquid_flash_mass_fraction': 0.2,
        'molecular_weight_kg_kmol': 20.0,
    })
    assert flashed['outputs']['flashed_amount_kmol'] == pytest.approx(10.0)

    toxic_duration = evaluate('release/level2-toxic-duration', {
        'available_mass_kg': 100.0,
        'mixture_release_rate_kg_s': 2.0,
        'detection_maximum_duration_s': 1000.0,
    })
    assert toxic_duration['outputs']['release_duration_s'] == pytest.approx(50.0)

    release_duration = evaluate('release/detection-isolation', {
        'detection_rating': 'A',
        'isolation_rating': 'A',
        'hole_size': 'small',
        'theoretical_rate_kg_s': 10.0,
        'available_mass_kg': 10000.0,
    })
    assert release_duration['outputs']['released_mass_kg'] == pytest.approx(9000.0)

    controlled = evaluate('release/controlled-scenario', {
        'source': {
            'diameter_m': 0.0254,
            'upstream_pressure_pa_abs': 1_000_000.0,
            'downstream_pressure_pa_abs': 101_325.0,
            'temperature_k': 300.0,
            'molecular_weight_kg_kmol': 28.0,
            'heat_capacity_ratio': 1.4,
        },
        'operating_temperature_k': 300.0,
        'component_mass_kg': 1000.0,
        'inventory_group_mass_kg': 2000.0,
        'detection': 'A',
        'isolation': 'A',
        'duration_hole': 'medium',
    })
    assert controlled['outputs']['release_type'] == 'continuous'
    assert controlled['outputs']['released_mass_kg'] == pytest.approx(470.7972455547523)

    area = evaluate('consequence/final-area', {
        'flammable_equipment_area_m2': 1.0,
        'flammable_personnel_area_m2': 2.0,
        'toxic_personnel_areas_m2': [3.0, 4.0],
        'nfnt_personnel_area_m2': 5.0,
    })
    assert area['outputs']['consequence_area_m2'] == pytest.approx(5.0)

    risk = evaluate('risk/assessment', {
        'component_type': 'PIPE-8', 'management_score': 500.0,
        'total_damage_factor': 10.0, 'damage_factor_source': 'direct-test',
        'consequences': [
            {'hole': 'small', 'equipment_area_m2': 100.0, 'personnel_area_m2': 200.0, 'financial_consequence': 1e6},
            {'hole': 'medium', 'equipment_area_m2': 100.0, 'personnel_area_m2': 200.0, 'financial_consequence': 1e6},
            {'hole': 'large', 'equipment_area_m2': 100.0, 'personnel_area_m2': 200.0, 'financial_consequence': 1e6},
            {'hole': 'rupture', 'equipment_area_m2': 100.0, 'personnel_area_m2': 200.0, 'financial_consequence': 1e6},
        ],
        'consequence_source': 'direct-test', 'currency': 'KRW',
    })
    assert risk['outputs']['risk']['annual_failure_frequency'] == pytest.approx(3.06e-4)


def test_public_fire_event_and_risk_classification_paths_are_directly_regressed():
    power = evaluate('effects/jet-fire-power', {
        'mass_rate_kg_s': 10.0,
        'heat_of_combustion_j_kg': 46e6,
    })
    assert power['outputs']['radiated_power_w'] == pytest.approx(161e6)

    distance = evaluate('effects/jet-fire-distance', {
        'radiated_power_w': power['outputs']['radiated_power_w'],
        'threshold_w_m2': 12600.0,
        'transmissivity_model': 'constant',
        'atmospheric_transmissivity': 0.8,
    })
    assert distance['outputs']['consequence_area_m2'] == pytest.approx(2555.555555555556)

    tree = evaluate('events/leakage-tree', {
        'phase': 'vapor', 'release_type': 'continuous',
        'ignition_probability': 0.4,
        'immediate_given_ignition': 0.25,
        'vce_given_delayed': 0.2,
    })
    assert tree['outputs']['probability_sum'] == pytest.approx(1.0)
    assert tree['outputs']['terminal_probabilities']['jet_fire'] == pytest.approx(0.1)

    matrix = evaluate('risk/matrix', {
        'frequency_per_year': 0.001, 'consequence': 10.0,
        'frequency_boundaries': [0.0001, 0.001, 0.01],
        'consequence_boundaries': [1.0, 10.0, 100.0],
        'risk_cells': [['L'] * 4, ['M'] * 4, ['H'] * 4, ['VH'] * 4],
        'policy_id': 'direct-test',
    })
    assert matrix['outputs']['risk_label'] == 'H'

    aggregate = evaluate('risk/aggregate', {
        'scenarios': [
            {'scenario_id': 'a', 'annual_failure_frequency': 0.1,
             'equipment_area_m2': 2.0, 'personnel_area_m2': 3.0,
             'financial_consequence': 4.0},
            {'scenario_id': 'b', 'annual_failure_frequency': 0.2,
             'equipment_area_m2': 1.0, 'personnel_area_m2': 5.0,
             'financial_consequence': 6.0},
        ],
        'currency': 'USD',
    })
    assert aggregate['outputs']['financial_risk_per_year'] == pytest.approx(1.6)


@pytest.mark.parametrize("score", [-1, 1001, float("nan"), float("inf"), True, "500"])
def test_invalid_numeric_inputs_rejected(score):
    with pytest.raises(ValidationError):
        frequency.ManagementFactorInput(score=score)


def test_context_and_model_errors():
    with pytest.raises(ValidationError):
        Context(standard_edition="2008")
    with pytest.raises(ValidationError):
        Context(observed_at="2026-10-24T00:00:00")
    with pytest.raises(ValidationError):
        frequency.ManagementFactorInput(score=500, typo=1)
    with pytest.raises(TypeError):
        frequency.management_factor(frequency.GenericInput(component_type="PIPE-8"))


def test_no_fake_dispersion_fallback():
    assert all(not item["available"] for item in dispersion.capabilities())
    request = dispersion.DispersionRequest(
        engine="slabx-lh2", fluid_id="H2", release_height_m=1, wind_speed_m_s=2,
        wind_reference_height_m=10, ambient_temperature_k=293,
        source_profile=[dict(time_s=0, mass_rate_kg_s=1, temperature_k=20, vapor_mass_fraction=0)],
        requested_outputs=["lfl_area"])
    with pytest.raises(DomainError, match="not configured") as error:
        dispersion.execute(request)
    assert error.value.code == "engine_not_configured"


def test_documented_dispersion_capability_paths_are_real():
    from api581 import dispersion as generic_dispersion
    from api581.api import dispersion as typed_dispersion
    assert callable(generic_dispersion.capabilities)
    assert callable(typed_dispersion.native_engine_capabilities)
    root = Path(__file__).parents[1]
    assert '`dispersion.native_engine_capabilities()`' not in (root / 'README.md').read_text(encoding='utf-8')
    assert '`dispersion.native_engine_capabilities()`' not in (root / 'docs' / 'VERIFICATION_COMMANDS.md').read_text(encoding='utf-8')


def test_direct_composition_and_declarative_workflow_agree():
    power = effects.jet_fire_power(effects.JetFirePowerInput(mass_rate_kg_s=10, heat_of_combustion_j_kg=46e6))
    direct = effects.jet_fire_distance(effects.JetFireDistanceInput(
        radiated_power_w=power.outputs.radiated_power_w, threshold_w_m2=12600,
        transmissivity_model="constant", atmospheric_transmissivity=.8))
    workflow = Workflow(steps=[
        Step(step_id="power", calculation_id="effects/jet-fire-power", inputs=power.normalized_inputs),
        Step(step_id="distance", calculation_id="effects/jet-fire-distance", inputs={
            **direct.normalized_inputs, "radiated_power_w": {"$ref": "power.outputs.radiated_power_w"}})])
    result = run_workflow(workflow)
    assert result["steps"]["distance"]["outputs"] == direct.outputs.model_dump()
    assert direct.outputs.consequence_area_m2 == pytest.approx(2555.555555555556)


def test_invalid_workflow_references_and_nested_input():
    with pytest.raises(DomainError) as error:
        run_workflow(Workflow(steps=[Step(step_id="a", calculation_id="frequency/management-factor",
            inputs={"score": {"$ref": "later.outputs.score"}})]))
    assert error.value.code == "invalid_workflow"
    with pytest.raises(ValidationError):
        run_workflow(Workflow(steps=[Step(step_id="a", calculation_id="frequency/management-factor", inputs={"score": -1})]))


def test_output_contract_failure_is_distinct_from_input_failure(monkeypatch):
    old = REGISTRY["frequency/management-factor"]
    monkeypatch.setitem(REGISTRY, old.id, replace(old, function=lambda x: {"wrong_field": 1}))
    with pytest.raises(DomainError) as error:
        frequency.management_factor(frequency.ManagementFactorInput(score=500))
    assert error.value.code == "output_contract_violation"


def test_new_fatigue_factors_and_composition():
    base = damage.FatigueBaseInput(previous_failure_count=1, shaking_severity="severe",
        shaking_duration_band="2_to_13_weeks", cyclic_loading="reciprocating_machinery")
    adjustments = damage.FatigueAdjustmentsInput(corrective_action="none", total_pipe_fittings=11,
        damaged_or_improper_supports=True, broken_or_directly_welded_gussets=True,
        branch_design="tee_or_weldolet", any_branch_above_nps_2=False)
    # max(50, 500*.2, 50) * (2*2*2*.2*1) = 160; condition is OR, not doubled.
    full = damage.mechanical_fatigue(damage.MechanicalFatigueInput(base=base, adjustments=adjustments))
    assert full.outputs.base_damage_factor == 100
    assert full.outputs.damage_factor == pytest.approx(160)


@pytest.mark.parametrize("susceptibility,expected", [("none", 0), ("low", 100), ("medium", 2000), ("high", 5000), ("damage_observed", 5000)])
def test_htha_table(susceptibility, expected):
    assert damage.htha_factor(damage.HthaFactorInput(susceptibility=susceptibility)).outputs.damage_factor == expected


def test_htha_screen_and_ambiguous_applicability():
    pressure = properties.hydrogen_partial_pressure(properties.HydrogenPartialPressureInput(
        total_pressure_pa_abs=1e6, hydrogen_mole_fraction=.5))
    request = damage.HthaCarbonScreenInput(material_group="carbon_steel", exposure_temperature_k=500,
        hydrogen_partial_pressure_pa_abs=pressure.outputs.hydrogen_partial_pressure_pa_abs, damage_history="none")
    assert damage.htha_carbon_screen(request).outputs.damage_factor == 5000
    with pytest.raises(DomainError) as error:
        damage.htha_carbon_screen(request.model_copy(update={"exposure_temperature_k": 400}))
    assert error.value.code == "unresolved_applicability"


def test_source_contains_no_transport_dependency():
    root = Path(__file__).resolve().parents[1]
    metadata = (root / "pyproject.toml").read_text()
    assert "fastapi" not in metadata and "uvicorn" not in metadata and "httpx" not in metadata
    assert not (root / "src/api581/__main__.py").exists()
