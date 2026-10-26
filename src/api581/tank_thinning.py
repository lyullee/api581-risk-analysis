"""2016 AST-bottom thinning: dedicated Art equation, table and adjustments."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, REGISTRY, calculation, ensure, finite_tree
from .tank_corrosion import BottomCorrosion, assessment as corrosion_assessment
from .tank_source import BottomSource
from .tank_integrated import BottomEconomics, BottomIntegrated, integrated

Grade = Literal["a","b","c","d","e"]
Lookup = Literal["exact_rows_only","linear_between_rows","conservative_upper_row"]
_ART = tuple(i/20 for i in range(21))
# Column order is E,D,C,B,A, as printed in Table4.7 (not the text's4.8).
_ROWS = (
    (.1,.1,.1,.1,.1),(4,1,.5,.4,.4),(14,3,1,.7,.7),(32,8,2,1,1),
    (56,18,6,2,1),(87,32,11,4,3),(125,53,21,9,6),(170,80,36,16,12),
    (222,115,57,29,21),(281,158,86,47,36),(347,211,124,73,58),
    (420,273,173,109,89),(500,346,234,158,133),(587,430,309,222,192),
    (681,527,401,305,270),(782,635,510,409,370),(890,757,638,538,498),
    (1005,893,789,696,658),(1126,1044,963,888,856),(1255,1209,1163,1118,1098),
    (1390,1390,1390,1390,1390))


class BottomMinimumThickness(Model):
    release_prevention_barrier: bool
    thickness_basis: Literal["api581_2016_default","documented_owner_method"]
    owner_minimum_thickness_m: Positive | None = None
    owner_method_basis: str | None = None


@calculation("tank/bottom-minimum-thickness", "AST floor minimum thickness for thinning calculation", BottomMinimumThickness,
    ["Part2 §4.5.7 STEP5(3)-(4); PDF p153"],limitations=[
        "Historical 2016 source defaults0.1in without RPB and0.05in with RPB converted exactly to SI. Owner documented alternate method permitted. Not current API653 acceptance, design-code compliance or FFS verification."])
def minimum_thickness(x):
    if x.thickness_basis == "api581_2016_default":
        ensure(x.owner_minimum_thickness_m is None and x.owner_method_basis is None,"Default thickness cannot have owner override")
        value = .00127 if x.release_prevention_barrier else .00254
    else:
        ensure(x.owner_minimum_thickness_m is not None and x.owner_method_basis is not None and bool(x.owner_method_basis.strip()),"Owner thickness requires value and documented method")
        value = x.owner_minimum_thickness_m
    return {"minimum_thickness_m":value,"thickness_basis":x.thickness_basis}


class BottomWallParameter(Model):
    starting_thickness_m: Positive
    corrosion_rate_m_year: NonNegative
    elapsed_years: NonNegative
    minimum_thickness_m: Positive
    corrosion_allowance_m: NonNegative


@calculation("tank/bottom-wall-parameter", "AST floor remaining thickness and Art parameter", BottomWallParameter,
    ["Part2 §4.5.7 STEP6(1),eq(2.12); PDF p153"],limitations=[
        "Art=max(1-(starting_thickness-rate*elapsed)/(minimum_thickness+corrosion_allowance),0). This is not non-AST fractional wall loss. Starting thickness and elapsed time must refer to same qualified baseline. Negative predicted remaining thickness is returned diagnostically; no clamp to hide penetration. Art>1 is outside the damage table and rejected by subsequent lookup."])
def wall_parameter(x):
    loss = x.corrosion_rate_m_year*x.elapsed_years
    remaining = x.starting_thickness_m-loss
    denominator = x.minimum_thickness_m+x.corrosion_allowance_m
    finite_tree([loss,remaining,denominator])
    art = max(1-remaining/denominator,0.)
    finite_tree(art)
    return {"art_parameter":art,"predicted_remaining_thickness_m":remaining,"predicted_wall_loss_m":loss,
        "reference_thickness_m":denominator,"at_or_below_minimum_thickness":remaining <= x.minimum_thickness_m,
        "predicted_penetration":remaining <= 0}


class BottomInspectionSelection(Model):
    eligible_inspection_grades: list[Grade] = Field(max_length=10000)
    eligibility_basis: str = Field(min_length=1)


@calculation("tank/bottom-inspection-selection", "Select one AST floor inspection credit", BottomInspectionSelection,
    ["Part2 §§4.5.5-4.5.6,Table4.7; PDF pp151-152,163"],limitations=[
        "Only best effectiveness of eligible inspections is credited, never stacked or Bayesian-upgraded. Empty list/E gives no credit. Caller qualifies actual inspection effectiveness under Annex2.C.5 and inclusion in baseline-to-assessment period; furnished-to-measured baseline reset does not preserve earlier inspection credit automatically."])
def inspection_selection(x):
    ensure(bool(x.eligibility_basis.strip()),"Inspection eligibility basis must not be blank")
    grade = min(x.eligible_inspection_grades,default="e")
    return {"selected_inspection_grade":grade,"credited_inspection_count":0 if grade == "e" else 1,
        "eligible_inspection_count":len(x.eligible_inspection_grades)}


class BottomBaseDamage(Model):
    art_parameter: NonNegative
    inspection_grade: Grade
    lookup_policy: Lookup


@calculation("tank/bottom-thinning-base", "AST floor tabulated base thinning damage factor", BottomBaseDamage,
    ["Part2 §4.5.7 STEP13,Table4.7; PDF pp155,163"],limitations=[
        "Uses all21x5 printed cells. STEP13 calls it Table4.8, but actual AST table is4.7; actual4.8 is online monitoring. Table covers0<=Art<=1. No extrapolation or terminal-row saturation for Art>1. Between-row handling is explicit owner numerical policy: linear, upper-row conservative, or exact-only; source gives no explicit interpolation instruction. Inspection columns assume at most one credited inspection."])
def base_damage(x):
    ensure(x.art_parameter <= 1,"AST Art exceeds1; predicted penetration is outside tabulated damage domain", "ast_damage_table_exceeded")
    i = bisect_left(_ART,x.art_parameter)
    column = "edcba".index(x.inspection_grade)
    if _ART[i] == x.art_parameter:
        lo = hi = i
        weight = 0.
        value = float(_ROWS[i][column])
    else:
        ensure(x.lookup_policy != "exact_rows_only","Art lies between table rows; choose qualified interpolation policy", "ast_damage_between_rows")
        lo, hi = i-1, i
        weight = (x.art_parameter-_ART[lo])/(_ART[hi]-_ART[lo])
        value = float(_ROWS[hi][column]) if x.lookup_policy == "conservative_upper_row" else _ROWS[lo][column]+weight*(_ROWS[hi][column]-_ROWS[lo][column])
    return {"base_damage_factor":value,"lower_art_row":_ART[lo],"upper_art_row":_ART[hi],
        "interpolation_weight":weight,"lookup_policy":x.lookup_policy}


class BottomAdjustments(Model):
    construction: Literal["welded","riveted"]
    maintained_per_api653: bool
    settlement_category: Literal["exceeds_api653","meets_api653","never_evaluated","concrete_no_settlement"]


@calculation("tank/bottom-thinning-adjustment-factors", "AST floor construction maintenance and settlement factors", BottomAdjustments,
    ["Part2 §4.5.7 STEP15(4)-(6); PDF p156"],limitations=[
        "Owner qualifies actual construction, historical API653 maintenance and settlement category. Factors are not a structural settlement assessment. Online monitoring for AST-bottom corrosion uses other-mechanism table value1 in integrated APIs; no invented monitoring credit."])
def adjustment_factors(x):
    return {"welded_construction_factor":1. if x.construction == "welded" else 10.,
        "maintenance_factor":1. if x.maintained_per_api653 else 5.,
        "settlement_factor":{"exceeds_api653":2.,"meets_api653":1.,"never_evaluated":1.5,"concrete_no_settlement":1.}[x.settlement_category]}


class BottomThinningBasis(Model):
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    baseline_basis: str = Field(min_length=1)
    corrosion_allowance_m: NonNegative
    minimum_thickness: BottomMinimumThickness
    inspections: BottomInspectionSelection
    lookup_policy: Lookup
    adjustments: BottomAdjustments


class BottomThinning(BottomThinningBasis):
    corrosion_rate_m_year: NonNegative
    corrosion_rate_basis: str = Field(min_length=1)


def _thinning(basis, rate):
    ensure(bool(basis.baseline_basis.strip()),"Thickness/time baseline basis must not be blank")
    minimum = minimum_thickness(basis.minimum_thickness)
    wall = wall_parameter(BottomWallParameter(starting_thickness_m=basis.starting_thickness_m,corrosion_rate_m_year=rate,
        elapsed_years=basis.elapsed_years,minimum_thickness_m=minimum["minimum_thickness_m"],corrosion_allowance_m=basis.corrosion_allowance_m))
    selected = inspection_selection(basis.inspections)
    base = base_damage(BottomBaseDamage(art_parameter=wall["art_parameter"],inspection_grade=selected["selected_inspection_grade"],lookup_policy=basis.lookup_policy))
    factors = adjustment_factors(basis.adjustments)
    value = base["base_damage_factor"]*factors["welded_construction_factor"]*factors["maintenance_factor"]*factors["settlement_factor"]
    finite_tree(value)
    return {**minimum,**wall,**selected,**base,**factors,"thinning_damage_factor":max(value,.1),"online_monitoring_factor":1.}


@calculation("tank/bottom-thinning-assessment", "AST floor dedicated thinning damage assessment", BottomThinning,
    ["Part2 §4.5.7,eqs(2.12),(2.23),Tables4.7-4.8; PDF pp152-156,163-164"],limitations=[
        "Carbon-steel unlined AST bottom with qualified supplied net corrosion rate. Uses dedicated table, not pressure strength-ratio/Bayesian non-AST equations. One inspection credit. Injection/deadleg factors1 as non-piping; monitoring1 for other-corrosion-mechanism row. No automatic baseline reset, coating/lining credit, variable corrosion history or all-mechanism DF. Minimum-thickness flag is diagnostic, not acceptance/FFS."])
def thinning_assessment(x):
    ensure(bool(x.corrosion_rate_basis.strip()),"Corrosion-rate basis must not be blank")
    return _thinning(x,x.corrosion_rate_m_year)


class BottomCorrosionThinning(Model):
    corrosion: BottomCorrosion
    thinning: BottomThinningBasis


@calculation("tank/bottom-corrosion-thinning-assessment", "AST floor two-sided corrosion through thinning damage", BottomCorrosionThinning,
    [*REGISTRY["tank/bottom-corrosion-assessment"].references,*REGISTRY["tank/bottom-thinning-assessment"].references],
    origin="api581_composition",limitations=[
        "Carbon-steel unlined AST floor only. Comparable baseline corrosion rates and provenance required; do not multiply already-corrected measured net rates again. RPB resistivity override and CP inspection gate enforced. Temperature and minimum-rate policies remain explicit.",
        *REGISTRY["tank/bottom-thinning-assessment"].limitations,
        "Same combined product/soil rate drives Art; same RPB status must drive corrosion and default minimum thickness. No second external-corrosion DF added for the same soil-side loss."])
def corrosion_thinning(x):
    ensure((x.corrosion.bottom_type != "single_bottom") == x.thinning.minimum_thickness.release_prevention_barrier,"RPB status must agree between corrosion and thinning")
    rate = corrosion_assessment(x.corrosion)
    finite_tree(rate)
    return {**rate,**_thinning(x.thinning,rate["combined_corrosion_rate_m_year"])}


class BottomCorrosionRisk(Model):
    damage: BottomCorrosionThinning
    source: BottomSource
    distance_to_groundwater_m: NonNegative
    economics: BottomEconomics
    management_score: NonNegative = Field(le=1000)
    damage_scope: Literal["qualified_thinning_only"]
    other_mechanisms_exclusion_basis: str = Field(min_length=1)


@calculation("tank/bottom-corrosion-risk-assessment", "AST floor corrosion through source consequence and annual financial risk", BottomCorrosionRisk,
    [*REGISTRY["tank/bottom-corrosion-thinning-assessment"].references,*REGISTRY["tank/bottom-integrated-assessment"].references],
    origin="api581_composition_with_qualified_thinning_only_scope",limitations=[
        *REGISTRY["tank/bottom-corrosion-thinning-assessment"].limitations,
        *REGISTRY["tank/bottom-source-assessment"].limitations,
        *REGISTRY["tank/bottom-financial-consequence"].limitations,
        "This composition derives DF internally for explicit qualified thinning-only scope; other applicable mechanisms must be excluded with owner basis. Uniform computed DF and Fms apply to all four holes. Annual financial risk=sum(GFF)*DF*Fms*already-GFF-weighted consequence. Single bottom, not all-mechanism or whole-tank risk. Corrosion, thickness and source RPB status must agree."])
def corrosion_risk(x):
    ensure(bool(x.other_mechanisms_exclusion_basis.strip()),"Thinning-only risk requires exclusion basis for other mechanisms")
    ensure(x.source.has_release_prevention_barrier == (x.damage.corrosion.bottom_type != "single_bottom"),"RPB status must agree between damage and release source")
    damage = corrosion_thinning(x.damage)
    finite_tree(damage)
    risk = integrated(BottomIntegrated(source=x.source,distance_to_groundwater_m=x.distance_to_groundwater_m,economics=x.economics,
        management_score=x.management_score,total_damage_factor=damage["thinning_damage_factor"],
        damage_factor_source="Same-request AST-bottom eq2.12,Table4.7,eq2.23; owner-qualified thinning-only scope"))
    return {**damage,**risk,"total_damage_factor":damage["thinning_damage_factor"],
        "integration_scope":"bottom_corrosion_thinning_source_financial_risk_qualified_thinning_only"}
