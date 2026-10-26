"""Optional CoolProp8.0.0 saturation regression and thermodynamic identities."""
import runpy
from api581 import DomainError
from api581.api import properties
from CoolProp.CoolProp import PropsSI


def at_pressure(fluid='Propane',pressure=101325.):
    return properties.pure_fluid_saturation_pressure(properties.PureFluidSaturationPressureInput(
        fluid=fluid,pressure_pa_abs=pressure,qualification_basis='Qualified native saturation fixture')).outputs


def at_temperature(fluid,temperature):
    return properties.pure_fluid_saturation_temperature(properties.PureFluidSaturationTemperatureInput(
        fluid=fluid,temperature_k=temperature,qualification_basis='Qualified native saturation fixture')).outputs


for fluid,expected_temperature in [('Propane',231.0362146443222),('Water',373.1242958476665)]:
    result=at_pressure(fluid)
    assert abs(result.bubble_temperature_k-expected_temperature)<1e-6
    assert abs(result.bubble_temperature_k-result.dew_temperature_k)<1e-8
    assert result.liquid_density_kg_m3>result.vapor_density_kg_m3
    assert abs(at_temperature(fluid,result.bubble_temperature_k).saturation_pressure_pa_abs-101325.)<.01
    # Clapeyron identity: EOS saturation pressure slope vs latent heat/specific volumes.
    temperature=result.bubble_temperature_k
    difference=(at_temperature(fluid,temperature+.001).saturation_pressure_pa_abs-
        at_temperature(fluid,temperature-.001).saturation_pressure_pa_abs)/.002
    expected=result.latent_heat_j_kg/(temperature*(1/result.vapor_density_kg_m3-1/result.liquid_density_kg_m3))
    assert abs(difference/expected-1.)<1e-6
for fluid in ['Air','R410A']:
    try:
        at_pressure(fluid)
    except DomainError as error:
        assert error.code=='unsupported_saturation_fluid'
    else:
        raise AssertionError('Pseudopure saturation accepted')
for action in [lambda:at_pressure(pressure=PropsSI('pcrit','Propane')),
        lambda:at_temperature('Propane',PropsSI('Tcrit','Propane')),
        lambda:at_pressure(pressure=PropsSI('ptriple','Propane')*.5),
        lambda:at_temperature('Propane',PropsSI('Ttriple','Propane')*.9)]:
    try:
        action()
    except DomainError as error:
        assert error.code=='unsupported_saturation_state'
    else:
        raise AssertionError('Unsupported saturation state accepted')
runpy.run_path('examples/saturation_to_pool.py',run_name='__main__')
print('VERIFIED: two pure fluids, pressure-temperature round trip, Clapeyron identity, domain guards, pool examples')
