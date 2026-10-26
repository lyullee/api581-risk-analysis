"""Priority, duration, explicit exclusions and pure-species native gating."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import consequence, dispersion
from api581.native_toxic import native_toxic_pool


def criterion(**changes):
    return consequence.SelectToxicCriterionInput(**(dict(fluid_id="chlorine",exposure_duration_s=600.,
        candidate_availability_basis="2016 table and qualified external criteria review fixture")|changes))


def external(identifier="external:lc50",kind="lc50",ppm=100.,duration=600.):
    return dict(criterion_id=identifier,kind=kind,concentration_ppm=ppm,exposure_duration_s=duration,source="Qualified test criterion source")


def source(**changes):
    return dict(substance=dict(fluid_id="chlorine",molecular_weight_kg_kmol=70.906,
        vapor_heat_capacity_j_kg_k=479.,liquid_heat_capacity_j_kg_k=950.,latent_heat_j_kg=287000.,
        normal_boiling_point_k=239.11,liquid_density_kg_m3=1467.,property_source="Qualified chlorine property fixture"),
        atmosphere=dict(wind_speed_m_s=3.,wind_reference_height_m=10.,temperature_k=293.,pressure_pa_abs=101325.,
            relative_humidity_fraction=.5,roughness_length_m=.01,stability="D"),
        vapor_source_rate_kg_s=1.,source_area_m2=10.,available_mass_kg=1200.,detection_maximum_duration_s=600.,
        receptor_height_m=0.,plume_distance_limit_m=5000.,crosswind_half_span_m=500.,crosswind_points_per_side=129,
        source_qualification="Qualified pure chlorine finite constant vapor pool fixture",meander_closure="ermak")|changes


def native_request(**changes):
    return dispersion.NativePoolToxicConsequenceInput(**(dict(criterion=criterion(),source=source(),non_ignition_probability=.8,
        exposure_model_basis="constant_exposure_equivalent_native_time_average")|changes))


def test_table_probit50_selected_by_priority_and_seconds_anchor():
    r = consequence.select_toxic_criterion(criterion()).outputs
    assert r.selected_criterion_id == "printed:probit50" and r.priority_tier == 1
    expected = math.exp(((5+8.29)/.92-math.log(600.))/2)
    assert r.pure_component_limit_ppm == pytest.approx(expected)
    assert r.threshold_volume_fraction == pytest.approx(expected/1e6)
    assert "printed:epa_endpoint" in r.unavailable_candidate_reasons


@pytest.mark.parametrize("fluid,duration,kind,value",[
    ("methanol",600.,"aegl3",15000.),("methanol",1800.,"aegl3",15000.),
    ("methanol",3600.,"aegl3",7900.),("styrene",1800.,"idlh",700.),("styrene",3600.,"erpg3",1000.)])
def test_missing_probit_fallback_exact_table_duration(fluid,duration,kind,value):
    r = consequence.select_toxic_criterion(criterion(fluid_id=fluid,exposure_duration_s=duration)).outputs
    assert r.selected_kind == kind and r.pure_component_limit_ppm == value


def test_same_priority_requires_choice_and_lower_priority_requires_exclusion():
    x = criterion(additional_candidates=[external()])
    with pytest.raises(DomainError) as exc:
        consequence.select_toxic_criterion(x)
    assert exc.value.code == "ambiguous_toxic_criterion"
    r = consequence.select_toxic_criterion(criterion(additional_candidates=[external()],selected_criterion_id="external:lc50")).outputs
    assert r.pure_component_limit_ppm == 100.
    with pytest.raises(DomainError) as exc:
        consequence.select_toxic_criterion(criterion(additional_candidates=[external(kind="aegl3")],selected_criterion_id="external:lc50"))
    assert exc.value.code == "toxic_criterion_priority_conflict"
    r = consequence.select_toxic_criterion(criterion(additional_candidates=[external(kind="aegl3")],
        selected_criterion_id="external:lc50",excluded_candidate_ids={"printed:probit50":"Qualified coeff/species applicability exclusion"})).outputs
    assert r.priority_tier == 2 and r.pure_component_limit_ppm == 100.


def test_wrong_duration_is_not_interpolated_and_unknown_fluid_requires_external_mode():
    with pytest.raises(DomainError) as exc:
        consequence.select_toxic_criterion(criterion(fluid_id="methanol",exposure_duration_s=601.))
    assert exc.value.code == "toxic_criterion_unavailable"
    with pytest.raises(DomainError):
        consequence.select_toxic_criterion(criterion(fluid_id="new_species",additional_candidates=[external()]))
    r = consequence.select_toxic_criterion(criterion(fluid_id="new_species",use_printed_table=False,additional_candidates=[external()])).outputs
    assert r.selected_kind == "lc50"


@pytest.mark.parametrize("fraction,present,attainable",[(0.,False,False),(.05,True,True),(1e-9,True,False)])
def test_mixture_mole_fraction_and_attainability(fraction,present,attainable):
    r = consequence.select_toxic_criterion(criterion(toxic_mole_fraction=fraction)).outputs
    assert r.component_present == present and r.attainable_in_mixture == attainable
    if attainable:
        assert r.modified_mixture_limit_ppm == pytest.approx(r.pure_component_limit_ppm/fraction)
    else:
        assert r.threshold_volume_fraction is None


@pytest.mark.parametrize("changes",[
    dict(excluded_candidate_ids={"printed:probit50":"   "}),dict(excluded_candidate_ids={"unknown":"fixture"}),
    dict(candidate_availability_basis="   "),dict(additional_candidates=[external(),external()]),
    dict(additional_candidates=[external(identifier="printed:probit50")])])
def test_ambiguous_unqualified_or_duplicate_criteria_rejected(changes):
    with pytest.raises(DomainError):
        consequence.select_toxic_criterion(criterion(**changes))


@pytest.mark.parametrize("changes,code",[
    (dict(criterion=criterion(toxic_mole_fraction=.05)),"unsupported_mixture_source"),
    (dict(source=source(available_mass_kg=60.)),"toxic_exposure_duration_unsupported"),
    (dict(criterion=criterion(fluid_id="hydrogen_sulfide")),"toxic_species_mismatch")])
def test_native_bridge_fails_before_engine_for_unsupported_exposure(changes,code,monkeypatch):
    monkeypatch.setattr("api581.native_toxic.native_pool_footprint",lambda x:(_ for _ in ()).throw(AssertionError("Should not run native")))
    with pytest.raises(DomainError) as exc:
        native_toxic_pool(native_request(**changes))
    assert exc.value.code == code


def test_native_bridge_derives_threshold_window_and_weights_toxic_once(monkeypatch):
    captured = []
    def receive(x):
        captured.append(x)
        return dict(threshold_area_m2=100.,footprint_status="closed_on_supplied_grid")
    monkeypatch.setattr("api581.native_toxic.native_pool_footprint",receive)
    r = native_toxic_pool(native_request())
    assert captured[0].release_duration_s == captured[0].averaging_time_s == 600.
    assert captured[0].threshold_volume_fraction == pytest.approx(r["pure_component_limit_ppm"]/1e6)
    assert r["personnel_area_m2"] == 80. and r["equipment_area_m2"] == 0.


def test_censored_native_toxic_area_does_not_become_zero_consequence(monkeypatch):
    monkeypatch.setattr("api581.native_toxic.native_pool_footprint",lambda x:dict(threshold_area_m2=None,footprint_status="boundary_censored"))
    with pytest.raises(DomainError) as exc:
        native_toxic_pool(native_request())
    assert exc.value.code == "dispersion_footprint_unusable"


@pytest.mark.parametrize("kind,duration",[("idlh",600.),("erpg3",1800.),("teel3",600.),("aegl3",601.)])
def test_external_criteria_must_preserve_source_exposure_windows(kind,duration):
    with pytest.raises(ValidationError):
        criterion(additional_candidates=[external(kind=kind,duration=duration)])


def test_toxic_bridge_requires_grade_level():
    with pytest.raises(ValidationError):
        native_request(source=source(receptor_height_m=1.))
