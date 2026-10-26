"""Optional pure-fluid CoolProp flash backend with typed public registry integration."""
import math
from typing import Literal
from pydantic import Field, model_validator
from .core import Model, Positive, NonNegative, Fraction, ensure, calculation


class PureFluidFlash(Model):
    fluid: str = Field(pattern=r'^[A-Za-z][A-Za-z0-9_-]{0,79}$')
    storage_pressure_pa_abs: Positive
    storage_temperature_k: Positive | None = None
    storage_vapor_mass_fraction: Fraction | None = None
    final_pressure_pa_abs: Positive
    method: Literal['isentropic','isenthalpic']
    qualification_basis: str = Field(min_length=1)

    @model_validator(mode='after')
    def storage_state_is_unambiguous(self):
        if (self.storage_temperature_k is None)==(self.storage_vapor_mass_fraction is None):
            raise ValueError('Provide exactly one storage temperature or equilibrium vapor mass fraction')
        return self


@calculation('properties/pure-fluid-flash','Qualified pure-fluid isentropic or isenthalpic flash',PureFluidFlash,
    ['Part3 §5.1.3,STEP1.3; PDF pp539-541'],origin='optional_coolprop_8_0_0_pure_fluid_flash',limitations=[
        'Optional CoolProp8.0.0 required. Pure-fluid HEOS expansion only; no mixtures,arbitrary backend strings,supercritical final pressure or equilibrium chemistry. Isentropic source preference and acceptable isenthalpic alternative explicitly selected. Returns final equilibrium vapor mass fraction,not incremental vaporized fraction or API581 rainout. Single-phase Q=-1 is not a physical quality: phase identifies0/1 vapor fraction. Storage uses exactly one of PT (unambiguous single phase) or pressure/equilibrium mass quality (triple-point to subcritical coexistence). Saturated PT ambiguities and invalid EOS states fail explicitly. Signed quality change includes condensation and is not rainout. Pure-propane reference verified; no independent fluid-wide/LH2 validation or hydraulic two-phase flow calculation. Final pressure supplied explicitly; atmospheric applicability owner-qualified.'])
def solve_pure_fluid_flash(inputs: PureFluidFlash) -> dict:
    """Internal backend for Part3 §5.1.3; requires optional CoolProp8.0.0."""
    ensure(bool(inputs.qualification_basis.strip()),'Fluid identity and EOS applicability qualification required')
    ensure(inputs.final_pressure_pa_abs < inputs.storage_pressure_pa_abs,'Flash expansion requires final pressure below storage')
    try:
        import CoolProp
        from CoolProp.CoolProp import PropsSI, PhaseSI, get_fluid_param_string
    except ImportError:
        ensure(False,'Pure-fluid flash requires optional CoolProp8.0.0','optional_engine_missing')
    ensure(CoolProp.__version__=='8.0.0','Flash backend requires tested CoolProp8.0.0','engine_version_mismatch')
    fluid=inputs.fluid
    try:
        ensure(get_fluid_param_string(fluid,'pure')=='true',
            'Pseudopure fluids and mixtures are outside pure-fluid flash scope','unsupported_flash_fluid')
        # No arbitrary backend strings or mixtures; fixed pure-fluid HEOS backend.
        critical=PropsSI('pcrit',fluid)
        ensure(inputs.final_pressure_pa_abs < critical,'Final pressure must be below critical pressure')
        key='Smass' if inputs.method=='isentropic' else 'Hmass'
        p=inputs.storage_pressure_pa_abs
        if inputs.storage_vapor_mass_fraction is not None:
            ensure(PropsSI('ptriple',fluid)<=p<critical,
                'Equilibrium storage quality requires triple-point to subcritical pressure','unsupported_storage_phase')
            storage_vapor_fraction=inputs.storage_vapor_mass_fraction
            coordinate,coordinate_value='Q',storage_vapor_fraction
            storage_phase=PhaseSI('P',p,coordinate,coordinate_value,fluid)
            ensure(storage_phase=='twophase','EOS did not return an equilibrium storage state','invalid_engine_result')
            t=PropsSI('T','P',p,coordinate,coordinate_value,fluid)
            state_basis='pressure_quality'
        else:
            t=inputs.storage_temperature_k
            coordinate,coordinate_value='T',t
            storage_phase=PhaseSI('P',p,coordinate,coordinate_value,fluid)
            if storage_phase in ('liquid','supercritical_liquid'):
                storage_vapor_fraction=0.
            elif storage_phase in ('gas','supercritical_gas'):
                storage_vapor_fraction=1.
            else:
                ensure(False,'Storage PT state must be unambiguous single-phase liquid or gas','unsupported_storage_phase')
            state_basis='pressure_temperature'
        value=PropsSI(key,'P',p,coordinate,coordinate_value,fluid)
        final=inputs.final_pressure_pa_abs
        temperature=PropsSI('T','P',final,key,value,fluid)
        phase=PhaseSI('P',final,key,value,fluid)
        quality=PropsSI('Q','P',final,key,value,fluid)
        if phase=='twophase':
            ensure(0<=quality<=1,'EOS returned invalid two-phase mass quality','invalid_engine_result')
            vapor_fraction=quality
        elif phase in ('liquid','supercritical_liquid'):
            vapor_fraction=0.
        elif phase in ('gas','supercritical_gas'):
            vapor_fraction=1.
        else:
            ensure(False,'Unsupported flashed phase: '+phase,'unsupported_flash_phase')
        density=PropsSI('Dmass','P',final,key,value,fluid)
        result=dict(flashed_temperature_k=temperature,vapor_mass_fraction=vapor_fraction,flashed_phase=phase,
            bulk_density_kg_m3=density,conserved_property=key,conserved_value_si=value,engine_version=CoolProp.__version__,
            storage_phase=storage_phase,storage_vapor_mass_fraction=storage_vapor_fraction,
            vapor_mass_fraction_change=vapor_fraction-storage_vapor_fraction,
            storage_temperature_k=t,storage_state_basis=state_basis)
        ensure(all(math.isfinite(result[k]) for k in ('flashed_temperature_k','vapor_mass_fraction','bulk_density_kg_m3','conserved_value_si','storage_temperature_k')),
            'Nonfinite EOS flash result','invalid_engine_result')
        ensure(temperature>0 and density>0 and t>0,'Nonpositive EOS temperature/density','invalid_engine_result')
        return result
    except ValueError as exc:
        from .core import DomainError
        if isinstance(exc,DomainError):
            raise
        ensure(False,'CoolProp could not solve supplied pure-fluid state','flash_solver_failure')


class PureLiquidFlashPartition(PureFluidFlash):
    adjusted_mass_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    equation_basis: Literal['api581_printed','post_flash_mass_balance']
    atmospheric_partition_basis: str = Field(min_length=1)


@calculation('release/pure-liquid-flash-partition','Pure-liquid flash with explicit pool/jet composition basis',PureLiquidFlashPartition,
    ['Part3 §§5.7.1-5.7.3 eqs(3.98)-(3.102); PDF p543'],
    origin='qualified_pure_liquid_flash_source_partition_composition',limitations=[
        'Optional CoolProp8.0.0; only unambiguous initially liquid pure fluid. Final pressure and atmospheric applicability must be qualified. Kletz rainout correlation is used, not experimentally validated for every fluid. Printed entrainment and conservation interpretation remain explicitly distinct; no silent erratum. Input mass/rate already detection/isolation/inventory adjusted. No hydraulic rate calculation, pool evaporation, mixtures or LH2 validation.'])
def pure_liquid_flash_partition(inputs: PureLiquidFlashPartition) -> dict:
    from .source_partition import Rainout, rainout, SourcePartition, source_partition
    ensure(bool(inputs.atmospheric_partition_basis.strip()),'Atmospheric partition applicability basis required')
    state=solve_pure_fluid_flash(PureFluidFlash(**inputs.model_dump(include=set(PureFluidFlash.model_fields))))
    ensure(state['storage_vapor_mass_fraction']==0.,
        'Liquid-flash partition requires initially liquid storage; gas condensation is a separate path','unsupported_partition_storage_phase')
    quality=state['vapor_mass_fraction']
    fraction=rainout(Rainout(flash_mass_fraction=quality))['rainout_mass_fraction']
    composition=(dict(stored_liquid_mass_fraction=1.,flash_mass_fraction=quality)
        if inputs.equation_basis=='api581_printed' else dict(post_flash_vapor_mass_fraction=quality))
    partition=source_partition(SourcePartition(adjusted_mass_rate_kg_s=inputs.adjusted_mass_rate_kg_s,
        released_mass_kg=inputs.released_mass_kg,rainout_mass_fraction=fraction,equation_basis=inputs.equation_basis,
        rainout_basis_source='API581 Kletz eqs(3.98)-(3.99); '+inputs.atmospheric_partition_basis,
        flash_property_source='CoolProp8.0.0 '+inputs.method+'; '+inputs.qualification_basis,**composition))
    return {**state,**partition,'rainout_mass_fraction':fraction}
