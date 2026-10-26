"""Unignited boiling/non-boiling pool vapor sources, with steady-state gates."""
import math
from typing import Literal
from .core import Model, NonNegative, Positive, calculation, ensure

_SURFACES={"concrete":(.92,4.16e-7,1),"soil_average":(.96,4.59e-7,3),
           "soil_sandy_dry":(.26,1.98e-7,3),"soil_sandy_moist_8pct":(.59,3.36e-7,3)}


class SurfaceLookup(Model):
    surface: Literal["concrete","soil_average","soil_sandy_dry","soil_sandy_moist_8pct"]


class SurfaceInteraction(Model):
    thermal_conductivity_w_m_k: Positive
    thermal_diffusivity_m2_s: Positive
    roughness_factor: Positive


@calculation("properties/pool-surface-interaction", "SI liquid-pool ground interaction properties", SurfaceLookup,
             ["Part3 Table5.2M; PDF p582"],
             limitations=["Printed SI table values directly; no exact back-conversion of rounded US table. Historical representative ground properties, not measured site or cryogenic validation. Concrete is source default but public selection is explicit."])
def surface_lookup(x):
    k,a,rough=_SURFACES[x.surface]
    return {"thermal_conductivity_w_m_k":k,"thermal_diffusivity_m2_s":a,"roughness_factor":rough}


class PoolTemperatures(Model):
    bubble_temperature_k: Positive
    ground_temperature_k: Positive


@calculation("release/pool-evaporation-regime", "Pool boiling/non-boiling temperature classification", PoolTemperatures,
             ["Part3 §5.7.4.2-5.7.4.3; PDF p544"],
             limitations=["Tb<Tg boiling; Tb>Tg non-boiling. Source gives no equality rule: equal temperatures return boundary_requires_qualification. Bubble temperature and ground temperature are supplied, not calculated with an EOS."])
def regime(x):
    label="boiling" if x.bubble_temperature_k < x.ground_temperature_k else (
          "non_boiling" if x.bubble_temperature_k > x.ground_temperature_k else "boundary_requires_qualification")
    return {"regime":label}


class BoilingSetup(PoolTemperatures):
    latent_heat_j_kg: Positive
    surface: SurfaceInteraction
    gravity_m_s2: Positive = 9.81


def _boiling_coefficient(x):
    ensure(x.bubble_temperature_k < x.ground_temperature_k,"Boiling model requires Tb<Tg")
    k=x.surface.thermal_conductivity_w_m_k
    a=x.surface.thermal_diffusivity_m2_s
    coefficient=math.pi**1.5*x.surface.roughness_factor*k*(x.ground_temperature_k-x.bubble_temperature_k)/(
        x.latent_heat_j_kg*math.sqrt(math.pi*a))
    ensure(math.isfinite(coefficient) and coefficient > 0,"Boiling coefficient outside finite positive numerical domain","numerical_failure")
    return coefficient


class BoilingEvaporation(BoilingSetup):
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative


@calculation("release/boiling-pool-evaporation", "Printed boiling-pool evaporation correlation", BoilingEvaporation,
             ["Part3 eq(3.103), Annex3.B C14=1; PDF pp544,647; Vdot/tp nomenclature PDF579"],
             limitations=["Uses pi^1.5, not1.5. Vdot is vapor volume leaving pool surface, not liquid feed volume. Time is time to steady state per source nomenclature; this primitive does not assert an arbitrary transient evolution. No rainout, flash/EOS, inventory, site limit or LH2 validation."])
def boiling_evaporation(x):
    coefficient=_boiling_coefficient(x)
    rate=coefficient*math.sqrt(2*x.gravity_m_s2*x.vapor_volumetric_rate_m3_s)*x.time_to_steady_s
    ensure(rate > 0 or x.vapor_volumetric_rate_m3_s == 0 or x.time_to_steady_s == 0,
           "Boiling evaporation rate underflow","numerical_failure")
    return {"evaporation_rate_kg_s":rate,"latent_heat_rate_w":rate*x.latent_heat_j_kg}


class BoilingRadius(Model):
    vapor_volumetric_rate_m3_s: NonNegative
    time_to_steady_s: NonNegative
    gravity_m_s2: Positive = 9.81


@calculation("release/boiling-pool-radius", "Boiling-pool spreading radius at steady-state time", BoilingRadius,
             ["Part3 eq(3.104); PDF p544; Vdot/tp nomenclature PDF579"],
             limitations=["r=sqrt(2/3)*(8*g*Vdot/pi)^.25*tp^.75. Vdot is vapor leaving the surface. Unconstrained correlation: no bund/terrain/site-area clipping or inventory mass balance."])
def boiling_radius(x):
    radius=math.sqrt(2/3)*(8*x.gravity_m_s2*x.vapor_volumetric_rate_m3_s/math.pi)**.25*x.time_to_steady_s**.75
    ensure(radius > 0 or x.vapor_volumetric_rate_m3_s == 0 or x.time_to_steady_s == 0,
           "Boiling pool radius underflow","numerical_failure")
    area=math.pi*radius**2
    ensure(area > 0 or radius == 0,"Boiling pool area underflow","numerical_failure")
    return {"pool_radius_m":radius,"pool_area_m2":area}


class BoilingSteadySource(BoilingSetup):
    liquid_feed_rate_kg_s: NonNegative
    pool_vapor_density_kg_m3: Positive
    supply_duration_s: Positive
    maximum_pool_area_m2: Positive


@calculation("release/boiling-pool-steady-source", "Boiling equilibrium vapor source with duration/site support checks", BoilingSteadySource,
             ["Part3 eqs(3.103)-(3.104), §5.7.4.2; PDF p544; Vdot definition PDF579"],
             origin="api581_steady_pool_with_explicit_support_checks",
             limitations=["At equilibrium evaporation=liquid feed; Vdot=feed/pool-vapor-density, not feed/liquid-density. Solves tp from eq3.103 then radius from3.104. Usable source returned only if feed persists beyond tp and equilibrium area fits supplied site limit. Failed support is not silently clipped or replaced by feed. No growing-pool transient, finite-inventory depletion, drainage or post-release evaporation solver."])
def boiling_steady_source(x):
    coefficient=_boiling_coefficient(x)
    feed=x.liquid_feed_rate_kg_s
    if feed == 0:
        return {"equilibrium_evaporation_rate_kg_s":0,"vapor_volumetric_rate_m3_s":0,"time_to_steady_s":None,
                "pool_radius_m":0,"pool_area_m2":0,"vapor_source_rate_kg_s":0,"support_status":"no_feed"}
    volume=feed/x.pool_vapor_density_kg_m3
    ensure(math.isfinite(volume) and volume > 0,"Pool vapor volumetric rate outside numerical domain","numerical_failure")
    time=feed/(coefficient*math.sqrt(2*x.gravity_m_s2*volume))
    ensure(math.isfinite(time) and time > 0,"Pool steady-state time outside numerical domain","numerical_failure")
    geometry=boiling_radius(BoilingRadius(vapor_volumetric_rate_m3_s=volume,time_to_steady_s=time,gravity_m_s2=x.gravity_m_s2))
    ensure(math.isfinite(geometry["pool_area_m2"]),"Pool equilibrium area outside numerical domain","numerical_failure")
    duration_limited=time >= x.supply_duration_s
    area_limited=geometry["pool_area_m2"] > x.maximum_pool_area_m2
    status=("duration_and_area_limited" if duration_limited and area_limited else "duration_limited" if duration_limited else (
            "area_limited" if area_limited else "supported"))
    return {"equilibrium_evaporation_rate_kg_s":feed,"vapor_volumetric_rate_m3_s":volume,"time_to_steady_s":time,**geometry,
            "vapor_source_rate_kg_s":feed if status == "supported" else None,"support_status":status}


class NonBoilingSetup(PoolTemperatures):
    bubble_pressure_at_ground_pa_abs: NonNegative
    ambient_pressure_pa_abs: Positive = 101325
    molecular_weight_kg_kmol: Positive
    storage_temperature_k: Positive
    wind_speed_m_s: NonNegative


def _nonboiling_coefficient(x):
    ensure(x.bubble_temperature_k > x.ground_temperature_k,"Non-boiling model requires Tb>Tg")
    ensure(x.bubble_pressure_at_ground_pa_abs < x.ambient_pressure_pa_abs,
           "Non-boiling bubble pressure at ground temperature must be below atmospheric pressure")
    # Printed Pb,g is kPa; R=8314 J/(kmol K), C15=4.685.
    coefficient=4.685*(x.bubble_pressure_at_ground_pa_abs/1000*x.molecular_weight_kg_kmol/(
        8314*x.storage_temperature_k))*x.wind_speed_m_s**.78
    ensure(math.isfinite(coefficient),"Non-boiling coefficient outside numerical domain","numerical_failure")
    ensure(coefficient > 0 or x.bubble_pressure_at_ground_pa_abs == 0 or x.wind_speed_m_s == 0,
           "Non-boiling coefficient underflow","numerical_failure")
    return coefficient


class NonBoilingEvaporation(NonBoilingSetup):
    pool_radius_m: NonNegative


@calculation("release/nonboiling-pool-evaporation", "Non-boiling pool wind-driven vapor generation", NonBoilingEvaporation,
             ["Part3 eq(3.105), Annex3.B C15; PDF pp544,647; P/R/Ts units PDF578-579"],
             limitations=["Follows printed C15=4.685 with Pb,g in kPa and R=8314; Pa public input divided by1000. Denominator uses printed storage Ts, not automatic substitution of ground temperature. Wind exponent.78 and radius exponent1.89. Wind qualified at6ft above grade. Zero wind gives zero correlation rate, not a model of molecular diffusion/quiescent evaporation. No site/inventory clipping or LH2 validation."])
def nonboiling_evaporation(x):
    coefficient=_nonboiling_coefficient(x)
    rate=coefficient*x.pool_radius_m**1.89
    ensure(rate > 0 or coefficient == 0 or x.pool_radius_m == 0,"Non-boiling evaporation underflow","numerical_failure")
    return {"evaporation_rate_kg_s":rate}


class NonBoilingSteadySource(NonBoilingSetup):
    liquid_feed_rate_kg_s: NonNegative
    maximum_pool_area_m2: Positive


@calculation("release/nonboiling-pool-steady-source", "Non-boiling equilibrium source radius and site support check", NonBoilingSteadySource,
             ["Part3 eq(3.105), §5.7.4.3; PDF p544"],
             origin="api581_steady_pool_inverse_with_explicit_site_check",
             limitations=["Solves evaporation=feed for radius. Time to equilibrium is not supplied by this equation and is not invented. Positive feed with zero wind/vapor pressure has no finite equilibrium in this correlation. Site limit failures return no usable source; no arbitrary radius clipping. Requires a separately qualified sustained feed/equilibrium assumption, not a transient pool or mass-balance simulation."])
def nonboiling_steady_source(x):
    coefficient=_nonboiling_coefficient(x)
    feed=x.liquid_feed_rate_kg_s
    if feed == 0:
        return {"equilibrium_evaporation_rate_kg_s":0,"pool_radius_m":0,"pool_area_m2":0,
                "vapor_source_rate_kg_s":0,"support_status":"no_feed"}
    if coefficient == 0:
        return {"equilibrium_evaporation_rate_kg_s":None,"pool_radius_m":None,"pool_area_m2":None,
                "vapor_source_rate_kg_s":None,"support_status":"no_finite_steady_state"}
    radius=math.exp((math.log(feed)-math.log(coefficient))/1.89)
    area=math.pi*radius**2
    ensure(math.isfinite(area) and area > 0 and radius > 0,"Non-boiling equilibrium geometry outside numerical domain","numerical_failure")
    supported=area <= x.maximum_pool_area_m2
    return {"equilibrium_evaporation_rate_kg_s":feed,"pool_radius_m":radius,"pool_area_m2":area,
            "vapor_source_rate_kg_s":feed if supported else None,"support_status":"supported" if supported else "area_limited"}
