"""Independent consequence primitives; explicit applicability and provenance."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure


class JetPower(Model):
    mass_rate_kg_s: NonNegative
    heat_of_combustion_j_kg: Positive
    radiative_fraction: Fraction = .35


@calculation("effects/jet-fire-power", "Jet fire radiated power", JetPower,
             ["Part 3 §5.8.3.2 eq (3.152); PDF p554"],
             limitations=["SI radiated power; external applicability validation required for LH2."])
def jet_power(x):
    return {"radiated_power_w": x.mass_rate_kg_s * x.heat_of_combustion_j_kg * x.radiative_fraction}


class JetFlux(Model):
    radiated_power_w: NonNegative
    distance_m: Positive
    atmospheric_transmissivity: Fraction


@calculation("effects/jet-fire-flux", "Point-source jet fire received radiation", JetFlux,
             ["Part 3 eqs (3.153)-(3.154); PDF p554"], limitations=["Far-field point source at grade; flame impingement and near field not represented."])
def jet_flux(x):
    return {"received_flux_w_m2": x.atmospheric_transmissivity * x.radiated_power_w / (4 * math.pi * x.distance_m ** 2)}


class JetDistance(Model):
    radiated_power_w: NonNegative
    threshold_w_m2: Positive
    transmissivity_model: Literal["constant", "api_water_vapor"]
    atmospheric_transmissivity: Fraction | None = None
    water_partial_pressure_pa: Positive | None = None


@calculation("effects/jet-fire-distance", "Jet fire threshold radius and consequence area", JetDistance,
             ["Part 3 eqs (3.140), (3.152)-(3.156)"],
             limitations=["Constant transmissivity is an explicitly supplied approximation; api_water_vapor uses distance-dependent attenuation capped at physical maximum 1.",
                          "Water-vapor mode uses eq (3.140) exponent -0.09 with C19=1.085 and pressure in kPa; the base-edition table labels C19 dimensions with exponent 0.092, recorded as a source discrepancy.",
                          "Point source at grade; LH2-specific validation outstanding."])
def jet_distance(x):
    ensure((x.transmissivity_model == "constant" and x.atmospheric_transmissivity is not None and x.water_partial_pressure_pa is None)
           or (x.transmissivity_model == "api_water_vapor" and x.water_partial_pressure_pa is not None and x.atmospheric_transmissivity is None),
           "Provide exactly the parameter for the selected transmissivity model")
    if x.radiated_power_w == 0 or (x.transmissivity_model == "constant" and x.atmospheric_transmissivity == 0):
        return {"threshold_distance_m": 0, "consequence_area_m2": 0, "transmissivity_at_distance": None}
    def tau(r):
        return x.atmospheric_transmissivity if x.transmissivity_model == "constant" else min(1, 1.085 * (x.water_partial_pressure_pa / 1000 * r) ** (-.09))
    high = math.sqrt(x.radiated_power_w / (4 * math.pi * x.threshold_w_m2))
    low = 0.0
    for _ in range(100):
        mid = (low + high) / 2
        if mid == 0:
            break
        flux = tau(mid) * x.radiated_power_w / (4 * math.pi * mid ** 2)
        if flux > x.threshold_w_m2:
            low = mid
        else:
            high = mid
    radius = (low + high) / 2
    return {"threshold_distance_m": radius, "consequence_area_m2": math.pi * radius ** 2,
            "transmissivity_at_distance": tau(radius)}


class FlashFire(Model):
    area_within_lfl_m2: NonNegative


@calculation("effects/flash-fire", "Flash fire consequence areas", FlashFire,
             ["Part 3 §4.8.2.3, §5.8.6"], limitations=["LFL footprint must come from a validated dispersion model."])
def flash_fire(x):
    return {"personnel_area_m2": x.area_within_lfl_m2, "equipment_area_m2": .25 * x.area_within_lfl_m2}


class PoolArea(Model):
    liquid_rate_kg_s: NonNegative
    burning_rate_kg_m2_s: Positive
    available_liquid_mass_kg: NonNegative
    density_kg_m3: Positive
    pool_depth_m: Positive = .005
    site_maximum_area_m2: Positive


@calculation("effects/pool-fire-area", "Pool burning area and radius", PoolArea,
             ["Part 3 eqs (3.131)-(3.134); PDF pp550-551"],
             limitations=["Pool geometry only; burning rate supplied by caller; surface radiation/view factors not included. Site limit is mandatory."])
def pool_area(x):
    burning_area = x.liquid_rate_kg_s / x.burning_rate_kg_m2_s
    mass_area = x.available_liquid_mass_kg / (x.density_kg_m3 * x.pool_depth_m)
    area = min(burning_area, mass_area, x.site_maximum_area_m2)
    return {"burning_area_m2": burning_area, "inventory_limited_area_m2": mass_area,
            "pool_area_m2": area, "pool_radius_m": math.sqrt(area / math.pi)}


class EmpiricalArea(Model):
    coefficient_a: NonNegative
    exponent_b: Positive
    release_magnitude: NonNegative
    magnitude_unit: Literal["kg/s", "kg"]
    coefficient_source: str = Field(min_length=1, max_length=500)


@calculation("consequence/power-law-area", "Level 1 consequence power-law primitive", EmpiricalArea,
             ["Part 3 eqs (3.16)-(3.17)"],
             limitations=["Caller-supplied SI coefficients only; does not select reference fluid or perform Type 0 blending. Not a complete Level 1 COF."])
def power_area(x):
    return {"area_m2": x.coefficient_a * x.release_magnitude ** x.exponent_b,
            "coefficient_source": x.coefficient_source}


class EventTree(Model):
    phase: Literal["vapor", "liquid"]
    release_type: Literal["continuous", "instantaneous"]
    ignition_probability: Fraction
    immediate_given_ignition: Fraction
    vce_given_delayed: Fraction


@calculation("events/leakage-tree", "Single-phase leakage event tree", EventTree,
             ["Part 3 §5.8.1.6, Figure 5.3"],
             limitations=["Leakage only, not rupture Figure 5.4; branch probabilities supplied by caller. Two-phase tree deferred."])
def leakage_tree(x):
    pi, immediate, vce = x.ignition_probability, x.immediate_given_ignition, x.vce_given_delayed
    fire = "pool_fire" if x.phase == "liquid" else ("jet_fire" if x.release_type == "continuous" else "fireball")
    probabilities = {"safe_dispersion": 1 - pi, fire: pi * immediate,
                     "vce": pi * (1 - immediate) * vce, "flash_fire": pi * (1 - immediate) * (1 - vce)}
    return {"terminal_probabilities": probabilities, "probability_sum": math.fsum(probabilities.values())}


class Probit(Model):
    intercept: float = Field(allow_inf_nan=False)
    slope: Positive
    concentration_exponent: Positive
    concentration: NonNegative
    exposure_duration: NonNegative
    concentration_unit: str = Field(min_length=1, max_length=50)
    duration_unit: str = Field(min_length=1, max_length=50)
    coefficient_source: str = Field(min_length=1, max_length=500)


@calculation("effects/toxic-probit", "User-parameterized toxic probit", Probit,
             ["Part 3 §5.9.2"], origin="engineering_utility",
             limitations=["Coefficient units must match supplied concentration/time. This generic utility uses caller-qualified coefficients; Table4.14 species calculations are separately available through toxic-species-probit."])
def toxic_probit(x):
    if x.concentration == 0 or x.exposure_duration == 0:
        return {"probit": None, "effect_probability": 0}
    y = x.intercept + x.slope * (x.concentration_exponent * math.log(x.concentration) + math.log(x.exposure_duration))
    return {"probit": y, "effect_probability": .5 * math.erfc(-(y - 5) / math.sqrt(2))}


class PoolBurning(Model):
    heat_of_combustion_j_kg: Positive
    latent_heat_j_kg: Positive
    boiling: bool
    specific_heat_j_kg_k: Positive | None = None
    boiling_temperature_k: Positive | None = None
    ambient_temperature_k: Positive | None = None


@calculation("effects/pool-burning-rate", "Pool fire surface mass burning rate", PoolBurning,
             ["Part 3 eqs (3.128)-(3.129), Annex 3.B C17; PDF pp550,648"],
             limitations=["Empirical pool burning correlation; LH2 applicability not validated. Does not model unignited pool evaporation."])
def pool_burning(x):
    denominator = x.latent_heat_j_kg
    if not x.boiling:
        ensure(all(v is not None for v in (x.specific_heat_j_kg_k, x.boiling_temperature_k, x.ambient_temperature_k)),
               "Non-boiling pool requires Cp, boiling and ambient temperatures")
        ensure(x.boiling_temperature_k >= x.ambient_temperature_k, "Non-boiling pool requires boiling temperature >= ambient")
        denominator += x.specific_heat_j_kg_k * (x.boiling_temperature_k - x.ambient_temperature_k)
    return {"burning_rate_kg_m2_s": .001481 * x.heat_of_combustion_j_kg / denominator}


class FireballGeometry(Model):
    flammable_mass_kg: NonNegative


@calculation("effects/fireball-geometry", "Fireball diameter, height and duration", FireballGeometry,
             ["Part 3 eqs (3.158)-(3.161), Annex 3.B C22-C24; PDF pp555,648"],
             limitations=["Instantaneous rupture fireball model; no continuous-release fireball. Empirical exponents follow printed 0.333/0.167."])
def fireball_geometry(x):
    mass = x.flammable_mass_kg
    diameter = 5.8 * mass ** .333
    duration = .45 * mass ** .333 if mass <= 29937 else 2.6 * mass ** .167
    return {"diameter_m": diameter, "center_height_m": .75 * diameter, "duration_s": duration}


class FireballFraction(Model):
    burst_pressure_pa_abs: Positive


@calculation("effects/fireball-radiative-fraction", "Fireball pressure-based radiative fraction", FireballFraction,
             ["Part 3 eq (3.163), Annex 3.B C25; PDF pp555,648"],
             limitations=["Raw correlation; results above 1 are rejected rather than silently capped. Applicability must be independently established."])
def fireball_fraction(x):
    fraction = .0296 * (x.burst_pressure_pa_abs / 1000) ** .32
    ensure(fraction <= 1, "Pressure correlation exceeds a physical radiative fraction of 1")
    return {"radiative_fraction": fraction}


class FireballEmissive(Model):
    flammable_mass_kg: NonNegative
    heat_of_combustion_j_kg: Positive
    radiative_fraction: Fraction
    diameter_m: Positive
    duration_s: Positive


@calculation("effects/fireball-emissive-power", "Fireball surface emissive power", FireballEmissive,
             ["Part 3 eq (3.162); PDF p555"])
def fireball_emissive(x):
    return {"surface_emissive_power_w_m2": x.radiative_fraction * x.flammable_mass_kg * x.heat_of_combustion_j_kg /
            (math.pi * x.diameter_m ** 2 * x.duration_s)}


class TntEquivalence(Model):
    flammable_cloud_mass_kg: NonNegative
    combustion_heat_j_kg: Positive
    explosion_yield: Fraction
    tnt_heat_j_kg: Positive
    tnt_heat_source: str = Field(min_length=1, max_length=500)


@calculation("effects/vce-tnt-equivalence", "VCE TNT equivalent mass", TntEquivalence,
             ["Part 3 eq (3.169); PDF pp557-558"],
             limitations=["TNT heat is mandatory: original text J/kg and Btu/lb values are inconsistent. Cloud mass definition and yield must be consistent. Blast pressure and distances require separate caller-qualified fit-domain inputs; equivalence alone does not establish blast-curve applicability."])
def tnt_equivalence(x):
    return {"tnt_equivalent_mass_kg": x.explosion_yield * x.flammable_cloud_mass_kg * x.combustion_heat_j_kg / x.tnt_heat_j_kg}
