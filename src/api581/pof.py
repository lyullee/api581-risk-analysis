"""Part 1 frequency/reliability and Part 2 governing factor calculations."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure

HOLES = ("small", "medium", "large", "rupture")
STANDARD = (8e-6, 2e-5, 2e-6, 6e-7)
GFF = {k: STANDARD for k in ["COMPR", "HEXSS", "HEXTS", "PIPE-8", "PIPE-10", "PIPE-12",
       "PIPE-16", "PIPEGT16", "PUMP2S", "PUMPR", "PUMP1S", "KODRUM", "COLBTM", "FINFAN",
       "FILTER", "DRUM", "REACTOR", "COLTOP", "COLMID"]}
GFF.update({"COMPC": (8e-6, 2e-5, 2e-6, 0), "PIPE-1": (2.8e-5, 0, 0, 2.6e-6),
            "PIPE-2": (2.8e-5, 0, 0, 2.6e-6), "PIPE-4": (8e-6, 2e-5, 0, 2.6e-6),
            "PIPE-6": (8e-6, 2e-5, 0, 2.6e-6)})


class Component(Model):
    component_type: str


@calculation("frequency/generic", "Component generic failure frequencies", Component,
             ["Part 2 Table 3.1; PDF p147"], limitations=["Non-tank lookup. Tank rows with differing printed/summed totals are exposed separately by tank/generic-frequency using eq3.208. HEXTUBE is not a 2016 table entry."])
def generic(x):
    ensure(x.component_type in GFF, f"Unsupported component_type; supported: {', '.join(GFF)}")
    values = GFF[x.component_type]
    return {"by_hole_per_year": dict(zip(HOLES, values)), "total_per_year": math.fsum(values)}


class Management(Model):
    score: NonNegative = Field(le=1000)


@calculation("frequency/management-factor", "Management systems factor", Management,
             ["Part 2 §3.5.4 eqs (2.9)-(2.10); PDF p145"])
def management(x):
    percent = x.score / 10
    return {"score_percent": percent, "management_factor": 10 ** (1 - .02 * percent)}


class Frequency(Model):
    generic_frequency_per_year: NonNegative
    total_damage_factor: NonNegative
    management_factor: Positive


@calculation("frequency/adjusted", "Damage-adjusted annual failure frequency", Frequency,
             ["Part 1 eq (1.1); Part 2 eq (2.1)"], limitations=["DF is supplied by caller; this endpoint does not assess damage applicability."])
def adjusted(x):
    return {"annual_failure_frequency": x.generic_frequency_per_year * x.total_damage_factor * x.management_factor,
            "unit": "1/year"}


class PofMethodSelection(Model):
    method: Literal["structural_reliability", "statistical_generic_data", "expert_judgment", "combined"]
    qualification_basis: str = Field(min_length=1, max_length=1000)
    uncertainty_quantified: bool


@calculation(
    "frequency/pof-method-selection",
    "Probability-of-failure methodology selection",
    PofMethodSelection,
    ["Part 2 §3.2; PDF p142"],
    limitations=[
        "Records the API 581 method route and qualification evidence; it does not calculate a structural reliability probability, fit a statistical distribution, or convert expert judgment into a numeric POF. Numeric Level 1 POF remains frequency/adjusted using GFF×DF×FMS."
    ],
)
def pof_method_selection(x):
    ensure(bool(x.qualification_basis.strip()), "POF method qualification_basis must be nonblank")
    return {
        "method": x.method,
        "qualification_basis": x.qualification_basis,
        "uncertainty_quantified": x.uncertainty_quantified,
        "numeric_pof_route": "gff_df_fms" if x.method in ("statistical_generic_data", "combined") else "external_method_result",
    }


class GoverningDamage(Model):
    thinning: NonNegative
    lining: NonNegative | None = None
    external: list[NonNegative] = Field(max_length=4)
    scc: list[NonNegative] = Field(max_length=9)
    htha: NonNegative
    fatigue: NonNegative
    brittle_fracture: NonNegative
    temper_embrittlement: NonNegative
    embrittlement_885f: NonNegative
    sigma_embrittlement: NonNegative
    thinning_external_distribution: Literal["local", "general"]


@calculation("damage/combine", "Governing and total damage factors", GoverningDamage,
             ["Part 2 §3.4.2 eqs (2.2)-(2.8); PDF pp142-143"],
             limitations=["Caller must identify applicable mechanisms; empty lists mean explicitly no applicable mechanism."])
def combine(x):
    thin = min(x.thinning, x.lining) if x.lining is not None else x.thinning
    ext, scc = max(x.external, default=0), max(x.scc, default=0)
    active = lambda v: v if v > 1 else 0
    brit = max(active(x.brittle_fracture) + active(x.temper_embrittlement),
               active(x.embrittlement_885f), active(x.sigma_embrittlement))
    wall = max(thin, ext) if x.thinning_external_distribution == "local" else thin + ext
    return {"governing_thinning": thin, "governing_external": ext, "governing_scc": scc,
            "governing_brittle": brit, "total_damage_factor": wall + scc + x.htha + brit + x.fatigue}


class InspectionEquivalent(Model):
    mechanism: Literal["scc", "external_clscc", "cui_clscc", "htha"]
    a: int = Field(ge=0)
    b: int = Field(ge=0)
    c: int = Field(ge=0)
    d: int = Field(ge=0)


@calculation("inspection/equivalent", "Equivalent inspection counts", InspectionEquivalent,
             ["Part 2 §3.4.3; PDF p143"], limitations=["Not applicable to thinning or external corrosion; E inspections cannot be upgraded."])
def inspection_equivalent(x):
    d, rd = divmod(x.d, 2)
    c, rc = divmod(x.c + d, 2)
    b, rb = divmod(x.b + c, 2)
    return {"a": x.a + b, "b": rb, "c": rc, "d": rd}


class InspectionEffectivenessSummary(Model):
    mechanism: Literal["scc", "external_clscc", "cui_clscc", "htha"]
    categories: list[Literal["A", "B", "C", "D", "E"]] = Field(min_length=1, max_length=100)


@calculation(
    "inspection/effectiveness-summary",
    "Combine inspection effectiveness history into highest category and equivalent counts",
    InspectionEffectivenessSummary,
    ["Part 2 §3.4.3; Part 2 Annex C §2.C.2; PDF pp143,443-445"],
    origin="api581_inspection_effectiveness_history_composition",
    limitations=[
        "Applies the printed A-D equivalence rule used for SCC-family mechanisms: two lower-category inspections promote one step; E inspections never receive credit. It does not assess whether the individual inspection method satisfies an Annex C table.",
        "Categories must already be qualified by a mechanism-specific inspection API or owner-user review. No date, coverage, age escalation or inspection effectiveness inference is performed here."
    ],
)
def effectiveness_summary(x):
    counts = {category.lower(): x.categories.count(category) for category in "ABCDE"}
    equivalent = inspection_equivalent(InspectionEquivalent(
        mechanism=x.mechanism, a=counts["a"], b=counts["b"], c=counts["c"], d=counts["d"]
    ))
    highest = next((category for category in "ABCD" if counts[category.lower()]), "E")
    return {
        "mechanism": x.mechanism,
        "highest_effectiveness_category": highest,
        "inspection_count": len(x.categories),
        "creditable_inspection_count": sum(counts[c.lower()] for c in "ABCD"),
        "counts": counts,
        "equivalent_counts": equivalent,
        "e_inspection_count": counts["e"],
        "qualification_status": "caller_qualified_categories",
    }


class Weibull(Model):
    shape: Positive
    characteristic_life_years: Positive
    age_years: NonNegative


@calculation("reliability/weibull", "Two-parameter Weibull reliability", Weibull,
             ["Part 1 eq (1.2), §8.3.2 eq (1.56)"],
             limitations=["User-supplied parameters only; PRD environmental and inspection adjustments not included."])
def weibull(x):
    z = (x.age_years / x.characteristic_life_years) ** x.shape
    hazard = None if x.age_years == 0 and x.shape < 1 else (
        x.shape / x.characteristic_life_years * (x.age_years / x.characteristic_life_years) ** (x.shape - 1)
        if x.age_years > 0 else (1 / x.characteristic_life_years if x.shape == 1 else 0))
    return {"cumulative_failure_probability": -math.expm1(-z), "survival_probability": math.exp(-z),
            "hazard_per_year": hazard, "hazard_singular_at_origin": hazard is None}


class WeibullQuantile(Model):
    shape: Positive
    characteristic_life_years: Positive
    probability: Fraction = Field(lt=1)


@calculation("reliability/weibull-quantile", "Time to a Weibull failure probability", WeibullQuantile,
             ["Part 1 §8.3.2 eq (1.57)"])
def weibull_quantile(x):
    return {"age_years": x.characteristic_life_years * (-math.log1p(-x.probability)) ** (1 / x.shape)}


class Mttf(Model):
    shape: Positive
    mean_life_years: Positive


@calculation("reliability/weibull-from-mttf", "Convert mean life to Weibull characteristic life", Mttf,
             ["Part 1 §8.3.4.2"], origin="engineering_utility")
def from_mttf(x):
    return {"characteristic_life_years": x.mean_life_years / math.gamma(1 + 1 / x.shape)}


class Poisson(Model):
    annual_failure_frequency: NonNegative
    duration_years: NonNegative


@calculation("reliability/poisson-probability", "Constant-frequency period probability", Poisson,
             ["Part 1 §4.1 Probability of Failure", "Part 1 §4.1.2 Generic Failure Frequency Method"],
             origin="engineering_utility", limitations=["Assumes a constant-rate Poisson process; not the GFF frequency itself."])
def poisson(x):
    return {"period_failure_probability": -math.expm1(-x.annual_failure_frequency * x.duration_years)}
