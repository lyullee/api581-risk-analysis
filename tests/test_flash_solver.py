import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.flash_solver import PureFluidFlash, solve_pure_fluid_flash
from api581.flash_solver import PureLiquidFlashPartition, pure_liquid_flash_partition


def request(**changes):
    return PureFluidFlash(**(dict(fluid='Propane',storage_pressure_pa_abs=1e6,storage_temperature_k=300.,
        final_pressure_pa_abs=101325.,method='isentropic',qualification_basis='Qualified pure-fluid reference')|changes))


@pytest.mark.parametrize('fluid',['HEOS::Propane','Propane&Butane','../fluid',''])
def test_only_simple_fluid_identifiers(fluid):
    with pytest.raises(ValidationError): request(fluid=fluid)


def test_expansion_and_qualification_checked_before_engine_import():
    for changes in [dict(final_pressure_pa_abs=1e6),dict(final_pressure_pa_abs=2e6),dict(qualification_basis=' ')]:
        with pytest.raises(DomainError): solve_pure_fluid_flash(request(**changes))


def test_missing_optional_engine_reports_domain_error():
    import importlib.util
    if importlib.util.find_spec('CoolProp') is not None:
        pytest.skip('Engine installed in this environment')
    with pytest.raises(DomainError) as error: solve_pure_fluid_flash(request())
    assert error.value.code=='optional_engine_missing'


def test_partition_qualification_checked_before_optional_engine():
    inputs=PureLiquidFlashPartition(**request().model_dump(),adjusted_mass_rate_kg_s=1.,released_mass_kg=10.,
        equation_basis='post_flash_mass_balance',atmospheric_partition_basis=' ')
    with pytest.raises(DomainError,match='Atmospheric partition applicability'):
        pure_liquid_flash_partition(inputs)


@pytest.mark.parametrize('changes',[
    dict(storage_temperature_k=None),
    dict(storage_vapor_mass_fraction=.5),
    dict(storage_temperature_k=None,storage_vapor_mass_fraction=-.01),
    dict(storage_temperature_k=None,storage_vapor_mass_fraction=1.01),
    dict(storage_temperature_k=None,storage_vapor_mass_fraction=float('nan')),
    dict(storage_temperature_k=None,storage_vapor_mass_fraction=float('inf')),
])
def test_storage_coordinate_ambiguity_and_invalid_mass_quality(changes):
    with pytest.raises(ValidationError):
        request(**changes)


@pytest.mark.parametrize('quality',[0.,.5,1.])
def test_explicit_equilibrium_quality_accepts_endpoints(quality):
    model=request(storage_temperature_k=None,storage_vapor_mass_fraction=quality)
    assert model.storage_vapor_mass_fraction==quality and model.storage_temperature_k is None
