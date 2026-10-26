"""External corrosion/CUI rate, coating and Bayesian damage calculations."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure
from .thinning import StrengthRatio, strength_ratio, Posterior, posterior, ThinningBase, thinning_base

Driver=Literal["marine_or_cooling_tower","temperate","arid_dry","severe"]
DRIVERS=("marine_or_cooling_tower","temperate","arid_dry","severe")
# SI mm/year. External -8 C severe cell contradicts US table; do not silently repair it.
EXTERNAL=[(-12,(0,0,0,0)),(-8,(.025,0,0,None)),(6,(.127,.076,.025,.254)),(32,(.127,.076,.025,.254)),
          (71,(.127,.051,.025,.254)),(107,(.025,0,0,.051)),(121,(0,0,0,0))]
CUI=[(-12,(0,0,0,0)),(-8,(.025,0,0,.076)),(6,(.127,.076,.025,.254)),(32,(.127,.076,.025,.254)),
     (71,(.254,.127,.051,.508)),(107,(.127,.025,.025,.254)),(135,(.051,.025,0,.254)),(162,(.025,0,0,.127)),(176,(0,0,0,0))]


class RateQuery(Model):
    temperature_k: Positive
    driver: Driver


def interpolate_rate(table,x):
    t=x.temperature_k-273.15
    column=DRIVERS.index(x.driver)
    ensure(table[0][0]-1e-9<=t<=table[-1][0]+1e-9,"Temperature outside source table range; no extrapolation")
    for temp,values in table:
        if math.isclose(t,temp,abs_tol=1e-9,rel_tol=0):
            ensure(values[column] is not None,"Conflicting SI/US source cell requires reconciliation", "ambiguous_source")
            return values[column]/1000
    for (a,va),(b,vb) in zip(table,table[1:]):
        if a<t<b:
            ensure(va[column] is not None and vb[column] is not None,"Interpolation touches a conflicting source cell", "ambiguous_source")
            return (va[column]+(vb[column]-va[column])*(t-a)/(b-a))/1000
    ensure(False,"Unresolved table interpolation")


@calculation("damage/external-base-rate", "External corrosion SI base rate", RateQuery,
             ["Part 2 Table 15.2M; PDF p231"], limitations=["Linear interpolation only within -12..121 C. Severe -8 C cell and adjacent interpolation are disabled due to SI/US mismatch."])
def external_base_rate(x):
    return {"base_corrosion_rate_m_year":interpolate_rate(EXTERNAL,x)}


@calculation("damage/cui-base-rate", "CUI SI base corrosion rate", RateQuery,
             ["Part 2 Table 16.2M; PDF p243"], limitations=["Linear interpolation only within -12..176 C; material/service screening separate."])
def cui_base_rate(x):
    return {"base_corrosion_rate_m_year":interpolate_rate(CUI,x)}


class ExposurePeriod(Model):
    temperature_k: Positive
    duration_fraction: Fraction


class WeightedRate(Model):
    mechanism: Literal["external","cui"]
    driver: Driver
    periods: list[ExposurePeriod]=Field(min_length=1,max_length=1000)


@calculation("damage/external-time-weighted-rate", "Time-weighted external/CUI base rate", WeightedRate,
             ["Part 2 Tables 15.2M/16.2M note 3"], limitations=["Weights describe operating-time fractions and must sum to one; all period temperatures must lie within the selected source table."])
def time_weighted_rate(x):
    ensure(math.isclose(math.fsum(p.duration_fraction for p in x.periods),1,abs_tol=1e-9),"Duration fractions must sum to 1")
    table=EXTERNAL if x.mechanism=="external" else CUI
    rates=[interpolate_rate(table,RateQuery(temperature_k=p.temperature_k,driver=x.driver)) for p in x.periods]
    return {"base_corrosion_rate_m_year":math.fsum(p.duration_fraction*r for p,r in zip(x.periods,rates)),"period_rates_m_year":rates}


class RateAdjustment(Model):
    base_corrosion_rate_m_year: NonNegative
    water_retaining_design: bool
    soil_or_water_interface: bool


@calculation("damage/external-rate-adjust", "External corrosion design/interface adjustment", RateAdjustment,
             ["Part 2 eq (2.34); PDF p224"])
def external_rate_adjust(x):
    factor=2 if x.water_retaining_design or x.soil_or_water_interface else 1
    return {"design_interface_factor":factor,"corrosion_rate_m_year":x.base_corrosion_rate_m_year*factor}


class CuiAdjustment(RateAdjustment):
    insulation: Literal["unknown","foamglass","pearlite","fiberglass","mineral_wool","calcium_silicate","asbestos"]
    complexity: Literal["below_average","average","above_average"]
    insulation_condition: Literal["below_average","average","above_average"]


@calculation("damage/cui-rate-adjust", "CUI insulation/condition/complexity adjustment", CuiAdjustment,
             ["Part 2 eq (2.51), §16.6.3, Table 16.3; PDF pp234-235,244"])
def cui_rate_adjust(x):
    insulation={"foamglass":.75,"pearlite":1}.get(x.insulation,1.25)
    complexity={"below_average":.75,"average":1,"above_average":1.25}[x.complexity]
    condition={"below_average":1.25,"average":1,"above_average":.75}[x.insulation_condition]
    design=2 if x.water_retaining_design or x.soil_or_water_interface else 1
    return {"insulation_factor":insulation,"complexity_factor":complexity,"condition_factor":condition,"design_interface_factor":design,
            "corrosion_rate_m_year":x.base_corrosion_rate_m_year*insulation*complexity*condition*design}


class CoatingExposure(Model):
    years_since_thickness_reading: NonNegative
    coating_age_years: NonNegative
    coating_quality: Literal["none_or_poor","medium","high"]


@calculation("damage/coating-exposure", "Coating-adjusted corrosion exposure time", CoatingExposure,
             ["Part 2 eqs (2.36)-(2.42),(2.53)-(2.59); PDF pp224,235"])
def coating_exposure(x):
    window={"none_or_poor":0,"medium":5,"high":15}[x.coating_quality]
    credit=min(window,x.coating_age_years)
    if x.years_since_thickness_reading<x.coating_age_years:
        credit-=min(window,x.coating_age_years-x.years_since_thickness_reading)
    credit=min(x.years_since_thickness_reading,max(0,credit))
    return {"coating_credit_years":credit,"corrosion_exposure_years":x.years_since_thickness_reading-credit}


class ExternalAssessment(Model):
    rate: RateAdjustment
    coating: CoatingExposure
    strength: StrengthRatio
    inspections: Posterior


class CuiAssessment(ExternalAssessment):
    rate: CuiAdjustment


def assess(x):
    rate=cui_rate_adjust(x.rate) if isinstance(x.rate,CuiAdjustment) else external_rate_adjust(x.rate)
    exposure=coating_exposure(x.coating)
    wall_loss=rate["corrosion_rate_m_year"]*exposure["corrosion_exposure_years"]/x.strength.starting_thickness_m
    strength=strength_ratio(x.strength)
    post=posterior(x.inspections)
    base=thinning_base(ThinningBase(wall_loss_fraction=wall_loss,strength_ratio=strength["strength_ratio"],posterior=post["posterior_probabilities"]))
    return {"corrosion_rate_m_year":rate["corrosion_rate_m_year"],**exposure,"wall_loss_fraction":wall_loss,**strength,**post,
            "reliability_indices":base["reliability_indices"],"weighted_failure_probability":base["weighted_failure_probability"],"damage_factor":base["base_damage_factor"]}


@calculation("damage/external-corrosion", "External corrosion Bayesian damage factor", ExternalAssessment,
             ["Part 2 §15.6.3 eqs (2.34)-(2.50)"], limitations=["Internal-pressure-governed strength path only; eligible material/service, base rate, flow stress and inspection validity supplied. No internal-thinning floor/adjustments applied."])
def external_assessment(x):
    return assess(x)


@calculation("damage/cui", "Corrosion-under-insulation Bayesian damage factor", CuiAssessment,
             ["Part 2 §16.6.3 eqs (2.51)-(2.67)"], limitations=["Internal-pressure-governed strength path (2.63) only; the Min/Max discrepancy in source (2.62) is not inferred. Base rate and inspection validity supplied. No internal-thinning floor/adjustments applied.",
                 "Source STEP 13 references Tables 5.6/5.7, which do not identify prior/conditional probability tables. This implementation explicitly adopts general-thinning Tables 4.5/4.6, consistent with external-corrosion methodology; this interpretation requires independent engineering verification."])
def cui_assessment(x):
    return assess(x)
