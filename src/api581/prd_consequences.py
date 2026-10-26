"""Part 1 §§7.4-7.6 PRD leakage consequences and risk integration."""
import math
from typing import Literal
from pydantic import Field, StrictBool
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

Discharge = Literal["atmosphere", "flare", "closed_system"]
LeakModel = Literal["two_case_equations", "three_case_table_7_15"]
LeakRiskBasis = Literal["annual_frequency", "source_cumulative_probability"]


class MoneyBasis(Model):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis_year: int = Field(strict=True,ge=1900,le=2200)


def _money(x):
    return {"currency":x.currency,"cost_basis_year":x.cost_basis_year}


class LeakageRates(Model):
    operating_capacity_kg_s: Positive


@calculation("prd/leakage-rates", "PRD minor/moderate/combined/stuck-open leakage rates", LeakageRates,
             ["Part 1 §7.5.2; eqs(1.40)-(1.41); Table7.15; PDF pp66,88"],
             limitations=["Capacity must be evaluated at normal operating conditions, not silently copied from a relief-condition rating. Eq(1.40) uses 1% for combined mild/moderate; Table7.15 uses 1% minor and 10% moderate. Both are returned explicitly. API520 capacity sizing is not implemented here."])
def leakage_rates(x):
    return {"minor_rate_kg_s":.01*x.operating_capacity_kg_s,
            "moderate_table_rate_kg_s":.1*x.operating_capacity_kg_s,
            "mild_moderate_equation_rate_kg_s":.01*x.operating_capacity_kg_s,
            "stuck_open_rate_kg_s":.25*x.operating_capacity_kg_s}


class LeakageDuration(Model):
    inlet_size_nps: Positive
    discharge: Discharge


@calculation("prd/leakage-duration", "PRD size/discharge leakage duration", LeakageDuration,
             ["Part 1 Table7.14; eq(1.42); PDF pp67,88"],
             limitations=["NPS is a nominal inlet designation, not a measured diameter in metres. Table duration days are converted exactly to seconds (including printed .33 days). Stuck-open duration uses exact30 minutes=1800s, not rounded .021 days."])
def leakage_duration(x):
    row = sum(x.inlet_size_nps > b for b in (.75,1.5,3,6))
    days = ((8,4,2,1,.33) if x.discharge == "atmosphere" else (60,30,15,7,2))[row]
    return {"mild_moderate_duration_s":days*86400,"stuck_open_duration_s":1800}


class InventoryRecovery(Model):
    discharge: Discharge
    flare_recovery_installed: StrictBool = False


@calculation("prd/inventory-loss-factor", "PRD residual inventory loss factor after recovery", InventoryRecovery,
             ["Part 1 §7.5.4; PDF p67"],
             limitations=["Factor Fr multiplies lost-inventory cost: closed system0, flare with recovery .5, otherwise1. It does not reduce physical leaked mass or environmental/repair/production costs."])
def inventory_recovery(x):
    ensure(not x.flare_recovery_installed or x.discharge == "flare", "Flare recovery is only applicable to flare discharge")
    return {"inventory_loss_factor":0 if x.discharge == "closed_system" else (.5 if x.flare_recovery_installed else 1)}


class InventoryLoss(MoneyBasis):
    leakage_rate_kg_s: NonNegative
    duration_s: NonNegative
    fluid_cost_per_kg: NonNegative
    inventory_loss_factor: Fraction


@calculation("prd/inventory-loss", "PRD leakage inventory mass and financial loss", InventoryLoss,
             ["Part 1 §7.5.5; eqs(1.43)-(1.44); PDF p67"],
             limitations=["SI mass rate kg/s times seconds replaces source hourly-rate/day factor24. Fluid value must correspond to the protected equipment at the PRD location. Constant supplied operating-capacity leak; no automatic finite inventory/supply limit."])
def inventory_loss(x):
    mass = x.leakage_rate_kg_s*x.duration_s
    residual = mass*x.inventory_loss_factor
    return {"leaked_mass_kg":mass,"inventory_loss_equivalent_mass_kg":residual,
            "inventory_loss_cost":residual*x.fluid_cost_per_kg,**_money(x)}


class ReferenceRepair(MoneyBasis):
    inlet_size_nps: Positive
    price_index_multiplier: Positive
    output_currency_per_usd: Positive


@calculation("prd/repair-cost", "PRD reference repair quote adjusted to declared price basis", ReferenceRepair,
             ["Part 1 §7.5.7; PDF p67"],
             limitations=["Printed reference USD1000 below NPS6, USD2000 at/above NPS6. Price quote year is not inferred from edition year; explicit owner-qualified price index and FX required. Actual work-order cost is preferred and can be supplied directly to leakage-consequence."])
def repair_cost(x):
    reference = 1000 if x.inlet_size_nps < 6 else 2000
    return {"reference_cost_usd":reference,"repair_cost":reference*x.price_index_multiplier*x.output_currency_per_usd,**_money(x)}


class ProductionLoss(MoneyBasis):
    daily_production_margin: NonNegative
    shutdown_duration_days: NonNegative
    leak_case: Literal["mild_moderate", "stuck_open"]
    mild_leak_tolerated_or_online_repair: StrictBool


@calculation("prd/production-loss", "PRD leakage shutdown production loss", ProductionLoss,
             ["Part 1 §7.5.8; eqs(1.45)-(1.47); PDF pp67-68"],
             limitations=["Mild/moderate leak tolerated or isolated/repaired online has zero production loss. Stuck-open case uses shutdown loss per eq(1.47). Caller supplies actual shutdown duration and production margin, including any qualified zero-duration repair."])
def production_loss(x):
    required = x.leak_case == "stuck_open" or not x.mild_leak_tolerated_or_online_repair
    return {"production_loss_cost":x.daily_production_margin*x.shutdown_duration_days if required else 0,
            "shutdown_loss_applied":required,**_money(x)}


class LeakageConsequence(MoneyBasis):
    operating_capacity_kg_s: Positive
    inlet_size_nps: Positive
    discharge: Discharge
    flare_recovery_installed: StrictBool = False
    fluid_cost_per_kg: NonNegative
    environmental_cost: NonNegative
    repair_cost: NonNegative
    daily_production_margin: NonNegative
    shutdown_duration_days: NonNegative
    mild_leak_tolerated_or_online_repair: StrictBool
    model_basis: LeakModel


@calculation("prd/leakage-consequence", "PRD two/three-case leakage financial consequence", LeakageConsequence,
             ["Part 1 §7.5.10; eqs(1.39)-(1.50); Tables7.14,7.15; PDF pp66-69,88"],
             origin="api581_equations_with_explicit_source_discrepancy_choice",
             limitations=["Caller explicitly selects two_case_equations (.9 at1% capacity + .1 stuck at25%) or three_case_table_7_15 (.5 at1%, .4 at10%, .1 at25%) because source rates conflict. Non-stuck cases share Table7.14 duration. Environmental and repair costs are common conditional case costs as printed. All monetary inputs share declared currency/year; no automatic price-year inference or supply/inventory cap."])
def leakage_consequence(x):
    rates = leakage_rates(LeakageRates(operating_capacity_kg_s=x.operating_capacity_kg_s))
    duration = leakage_duration(LeakageDuration(inlet_size_nps=x.inlet_size_nps,discharge=x.discharge))
    recovery = inventory_recovery(InventoryRecovery(discharge=x.discharge,flare_recovery_installed=x.flare_recovery_installed))["inventory_loss_factor"]
    cases = ({"mild_moderate":(.9,rates["mild_moderate_equation_rate_kg_s"]),"stuck_open":(.1,rates["stuck_open_rate_kg_s"])}
             if x.model_basis == "two_case_equations" else
             {"minor":(.5,rates["minor_rate_kg_s"]),"moderate":(.4,rates["moderate_table_rate_kg_s"]),"stuck_open":(.1,rates["stuck_open_rate_kg_s"])})
    costs,weights = {},{}
    for name,(weight,rate) in cases.items():
        stuck = name == "stuck_open"
        seconds = duration["stuck_open_duration_s" if stuck else "mild_moderate_duration_s"]
        inv = inventory_loss(InventoryLoss(leakage_rate_kg_s=rate,duration_s=seconds,fluid_cost_per_kg=x.fluid_cost_per_kg,
            inventory_loss_factor=recovery,**_money(x)))
        prod = production_loss(ProductionLoss(daily_production_margin=x.daily_production_margin,
            shutdown_duration_days=x.shutdown_duration_days,leak_case="stuck_open" if stuck else "mild_moderate",
            mild_leak_tolerated_or_online_repair=x.mild_leak_tolerated_or_online_repair,**_money(x)))
        total = inv["inventory_loss_cost"]+prod["production_loss_cost"]+x.environmental_cost+x.repair_cost
        costs[name] = {"leakage_rate_kg_s":rate,"duration_s":seconds,"leaked_mass_kg":inv["leaked_mass_kg"],
                       "inventory_loss_cost":inv["inventory_loss_cost"],"production_loss_cost":prod["production_loss_cost"],
                       "environmental_cost":x.environmental_cost,"repair_cost":x.repair_cost,"financial_consequence":total}
        weights[name] = weight
    return {"financial_consequence":math.fsum(weights[k]*v["financial_consequence"] for k,v in costs.items()),
            "case_weights":weights,"costs_by_case":costs,"inventory_loss_factor":recovery,"model_basis":x.model_basis,**_money(x)}


class MultipleDevicePressure(Model):
    analyzed_orifice_area_m2: Positive
    total_installed_orifice_area_m2: Positive
    scenario_pressure_pa_gauge: NonNegative


@calculation("prd/multiple-device-pressure", "Multiple PRD area-based protected-equipment pressure adjustment", MultipleDevicePressure,
             ["Part 1 §7.4.4; eqs(1.37)-(1.38); PDF pp64-65"],
             limitations=["Total installed area includes analyzed PRD. Fa=max(.25,sqrt(Aprd/Atotal)). Reduced pressure is used for protected-equipment LOC and consequence calculations only; original scenario pressure must be retained for Fop (PRD POFOD). Source square-root approximation is not an independent parallel-failure probability or a capacity-design verification."])
def multiple_device_pressure(x):
    ensure(x.analyzed_orifice_area_m2 <= x.total_installed_orifice_area_m2, "Total installed orifice area must include analyzed device")
    factor = max(.25,math.sqrt(x.analyzed_orifice_area_m2/x.total_installed_orifice_area_m2))
    return {"multiple_device_factor":factor,"protected_equipment_pressure_pa_gauge":factor*x.scenario_pressure_pa_gauge,
            "unreduced_pressure_for_fop_pa_gauge":x.scenario_pressure_pa_gauge}


class FailRiskCase(Model):
    case_id: str = Field(min_length=1,max_length=100)
    annual_failure_frequency: NonNegative
    financial_consequence: NonNegative


class ProtectedRisk(Model):
    equipment_id: str = Field(min_length=1,max_length=200)
    cases: list[FailRiskCase] = Field(min_length=1,max_length=100)


class FailRisk(MoneyBasis):
    protected_equipment: list[ProtectedRisk] = Field(min_length=1,max_length=100)


@calculation("prd/fail-risk", "PRD fail-to-open case sum and protected-equipment maximum risk", FailRisk,
             ["Part 1 §7.6.1; eqs(1.51)-(1.52); PDF p69"],
             limitations=["Within each protected item, sum distinct demand-case frequency*conditional consequence. Then take maximum across protected items as prescribed, not their sum. Caller supplies qualified case frequencies and pressure-dependent COF; currency/year must be common."])
def fail_risk(x):
    ensure(len({e.equipment_id for e in x.protected_equipment}) == len(x.protected_equipment), "Duplicate protected equipment ID")
    values = {}
    for equipment in x.protected_equipment:
        ensure(len({c.case_id for c in equipment.cases}) == len(equipment.cases), "Duplicate demand case ID within protected equipment")
        values[equipment.equipment_id] = math.fsum(c.annual_failure_frequency*c.financial_consequence for c in equipment.cases)
    maximum = max(values.values())
    return {"protected_equipment_risks_per_year":values,"maximum_fail_risk_per_year":maximum,
            "governing_equipment_ids":[k for k,v in values.items() if v == maximum],**_money(x)}


class LeakageRisk(MoneyBasis):
    leakage_measure: NonNegative
    financial_consequence: NonNegative
    measure_basis: LeakRiskBasis


@calculation("prd/leakage-risk", "PRD leakage consequence weighted by declared probability/frequency basis", LeakageRisk,
             ["Part 1 §7.6.2; eq(1.53); PDF p69"],
             limitations=["Source multiplies leakage Weibull cumulative probability by consequence but uses annual-risk terminology. Basis must be explicit: source_cumulative_probability gives monetary probability-weighted consequence; annual_frequency requires an independently qualified annual event frequency. No silent CDF annualization."])
def leakage_risk(x):
    ensure(x.measure_basis != "source_cumulative_probability" or x.leakage_measure <= 1, "Cumulative leakage probability must not exceed1")
    return {"leakage_risk_value":x.leakage_measure*x.financial_consequence,
            "measure_basis":x.measure_basis,"risk_unit":"currency/year" if x.measure_basis == "annual_frequency" else "currency",**_money(x)}


class TotalRisk(MoneyBasis):
    fail_risk_per_year: NonNegative
    leakage_risk_value: NonNegative
    leakage_measure_basis: LeakRiskBasis


@calculation("prd/total-risk", "PRD combined risk with explicit dimensional basis", TotalRisk,
             ["Part 1 §7.6.3; eq(1.54); PDF p69"],
             origin="api581_aggregation_with_explicit_measure_basis",
             limitations=["Annual leakage-frequency basis permits an annual total. Source cumulative-probability basis reproduces printed addition only as source_total_risk_index and leaves annual_financial_risk unset, because summands have inconsistent dimensions. Source index must not be presented as a certified monetary annual rate."])
def total_risk(x):
    combined = x.fail_risk_per_year+x.leakage_risk_value
    annual = x.leakage_measure_basis == "annual_frequency"
    return {"annual_financial_risk":combined if annual else None,"source_total_risk_index":None if annual else combined,
            "leakage_measure_basis":x.leakage_measure_basis,**_money(x)}


class RiskAssessment(FailRisk):
    leakage_measure: NonNegative
    leakage_financial_consequence: NonNegative
    leakage_measure_basis: LeakRiskBasis


@calculation("prd/risk-assessment", "Compose protected-item fail risk and PRD leakage risk", RiskAssessment,
             ["Part 1 §7.6.4; eqs(1.51)-(1.54); PDF pp69-70"],
             origin="api581_aggregation_with_explicit_measure_basis",
             limitations=["Integration over supplied case frequencies, protected-item conditional consequences and leakage measure/consequence. It does not automatically derive complete relief design or COF. Fail risk takes max across protected items. Cumulative leakage basis yields source index only; annual total requires qualified leakage annual frequency."])
def risk_assessment(x):
    failed = fail_risk(FailRisk(protected_equipment=x.protected_equipment,**_money(x)))
    leak = leakage_risk(LeakageRisk(leakage_measure=x.leakage_measure,financial_consequence=x.leakage_financial_consequence,
        measure_basis=x.leakage_measure_basis,**_money(x)))
    total = total_risk(TotalRisk(fail_risk_per_year=failed["maximum_fail_risk_per_year"],leakage_risk_value=leak["leakage_risk_value"],
        leakage_measure_basis=x.leakage_measure_basis,**_money(x)))
    return {**failed,**total,"leakage_risk_value":leak["leakage_risk_value"],"leakage_risk_unit":leak["risk_unit"]}
