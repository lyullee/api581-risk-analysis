import importlib.util
import pytest
from api581 import DomainError
from api581.saturation import SaturationPressure, SaturationTemperature, saturation_pressure, saturation_temperature


@pytest.mark.parametrize('model,kernel,coordinate',[(SaturationPressure,saturation_pressure,dict(pressure_pa_abs=101325.)),
    (SaturationTemperature,saturation_temperature,dict(temperature_k=300.))])
def test_qualification_precedes_optional_engine(model,kernel,coordinate):
    with pytest.raises(DomainError,match='qualification required'):
        kernel(model(fluid='Propane',qualification_basis=' ',**coordinate))


@pytest.mark.parametrize('model,kernel,coordinate',[(SaturationPressure,saturation_pressure,dict(pressure_pa_abs=101325.)),
    (SaturationTemperature,saturation_temperature,dict(temperature_k=300.))])
def test_dependency_free_saturation_error(model,kernel,coordinate):
    if importlib.util.find_spec('CoolProp') is not None:
        pytest.skip('Optional engine installed')
    with pytest.raises(DomainError) as caught:
        kernel(model(fluid='Propane',qualification_basis='Qualified pure-fluid fixture',**coordinate))
    assert caught.value.code=='optional_engine_missing'
