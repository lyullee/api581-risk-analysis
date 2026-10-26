"""Level 1 toxic, NFNT, final area and financial consequence calculations."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure


class Mitigation(Model):
    system: Literal["inventory_blowdown", "deluge_and_monitors", "monitors", "foam", "none"]
    isolation_class: Literal["A", "B", "C"]


@calculation("level1/mitigation", "Flammable consequence mitigation factor", Mitigation,
             ["Part 3 Table 4.10; PDF p525"], limitations=["Select one applicable measure; no unsupported combination/stacking of credits."])
def mitigation(x):
    ensure(x.system != "inventory_blowdown" or x.isolation_class in ("A","B"), "Blowdown credit requires isolation class A or B")
    return {"mitigation_fraction": {"inventory_blowdown":.25,"deluge_and_monitors":.2,"monitors":.05,"foam":.15,"none":0}[x.system]}


class ToxicSource(Model):
    theoretical_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    toxic_mass_fraction: Fraction


@calculation("level1/toxic-source", "Toxic component rate and mass", ToxicSource,
             ["Part 3 eqs (3.61)-(3.62); PDF p497"], limitations=["Use theoretical rate, without flammable detection magnitude reduction. Explicit toxic mitigation, if justified, is a separate input adjustment."])
def toxic_source(x):
    return {"toxic_rate_kg_s": x.theoretical_rate_kg_s*x.toxic_mass_fraction,"toxic_mass_kg": x.released_mass_kg*x.toxic_mass_fraction}


class ToxicDuration(Model):
    available_mass_kg: NonNegative
    theoretical_rate_kg_s: NonNegative
    detection_maximum_duration_s: NonNegative


@calculation("level1/toxic-duration", "Toxic release exposure duration", ToxicDuration,
             ["Part 3 §4.9.10 eq (3.67)"], limitations=["One-hour cap; detection magnitude reduction does not apply to toxic source rate."])
def toxic_duration(x):
    duration = min(3600,x.detection_maximum_duration_s,x.available_mass_kg/x.theoretical_rate_kg_s) if x.theoretical_rate_kg_s else 0
    return {"duration_s":duration}


AMMONIA = [(636.7,1.183),(846.3,1.181),(1053,1.180),(1256,1.178),(1455,1.176),(1650,1.174),
           (1842,1.172),(2029,1.169),(2213,1.166),(2389,1.161),(2558,1.155),(2714,1.145)]
CHLORINE = [(3350,1.097),(3518,1.095),(3798,1.092),(4191,1.089),(4694,1.085),(5312,1.082),
            (6032,1.077),(6860,1.072),(7788,1.066),(8798,1.057),(9890,1.046),(10994,1.026)]


class ToxicArea(Model):
    fluid: Literal["ammonia","chlorine"]
    release_type: Literal["continuous","instantaneous"]
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    duration_s: NonNegative
    nonignition_probability: Fraction


@calculation("level1/toxic-area", "Ammonia/chlorine toxic consequence area", ToxicArea,
             ["Part 3 eqs (3.65)-(3.66), §4.9.11, Table 4.12M; PDF pp498,526"],
             limitations=["Continuous curves support 5-60 minutes only; interpolate areas between duration curves, never extrapolate. Explicit nonignition probability supplied; no IDLH screening or spray credit selection."])
def toxic_area(x):
    if (x.release_type=="continuous" and (x.toxic_rate_kg_s==0 or x.duration_s==0)) or (x.release_type=="instantaneous" and x.toxic_mass_kg==0):
        return {"unweighted_personnel_area_m2":0,"personnel_area_m2":0}
    if x.release_type=="instantaneous":
        a,b = (2.684,.9011) if x.fluid=="ammonia" else (3.528,1.177)
        area=a*x.toxic_mass_kg**b
    else:
        ensure(300<=x.duration_s<=3600,"Continuous toxic duration must be within table range 300-3600 s")
        rows=AMMONIA if x.fluid=="ammonia" else CHLORINE
        position=x.duration_s/300-1
        lo,hi=math.floor(position),math.ceil(position)
        a,b=rows[lo]; lower=a*x.toxic_rate_kg_s**b
        a,b=rows[hi]; upper=a*x.toxic_rate_kg_s**b
        area=lower+(upper-lower)*(position-lo)
    return {"unweighted_personnel_area_m2":area,"personnel_area_m2":area*x.nonignition_probability}


class Steam(Model):
    adjusted_rate_kg_s: NonNegative
    released_mass_kg: NonNegative


@calculation("level1/steam-area", "Steam leak personnel consequence area", Steam,
             ["Part 3 eqs (3.69)-(3.71),(3.76); Annex 3.B C9,C10; PDF pp502,647"], limitations=["Level 1 steam burn correlation; no equipment damage area."])
def steam(x):
    continuous=.123*x.adjusted_rate_kg_s
    instantaneous=9.744*x.released_mass_kg**.6384
    weight=min(x.adjusted_rate_kg_s/25.2,1)
    return {"continuous_area_m2":continuous,"instantaneous_area_m2":instantaneous,"instantaneous_weight":weight,
            "personnel_area_m2":instantaneous*weight+continuous*(1-weight),"equipment_area_m2":0}


class Acid(Model):
    adjusted_rate_kg_s: NonNegative
    differential_pressure_pa: NonNegative


@calculation("level1/acid-caustic-area", "Acid/caustic splash personnel consequence", Acid,
             ["Part 3 eqs (3.72)-(3.75); Annex 3.B C4B,C8,C11; PDF pp502,647"],
             limitations=["Empirical correlation developed at approximately 15,30,60 psig. Reject extrapolation outside 103.4-413.7 kPa differential. Source has inconsistent C4/C4B naming; uses lb/s conversion 2.205."])
def acid(x):
    ensure(103400<=x.differential_pressure_pa<=413700,"Acid splash pressure outside documented 103.4-413.7 kPa range")
    pressure=.145*x.differential_pressure_pa/1000
    g=2696-21.9*pressure+1.474*pressure**2
    h=.31-.00032*(pressure-40)**2
    area=.2*.0929*g*(2.205*x.adjusted_rate_kg_s)**h if x.adjusted_rate_kg_s else 0
    return {"personnel_area_m2":area,"equipment_area_m2":0,"coefficient_g":g,"exponent_h":h}


class FinalArea(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_areas_m2: list[NonNegative] = Field(max_length=100)
    nfnt_personnel_area_m2: NonNegative


@calculation("consequence/final-area", "Final Level 1 consequence areas", FinalArea,
             ["Part 3 §§4.9.12,4.11 eqs (3.81)-(3.84)"], limitations=["Inputs must be evaluated on the same basis; multiple toxic species use maximum, not area addition."])
def final_area(x):
    toxic=max(x.toxic_personnel_areas_m2,default=0)
    injury=max(x.flammable_personnel_area_m2,toxic,x.nfnt_personnel_area_m2)
    return {"equipment_area_m2":x.flammable_equipment_area_m2,"personnel_area_m2":injury,
            "consequence_area_m2":max(x.flammable_equipment_area_m2,injury)}


class HoleValue(Model):
    hole: Literal["small","medium","large","rupture"]
    generic_frequency_per_year: NonNegative
    value: NonNegative


class Weighted(Model):
    holes: list[HoleValue] = Field(min_length=4,max_length=4)
    value_unit: str = Field(min_length=1,max_length=50)


@calculation("consequence/hole-weighted", "Generic-frequency weighted four-hole consequence", Weighted,
             ["Part 3 eqs (3.27)-(3.28),(3.68),(3.78),(3.86),(3.88),(3.94)"],
             limitations=["All four holes required; value may be area, repair cost, outage or spill volume. Already conditional consequences; no second event weighting."])
def hole_weighted(x):
    ensure({h.hole for h in x.holes}=={"small","medium","large","rupture"},"Exactly one value per hole is required")
    total=math.fsum(h.generic_frequency_per_year for h in x.holes)
    ensure(total>0,"Total generic frequency must be positive")
    return {"weighted_value":math.fsum(h.generic_frequency_per_year*h.value for h in x.holes)/total,"value_unit":x.value_unit}


class SurroundingCost(Model):
    equipment_area_m2: NonNegative
    replacement_cost_per_m2: NonNegative
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("financial/surrounding-damage", "Surrounding equipment damage cost", SurroundingCost,["Part 3 eq (3.87)"])
def surrounding_cost(x):
    return {"cost":x.equipment_area_m2*x.replacement_cost_per_m2,"currency":x.currency}


class ProductionCost(Model):
    component_outage_days: NonNegative
    surrounding_outage_days: NonNegative
    production_cost_per_day: NonNegative
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("financial/production-loss", "Business interruption cost", ProductionCost,["Part 3 eq (3.90)"])
def production_cost(x):
    return {"cost":(x.component_outage_days+x.surrounding_outage_days)*x.production_cost_per_day,"currency":x.currency}


class InjuryCost(Model):
    personnel_area_m2: NonNegative
    population_density_per_m2: NonNegative
    cost_per_injury: NonNegative
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("financial/injury", "Potential injury cost", InjuryCost,["Part 3 eq (3.91)"])
def injury_cost(x):
    return {"cost":x.personnel_area_m2*x.population_density_per_m2*x.cost_per_injury,"currency":x.currency}


class Spill(Model):
    released_mass_kg: NonNegative
    liquid_density_kg_m3: Positive
    evaporated_fraction: Fraction
    cleanup_cost_per_m3: NonNegative
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("financial/spill-cleanup", "Liquid spill remediation volume and cost", Spill,
             ["Part 3 eqs (3.93)-(3.94), expressed in m3"], limitations=["Caller must screen liquid phase, boiling point and ignition eligibility; evaporation fraction supplied. Cost basis is per m3, not per barrel."])
def spill(x):
    volume=x.released_mass_kg/x.liquid_density_kg_m3*(1-x.evaporated_fraction)
    return {"remediation_volume_m3":volume,"cost":volume*x.cleanup_cost_per_m3,"currency":x.currency}


class HoleFinancial(Model):
    """Financial consequence components for one API 581 release hole."""
    hole: Literal["small", "medium", "large", "rupture"]
    generic_frequency_per_year: NonNegative
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative


class FinancialByHole(Model):
    """Four-hole financial consequence roll-up on one declared basis."""
    holes: list[HoleFinancial] = Field(min_length=4, max_length=4)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis_year: int = Field(ge=1900, le=2200)


@calculation(
    "financial/hole-total",
    "Four-hole financial consequence and annual risk roll-up",
    FinancialByHole,
    ["Part 3 §§4.11-4.12; eqs (3.86)-(3.94)"],
    limitations=[
        "All five cost categories are caller-qualified on one currency and cost basis year.",
        "Per-hole generic frequencies must be disjoint and already include the applicable GFF basis; no second ignition or weather weighting is applied.",
        "The API does not infer damage applicability, release hydraulics, cleanup unit costs, or currency escalation.",
    ],
)
def financial_by_hole(x: FinancialByHole):
    ensure(
        {item.hole for item in x.holes} == {"small", "medium", "large", "rupture"},
        "Exactly one financial row for each of the four holes is required",
    )
    total_frequency = math.fsum(item.generic_frequency_per_year for item in x.holes)
    ensure(total_frequency > 0, "Total generic frequency must be positive")
    rows = []
    for item in x.holes:
        total = math.fsum((item.component_repair_cost, item.surrounding_equipment_cost,
                           item.business_interruption_cost, item.injury_cost,
                           item.environmental_cost))
        rows.append({"hole": item.hole, "generic_frequency_per_year": item.generic_frequency_per_year,
                     "financial_consequence": total})
    annual = math.fsum(row["generic_frequency_per_year"] * row["financial_consequence"] for row in rows)
    return {
        "currency": x.currency,
        "cost_basis_year": x.cost_basis_year,
        "total_generic_frequency_per_year": total_frequency,
        "per_hole": rows,
        "frequency_weighted_financial_consequence": annual / total_frequency,
        "annual_financial_risk": annual,
    }
