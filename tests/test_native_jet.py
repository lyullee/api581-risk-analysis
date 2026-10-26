"""Jet state validation and same-partition handoff without synthetic physics."""
import runpy
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import dispersion
from api581.jet_handoff import partitioned_jet


def request(**changes):
    factory = runpy.run_path('examples/native_jet_dispersion.py')['request']
    return factory(**changes)


def geometry(**changes):
    return {k:v for k,v in request().model_dump().items() if k not in {
        'mass_source_rate_kg_s','release_duration_s','jet_liquid_mass_fraction'}}|changes


def partition(**changes):
    return dict(adjusted_mass_rate_kg_s=2.,released_mass_kg=120.,rainout_mass_fraction=.25,
        equation_basis='post_flash_mass_balance',post_flash_vapor_mass_fraction=.5,
        rainout_basis_source='Qualified rainout fixture',flash_property_source='Qualified flash fixture')|changes


@pytest.mark.parametrize('changes',[
    dict(jet_liquid_mass_fraction=1.),dict(jet_exit_area_m2=0),dict(orientation='downward'),
    dict(mass_source_rate_kg_s=0),dict(source_temperature_k=220.),
    dict(jet_liquid_mass_fraction=.2),dict(temperature_basis='silent_clamp')])
def test_unsupported_or_inconsistent_native_source_rejected(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_native_temperature_clamping_is_an_explicit_input_choice():
    x = request(jet_liquid_mass_fraction=.2,source_temperature_k=250.,temperature_basis='allow_native_clamp')
    assert x.source_temperature_k == 250.
    x = request(jet_liquid_mass_fraction=.2,source_temperature_k=231.)
    assert x.temperature_basis == 'require_consistent'


def test_partition_derives_total_jet_rate_liquid_fraction_and_duration(monkeypatch):
    captured = []
    def receive(x):
        captured.append(x)
        return dict(orientation=x.orientation)
    monkeypatch.setattr('api581.jet_handoff.native_jet',receive)
    output = partitioned_jet(dispersion.PartitionedJetCentrelineInput(partition=partition(),
        jet=geometry(source_temperature_k=231.)))
    sent = captured[0]
    assert sent.mass_source_rate_kg_s == 1.5
    assert sent.release_duration_s == 60.
    assert sent.jet_liquid_mass_fraction == pytest.approx(1/3)
    assert output['pool_liquid_rate_kg_s'] == .5
    assert output['jet_vapor_rate_kg_s'] == 1.
    assert output['jet_liquid_rate_kg_s'] == pytest.approx(.5)


@pytest.mark.parametrize('changes,code',[
    (dict(rainout_mass_fraction=1.,post_flash_vapor_mass_fraction=0.),'empty_jet_source'),
    (dict(adjusted_mass_rate_kg_s=0),'empty_jet_source'),
    (dict(released_mass_kg=0),'empty_jet_source'),
    (dict(post_flash_vapor_mass_fraction=0.),'unsupported_engine_source_domain')])
def test_no_jet_and_pure_liquid_partition_fail_before_engine(changes,code,monkeypatch):
    def never_run(x):
        raise AssertionError('Unsupported jet reached native engine')
    monkeypatch.setattr('api581.jet_handoff.native_jet',never_run)
    with pytest.raises(DomainError) as exc:
        partitioned_jet(dispersion.PartitionedJetCentrelineInput(partition=partition(**changes),jet=geometry()))
    assert exc.value.code == code


def test_partition_temperature_conflict_is_explicit_domain_error():
    with pytest.raises(DomainError) as exc:
        partitioned_jet(dispersion.PartitionedJetCentrelineInput(partition=partition(),jet=geometry(source_temperature_k=250.)))
    assert exc.value.code == 'native_source_state_inconsistent'


@pytest.mark.parametrize('duplicate',[
    dict(mass_source_rate_kg_s=1.),dict(release_duration_s=60.),dict(jet_liquid_mass_fraction=.2)])
def test_no_duplicate_source_quantities_in_partitioned_geometry(duplicate):
    with pytest.raises(ValidationError):
        dispersion.PartitionedJetCentrelineInput(partition=partition(),jet=geometry(**duplicate))
