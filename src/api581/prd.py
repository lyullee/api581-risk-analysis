"""Part 1 §7 pressure-relief-device reliability primitives."""
import math
from typing import Literal
from pydantic import Field, StrictBool
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .pof import Weibull, weibull, HOLES

Device = Literal["conventional", "balanced_bellows", "pilot_operated", "rupture_disk"]
Mode = Literal["fail_to_open", "leak"]
Severity = Literal["mild", "moderate", "severe"]


class PrdDefaults(Model):
    device_type: Device
    failure_mode: Mode
    severity: Severity
    closed_system_or_flare: StrictBool = False
    soft_seated: StrictBool = False


@calculation("prd/default-weibull", "PRD default Weibull parameters and design modifiers", PrdDefaults,
             ["Part 1 Tables 7.5,7.12; §7.2.4(g),§7.3.2(g); PDF pp53,62,83,87"],
             limitations=["Owner selects severity independently for FAIL and LEAK. Uses printed rounded pilot-operated eta (33.7,8.0,3.5), not another division of these entries. Closed-system factor .75 applies only to conventional FAIL; soft-seat factor 1.25 only to conventional/balanced LEAK. Environmental and inspection adjustments are separate."])
def prd_defaults(x):
    i = ("mild","moderate","severe").index(x.severity)
    if x.failure_mode == "fail_to_open":
        shape = 1.8
        eta = 50.5 if x.device_type == "rupture_disk" else ((33.7,8,3.5) if x.device_type == "pilot_operated" else (50.5,23.9,17.6))[i]
        factor = .75 if x.device_type == "conventional" and x.closed_system_or_flare else 1
    else:
        shape = 1.6
        eta = 17.5 if x.device_type == "rupture_disk" else ((16,14,11.5) if x.device_type == "balanced_bellows" else (17.5,15.5,13.1))[i]
        factor = 1.25 if x.soft_seated and x.device_type in ("conventional","balanced_bellows") else 1
    return {"shape":shape,"default_characteristic_life_years":eta,"design_factor":factor,
            "design_adjusted_characteristic_life_years":eta*factor}


class PrdEnvironment(Model):
    device_type: Device
    failure_mode: Mode
    operating_temperature_k: Positive
    operating_to_set_pressure_ratio: NonNegative
    installed_piping_vibration: StrictBool
    pulsating_or_cyclic_service: StrictBool
    actuations_per_year: NonNegative
    history_of_chatter: StrictBool
    qualified_pilot_high_ratio_exception: StrictBool = False


@calculation("prd/environment-factor", "PRD environmental characteristic-life modifier", PrdEnvironment,
             ["Part 1 Table 7.6; PDF p83"],
             limitations=["Products of applicable modifiers. LEAK excessive-actuation modifier is not reapplied when operating-ratio modifier applies (Table7.6 note2). Pilot high-ratio exception must be explicitly qualified. Printed strict 200<T<500 F and T>500 F leave exactly 500 F unresolved for LEAK; it is rejected. FAIL does not use temperature/ratio/vibration/cyclic factors."])
def prd_environment(x):
    ensure(not x.qualified_pilot_high_ratio_exception or x.device_type == "pilot_operated", "High operating-ratio exception applies only to qualified pilot-operated devices")
    factors = {"chatter":.5 if x.history_of_chatter else 1,
               "excessive_actuation":.5 if x.actuations_per_year > 5 else 1}
    if x.failure_mode == "leak":
        t200 = (200-32)*5/9+273.15
        t500 = (500-32)*5/9+273.15
        ensure(not math.isclose(x.operating_temperature_k,t500,rel_tol=0,abs_tol=1e-9),
               "Exactly 500 F is not assigned by printed Table7.6 temperature bands", "unresolved_applicability")
        threshold = .95 if x.device_type == "pilot_operated" else .9
        ratio_applies = x.device_type != "rupture_disk" and x.operating_to_set_pressure_ratio > threshold and not x.qualified_pilot_high_ratio_exception
        factors.update(temperature=.6 if x.operating_temperature_k > t500 else (.8 if x.operating_temperature_k > t200 else 1),
                       operating_ratio=.5 if ratio_applies else 1,
                       vibration=.8 if x.installed_piping_vibration else 1,
                       cyclic_service=.8 if x.pulsating_or_cyclic_service else 1)
        if ratio_applies:
            factors["excessive_actuation"] = 1
    return {"environment_factor":math.prod(factors.values()),"individual_factors":factors}


class PrdSetPressure(Model):
    device_type: Device
    operating_to_set_pressure_ratio: NonNegative


@calculation("prd/set-pressure-factor", "PRD leakage set-pressure probability modifier", PrdSetPressure,
             ["Part 1 Table 7.7; eq (1.36); PDF pp61,84"],
             limitations=["Pressure ratio supplied on a consistent pressure basis. Applies to leakage probability after Weibull evaluation, not to eta. Rupture-disk factor=1."])
def prd_set_pressure(x):
    limit = .95 if x.device_type == "pilot_operated" else .9
    return {"set_pressure_factor":1 if x.device_type == "rupture_disk" else min(limit,x.operating_to_set_pressure_ratio)/limit}


class PrdOverpressure(Model):
    overpressure_to_set_pressure_ratio: Positive


@calculation("prd/overpressure-factor", "PRD fail-to-open overpressure modifier", PrdOverpressure,
             ["Part 1 §7.2.4(j); eq (1.31); PDF pp57-58"])
def prd_overpressure(x):
    return {"overpressure_factor":max(.2,min(1,1-(x.overpressure_to_set_pressure_ratio-1.3)/3.375))}


class DemandCase(Model):
    initiating_event_frequency_per_year: NonNegative
    demand_rate_reduction_factor: Fraction


class PrdDemand(Model):
    cases: list[DemandCase] = Field(min_length=1, max_length=100)


@calculation("prd/demand-rate", "PRD case and total demand rates", PrdDemand,
             ["Part 1 §7.2.3; eqs (1.12)-(1.13); PDF p50"],
             limitations=["Reduction factor is the residual fraction multiplying initiating frequency, not its reciprocal. Owner qualifies independent demand cases and LOPA credits; defaults/automatic relief-design basis are not inferred."])
def prd_demand(x):
    values = [c.initiating_event_frequency_per_year*c.demand_rate_reduction_factor for c in x.cases]
    return {"case_demand_rates_per_year":values,"total_demand_rate_per_year":math.fsum(values)}


class InspectionUpdate(Model):
    shape: Positive
    prior_characteristic_life_years: Positive
    duration_years: NonNegative
    effectiveness: Literal["ineffective", "fairly", "usually", "highly"]
    result: Literal["pass", "fail", "no_leak", "leak"]
    piping_plugged: StrictBool = False


@calculation("prd/inspection-update", "PRD single inspection characteristic-life update", InspectionUpdate,
             ["Part 1 §7.2.4(i); eqs (1.17)-(1.21); Tables7.8,7.9; PDF pp54-57,84"],
             limitations=["Implements printed eq (1.20), including CF_pass in its second term. Ineffective tests and durations<1 year get no update. Pass/no-leak cannot reduce eta, fail/leak cannot increase eta. Plugged piping overrides pass to fail. Caller sequences records and handles overhaul/as-new date and invalidation after design change. Invalid weighted probability is rejected, not clipped."])
def prd_inspection_update(x):
    prior = weibull(Weibull(shape=x.shape,characteristic_life_years=x.prior_characteristic_life_years,
        age_years=x.duration_years))["cumulative_failure_probability"]
    failed = x.piping_plugged or x.result in ("fail","leak")
    if x.effectiveness == "ineffective" or x.duration_years < 1:
        return {"prior_failure_probability":prior,"conditional_failure_probability":None,
                "weighted_failure_probability":prior,"updated_characteristic_life_years":x.prior_characteristic_life_years,
                "update_applied":False,"effective_failed_result":failed}
    pass_cf,fail_cf = {"fairly":(.5,.7),"usually":(.7,.95),"highly":(.9,.95)}[x.effectiveness]
    conditional = fail_cf*prior+(1-pass_cf)*(1-prior) if failed else (1-pass_cf)*(1-prior)
    if failed:
        weighted = .5*(prior+conditional) if x.effectiveness == "fairly" else conditional
    else:
        weighted = prior+.2*(x.duration_years/x.prior_characteristic_life_years)*(conditional-prior)
    ensure(0 < weighted < 1, "Inspection update gives probability outside open interval (0,1)", "outside_update_domain")
    eta = x.duration_years/(-math.log1p(-weighted))**(1/x.shape)
    eta = min(eta,x.prior_characteristic_life_years) if failed else max(eta,x.prior_characteristic_life_years)
    return {"prior_failure_probability":prior,"conditional_failure_probability":conditional,
            "weighted_failure_probability":weighted,"updated_characteristic_life_years":eta,
            "update_applied":True,"effective_failed_result":failed}


class ProtectedEquipment(Model):
    generic_frequencies_per_year: dict[Literal["small","medium","large","rupture"], NonNegative]
    total_damage_factor: NonNegative
    management_factor: Positive
    overpressure_to_mawp_ratio: Positive


@calculation("prd/protected-equipment", "Protected equipment overpressure loss-of-containment model", ProtectedEquipment,
             ["Part 1 §7.2.5; eqs (1.32)-(1.33); PDF p58"],
             limitations=["Uses normal damage-adjusted frequency at pressure<=MAWP; above MAWP applies printed exponential and caps source-model probability at1. Source mixes annual-frequency/probability terms; returned source_model_loc_probability follows the published model, not a Poisson conversion. Caller supplies DF at evaluation time and all four GFF holes."])
def protected_equipment(x):
    ensure(set(x.generic_frequencies_per_year)==set(HOLES), "All four generic-frequency hole rows are required")
    total = math.fsum(x.generic_frequencies_per_year.values())
    ensure(total > 0, "Generic frequency total must be positive")
    baseline = total*x.total_damage_factor*x.management_factor
    if x.overpressure_to_mawp_ratio <= 1 or baseline == 0:
        probability = min(1,baseline)
    else:
        logp = math.log(baseline)+math.log(.0312881)+3.464837*x.overpressure_to_mawp_ratio
        probability = 1 if logp >= 0 else math.exp(logp)
    return {"normal_failure_frequency_per_year":baseline,"source_model_loc_probability":probability,
            "by_hole_loc_probability":{k:probability*v/total for k,v in x.generic_frequencies_per_year.items()}}


class PrdFailFrequency(Model):
    failure_on_demand_probability: Fraction
    demand_rate_per_year: NonNegative
    protected_equipment_loc_probability: Fraction


@calculation("prd/fail-frequency", "PRD fail-to-open loss-of-containment scenario frequency", PrdFailFrequency,
             ["Part 1 §7.2.2; eq (1.11); PDF p49"],
             limitations=["One demand case: multiplies scenario-adjusted POFOD, demand rate and protected-equipment LOC model probability. Sum only justified distinct scenarios; dependencies and common-cause effects require owner analysis."])
def prd_fail_frequency(x):
    return {"annual_failure_frequency":x.failure_on_demand_probability*x.demand_rate_per_year*x.protected_equipment_loc_probability}


class BaseReliability(Model):
    defaults: PrdDefaults
    environment: PrdEnvironment
    age_years: NonNegative
    overpressure_to_set_pressure_ratio: Positive = 1.3


@calculation("prd/base-reliability", "PRD default/design/environment/scenario probability", BaseReliability,
             ["Part 1 eqs (1.14)-(1.16),(1.34)-(1.36); Tables7.5-7.7,7.12"],
             limitations=["Uninspected/default reliability path only; no implicit inspection history. Computes cumulative Weibull probability at age and applies Fop for FAIL or Fset for LEAK. LEAK result is not automatically reinterpreted as an instantaneous annual frequency. Caller supplies qualified severity, environmental and pressure inputs."])
def prd_base_reliability(x):
    ensure(x.defaults.device_type == x.environment.device_type and x.defaults.failure_mode == x.environment.failure_mode,
           "Default and environment device/failure mode must match")
    base,env = prd_defaults(x.defaults),prd_environment(x.environment)
    eta = base["design_adjusted_characteristic_life_years"]*env["environment_factor"]
    probability = weibull(Weibull(shape=base["shape"],characteristic_life_years=eta,age_years=x.age_years))["cumulative_failure_probability"]
    factor = (prd_overpressure(PrdOverpressure(overpressure_to_set_pressure_ratio=x.overpressure_to_set_pressure_ratio))["overpressure_factor"]
              if x.defaults.failure_mode == "fail_to_open" else
              prd_set_pressure(PrdSetPressure(device_type=x.defaults.device_type,operating_to_set_pressure_ratio=x.environment.operating_to_set_pressure_ratio))["set_pressure_factor"])
    return {"shape":base["shape"],"modified_characteristic_life_years":eta,"environment_factor":env["environment_factor"],
            "scenario_probability_factor":factor,"unadjusted_cumulative_probability":probability,"scenario_adjusted_probability":probability*factor}
