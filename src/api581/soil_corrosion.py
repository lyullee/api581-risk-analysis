"""2016 Annex2.B §12 buried-carbon-steel soil-side corrosion rates."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure, finite_tree
from .thinning import WallLoss, StrengthRatio, Posterior, UncladThinning, unclad

Profile = Literal["dry_inland_sand","variable_industrial_silt","saturated_coastal_clay"]
Coating = Literal["bare","fusion_bonded_epoxy","liquid_epoxy","asphalt_enamel","asphalt_mastic",
    "coal_tar_enamel","extruded_pe_mastic_or_rubber","mill_pe_tape_mastic","field_pe_tape_mastic","three_layer_pe_pp"]
CP = Literal["unprotected_adjacent_cp_stray_current","no_cp","not_annual_or_partly_noncompliant",
    "annual_on_potential_entire_structure","annual_polarized_or_instant_off_entire_structure"]
_BASE = {"dry_inland_sand":(.03,1.,"Sand; low chlorides inland/non-industrial; homogeneous fine silt or sand; dry desert-like"),
    "variable_industrial_silt":(.13,5.,"Silt; moderate industrial contaminants; mixed particles; variable moisture"),
    "saturated_coastal_clay":(.25,10.,"Clay; high chlorides coastal; >50% gravel; normally saturated")}
_COAT = {k:(1.,1.1,1.5,1.1) for k in ("fusion_bonded_epoxy","liquid_epoxy","asphalt_enamel","asphalt_mastic")}
_COAT.update(coal_tar_enamel=(1.,1.2,2.,1.5),extruded_pe_mastic_or_rubber=(1.,1.2,3.,1.5),
    mill_pe_tape_mastic=(1.5,1.2,3.,1.5),field_pe_tape_mastic=(2.,2.,3.,1.5),three_layer_pe_pp=(1.,1.2,2.,1.2))
_CP = dict(zip(("unprotected_adjacent_cp_stray_current","no_cp","not_annual_or_partly_noncompliant",
    "annual_on_potential_entire_structure","annual_polarized_or_instant_off_entire_structure"),(10.,1.,.8,.4,.05)))


class SoilBaseRate(Model):
    condition_profile: Profile
    unit_basis: Literal["printed_si","printed_us_mpy"]


@calculation("damage/soil-base-rate-table", "Soil base corrosion-rate reference profiles", SoilBaseRate,
    ["Part2 Annex2.B §12.4.2,Table2.B.12.2; PDF pp417,420"],limitations=[
        "Three full soil/contaminant/particle/moisture profiles, not automatic classification by soil name alone. Measured comparable rates take precedence under source guidance. Mixed conditions require qualified owner base rate, no invented interpolation. Printed SI.03/.13/.25mm/y differ from exact1/5/10mpy conversion; selected basis explicit."])
def base_rate(x):
    si,mpy,description = _BASE[x.condition_profile]
    rate = si/1000 if x.unit_basis == "printed_si" else mpy*.0000254
    return {"corrosion_rate_m_year":rate,"printed_si_rate_mm_year":si,"printed_us_rate_mpy":mpy,
        "selected_unit_basis":x.unit_basis,"condition_description":description}


class SoilResistivity(Model):
    soil_resistivity_ohm_m: Positive
    shared_boundary_basis: Literal["lower_resistivity_interval","higher_resistivity_interval"] | None = None


@calculation("damage/soil-resistivity-factor", "Optional soil resistivity adjustment factor", SoilResistivity,
    ["Part2 Annex2.B §12.4.3,Table2.B.12.3; PDF pp417-418,420"],limitations=[
        "Public resistivity ohm m; source ohm cm=100*ohm m. Shared1000/2000ohm cm endpoints require explicit lower/higher interval selection.500 belongs500-1000,10000 belongs2000-10000. No inferred continuous resistivity interpolation. Omit adjustment when already incorporated in base rate to avoid double counting."])
def resistivity(x):
    value = x.soil_resistivity_ohm_m
    if value in (10.,20.):
        ensure(x.shared_boundary_basis is not None,"Shared resistivity endpoint requires interval basis","ambiguous_soil_resistivity_boundary")
        index = (1 if value == 10. else 2)+(x.shared_boundary_basis == "higher_resistivity_interval")
    else:
        index = 0 if value < 5 else 1 if value < 10 else 2 if value < 20 else 3 if value <= 100 else 4
    return {"resistivity_factor":(1.5,1.25,1.,.83,.6)[index],"source_row":index+1}


class SoilTemperature(Model):
    equipment_temperature_k: Positive
    threshold_basis: Literal["printed_si","printed_us_converted"]


@calculation("damage/soil-temperature-factor", "Buried equipment soil-corrosion temperature factor", SoilTemperature,
    ["Part2 Annex2.B §12.4.4,Table2.B.12.4; PDF pp418,420"],limitations=[
        "SI uses49/104C; US uses120/220F converted exactly to K. Paired boundaries differ, so basis required. Middle interval includes both endpoints; outer factors1, middle2. This table lookup does not qualify cryogenic/high-temperature buried service or frozen-soil chemistry."])
def temperature(x):
    low,high = (322.15,377.15) if x.threshold_basis == "printed_si" else ((120-32)*5/9+273.15,(220-32)*5/9+273.15)
    return {"temperature_factor":2. if low <= x.equipment_temperature_k <= high else 1.,
        "lower_boundary_k":low,"upper_boundary_k":high,"threshold_basis":x.threshold_basis}


class SoilCathodicProtection(Model):
    protection_category: CP


@calculation("damage/soil-cp-factor", "Soil corrosion cathodic-protection effectiveness factor", SoilCathodicProtection,
    ["Part2 Annex2.B §12.4.5,Table2.B.12.5; PDF pp418,421"],limitations=[
        "Owner classifies actual coverage, annual testing,2016 NACE-reference compliance and adjacent-CP stray-current risk. No-CP1 differs from unprotected/untested with adjacent-CP stray current10. Factor.05 requires full-structure annual polarized/instant-off criteria; not automatic interpretation of one potential reading. Large/dynamic stray currents require specialist analysis under source scope."])
def cathodic_protection(x):
    return {"cathodic_protection_factor":_CP[x.protection_category]}


class SoilCoating(Model):
    coating_type: Coating
    coating_age_years: NonNegative
    rated_temperature_occasionally_exceeded: bool
    maintenance_rare_or_none: bool


@calculation("damage/soil-coating-factor", "Product of independent soil-coating effectiveness factors", SoilCoating,
    ["Part2 Annex2.B §12.4.6,eq(2.B.22),Table2.B.12.6; PDF pp419,421"],limitations=[
        "Factors apply independently; age multiplier only for age>20years, nonapplicable multipliers1. Bare factor1. Applies even without CP. Source worked mill-PE example prints1.5*1.2*3*1.5=13.5, but table-factor product is8.1; calculation follows factor multiplication, reports printed example separately and does not assert an authorized erratum."])
def coating(x):
    if x.coating_type == "bare":
        ensure(not x.rated_temperature_occasionally_exceeded and not x.maintenance_rare_or_none,
            "Bare structure cannot have coating-temperature/maintenance conditions")
        factors = [1.,1.,1.,1.]
    else:
        base,age,abuse,maintenance = _COAT[x.coating_type]
        factors = [base,age if x.coating_age_years > 20 else 1.,abuse if x.rated_temperature_occasionally_exceeded else 1.,
            maintenance if x.maintenance_rare_or_none else 1.]
    example = x.coating_type == "mill_pe_tape_mastic" and x.coating_age_years > 20 and x.rated_temperature_occasionally_exceeded and x.maintenance_rare_or_none
    return {"coating_effectiveness_factor":math.prod(factors),"base_factor":factors[0],"age_factor":factors[1],
        "temperature_abuse_factor":factors[2],"maintenance_factor":factors[3],
        "calculation_basis":"table_factor_product","printed_example_discrepancy_applies":example,
        "printed_example_reported_factor":13.5 if example else None}


class SoilRateEquation(Model):
    base_corrosion_rate_m_year: NonNegative
    resistivity_factor: Positive
    temperature_factor: Positive
    cathodic_protection_factor: Positive
    coating_effectiveness_factor: Positive


@calculation("damage/soil-rate-equation", "Soil corrosion multiplicative rate equation", SoilRateEquation,
    ["Part2 Annex2.B eq(2.B.21); PDF p417"],limitations=[
        "CR=CRB*FSR*FT*FCP*FCE. Qualified factors supplied; no automatic material/service selection. Does not clamp to minimum corrosion rate or infer coating as zero-corrosion protection."])
def rate_equation(x):
    if x.base_corrosion_rate_m_year == 0:
        value = 0.
    else:
        value = math.exp(math.fsum(math.log(v) for v in (x.base_corrosion_rate_m_year,x.resistivity_factor,
            x.temperature_factor,x.cathodic_protection_factor,x.coating_effectiveness_factor)))
        ensure(value > 0,"Positive soil corrosion rate underflow","numerical_failure")
    return {"corrosion_rate_m_year":value}


class SoilRate(Model):
    material: Literal["carbon_steel"]
    in_contact_with_soil: bool
    applicability_basis: str = Field(min_length=1,max_length=1000)
    base_corrosion_rate_m_year: NonNegative
    base_rate_source: str = Field(min_length=1,max_length=1000)
    resistivity_application: Literal["apply","already_in_base","omitted_by_qualification"]
    resistivity: SoilResistivity | None = None
    resistivity_omission_basis: str | None = Field(default=None,min_length=1,max_length=1000)
    temperature: SoilTemperature
    cathodic_protection: SoilCathodicProtection
    coating: SoilCoating


_SOIL_LIMITS = [
    "Annex2.B screening requires carbon steel in soil contact. Owner qualifies buried-service applicability, actual soil/base rate and current/coating condition. Uses Table2.B.1.2 local thinning classification; not atmospheric/CUI corrosion, AST floor automatic model, MIC/stray-current detailed analysis or arbitrary cryogenic service.",
    "Optional resistivity factor must be explicitly applied or omitted with basis, including when already incorporated in base rate. No duplicate soil-resistivity weighting. Source SI/US rate/temperature rounding, resistivity shared endpoints and coating example8.1vs13.5 remain explicit. Coating uses table product, not erroneous worked arithmetic.",
    "Base-rate reference conditions must be qualified before reapplying CP,coating or temperature effects. Already-adjusted measured net rates can feed the existing thinning kernel directly; this composition does not infer which effects a measured rate already contains.",
]


@calculation("damage/soil-corrosion-rate", "Compose qualified soil-side corrosion base rate and table factors", SoilRate,
    ["Part2 Annex2.B Tables2.B.1.1/1.2,§12,eq(2.B.21); PDF pp322-323,417-421"],limitations=_SOIL_LIMITS)
def soil_rate(x):
    ensure(x.in_contact_with_soil,"Soil contact screening not met","soil_screen_not_met")
    ensure(x.applicability_basis.strip() and x.base_rate_source.strip(),"Applicability and base-rate sources must be nonblank")
    if x.resistivity_application == "apply":
        ensure(x.resistivity is not None and x.resistivity_omission_basis is None,"Applied resistivity needs input and no omission basis")
        fsr = resistivity(x.resistivity)["resistivity_factor"]
    else:
        ensure(x.resistivity is None and x.resistivity_omission_basis is not None and x.resistivity_omission_basis.strip(),
            "Omitted/already-in-base resistivity needs explicit basis and no duplicate input")
        fsr = 1.
    ft = temperature(x.temperature)["temperature_factor"]
    fcp = cathodic_protection(x.cathodic_protection)["cathodic_protection_factor"]
    fce = coating(x.coating)
    factors = dict(resistivity_factor=fsr,temperature_factor=ft,cathodic_protection_factor=fcp,
        coating_effectiveness_factor=fce["coating_effectiveness_factor"])
    rate = rate_equation(SoilRateEquation(base_corrosion_rate_m_year=x.base_corrosion_rate_m_year,**factors))
    return {**rate,**factors,"base_corrosion_rate_m_year":x.base_corrosion_rate_m_year,
        "thinning_type":"local","resistivity_application":x.resistivity_application,
        "coating_calculation_basis":fce["calculation_basis"],"coating_example_discrepancy_applies":fce["printed_example_discrepancy_applies"]}


class SoilThinning(Model):
    soil: SoilRate
    elapsed_years: NonNegative
    strength: StrengthRatio
    inspections: Posterior
    online_monitoring_factor: Positive
    assessment_scope: Literal["unclad_internal_pressure_governed_non_ast"]


@calculation("damage/soil-thinning-assessment", "Soil corrosion rate through unclad non-AST thinning DF", SoilThinning,
    ["Part2 Annex2.B §12; Part2 §4.5.7 eqs(2.13),(2.18)-(2.23)"],
    origin="api581_soil_rate_to_unclad_thinning_composition",limitations=_SOIL_LIMITS+[
        "Single soil-side mechanism for qualified unclad non-AST internal-pressure-governed component and one constant-rate interval. No automatic history integration across coating-age20,CP or temperature changes. Same starting thickness from strength input feeds wall loss. Uses existing Bayesian thinning kernel and supplied monitoring factor. Injection/deadleg factors1 for this soil-only path. No AST floor, structural/external-pressure, cladding or automatic inspection-effectiveness determination. Result is not total all-mechanism DF or inspection acceptance."])
def soil_thinning(x):
    rate = soil_rate(x.soil)
    finite_tree(rate)
    result = unclad(UncladThinning(wall=WallLoss(starting_thickness_m=x.strength.starting_thickness_m,
        corrosion_rate_m_year=rate["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),strength=x.strength,
        inspections=x.inspections,injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=x.online_monitoring_factor))
    return {**rate,**result,"assessment_scope":x.assessment_scope}
