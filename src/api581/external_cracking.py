"""Austenitic external and CUI chloride SCC, Part 2 §§17-18."""
import math
from typing import Literal
from .core import Model, NonNegative, calculation, ensure
from .external_corrosion import RateQuery, DRIVERS, CoatingExposure, coating_exposure
from .scc_mechanisms import Assessment
from .pof import InspectionEquivalent, inspection_equivalent
from .cracking import SccBase, scc_base


class SusceptibilityQuery(RateQuery):
    mechanism: Literal["external_clscc","cui_clscc"]


@calculation("damage/external-clscc-base-susceptibility", "External/CUI CLSCC climate-temperature base susceptibility", SusceptibilityQuery,
             ["Part 2 Tables 17.2,18.2; PDF pp249,255"],
             limitations=["Eligible austenitic material/service required. CUI complexity/condition/chloride adjustments not included. Source rows overlap at 93 C, requiring manual classification."])
def base_susceptibility(x):
    t=x.temperature_k-273.15
    ensure(not math.isclose(t,93,abs_tol=1e-9,rel_tol=0),"Source temperature rows overlap at 93 C", "ambiguous_source")
    if t<49 or t>149: level="none"
    else:
        column=DRIVERS.index(x.driver)
        if x.mechanism=="external_clscc": rows=[("medium","low","none","high"),("low","low","none","medium")]
        else: rows=[("high","medium","low","high"),("medium","low","none","high")]
        level=rows[t>93][column]
    return {"base_susceptibility":level}


class CrackingAssessment(Assessment):
    coating_age_years: NonNegative
    coating_quality: Literal["none_or_poor","medium","high"]


def assess(x):
    ensure(not x.unrepaired_cracks,"Unrepaired cracking requires FFS evaluation", "ffs_required")
    level="high" if x.confirmed_cracking else x.susceptibility
    svi={"none":0,"low":1,"medium":10,"high":50}[level]
    counts=inspection_equivalent(InspectionEquivalent(mechanism="external_clscc",**x.inspections.model_dump()))
    grade,count="E",0
    for letter in "abcd":
        if counts[letter]: grade,count=letter.upper(),counts[letter]; break
    ensure(count<=6,"Equivalent inspection count exceeds source table support")
    base=scc_base(SccBase(severity_index=svi,inspection_grade=grade,inspection_count=count))["base_damage_factor"]
    exposure=coating_exposure(CoatingExposure(years_since_thickness_reading=x.years_since_qualifying_inspection,
                              coating_age_years=x.coating_age_years,coating_quality=x.coating_quality))
    age_factor=max(exposure["corrosion_exposure_years"],1)**1.1
    return {"effective_susceptibility":level,"severity_index":svi,"equivalent_inspection_grade":grade,
            "equivalent_inspection_count":count,"base_damage_factor":base,"age_factor":age_factor,
            "coating_credit_years":exposure["coating_credit_years"],"cracking_exposure_years":exposure["corrosion_exposure_years"],
            "damage_factor":base*age_factor}


@calculation("damage/external-clscc", "External chloride SCC damage factor", CrackingAssessment,
             ["Part 2 §17.6.3 eqs (2.68)-(2.76), Table 17.3"], limitations=["Qualified susceptibility and inspection age supplied; eligible material/service screening is separate. External severity scale differs from internal CLSCC."])
def external_clscc(x):
    return assess(x)


@calculation("damage/cui-clscc", "Chloride SCC under insulation damage factor", CrackingAssessment,
             ["Part 2 §18.6.3 eqs (2.77)-(2.85), Table 17.3"], limitations=["Caller supplies susceptibility AFTER complexity, insulation-condition and chloride adjustments. Eligible material/service screening remains separate."])
def cui_clscc(x):
    return assess(x)
