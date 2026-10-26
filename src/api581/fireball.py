"""Fireball radiation with explicit printed versus elevated-sphere geometry."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .effects import (FireballGeometry, fireball_geometry, FireballFraction,
                      fireball_fraction, FireballEmissive, fireball_emissive)
from .pool_fire import Atmosphere, _atmosphere

GeometryBasis = Literal["api581_printed", "elevated_sphere_maximum"]
_GEOMETRY_LIMIT = (
    "Explicit basis required: api581_printed follows eqs(3.165)-(3.166), "
    "C=.5*hypot(D,xs), F=D^2/(D^2+xs^2), without using H=.75D. "
    "elevated_sphere_maximum is a separately identified geometric interpretation: "
    "grade receiver at horizontal radius xs, sphere center H=.75D, receiver plane "
    "normal facing the center, F=(D/(2*hypot(H,xs)))^2. It is not an authorized erratum."
)


class FireballMass(Model):
    available_mass_kg: NonNegative
    flammable_mass_fraction: Fraction


@calculation("effects/fireball-mass", "Flammable mass available to a rupture fireball", FireballMass,
             ["Part3 eq(3.157); PDF p555"],
             limitations=["Mass fraction of available release inventory, not mole fraction or dispersion cloud mass. Instantaneous rupture applicability must be established by caller."])
def mass(x):
    return {"flammable_mass_kg":x.available_mass_kg*x.flammable_mass_fraction}


class SphereView(Model):
    diameter_m: Positive
    distance_m: NonNegative
    geometry_basis: GeometryBasis


@calculation("effects/fireball-view-factor", "Fireball spherical radiation view factor", SphereView,
             ["Part3 eqs(3.159),(3.165)-(3.166); PDF pp555-556"],
             origin="api581_with_explicit_fireball_geometry_basis", limitations=[_GEOMETRY_LIMIT])
def view(x):
    if x.geometry_basis == "api581_printed":
        center=.5*math.hypot(x.diameter_m,x.distance_m)
        # The printed xs is used as the attenuation path, as stated below eq(3.166).
        path=x.distance_m
    else:
        center=math.hypot(.75*x.diameter_m,x.distance_m)
        path=center-.5*x.diameter_m
    ensure(math.isfinite(center) and center > 0,"Fireball center distance outside numerical domain","numerical_failure")
    factor=(.5*x.diameter_m/center)**2
    ensure(factor > 0,"Fireball view factor underflow","numerical_failure")
    return {"view_factor":factor,"model_center_distance_m":center,
            "attenuation_path_m":path,"geometry_basis":x.geometry_basis}


class RadiationSetup(Model):
    diameter_m: Positive
    surface_emissive_power_w_m2: NonNegative
    atmosphere: Atmosphere
    geometry_basis: GeometryBasis


class FireballFlux(RadiationSetup):
    distance_m: NonNegative


def _tau(atmosphere,path):
    # Validate the chosen atmospheric parameter even at zero distance/zero energy.
    selected=_atmosphere(atmosphere,path if path > 0 else 1)
    if path == 0 and atmosphere.transmissivity_model == "api_water_vapor":
        return 1.0  # Physical cap of the zero-path limiting value.
    return selected


@calculation("effects/fireball-radiation-flux", "Fireball received thermal radiation", FireballFlux,
             ["Part3 eqs(3.140),(3.164)-(3.166); PDF pp552,555-556"],
             origin="api581_with_explicit_fireball_geometry_basis",
             limitations=[_GEOMETRY_LIMIT,
                          "Printed basis uses nominal xs for atmospheric attenuation. Elevated sphere uses center-to-receiver distance minus radius. Zero printed path uses capped limiting transmissivity1. No flame contact or LH2-specific validation."])
def flux(x):
    geometry=view(SphereView(diameter_m=x.diameter_m,distance_m=x.distance_m,geometry_basis=x.geometry_basis))
    tau=_tau(x.atmosphere,geometry["attenuation_path_m"])
    return {**geometry,"transmissivity":tau,
            "received_flux_w_m2":tau*x.surface_emissive_power_w_m2*geometry["view_factor"]}


class FireballDistance(RadiationSetup):
    threshold_w_m2: Positive
    maximum_distance_m: Positive
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


@calculation("effects/fireball-distance", "Fireball thermal threshold distance and area", FireballDistance,
             ["Part3 eqs(3.164)-(3.168); PDF pp555-556"],
             origin="api581_threshold_iteration_with_explicit_fireball_geometry_basis",
             limitations=[_GEOMETRY_LIMIT,
                          "Monotone spherical flux solution within caller maximum distance; no automatic bracket expansion. Returns safe upper bracket, with error bounded by distance_tolerance_m. Area=pi*distance^2 per printed equations; elevated-sphere distance is horizontal radius. If origin is below threshold returns zero area and no claimed threshold root."])
def distance(x):
    setup=x.model_dump(include=set(RadiationSetup.model_fields))
    def received(at):
        return flux(FireballFlux(**setup,distance_m=at))["received_flux_w_m2"]
    low,high=0.0,x.maximum_distance_m
    at_origin=received(low)
    if at_origin <= x.threshold_w_m2:
        return {"safe_distance_m":0,"consequence_area_m2":0,"status":"below_limit_at_origin",
                "iterations":0,"flux_residual_w_m2":None,"geometry_basis":x.geometry_basis}
    ensure(received(high) <= x.threshold_w_m2,"Fireball threshold not bracketed by supplied maximum distance","unbracketed_threshold")
    iterations=0
    while high-low > x.distance_tolerance_m and iterations < x.maximum_iterations:
        mid=low+(high-low)/2
        ensure(low < mid < high,"Fireball distance iteration reached floating point resolution","numerical_failure")
        if received(mid) > x.threshold_w_m2:
            low=mid
        else:
            high=mid
        iterations+=1
    ensure(high-low <= x.distance_tolerance_m,"Fireball distance did not converge","nonconvergent_threshold")
    return {"safe_distance_m":high,"consequence_area_m2":math.pi*high**2,"status":"threshold_solved",
            "iterations":iterations,"flux_residual_w_m2":received(high)-x.threshold_w_m2,"geometry_basis":x.geometry_basis}


class FireballConsequence(FireballMass):
    heat_of_combustion_j_kg: Positive
    burst_pressure_pa_abs: Positive
    atmosphere: Atmosphere
    geometry_basis: GeometryBasis
    maximum_distance_m: Positive
    personnel_threshold_w_m2: Positive = 12600
    equipment_threshold_w_m2: Positive = 37800
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


@calculation("effects/fireball-consequence", "Rupture fireball radiation consequence chain", FireballConsequence,
             ["Part3 eqs(3.157)-(3.168); PDF pp555-556"],
             origin="api581_composition_with_explicit_fireball_geometry_basis",
             limitations=[_GEOMETRY_LIMIT,
                          "Instantaneous rupture only. Caller qualifies inventory, combustion heat, and burst pressure: normal operating pressure for normal rupture or likely elevated pressure for PRD failure. Pressure correlation giving radiative fraction above1 is rejected. Constant or water-vapor atmospheric model is explicit. No ignition probability weighting, duration-dose injury model, or LH2 validation."])
def consequence(x):
    _tau(x.atmosphere,1)
    flammable=mass(FireballMass(available_mass_kg=x.available_mass_kg,flammable_mass_fraction=x.flammable_mass_fraction))["flammable_mass_kg"]
    beta=fireball_fraction(FireballFraction(burst_pressure_pa_abs=x.burst_pressure_pa_abs))["radiative_fraction"]
    geometry=fireball_geometry(FireballGeometry(flammable_mass_kg=flammable))
    base={"flammable_mass_kg":flammable,**geometry,"radiative_fraction":beta,"geometry_basis":x.geometry_basis}
    if flammable == 0:
        return {**base,"surface_emissive_power_w_m2":0,"personnel_area_m2":0,"equipment_area_m2":0,
                "personnel_safe_distance_m":0,"equipment_safe_distance_m":0,
                "personnel_status":"no_flammable_mass","equipment_status":"no_flammable_mass"}
    ensure(geometry["diameter_m"] > 0 and geometry["duration_s"] > 0,
           "Fireball geometry underflow","numerical_failure")
    emissive=fireball_emissive(FireballEmissive(flammable_mass_kg=flammable,heat_of_combustion_j_kg=x.heat_of_combustion_j_kg,
        radiative_fraction=beta,diameter_m=geometry["diameter_m"],duration_s=geometry["duration_s"]))["surface_emissive_power_w_m2"]
    ensure(math.isfinite(emissive),"Fireball emissive power exceeds numerical domain","numerical_failure")
    setup={"diameter_m":geometry["diameter_m"],"surface_emissive_power_w_m2":emissive,"atmosphere":x.atmosphere,
           "geometry_basis":x.geometry_basis,"maximum_distance_m":x.maximum_distance_m,
           "distance_tolerance_m":x.distance_tolerance_m,"maximum_iterations":x.maximum_iterations}
    personnel=distance(FireballDistance(**setup,threshold_w_m2=x.personnel_threshold_w_m2))
    equipment=distance(FireballDistance(**setup,threshold_w_m2=x.equipment_threshold_w_m2))
    return {**base,"surface_emissive_power_w_m2":emissive,
            "personnel_area_m2":personnel["consequence_area_m2"],"equipment_area_m2":equipment["consequence_area_m2"],
            "personnel_safe_distance_m":personnel["safe_distance_m"],"equipment_safe_distance_m":equipment["safe_distance_m"],
            "personnel_status":personnel["status"],"equipment_status":equipment["status"]}
