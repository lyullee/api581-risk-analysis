import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.AcsccWaterSusceptibilityInput(**(dict(water_ph=7.7,carbonate_ppm=100.,pwht=False,
        carbonate_measurement_basis='Qualified carbonate-specific analysis, not P/M titration',traditional_alkalinity_only=False,
        service_fabrication_basis='Qualified PWHT/fabrication and service fixture')|changes))


@pytest.mark.parametrize('ph,carbonate,level',[(7.4,100.,'none'),(7.5,99.,'low'),(7.5,100.,'medium'),
    (8.5,99.,'low'),(8.5,100.,'high'),(9.1,0.,'high')])
def test_source_rows_and_carbonate_boundary(ph,carbonate,level):
    assert damage.acscc_water_susceptibility(request(water_ph=ph,carbonate_ppm=carbonate)).outputs.susceptibility==level
    assert damage.acscc_water_susceptibility(request(water_ph=ph,carbonate_ppm=carbonate,pwht=True)).outputs.susceptibility=='none'


@pytest.mark.parametrize('ph,carbonate,lower,higher',[(8.,100.,'medium','high'),(9.,99.,'low','high')])
def test_shared_ph_explicit_policy(ph,carbonate,lower,higher):
    with pytest.raises(DomainError):
        damage.acscc_water_susceptibility(request(water_ph=ph))
    for policy,level in [('lower_ph_row',lower),('higher_ph_row',higher)]:
        r=damage.acscc_water_susceptibility(request(water_ph=ph,carbonate_ppm=carbonate,shared_ph_boundary_policy=policy)).outputs
        assert r.susceptibility==level and r.shared_ph_boundary_encountered


def test_alkalinity_is_not_carbonate_measurement():
    with pytest.raises(DomainError) as caught:
        damage.acscc_water_susceptibility(request(traditional_alkalinity_only=True))
    assert caught.value.code=='unsupported_carbonate_measurement'


def test_unused_boundary_policy_rejected():
    with pytest.raises(DomainError):
        damage.acscc_water_susceptibility(request(shared_ph_boundary_policy='higher_ph_row'))
