"""Carbon-steel AST floor corrosion, 2016 Annex 2.B section 14."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure

Pad = Literal["soil_high_salt", "crushed_limestone", "native_soil", "construction_grade_sand",
    "continuous_asphalt", "continuous_concrete", "oil_sand", "high_resistivity_low_chloride_sand"]
Bottom = Literal["rpb_not_per_api650", "rpb_per_api650", "single_bottom"]
Boundary = Literal["lower_resistivity_interval", "higher_resistivity_interval"]
Policy = Literal["apply_2_mpy_recommendation", "qualified_no_floor"]
_PADS = dict(zip(Pad.__args__, (1.5, 1.4, 1.3, 1.15, 1., 1., .7, .7)))


class BottomBase(Model):
    side: Literal["soil", "product"]
    unit_basis: Literal["printed_si", "printed_us_mpy"]


@calculation("tank/bottom-base-corrosion-rate", "AST floor reference base corrosion rate", BottomBase,
    ["Part2 Annex2.B §14.3.1-14.3.2,Tables2.B.14.3,14.10; PDF pp430-435"], limitations=[
        "Fallback rates only; comparable inspection-derived base rates take precedence. Rounded SI and US pairs differ. Soil reference: moderate resistivity, continuous asphalt/concrete, good drainage, no functioning CP, single bottom, below24C. Product reference: no required coating, below24C, no coil, no regular water draws. Not a measured net rate."])
def base(x):
    si, us = (.13, 5.) if x.side == "soil" else (.05, 2.)
    return dict(base_corrosion_rate_m_year=si/1000 if x.unit_basis == "printed_si" else us*.0000254,
        printed_si_rate_mm_year=si, printed_us_rate_mpy=us, side=x.side, unit_basis=x.unit_basis)


class BottomSoilRateEquation(Model):
    base_corrosion_rate_m_year: NonNegative
    resistivity_factor: NonNegative
    pad_factor: NonNegative
    drainage_factor: NonNegative
    cathodic_protection_factor: NonNegative
    bottom_type_factor: NonNegative
    temperature_factor: NonNegative


@calculation("tank/bottom-soil-rate-equation", "AST floor soil-side corrosion rate equation", BottomSoilRateEquation,
    ["Part2 Annex2.B §14.2.1,eq(2.B.37); PDF p430"], limitations=[
        "Independent equation kernel only. Factors and reference base rate are supplied and must be qualified from §14.3 tables or comparable inspection data. No soil classification, factor selection, AST applicability or measured-rate correction is inferred."])
def soil_rate_equation(x):
    rate = _rate(x.base_corrosion_rate_m_year, [x.resistivity_factor, x.pad_factor,
        x.drainage_factor, x.cathodic_protection_factor, x.bottom_type_factor,
        x.temperature_factor])
    return dict(soil_corrosion_rate_m_year=rate)


class BottomProductRateEquation(Model):
    base_corrosion_rate_m_year: NonNegative
    product_condition_factor: NonNegative
    temperature_factor: NonNegative
    steam_coil_factor: NonNegative
    water_draw_factor: NonNegative


@calculation("tank/bottom-product-rate-equation", "AST floor product-side corrosion rate equation", BottomProductRateEquation,
    ["Part2 Annex2.B §14.2.2,eq(2.B.38); PDF p430"], limitations=[
        "Independent equation kernel only. Factors and reference base rate are supplied and must be qualified from §14.3 tables or comparable inspection data. No product wetness, temperature, coil or water-draw classification is inferred."])
def product_rate_equation(x):
    rate = _rate(x.base_corrosion_rate_m_year, [x.product_condition_factor,
        x.temperature_factor, x.steam_coil_factor, x.water_draw_factor])
    return dict(product_corrosion_rate_m_year=rate)


class BottomResistivity(Model):
    release_prevention_barrier: bool
    soil_resistivity_ohm_m: Positive | None = None
    shared_boundary_basis: Boundary | None = None


@calculation("tank/bottom-soil-resistivity-factor", "AST floor native-soil resistivity factor", BottomResistivity,
    ["Part2 Annex2.B §14.3.1(a),Table2.B.14.4; PDF pp430,433"], limitations=[
        "RPB or unknown resistivity uses1 by source instruction. Public ohm m; source ohm cm=100*ohm m. Shared1000/2000ohm cm endpoints require explicit interval basis. High-resistivity factor is.66 for AST, not the buried-pipe.60 factor."])
def resistivity(x):
    v = x.soil_resistivity_ohm_m
    if x.release_prevention_barrier or v is None:
        ensure(x.shared_boundary_basis is None, "Interval basis is inapplicable when resistivity is not used")
        return dict(resistivity_factor=1., selection_reason="rpb" if x.release_prevention_barrier else "unknown_assume_moderate")
    if v in (10., 20.):
        ensure(x.shared_boundary_basis is not None, "Shared resistivity endpoint requires interval basis", "ambiguous_soil_resistivity_boundary")
        i = (1 if v == 10 else 2)+(x.shared_boundary_basis == "higher_resistivity_interval")
    else:
        ensure(x.shared_boundary_basis is None, "Interval basis applies only at shared endpoints")
        i = 0 if v < 5 else 1 if v < 10 else 2 if v < 20 else 3 if v <= 100 else 4
    return dict(resistivity_factor=(1.5, 1.25, 1., .83, .66)[i], selection_reason="resistivity_table")


class BottomPad(Model):
    pad_type: Pad


@calculation("tank/bottom-pad-factor", "AST floor foundation pad factor", BottomPad,
    ["Part2 Annex2.B Table2.B.14.5; PDF p434"], limitations=["Owner qualifies actual pad category; no interpolation or automatic soil classification."])
def pad(x):
    return dict(pad_factor=_PADS[x.pad_type])


class BottomDrainage(Model):
    drainage_category: Literal["one_third_frequently_underwater", "storm_water_collects", "no_storm_water_collects"]


@calculation("tank/bottom-drainage-factor", "AST floor drainage factor", BottomDrainage,
    ["Part2 Annex2.B §14.3.1(c),Table2.B.14.6; PDF pp430,434"], limitations=[
        "Owner selects category: table says one-third frequently underwater; prose describes more than one-third circumference underwater for extended periods. No invented numeric exposure classifier."])
def drainage(x):
    return dict(drainage_factor={"one_third_frequently_underwater":3., "storm_water_collects":2., "no_storm_water_collects":1.}[x.drainage_category])


class BottomCP(Model):
    protection_category: Literal["none", "present_not_per_api651", "present_per_api651"]
    effectiveness_verified_by_high_level_inspection: bool
    verification_basis: str | None = None


@calculation("tank/bottom-cp-factor", "AST floor cathodic protection factor with inspection credit gate", BottomCP,
    ["Part2 Annex2.B §14.3.1(d),Table2.B.14.7; PDF pp431,434"], limitations=[
        "Table nominal factors1/.66/.33; text allows no credit without High Level inspection verifying effective CP under referenced NACE RP0169 or equivalent. Owner supplies verification basis. Historical references do not establish current compliance."])
def cp(x):
    verified = x.effectiveness_verified_by_high_level_inspection
    if verified:
        ensure(x.protection_category != "none", "Absent CP cannot receive verified credit")
        ensure(x.verification_basis is not None and bool(x.verification_basis.strip()), "Verified CP requires inspection basis")
    else:
        ensure(x.verification_basis is None, "Unverified CP cannot supply verification basis")
    nominal = {"none":1., "present_not_per_api651":.66, "present_per_api651":.33}[x.protection_category]
    return dict(nominal_table_factor=nominal, cathodic_protection_factor=nominal if verified else 1., credit_applied=verified)


class BottomType(Model):
    bottom_type: Bottom


@calculation("tank/bottom-type-factor", "AST floor construction factor", BottomType,
    ["Part2 Annex2.B Table2.B.14.8; PDF p434"], limitations=["RPB classification is supplied by the owner; qualified RPB and single bottom both have factor1."])
def bottom_type(x):
    return dict(bottom_type_factor=1.4 if x.bottom_type == "rpb_not_per_api650" else 1.)


class BottomTemperature(Model):
    highest_operating_temperature_k: Positive
    threshold_basis: Literal["printed_si", "printed_us_converted"]


@calculation("tank/bottom-temperature-factor", "AST floor soil and product temperature factor", BottomTemperature,
    ["Part2 Annex2.B Tables2.B.14.9,14.12; PDF p435"], limitations=[
        "Both tables have identical five bands. Printed SI24/66/93/121C differ from US75/150/200/250F converted to K; basis required. Above highest threshold source factor returns1; not a qualification of high-temperature or cryogenic service."])
def temperature(x):
    bounds = [c+273.15 for c in (24.,66.,93.,121.)] if x.threshold_basis == "printed_si" else [(f-32)*5/9+273.15 for f in (75.,150.,200.,250.)]
    i = next((i for i, b in enumerate(bounds) if x.highest_operating_temperature_k <= b), 4)
    return dict(temperature_factor=(1.,1.1,1.3,1.4,1.)[i], source_row=i+1, threshold_basis=x.threshold_basis)


class BottomProductCondition(Model):
    product_condition: Literal["wet", "dry"]


@calculation("tank/bottom-product-condition-factor", "AST floor product wetness factor", BottomProductCondition,
    ["Part2 Annex2.B §14.3.2(a),Table2.B.14.11; PDF pp431,435"], limitations=["Wet means significant bottom sediment and water; owner qualifies actual condition."])
def product_condition(x):
    return dict(product_condition_factor=2.5 if x.product_condition == "wet" else 1.)


class BottomSteamCoil(Model):
    steam_coil_present: bool


@calculation("tank/bottom-steam-coil-factor", "AST floor steam coil factor", BottomSteamCoil,
    ["Part2 Annex2.B Table2.B.14.13; PDF p436"], limitations=["Presence multiplier only; no detailed steam-leak thermal model."])
def steam_coil(x):
    return dict(steam_coil_factor=1.15 if x.steam_coil_present else 1.)


class BottomWaterDraw(Model):
    water_draw_practice: Literal["none_or_not_regular", "weekly", "after_every_receipt"]


@calculation("tank/bottom-water-draw-factor", "AST floor qualified regular water draw factor", BottomWaterDraw,
    ["Part2 Annex2.B §14.3.2(d),Table2.B.14.14; PDF pp431,436"], limitations=["Credit.7 requires weekly draws or draws after every receipt; merely having a drain earns no credit."])
def water_draw(x):
    return dict(water_draw_factor=1. if x.water_draw_practice == "none_or_not_regular" else .7)


class BottomCombine(Model):
    soil_corrosion_rate_m_year: NonNegative
    product_corrosion_rate_m_year: NonNegative
    product_distribution: Literal["general", "local"]
    minimum_rate_policy: Policy
    no_floor_qualification_basis: str | None = None


@calculation("tank/bottom-corrosion-rate-combine", "AST floor two-sided corrosion-rate combination", BottomCombine,
    ["Part2 Annex2.B §14.3.3; PDF p431"], limitations=[
        "Soil corrosion is local. General product corrosion adds both rates; local product corrosion uses maximum. Source recommends minimum2mpy=.0000508m/year. Explicit qualified bypass retains raw value. General/local selection follows section14.3.3; summary Table2.B.1.2 lists AST product as local. No AST damage factor computed here."])
def combine(x):
    apply = x.minimum_rate_policy == "apply_2_mpy_recommendation"
    ensure((x.no_floor_qualification_basis is None) if apply else (x.no_floor_qualification_basis is not None and bool(x.no_floor_qualification_basis.strip())), "Floor policy and qualification basis must agree")
    values = x.soil_corrosion_rate_m_year, x.product_corrosion_rate_m_year
    raw = sum(values) if x.product_distribution == "general" else max(values)
    return dict(raw_combined_rate_m_year=raw, combined_corrosion_rate_m_year=max(raw,.0000508) if apply else raw,
        recommended_minimum_rate_m_year=.0000508, minimum_applied=apply and raw < .0000508,
        combination_rule="sum" if x.product_distribution == "general" else "maximum")


class BottomCorrosion(Model):
    material: Literal["carbon_steel"]
    applicability_basis: str = Field(min_length=1)
    soil_base_corrosion_rate_m_year: NonNegative
    product_base_corrosion_rate_m_year: NonNegative
    soil_base_rate_source: str = Field(min_length=1)
    product_base_rate_source: str = Field(min_length=1)
    bottom_type: Bottom
    soil_resistivity_ohm_m: Positive | None = None
    shared_boundary_basis: Boundary | None = None
    pad: BottomPad
    drainage: BottomDrainage
    cathodic_protection: BottomCP
    temperature: BottomTemperature
    product_condition: BottomProductCondition
    steam_coil: BottomSteamCoil
    water_draw: BottomWaterDraw
    product_distribution: Literal["general", "local"]
    minimum_rate_policy: Policy
    no_floor_qualification_basis: str | None = None


def _rate(base_rate, factors):
    if base_rate == 0:
        return 0.
    rate = base_rate*math.prod(factors)
    ensure(rate > 0 and math.isfinite(rate), "Corrosion-rate product outside finite positive range", "numerical_failure")
    return rate


@calculation("tank/bottom-corrosion-assessment", "AST floor soil and product corrosion assessment", BottomCorrosion,
    ["Part2 Annex2.B §14.3,eqs(2.B.37-38),Tables2.B.14.4-14; PDF pp430-436"], limitations=[
        "Carbon-steel AST floor only. Explicit comparable base rates and provenance required; measured net rates must not be multiplied again without qualification. RPB soil-resistivity override derives from bottom type. Single highest operating temperature drives both source temperature factors. CP inspection gate enforced. No coating credit, remaining life, AST thinning damage factor or complete asset risk calculation."])
def assessment(x):
    ensure(all(s.strip() for s in (x.applicability_basis,x.soil_base_rate_source,x.product_base_rate_source)), "Qualification and provenance must not be blank")
    fsr = resistivity(BottomResistivity(release_prevention_barrier=x.bottom_type != "single_bottom",
        soil_resistivity_ohm_m=x.soil_resistivity_ohm_m, shared_boundary_basis=x.shared_boundary_basis))["resistivity_factor"]
    fpa, fdr = pad(x.pad)["pad_factor"], drainage(x.drainage)["drainage_factor"]
    cp_result = cp(x.cathodic_protection)
    fcp = cp_result["cathodic_protection_factor"]
    ftb = bottom_type(BottomType(bottom_type=x.bottom_type))["bottom_type_factor"]
    ft = temperature(x.temperature)["temperature_factor"]
    fpc = product_condition(x.product_condition)["product_condition_factor"]
    fsc, fwd = steam_coil(x.steam_coil)["steam_coil_factor"], water_draw(x.water_draw)["water_draw_factor"]
    soil_rate = _rate(x.soil_base_corrosion_rate_m_year,[fsr,fpa,fdr,fcp,ftb,ft])
    product_rate = _rate(x.product_base_corrosion_rate_m_year,[fpc,ft,fsc,fwd])
    result = combine(BottomCombine(soil_corrosion_rate_m_year=soil_rate,product_corrosion_rate_m_year=product_rate,
        product_distribution=x.product_distribution,minimum_rate_policy=x.minimum_rate_policy,no_floor_qualification_basis=x.no_floor_qualification_basis))
    return dict(**result,soil_corrosion_rate_m_year=soil_rate,product_corrosion_rate_m_year=product_rate,
        resistivity_factor=fsr,pad_factor=fpa,drainage_factor=fdr,cathodic_protection_factor=fcp,bottom_type_factor=ftb,
        temperature_factor=ft,product_condition_factor=fpc,steam_coil_factor=fsc,water_draw_factor=fwd,
        cp_credit_applied=cp_result["credit_applied"])
