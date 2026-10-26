"""AST environmental allocation and bottom repair; native volume unit is bbl."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

HOLES = ("small", "medium", "large", "rupture")
Hole = Literal["small", "medium", "large", "rupture"]
LOCATIONS = ("in_dike", "surface_on_site", "surface_off_site", "subsoil", "groundwater", "surface_water")
Location = Literal["in_dike", "surface_on_site", "surface_off_site", "subsoil", "groundwater", "surface_water"]
_COSTS = {"low": (10, 50, 100, 500, 1000, 500),
          "medium": (10, 50, 250, 1500, 5000, 1500),
          "high": (10, 50, 500, 3000, 10000, 5000)}


class EnvironmentalCostTable(Model):
    sensitivity: Literal["low", "medium", "high"]


@calculation("tank/environment-cost-table", "AST estimated environmental costs in source USD/bbl", EnvironmentalCostTable,
    ["Part3 Table6.6; PDF p608"], limitations=["Historical source estimates, not current prices. Source supplies no explicit price year for Table6.6; no 2001 assumption is inferred from repair Table4.15. End user must qualify applicability and escalation."])
def environment_cost_table(x):
    return {"cost_by_location_usd_per_bbl": dict(zip(LOCATIONS, _COSTS[x.sensitivity]))}


class SurfaceSpill(Model):
    released_volume_bbl: NonNegative
    fraction_leaving_dike: Fraction
    fraction_on_site: Fraction
    fraction_off_site: Fraction


@calculation("tank/surface-spill-partition", "Sequential AST surface spill allocation", SurfaceSpill,
    ["Part3 eqs(3.232)-(3.235),(3.238)-(3.241); PDF pp599-600"],
    limitations=["Fractions are conditional: on-site applies to volume leaving dike; off-site applies to what remains after on-site. Use fractions0..1, not percentage numbers0..100. No dike capacity or surface transport simulation."])
def surface_spill(x):
    return _surface(x, x.released_volume_bbl)


class GroundwaterArrival(Model):
    distance_to_groundwater_m: NonNegative
    seepage_velocity_m_day: NonNegative


@calculation("tank/groundwater-arrival", "AST seepage travel time to groundwater", GroundwaterArrival,
    ["Part3 eq(3.244); PDF p601"], limitations=["Zero distance means already at groundwater; positive distance with zero velocity returns null arrival time, not infinity. No plume, retardation or groundwater migration model."])
def groundwater_arrival(x):
    if x.distance_to_groundwater_m == 0:
        return {"arrival_time_days": 0, "arrival_status": "already_at_groundwater"}
    if x.seepage_velocity_m_day == 0:
        return {"arrival_time_days": None, "arrival_status": "no_finite_arrival"}
    arrival = x.distance_to_groundwater_m/x.seepage_velocity_m_day
    ensure(math.isfinite(arrival) and arrival > 0, "Groundwater travel time outside numerical range", "numerical_failure")
    return {"arrival_time_days": arrival, "arrival_status": "finite_travel"}


class SubsurfaceSpill(Model):
    leaked_volume_bbl: NonNegative
    detection_time_days: Positive
    groundwater_arrival_time_days: NonNegative | None


@calculation("tank/subsurface-spill-partition", "AST bottom leakage allocation to groundwater and subsoil", SubsurfaceSpill,
    ["Part3 eqs(3.245)-(3.247); PDF p601"], limitations=["Printed detection time is the denominator, even if inventory depletion limits actual leak duration. This is not a transient transport solution. Null arrival means no finite arrival. Positive detection time required; zero-volume leakage returns zero in both compartments."])
def subsurface_spill(x):
    arrival = x.groundwater_arrival_time_days
    fraction = 0 if arrival is None or arrival >= x.detection_time_days else 1-arrival/x.detection_time_days
    groundwater = x.leaked_volume_bbl*fraction
    return {"groundwater_bbl": groundwater, "subsoil_bbl": x.leaked_volume_bbl-groundwater,
            "groundwater_fraction": fraction}


class FrequencyWeights(Model):
    generic_frequency_by_hole_per_year: dict[Hole, NonNegative]


def _weights(x):
    rates = x.generic_frequency_by_hole_per_year
    ensure(set(rates) == set(HOLES), "Exactly small, medium, large and rupture frequencies required", "incomplete_hole_set")
    scale = max(rates.values())
    ensure(scale > 0, "Total generic frequency must be positive")
    scaled = {h: rates[h]/scale for h in HOLES}
    total = math.fsum(scaled.values())
    return {h: scaled[h]/total for h in HOLES}


class EnvironmentalBasis(FrequencyWeights):
    cost_by_location_per_bbl: dict[Location, NonNegative]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis: str = Field(min_length=1, max_length=500)
    fraction_leaving_dike: Fraction
    fraction_on_site: Fraction
    fraction_off_site: Fraction


def _check_costs(x):
    ensure(set(x.cost_by_location_per_bbl) == set(LOCATIONS), "All six environmental cost locations required", "incomplete_cost_set")
    ensure(bool(x.cost_basis.strip()), "Cost basis must identify source or qualified valuation")


def _surface(x, volume):
    outside = volume*x.fraction_leaving_dike
    after_on_site = outside*(1-x.fraction_on_site)
    return {"in_dike_bbl": volume*(1-x.fraction_leaving_dike),
            "surface_on_site_bbl": outside*x.fraction_on_site,
            "surface_off_site_bbl": after_on_site*x.fraction_off_site,
            "surface_water_bbl": after_on_site*(1-x.fraction_off_site)}


def _surface_cost(x, volumes):
    return math.fsum(volumes[k+"_bbl"]*x.cost_by_location_per_bbl[k]
                     for k in ("in_dike", "surface_on_site", "surface_off_site", "surface_water"))


class ShellEnvironment(EnvironmentalBasis):
    released_volume_by_hole_bbl: dict[Hole, NonNegative]


_ENV_LIMITS = ["Caller supplies qualified per-hole GFF; total is their sum (eq3.208), including rupture in leak denominator. No ambiguous printed tank-total lookup. Frequencies are normalized once; no ignition probability applied.",
               "Costs are per bbl in one declared currency and caller-declared cost basis. No implicit escalation, FX conversion or current-price claim. Table6.6 values require owner qualification."]


@calculation("tank/shell-environment-cost", "GFF-weighted AST shell environmental consequence", ShellEnvironment,
    ["Part3 eqs(3.208),(3.231)-(3.243); PDF pp593,599-600"], limitations=_ENV_LIMITS)
def shell_environment(x):
    _check_costs(x)
    weights = _weights(x)
    ensure(set(x.released_volume_by_hole_bbl) == set(HOLES), "Exactly four released-volume holes required", "incomplete_hole_set")
    leak = math.fsum(weights[h]*x.released_volume_by_hole_bbl[h] for h in HOLES[:3])
    rupture = weights["rupture"]*x.released_volume_by_hole_bbl["rupture"]
    leak_volumes, rupture_volumes = _surface(x, leak), _surface(x, rupture)
    leak_cost, rupture_cost = _surface_cost(x, leak_volumes), _surface_cost(x, rupture_volumes)
    return {"weighted_leak_volume_bbl": leak, "weighted_rupture_volume_bbl": rupture,
            "weighted_leak_surface_volumes_bbl": leak_volumes, "weighted_rupture_surface_volumes_bbl": rupture_volumes,
            "leak_environment_cost": leak_cost, "rupture_environment_cost": rupture_cost,
            "environment_cost": leak_cost+rupture_cost, "currency": x.currency, "cost_basis": x.cost_basis}


class BottomEnvironment(EnvironmentalBasis):
    leaked_volume_by_hole_bbl: dict[Literal["small", "medium", "large"], NonNegative]
    total_tank_volume_bbl: NonNegative
    detection_time_days: Positive
    groundwater_arrival_time_days: NonNegative | None


@calculation("tank/bottom-environment-cost", "GFF-weighted AST bottom environmental consequence", BottomEnvironment,
    ["Part3 eqs(3.238)-(3.249); PDF pp600-601"], limitations=_ENV_LIMITS+[
        "Bottom leaks enter subsoil/groundwater; rupture releases total tank inventory to four surface locations. Printed detection-time partition retained despite inventory-limited release duration. Surrounding-equipment and injury costs are not applicable to bottom assessment; this API returns environmental cost only."])
def bottom_environment(x):
    _check_costs(x)
    weights = _weights(x)
    ensure(set(x.leaked_volume_by_hole_bbl) == set(HOLES[:3]), "Exactly three leakage holes required", "incomplete_hole_set")
    parts = {h: subsurface_spill(SubsurfaceSpill(leaked_volume_bbl=x.leaked_volume_by_hole_bbl[h],
        detection_time_days=x.detection_time_days, groundwater_arrival_time_days=x.groundwater_arrival_time_days)) for h in HOLES[:3]}
    groundwater = math.fsum(weights[h]*parts[h]["groundwater_bbl"] for h in HOLES[:3])
    subsoil = math.fsum(weights[h]*parts[h]["subsoil_bbl"] for h in HOLES[:3])
    leak_cost = math.fsum((groundwater*x.cost_by_location_per_bbl["groundwater"], subsoil*x.cost_by_location_per_bbl["subsoil"]))
    rupture = weights["rupture"]*x.total_tank_volume_bbl
    rupture_volumes = _surface(x, rupture)
    rupture_cost = _surface_cost(x, rupture_volumes)
    return {"weighted_groundwater_volume_bbl": groundwater, "weighted_subsoil_volume_bbl": subsoil,
            "weighted_rupture_volume_bbl": rupture, "weighted_rupture_surface_volumes_bbl": rupture_volumes,
            "leak_environment_cost": leak_cost, "rupture_environment_cost": rupture_cost,
            "environment_cost": leak_cost+rupture_cost, "currency": x.currency, "cost_basis": x.cost_basis}


class BottomRepair(FrequencyWeights):
    tank_diameter_m: Positive
    repair_cost_by_hole: dict[Hole, NonNegative]
    material_factor: Positive
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis: str = Field(min_length=1, max_length=500)


@calculation("tank/bottom-repair-cost", "AST bottom repair with rupture-only diameter scaling", BottomRepair,
    ["Part3 eq(3.250),Tables4.15/4.16,Annex3.B C36; PDF pp532-533,601,649"], limitations=[
        "Caller supplies all four repair costs and qualified GFF. Only rupture cost scales by (D/30.5m)^2; small/medium/large repair costs do not. Historical financial/repair-table returns USD2001; caller must explicitly qualify escalation/currency and retain consistent cost basis."])
def bottom_repair(x):
    weights = _weights(x)
    ensure(set(x.repair_cost_by_hole) == set(HOLES), "Exactly four repair cost holes required", "incomplete_hole_set")
    ensure(bool(x.cost_basis.strip()), "Cost basis must identify source or qualified valuation")
    # Avoid squaring diameter when rupture contributes nothing.
    rupture = weights["rupture"]*x.repair_cost_by_hole["rupture"]
    rupture = 0 if rupture == 0 else rupture*(x.tank_diameter_m/30.5)**2
    cost = math.fsum([weights[h]*x.repair_cost_by_hole[h] for h in HOLES[:3]]+[rupture])*x.material_factor
    return {"component_repair_cost": cost, "currency": x.currency, "cost_basis": x.cost_basis}
