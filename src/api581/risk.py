"""Consequence aggregation, risk and planning utilities with explicit units."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .pof import Component, generic, Management, management, GoverningDamage, combine


class Outcome(Model):
    event_id: str = Field(min_length=1, max_length=100)
    probability: Fraction
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    financial_consequence: NonNegative


class Consequences(Model):
    outcomes: list[Outcome] = Field(min_length=1, max_length=100)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("consequence/expected", "Conditional event-weighted consequence", Consequences,
             ["Part 3 §5.8.7, §5.11"], limitations=["Inputs must be mutually exclusive complete terminal outcomes, already conditional on the same release/weather case."])
def expected(x):
    ensure(len({o.event_id for o in x.outcomes}) == len(x.outcomes), "Duplicate event_id")
    ensure(math.isclose(math.fsum(o.probability for o in x.outcomes), 1, abs_tol=1e-9), "Terminal probabilities must sum to 1")
    return {"equipment_area_m2": math.fsum(o.probability * o.equipment_area_m2 for o in x.outcomes),
            "personnel_area_m2": math.fsum(o.probability * o.personnel_area_m2 for o in x.outcomes),
            "financial_consequence": math.fsum(o.probability * o.financial_consequence for o in x.outcomes), "currency": x.currency}


class RiskScenario(Model):
    scenario_id: str = Field(min_length=1, max_length=100)
    annual_failure_frequency: NonNegative
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    financial_consequence: NonNegative


class Risk(Model):
    scenarios: list[RiskScenario] = Field(min_length=1, max_length=1000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("risk/aggregate", "Aggregate disjoint release-scenario risks", Risk,
             ["Part 1 §4.3.1 eqs (1.6)-(1.8)"],
             limitations=["Scenarios must be disjoint; each consequence is conditional and already event/weather weighted. No individual/societal risk calculation."])
def aggregate(x):
    ensure(len({s.scenario_id for s in x.scenarios}) == len(x.scenarios), "Duplicate scenario_id")
    total = math.fsum(s.annual_failure_frequency for s in x.scenarios)
    equip = math.fsum(s.annual_failure_frequency * s.equipment_area_m2 for s in x.scenarios)
    person = math.fsum(s.annual_failure_frequency * s.personnel_area_m2 for s in x.scenarios)
    financial = math.fsum(s.annual_failure_frequency * s.financial_consequence for s in x.scenarios)
    return {"annual_failure_frequency": total, "equipment_area_risk_m2_per_year": equip,
            "personnel_area_risk_m2_per_year": person, "area_risk_m2_per_year": max(equip, person),
            "financial_risk_per_year": financial, "currency": x.currency,
            "frequency_weighted_equipment_area_m2": equip / total if total else None,
            "frequency_weighted_personnel_area_m2": person / total if total else None}


class HoleConsequence(Model):
    hole: Literal["small", "medium", "large", "rupture"]
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    financial_consequence: NonNegative


class Assessment(Model):
    component_type: str
    management_score: NonNegative = Field(le=1000)
    total_damage_factor: NonNegative
    damage_factor_source: str = Field(min_length=1, max_length=500)
    consequences: list[HoleConsequence] = Field(min_length=4, max_length=4)
    consequence_source: str = Field(min_length=1, max_length=500)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation("risk/assessment", "Compose GFF, Fms, supplied DF and supplied hole consequences", Assessment,
             ["Part 1 §4.1, §4.3; Part 2 §3.3, §3.5.4"],
             limitations=["Integration boundary: DF and COF supplied externally; not a complete asset damage/COF assessment. All four holes required."])
def assessment(x):
    ensure({c.hole for c in x.consequences} == {"small", "medium", "large", "rupture"}, "Exactly one consequence for each of the four holes is required")
    g = generic(Component(component_type=x.component_type))
    fms = management(Management(score=x.management_score))["management_factor"]
    scenarios = [RiskScenario(scenario_id=c.hole, annual_failure_frequency=g["by_hole_per_year"][c.hole] * x.total_damage_factor * fms,
                             equipment_area_m2=c.equipment_area_m2, personnel_area_m2=c.personnel_area_m2,
                             financial_consequence=c.financial_consequence) for c in x.consequences]
    return {"integration_scope": "supplied_damage_and_consequences", "management_factor": fms,
            "generic_frequencies": g, "scenarios": [s.model_dump() for s in scenarios],
            "risk": aggregate(Risk(scenarios=scenarios, currency=x.currency))}


class DamageAssessment(Model):
    component_type: str
    management_score: NonNegative = Field(le=1000)
    damage: GoverningDamage
    damage_factor_source: str = Field(min_length=1, max_length=500)
    consequences: list[HoleConsequence] = Field(min_length=4, max_length=4)
    consequence_source: str = Field(min_length=1, max_length=500)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


@calculation(
    "risk/assessment-from-damage",
    "Compose damage mechanisms, GFF, management factor and hole consequences",
    DamageAssessment,
    ["Part 1 §§4.1,4.3; Part 2 §§3.4.2,3.5.4; Part 3 consequence inputs"],
    limitations=[
        "Damage mechanism inputs are still owner-qualified outputs from the individual Part 2 APIs. This composition performs the governing/total damage-factor combination and risk weighting; it does not infer applicability, inspection effectiveness, consequence areas or currency assumptions."
    ],
)
def assessment_from_damage(x):
    combined = combine(x.damage)
    result = assessment(
        Assessment(
            component_type=x.component_type,
            management_score=x.management_score,
            total_damage_factor=combined["total_damage_factor"],
            damage_factor_source=x.damage_factor_source,
            consequences=x.consequences,
            consequence_source=x.consequence_source,
            currency=x.currency,
        )
    )
    return {**result, "integration_scope": "combined_damage_and_supplied_consequences",
            "damage_factor": combined}


class Financial(Model):
    component_repair_cost: NonNegative
    surrounding_equipment_cost: NonNegative
    business_interruption_cost: NonNegative
    injury_cost: NonNegative
    environmental_cost: NonNegative
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis_year: int = Field(ge=1900, le=2200)


@calculation("consequence/financial-total", "Sum non-overlapping financial consequence categories", Financial,
             ["Part 3 §4.12"], origin="engineering_utility",
             limitations=["Category costs supplied by caller; repair/downtime/cleanup submodels not yet implemented."])
def financial(x):
    return {"financial_consequence": math.fsum([x.component_repair_cost, x.surrounding_equipment_cost,
            x.business_interruption_cost, x.injury_cost, x.environmental_cost]), "currency": x.currency,
            "cost_basis_year": x.cost_basis_year}


class Matrix(Model):
    frequency_per_year: NonNegative
    consequence: NonNegative
    frequency_boundaries: list[Positive] = Field(min_length=1, max_length=20)
    consequence_boundaries: list[Positive] = Field(min_length=1, max_length=20)
    risk_cells: list[list[str]]
    policy_id: str = Field(min_length=1, max_length=200)


@calculation("risk/matrix", "Owner-defined risk matrix classification", Matrix,
             ["Part 1 §4.3.2"], limitations=["No built-in universal acceptance limits; equality is assigned to the higher category."])
def matrix(x):
    for bounds in (x.frequency_boundaries, x.consequence_boundaries):
        ensure(all(b > a for a, b in zip(bounds, bounds[1:])), "Boundaries must strictly increase")
    ensure(len(x.risk_cells) == len(x.frequency_boundaries) + 1 and
           all(len(row) == len(x.consequence_boundaries) + 1 for row in x.risk_cells), "risk_cells dimensions must match boundaries")
    i = sum(x.frequency_per_year >= b for b in x.frequency_boundaries)
    j = sum(x.consequence >= b for b in x.consequence_boundaries)
    return {"frequency_category": i + 1, "consequence_category": j + 1, "risk_label": x.risk_cells[i][j], "policy_id": x.policy_id}


class RiskPoint(Model):
    time_years: NonNegative
    value: NonNegative


class Crossing(Model):
    points: list[RiskPoint] = Field(min_length=2, max_length=10000)
    target: Positive
    metric: Literal["financial_per_year", "area_m2_per_year", "frequency_per_year", "damage_factor"]


@calculation("planning/target-crossing", "First target crossing on a supplied risk curve", Crossing,
             ["Part 1 §4.4"], origin="engineering_utility",
             limitations=["Linear interpolation between supplied points; does not generate DF forecasts or select NDE effectiveness. Unresolved crossings between samples remain possible."])
def crossing(x):
    ensure(all(b.time_years > a.time_years for a, b in zip(x.points, x.points[1:])), "Curve times must strictly increase")
    if x.points[0].value >= x.target:
        return {"status": "already_exceeded", "crossing_years": x.points[0].time_years}
    for a, b in zip(x.points, x.points[1:]):
        if b.value >= x.target:
            time = a.time_years + (b.time_years - a.time_years) * (x.target - a.value) / (b.value - a.value)
            return {"status": "crossing", "crossing_years": time}
    return {"status": "not_crossed_within_horizon", "crossing_years": None, "horizon_years": x.points[-1].time_years}
