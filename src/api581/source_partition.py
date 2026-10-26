"""Level2 pressure-phase screening and explicit rainout/aerosol source bases."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .release import Orifice, orifice, Gas, gas, Liquid, liquid

Phase = Literal["vapor","liquid","two_phase"]
Basis = Literal["api581_printed","post_flash_mass_balance"]


class PhaseScreen(Model):
    storage_pressure_pa_abs: Positive
    saturation_pressure_at_storage_pa_abs: Positive
    ambient_pressure_pa_abs: Positive = 101325


@calculation("release/level2-release-phase", "Pressure-based Level2 release-phase screening", PhaseScreen,
             ["Part3 eqs(3.95)-(3.97); PDF p541"],
             limitations=["Release phase at opening differs from storage phase and final atmospheric flashed phase. Source inequalities overlap at Psat=Ps and omit equality at Psat=Patm; these boundaries return no selected phase. Ps=Patm returns no_driving_pressure. Saturation pressure is caller-qualified; no supercritical EOS inference."])
def phase_screen(x):
    ps,pv,pa=x.storage_pressure_pa_abs,x.saturation_pressure_at_storage_pa_abs,x.ambient_pressure_pa_abs
    ensure(ps >= pa,"Storage pressure must be at least ambient pressure")
    if ps == pa:
        return {"release_phase":None,"status":"no_driving_pressure"}
    if pv == ps:
        return {"release_phase":None,"status":"saturation_storage_boundary"}
    if pv == pa:
        return {"release_phase":None,"status":"saturation_ambient_boundary"}
    return {"release_phase":"vapor" if pv > ps else "two_phase" if pv > pa else "liquid","status":"classified"}


class Level2Orifice(PhaseScreen):
    diameter_m: NonNegative
    gas_temperature_k: Positive | None = None
    gas_molecular_weight_kg_kmol: Positive | None = None
    gas_heat_capacity_ratio: Positive | None = None
    liquid_density_kg_m3: Positive | None = None
    gas_discharge_coefficient: Fraction = .9
    liquid_discharge_coefficient: Fraction = .61
    liquid_viscosity_factor: Positive = 1
    qualified_boundary_phase: Phase | None = None
    boundary_phase_source: str | None = Field(default=None,min_length=1,max_length=1000)


@calculation("release/level2-orifice-rate", "Level2 phase-selected gas/liquid/conservative two-phase source rate", Level2Orifice,
             ["Part3 §§5.3.3-5.3.6 eqs(3.95)-(3.97); PDF pp541-542; §4.3 eqs(3.3),(3.6)-(3.7)"],
             origin="api581_phase_selected_orifice_composition",
             limitations=["Two-phase branch uses source-permitted conservative LIQUID approximation, not HEM/Omega or a flashing two-phase flow solver. Vapor uses ideal gas constant upstream model. Boundary phase override requires a nonblank owner basis and cannot contradict a classified phase. No-driving-pressure returns zero without inventing phase. Caller qualifies saturation pressure and properties; no thermodynamic or LH2 validation."])
def level2_orifice(x):
    selected=phase_screen(PhaseScreen(**x.model_dump(include=set(PhaseScreen.model_fields))))
    phase=selected["release_phase"]
    ensure((x.qualified_boundary_phase is None) == (x.boundary_phase_source is None),"Boundary phase and source must be supplied together")
    if x.boundary_phase_source is not None:
        ensure(bool(x.boundary_phase_source.strip()),"Boundary phase source must be nonblank")
    if selected["status"] == "no_driving_pressure":
        ensure(x.qualified_boundary_phase is None,"No phase override for zero driving pressure")
        return {"mass_rate_kg_s":0,"area_m2":orifice(Orifice(diameter_m=x.diameter_m))["area_m2"],
                "release_phase":None,"rate_method":"no_driving_pressure","phase_basis":"pressure_screen"}
    if phase is None:
        ensure(x.qualified_boundary_phase is not None,"Source pressure boundary requires qualified phase selection","phase_boundary_requires_qualification")
        phase=x.qualified_boundary_phase
    else:
        ensure(x.qualified_boundary_phase is None or x.qualified_boundary_phase == phase,"Boundary override contradicts classified phase")
    if phase == "vapor":
        ensure(all(v is not None for v in (x.gas_temperature_k,x.gas_molecular_weight_kg_kmol,x.gas_heat_capacity_ratio)),
               "Vapor phase requires gas temperature, molecular weight and heat capacity ratio")
        ensure(x.gas_heat_capacity_ratio > 1,"Gas heat capacity ratio must exceed1")
        result=gas(Gas(diameter_m=x.diameter_m,upstream_pressure_pa_abs=x.storage_pressure_pa_abs,
            downstream_pressure_pa_abs=x.ambient_pressure_pa_abs,temperature_k=x.gas_temperature_k,
            molecular_weight_kg_kmol=x.gas_molecular_weight_kg_kmol,heat_capacity_ratio=x.gas_heat_capacity_ratio,
            discharge_coefficient=x.gas_discharge_coefficient))
        method="ideal_gas"
    else:
        ensure(x.liquid_density_kg_m3 is not None,"Liquid or conservative two-phase source requires liquid density")
        result=liquid(Liquid(diameter_m=x.diameter_m,upstream_pressure_pa_abs=x.storage_pressure_pa_abs,
            downstream_pressure_pa_abs=x.ambient_pressure_pa_abs,density_kg_m3=x.liquid_density_kg_m3,
            discharge_coefficient=x.liquid_discharge_coefficient,viscosity_factor=x.liquid_viscosity_factor))
        method="liquid" if phase == "liquid" else "liquid_conservative_two_phase"
    return {"mass_rate_kg_s":result["mass_rate_kg_s"],"area_m2":result["area_m2"],"release_phase":phase,"rate_method":method,
            "phase_basis":"qualified_boundary" if selected["release_phase"] is None else "pressure_screen"}


class Rainout(Model):
    flash_mass_fraction: Fraction


@calculation("release/kletz-rainout-fraction", "Kletz rainout mass-fraction correlation", Rainout,
             ["Part3 eqs(3.98)-(3.99); PDF p543"],
             limitations=["Rainout=max(0,1-2*flash_fraction). Flash fraction must be supplied by qualified isentropic/isenthalpic atmospheric flash calculation. This correlation does not calculate flash state or verify entrainment composition; no LH2 validation."])
def rainout(x):
    return {"rainout_mass_fraction":max(0,1-2*x.flash_mass_fraction)}


class RateSplit(Model):
    adjusted_mass_rate_kg_s: NonNegative
    rainout_mass_fraction: Fraction


@calculation("release/rainout-rate-split", "Rainout pool and aerosol-containing jet rates", RateSplit,
             ["Part3 eqs(3.100)-(3.101); PDF p543"],
             limitations=["Pool=adjusted rate*rainout; jet=adjusted rate*(1-rainout). Jet may contain liquid aerosol and must not be labeled pure vapor. Rainout correlation/flash composition supplied separately; no pool evaporation in this split."])
def rate_split(x):
    return {"pool_liquid_rate_kg_s":x.adjusted_mass_rate_kg_s*x.rainout_mass_fraction,
            "jet_total_rate_kg_s":x.adjusted_mass_rate_kg_s*(1-x.rainout_mass_fraction)}


class Entrainment(Model):
    rainout_mass_fraction: Fraction
    equation_basis: Basis
    stored_liquid_mass_fraction: Fraction | None = None
    flash_mass_fraction: Fraction | None = None
    post_flash_vapor_mass_fraction: Fraction | None = None


@calculation("release/jet-liquid-entrainment", "Printed or post-flash-mass-balance aerosol fraction", Entrainment,
             ["Part3 eq(3.102); PDF p543; phase-fraction nomenclature PDF575-576"],
             origin="api581_with_explicit_entrainment_basis",
             limitations=["api581_printed uses stored_liquid_fraction*flash_fraction/(1-rainout), exactly the printed product. Reports physical_range but does not prove EOS consistency. post_flash_mass_balance uses supplied total post-flash vapor fraction and remaining liquid after rainout, a separately labeled conservation interpretation, not an authorized erratum. Exactly the selected basis fields required. No jet at rainout1 has no defined composition; returns None, not division by zero."])
def entrainment(x):
    printed=x.equation_basis == "api581_printed"
    ensure((printed and x.stored_liquid_mass_fraction is not None and x.flash_mass_fraction is not None and x.post_flash_vapor_mass_fraction is None)
           or (not printed and x.stored_liquid_mass_fraction is None and x.flash_mass_fraction is None and x.post_flash_vapor_mass_fraction is not None),
           "Provide exactly the parameters for selected entrainment basis")
    jet_fraction=1-x.rainout_mass_fraction
    if not printed:
        ensure(math.fsum([x.post_flash_vapor_mass_fraction,x.rainout_mass_fraction]) <= 1,
               "Post-flash vapor plus rainout exceeds total mass")
    if jet_fraction == 0:
        ensure(printed or x.post_flash_vapor_mass_fraction == 0,"No-jet rainout cannot coexist with positive post-flash vapor")
        return {"entrained_liquid_mass_fraction":None,"jet_vapor_mass_fraction":None,"physical_range":True,
                "jet_fraction_nonzero":False,"equation_basis":x.equation_basis}
    if printed:
        fraction=x.stored_liquid_mass_fraction*x.flash_mass_fraction/jet_fraction
        physical=0 <= fraction <= 1
        vapor=1-fraction if physical else None
    else:
        # min removes only <=1ulp ratio overshoot at a rounded exact mass boundary.
        vapor=min(1,x.post_flash_vapor_mass_fraction/jet_fraction)
        fraction=1-vapor
        physical=True
    return {"entrained_liquid_mass_fraction":fraction,"jet_vapor_mass_fraction":vapor,"physical_range":physical,
            "jet_fraction_nonzero":True,"equation_basis":x.equation_basis}


class SourcePartition(Entrainment):
    adjusted_mass_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    rainout_basis_source: str = Field(min_length=1,max_length=1000)
    flash_property_source: str = Field(min_length=1,max_length=1000)


@calculation("release/level2-source-partition", "Pool/jet/vapor/aerosol mass and rate partition", SourcePartition,
             ["Part3 eqs(3.100)-(3.102), STEP7.3-7.6; PDF pp543,545"],
             origin="api581_source_partition_with_explicit_entrainment_basis",
             limitations=["Adjusted total rate and released mass must be qualified after detection/isolation and inventory limits. Pool+jet and jet-vapor+jet-liquid conserve mass. Printed composition is explicit and not asserted as EOS closure; nonphysical printed fractions rejected. Rainout and flash properties supplied with source; no pool evaporation, flash/EOS, two-phase hydraulic solver or actual dispersion run."])
def source_partition(x):
    ensure(x.rainout_basis_source.strip() and x.flash_property_source.strip(),"Rainout and flash-property sources must be nonblank")
    composition=entrainment(Entrainment(**x.model_dump(include=set(Entrainment.model_fields))))
    ensure(composition["physical_range"],"Printed entrained-liquid fraction outside0..1 cannot define physical source","invalid_entrainment_fraction")
    rates=rate_split(RateSplit(adjusted_mass_rate_kg_s=x.adjusted_mass_rate_kg_s,rainout_mass_fraction=x.rainout_mass_fraction))
    pool_mass=x.released_mass_kg*x.rainout_mass_fraction
    jet_mass=x.released_mass_kg*(1-x.rainout_mass_fraction)
    liquid_fraction=composition["entrained_liquid_mass_fraction"] or 0
    vapor_fraction=composition["jet_vapor_mass_fraction"] or 0
    return {**composition,**rates,"pool_liquid_mass_kg":pool_mass,"jet_total_mass_kg":jet_mass,
            "jet_liquid_rate_kg_s":rates["jet_total_rate_kg_s"]*liquid_fraction,
            "jet_vapor_rate_kg_s":rates["jet_total_rate_kg_s"]*vapor_fraction,
            "jet_liquid_mass_kg":jet_mass*liquid_fraction,"jet_vapor_mass_kg":jet_mass*vapor_fraction}
