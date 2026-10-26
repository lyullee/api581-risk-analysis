"""Optional native adapter validation/protocol failures without surrogate physics."""
import subprocess
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import dispersion
from api581.slabx_adapter import native_pool, native_pool_flash_fire


def request(**changes):
    return dispersion.NativePoolCentrelineInput(**(dict(engine="slabx",
        substance=dict(fluid_id="methane",molecular_weight_kg_kmol=16.043,vapor_heat_capacity_j_kg_k=2238.,
            liquid_heat_capacity_j_kg_k=3348.5,latent_heat_j_kg=509900.,normal_boiling_point_k=111.7,
            liquid_density_kg_m3=424.1,property_source="qualified test properties"),
        atmosphere=dict(wind_speed_m_s=1.94,wind_reference_height_m=3.,temperature_k=290.,pressure_pa_abs=101325.,
            relative_humidity_fraction=.5,roughness_length_m=.0002,stability="E"),
        vapor_source_rate_kg_s=116.93,source_area_m2=700.,release_duration_s=107.,receptor_height_m=1.,
        averaging_time_s=80.,plume_distance_limit_m=2000.,threshold_volume_fraction=.05,
        threshold_source="qualified test criterion",source_qualification="qualified vapor pool fixture",
        meander_closure="ermak",lh2_plume_width_coupling=False)|changes))


@pytest.mark.parametrize("field,value",[("vapor_source_rate_kg_s",0),("threshold_volume_fraction",5),
    ("averaging_time_s",0),("release_duration_s",float("inf")),("puff_steps",True),
    ("source_qualification","   "),("lh2_plume_width_coupling",True)])
def test_no_silent_native_defaults_or_unit_coercion(field,value):
    with pytest.raises(ValidationError):
        request(**{field:value})


def test_lh2_requires_explicit_hydrogen_not_fuel_alias_or_lng_properties():
    with pytest.raises(ValidationError):
        request(engine="slabx-lh2")
    properties = request().substance.model_dump()|dict(fluid_id="hydrogen",molecular_weight_kg_kmol=2.016)
    assert request(engine="slabx-lh2",substance=properties,lh2_plume_width_coupling=True).engine == "slabx-lh2"


def test_unqualified_pressure_and_invalid_reference_wind_rejected():
    for update in [dict(pressure_pa_abs=90000.),dict(wind_reference_height_m=.0001)]:
        atmosphere = request().atmosphere.model_dump()|update
        with pytest.raises(ValidationError):
            request(atmosphere=atmosphere)


def test_timeout_is_explicit_and_not_a_fallback(monkeypatch):
    def timeout(*args,**kwargs):
        assert kwargs["capture_output"] and kwargs["input"]
        raise subprocess.TimeoutExpired("native-worker",1)
    monkeypatch.setattr("api581.slabx_adapter.subprocess.run",timeout)
    with pytest.raises(DomainError) as exc:
        native_pool(request())
    assert exc.value.code == "engine_timeout"


@pytest.mark.parametrize("stdout,returncode,code",[
    ('',0,"engine_protocol_failure"),('[]',0,"engine_protocol_failure"),
    ('{}',0,"engine_result_invalid"),
    ('{"code":"engine_not_configured","error":"Optional package absent"}',1,"engine_not_configured"),
    ('{"code":"unsupported_engine_version","error":"Version mismatch"}',1,"unsupported_engine_version")])
def test_worker_protocol_and_engine_errors_stay_explicit(monkeypatch,stdout,returncode,code):
    monkeypatch.setattr("api581.slabx_adapter.subprocess.run",lambda *args,**kwargs:SimpleNamespace(stdout=stdout,returncode=returncode))
    with pytest.raises(DomainError) as exc:
        native_pool(request())
    assert exc.value.code == code


def test_worker_stderr_is_preserved_as_bounded_diagnostic(monkeypatch):
    monkeypatch.setattr("api581.slabx_adapter.subprocess.run", lambda *args, **kwargs:
        SimpleNamespace(stdout="", stderr="native traceback\n" * 200, returncode=0))
    with pytest.raises(DomainError) as exc:
        native_pool(request())
    assert exc.value.code == "engine_protocol_failure"
    assert "native traceback" in str(exc.value)
    assert len(str(exc.value)) < 700


@pytest.mark.parametrize("kwargs",[dict(crosswind_half_span_m=0),dict(crosswind_points_per_side=True),dict(crosswind_points_per_side=1001)])
def test_native_footprint_requires_bounded_physical_grid(kwargs):
    values = request().model_dump()|dict(crosswind_half_span_m=250.,crosswind_points_per_side=65)|kwargs
    with pytest.raises(ValidationError):
        dispersion.NativePoolFootprintInput(**values)


@pytest.mark.parametrize("status",["boundary_censored","premise_violated"])
def test_invalid_native_footprint_cannot_become_flash_consequence(monkeypatch,status):
    monkeypatch.setattr("api581.slabx_adapter.native_pool_footprint",lambda x:dict(threshold_area_m2=None,footprint_status=status))
    x = dispersion.NativePoolFlashFireInput(**(request().model_dump()|dict(receptor_height_m=0.)),crosswind_half_span_m=250.,criterion_role="qualified_lfl")
    with pytest.raises(DomainError) as exc:
        native_pool_flash_fire(x)
    assert exc.value.code == "dispersion_footprint_unusable"


@pytest.mark.parametrize("area",[0.,100.])
def test_flash_bridge_applies_quarter_factor_without_event_weight(monkeypatch,area):
    monkeypatch.setattr("api581.slabx_adapter.native_pool_footprint",lambda x:dict(threshold_area_m2=area,footprint_status="not_reached" if area == 0 else "closed_on_supplied_grid"))
    x = dispersion.NativePoolFlashFireInput(**(request().model_dump()|dict(receptor_height_m=0.)),crosswind_half_span_m=250.,criterion_role="qualified_lfl")
    r = native_pool_flash_fire(x)
    assert r["personnel_area_m2"] == area and r["equipment_area_m2"] == .25*area


def test_api581_flash_bridge_requires_grade_level():
    with pytest.raises(ValidationError):
        dispersion.NativePoolFlashFireInput(**request().model_dump(),crosswind_half_span_m=250.,criterion_role="qualified_lfl")


def test_engine_capability_probe_is_nonfatal_and_reports_contract():
    result = dispersion.native_engine_capabilities(
        dispersion.NativeEngineCapabilitiesInput(requested_engines=["slabx-lh2"])
    ).outputs
    assert result.requested_engines == ["slabx", "slabx-lh2"]
    assert result.worker_isolation == "subprocess"
    assert result.probe_scope == "package_presence_version_and_importability"
    assert set(result.module_import_status) == {"slabx", "slabx-lh2"}
    assert set(result.engine_status) == {"slabx", "slabx-lh2"}


def test_matching_distribution_with_broken_import_is_not_available(monkeypatch):
    monkeypatch.setattr("api581.slabx_adapter.importlib.metadata.version", lambda name: {"slabx": "1.0.8"}[name])
    monkeypatch.setattr("api581.slabx_adapter.importlib.util.find_spec", lambda name: None)
    result = dispersion.native_engine_capabilities(
        dispersion.NativeEngineCapabilitiesInput(requested_engines=["slabx"])
    ).outputs
    assert result.engine_status["slabx"] == "not_importable"
    assert result.module_import_status["slabx"] == "not_importable"
