"""Real optional EOS verification, separate from dependency-free unit checks."""
from api581 import DomainError
from api581.api import properties, release
from CoolProp.CoolProp import PropsSI


def flash(**changes):
    return properties.pure_fluid_flash(properties.PureFluidFlashInput(**(dict(fluid='Propane',storage_pressure_pa_abs=1e6,
        storage_temperature_k=300.,final_pressure_pa_abs=101325.,method='isentropic',qualification_basis='Qualified native reference fixture')|changes))).outputs


for method,quality in [('isentropic',.34426146819171444),('isenthalpic',.398968185444062)]:
    r=flash(method=method)
    assert r.flashed_phase=='twophase' and abs(r.vapor_mass_fraction-quality)<1e-10
    assert abs(r.flashed_temperature_k-231.0362146443222)<1e-7
    assert r.storage_vapor_mass_fraction==0. and r.vapor_mass_fraction_change==r.vapor_mass_fraction
    # Reconstruct the final state independently from pressure and mass quality.
    recovered=PropsSI(r.conserved_property,'P',101325.,'Q',r.vapor_mass_fraction,'Propane')
    assert abs(recovered-r.conserved_value_si) <= 1e-7*max(1.,abs(r.conserved_value_si))
gas=flash(storage_temperature_k=450.)
assert gas.flashed_phase=='gas' and gas.vapor_mass_fraction==1.
assert gas.storage_vapor_mass_fraction==1. and gas.vapor_mass_fraction_change==0.
liquid=flash(storage_temperature_k=180.)
assert liquid.flashed_phase=='liquid' and liquid.vapor_mass_fraction==0.
assert liquid.storage_vapor_mass_fraction==0. and liquid.vapor_mass_fraction_change==0.
try:
    flash(storage_pressure_pa_abs=1e7,storage_temperature_k=600.)
except DomainError as exc:
    assert exc.code=='unsupported_storage_phase'
else:
    raise AssertionError('Unclassified supercritical storage accepted')
for fluid in ['Air','R410A']:
    try:
        flash(fluid=fluid)
    except DomainError as exc:
        assert exc.code=='unsupported_flash_fluid'
    else:
        raise AssertionError('Pseudopure fluid accepted')
print('VERIFIED: native flash two methods, single-phase liquid/gas, pseudopure rejection')

def partition(**changes):
    return release.pure_liquid_flash_partition(release.PureLiquidFlashPartitionInput(**(dict(
        fluid='Propane',storage_pressure_pa_abs=3e6,storage_temperature_k=350.,
        final_pressure_pa_abs=101325.,method='isenthalpic',qualification_basis='Qualified pure-propane EOS fixture',
        adjusted_mass_rate_kg_s=10.,released_mass_kg=100.,equation_basis='post_flash_mass_balance',
        atmospheric_partition_basis='Atmospheric pure-propane Kletz demonstration only')|changes))).outputs

for basis in ['api581_printed','post_flash_mass_balance']:
    r=partition(equation_basis=basis)
    assert .5 < r.vapor_mass_fraction < 1.
    assert abs(r.pool_liquid_mass_kg+r.jet_liquid_mass_kg+r.jet_vapor_mass_kg-100.)<1e-10
    assert abs(r.pool_liquid_rate_kg_s+r.jet_liquid_rate_kg_s+r.jet_vapor_rate_kg_s-10.)<1e-10
    expected=r.vapor_mass_fraction if basis=='post_flash_mass_balance' else 1-r.vapor_mass_fraction
    assert abs(r.jet_vapor_mass_fraction-expected)<1e-10
for temperature,expected_pool in [(180.,100.),(300.,None)]:
    r=partition(storage_temperature_k=temperature)
    if expected_pool is not None:
        assert r.pool_liquid_mass_kg==expected_pool and r.jet_total_mass_kg==0.
    else:
        assert abs(r.jet_vapor_mass_kg-100.*r.vapor_mass_fraction)<1e-10
try:
    partition(storage_temperature_k=450.)
except DomainError as exc:
    assert exc.code=='unsupported_partition_storage_phase'
else:
    raise AssertionError('Initially gaseous fluid accepted by liquid-flash partition')
print('VERIFIED: typed flash partition, explicit composition bases, mass/rate closure, liquid endpoint, gas rejection')

for method,property_name in [('isentropic','Smass'),('isenthalpic','Hmass')]:
    for initial_quality in [0.,.2,.9,1.]:
        result=flash(storage_temperature_k=None,storage_vapor_mass_fraction=initial_quality,method=method)
        assert result.storage_state_basis=='pressure_quality' and result.storage_phase=='twophase'
        assert result.storage_vapor_mass_fraction==initial_quality
        assert abs(result.vapor_mass_fraction_change-(result.vapor_mass_fraction-initial_quality))<1e-12
        initial=(1-initial_quality)*PropsSI(property_name,'P',1e6,'Q',0.,'Propane')+initial_quality*PropsSI(property_name,'P',1e6,'Q',1.,'Propane')
        assert abs(initial-result.conserved_value_si)<1e-7*max(1.,abs(initial))
        coordinate='Q' if result.flashed_phase=='twophase' else 'T'
        state=result.vapor_mass_fraction if coordinate=='Q' else result.flashed_temperature_k
        final=PropsSI(property_name,'P',101325.,coordinate,state,'Propane')
        assert abs(final-initial)<1e-7*max(1.,abs(initial))
condensation=flash(storage_temperature_k=None,storage_vapor_mass_fraction=.9)
assert abs(condensation.vapor_mass_fraction-.8857022756860086)<1e-10
assert condensation.vapor_mass_fraction_change<0.
assert flash().storage_state_basis=='pressure_temperature'
for pressure in [PropsSI('pcrit','Propane'),PropsSI('ptriple','Propane')*.5]:
    try:
        flash(storage_temperature_k=None,storage_pressure_pa_abs=pressure,
            final_pressure_pa_abs=pressure*.5,storage_vapor_mass_fraction=.5)
    except DomainError as exc:
        assert exc.code=='unsupported_storage_phase'
    else:
        raise AssertionError('Quality outside liquid-vapor coexistence pressure accepted')
try:
    flash(storage_temperature_k=PropsSI('T','P',1e6,'Q',0.,'Propane'))
except DomainError as exc:
    assert exc.code=='unsupported_storage_phase'
else:
    raise AssertionError('Ambiguous saturated PT state accepted')
partition(storage_temperature_k=None,storage_vapor_mass_fraction=0.)
try:
    partition(storage_temperature_k=None,storage_vapor_mass_fraction=.2)
except DomainError as exc:
    assert exc.code=='unsupported_partition_storage_phase'
else:
    raise AssertionError('Initial two-phase mixture accepted by liquid-only Kletz composition')
print('VERIFIED: equilibrium storage quality endpoints/interior, conservation, signed condensation, PT ambiguity, domain guards')
