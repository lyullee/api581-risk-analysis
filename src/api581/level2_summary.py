"""Level2 event weighting, non-ignition maxima, GFF averages and assessment.

Unlike Level1, eqs3.202/203 ADD flammable areas to the non-ignition branch.
"""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Fraction, calculation, ensure
from .physical_explosion import NfntCase, nfnt_case
from .toxic_level2 import ToxicCloudArea, ToxicCase, toxic_case
from .pof import Component, generic, Management, management, Frequency, adjusted
from .cost_tables import RepairCost, ComponentOutage, FinancialConsequence, financial_consequence
from .risk import Risk, RiskScenario, aggregate

Hole=Literal["small","medium","large","rupture"]
Event=Literal["pool_fire","jet_fire","fireball","vce","flash_fire"]
_EVENTS={"pool_fire","jet_fire","fireball","vce","flash_fire"}
_MECHANISMS=("flammable_equipment_area_m2","flammable_personnel_area_m2","toxic_personnel_area_m2",
             "nfnt_equipment_area_m2","nfnt_personnel_area_m2")


class FlammableOutcome(Model):
    event: Event
    probability: Fraction
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative


class CorrelatedJetPool(Model):
    probability: Fraction
    jet_equipment_area_m2: NonNegative
    jet_personnel_area_m2: NonNegative
    pool_equipment_area_m2: NonNegative
    pool_personnel_area_m2: NonNegative
    consequence_source: str = Field(min_length=1,max_length=1000)


@calculation("level2/correlated-jet-pool", "One immediate-ignition branch with max(jet,pool) area", CorrelatedJetPool,
             ["Part3 Figure5.3 two-phase continuous immediate branch; PDF p586; eqs(3.176)-(3.177)"],
             origin="api581_correlated_two_phase_immediate_area",
             limitations=["One branch probability applies to maximum jet/pool area, separately for equipment and personnel. Do not treat jet and pool as two independent terminal probabilities or sum their areas. Source footprints supplied and qualified externally; no geometric union or simultaneous-fire radiation solver."])
def correlated_jet_pool(x):
    ensure(x.consequence_source.strip(),"Correlated branch consequence source must be nonblank")
    equipment=max(x.jet_equipment_area_m2,x.pool_equipment_area_m2)
    personnel=max(x.jet_personnel_area_m2,x.pool_personnel_area_m2)
    def governing(jet,pool):
        return "equal" if jet == pool else "jet" if jet > pool else "pool"
    return {"equipment_area_m2":x.probability*equipment,"personnel_area_m2":x.probability*personnel,
            "maximum_equipment_area_m2":equipment,"maximum_personnel_area_m2":personnel,
            "governing_equipment":governing(x.jet_equipment_area_m2,x.pool_equipment_area_m2),
            "governing_personnel":governing(x.jet_personnel_area_m2,x.pool_personnel_area_m2)}


class FlammableCase(Model):
    hole: Hole
    release_type: Literal["continuous","instantaneous"]
    outcomes: list[FlammableOutcome] = Field(min_length=5,max_length=5)
    non_ignition_probability: Fraction
    event_tree_source: str = Field(min_length=1,max_length=1000)
    consequence_source: str = Field(min_length=1,max_length=1000)
    fireball_applicability_basis: Literal["rupture_only_text","figure53_instantaneous"] = "rupture_only_text"
    correlated_jet_pool: CorrelatedJetPool | None = None


@calculation("level2/flammable-case", "Flammable areas with optional correlated immediate branch", FlammableCase,
             ["Part3 eqs(3.176)-(3.177),Figure5.3; PDF pp559,586"],
             limitations=["Requires pool,jet,fireball,VCE,flash outcomes exactly once, including explicit zero branches. Together with optional correlated_jet_pool and non-ignition probabilities they sum to1. Raw areas weighted once. Correlated max(jet,pool) only for continuous leakage; separate jet/pool branches must be zero. Fireball defaults to instantaneous rupture-only text; explicit figure53_instantaneous also permits figure5.3 instantaneous leakage. Caller qualifies tree/area sources."])
def flammable_case(x):
    ensure({o.event for o in x.outcomes} == _EVENTS,"Require five distinct canonical flammable outcomes")
    ensure(x.event_tree_source.strip() and x.consequence_source.strip(),"Event-tree and consequence sources must be nonblank")
    correlated={"equipment_area_m2":0,"personnel_area_m2":0}
    if x.correlated_jet_pool is not None:
        ensure(x.release_type == "continuous" and x.hole != "rupture","Correlated jet/pool branch only for continuous leakage")
        ensure(all(o.probability == o.equipment_area_m2 == o.personnel_area_m2 == 0 for o in x.outcomes if o.event in {"jet_fire","pool_fire"}),
               "Correlated branch cannot coexist with separate jet/pool probability or area")
        correlated=correlated_jet_pool(x.correlated_jet_pool)
    total=math.fsum([o.probability for o in x.outcomes]+[x.non_ignition_probability,
        x.correlated_jet_pool.probability if x.correlated_jet_pool is not None else 0])
    ensure(math.isclose(total,1,rel_tol=0,abs_tol=1e-10),"Flammable outcomes plus non-ignition probability must sum to1")
    for outcome in x.outcomes:
        inactive=(outcome.event == "fireball" and (x.release_type != "instantaneous" or (
                  x.hole != "rupture" and x.fireball_applicability_basis != "figure53_instantaneous"))) or (
                  outcome.event == "jet_fire" and x.release_type != "continuous")
        ensure(not inactive or outcome.probability == outcome.equipment_area_m2 == outcome.personnel_area_m2 == 0,
               "Inapplicable fireball/jet branch must have zero probability and area")
    equipment=math.fsum([o.probability*o.equipment_area_m2 for o in x.outcomes]+[correlated["equipment_area_m2"]])
    personnel=math.fsum([o.probability*o.personnel_area_m2 for o in x.outcomes]+[correlated["personnel_area_m2"]])
    return {"flammable_equipment_area_m2":equipment,"flammable_personnel_area_m2":personnel,
            "non_ignition_probability":x.non_ignition_probability,"terminal_probability_sum":total}


class FinalArea(Model):
    flammable_equipment_area_m2: NonNegative
    flammable_personnel_area_m2: NonNegative
    toxic_personnel_area_m2: NonNegative
    nfnt_equipment_area_m2: NonNegative
    nfnt_personnel_area_m2: NonNegative


@calculation("level2/final-area", "Final Level2 component/personnel consequence areas", FinalArea,
             ["Part3 eqs(3.202)-(3.204); PDF pp572-573"],
             limitations=["Inputs must already be event- and hole-weighted on a common basis. Equipment=flammable+NFNT; personnel=flammable+max(toxic,NFNT); final=max(equipment,personnel). Safe-event areas are0. Do not replace with Level1 maximum over all mechanisms or apply non-ignition probability twice."])
def final_area(x):
    equipment=x.flammable_equipment_area_m2+x.nfnt_equipment_area_m2
    nonignition=max(x.toxic_personnel_area_m2,x.nfnt_personnel_area_m2)
    personnel=x.flammable_personnel_area_m2+nonignition
    ensure(math.isfinite(equipment) and math.isfinite(personnel),"Final Level2 area exceeds numerical domain","numerical_failure")
    return {"equipment_area_m2":equipment,"personnel_area_m2":personnel,"consequence_area_m2":max(equipment,personnel),
            "non_ignition_personnel_area_m2":nonignition,
            "governing_non_ignition_personnel_mechanism":"equal" if x.toxic_personnel_area_m2 == x.nfnt_personnel_area_m2 else (
                "toxic" if x.toxic_personnel_area_m2 > x.nfnt_personnel_area_m2 else "nfnt")}


class MechanismHole(FinalArea):
    hole: Hole
    generic_frequency_per_year: NonNegative


class ConsequenceSummary(Model):
    holes: list[MechanismHole] = Field(min_length=4,max_length=4)


def _holes(cases):
    ensure({c.hole for c in cases} == {"small","medium","large","rupture"},"Require four distinct canonical holes")


@calculation("level2/consequence-summary", "GFF mechanism averages followed by Level2 final selection", ConsequenceSummary,
             ["Part3 eqs(3.178)-(3.179),(3.191),(3.200)-(3.204); PDF pp560,567,570,572-573"],
             origin="api581_level2_mechanism_composition",
             limitations=["All four holes required. Input mechanism areas already include event/non-ignition probabilities. GFF averages are formed separately before final non-ignition maximum. Averaging per-hole maxima generally gives a different result. No DF-adjusted frequencies as GFF weights."])
def consequence_summary(x):
    _holes(x.holes)
    total=math.fsum(h.generic_frequency_per_year for h in x.holes)
    ensure(math.isfinite(total) and total > 0,"Total generic frequency must be finite and positive")
    values={name:math.fsum(h.generic_frequency_per_year/total*getattr(h,name) for h in x.holes) for name in _MECHANISMS}
    return {**values,**final_area(FinalArea(**values)),"generic_frequency_per_year":total}


class NfntAreas(Model):
    physical_equipment_area_m2: NonNegative = 0
    physical_personnel_area_m2: NonNegative = 0
    bleve_equipment_area_m2: NonNegative = 0
    bleve_personnel_area_m2: NonNegative = 0
    steam_chemical_personnel_area_m2: NonNegative = 0
    consequence_source: str = Field(min_length=1,max_length=1000)


class ScenarioCase(FlammableCase):
    toxic_components: list[ToxicCloudArea] = Field(max_length=100)
    toxic_applicability: Literal["evaluated","not_applicable"]
    toxic_applicability_source: str = Field(min_length=1,max_length=1000)
    nfnt: NfntAreas


@calculation("level2/scenario-consequence", "One-hole flammable/toxic/NFNT mechanism consequences", ScenarioCase,
             ["Part3 eqs(3.176)-(3.177),(3.188),(3.198)-(3.199),Figure5.3; PDF pp559,567,570,586"],
             origin="api581_level2_conditional_scenario_composition",
             limitations=["Supplied terminal probabilities and raw event/footprint areas; no release or dispersion calculation is inferred. One shared non-ignition probability drives toxic and NFNT. Empty toxic list requires explicit not_applicable with basis. Outputs remain separate mechanisms; final selection is after hole weighting."])
def scenario_consequence(x):
    ensure(x.toxic_applicability_source.strip() and x.nfnt.consequence_source.strip(),"Toxic applicability and NFNT sources must be nonblank")
    ensure(bool(x.toxic_components) == (x.toxic_applicability == "evaluated"),"Toxic components must match explicit applicability")
    flammable=flammable_case(FlammableCase(**x.model_dump(include=set(FlammableCase.model_fields))))
    toxic=0
    if x.toxic_components:
        toxic=toxic_case(ToxicCase(components=x.toxic_components,non_ignition_probability=x.non_ignition_probability))["personnel_area_m2"]
    nfnt=nfnt_case(NfntCase(**x.nfnt.model_dump(exclude={"consequence_source"}),hole=x.hole,
        non_ignition_probability=x.non_ignition_probability))
    return {**flammable,"toxic_personnel_area_m2":toxic,"nfnt_equipment_area_m2":nfnt["equipment_area_m2"],
            "nfnt_personnel_area_m2":nfnt["personnel_area_m2"],"hole":x.hole}


class FrequencyScenario(ScenarioCase):
    generic_frequency_per_year: NonNegative


class ScenarioSummary(Model):
    cases: list[FrequencyScenario] = Field(min_length=4,max_length=4)


@calculation("level2/scenario-summary", "Four raw event scenarios to final Level2 consequence areas", ScenarioSummary,
             ["Part3 §§5.8.7-5.11 eqs(3.176)-(3.204); PDF pp559-573"],
             origin="api581_level2_event_to_final_area_composition",
             limitations=["Caller-qualified event probabilities and raw event/dispersion areas for all four holes. Composes conditional mechanisms, separate GFF averages, flammable addition and non-ignition maximum. Does not run thermodynamics, dispersion or applicability inference."])
def scenario_summary(x):
    _holes(x.cases)
    holes=[]
    for case in x.cases:
        result=scenario_consequence(ScenarioCase(**case.model_dump(include=set(ScenarioCase.model_fields))))
        holes.append(MechanismHole(hole=case.hole,generic_frequency_per_year=case.generic_frequency_per_year,
            **{name:result[name] for name in _MECHANISMS}))
    return consequence_summary(ConsequenceSummary(holes=holes))


class FinancialBasis(Model):
    repair: RepairCost
    outage: ComponentOutage
    equipment_cost_per_m2: NonNegative
    production_cost_per_day: NonNegative
    population_density_per_m2: NonNegative
    cost_per_injury: NonNegative
    weighted_cleanup_volume_m3: NonNegative
    cleanup_cost_per_m3: NonNegative


class Assessment(Model):
    component_type: str = Field(min_length=1,max_length=100)
    management_score: NonNegative = Field(le=1000)
    total_damage_factor: NonNegative
    damage_factor_source: str = Field(min_length=1,max_length=1000)
    cases: list[ScenarioCase] = Field(min_length=4,max_length=4)
    financial: FinancialBasis


@calculation("level2/assessment", "Supplied Level2 event consequences to financial/annual risk", Assessment,
             ["Part3 §§5.8.7-5.12 eqs(3.176)-(3.204); Part1 eqs(1.1),(1.6)-(1.8)"],
             origin="api581_level2_supplied_event_area_and_damage_assessment",
             limitations=["Explicit integration boundary: owner-qualified terminal probabilities, raw event/dispersion areas, applicability and total DF supplied. Computes GFF/Fms, Level2 area composition, five financial categories and component annual risk. Non-tank GFF only. Common component DF/Fms; no hole-specific DF substitution or automatic future damage model.",
                          "Repair/outage component types must match assessment. Areas are computed here; cleanup volume/pricing/screening remain supplied. Financial equations reuse §4.12 per §5.12. Not a complete asset-data-to-risk workflow or independent certification."])
def assessment(x):
    ensure(x.damage_factor_source.strip(),"Damage factor source must be nonblank")
    ensure(x.component_type == x.financial.repair.component_type == x.financial.outage.component_type,
           "Assessment, repair and outage component types must match")
    frequencies=generic(Component(component_type=x.component_type))
    cases=[FrequencyScenario(**c.model_dump(),generic_frequency_per_year=frequencies["by_hole_per_year"][c.hole]) for c in x.cases]
    area=scenario_summary(ScenarioSummary(cases=cases))
    finance=financial_consequence(FinancialConsequence(**x.financial.model_dump(),
        equipment_area_m2=area["equipment_area_m2"],personnel_area_m2=area["personnel_area_m2"]))
    fms=management(Management(score=x.management_score))["management_factor"]
    occurrence=adjusted(Frequency(generic_frequency_per_year=frequencies["total_per_year"],total_damage_factor=x.total_damage_factor,
        management_factor=fms))["annual_failure_frequency"]
    ensure(math.isfinite(occurrence) and (occurrence > 0 or x.total_damage_factor == 0),
           "Adjusted frequency outside finite positive numerical domain","numerical_failure")
    risk=aggregate(Risk(currency=finance["currency"],scenarios=[RiskScenario(scenario_id="level2_component",
        annual_failure_frequency=occurrence,equipment_area_m2=area["equipment_area_m2"],personnel_area_m2=area["personnel_area_m2"],
        financial_consequence=finance["financial_consequence"])]))
    return {"integration_scope":"supplied_level2_event_probabilities_areas_and_damage",
            "management_factor":fms,**area,**finance,**risk}
