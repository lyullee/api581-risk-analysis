"""Four-hole Level 1 aggregation with mechanism selection after frequency weighting."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, calculation, ensure
from .pof import Component, generic
from .consequences import HoleValue, Weighted, hole_weighted, FinalArea, final_area


class HoleAreas(Model):
    hole: Literal["small","medium","large","rupture"]
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative


class Summary(Model):
    component_type: str
    holes: list[HoleAreas] = Field(min_length=4,max_length=4)


@calculation("level1/consequence-summary", "Four-hole mechanism-weighted final consequence areas", Summary,
             ["Part 3 eqs (3.27)-(3.28),(3.68),(3.78),(3.81)-(3.84)"],
             limitations=["Caller supplies complete per-hole mechanism consequences, already event-weighted. GFF table supports non-tank components. Mechanism areas are frequency-weighted before final maximum selection."])
def summary(x):
    ensure({h.hole for h in x.holes}=={"small","medium","large","rupture"},"Exactly one consequence per hole is required")
    frequencies=generic(Component(component_type=x.component_type))
    values={}
    for name in ["flammable_equipment_area_m2","flammable_personnel_area_m2","toxic_personnel_area_m2","nfnt_personnel_area_m2"]:
        weighted=hole_weighted(Weighted(value_unit="m2",holes=[HoleValue(hole=h.hole,generic_frequency_per_year=frequencies["by_hole_per_year"][h.hole],value=getattr(h,name)) for h in x.holes]))
        values[name]=weighted["weighted_value"]
    result=final_area(FinalArea(flammable_equipment_area_m2=values["flammable_equipment_area_m2"],
                     flammable_personnel_area_m2=values["flammable_personnel_area_m2"],
                     toxic_personnel_areas_m2=[values["toxic_personnel_area_m2"]],nfnt_personnel_area_m2=values["nfnt_personnel_area_m2"]))
    return {**values,**result,"generic_frequency_per_year":frequencies["total_per_year"]}
