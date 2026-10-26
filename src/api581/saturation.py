"""Optional pure-fluid equilibrium properties for Level2 pool source calculations."""
import math
from pydantic import Field
from .core import Model, Positive, DomainError, calculation, ensure


class PureFluidIdentity(Model):
    fluid: str = Field(pattern=r'^[A-Za-z][A-Za-z0-9_-]{0,79}$')
    qualification_basis: str = Field(min_length=1)


class SaturationPressure(PureFluidIdentity):
    pressure_pa_abs: Positive


class SaturationTemperature(PureFluidIdentity):
    temperature_k: Positive


def _saturation(inputs, coordinate):
    ensure(bool(inputs.qualification_basis.strip()),'Fluid identity and EOS applicability qualification required')
    try:
        import CoolProp
        from CoolProp.CoolProp import PropsSI, get_fluid_param_string
    except ImportError:
        ensure(False,'Pure-fluid saturation requires optional CoolProp8.0.0','optional_engine_missing')
    ensure(CoolProp.__version__=='8.0.0','Saturation backend requires tested CoolProp8.0.0','engine_version_mismatch')
    fluid=inputs.fluid
    try:
        ensure(get_fluid_param_string(fluid,'pure')=='true','Pseudopure fluids and mixtures are outside pure-fluid saturation scope','unsupported_saturation_fluid')
        value=inputs.pressure_pa_abs if coordinate=='P' else inputs.temperature_k
        lower=PropsSI('ptriple' if coordinate=='P' else 'Ttriple',fluid)
        upper=PropsSI('pcrit' if coordinate=='P' else 'Tcrit',fluid)
        ensure(lower<=value<upper,'Saturation coordinate must be at/above triple point and below critical point','unsupported_saturation_state')
        def prop(name, quality):
            return PropsSI(name,coordinate,value,'Q',quality,fluid)
        temperature=prop('T',0.)
        latent=prop('Hmass',1.)-prop('Hmass',0.)
        output=dict(saturation_pressure_pa_abs=prop('P',0.),bubble_temperature_k=temperature,
            dew_temperature_k=prop('T',1.),liquid_density_kg_m3=prop('Dmass',0.),vapor_density_kg_m3=prop('Dmass',1.),
            liquid_specific_heat_j_kg_k=prop('Cpmass',0.),latent_heat_j_kg=latent,
            vapor_specific_heat_j_kg_k=prop('Cpmass',1.),
            molecular_weight_kg_kmol=PropsSI('molar_mass',fluid)*1000.)
        ensure(all(math.isfinite(v) and v>0 for v in output.values()),'Nonfinite or nonpositive saturation property','invalid_engine_result')
        return {**output,'engine_version':CoolProp.__version__}
    except ValueError as exc:
        if isinstance(exc,DomainError):
            raise
        ensure(False,'CoolProp could not solve supplied pure-fluid saturation state','saturation_solver_failure')


_LIMITS=['Optional CoolProp8.0.0 HEOS pure fluids only. Triple-point to subcritical equilibrium saturation; no metastable, solid, pseudopure or mixture states. Saturated liquid cp/densities and latent heat are evaluated on the coexistence curve, not at storage or arbitrary flash temperature. Pure-fluid bubble/dew temperatures coincide. No heat of combustion, flammability, transient evaporation or fluid-wide/LH2 validation. Caller qualifies EOS and physical applicability.']


@calculation('properties/pure-fluid-saturation-pressure','Pure-fluid bubble/dew and saturated properties at pressure',SaturationPressure,
    ['Part3 §5.1.3-5.1.4 STEP1.4; §5.7.4.2; PDF pp540-541,544'],
    origin='optional_coolprop_8_0_0_pure_fluid_saturation',limitations=_LIMITS)
def saturation_pressure(inputs):
    return _saturation(inputs,'P')


@calculation('properties/pure-fluid-saturation-temperature','Pure-fluid vapor pressure and saturated properties at temperature',SaturationTemperature,
    ['Part3 §5.7.4.3 eq(3.105); PDF p544'],
    origin='optional_coolprop_8_0_0_pure_fluid_saturation',limitations=_LIMITS)
def saturation_temperature(inputs):
    return _saturation(inputs,'T')
