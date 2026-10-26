"""AST diked pool effects and continuous-shell Level2 area/risk composition."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, REGISTRY, calculation, ensure, finite_tree
from .pool_fire import PoolConsequence, pool_consequence
from .level2_summary import FlammableCase, flammable_case
from .toxic_level2 import ToxicCloudArea, ToxicCase, toxic_case
from .tank_environment import HOLES, FrequencyWeights, _weights
from .tank_financial import TankComponent, generic_frequency, DamageBasis, ShellFinancial, ShellAssessment, shell_assessment
from .tank_source import ShellSource, shell_source
from .tank_integrated import BottomEconomics

DikeBasis = Literal["burning_pool_area", "burning_and_consequence_area"]


class DikedPool(PoolConsequence):
    site_maximum_area_m2: Positive | None = None
    dike_area_m2: Positive
    dike_limit_basis: DikeBasis


@calculation("tank/diked-pool-consequence", "AST pool radiation with explicit dike-area interpretation", DikedPool,
    ["Part3 §6.7.2; PDF p596", *REGISTRY["effects/pool-fire-consequence"].references],
    origin="api581_pool_chain_with_explicit_ast_dike_interpretation",
    limitations=[*REGISTRY["effects/pool-fire-consequence"].limitations,
        "Source says pool fire area must not exceed dike area without distinguishing burning pool from radiation consequence. Required burning_pool_area caps physical pool before radiation; burning_and_consequence_area additionally clips reported consequence areas numerically. Neither is an authorized erratum. Raw radiation areas and threshold separations remain separately labeled; numerical clipping is not a spatial dike intersection. No ignition/hole weighting."])
def diked_pool(x):
    cap = min(x.dike_area_m2, x.site_maximum_area_m2) if x.site_maximum_area_m2 is not None else x.dike_area_m2
    fields = {k:getattr(x,k) for k in PoolConsequence.model_fields}
    fields["site_maximum_area_m2"] = cap
    result = pool_consequence(PoolConsequence(**fields))
    raw_equipment, raw_personnel = result["equipment_area_m2"], result["personnel_area_m2"]
    equipment = min(raw_equipment,x.dike_area_m2) if x.dike_limit_basis == "burning_and_consequence_area" else raw_equipment
    personnel = min(raw_personnel,x.dike_area_m2) if x.dike_limit_basis == "burning_and_consequence_area" else raw_personnel
    distances = {"unclipped_"+k:result.pop(k) for k in ("personnel_safe_surface_distance_m","equipment_safe_surface_distance_m")}
    return {**result,**distances,"equipment_area_m2":equipment,"personnel_area_m2":personnel,
        "unclipped_equipment_area_m2":raw_equipment,"unclipped_personnel_area_m2":raw_personnel,
        "effective_pool_area_limit_m2":cap,"dike_area_m2":x.dike_area_m2,"dike_limit_basis":x.dike_limit_basis,
        "equipment_area_clipped":equipment < raw_equipment,"personnel_area_clipped":personnel < raw_personnel}


class ShellCase(FlammableCase):
    release_type: Literal["continuous"] = "continuous"
    toxic_components: list[ToxicCloudArea] = Field(max_length=100)
    toxic_applicability: Literal["evaluated","not_applicable"]
    toxic_applicability_source: str = Field(min_length=1,max_length=1000)
    dike_area_m2: Positive
    burning_pool_area_m2: NonNegative
    pool_dike_limit_basis: DikeBasis


_AREA_LIMITS = [
    "AST shell release type is continuous, including rupture. Raw event probabilities and flammable/toxic footprints are externally qualified. All five canonical flammable events required; inapplicable fireball branch zero. Shared non-ignition probability weights toxic once; empty toxic components require explicit not-applicable basis.",
    "NFNT is not determined for AST per §6.10 and is absent from the request. Pool burning area must fit dike; explicit dike interpretation and raw footprint provenance are required. Burning area0 requires zero pool radiation footprint; no circular radiation area is silently clipped after weighting.",
]


@calculation("tank/shell-level2-case", "AST continuous shell event-weighted flammable and toxic areas", ShellCase,
    ["Part3 §§6.5,6.7.2,6.8-6.11; PDF pp596,598", "Part3 eqs(3.176)-(3.177),(3.188)"],
    origin="api581_ast_conditional_event_composition",limitations=_AREA_LIMITS)
def shell_case(x):
    ensure(x.toxic_applicability_source.strip(), "Toxic applicability source must be nonblank")
    ensure(bool(x.toxic_components) == (x.toxic_applicability == "evaluated"), "Toxic components must match applicability")
    ensure(x.burning_pool_area_m2 <= x.dike_area_m2, "Burning pool exceeds dike area", "dike_area_exceeded")
    pool = next((o for o in x.outcomes if o.event == "pool_fire"),None)
    pool_areas = [] if pool is None else [pool.equipment_area_m2,pool.personnel_area_m2]
    if x.correlated_jet_pool is not None:
        pool_areas += [x.correlated_jet_pool.pool_equipment_area_m2,x.correlated_jet_pool.pool_personnel_area_m2]
    ensure(x.burning_pool_area_m2 > 0 or all(a == 0 for a in pool_areas), "No burning pool requires zero pool footprints")
    if x.pool_dike_limit_basis == "burning_and_consequence_area":
        ensure(all(a <= x.dike_area_m2 for a in pool_areas), "Pool consequence area exceeds selected literal dike cap", "dike_area_exceeded")
    flame = flammable_case(FlammableCase(**x.model_dump(include=set(FlammableCase.model_fields))))
    toxic = toxic_case(ToxicCase(components=x.toxic_components,non_ignition_probability=x.non_ignition_probability))["personnel_area_m2"] if x.toxic_components else 0.
    return {**flame,"toxic_personnel_area_m2":toxic,"nfnt_status":"not_determined_for_ast"}


class ShellSummary(Model):
    cases: list[ShellCase] = Field(min_length=4,max_length=4)


@calculation("tank/shell-level2-summary", "AST four-hole GFF-weighted flammable plus toxic final areas", ShellSummary,
    ["Part3 §§6.10-6.11,eqs(3.178)-(3.179),(3.191),(3.202)-(3.204); PDF pp560,567,572-573,598"],
    origin="api581_ast_level2_mechanism_composition",limitations=_AREA_LIMITS+[
        "Exactly four canonical holes on one common dike basis. Uses COURSE-1-10 Table3.1 frequencies with eq3.208 total. Mechanism GFF averages precede final equipment=flammable and personnel=flammable+toxic; this is Level2 additive composition with NFNT absent, not Level1 maximum selection. No DF in GFF averaging."])
def shell_summary(x):
    ensure({c.hole for c in x.cases} == set(HOLES), "Exactly four distinct canonical holes required")
    ensure(len({(c.dike_area_m2,c.pool_dike_limit_basis) for c in x.cases}) == 1, "Four cases must share dike area and interpretation")
    gff = generic_frequency(TankComponent(component_type="COURSE-1-10"))
    weights = _weights(FrequencyWeights(generic_frequency_by_hole_per_year=gff["by_hole_per_year"]))
    cases = {c.hole:shell_case(c) for c in x.cases}
    names = ("flammable_equipment_area_m2","flammable_personnel_area_m2","toxic_personnel_area_m2")
    values = {name:math.fsum(weights[h]*cases[h][name] for h in HOLES) for name in names}
    personnel = values["flammable_personnel_area_m2"]+values["toxic_personnel_area_m2"]
    return {**values,"equipment_area_m2":values["flammable_equipment_area_m2"],"personnel_area_m2":personnel,
        "consequence_area_m2":max(values["flammable_equipment_area_m2"],personnel),
        "generic_frequency_per_year":gff["total_per_year"],"nfnt_status":"not_determined_for_ast",
        **{"by_hole_"+name:{h:cases[h][name] for h in HOLES} for name in names}}


class ShellEconomics(BottomEconomics):
    equipment_cost_per_m2: NonNegative
    population_density_per_m2: NonNegative
    cost_per_injury: NonNegative


class ShellIntegrated(DamageBasis):
    source: ShellSource
    cases: list[ShellCase] = Field(min_length=4,max_length=4)
    economics: ShellEconomics


@calculation("tank/shell-integrated-assessment", "AST shell source, supplied event footprints, financial consequence and annual risk", ShellIntegrated,
    [*REGISTRY["tank/shell-source-assessment"].references,*REGISTRY["tank/shell-level2-summary"].references,
     *REGISTRY["tank/shell-risk-assessment"].references],
    origin="api581_ast_source_with_qualified_event_footprints_and_supplied_damage",
    limitations=[*REGISTRY["tank/shell-source-assessment"].limitations,*REGISTRY["tank/shell-level2-summary"].limitations,
        *REGISTRY["tank/shell-risk-assessment"].limitations,
        "Computes source/GFF/environment from one geometry request and inserts event/GFF-weighted AST areas into financial risk. Footprints and event probabilities remain external and must be qualified for this computed source. Does not infer dispersion, EOS, source-to-footprint consistency or whole-tank spatial overlap. Dry source requires zero flammable/toxic footprints for every hole."])
def shell_integrated(x):
    source = shell_source(x.source)
    finite_tree(source)
    areas = shell_summary(ShellSummary(cases=x.cases))
    finite_tree(areas)
    if not source["course_wet"]:
        for case in x.cases:
            ensure(case.burning_pool_area_m2 == 0, "Dry source cannot have a burning pool")
            ensure(all(o.equipment_area_m2 == o.personnel_area_m2 == 0 for o in case.outcomes), "Dry source cannot have flammable footprints")
            ensure(not case.toxic_components or all(c.cloud_area_m2 == 0 for c in case.toxic_components), "Dry source cannot have toxic footprints")
            if case.correlated_jet_pool is not None:
                ensure(all(getattr(case.correlated_jet_pool,k) == 0 for k in (
                    "jet_equipment_area_m2","jet_personnel_area_m2","pool_equipment_area_m2","pool_personnel_area_m2")),
                    "Dry source cannot have correlated footprints")
    financial = ShellFinancial(**x.economics.model_dump(),
        generic_frequency_by_hole_per_year=source["generic_frequency_by_hole_per_year"],
        generic_frequency_source="Part2 Table3.1; sum eq3.208; computed within same shell source",
        released_volume_by_hole_bbl=source["released_volume_by_hole_bbl"],
        equipment_area_m2=areas["equipment_area_m2"],personnel_area_m2=areas["personnel_area_m2"])
    risk = shell_assessment(ShellAssessment(financial=financial,management_score=x.management_score,
        total_damage_factor=x.total_damage_factor,damage_factor_source=x.damage_factor_source))
    return {**source,**areas,**risk,"integration_scope":"shell_geometry_source_supplied_event_footprints_financial_risk"}
