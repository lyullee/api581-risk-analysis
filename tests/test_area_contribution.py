import math
import runpy
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import risk


def request(**changes):
    return risk.AreaEventContributionInput(**(dict(annual_release_frequency_per_year=.01,weather_probability_given_release=.25,
        event_probability_given_release_weather=.2,equipment_area_m2=20.,personnel_area_m2=80.,
        probability_source='Qualified conditional weather/event fixture')|changes))


def test_partial_contribution_weights_once_with_known_values():
    result=risk.area_event_contribution(request()).outputs
    assert result.conditional_joint_probability==.05
    assert result.annual_selected_event_frequency_per_year==.0005
    assert result.event_weighted_equipment_area_m2==1.
    assert result.event_weighted_personnel_area_m2==4.
    assert result.equipment_area_risk_contribution_m2_per_year==.01
    assert result.personnel_area_risk_contribution_m2_per_year==.04
    assert result.contribution_scope=='selected_event_weather_case'


@pytest.mark.parametrize('weather,event,frequency',[(0.,.2,.01),(.25,0.,.01),(1.,1.,.01),(.25,.2,0.)])
def test_probability_and_frequency_boundaries(weather,event,frequency):
    result=risk.area_event_contribution(request(weather_probability_given_release=weather,event_probability_given_release_weather=event,
        annual_release_frequency_per_year=frequency)).outputs
    assert math.isclose(result.area_risk_contribution_m2_per_year,frequency*weather*event*80.)
    assert result.event_weighted_personnel_area_m2==weather*event*80.


@pytest.mark.parametrize('changes',[dict(weather_probability_given_release=1.01),dict(event_probability_given_release_weather=-.1),
    dict(annual_release_frequency_per_year=-.01),dict(personnel_area_m2=float('inf'))])
def test_invalid_frequency_probability_and_area(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_blank_probability_basis_rejected():
    with pytest.raises(DomainError):
        risk.area_event_contribution(request(probability_source=' '))


@pytest.mark.parametrize('field',['damage_factor_source','hole_release_basis','probability_source'])
def test_integrated_source_gates_before_optional_engines(field):
    factory=runpy.run_path('examples/flashed_pool_risk_contribution.py')['request']
    with pytest.raises(DomainError) as caught:
        risk.flashed_pool_flash_fire_contribution(factory(**{field:' '}))
    assert caught.value.code=='outside_model_domain'


def test_unknown_component_rejected_before_optional_engines():
    factory=runpy.run_path('examples/flashed_pool_risk_contribution.py')['request']
    with pytest.raises(DomainError,match='Unsupported component_type'):
        risk.flashed_pool_flash_fire_contribution(factory(component_type='unknown-component'))
