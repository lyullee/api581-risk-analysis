"""2016 Annex2.B section13 carbonic-acid corrosion equations and table."""
from bisect import bisect_left
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure, finite_tree
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

PSI_PA = 6894.757293168
_TEMPS = tuple(c+273.15 for c in range(20,151,10))
_PH = (3.5,4.,4.5,5.,5.5,6.,6.5)
_TPH = ((6,5.45,4.9,3.72,2.55,1.55,.72),(8.52,7.77,7.02,5.16,3.4,2.,.91),
    (10.98,10.06,9.13,6.49,4.08,2.3,1.02),(11.92,10.96,10.01,6.86,4.1,2.2,.94),
    (12.83,11.86,10.89,7.18,4.05,2.03,.84),(13.42,12.01,10.6,6.58,3.61,1.86,.87),
    (13.93,12.12,10.31,6.01,3.2,1.7,.9),(9.37,7.91,6.45,2.44,.82,.49,.32),
    (9.23,8.04,6.38,2.19,.94,.62,.42),(8.96,8.09,6.22,1.87,1.07,.77,.53),
    (8.55,8.06,5.98,1.48,1.2,.92,.65),(7.38,6.39,3.98,.96,.8,.63,.47),
    (6.26,4.91,2.31,.53,.46,.39,.32),(5.2,3.62,.98,.19,.19,.19,.19))


class CO2Humidity(Model):
    water_mass_fraction: Fraction = Field(lt=1)
    total_pressure_pa_abs: Positive
    water_saturation_pressure_pa_abs: Positive


@calculation("damage/co2-relative-humidity", "CO2-service source relative-humidity approximation", CO2Humidity,
    ["Part2 eq(2.B.24); PDF pp423-424"],limitations=[
        "x=water mass fraction/(1-water mass fraction); RH=x*P/Psat/(.622+x). Source uses air-based MW ratio.622 while discussing natural gas; preserve literal approximation, not an EOS or general natural-gas dew-point calculation. RH may exceed1, not clamped. Strictly greater than1 indicates source condensation condition; equality reported saturated, not automatically free liquid water."])
def humidity(x):
    ratio = x.water_mass_fraction/(1-x.water_mass_fraction)
    rh = ratio/(.622+ratio)*(x.total_pressure_pa_abs/x.water_saturation_pressure_pa_abs)
    finite_tree([ratio,rh])
    return {"water_dry_gas_mass_ratio":ratio,"relative_humidity_fraction":rh,"supersaturated":rh > 1,"saturated":rh == 1}


class CO2DewPoint(Model):
    water_mass_fraction: float = Field(gt=0,le=.3,strict=True,allow_inf_nan=False)
    total_pressure_pa_abs: Positive


@calculation("damage/co2-dew-point", "Approximate source dew point for water-containing gas", CO2DewPoint,
    ["Part2 eq(2.B.25),Table2.B.13.1; PDF pp424,427"],limitations=[
        "log10(Td_F)=2.0866+.2088*log10(water mass fraction)+.2242*log10(P_psia). Source water0..30wt%; zero has undefined logarithm and is rejected, not a fabricated dew point. ReturnsK; guidance should not be assumed accurate within±10F. No automatic dry-service screening from this approximate value."])
def dew_point(x):
    fahrenheit = 10**(2.0866+.2088*math.log10(x.water_mass_fraction)+.2242*math.log10(x.total_pressure_pa_abs/PSI_PA))
    return {"dew_point_temperature_k":(fahrenheit-32)*5/9+273.15}


class CO2TemperaturePH(Model):
    temperature_k: Positive
    ph: float = Field(ge=3.5,le=6.5,strict=True,allow_inf_nan=False)
    lookup_policy: Literal["exact_nodes_only","bilinear"]
    jump_policy: Literal["reject_cross_80_90","qualified_linear_across_jump"]
    jump_qualification_basis: str | None = None


def _bracket(nodes,value):
    value = next((v for v in nodes if math.isclose(v,value,rel_tol=0,abs_tol=1e-10)),value)
    ensure(nodes[0] <= value <= nodes[-1],"Outside temperature-pH table; no extrapolation")
    i = bisect_left(nodes,value)
    return (i,i,0.) if value == nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


@calculation("damage/co2-temperature-ph-factor", "CO2 corrosion temperature-pH table function", CO2TemperaturePH,
    ["Part2 Tables2.B.13.2/13.2M; PDF p428"],limitations=[
        "All98 cells,20..150C andpH3.5..6.5; exact or explicitly selected bilinear interpolation. Detailed source scope says temperatures above140C not considered: standalone table includes150C printed row, integrated model rejects>140C. Sharp80..90C change is not silently smoothed: interpolation across that interval requires explicit qualified policy/basis. No clamped/extrapolated pH or temperature; table function is not corrosion rate alone."])
def temperature_ph(x):
    qualified = x.jump_policy == "qualified_linear_across_jump"
    ensure((x.jump_qualification_basis is not None and bool(x.jump_qualification_basis.strip())) if qualified else x.jump_qualification_basis is None,"Jump policy and qualification basis must agree")
    a,b,wt = _bracket(_TEMPS,x.temperature_k)
    c,d,wp = _bracket(_PH,x.ph)
    ensure(x.lookup_policy == "bilinear" or (a == b and c == d),"Exact-node policy does not interpolate")
    crossing = a == 6 and b == 7
    ensure(not crossing or qualified,"Interpolation across sharp80-90C change requires qualified policy","co2_temperature_jump")
    low = _TPH[a][c]+wp*(_TPH[a][d]-_TPH[a][c])
    high = _TPH[b][c]+wp*(_TPH[b][d]-_TPH[b][c])
    return {"temperature_ph_factor":low+wt*(high-low),"sharp_temperature_interval_interpolated":crossing}


class CO2PHEstimate(Model):
    temperature_k: Positive
    co2_partial_pressure_pa_abs: Positive
    water_case: Literal["condensate","ferrous_saturated","salinity_46_g_l"]
    approximation_basis: str = Field(min_length=1)


@calculation("damage/co2-ph-estimate", "Carbonic-acid RBI pH approximation by water case", CO2PHEstimate,
    ["Part2 eqs(2.B.27)-(2.B.29); PDF p424"],limitations=[
        "Uses temperatureF and CO2 partial pressurepsi as printed; publicK/Pa converted first. Supplied known pH preferred. Owner qualifies simple water/Fe++/saline case, negligible bicarbonate buffering and salinity limitations. Source saline case says46g/L but following paragraph cautions>45g/L: no automatic resolution or general electrolyte equilibrium model. PositiveF required for logarithm; result not forced into lookup range."])
def ph_estimate(x):
    ensure(bool(x.approximation_basis.strip()),"pH approximation applicability basis required")
    f = (x.temperature_k-273.15)*9/5+32
    ensure(f > 0,"Printed pH approximation requires positive Fahrenheit logarithm argument")
    a,b,c = {"condensate":(2.8686,.7931,.57),"ferrous_saturated":(2.5907,.8668,.49),"salinity_46_g_l":(2.7137,.8002,.57)}[x.water_case]
    return {"estimated_ph":a+b*math.log10(f)-c*math.log10(x.co2_partial_pressure_pa_abs/PSI_PA)}


class CO2Fugacity(Model):
    temperature_k: Positive
    co2_partial_pressure_pa_abs: Positive
    temperature_denominator_basis: Literal["printed_celsius_plus_273","kelvin_exact"]


@calculation("damage/co2-fugacity", "CO2 fugacity and coefficient from partial pressure", CO2Fugacity,
    ["Part2 eqs(2.B.30)-(2.B.32); PDF p425"],limitations=[
        "Literal log10(f_bar)=log10(p_bar)+min(250,p_bar)*(.0031-1.4/(T_C+273)). PublicPa/K; explicit printed273 versus exactK denominator basis, no hidden273.15 repair. Primitive evaluates printed250bar exponent cap; integrated model separately limits partial pressure4MPa perTable13.1. Not a general-mixture EOS, total-pressure substitution or phase-equilibrium calculation."])
def fugacity(x):
    denominator = x.temperature_k-.15 if x.temperature_denominator_basis == "printed_celsius_plus_273" else x.temperature_k
    ensure(denominator > 0,"Printed fugacity temperature denominator must be positive")
    bar = x.co2_partial_pressure_pa_abs/1e5
    alpha = 10**(min(250.,bar)*(.0031-1.4/denominator))
    f = x.co2_partial_pressure_pa_abs*alpha
    ensure(math.isfinite(alpha) and math.isfinite(f) and alpha > 0 and f > 0,"Fugacity outside finite positive range","numerical_failure")
    return {"fugacity_pa":f,"fugacity_coefficient":alpha}


class CO2Reynolds(Model):
    diameter_m: Positive
    mixture_density_kg_m3: Positive
    mixture_velocity_m_s: NonNegative
    mixture_viscosity_pa_s: Positive


@calculation("damage/co2-reynolds", "Mixture Reynolds number for CO2 flow correlation", CO2Reynolds,
    ["Part2 eq(2.B.35); PDF p425"],limitations=["D*rho*velocity/viscosity, all SI. Mixture properties externally qualified; no two-phase holdup/viscosity/density or gas-in-oil solubility model inferred."])
def reynolds(x):
    value = x.diameter_m*x.mixture_density_kg_m3*x.mixture_velocity_m_s/x.mixture_viscosity_pa_s
    finite_tree(value)
    return {"reynolds_number":value}


class CO2Friction(Model):
    reynolds_number: Positive
    relative_roughness: Fraction


@calculation("damage/co2-friction-factor", "Source turbulent mixture friction factor", CO2Friction,
    ["Part2 eq(2.B.34); PDF p425"],limitations=[
        "f=.001375*[1+(20000*relative_roughness+1e6/Re)^.33]. Printed.33 exponent retained, not1/3. Valid only Re>2300; no laminar/transitional fallback or automatic Darcy/Fanning conversion."])
def friction(x):
    ensure(x.reynolds_number > 2300,"Source turbulent correlation requiresRe>2300")
    return {"friction_factor":.001375*(1+(20000*x.relative_roughness+1e6/x.reynolds_number)**.33)}


class CO2Shear(Model):
    friction_factor: Positive
    mixture_density_kg_m3: Positive
    mixture_velocity_m_s: NonNegative


@calculation("damage/co2-shear-stress", "CO2 mixture wall shear stress", CO2Shear,
    ["Part2 eq(2.B.33); PDF p425"],limitations=["RawS=f*rho*velocity^2/2; no hidden factor conversion. Separate corrosion base-rate API caps applied shear150Pa, preserves requested shear separately. Not CFD or two-phase property prediction."])
def shear(x):
    value = x.friction_factor*x.mixture_density_kg_m3*x.mixture_velocity_m_s**2/2
    finite_tree(value)
    return {"shear_stress_pa":value}


class CO2BaseRate(Model):
    temperature_ph_factor: Positive
    fugacity_pa: Positive
    shear_stress_pa: NonNegative


@calculation("damage/co2-base-rate", "CO2 carbonic-acid base corrosion equation", CO2BaseRate,
    ["Part2 eq(2.B.26),§13.3.6; PDF pp424-425"],limitations=[
        "CR_mm/y=f(T,pH)*f_bar^.62*(min(S,150)/19)^(.146+.0324*f_bar), literal exponent uses fugacity itself, not log(fugacity). PublicPa/m-year conversions explicit. Applied shear capped150Pa. Zero shear yields literal equation zero; this is not proof stagnant wet steel is safe or outside-mechanism corrosion absent. Positive numeric under/overflow rejected. No automatic applicability or pH-table screening in this primitive."])
def base_rate(x):
    applied = min(x.shear_stress_pa,150.)
    if applied == 0:
        rate = 0.
    else:
        f = x.fugacity_pa/1e5
        log_rate = math.log(x.temperature_ph_factor)+.62*math.log(f)+(.146+.0324*f)*math.log(applied/19)-math.log(1000)
        rate = math.exp(log_rate)
        ensure(rate > 0 and math.isfinite(rate),"CO2 rate outside finite positive range","numerical_failure")
    return {"base_corrosion_rate_m_year":rate,"applied_shear_stress_pa":applied,"shear_cap_applied":x.shear_stress_pa > 150}


class CO2Glycol(Model):
    composition_percent: float = Field(ge=0,le=100,strict=True,allow_inf_nan=False)
    composition_basis: Literal["equation_g_percent","table_water_weight_percent"]


@calculation("damage/co2-glycol-factor", "CO2 glycol reduction with explicit composition basis", CO2Glycol,
    ["Part2 eq(2.B.36),Table2.B.13.1; PDF pp426-427"],limitations=[
        "Equation definesG glycol percent while data table requests water weight percent of glycol/water mix. Explicit basis either uses literalG orG=100-water%; no inference of arbitrary glycol-to-water mass ratio. Factor=max(.008,((100-G)/100)^1.6), algebraically equivalent to printed base10 logs. G100 uses continuous limiting value with source.008 floor, not log0. Absent glycol isG0,factor1."])
def glycol(x):
    g = x.composition_percent if x.composition_basis == "equation_g_percent" else 100-x.composition_percent
    raw = ((100-g)/100)**1.6
    return {"glycol_factor":max(.008,raw),"glycol_floor_applied":raw < .008}


class CO2Reductions(Model):
    glycol: CO2Glycol | None = None
    inhibitor_factor: Fraction | None = None
    inhibitor_effectiveness_basis: str | None = None


class CO2Adjustment(CO2Reductions):
    base_corrosion_rate_m_year: NonNegative


@calculation("damage/co2-rate-adjustment", "Apply minimum of glycol and independently qualified inhibitor factors", CO2Adjustment,
    ["Part2 eq(2.B.23),§13.3.7; PDF pp423,426"],limitations=[
        "FinalCR=baseCR*min(Fglycol,Finhibitor), never product or additive credit. No glycol/inhibitor defaults factor1. Any supplied inhibitor factor requires independently determined effectiveness basis, including explicitly supplied1. Factor0 is retained if independently qualified; glycol.008 floor does not impose an invented floor on the inhibitor. This calculation does not validate real inhibitor deployment or uptime."])
def adjustment(x):
    supplied = x.inhibitor_factor is not None
    ensure((x.inhibitor_effectiveness_basis is not None and bool(x.inhibitor_effectiveness_basis.strip())) if supplied else x.inhibitor_effectiveness_basis is None,"Inhibitor factor requires matching independent-effectiveness basis")
    fg = glycol(x.glycol)["glycol_factor"] if x.glycol is not None else 1.
    fi = x.inhibitor_factor if supplied else 1.
    factor = min(fg,fi)
    rate = x.base_corrosion_rate_m_year*factor
    ensure(math.isfinite(rate) and (rate > 0 or x.base_corrosion_rate_m_year == 0 or factor == 0),"Adjusted CO2 rate outside numeric range","numerical_failure")
    return {"glycol_factor":fg,"inhibitor_factor":fi,"applied_reduction_factor":factor,"corrosion_rate_m_year":rate}


class SuppliedPH(Model):
    method: Literal["supplied"]
    ph: float = Field(ge=0,le=14,strict=True,allow_inf_nan=False)
    qualification_basis: str = Field(min_length=1)


class EstimatedPH(Model):
    method: Literal["condensate","ferrous_saturated","salinity_46_g_l"]
    qualification_basis: str = Field(min_length=1)


class SuppliedShear(Model):
    method: Literal["supplied"]
    shear_stress_pa: NonNegative
    qualification_basis: str = Field(min_length=1)


class TurbulentShear(CO2Reynolds):
    method: Literal["turbulent_flow"]
    relative_roughness: Fraction
    qualification_basis: str = Field(min_length=1)


class CO2WetModel(CO2Reductions):
    ph: SuppliedPH | EstimatedPH = Field(discriminator="method")
    flow: SuppliedShear | TurbulentShear = Field(discriminator="method")
    lookup_policy: Literal["exact_nodes_only","bilinear"]
    jump_policy: Literal["reject_cross_80_90","qualified_linear_across_jump"]
    jump_qualification_basis: str | None = None
    temperature_denominator_basis: Literal["printed_celsius_plus_273","kelvin_exact"]
    simple_upstream_mixture_and_wetting_basis: str = Field(min_length=1)


class CO2Assessment(Model):
    material: Literal["carbon_steel","low_alloy_steel"]
    temperature_k: Positive
    co2_partial_pressure_pa_abs: NonNegative
    free_liquid_water_present: bool
    applicability_basis: str = Field(min_length=1)
    wet_model: CO2WetModel | None = None


@calculation("damage/co2-corrosion-assessment", "Qualified free-water CO2 corrosion from pH fugacity flow and reductions", CO2Assessment,
    ["Part2 Annex2.B §13,eqs(2.B.23)-(2.B.36),Table2.B.13.1; PDF pp423-429"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Carbon/low-alloy steel only, integrated wet model20..140C and CO2 partial pressure<=4MPa; table150C remains standalone only. No free liquid water or CO2 gives CO2-specific rate0, not zero total corrosion/damage. Free-water and upstream simple crude/water/natural-gas wetting applicability are externally qualified; oil-water<20%/velocity>1m/s figure screen and approximate dew point are not automatically used to assert dry metal. pH and shear supplied or estimated with explicit bases; no two-phase EOS, buffering/salinity chemistry, inhibition efficacy or material immunity inferred. Positive wet case uses same pressure/temperature through all primitives; table interpolation and273 denominator explicit. Standalone RH/dew-point approximations do not substitute for free-water evidence."])
def assessment(x):
    ensure(bool(x.applicability_basis.strip()),"Free-water/material/CO2 applicability basis must not be blank")
    if not x.free_liquid_water_present or x.co2_partial_pressure_pa_abs == 0:
        ensure(x.wet_model is None,"Dry/no-CO2 branch cannot carry unused wet-model inputs")
        return {"calculation_branch":"no_free_water" if not x.free_liquid_water_present else "no_co2","corrosion_rate_m_year":0.,
            "base_corrosion_rate_m_year":0.,"model_ph":None,"temperature_ph_factor":None,"fugacity_pa":None,
            "requested_shear_stress_pa":None,"applied_shear_stress_pa":None,"shear_cap_applied":False,
            "glycol_factor":1.,"inhibitor_factor":1.,"applied_reduction_factor":1.,"sharp_temperature_interval_interpolated":False}
    ensure(293.15 <= x.temperature_k <= 413.15,"Integrated CO2 scope20..140C")
    ensure(x.co2_partial_pressure_pa_abs <= 4e6,"Integrated CO2 partial pressure exceeds4MPa")
    m = x.wet_model
    ensure(m is not None,"Positive wet CO2 case requires wet-model inputs")
    ensure(all(s.strip() for s in (m.ph.qualification_basis,m.flow.qualification_basis,m.simple_upstream_mixture_and_wetting_basis)),"pH/flow/upstream-mixture qualification bases must not be blank")
    ph = m.ph.ph if m.ph.method == "supplied" else ph_estimate(CO2PHEstimate(temperature_k=x.temperature_k,co2_partial_pressure_pa_abs=x.co2_partial_pressure_pa_abs,
        water_case=m.ph.method,approximation_basis=m.ph.qualification_basis))["estimated_ph"]
    table = temperature_ph(CO2TemperaturePH(temperature_k=x.temperature_k,ph=ph,lookup_policy=m.lookup_policy,jump_policy=m.jump_policy,jump_qualification_basis=m.jump_qualification_basis))
    fug = fugacity(CO2Fugacity(temperature_k=x.temperature_k,co2_partial_pressure_pa_abs=x.co2_partial_pressure_pa_abs,temperature_denominator_basis=m.temperature_denominator_basis))
    if m.flow.method == "supplied":
        stress = m.flow.shear_stress_pa
    else:
        re = reynolds(m.flow)["reynolds_number"]
        f = friction(CO2Friction(reynolds_number=re,relative_roughness=m.flow.relative_roughness))["friction_factor"]
        stress = shear(CO2Shear(friction_factor=f,mixture_density_kg_m3=m.flow.mixture_density_kg_m3,mixture_velocity_m_s=m.flow.mixture_velocity_m_s))["shear_stress_pa"]
    base = base_rate(CO2BaseRate(temperature_ph_factor=table["temperature_ph_factor"],fugacity_pa=fug["fugacity_pa"],shear_stress_pa=stress))
    reduced = adjustment(CO2Adjustment(base_corrosion_rate_m_year=base["base_corrosion_rate_m_year"],glycol=m.glycol,inhibitor_factor=m.inhibitor_factor,
        inhibitor_effectiveness_basis=m.inhibitor_effectiveness_basis))
    return {**base,**reduced,**table,"calculation_branch":"wet_carbonic_acid_model","model_ph":ph,"fugacity_pa":fug["fugacity_pa"],"requested_shear_stress_pa":stress}


class CO2Thinning(Model):
    corrosion: CO2Assessment
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/co2-thinning-assessment", "CO2 corrosion through qualified non-AST unclad thinning DF", CO2Thinning,
    ["Part2 Annex2.B §13; Part2 §4.5.7"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same CO2 rate drives constant-baseline unclad non-AST wall loss and either strength method. Owner qualifies localized/general inspection coverage, free-water/material/mixture scope and conditions. Zero CO2 rate does not force DF0: baseline strength, uncertainty and.1 thinning floor remain. No AST, cladding, total all-mechanism DF, FFS or automatic moisture/material/wetting/inhibitor qualification."])
def co2_thinning(x):
    rate = assessment(x.corrosion)
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=rate["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**rate,**result}
