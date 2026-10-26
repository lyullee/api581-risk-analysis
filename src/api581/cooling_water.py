"""2016 Annex2.B section11 cooling-water corrosion, with explicit source policies."""
from bisect import bisect_left
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure, finite_tree
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Lookup = Literal["exact_rows_only","linear_between_rows","maximum_bracketing_value"]
Units = Literal["printed_si","printed_us_converted"]
_C2C = (1,4,8,12,16,19,24,29,34,41,47,53,60,68,77)
_C2F = (33,39,46,53,60,67,76,85,94,105,117,128,140,154,170)
_C2 = tuple(2.6-i*.1 for i in range(15))
_CA = (10.5,12.5,15.5,25,39,49.5,62.5,78.5,99,124.5,156.5,197.5,250,310,390,495,625,785,940)
_C3 = (.6,.7,.8,1.,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.,2.1,2.2,2.3,2.4,2.5,2.6)
_MOA = (10.5,12.5,15.5,25,40,50,62.5,79,99.5,125,158,197.5,250,315,400,500,625,790,945)
_C4 = (10.5,12.5,1.2,1.4,1.6,1.7,1.8,1.9,2.,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2.9,3.)
_CL = (5,10,50,100,250,500,750,1000,2000,3000,5000,10000)
_BASE_US = ((1,2,4,6,9,13,15,17,17,16,15,13),(.3,.6,1.4,2,3,4.3,5,5.7,5.6,5.4,4.9,4.3))
_BASE_SI = ((.03,.05,.1,.15,.23,.33,.38,.43,.43,.41,.38,.33),(.01,.02,.04,.05,.08,.11,.13,.14,.14,.14,.12,.11))
_FTC = (24,27,29,32,35,38,41,43,46,49,52,54,57,60,63,66,68,71,74,77,79,82,85,88,91,93,99)
_FTF = tuple(range(75,205,5))+(210,)
_CLOSED = (.1,.3,.4,.6,.8,.9,1.1,1.2,1.4,1.6,1.7,1.9,2.1,2.2,2.4,2.5,2.7,2.9,3.,3.2,3.4,3.5,3.7,3.8,4.,4.2,4.5)
_OPEN = _CLOSED[:20]+(3.3,3.3,3.3,3.3,3.1,2.9,1.7)


class CoolingRateFactors(Model):
    """Qualified qualitative factors described in Annex 2.B §11.1.6."""
    process_temperature_k: Positive
    impurities_in_makeup_water: bool = False
    deposits_present: bool = False
    corrosion_products_present: bool = False
    biomass_present: bool = False
    hydrocarbon_process_leak: bool = False
    low_flow_or_stagnant_area: bool = False


@calculation("damage/cooling-water-rate-factors", "Cooling-water qualitative corrosion-rate factor flags", CoolingRateFactors,
    ["Part2 Annex2.B §11.1.6; PDF pp398-399"], limitations=[
        "Qualitative screening only: the source describes impurities, scale, deposits, biomass and low-flow effects but supplies no universal multipliers. Scale potential is flagged when process temperature exceeds60C. No flag is converted into a corrosion rate, damage factor or treatment credit; owner qualification remains required."])
def rate_factors(x):
    scale = x.process_temperature_k > 333.15
    deposit = x.deposits_present or x.corrosion_products_present or x.biomass_present
    flags = []
    if x.impurities_in_makeup_water:
        flags.append("makeup_impurities")
    if scale:
        flags.append("scale_potential_above_60C")
    if x.deposits_present:
        flags.append("mud_silt_or_other_deposit")
    if x.corrosion_products_present:
        flags.append("corrosion_products_deposit")
    if x.biomass_present:
        flags.append("biomass_or_mic_environment")
    if x.hydrocarbon_process_leak:
        flags.append("hydrocarbon_leak_biomass_acceleration")
    if x.low_flow_or_stagnant_area:
        flags.append("low_flow_or_stagnant_area")
    return {"scale_potential": scale, "deposit_risk": deposit,
        "biological_or_mic_risk": x.biomass_present or x.hydrocarbon_process_leak,
        "underdeposit_risk": deposit or x.low_flow_or_stagnant_area,
        "factor_flags": flags}


def _lookup(nodes,values,value,policy,holes=()):
    value = next((n for n in nodes if math.isclose(n,value,rel_tol=0,abs_tol=1e-9)),value)
    ensure(nodes[0] <= value <= nodes[-1],"Argument outside source table; no extrapolation","cooling_table_range")
    i = bisect_left(nodes,value)
    if nodes[i] == value:
        return float(values[i])
    ensure(policy != "exact_rows_only","Argument between source rows; numerical policy required","cooling_between_rows")
    a,b = nodes[i-1],nodes[i]
    ensure(not any(a < h < b for h in holes),"Interpolation crosses missing or unresolved source row","ambiguous_source")
    return max(values[i-1],values[i]) if policy == "maximum_bracketing_value" else values[i-1]+(value-a)/(b-a)*(values[i]-values[i-1])


class CoolingCoefficients(Model):
    total_dissolved_solids_mg_l: NonNegative
    water_temperature_k: Positive
    temperature_basis: Units
    calcium_hardness_mg_caco3_l: Positive
    methyl_orange_alkalinity_mg_caco3_l: Positive
    lookup_policy: Lookup
    c4_source_policy: Literal["reject_ambiguous_cells","qualified_printed_literal"]
    c4_literal_basis: str | None = None


@calculation("damage/cooling-water-ph-coefficients", "Cooling water saturation-pH coefficient table", CoolingCoefficients,
    ["Part2 Table2.B.11.3; PDF p408"],limitations=[
        "C1 TDS50..400=.1,>400..1000=.2. C2 uses explicit printed C/F temperature grid; pairs rounded inconsistently. C3/C4 rows20/31 have no printed factors: exact use or interpolation crossing those rows rejected. C4 first two factors print10.5/12.5, unlike following1.2..3: reject those cells/adjacent interpolation unless qualified printed-literal policy and basis chosen. No inferred1.0/1.1 repair. Interpolation/maximum bracketing is explicit numerical policy, not a source mandate."])
def coefficients(x):
    ensure(50 <= x.total_dissolved_solids_mg_l <= 1000,"TDS outside50..1000mg/L coefficient table")
    literal = x.c4_source_policy == "qualified_printed_literal"
    ensure((x.c4_literal_basis is not None and bool(x.c4_literal_basis.strip())) if literal else x.c4_literal_basis is None,"C4 literal policy requires matching qualification basis")
    c = x.water_temperature_k-273.15
    temp,grid = (c,_C2C) if x.temperature_basis == "printed_si" else (c*9/5+32,_C2F)
    # Missing printed20/31 nodes cannot be bypassed through a smooth interpolation.
    ca,moa = x.calcium_hardness_mg_caco3_l,x.methyl_orange_alkalinity_mg_caco3_l
    ensure(ca not in (20,31) and moa not in (20,31),"Missing C3/C4 source coefficient","ambiguous_source")
    ensure(literal or moa >= 15.5,"Ambiguous first C4 cells require qualified printed-literal policy","ambiguous_source")
    return {"c1":.1 if x.total_dissolved_solids_mg_l <= 400 else .2,
        "c2":_lookup(grid,_C2,temp,x.lookup_policy),"c3":_lookup(_CA,_C3,ca,x.lookup_policy,(20,31)),
        "c4":_lookup(_MOA,_C4,moa,x.lookup_policy,(20,31)),"c4_printed_literal_used":literal and moa < 15.5}


class CoolingIndices(Model):
    actual_ph: NonNegative = Field(le=14)
    saturation_ph: NonNegative = Field(le=14)


@calculation("damage/cooling-water-stability-indices", "Langelier and Ryznar cooling-water indices", CoolingIndices,
    ["Part2 eqs(2.B.9)-(2.B.10); PDF p402"],limitations=[
        "LSI=pHa-pHs; RSI=2*pHs-pHa. Index alone is not quantitative corrosion rate or water-treatment effectiveness. Main cooling model assumes pH6.5..9.5; this independent index arithmetic does not screen that applicability."])
def indices(x):
    return {"langelier_saturation_index":x.actual_ph-x.saturation_ph,"ryznar_stability_index":2*x.saturation_ph-x.actual_ph}


class CoolingSaturationPH(Model):
    c1: NonNegative
    c2: NonNegative
    c3: NonNegative
    c4: NonNegative


@calculation("damage/cooling-water-saturation-ph", "Cooling water saturation pH from four coefficients", CoolingSaturationPH,
    ["Part2 eq(2.B.11); PDF p403"],limitations=[
        "pHs=(9.3+C1+C2)-(C3+C4). Coefficients supplied or obtained from separate table API. Signed raw pHs retained diagnostically; no clamp of anomalous literal C4 results into a physical range. Main freshwater model requires qualified pHs0..14."])
def saturation_ph(x):
    value = 9.3+x.c1+x.c2-x.c3-x.c4
    finite_tree(value)
    return {"saturation_ph":value}


class CoolingBase(Model):
    chloride_ppm: NonNegative
    ryznar_stability_index: NonNegative
    velocity_m_s: NonNegative
    condition_interpretation: Literal["body_rsi6_velocity2_44","us_header_rsi6_velocity8ft"]
    rate_unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/cooling-water-base-rate", "Cooling water chloride and scaling base corrosion rate", CoolingBase,
    ["Part2 §11.3.1.2,Tables2.B.11.4/11.4M; PDF pp402-403,409"],limitations=[
        "SI table both headers repeat RSI<=1.8 and velocity<=2.4; unusable for automatic column choice. Explicit interpretation follows detailed-body RSI6/2.44m/s or US header RSI6/8ft/s; no official SI erratum asserted. High column if RSI>6 OR velocity>threshold, otherwise scaling low column. Printed SI rates and exact US-mpy conversion differ. Chloride5..10000ppm only, explicit interpolation policy; maximum bracketing stays conservative on declining high-chloride rows. Not automatic seawater/freshwater classification."])
def base_rate(x):
    threshold = 2.44 if x.condition_interpretation == "body_rsi6_velocity2_44" else 8*.3048
    col = 0 if x.ryznar_stability_index > 6 or x.velocity_m_s > threshold else 1
    native = _lookup(_CL,(_BASE_SI if x.rate_unit_basis == "printed_si" else _BASE_US)[col],x.chloride_ppm,x.lookup_policy)
    return {"base_corrosion_rate_m_year":native*(.001 if x.rate_unit_basis == "printed_si" else .0000254),
        "base_column":"unprotected_high" if col == 0 else "scaling_low","base_velocity_threshold_m_s":threshold}


class CoolingTemperature(Model):
    metal_temperature_k: Positive
    system: Literal["open","closed"]
    temperature_basis: Units
    argument_policy: Literal["table_operating_temperature","text_delta_from_reference"]
    duplicate_row_policy: Literal["reject_unresolved_row","qualified_ignore_misordered_row"]
    duplicate_row_basis: str | None = None
    lookup_policy: Lookup


@calculation("damage/cooling-water-temperature-factor", "Cooling water open or closed system temperature factor", CoolingTemperature,
    ["Part2 eq(2.B.12),Table2.B.11.5; PDF pp403,410"],limitations=[
        "Text says use deltaT from24C/75F, table labels operating temperature. Explicit argument policy selects interpretation. Source penultimate row repeats41C/105F with factors4.3/2.5 after93C/200F; no invented96C/205F fix. Default rejects repeated node/adjacent interpolation and upper gap crossing misordered row. Qualified ignore policy omits row explicitly, with owner basis; remaining printed rows interpolate by selected policy. No table-range extrapolation; temperature basis is rounded SI or converted US grid."])
def temperature_factor(x):
    ignore = x.duplicate_row_policy == "qualified_ignore_misordered_row"
    ensure((x.duplicate_row_basis is not None and bool(x.duplicate_row_basis.strip())) if ignore else x.duplicate_row_basis is None,"Ignoring misordered temperature row requires qualification basis")
    c = x.metal_temperature_k-273.15
    value,grid,duplicate = (c,_FTC,41.) if x.temperature_basis == "printed_si" else (c*9/5+32,_FTF,105.)
    if x.argument_policy == "text_delta_from_reference":
        value -= 24. if x.temperature_basis == "printed_si" else 75.
    if not ignore:
        i = bisect_left(grid,value)
        if i < len(grid) and grid[i] == value:
            ensure(value != duplicate,"Conflicting repeated temperature source row","ambiguous_source")
        elif 0 < i < len(grid):
            ensure(duplicate not in (grid[i-1],grid[i]) and i != len(grid)-1,"Temperature interpolation touches unresolved row","ambiguous_source")
    factor = _lookup(grid,_OPEN if x.system == "open" else _CLOSED,value,x.lookup_policy)
    return {"temperature_factor":factor,"temperature_table_argument":value,"misordered_row_ignored":ignore}


class CoolingVelocity(Model):
    velocity_m_s: NonNegative
    equation_basis: Units


@calculation("damage/cooling-water-velocity-factor", "Cooling water velocity adjustment equation", CoolingVelocity,
    ["Part2 eqs(2.B.13)-(2.B.18),Table2.B.11.6; PDF pp403-404,411"],limitations=[
        "Printed SI uses boundaries.914/2.44m/s and slopes1.64/.82; US3/8ft/s and slopes.50/.25. Explicit basis preserves rounding difference. Public velocitym/s, qualified source application up to6.1m/s(20ft/s rounded), no extrapolation beyond. Equation evaluated directly, not interpolated rounded table values."])
def velocity_factor(x):
    ensure(x.velocity_m_s <= 6.1,"Velocity beyond stated cooling-system assumption6.1m/s")
    v,lo,hi,a,b = (x.velocity_m_s,.914,2.44,1.64,.82) if x.equation_basis == "printed_si" else (x.velocity_m_s/.3048,3.,8.,.5,.25)
    return {"velocity_factor":1+a*(lo-v) if v < lo else 1+b*(v-hi) if v > hi else 1.}


class CoolingRateEquation(Model):
    base_corrosion_rate_m_year: NonNegative
    temperature_factor: Positive
    velocity_factor: Positive


@calculation("damage/cooling-water-rate-equation", "Cooling water base rate with temperature and velocity factors", CoolingRateEquation,
    ["Part2 eq(2.B.8); PDF p402"],limitations=["Constant qualified carbon-steel cooling-water factors only; this equation does not screen treatment, MIC, deposits or material applicability."])
def rate_equation(x):
    rate = x.base_corrosion_rate_m_year*x.temperature_factor*x.velocity_factor
    ensure(math.isfinite(rate) and (rate > 0 or x.base_corrosion_rate_m_year == 0),"Corrosion product outside numeric range","numerical_failure")
    return {"corrosion_rate_m_year":rate}


class CoolingSeawater(Model):
    material: Literal["carbon_steel"]
    velocity_m_s: NonNegative
    equation_basis: Units
    applicability_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-seawater-rate", "Once-through seawater carbon-steel corrosion correlation", CoolingSeawater,
    ["Part2 §11.3.2.3,eqs(2.B.19)-(2.B.20); PDF p405"],limitations=[
        "Correlation reference about21C and dissolved oxygen6-8ppm; owner qualifies seawater, untreated carbon steel, oxygen/temperature and absence of deposit/MIC exceptions. Public velocitym/s, limit6.1m/s source cooling assumption; erosion-corrosion above about12.2m/s is outside. SI polynomialmm/y and US polynomialmpy are separately rounded and selectable. No temperature/oxygen/treatment correction invented."])
def seawater_rate(x):
    ensure(bool(x.applicability_basis.strip()),"Seawater applicability basis must not be blank")
    ensure(x.velocity_m_s <= 6.1,"Seawater velocity exceeds stated cooling-system assumption")
    v = x.velocity_m_s if x.equation_basis == "printed_si" else x.velocity_m_s/.3048
    native = .1318+.3108*v-.0579*v*v+.01208*v**2.5 if x.equation_basis == "printed_si" else 5.1885+3.7293*v-.21181*v*v+.02439*v**2.5
    return {"corrosion_rate_m_year":native*(.001 if x.equation_basis == "printed_si" else .0000254)}


class CoolingCoupon(Model):
    coupon_general_corrosion_rate_m_year: NonNegative
    pitting_multiplier: Positive = Field(ge=5,le=10)
    representativeness_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-coupon-pitting-rate", "Qualified cooling-water coupon general to pitting estimate", CoolingCoupon,
    ["Part2 §11.1.10(c),Table2.B.11.1; PDF pp401,407"],limitations=[
        "Source prefers representative measured coupon rates over model; rule-of-thumb pitting5-10 times weight-loss general rate. Explicit multiplier and representativeness basis required. Flowing coupon may miss deposits/stagnant/MIC attack; no implied qualification of those cases or universal pitting multiplier."])
def coupon_rate(x):
    ensure(bool(x.representativeness_basis.strip()),"Coupon representativeness basis must not be blank")
    rate = x.coupon_general_corrosion_rate_m_year*x.pitting_multiplier
    finite_tree(rate)
    return {"pitting_corrosion_rate_m_year":rate}


class CoolingFresh(Model):
    material: Literal["carbon_steel"]
    applicability_basis: str = Field(min_length=1)
    actual_ph: float = Field(ge=6.5,le=9.5,strict=True,allow_inf_nan=False)
    saturation_ph: NonNegative = Field(le=14)
    saturation_ph_basis: str = Field(min_length=1)
    chloride_ppm: NonNegative
    velocity_m_s: NonNegative
    system: Literal["open_recirculating","closed_recirculating","once_through_fresh"]
    effective_microbiological_control: bool
    no_deposits_or_local_low_flow: bool
    no_corrosion_inhibitor_model_credit: Literal[True]
    condition_interpretation: Literal["body_rsi6_velocity2_44","us_header_rsi6_velocity8ft"]
    rate_unit_basis: Units
    velocity_equation_basis: Units
    temperature: CoolingTemperature
    chloride_lookup_policy: Lookup


@calculation("damage/cooling-water-fresh-assessment", "Untreated freshwater cooling corrosion with qualified supplied saturation pH", CoolingFresh,
    ["Part2 §11.1.10,§11.3.1-11.3.2.2,eqs(2.B.8)-(2.B.18); PDF pp401-404,409-410"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Carbon-steel representative rate; qualified supplied pHs can bypass unresolved coefficient table cells without inventing corrections. Measured representative rates preferred. Assumes pH6.5..9.5, effective MIC control and no deposits/local low flow; no inhibitor credit in this model path. Once-through fresh requires chloride<1000ppm; exactly1000 is unclassified by source strict inequalities and rejected. Temperature table and actual system must agree, once-through fresh uses open factors. Return rate is not automatically general/pitting classified; detailed body says pitting dominates, Annex2.B Table1.2 lists general at specified velocity. No5-10 coupon multiplier automatically applied to modeled rate."])
def fresh_assessment(x):
    ensure(bool(x.applicability_basis.strip()) and bool(x.saturation_ph_basis.strip()),"Applicability and saturation-pH basis required")
    ensure(x.effective_microbiological_control and x.no_deposits_or_local_low_flow,"Cooling-water MIC/deposit/low-flow assumptions not met")
    ensure(x.temperature.system == ("closed" if x.system == "closed_recirculating" else "open"),"Temperature system factor must match water system")
    if x.system == "once_through_fresh":
        ensure(x.chloride_ppm < 1000,"Once-through fresh classification requires chloride<1000ppm; boundary not inferred")
    stability = indices(CoolingIndices(actual_ph=x.actual_ph,saturation_ph=x.saturation_ph))
    ensure(stability["ryznar_stability_index"] >= 0,"RSI outside source expected positive domain")
    base = base_rate(CoolingBase(chloride_ppm=x.chloride_ppm,ryznar_stability_index=stability["ryznar_stability_index"],velocity_m_s=x.velocity_m_s,
        condition_interpretation=x.condition_interpretation,rate_unit_basis=x.rate_unit_basis,lookup_policy=x.chloride_lookup_policy))
    temp = temperature_factor(x.temperature)
    vel = velocity_factor(CoolingVelocity(velocity_m_s=x.velocity_m_s,equation_basis=x.velocity_equation_basis))
    rate = rate_equation(CoolingRateEquation(base_corrosion_rate_m_year=base["base_corrosion_rate_m_year"],temperature_factor=temp["temperature_factor"],velocity_factor=vel["velocity_factor"]))
    return {**stability,**base,**temp,**vel,**rate}


class CoolingThinning(Model):
    cooling: CoolingFresh
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    thinning_type: Literal["general","local"]
    qualification_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-thinning-assessment", "Freshwater cooling rate through qualified non-AST thinning DF", CoolingThinning,
    ["Part2 Annex2.B §11; Part2 §4.5.7"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Unclad non-AST component only. Same representative cooling model rate drives loss and either strength method; conditions derive monitoring/piping adjustments. Owner must qualify general/local thinning and actual inspection coverage despite source body/summary classification difference. No automatic pit multiplier on modeled rate; coupon-pitting estimate is a separate API. No treatment-credit path, MIC/deposit modeling, all-mechanism DF, heat-exchanger bundle rupture model or AST use."])
def cooling_thinning(x):
    rate = fresh_assessment(x.cooling)
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=rate["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**rate,**result,"thinning_type":x.thinning_type}
