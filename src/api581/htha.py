"""HTHA partial-pressure, bounded screening and damage table."""
from typing import Literal
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure


class HydrogenPressure(Model):
    total_pressure_pa_abs: Positive
    hydrogen_mole_fraction: Fraction


@calculation("properties/hydrogen-partial-pressure", "Hydrogen ideal-mixture partial pressure", HydrogenPressure,
             ["Part 2 Table 19.1; PDF p259"], limitations=["Mole fraction times total absolute pressure; not a fugacity model."])
def partial_pressure(x):
    return {"hydrogen_partial_pressure_pa_abs":x.total_pressure_pa_abs*x.hydrogen_mole_fraction}


class HthaDamage(Model):
    susceptibility: Literal["damage_observed","high","medium","low","none"]


@calculation("damage/htha-factor", "HTHA susceptibility damage factor", HthaDamage,
             ["Part 2 Table 19.2; PDF p260"], limitations=["Qualified susceptibility supplied; historical exposure and pre-1970 fabrication may require more conservative owner review."])
def htha_factor(x):
    return {"damage_factor":{"damage_observed":5000,"high":5000,"medium":2000,"low":100,"none":0}[x.susceptibility]}


class CarbonHtha(Model):
    material_group: Literal["carbon_steel","c_half_mo"]
    exposure_temperature_k: Positive
    hydrogen_partial_pressure_pa_abs: NonNegative
    damage_history: Literal["none","observed_not_replaced","replaced_in_kind","upgraded_material"]


@calculation("damage/htha-carbon-screen", "Carbon/C-half-Mo HTHA screening and factor", CarbonHtha,
             ["Part 2 §19.6.3 STEP 1-4; PDF pp258-260"],
             limitations=["Current material must match material_group. Uses printed SI 177 C and 0.345 MPa thresholds. Mixed high/low temperature-pressure cases are not assigned by the printed carbon-steel rules and require engineering review. Cr-Mo/API 941 curve screening is separate."])
def carbon_htha(x):
    if x.damage_history=="observed_not_replaced": susceptibility="damage_observed"
    elif x.damage_history=="replaced_in_kind": susceptibility="high"
    else:
        hot=x.exposure_temperature_k>450.15
        high_pressure=x.hydrogen_partial_pressure_pa_abs>345000
        ensure(hot==high_pressure,"Mixed HTHA temperature/pressure threshold case requires engineering review", "unresolved_applicability")
        susceptibility="high" if hot else "none"
    return {"susceptibility":susceptibility,**htha_factor(HthaDamage(susceptibility=susceptibility))}
