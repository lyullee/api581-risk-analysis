"""AST component financial consequence and uniform-DF financial risk composition."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .pof import Management, management
from .cost_tables import REPAIR, MATERIAL, OUTAGE, SurroundingOutage, surrounding_outage
from .tank_environment import (
    HOLES, Hole, FrequencyWeights, _weights, BottomEnvironment, ShellEnvironment,
    bottom_environment, shell_environment, BottomRepair, bottom_repair,
)

TankType = Literal["TANKBOTTOM", "COURSE-1-10"]
_GFF = {"TANKBOTTOM": (7.2e-4, 0., 0., 2e-6), "COURSE-1-10": (7e-5, 2.5e-5, 5e-6, 1e-7)}
_PRINTED_TOTAL = {"TANKBOTTOM": 7.2e-4, "COURSE-1-10": 1e-4}


def _product(*values):
    if any(v == 0 for v in values):
        return 0.
    value = math.prod(values)
    ensure(math.isfinite(value) and value > 0, "Positive product outside numerical range", "numerical_failure")
    return value


class TankComponent(Model):
    component_type: TankType


@calculation("tank/generic-frequency", "AST generic frequencies with explicit equation-summed total", TankComponent,
    ["Part2 Table3.1; Part3 eq(3.208); PDF pp147,593"], limitations=[
        "Uses the sum of four hole frequencies authorized by eq3.208. Printed tank totals differ and are returned separately; this is not an authorized correction of Table3.1. COURSE-1-10 is one shell-course component, not the whole tank or ten multiplied courses."])
def generic_frequency(x):
    values = _GFF[x.component_type]
    total = math.fsum(values)
    printed = _PRINTED_TOTAL[x.component_type]
    return {"by_hole_per_year": dict(zip(HOLES, values)), "total_per_year": total,
            "printed_total_per_year": printed, "sum_minus_printed_per_year": total-printed,
            "total_basis": "hole_sum_eq3_208"}


class TankOutage(FrequencyWeights):
    component_type: TankType
    outage_multiplier: Positive
    override_days: dict[Hole, NonNegative] = Field(default_factory=dict)


@calculation("tank/component-outage", "AST GFF-weighted component outage duration", TankOutage,
    ["Part3 eq(3.88),Table4.17,§6.12; PDF pp506,534,599-601"], limitations=[
        "All four qualified per-hole GFF are supplied by caller and normalized by their sum. Source NA is not zero: nonzero-frequency NA requires owner override. Zero-frequency NA contributes zero. No automatic diameter correction of outage duration."])
def component_outage(x):
    weights = _weights(x)
    days = dict(zip(HOLES, OUTAGE[x.component_type]))
    days.update(x.override_days)
    for h in HOLES:
        ensure(days[h] is not None or x.generic_frequency_by_hole_per_year[h] == 0,
               f"Outage NA for nonzero-frequency hole {h}; supply override_days", "missing_outage_override")
    value = math.fsum(weights[h]*(days[h] if days[h] is not None else 0) for h in HOLES)*x.outage_multiplier
    return {"component_outage_days": value, "effective_days_by_hole": days}


class TankRepairBasis(Model):
    material_id: Literal[tuple(MATERIAL)]
    price_factor_since_2001: Positive
    usd_to_output_currency: Positive
    cost_basis_year: int = Field(ge=2001, le=2200)


class OperatingCosts(Model):
    repair: TankRepairBasis
    outage_multiplier: Positive
    override_outage_days: dict[Hole, NonNegative] = Field(default_factory=dict)
    production_cost_per_day: NonNegative
    generic_frequency_source: str = Field(min_length=1, max_length=500)


class BottomFinancial(BottomEnvironment, OperatingCosts):
    tank_diameter_m: Positive


class ShellFinancial(ShellEnvironment, OperatingCosts):
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    equipment_cost_per_m2: NonNegative
    population_density_per_m2: NonNegative
    cost_per_injury: NonNegative


_FIN_LIMITS = [
    "Per-hole GFF, release volumes and qualified environmental costs are supplied inputs. Environment, production, surrounding-equipment and injury unit costs must use the declared currency and repair.cost_basis_year; cost_basis records the common valuation. Table6.6 has no stated price year and must be qualified explicitly before combining with escalated USD2001 repair costs.",
    "Component-only consequence. Damage applicability, release hydraulics, consequence areas and monetary qualification are not inferred. Per-hole frequencies normalize once including rupture. No additional ignition weighting or automatic whole-tank course summation.",
]


def _environment(x, cls, fn):
    # Only original validated fields enter a submodel; no derived values are coerced.
    return fn(cls(**{k: getattr(x, k) for k in cls.model_fields}))


def _outage(x, component_type):
    ensure(bool(x.generic_frequency_source.strip()), "Generic frequency source must be nonblank")
    return component_outage(TankOutage(component_type=component_type,
        generic_frequency_by_hole_per_year=x.generic_frequency_by_hole_per_year,
        outage_multiplier=x.outage_multiplier, override_days=x.override_outage_days))["component_outage_days"]


def _repair(x, component_type):
    weights = _weights(x)
    if component_type == "TANKBOTTOM":
        reference = bottom_repair(BottomRepair(
            generic_frequency_by_hole_per_year=x.generic_frequency_by_hole_per_year,
            tank_diameter_m=x.tank_diameter_m, repair_cost_by_hole=dict(zip(HOLES, REPAIR[component_type])),
            material_factor=MATERIAL[x.repair.material_id], currency="USD", cost_basis="Table4.15 USD2001"))["component_repair_cost"]
    else:
        reference = math.fsum(weights[h]*v for h,v in zip(HOLES, REPAIR[component_type]))*MATERIAL[x.repair.material_id]
    return _product(reference, x.repair.price_factor_since_2001, x.repair.usd_to_output_currency)


def _result(x, repair, outage, environment, surrounding=0., surrounding_days=0., injury=0., reference_surrounding=0.):
    production = _product(outage+surrounding_days, x.production_cost_per_day)
    return {"component_repair_cost": repair, "surrounding_equipment_cost": surrounding,
            "business_interruption_cost": production, "injury_cost": injury, "environmental_cost": environment["environment_cost"],
            "component_outage_days": outage, "surrounding_outage_days": surrounding_days,
            "surrounding_cost_reference_usd_2001": reference_surrounding,
            "leak_environment_cost": environment["leak_environment_cost"], "rupture_environment_cost": environment["rupture_environment_cost"],
            "financial_consequence": math.fsum([repair, surrounding, production, injury, environment["environment_cost"]]),
            "currency": x.currency, "cost_basis_year": x.repair.cost_basis_year, "cost_basis": x.cost_basis}


@calculation("tank/bottom-financial-consequence", "Compose AST bottom repair, production and environmental consequence", BottomFinancial,
    ["Part3 §6.12.3,eqs(3.88),(3.90),(3.243)-(3.250); PDF pp506,600-601"], limitations=_FIN_LIMITS+[
        "Bottom surrounding-equipment and injury costs are not applicable per §6.12.3 and returned zero. Rupture repair alone scales by diameter squared. Groundwater uses printed detection time, not inventory depletion time."])
def bottom_financial(x):
    environment = _environment(x, BottomEnvironment, bottom_environment)
    outage = _outage(x, "TANKBOTTOM")
    return _result(x, _repair(x, "TANKBOTTOM"), outage, environment)


@calculation("tank/shell-financial-consequence", "Compose five AST shell-course financial consequence categories", ShellFinancial,
    ["Part3 §6.12.2,eqs(3.85)-(3.91),(3.231)-(3.243); PDF pp505-506,599-600"], limitations=_FIN_LIMITS+[
        "Areas must already be GFF-weighted from a qualified AST flammable/toxic assessment. No automatic AST NFNT area is inferred. Surrounding-outage correlation uses equivalent USD2001 via explicit escalation/FX factors; damage area is not converted again."])
def shell_financial(x):
    environment = _environment(x, ShellEnvironment, shell_environment)
    outage = _outage(x, "COURSE-1-10")
    surrounding = _product(x.equipment_area_m2, x.equipment_cost_per_m2)
    reference = surrounding/x.repair.usd_to_output_currency/x.repair.price_factor_since_2001
    ensure(math.isfinite(reference), "Reference surrounding cost overflow", "numerical_failure")
    ensure(reference > 0 or surrounding == 0, "Reference surrounding cost underflow", "numerical_failure")
    days = surrounding_outage(SurroundingOutage(surrounding_damage_cost_usd=reference))["surrounding_outage_days"]
    injury = _product(x.personnel_area_m2, x.population_density_per_m2, x.cost_per_injury)
    return _result(x, _repair(x, "COURSE-1-10"), outage, environment, surrounding, days, injury, reference)


class DamageBasis(Model):
    management_score: NonNegative = Field(le=1000)
    total_damage_factor: NonNegative
    damage_factor_source: str = Field(min_length=1, max_length=500)


class BottomAssessment(DamageBasis):
    financial: BottomFinancial


class ShellAssessment(DamageBasis):
    financial: ShellFinancial


_RISK_LIMITS = _FIN_LIMITS+[
    "Uniform supplied DF and Fms apply to all four holes of one component. Annual financial risk is sum(GFF)*DF*Fms*already-GFF-weighted financial consequence. This composition does not calculate damage applicability, dynamic release, whole-tank common-cause risk or individual/societal risk.",
]


def _assessment(x, fn):
    ensure(bool(x.damage_factor_source.strip()), "Damage factor source must be nonblank")
    financial = fn(x.financial)
    fms = management(Management(score=x.management_score))["management_factor"]
    rates = x.financial.generic_frequency_by_hole_per_year
    total = math.fsum(rates.values())
    adjusted = {h: _product(rates[h], x.total_damage_factor, fms) for h in HOLES}
    annual = math.fsum(adjusted.values())
    ensure(math.isfinite(annual), "Annual frequency overflow", "numerical_failure")
    ensure(annual > 0 or x.total_damage_factor == 0, "Annual frequency underflow", "numerical_failure")
    return {**financial, "generic_frequency_per_year": total, "management_factor": fms,
            "annual_failure_frequency": annual, "annual_frequency_by_hole": adjusted,
            "financial_risk_per_year": _product(annual, financial["financial_consequence"]),
            "integration_scope": "supplied_uniform_df_and_tank_release_consequences"}


@calculation("tank/bottom-risk-assessment", "AST bottom financial consequence and annual risk", BottomAssessment,
    ["Part1 eqs(1.1),(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.3"], limitations=_RISK_LIMITS+[
        "Bottom assessment returns financial risk only; no unsupported zero-valued physical consequence area is implied. Surrounding-equipment and injury costs are not applicable; rupture-only repair diameter scaling and printed detection-time groundwater partition retained."])
def bottom_assessment(x):
    return _assessment(x, bottom_financial)


@calculation("tank/shell-risk-assessment", "AST shell-course financial and area risks", ShellAssessment,
    ["Part1 eqs(1.1),(1.6)-(1.8); Part2 eqs(2.9)-(2.10); Part3 §6.12.2"], limitations=_RISK_LIMITS+[
        "Equipment/personnel area risks use externally qualified GFF-weighted AST areas. No automatic AST NFNT, course summation or whole-tank spatial overlap resolution."])
def shell_assessment(x):
    result = _assessment(x, shell_financial)
    return {**result, "equipment_area_risk_m2_per_year": _product(result["annual_failure_frequency"], x.financial.equipment_area_m2),
            "personnel_area_risk_m2_per_year": _product(result["annual_failure_frequency"], x.financial.personnel_area_m2)}
