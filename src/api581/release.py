"""Single-phase source calculations. Internal units: SI, absolute pressures."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

R = 8.31446261815324  # J/(mol K); molecular weight API uses kg/kmol, hence R*1000


class HoleSizeSelection(Model):
    """Actual opening to API 581 Table 4.4/4.4M release-hole class."""
    hole_diameter_m: NonNegative
    component_diameter_m: Positive
    diameter_basis: Literal["printed_si", "printed_us_converted"]


@calculation("release/hole-size-selection", "Release hole class and representative diameter",
             HoleSizeSelection,
             ["Part 3 §4.2, Table 4.4/Table 4.4M; PDF p518"],
             limitations=[
                 "The measured opening is supplied in metres; diameter_basis selects the printed SI millimetre or US inch boundaries. Exact upper boundaries belong to the lower class. Rupture representative diameter is min(component diameter, 406 mm/16 in); this class selection does not calculate an orifice rate or infer component geometry."])
def hole_size_selection(x):
    if x.diameter_basis == "printed_si":
        small, medium, large = .0064, .025, .102
        upper_small, upper_medium, upper_large = .0064, .051, .152
        basis_name = "Table 4.4M"
    else:
        small, medium, large = .00635, .0254, .1016
        upper_small, upper_medium, upper_large = .00635, .0508, .1524
        basis_name = "Table 4.4"
    d = x.hole_diameter_m
    if d <= upper_small:
        hole, representative = "small", small
        lower, upper = 0., upper_small
    elif d <= upper_medium:
        hole, representative = "medium", medium
        lower, upper = upper_small, upper_medium
    elif d <= upper_large:
        hole, representative = "large", large
        lower, upper = upper_medium, upper_large
    else:
        hole, representative = "rupture", min(x.component_diameter_m, .4064)
        lower, upper = upper_large, None
    return {"selected_hole": hole, "representative_diameter_m": representative,
            "lower_bound_m": lower, "upper_bound_m": upper,
            "diameter_basis": x.diameter_basis, "source_table": basis_name}


class DetectionIsolationRating(Model):
    """Qualitative Table 4.5 detection and isolation classification."""
    detection_type: Literal[
        "process_instrumentation",
        "outside_envelope_detector",
        "visual_or_marginal"]
    isolation_type: Literal[
        "automatic_instrument_or_detector",
        "remote_operator",
        "manual_valve"]
    qualification_basis: str = Field(min_length=1, max_length=1000)


@calculation("release/detection-isolation-rating", "Table 4.5 detection and isolation system classification",
             DetectionIsolationRating,
             ["Part 3 Table 4.5; PDF p519"],
             limitations=[
                 "Maps only the printed qualitative descriptions to A/B/C. It does not inspect plant instrumentation, coverage, response time or proof-test data; those remain owner-qualified evidence in qualification_basis."])
def detection_isolation_rating(x):
    ensure(x.qualification_basis.strip(), "Detection/isolation qualification basis must be nonblank")
    detection = {
        "process_instrumentation": "A",
        "outside_envelope_detector": "B",
        "visual_or_marginal": "C",
    }[x.detection_type]
    isolation = {
        "automatic_instrument_or_detector": "A",
        "remote_operator": "B",
        "manual_valve": "C",
    }[x.isolation_type]
    return {"detection_rating": detection, "isolation_rating": isolation,
            "detection_type": x.detection_type, "isolation_type": x.isolation_type,
            "qualification_basis": x.qualification_basis}


class Orifice(Model):
    diameter_m: NonNegative


@calculation("release/orifice-area", "Circular release area", Orifice, ["Part 3 eq (3.8)"])
def orifice(x):
    return {"area_m2": math.pi * x.diameter_m ** 2 / 4}


class Viscosity(Model):
    reynolds_number: Positive


@calculation("release/viscosity-factor", "Liquid viscosity correction", Viscosity,
             ["Part 3 eq (3.4); PDF p485"])
def viscosity(x):
    re = x.reynolds_number
    return {"viscosity_factor": 1 / (.9935 + 2.878 / math.sqrt(re) + 342.75 / re ** 1.5)}


class Liquid(Model):
    diameter_m: NonNegative
    upstream_pressure_pa_abs: Positive
    downstream_pressure_pa_abs: Positive = 101325
    density_kg_m3: Positive
    discharge_coefficient: Fraction = .61
    viscosity_factor: Positive = 1


@calculation("release/liquid", "Liquid orifice mass release rate", Liquid,
             ["Part 3 §4.3.2 eq (3.3); PDF p485"],
             limitations=["Steady upstream state; no line friction, flash fraction or pool evaporation calculation."])
def liquid(x):
    ensure(x.upstream_pressure_pa_abs >= x.downstream_pressure_pa_abs, "Upstream pressure must be >= downstream pressure")
    area = orifice(Orifice(diameter_m=x.diameter_m))["area_m2"]
    rate = x.discharge_coefficient * x.viscosity_factor * area * math.sqrt(
        2 * x.density_kg_m3 * (x.upstream_pressure_pa_abs - x.downstream_pressure_pa_abs))
    return {"mass_rate_kg_s": rate, "area_m2": area, "regime": "liquid"}


class Gas(Model):
    diameter_m: NonNegative
    upstream_pressure_pa_abs: Positive
    downstream_pressure_pa_abs: Positive = 101325
    temperature_k: Positive
    molecular_weight_kg_kmol: Positive
    heat_capacity_ratio: Positive = Field(gt=1)
    discharge_coefficient: Fraction = .9


@calculation("release/gas", "Sonic or subsonic ideal-gas release", Gas,
             ["Part 3 §4.3.3 eqs (3.5)-(3.7); PDF p486"],
             limitations=["Ideal gas, constant upstream state; not a two-phase or real-gas near-critical model."])
def gas(x):
    p, back, k = x.upstream_pressure_pa_abs, x.downstream_pressure_pa_abs, x.heat_capacity_ratio
    ensure(p >= back, "Upstream pressure must be >= downstream pressure")
    ratio = back / p
    critical = (2 / (k + 1)) ** (k / (k - 1))
    area = orifice(Orifice(diameter_m=x.diameter_m))["area_m2"]
    specific_r = R * 1000 / x.molecular_weight_kg_kmol
    if ratio <= critical:
        factor = k * (2 / (k + 1)) ** ((k + 1) / (k - 1))
        regime = "sonic"
    else:
        # expm1 avoids cancellation as upstream approaches downstream pressure.
        factor = 2 * k / (k - 1) * ratio ** (2 / k) * (-math.expm1((k - 1) / k * math.log(ratio)))
        regime = "subsonic"
    rate = x.discharge_coefficient * area * p * math.sqrt(max(0, factor) / (specific_r * x.temperature_k))
    return {"mass_rate_kg_s": rate, "area_m2": area, "regime": regime,
            "critical_downstream_upstream_ratio": critical, "transition_pressure_pa_abs": back / critical}


class HeatCapacity(Model):
    cp_j_mol_k: Positive


@calculation("properties/heat-capacity-ratio", "Ideal-gas specific heat ratio", HeatCapacity,
             ["Part 3 eq (3.1)"])
def heat_capacity(x):
    ensure(x.cp_j_mol_k > R, "Molar Cp must exceed R")
    return {"heat_capacity_ratio": x.cp_j_mol_k / (x.cp_j_mol_k - R)}


class AvailableInventory(Model):
    component_mass_kg: NonNegative
    inventory_group_mass_kg: NonNegative
    release_rate_kg_s: NonNegative
    eight_inch_rate_kg_s: NonNegative


@calculation("release/available-inventory", "Maximum available mass", AvailableInventory,
             ["Part 3 §4.4.2 eqs (3.10)-(3.11); PDF p487"])
def inventory(x):
    ensure(x.inventory_group_mass_kg >= x.component_mass_kg, "Inventory group must include component mass")
    added = 180 * min(x.release_rate_kg_s, x.eight_inch_rate_kg_s)
    return {"added_mass_kg": added, "available_mass_kg": min(x.component_mass_kg + added, x.inventory_group_mass_kg)}


class ReleaseType(Model):
    diameter_m: NonNegative
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative


@calculation("release/type", "Continuous or instantaneous release classification", ReleaseType,
             ["Part 3 §4.5.2 eq (3.12); PDF p488"], limitations=["Uses the text's rounded 4536 kg threshold."])
def release_type(x):
    time = 4536 / x.theoretical_rate_kg_s if x.theoretical_rate_kg_s else None
    instant = x.diameter_m > .00635 and time is not None and time <= 180 and x.available_mass_kg > 4536
    return {"release_type": "instantaneous" if instant else "continuous", "time_to_4536kg_s": time}


class ReleaseMagnitude(Model):
    theoretical_rate_kg_s: NonNegative
    reduction_fraction: Fraction
    available_mass_kg: NonNegative
    maximum_duration_s: NonNegative


@calculation("release/magnitude", "Adjusted release rate, duration and mass", ReleaseMagnitude,
             ["Part 3 §4.7 eqs (3.13)-(3.15); PDF p490"],
             limitations=["Detection reduction and maximum duration supplied by caller, not yet selected from Tables 4.6/4.7."])
def magnitude(x):
    rate = x.theoretical_rate_kg_s * (1 - x.reduction_fraction)
    duration = min(x.maximum_duration_s, x.available_mass_kg / rate) if rate else 0
    return {"adjusted_rate_kg_s": rate, "duration_s": duration,
            "released_mass_kg": min(x.available_mass_kg, rate * duration)}


class DetectionIsolation(Model):
    """API 581 Table 4.6/4.7M detection and isolation selection."""
    detection_rating: Literal["A", "B", "C"]
    isolation_rating: Literal["A", "B", "C"]
    hole_size: Literal["small", "medium", "large", "rupture"]
    theoretical_rate_kg_s: NonNegative
    available_mass_kg: NonNegative


@calculation("release/detection-isolation", "Detection/isolation release reduction and maximum leak duration",
             DetectionIsolation,
             ["Part 3 §4.6.2-§4.6.6, Tables 4.6/4.7M; PDF pp488-490,520"],
             limitations=[
                 "Uses the printed SI Table 4.7M hole classes (6.4, 25 and 102 mm). A rupture hole has no maximum duration in Table 4.7M, so its instantaneous released mass is the available mass and duration is null. Ratings are supplied after the qualitative Table 4.5 screening; no detector/isolation hardware classification is inferred."])
def detection_isolation(x):
    d, i = x.detection_rating, x.isolation_rating
    # Table 4.6: release magnitude reduction factor fact_di.
    reduction = {
        ("A", "A"): .25, ("A", "B"): .20, ("A", "C"): .10,
        ("B", "A"): .10, ("B", "B"): .15, ("B", "C"): .10,
        ("C", "A"): .00, ("C", "B"): .00, ("C", "C"): .00,
    }[(d, i)]
    # Table 4.7M, seconds; the rupture row intentionally has no duration.
    duration_by_rating = {
        ("A", "A"): {"small": 20*60, "medium": 10*60, "large": 5*60},
        ("A", "B"): {"small": 30*60, "medium": 20*60, "large": 10*60},
        ("A", "C"): {"small": 40*60, "medium": 30*60, "large": 20*60},
        ("B", "A"): {"small": 40*60, "medium": 30*60, "large": 20*60},
        ("B", "B"): {"small": 40*60, "medium": 30*60, "large": 20*60},
        ("B", "C"): {"small": 60*60, "medium": 30*60, "large": 20*60},
        ("C", "A"): {"small": 40*60, "medium": 20*60},
        ("C", "B"): {"small": 40*60, "medium": 20*60},
        ("C", "C"): {"small": 40*60, "medium": 20*60},
    }
    maximum_duration = duration_by_rating[(d, i)].get(x.hole_size)
    adjusted_rate = x.theoretical_rate_kg_s * (1 - reduction)
    if x.hole_size == "rupture":
        duration = None
        released = x.available_mass_kg
    elif adjusted_rate == 0:
        duration = 0.
        released = 0.
    else:
        duration = min(maximum_duration, x.available_mass_kg / adjusted_rate)
        released = min(x.available_mass_kg, adjusted_rate * duration)
    return {"release_reduction_fraction": reduction,
            "adjusted_rate_kg_s": adjusted_rate,
            "maximum_leak_duration_s": maximum_duration,
            "duration_s": duration,
            "released_mass_kg": released,
            "detection_rating": d, "isolation_rating": i, "hole_size": x.hole_size}


class TimePoint(Model):
    time_s: NonNegative
    rate_kg_s: NonNegative


class Transient(Model):
    points: list[TimePoint] = Field(min_length=2, max_length=10000)
    available_mass_kg: NonNegative


@calculation("release/integrate-profile", "Integrate a piecewise-linear release profile", Transient,
             ["Part 3 §4.7.3 Calculation of Release Rate and Mass", "Part 3 §5.7.3 Calculation of Jet Release Rate and Pool Release Rate"],
             origin="engineering_utility", limitations=["Profile supplied externally; not a vessel blowdown solver. Inventory exceedance is rejected, not clipped."])
def integrate_profile(x):
    ensure(x.points[0].time_s == 0, "Profile must start at time 0")
    intervals = []
    for left, right in zip(x.points, x.points[1:]):
        ensure(right.time_s > left.time_s, "Profile times must strictly increase")
        intervals.append((right.time_s - left.time_s) * (left.rate_kg_s + right.rate_kg_s) / 2)
    mass = math.fsum(intervals)
    ensure(mass <= x.available_mass_kg + max(1e-9, 1e-9 * x.available_mass_kg), "Profile exceeds available inventory")
    return {"released_mass_kg": mass, "duration_s": x.points[-1].time_s}


class MixtureComponent(Model):
    mole_fraction: Fraction
    molecular_weight_kg_kmol: Positive


class Mixture(Model):
    components: list[MixtureComponent] = Field(min_length=1, max_length=100)


@calculation("properties/mixture-molecular-weight", "Mole-weighted mixture and mass fractions", Mixture,
             ["Part 3 §4.1.2, §4.9.4; mixture molecular-weight and mass-fraction inputs"],
             origin="api581_input_preparation",
             limitations=["Mole fractions and component molecular weights are supplied by the caller; this does not select a representative fluid or perform Level 2 thermodynamic flash."])
def mixture(x):
    ensure(math.isclose(math.fsum(c.mole_fraction for c in x.components), 1, abs_tol=1e-9), "Mole fractions must sum to 1")
    mw = math.fsum(c.mole_fraction * c.molecular_weight_kg_kmol for c in x.components)
    return {"molecular_weight_kg_kmol": mw,
            "mass_fractions": [c.mole_fraction * c.molecular_weight_kg_kmol / mw for c in x.components]}
