import runpy
import pytest
from api581 import DomainError
from api581.api import dispersion


request=runpy.run_path('examples/flashed_boiling_pool.py')['request']


@pytest.mark.parametrize('changes,code',[
    (dict(released_mass_kg=0.),'no_source_window'),
    (dict(adjusted_mass_rate_kg_s=0.),'no_source_window'),
    (dict(final_pressure_pa_abs=100000.),'outside_model_domain'),
    (dict(native_property_basis=' '),'outside_model_domain'),
    (dict(threshold_source=' '),'outside_model_domain'),
])
def test_source_and_qualification_gates_before_engines(changes,code):
    with pytest.raises(DomainError) as caught:
        dispersion.flashed_boiling_pool_centreline(request(**changes))
    assert caught.value.code==code
