import runpy
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import dispersion


request=runpy.run_path('examples/flashed_pool_flash_fire.py')['request']


@pytest.mark.parametrize('changes',[
    dict(receptor_height_m=1.),dict(criterion_role='arbitrary_threshold'),dict(crosswind_points_per_side=2),
    dict(crosswind_half_span_m=0.)])
def test_flash_fire_requires_ground_lfl_and_valid_sampling(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_qualification_gate_precedes_optional_engines():
    with pytest.raises(DomainError) as caught:
        dispersion.flashed_boiling_pool_flash_fire(request(native_property_basis=' '))
    assert caught.value.code=='outside_model_domain'
