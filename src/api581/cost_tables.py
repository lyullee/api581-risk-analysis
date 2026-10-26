"""Part 3 Tables 4.15-4.18M and associated financial calculations."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure
from .pof import Component, generic, HOLES

REPAIR = {
    "COMPC":(10000,20000,100000,300000),"COMPR":(5000,10000,50000,100000),
    "HEXSS":(1000,2000,20000,60000),"HEXTS":(1000,2000,20000,60000),"HEXTUBE":(1000,2000,20000,60000),
    "PIPE-1":(5,0,0,20),"PIPE-2":(5,0,0,40),"PIPE-4":(5,10,0,60),"PIPE-6":(5,20,0,120),
    "PIPE-8":(5,30,60,180),"PIPE-10":(5,40,80,240),"PIPE-12":(5,60,120,360),"PIPE-16":(5,80,160,500),"PIPEGT16":(10,120,240,700),
    "PUMP2S":(1000,2500,5000,5000),"PUMP1S":(1000,2500,5000,5000),"PUMPR":(1000,2500,5000,10000),
    "TANKBOTTOM":(5000,0,0,120000),"COURSE-1-10":(5000,12000,20000,40000),
    "KODRUM":(5000,12000,20000,40000),"DRUM":(5000,12000,20000,40000),"FINFAN":(1000,2000,20000,60000),
    "FILTER":(1000,2000,4000,10000),"REACTOR":(10000,24000,40000,80000),
    "COLTOP":(10000,25000,50000,100000),"COLMID":(10000,25000,50000,100000),"COLBTM":(10000,25000,50000,100000)}

MATERIAL = {"carbon_steel":1,"1.25Cr-0.5Mo":1.3,"2.25Cr-1Mo":1.7,"5Cr-0.5Mo":1.7,"7Cr-0.5Mo":2,
    "clad_304_ss":2.1,"polypropylene_lined":2.5,"9Cr-1Mo":2.6,"405_ss":2.8,"410_ss":2.8,"304_ss":3.2,
    "clad_316_ss":3.3,"cs_saran_lined":3.4,"cs_rubber_lined":4.4,"316_ss":4.8,"cs_glass_lined":5.8,"clad_alloy_400":6.4,
    "90_10_CuNi":6.8,"clad_alloy_600":7,"cs_teflon_lined":7.8,"clad_nickel":8,"alloy_800":8.4,"70_30_CuNi":8.5,
    "904L":8.8,"alloy_20":11,"alloy_400":15,"alloy_600":15,"nickel":18,"alloy_625":26,"titanium":28,
    "alloy_C":29,"zirconium":34,"alloy_B":36,"tantalum":535}

OUTAGE = {"COMPC":(None,3,7,None),"COMPR":(None,3,7,None),"HEXSS":(2,3,3,10),"HEXTS":(2,3,3,10),
    "HEXTUBE":(None,None,None,None),"PIPE-1":(0,None,None,1),"PIPE-2":(0,None,None,1),"PIPE-4":(0,1,None,2),
    "PIPE-6":(0,1,2,3),"PIPE-8":(0,2,2,3),"PIPE-10":(0,2,2,4),"PIPE-12":(1,3,4,4),"PIPE-16":(1,3,4,5),"PIPEGT16":(1,4,5,7),
    "PUMP2S":(0,0,0,None),"PUMPR":(0,0,0,None),"PUMP1S":(0,0,0,None),"TANKBOTTOM":(5,None,None,50),
    "COURSE-1-10":(2,3,3,14),"KODRUM":(2,3,3,10),"FINFAN":(0,0,2,3),"FILTER":(0,1,2,3),"DRUM":(2,3,3,10),
    "REACTOR":(4,6,6,21),"COLTOP":(3,4,5,21),"COLMID":(3,4,5,21),"COLBTM":(3,4,5,21)}

# MW kg/kmol, tabulated liquid density kg/m3, NBP Celsius, fraction evaporated in 24h.
LEAK = {"C1-C2":(23,250.513,-125,1),"C3-C5":(58,580.012,-1,1),"C6-C8":(100,684.020,99,.9),
    "C9-C12":(149,734.014,184,.5),"C13-C16":(205,764.529,261,.1),"C17-C25":(280,775.021,344,.05),"C25+":(422,900.029,527,.02),
    "Acid":(18,997.950,100,.9),"H2":(2,71.010,-253,1),"H2S":(34,993.032,-59,1),"HF":(20,967.034,20,1),
    "CO":(28,800.923,-191,1),"DEE":(74,720.831,35,1),"HCL":(36,1185.366,-85,1),"Nitric Acid":(63,1521.754,121,.8),
    "NO2":(90,929.071,135,.75),"Phosgene":(99,1377.588,83,1),"TDI":(174,1217.403,251,.15),"Methanol":(32,800.923,65,1),
    "PO":(58,832.960,34,1),"Styrene":(104,683.988,145,.6),"EEA":(132,977.126,156,.65),"EE":(90,929.071,135,.75),
    "EG":(62,1105.274,197,.45),"EO":(44,881.015,0,1)}


@calculation("financial/repair-table", "2001 USD component repair cost table", Component,
             ["Part 3 Table 4.15; PDF p532"], limitations=["Historical 2001 USD, not current prices. COURSE-1-10 normalizes source COURSES-10 label."])
def repair_table(x):
    ensure(x.component_type in REPAIR,"Unsupported repair cost component")
    return {"cost_by_hole_usd_2001":dict(zip(HOLES,REPAIR[x.component_type])),"cost_basis_year":2001,"currency":"USD"}


class Material(Model):
    material_id: Literal[tuple(MATERIAL)]


@calculation("financial/material-factor", "Material repair cost multiplier", Material,["Part 3 Table 4.16; PDF p533"])
def material_factor(x):
    ensure(x.material_id in MATERIAL,"Unsupported material_id; inspect MODULE_CATALOG or table constants")
    return {"material_factor":MATERIAL[x.material_id]}


@calculation("financial/outage-table", "Estimated equipment outage table", Component,
             ["Part 3 Table 4.17; PDF p534"], limitations=["NA is returned as null, never zero. Historical estimates require owner review."])
def outage_table(x):
    ensure(x.component_type in OUTAGE,"Unsupported outage component")
    return {"days_by_hole":dict(zip(HOLES,OUTAGE[x.component_type]))}


class RepairCost(Model):
    component_type: str
    material_id: Literal[tuple(MATERIAL)]
    price_factor_since_2001: Positive
    usd_to_output_currency: Positive
    cost_basis_year: int = Field(ge=2001,le=2200)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("financial/component-repair", "GFF-weighted material-adjusted component repair cost", RepairCost,
             ["Part 3 eq (3.86), Tables 4.15/4.16"], limitations=["Inflation and currency conversion are explicit caller assumptions, not fetched market data. Non-tank GFF support only."])
def repair_cost(x):
    gff=generic(Component(component_type=x.component_type))
    costs=repair_table(Component(component_type=x.component_type))["cost_by_hole_usd_2001"]
    factor=material_factor(Material(material_id=x.material_id))["material_factor"]
    base=math.fsum(gff["by_hole_per_year"][h]*costs[h] for h in HOLES)/gff["total_per_year"]*factor
    return {"weighted_repair_cost_usd_2001":base,"cost":base*x.price_factor_since_2001*x.usd_to_output_currency,
            "material_factor":factor,"cost_basis_year":x.cost_basis_year,"currency":x.currency}


class ComponentOutage(Model):
    component_type: str
    outage_multiplier: Positive
    override_days: dict[Literal["small","medium","large","rupture"],NonNegative] = Field(default_factory=dict)


@calculation("financial/component-outage", "GFF-weighted component outage duration", ComponentOutage,
             ["Part 3 eq (3.88), Table 4.17"], limitations=["A nonzero-frequency hole with NA outage requires an explicit owner-supplied override; NA is not silently filled."])
def component_outage(x):
    gff=generic(Component(component_type=x.component_type))
    days=outage_table(Component(component_type=x.component_type))["days_by_hole"]
    days.update(x.override_days)
    terms=[]
    for h in HOLES:
        frequency=gff["by_hole_per_year"][h]
        ensure(days[h] is not None or frequency==0,f"Outage NA for nonzero-frequency hole {h}; supply override_days", "missing_outage_override")
        terms.append(frequency*(days[h] if days[h] is not None else 0))
    return {"component_outage_days":math.fsum(terms)/gff["total_per_year"]*x.outage_multiplier,"effective_days_by_hole":days}


class SurroundingOutage(Model):
    surrounding_damage_cost_usd: NonNegative


@calculation("financial/surrounding-outage", "Surrounding equipment repair outage correlation", SurroundingOutage,
             ["Part 3 eq (3.89); PDF p506"], limitations=["USD cost input only; correlation monetary basis must be consistent with the source methodology. Zero damage cost returns the continuous limit 0 days."])
def surrounding_outage(x):
    # Algebraic power form equals 10**(1.242+.585*log10(cost*1e-6)), and handles cost=0.
    return {"surrounding_outage_days":10**1.242*(x.surrounding_damage_cost_usd/1e6)**.585}


class LeakProperties(Model):
    fluid: Literal[tuple(LEAK)]


@calculation("properties/leak-table", "Tabulated SI leak/remediation properties", LeakProperties,
             ["Part 3 Table 4.18M; PDF p536"], limitations=["Table liquid density for remediation, not operating gas density or a thermodynamic property solver. Source C3-C5 label is retained and not silently aliased to C3-C4."])
def leak_properties(x):
    ensure(x.fluid in LEAK,"Unsupported leak-properties fluid")
    mw,density,nbp,evap=LEAK[x.fluid]
    return {"molecular_weight_kg_kmol":mw,"tabulated_liquid_density_kg_m3":density,"normal_boiling_point_k":nbp+273.15,
            "evaporated_fraction_24h":evap}


class CleanupEligibility(Model):
    release_phase: Literal["gas","liquid"]
    normal_boiling_point_k: Positive
    autoignition_likely: bool


@calculation("financial/cleanup-eligibility", "Level 1 environmental cleanup screening", CleanupEligibility,
             ["Part 3 §4.12.6"], limitations=["Uses the text's rounded 93 Celsius threshold; source also states 200 Fahrenheit. Screening only; no cost or evaporation-rate model."])
def cleanup_eligibility(x):
    eligible=x.release_phase=="liquid" and x.normal_boiling_point_k>=366.15 and not x.autoignition_likely
    return {"include_cleanup_cost":eligible}


class FinancialConsequence(Model):
    repair: RepairCost
    outage: ComponentOutage
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    equipment_cost_per_m2: NonNegative
    production_cost_per_day: NonNegative
    population_density_per_m2: NonNegative
    cost_per_injury: NonNegative
    weighted_cleanup_volume_m3: NonNegative
    cleanup_cost_per_m3: NonNegative


@calculation("financial/level1-consequence", "Compose five Level 1 financial consequence categories", FinancialConsequence,
             ["Part 3 §§4.12.2-4.12.7 eqs (3.85)-(3.94)"],
             limitations=["Input areas and remediation volume must already be hole-weighted and screened. All user monetary inputs use repair.currency and repair.cost_basis_year. Surrounding-outage correlation receives equivalent 2001 USD via the explicit price/currency factors."])
def financial_consequence(x):
    ensure(x.repair.component_type==x.outage.component_type,"Repair and outage component types must match")
    repair=repair_cost(x.repair)
    outage=component_outage(x.outage)
    surrounding=x.equipment_area_m2*x.equipment_cost_per_m2
    reference_cost=surrounding/x.repair.usd_to_output_currency/x.repair.price_factor_since_2001
    downtime=surrounding_outage(SurroundingOutage(surrounding_damage_cost_usd=reference_cost))["surrounding_outage_days"]
    production=(outage["component_outage_days"]+downtime)*x.production_cost_per_day
    injury=x.personnel_area_m2*x.population_density_per_m2*x.cost_per_injury
    environment=x.weighted_cleanup_volume_m3*x.cleanup_cost_per_m3
    return {"component_repair_cost":repair["cost"],"surrounding_equipment_cost":surrounding,
            "business_interruption_cost":production,"injury_cost":injury,"environmental_cost":environment,
            "component_outage_days":outage["component_outage_days"],"surrounding_outage_days":downtime,
            "surrounding_cost_reference_usd_2001":reference_cost,
            "financial_consequence":math.fsum([repair["cost"],surrounding,production,injury,environment]),
            "currency":x.repair.currency,"cost_basis_year":x.repair.cost_basis_year}
