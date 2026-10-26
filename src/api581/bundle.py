"""Part 1 §8 bundle life, cost and replacement planning primitives."""
import math
from typing import Literal
from pydantic import Field, StrictBool
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .pof import Weibull, weibull


class LifeRecord(Model):
    duration_years: NonNegative
    failed: StrictBool


class BundleHistory(Model):
    shape: Positive
    cycles: list[LifeRecord] = Field(min_length=2, max_length=10000)


def _eta(shape, cycles):
    failures = sum(record.failed for record in cycles)
    ensure(failures > 0, "Zero failures give no finite point estimate of characteristic life", "insufficient_failure_data")
    scale = max(record.duration_years for record in cycles)
    ensure(scale > 0, "At least one positive life duration is required")
    eta = scale*(math.fsum((record.duration_years/scale)**shape for record in cycles)/failures)**(1/shape)
    ensure(eta > 0 and math.isfinite(eta), "Characteristic life outside numerical domain", "numerical_failure")
    return eta, failures


@calculation("bundle/weibayes-history", "Fixed-shape bundle Weibayes life estimate", BundleHistory,
             ["Part 1 §8.3.4.3; eqs (1.62)-(1.63); PDF p100"],
             limitations=["At least two matched life records and one failure required; failures and right-censored suspensions enter the powered exposure sum. Owner qualifies unchanged design/material/service and externally selected shape. Does not fit shape, perform database matching, goodness-of-fit or Fisher confidence bounds."])
def bundle_history(x):
    eta, failures = _eta(x.shape, x.cycles)
    return {"shape": x.shape, "characteristic_life_years": eta,
            "failure_count": failures, "record_count": len(x.cycles)}


class BundleConditionUpdate(BundleHistory):
    predicted_failure_life_years: Positive


@calculation("bundle/condition-update", "Add inspection-predicted bundle failure point", BundleConditionUpdate,
             ["Part 1 §8.6.4(e); eqs (1.76)-(1.77); PDF pp104-105"],
             limitations=["Adds predicted total life as one additional failure point, including one additional failure in denominator. This is not another right-censored observation. Owner supplies qualified predicted total life; statistical confidence and additional uncertainty are separate."])
def bundle_condition_update(x):
    cycles = [*x.cycles, LifeRecord(duration_years=x.predicted_failure_life_years, failed=True)]
    eta, failures = _eta(x.shape, cycles)
    return {"shape":x.shape, "characteristic_life_years":eta, "failure_count":failures, "record_count":len(cycles)}


class BundleThicknessLife(Model):
    original_thickness_m: Positive
    measured_thickness_m: Positive
    service_duration_years: Positive
    remaining_wall_failure_fraction: Fraction = Field(gt=0, lt=1)
    formula_basis: Literal["printed_eq_1_72", "remaining_wall_threshold"]


@calculation("bundle/thickness-life", "Inspection-based tube thinning and predicted life", BundleThicknessLife,
             ["Part 1 §8.6.4(c); eqs (1.71)-(1.74); PDF pp103-104"],
             origin="api581_equation_or_explicit_remaining_wall_interpretation",
             limitations=["General corrosion and average tube thickness only. Printed eq (1.72) uses RWT*t_original/rate although RWT is described as remaining wall fraction; a physical threshold extrapolation uses (1-RWT)*t_original/rate. Caller must select basis explicitly. Both agree for the printed 0.5 example. Zero measured loss gives no finite extrapolated life, not a manufactured failure point."])
def bundle_thickness_life(x):
    ensure(x.measured_thickness_m <= x.original_thickness_m, "Measured thickness exceeds original; negative thinning is outside this model")
    rate = (x.original_thickness_m-x.measured_thickness_m)/x.service_duration_years
    fraction = x.remaining_wall_failure_fraction
    threshold_reached = x.measured_thickness_m <= fraction*x.original_thickness_m
    life = None if rate == 0 else ((fraction if x.formula_basis == "printed_eq_1_72" else 1-fraction)*x.original_thickness_m/rate)
    return {"thinning_rate_m_year":rate, "predicted_bundle_life_years":life,
            "remaining_life_years": None if life is None else max(0,life-x.service_duration_years),
            "remaining_wall_threshold_reached":threshold_reached, "formula_basis":x.formula_basis}


class BundleEstimatedLife(Model):
    service_duration_years: NonNegative
    estimated_remaining_life_years: NonNegative


@calculation("bundle/estimated-life", "Predicted bundle life from estimated remaining life", BundleEstimatedLife,
             ["Part 1 §8.6.4(d); eq (1.75); PDF p104"])
def bundle_estimated_life(x):
    return {"predicted_bundle_life_years": x.service_duration_years+x.estimated_remaining_life_years}


class BundleLifeExtension(Model):
    age_at_action_years: NonNegative
    life_extension_factor: Fraction
    years_since_action: NonNegative = 0


@calculation("bundle/life-extension", "Effective bundle age after life-extension action", BundleLifeExtension,
             ["Part 1 §8.6.5; eqs (1.79)-(1.81); PDF p105"],
             limitations=["Owner supplies qualified LEF. Returns effective age rather than imposing a date/day-count convention. Original age is not reset by an ordinary inspection or cleaning; apply only after a qualifying life-extension action."])
def bundle_life_extension(x):
    adjusted = (1-x.life_extension_factor)*x.age_at_action_years
    return {"adjusted_age_at_action_years":adjusted, "effective_age_years":adjusted+x.years_since_action,
            "installation_shift_years": x.age_at_action_years-adjusted}


class BundleConsequence(Model):
    daily_production_margin: NonNegative
    production_rate_reduction_fraction: Fraction
    shutdown_days: NonNegative
    environmental_cost: NonNegative
    replacement_cost: NonNegative
    maintenance_cost: NonNegative
    currency: str = Field(min_length=1, max_length=20)
    cost_basis_year: int = Field(ge=1900, le=2200, strict=True)


@calculation("bundle/consequence", "Bundle failure or planned replacement financial consequence", BundleConsequence,
             ["Part 1 §8.4.1; eqs (1.64)-(1.67), (1.88); PDF pp100-101,107"],
             limitations=["All monetary inputs must share declared currency and price year. Caller explicitly chooses planned or unplanned shutdown duration and environmental cost. No silent historical environmental default or inflation assumption."])
def bundle_consequence(x):
    production = x.daily_production_margin*x.production_rate_reduction_fraction*x.shutdown_days
    return {"production_loss_cost":production, "financial_consequence":production+x.environmental_cost+x.replacement_cost+x.maintenance_cost,
            "currency":x.currency, "cost_basis_year":x.cost_basis_year}


class BundleRisk(Model):
    shape: Positive
    characteristic_life_years: Positive
    age_years: NonNegative
    financial_consequence: NonNegative
    currency: str = Field(min_length=1, max_length=20)


@calculation("bundle/risk", "Bundle unreliability-weighted consequence", BundleRisk,
             ["Part 1 §8.5; eq (1.68); PDF p101"],
             limitations=["Weibull cumulative probability times consequence. Despite source annual-risk terminology, this product is a probability-weighted monetary amount at age, not an instantaneous annual failure-frequency risk. No confidence-bound/inspection-uncertainty shift is inferred."])
def bundle_risk(x):
    probability = weibull(Weibull(shape=x.shape, characteristic_life_years=x.characteristic_life_years,age_years=x.age_years))["cumulative_failure_probability"]
    return {"cumulative_failure_probability":probability, "probability_weighted_consequence":probability*x.financial_consequence, "currency":x.currency}


class BundleTarget(Model):
    shape: Positive
    characteristic_life_years: Positive
    target_probability_weighted_consequence: NonNegative
    financial_consequence: Positive


@calculation("bundle/target-age", "Bundle age at owner probability-weighted risk target", BundleTarget,
             ["Part 1 §8.6.1; eqs (1.57),(1.69)-(1.70); PDF pp97,102"],
             limitations=["Uses an explicitly supplied target on the same probability-weighted consequence basis as bundle/risk. Target >= consequence has no finite crossing. Owner must supply any confidence-bound/uncertainty-adjusted Weibull parameters; raw parameters are not automatically treated as 90% LBC."])
def bundle_target(x):
    ratio = x.target_probability_weighted_consequence/x.financial_consequence
    age = None if ratio >= 1 else x.characteristic_life_years*(-math.log1p(-ratio))**(1/x.shape)
    return {"target_failure_probability":min(1,ratio), "target_age_years":age,
            "status":"no_finite_crossing" if age is None else "finite_crossing"}


class BundleDeferral(Model):
    shape: Positive
    characteristic_life_years: Positive
    first_turnaround_age_years: NonNegative
    second_turnaround_age_years: Positive
    financial_consequence: NonNegative
    inspection_cost: NonNegative
    replacement_cost: NonNegative
    maintenance_cost: NonNegative
    hurdle_rate: NonNegative = 0
    currency: str = Field(min_length=1, max_length=20)


@calculation("bundle/deferral-decision", "Conditional incremental risk and inspection/replacement economics", BundleDeferral,
             ["Part 1 §8.7.2; eqs (1.82)-(1.84); PDF p106"],
             limitations=["Conditioned on survival to first turnaround; uses survival ratio, not the difference of unconditional CDFs. Source prose reverses action-cost inequality; explicit eqs (1.83)-(1.84) are followed: action cost*(1+ROR) < EIR. Both economic flags may be true; this is not an exclusive inspection plan."])
def bundle_deferral(x):
    ensure(x.second_turnaround_age_years > x.first_turnaround_age_years, "Second turnaround must follow first")
    # Compute cumulative-hazard difference without subtracting two underflowed survivals.
    a,b = x.first_turnaround_age_years,x.second_turnaround_age_years
    zb = (b/x.characteristic_life_years)**x.shape
    if a == 0:
        difference = zb
    else:
        log_ratio = math.log(a)-math.log(b) if a <= b/2 else math.log1p((a-b)/b)
        difference = zb*(-math.expm1(x.shape*log_ratio))
    probability = -math.expm1(-difference)
    risk = x.financial_consequence*probability
    inspect = (x.inspection_cost+x.maintenance_cost)*(1+x.hurdle_rate)
    replace = (x.replacement_cost+x.maintenance_cost)*(1+x.hurdle_rate)
    return {"conditional_failure_probability":probability,"expected_incremental_risk":risk,
            "inspection_hurdle_cost":inspect,"replacement_hurdle_cost":replace,
            "inspection_economically_justified":inspect < risk,"replacement_economically_justified":replace < risk,
            "currency":x.currency}


class BundleReplacement(Model):
    shape: Positive
    characteristic_life_years: Positive
    unplanned_failure_consequence: NonNegative
    planned_replacement_consequence: Positive
    step_days: Positive = 7
    maximum_replacement_age_years: Positive
    currency: str = Field(min_length=1, max_length=20)


@calculation("bundle/replacement-optimization", "Bundle planned-replacement grid cost optimization", BundleReplacement,
             ["Part 1 §8.7.4; eqs (1.85)-(1.93); PDF pp107-109"],
             limitations=["Source right-endpoint failure-life integration on uniform grid; days/year=365.24. Global minimum is over supplied finite grid only, not an unbounded certified optimum. Boundary minima are flagged. No confidence bounds, cost inflation or automatic inspection effects. Grid limited to 10000 points."])
def bundle_replacement(x):
    step = x.step_days/365.24
    count = math.floor(x.maximum_replacement_age_years/step)
    ensure(1 <= count <= 10000, "Replacement grid must contain 1-10000 points")
    fail_life, previous, samples = 0.0,0.0,[]
    for n in range(1,count+1):
        age = n*step
        z = (age/x.characteristic_life_years)**x.shape
        p,s = -math.expm1(-z),math.exp(-z)
        fail_life += age*(p-previous)
        life = fail_life+age*s
        ensure(life > 0, "Estimated service life underflow", "numerical_failure")
        cost = (x.unplanned_failure_consequence*p+x.planned_replacement_consequence*s)/(365.24*life)
        samples.append({"replacement_age_years":age,"failure_probability":p,
                        "expected_service_life_years":life,"total_cost_per_day":cost})
        previous = p
    index = min(range(len(samples)),key=lambda i:samples[i]["total_cost_per_day"])
    best = samples[index]
    return {"optimal_grid_age_years":best["replacement_age_years"],"minimum_cost_per_day":best["total_cost_per_day"],
            "minimum_at_grid_boundary":index in (0,count-1),"grid_points":count,"samples":samples,"currency":x.currency}


MATERIAL_FACTORS = {
    "Carbon Steel":1, "C-1/2 Mo":2, "1-1/4 Cr":2, "2-1/4 Cr":2.8,
    "5 Cr":3.2, "9 Cr":3.3, "12 Cr":3.4, "70/30 CuNi":3.5, "90/10 CuNi":3.5,
    "Monel 400":7, "Nickel 200":8.5, "304/309/310 SS":2.6, "304L/321/347 SS":2.8,
    "316 SS":3, "316L SS":3, "317L SS":4.2, "410/439 SS":2.8, "444 SS":3.2,
    "904L":7, "2205 Duplex SS":3, "2304 Duplex SS":2.8, "2507 Duplex SS":4,
    "AL6XN/254 SMO":7, "Seacure/E-Brite":6,
    "Admiralty Brass/Aluminum Brass/Red Brass/Muntz":2.5, "Aluminum Alloy":3,
    "Alloy 20 Cb3":6.5, "Alloy 600":9.5, "Alloy 625":11, "Alloy 800":7,
    "Alloy 825":8, "Alloy C276":11, "Ferralium 255":7, "Bimetallic":4.5,
    "Ceramic":1, "Plastic":1, "Titanium Gr. 2":6, "Titanium Gr. 12":10,
    "Titanium Gr. 16":14, "Zeron 100":4, "Zirconium Alloy":15,
}


class BundleMaterial(Model):
    material: str


@calculation("bundle/material-factor", "Bundle replacement material cost factor", BundleMaterial,
             ["Part 1 Table8.3; PDF pp119-120"],
             limitations=["Historical generic bundle factors, not current quotations or the fixed-equipment material factors. Caller may supply a different qualified factor directly to replacement-cost."])
def bundle_material(x):
    ensure(x.material in MATERIAL_FACTORS, "Unsupported material; use a printed Table8.3 material label")
    return {"material_factor":MATERIAL_FACTORS[x.material]}


class BundleReplacementCost(Model):
    shell_inside_diameter_m: Positive
    tube_length_m: Positive
    material_factor: Positive
    reference_bundle_cost_usd: NonNegative = 22000
    price_index_multiplier: Positive
    output_currency_per_usd: Positive
    output_currency: str = Field(min_length=1, max_length=20)
    output_cost_basis_year: int = Field(strict=True, ge=1900, le=2200)


@calculation("bundle/replacement-cost", "Volume/material-scaled bundle replacement cost", BundleReplacementCost,
             ["Part 1 §8.4.1; eq (1.66); PDF p101"],
             limitations=["Printed reference volume 3.016 m3 and default reference quote USD22000. Reference quote date is not inferred from edition year; caller supplies qualified price-index multiplier and FX to declared output price year/currency. This is a size/material estimate, not a vendor quote."])
def bundle_replacement_cost(x):
    volume = math.pi*x.shell_inside_diameter_m**2*x.tube_length_m/4
    reference = x.reference_bundle_cost_usd*volume*x.material_factor/3.016
    return {"bundle_volume_m3":volume,"reference_basis_cost_usd":reference,
            "replacement_cost":reference*x.price_index_multiplier*x.output_currency_per_usd,
            "currency":x.output_currency,"cost_basis_year":x.output_cost_basis_year}


class BundleExtensionFactor(Model):
    method: Literal["plug_tubes", "rotate_180", "partial_retube", "total_retube", "install_spare", "tube_ferrules"]
    ferrules_for_localized_tube_end_damage: StrictBool = False


@calculation("bundle/life-extension-factor", "Suggested bundle life-extension action factor", BundleExtensionFactor,
             ["Part 1 Table8.5 Effects of Bundle Life Extension Methods; PDF p121"],
             limitations=["This is the second table numbered8.5; inspection uncertainty is a different table. Suggested values need owner qualification. Spare factor .5 assumes unknown condition. Ferrules .75 only for localized tube-end erosion/corrosion/impingement protection."])
def bundle_extension_factor(x):
    ensure(x.method != "tube_ferrules" or x.ferrules_for_localized_tube_end_damage,
           "Ferrule LEF requires qualified protection against localized tube-end damage")
    factors={"plug_tubes":.1,"rotate_180":.5,"partial_retube":.5,"total_retube":.9,"install_spare":.5,"tube_ferrules":.75}
    return {"life_extension_factor":factors[x.method]}


class BundleCategories(Model):
    cumulative_failure_probability: Fraction
    financial_consequence_usd: NonNegative
    consequence_basis: Literal["printed_table_USD_basis"]


@calculation("bundle/categories", "Bundle probability and financial consequence categories", BundleCategories,
             ["Part 1 Table8.6; PDF p121"],
             limitations=["Uses displayed probability and financial-USD thresholds, not inconsistent DF/area footnotes. Caller explicitly declares consequence on printed USD basis; no automatic present-value inflation or FX normalization. Returns categories only; owner risk-color matrix is separate."])
def bundle_categories(x):
    p = 1+sum(x.cumulative_failure_probability > b for b in (.1,.2,.3,.5))
    c = sum(x.financial_consequence_usd > b for b in (10000,50000,150000,1000000))
    return {"probability_category":p,"consequence_category":"ABCDE"[c]}
