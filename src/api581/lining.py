"""2016 lining tables, qualified inspection-age policy and governing thinning."""
from datetime import date
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, calculation, ensure, finite_tree
from .cracking import LiningAdjustment, lining_adjust

LiningType = Literal["strip_lined_resistant_alloy","castable_refractory","castable_refractory_severe",
    "glass_lined","acid_brick","fiberglass","organic_low_quality","organic_medium_quality","organic_high_quality"]
Lookup = Literal["exact_rows_only","linear_between_rows","conservative_upper_row"]
FirstYear = Literal["reject_below_first_year","qualified_first_year_value"]
_INORGANIC = (
    (.3,.5,9,3,.01,1),(.5,1,40,4,.03,1),(.7,2,146,6,.05,1),(1,4,428,7,.15,1),
    (1,9,1017,9,1,1),(2,16,1978,11,1,1),(3,30,3000,13,1,2),(4,53,3000,16,1,3),
    (6,89,3000,20,2,7),(9,146,3000,25,3,13),(12,230,3000,30,4,26),(16,351,3000,36,5,47),
    (22,518,3000,44,7,82),(30,738,3000,53,9,139),(40,1017,3000,63,11,228),
    (53,1358,3000,75,15,359),(69,1758,3000,89,19,548),(89,2209,3000,105,25,808),
    (115,2697,3000,124,31,1151),(146,3000,3000,146,40,1587),(184,3000,3000,170,50,2119),
    (230,3000,3000,199,63,2743),(286,3000,3000,230,78,3000),(351,3000,3000,266,97,3000),
    (428,3000,3000,306,119,3000))
_ORGANIC = ((30,1,.1),(89,4,.13),(230,16,.15),(518,53,.17),(1017,146,.2),(1758,351,1),
    (2697,738,4),(3000,1358,16),(3000,2209,53),(3000,3000,146),(3000,3000,351),
    (3000,3000,738),(3000,3000,1358),(3000,3000,2209))+((3000,3000,3000),)*11


class LiningInspection(Model):
    inspection_id: str = Field(min_length=1)
    inspected_on: date
    effectiveness: Literal["a","b","c","d","e"]
    qualified_for_age_reset: bool
    qualification_basis: str | None = None


class LiningAge(Model):
    lining_family: Literal["inorganic","organic"]
    installed_on: date
    evaluated_on: date
    inspections: list[LiningInspection] = Field(default_factory=list,max_length=10000)
    age_basis_policy: Literal["step1_installation_or_last_ab","figure51_organic_service_only"]
    year_length_days: Literal[365,365.25]


@calculation("damage/lining-effective-age", "Lining age from installation or qualified A/B inspection", LiningAge,
    ["Part2 §§5.5.2-5.5.3 STEP1,Table5.3,Figure5.1; PDF pp166,168,171"],limitations=[
        "STEP1 permits installation or last A/B inspection baseline; organic table/figure also say years in service. Explicit policy chooses STEP1 reset or organic service-only interpretation, not an asserted erratum. No inspection-count/Bayesian credit. Owner qualifies A/B reset applicability under Annex2.C.6; C/D/E cannot reset. Date-only deterministic elapsed days divided by explicit365 or365.25; no inferred current clock, time zone or service downtime subtraction."])
def effective_age(x):
    ensure(x.evaluated_on >= x.installed_on,"Evaluation date precedes installation")
    ensure(x.age_basis_policy != "figure51_organic_service_only" or x.lining_family == "organic","Service-only figure interpretation applies only to organic lining")
    ensure(len({i.inspection_id for i in x.inspections}) == len(x.inspections),"Duplicate lining inspection identifier")
    eligible = []
    for i in x.inspections:
        ensure(bool(i.inspection_id.strip()),"Inspection identifier must not be blank")
        ensure(x.installed_on <= i.inspected_on <= x.evaluated_on,"Inspection date outside lining service/evaluation period")
        if i.qualified_for_age_reset:
            ensure(i.effectiveness in ("a","b") and i.qualification_basis is not None and bool(i.qualification_basis.strip()),"Age reset requires qualified A/B inspection and basis")
            eligible.append(i)
        else:
            ensure(i.qualification_basis is None,"Unqualified reset cannot carry qualification basis")
    latest = max(eligible,key=lambda i:(i.inspected_on,i.inspection_id),default=None)
    reset = latest if x.age_basis_policy == "step1_installation_or_last_ab" else None
    baseline = reset.inspected_on if reset is not None else x.installed_on
    return {"effective_age_years":(x.evaluated_on-baseline).days/x.year_length_days,
        "elapsed_service_years":(x.evaluated_on-x.installed_on).days/x.year_length_days,
        "age_baseline_date":baseline.isoformat(),"age_baseline_source":"qualified_ab_inspection" if reset else "installation",
        "reset_inspection_id":reset.inspection_id if reset else None,"qualified_ab_inspection_count":len(eligible),
        "age_basis_policy":x.age_basis_policy}


class LiningBase(Model):
    lining_type: LiningType
    age_years: NonNegative
    lookup_policy: Lookup
    first_year_policy: FirstYear
    first_year_qualification_basis: str | None = None


@calculation("damage/lining-base-factor", "Inorganic and organic lining base damage factor tables", LiningBase,
    ["Part2 Tables5.4-5.5; PDF pp169-170"],limitations=[
        "All225 cells:6 inorganic/3 organic columns over1..25years. Fiberglass follows source Table5.4 grouping without inferring chemical classification. Organic quality includes stated application/reinforcement thickness, not material name alone. No >25year extrapolation even if selected column plateaus. Between-year numerical policy explicit; source gives no interpolation instruction. Below1year requires rejection or qualified first-year-value policy, never silently zero damage or invented age0 row."])
def base_factor(x):
    qualified = x.first_year_policy == "qualified_first_year_value"
    ensure((x.first_year_qualification_basis is not None and bool(x.first_year_qualification_basis.strip())) if qualified else x.first_year_qualification_basis is None,
        "First-year policy and qualification basis must agree")
    ensure(x.age_years <= 25,"Lining age exceeds25year source table; no extrapolation","lining_table_age_exceeded")
    ensure(x.age_years >= 1 or qualified,"Lining age below1year requires qualified first-year policy","lining_age_below_first_row")
    age = max(x.age_years,1.)
    col = LiningType.__args__.index(x.lining_type)
    table, col = (_INORGANIC,col) if col < 6 else (_ORGANIC,col-6)
    low, high = math.floor(age),math.ceil(age)
    weight = age-low
    ensure(low == high or x.lookup_policy != "exact_rows_only","Age lies between table rows; numerical policy required","lining_age_between_rows")
    value = float(table[high-1][col]) if x.lookup_policy == "conservative_upper_row" else table[low-1][col]+weight*(table[high-1][col]-table[low-1][col])
    return {"base_damage_factor":value,"lower_age_row_years":float(low),"upper_age_row_years":float(high),
        "age_interpolation_weight":weight,"first_year_value_used":x.age_years < 1,"source_table":"5.4" if table is _INORGANIC else "5.5"}


class LiningCondition(Model):
    condition: Literal["good","average","poor"]


@calculation("damage/lining-condition-factor", "Qualitative lining condition factor", LiningCondition,
    ["Part2 Table5.6; PDF p171"],limitations=[
        "Owner classifies good: like new/no attack/no repairs; average: no excessive attack with successful good-quality local repairs; poor: prior failures/imminent failure conditions or unsuccessful/poor repairs. No automatic classification from a single damage flag or image."])
def condition_factor(x):
    return {"condition_factor":{"good":1.,"average":2.,"poor":10.}[x.condition]}


class LiningMonitoring(Model):
    monitoring_used: bool
    known_effective_for_lining_deterioration: bool
    effectiveness_basis: str | None = None


@calculation("damage/lining-monitoring-factor", "Lining early-detection monitoring credit", LiningMonitoring,
    ["Part2 §5.5.3 STEP3(2); PDF p167"],limitations=[
        "Factor.1 only when monitoring is used and known effective for detecting lining deterioration early enough for orderly shutdown; otherwise1. Owner supplies effectiveness basis. Merely installed sensors do not prove efficacy. Unlike thinning FOM, lining factor multiplies DF, not divides; no stacked methods."])
def monitoring_factor(x):
    if x.known_effective_for_lining_deterioration:
        ensure(x.monitoring_used and x.effectiveness_basis is not None and bool(x.effectiveness_basis.strip()),"Effective lining monitoring requires use and qualification basis")
    else:
        ensure(x.effectiveness_basis is None,"Unverified monitoring cannot claim effectiveness basis")
    return {"monitoring_factor":.1 if x.known_effective_for_lining_deterioration else 1.}


class GoverningLining(Model):
    base_material_thinning_damage_factor: NonNegative
    lining_damage_factor: NonNegative


@calculation("damage/lining-governing-thinning", "Minimum of base-material thinning and lining damage factors", GoverningLining,
    ["Part2 §5.5.1 and eq(2.2); PDF pp142,166"],limitations=[
        "Compares lining DF to base-material thinning DF as source instructs. Not total DF: other applicable damage mechanisms require separate combination. No automatic zero/thinning applicability assumption or additional.1 floor on lining DF."])
def governing_thinning(x):
    return {"governing_thinning_damage_factor":min(x.base_material_thinning_damage_factor,x.lining_damage_factor),
        "governing_source":"equal" if x.base_material_thinning_damage_factor == x.lining_damage_factor else "lining" if x.lining_damage_factor < x.base_material_thinning_damage_factor else "base_material_thinning"}


class LiningAssessment(Model):
    lining_type: LiningType
    applicability_basis: str = Field(min_length=1)
    organic_compatible_with_environment: bool | None = None
    organic_within_design_temperature_including_steamout: bool | None = None
    organic_properly_applied_and_cured: bool | None = None
    age: LiningAge
    lookup_policy: Lookup
    first_year_policy: FirstYear
    first_year_qualification_basis: str | None = None
    condition: LiningCondition
    monitoring: LiningMonitoring
    base_material_thinning_damage_factor: NonNegative
    base_material_thinning_basis: str = Field(min_length=1)


@calculation("damage/lining-assessment", "Compose lining age base factor condition monitoring and governing thinning", LiningAssessment,
    ["Part2 §§5.1-5.5,eq(2.24),Tables5.4-5.6,Figure5.1; PDF pp166-171"],origin="api581_composition_with_explicit_age_policies",limitations=[
        "Compatible protective lining must be owner-qualified. Organic compatibility, temperature including steamout and proper application/curing must all be affirmed; false/unknown rejects source-assumption credit. Date history only resets per explicit source-interpretation policy and qualified A/B inspection. No automatic inspection-method classification or actual lining degradation-rate model. Base tables1..25years; interpolation/first-year policies explicit. LiningDF=base*condition*monitoring, then governing thinning=min(base-metal thinningDF,liningDF), not sum or product of both DFs. No.1 floor or automatic all-mechanism DF. Cladding/overlay sequential wall-loss calculations are distinct."])
def assessment(x):
    ensure(bool(x.applicability_basis.strip()) and bool(x.base_material_thinning_basis.strip()),"Applicability and base-material thinning basis must be nonblank")
    organic = x.lining_type.startswith("organic_")
    ensure(x.age.lining_family == ("organic" if organic else "inorganic"),"Lining type and age family must agree with source table grouping")
    flags = (x.organic_compatible_with_environment,x.organic_within_design_temperature_including_steamout,x.organic_properly_applied_and_cured)
    ensure(all(v is True for v in flags) if organic else all(v is None for v in flags),"Organic assumptions must all be affirmed for organic lining and omitted for inorganic table types")
    age = effective_age(x.age)
    base = base_factor(LiningBase(lining_type=x.lining_type,age_years=age["effective_age_years"],lookup_policy=x.lookup_policy,
        first_year_policy=x.first_year_policy,first_year_qualification_basis=x.first_year_qualification_basis))
    condition, monitoring = condition_factor(x.condition),monitoring_factor(x.monitoring)
    # Reuse the established eq2.24 calculation after the stronger qualification gates.
    result = lining_adjust(LiningAdjustment(base_damage_factor=base["base_damage_factor"],condition=x.condition.condition,
        effective_online_monitoring=monitoring["monitoring_factor"] == .1))
    finite_tree(result)
    governing = governing_thinning(GoverningLining(base_material_thinning_damage_factor=x.base_material_thinning_damage_factor,lining_damage_factor=result["lining_damage_factor"]))
    return {**age,**base,**condition,**monitoring,**result,**governing,"base_material_thinning_damage_factor":x.base_material_thinning_damage_factor}
