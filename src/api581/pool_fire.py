"""Pool fire radiation, with printed and independently integrated geometry bases."""
import math
from typing import Annotated, Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .effects import PoolBurning, pool_burning, PoolArea, pool_area

Tilt = Annotated[float,Field(ge=0,lt=math.pi/2,strict=True,allow_inf_nan=False)]
EquationBasis = Literal["api581_printed", "geometry_checked"]
DistanceConvention = Literal["printed_surface_ratio", "surface_to_axis"]


class WaterPressure(Model):
    ambient_temperature_k: Positive
    relative_humidity_fraction: Fraction
    ambient_pressure_pa_abs: Positive = 101325


@calculation("properties/water-partial-pressure", "Water partial pressure for radiation attenuation", WaterPressure,
             ["Part3 eq(3.141), Annex3.B C20/C21; PDF pp552,648"],
             limitations=["Uses printed1.013kPa,5328K and14.4114. RH in this equation is percent; public fraction is multiplied by100. Rejects pressure above declared ambient pressure. Empirical ambient correlation, not a general steam/ice or cryogenic property solver."])
def water_pressure(x):
    pressure=1013*(100*x.relative_humidity_fraction)*math.exp(14.4114-5328/x.ambient_temperature_k)
    ensure(pressure <= x.ambient_pressure_pa_abs,"Water partial pressure exceeds ambient pressure; correlation/conditions outside physical domain")
    return {"water_partial_pressure_pa":pressure}


class Transmissivity(Model):
    water_partial_pressure_pa: NonNegative
    path_length_m: Positive


@calculation("effects/atmospheric-transmissivity", "Water-vapor thermal-radiation transmissivity", Transmissivity,
             ["Part3 eq(3.140), Annex3.B C19; PDF pp552,648"],
             limitations=["Equation exponent-.09 and C19=1.085 with pressure in kPa. Annex dimensional exponent.092 differs; equation exponent followed. Capped at physical maximum1. At zero water pressure uses limiting tau=1 and reports no finite uncapped value."])
def transmissivity(x):
    if x.water_partial_pressure_pa == 0:
        return {"transmissivity":1,"uncapped_transmissivity":None,"dry_air_limit":True}
    # Log form avoids underflow in pressure*distance before negative exponent.
    raw=1.085*math.exp(-.09*(math.log(x.water_partial_pressure_pa)-math.log(1000)+math.log(x.path_length_m)))
    return {"transmissivity":min(1,raw),"uncapped_transmissivity":raw,"dry_air_limit":False}


class MixtureComponent(Model):
    mole_fraction: Fraction
    burning_rate_kg_m2_s: NonNegative


class MixtureBurning(Model):
    components: list[MixtureComponent] = Field(min_length=1,max_length=100)


@calculation("effects/pool-mixture-burning-rate", "Mole-weighted liquid-mixture pool burning rate", MixtureBurning,
             ["Part3 eq(3.130); PDF p550"],
             limitations=["Source mole-fraction weighting of supplied component burning rates; not a mixture thermodynamic or unignited evaporation model. Fractions must sum to1 and are not silently normalized."])
def mixture_burning(x):
    ensure(math.isclose(math.fsum(c.mole_fraction for c in x.components),1,rel_tol=0,abs_tol=1e-9),"Mole fractions must sum to1")
    return {"burning_rate_kg_m2_s":math.fsum(c.mole_fraction*c.burning_rate_kg_m2_s for c in x.components)}


class FlameGeometry(Model):
    pool_radius_m: Positive
    burning_rate_kg_m2_s: Positive
    air_density_kg_m3: Positive
    vapor_density_kg_m3: Positive
    wind_speed_m_s: NonNegative
    gravity_m_s2: Positive = 9.81


@calculation("effects/pool-flame-geometry", "Thomas pool flame length and wind tilt", FlameGeometry,
             ["Part3 eqs(3.135)-(3.137); PDF p551"],
             limitations=["Air density enters Thomas length; vapor density enters nondimensional wind (not interchangeable). Wind must be qualified at source reference height6ft above grade. Printed powers.67,.333,-.21 followed. No automatic wind-height conversion or LH2 validation."])
def flame_geometry(x):
    wind=max(1,x.wind_speed_m_s*(x.vapor_density_kg_m3/(2*x.gravity_m_s2*x.burning_rate_kg_m2_s*x.pool_radius_m))**.333)
    length=110*x.pool_radius_m*(x.burning_rate_kg_m2_s/(x.air_density_kg_m3*math.sqrt(2*x.gravity_m_s2*x.pool_radius_m)))**.67*wind**(-.21)
    tilt=math.acos(1/math.sqrt(wind))
    ensure(math.isfinite(wind) and math.isfinite(length) and length > 0 and tilt < math.pi/2,
           "Flame geometry exceeds finite numerical domain", "numerical_failure")
    return {"nondimensional_wind_speed":wind,"flame_length_m":length,"flame_tilt_rad":tilt,
            "vertical_flame_height_m":length*math.cos(tilt),"downwind_axis_extension_m":length*math.sin(tilt)}


class SurfaceEmissive(Model):
    pool_radius_m: Positive
    flame_length_m: Positive
    burning_rate_kg_m2_s: Positive
    heat_of_combustion_j_kg: Positive
    radiative_fraction: Fraction = .35


@calculation("effects/pool-surface-emissive-power", "Pool flame surface emissive power", SurfaceEmissive,
             ["Part3 eq(3.138); PDF p551"],
             limitations=["Surface emissive power W/m2, not total radiated power W. Uses printed cylindrical side-plus-top area2*pi*R*L+pi*R^2. Uniform emissive surface; no smoke shielding or fuel-specific emissivity model."])
def surface_emissive(x):
    burning_mass=x.burning_rate_kg_m2_s*math.pi*x.pool_radius_m**2
    power=x.radiative_fraction*burning_mass*x.heat_of_combustion_j_kg
    area=2*math.pi*x.pool_radius_m*x.flame_length_m+math.pi*x.pool_radius_m**2
    ensure(math.isfinite(power) and math.isfinite(area) and area > 0,
           "Pool radiated power/surface area exceeds numerical domain", "numerical_failure")
    return {"burning_mass_rate_kg_s":burning_mass,"radiated_power_w":power,
            "emitting_surface_area_m2":area,"surface_emissive_power_w_m2":power/area}


class CylinderView(Model):
    length_radius_ratio: Positive
    distance_radius_ratio: Positive
    flame_tilt_rad: Tilt
    equation_basis: EquationBasis


@calculation("effects/pool-cylinder-view-factor", "Pool cylinder vertical/horizontal/maximum view factors", CylinderView,
             ["Part3 eqs(3.142)-(3.149); PDF pp552-553", "Independent oblique-cylinder surface integral: docs/POOL_RADIATION_VALIDATION.md"],
             origin="explicit_printed_or_geometrically_checked_equations",
             limitations=["Printed2016 Fv has atan(q), not atan(sqrt(q)), and numerator2Y(1+sin(theta)), not2Y(1+Xsin(theta)). api581_printed reproduces these; geometry_checked makes the two explicit changes verified against independent side-surface integration. Not an authorized standard erratum. Requires Y>1+Xsin(theta), outside downwind flame projection. Ground target in tilt plane; uniform side emission. Physical-range flag must be checked before flux use."])
def cylinder_view(x):
    X,Y=x.length_radius_ratio,x.distance_radius_ratio
    s,c=math.sin(x.flame_tilt_rad),math.cos(x.flame_tilt_rad)
    ensure(Y > 1+X*s,"Target must be outside downwind flame projection: Y > 1+X*sin(tilt)")
    A=(X*c)**2+(Y+1-X*s)**2
    B=(X*c)**2+(Y-1-X*s)**2
    D=Y*Y-1
    C=1+D*c*c
    q=A*(Y-1)/(B*(Y+1))
    common=math.atan2(X*Y/(math.sqrt(D)*math.sqrt(C)),1-s*(X*Y-D*s)/C)
    numerator=((X*c)**2+(Y-X*s)**2+1 if x.equation_basis == "geometry_checked"
               else X*X+(Y+1)**2-2*Y*(1+s))
    vertical_atan=math.atan(math.sqrt(q) if x.equation_basis == "geometry_checked" else q)
    fv=(X*c/(Y-X*s)*numerator/(math.pi*math.sqrt(A*B))*vertical_atan
        +c/(math.pi*math.sqrt(C))*common
        -X*c/(math.pi*(Y-X*s))*math.atan(math.sqrt((Y-1)/(Y+1))))
    fh=(math.atan(math.sqrt((Y+1)/(Y-1)))/math.pi
        -(X*X+(Y+1)**2-2*(Y+1+X*Y*s))/(math.pi*math.sqrt(A*B))*math.atan(math.sqrt(q))
        +s/(math.pi*math.sqrt(C))*common)
    combined=math.hypot(fv,fh)
    physical=min(fv,fh) >= -1e-12 and max(fv,fh,combined) <= 1+1e-12
    return {"vertical_view_factor":fv,"horizontal_view_factor":fh,"maximum_view_factor":combined,
            "physical_range":physical,"equation_basis":x.equation_basis}


class Atmosphere(Model):
    transmissivity_model: Literal["constant","api_water_vapor"]
    constant_transmissivity: Fraction | None = None
    water_partial_pressure_pa: NonNegative | None = None


def _atmosphere(x,distance):
    ensure((x.transmissivity_model == "constant" and x.constant_transmissivity is not None and x.water_partial_pressure_pa is None)
           or (x.transmissivity_model == "api_water_vapor" and x.water_partial_pressure_pa is not None and x.constant_transmissivity is None),
           "Provide exactly the parameter for selected transmissivity model")
    return x.constant_transmissivity if x.transmissivity_model == "constant" else transmissivity(
        Transmissivity(water_partial_pressure_pa=x.water_partial_pressure_pa,path_length_m=distance))["transmissivity"]


class RadiationSetup(Model):
    pool_radius_m: Positive
    flame_length_m: Positive
    flame_tilt_rad: Tilt
    surface_emissive_power_w_m2: NonNegative
    atmosphere: Atmosphere
    equation_basis: EquationBasis
    distance_convention: DistanceConvention


class PoolFlux(RadiationSetup):
    surface_distance_m: Positive


@calculation("effects/pool-radiation-flux", "Pool thermal radiation at a specified surface separation", PoolFlux,
             ["Part3 eqs(3.139)-(3.149); PDF pp552-553"],
             origin="api581_surface_flux_with_explicit_geometry_basis",
             limitations=["Source nomenclature defines xs from flame surface, but printed Y=xs/R conflicts with axis-distance geometry. Caller selects printed_surface_ratio (Y=xs/R) or surface_to_axis (Y=(xs+R)/R). Atmospheric path always uses surface separation. Invalid physical view factors are rejected; no automatic formula fallback."])
def pool_flux(x):
    distance=x.surface_distance_m+(x.pool_radius_m if x.distance_convention == "surface_to_axis" else 0)
    view=cylinder_view(CylinderView(length_radius_ratio=x.flame_length_m/x.pool_radius_m,
        distance_radius_ratio=distance/x.pool_radius_m,flame_tilt_rad=x.flame_tilt_rad,equation_basis=x.equation_basis))
    ensure(view["physical_range"],"Selected printed/geometric view factor lies outside physical range", "invalid_view_factor")
    tau=_atmosphere(x.atmosphere,x.surface_distance_m)
    return {"received_flux_w_m2":tau*x.surface_emissive_power_w_m2*view["maximum_view_factor"],
            "transmissivity":tau,"maximum_view_factor":view["maximum_view_factor"],"view_factor_distance_m":distance,
            "equation_basis":x.equation_basis,"distance_convention":x.distance_convention}


class PoolDistance(RadiationSetup):
    threshold_w_m2: Positive
    maximum_surface_distance_m: Positive
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


@calculation("effects/pool-fire-distance", "Pool radiation threshold separation and consequence area", PoolDistance,
             ["Part3 §5.8.2.6; eqs(3.150)-(3.151); PDF p553"],
             origin="api581_threshold_iteration_with_explicit_geometry_basis",
             limitations=["Assumes decreasing flux outside downwind flame envelope. Solves only within supplied maximum distance; no implicit expansion or far-field substitution. If flux already below limit at domain boundary, returns conservative flame-envelope separation and boundary status, not a claimed threshold crossing. Area always pi*(surface_distance+pool_radius)^2. Printed formula/geometry and distance convention are explicit; no validated LH2 applicability."])
def pool_distance(x):
    envelope=x.flame_length_m*math.sin(x.flame_tilt_rad)
    minimum=envelope+(x.pool_radius_m if x.distance_convention == "printed_surface_ratio" else 0)
    lo=minimum+max(1e-9,1e-8*x.pool_radius_m)
    hi=x.maximum_surface_distance_m
    ensure(hi > lo,"Maximum surface distance must lie outside flame/view-factor domain")
    def flux(distance):
        return pool_flux(PoolFlux(**{k:getattr(x,k) for k in RadiationSetup.model_fields},surface_distance_m=distance))["received_flux_w_m2"]
    lower,upper=flux(lo),flux(hi)
    ensure(upper <= x.threshold_w_m2,"Threshold not bracketed; increase maximum surface distance", "unbracketed_threshold")
    if lower <= x.threshold_w_m2:
        distance,status,iterations,residual=minimum,"below_limit_at_domain_boundary",0,None
    else:
        iterations=0
        while hi-lo > x.distance_tolerance_m and iterations < x.maximum_iterations:
            mid=lo+(hi-lo)/2
            if flux(mid) > x.threshold_w_m2:lo=mid
            else:hi=mid
            iterations+=1
        ensure(hi-lo <= x.distance_tolerance_m,"Threshold solver did not converge", "nonconvergent_threshold")
        distance,status=hi,"threshold_solved"
        residual=flux(distance)-x.threshold_w_m2
    return {"safe_surface_distance_m":distance,"consequence_radius_m":distance+x.pool_radius_m,
            "consequence_area_m2":math.pi*(distance+x.pool_radius_m)**2,"status":status,
            "iterations":iterations,"flux_residual_w_m2":residual,"minimum_surface_domain_m":minimum,
            "equation_basis":x.equation_basis,"distance_convention":x.distance_convention}


class PoolConsequence(Model):
    burning: PoolBurning
    liquid_rate_kg_s: NonNegative
    available_liquid_mass_kg: NonNegative
    liquid_density_kg_m3: Positive
    pool_depth_m: Positive = .005
    site_maximum_area_m2: Positive
    air_density_kg_m3: Positive
    vapor_density_kg_m3: Positive
    wind_speed_m_s: NonNegative
    radiative_fraction: Fraction = .35
    atmosphere: Atmosphere
    equation_basis: EquationBasis
    distance_convention: DistanceConvention
    maximum_surface_distance_m: Positive
    personnel_threshold_w_m2: Positive = 12600
    equipment_threshold_w_m2: Positive = 37800


@calculation("effects/pool-fire-consequence", "Compose burning, pool size, flame and radiation consequence areas", PoolConsequence,
             ["Part3 §5.8.2; eqs(3.128)-(3.151); PDF pp550-553"],
             origin="api581_pool_chain_with_explicit_geometry_basis",
             limitations=["Single pool/event only; no ignition/event or hole weighting. Qualified liquid rainout rate/mass supplied; inventory input is liquid mass, not automatic substitution of ambiguous frac_ro in printed eq(3.132). Site limit mandatory. Explicit printed/geometry_checked and distance choices; source-view-factor discrepancies are not silently corrected. Uniform plume model, no smoke/terrain/flame-impingement or LH2-specific validation."])
def pool_consequence(x):
    rate=pool_burning(x.burning)["burning_rate_kg_m2_s"]
    ensure(math.isfinite(rate) and rate > 0,"Pool burning rate underflow/overflow", "numerical_failure")
    area=pool_area(PoolArea(liquid_rate_kg_s=x.liquid_rate_kg_s,burning_rate_kg_m2_s=rate,
        available_liquid_mass_kg=x.available_liquid_mass_kg,density_kg_m3=x.liquid_density_kg_m3,
        pool_depth_m=x.pool_depth_m,site_maximum_area_m2=x.site_maximum_area_m2))
    # Validate atmosphere contract even for an empty pool.
    _atmosphere(x.atmosphere,1)
    if area["pool_radius_m"] == 0:
        return {"burning_rate_kg_m2_s":rate,**area,"flame_length_m":0,"flame_tilt_rad":0,
                "surface_emissive_power_w_m2":0,"personnel_area_m2":0,"equipment_area_m2":0,
                "personnel_safe_surface_distance_m":0,"equipment_safe_surface_distance_m":0,
                "personnel_status":"no_pool","equipment_status":"no_pool",
                "equation_basis":x.equation_basis,"distance_convention":x.distance_convention}
    flame=flame_geometry(FlameGeometry(pool_radius_m=area["pool_radius_m"],burning_rate_kg_m2_s=rate,
        air_density_kg_m3=x.air_density_kg_m3,vapor_density_kg_m3=x.vapor_density_kg_m3,wind_speed_m_s=x.wind_speed_m_s))
    emitted=surface_emissive(SurfaceEmissive(pool_radius_m=area["pool_radius_m"],flame_length_m=flame["flame_length_m"],
        burning_rate_kg_m2_s=rate,heat_of_combustion_j_kg=x.burning.heat_of_combustion_j_kg,radiative_fraction=x.radiative_fraction))
    setup=dict(pool_radius_m=area["pool_radius_m"],flame_length_m=flame["flame_length_m"],flame_tilt_rad=flame["flame_tilt_rad"],
        surface_emissive_power_w_m2=emitted["surface_emissive_power_w_m2"],atmosphere=x.atmosphere,
        equation_basis=x.equation_basis,distance_convention=x.distance_convention,maximum_surface_distance_m=x.maximum_surface_distance_m)
    personnel=pool_distance(PoolDistance(**setup,threshold_w_m2=x.personnel_threshold_w_m2))
    equipment=pool_distance(PoolDistance(**setup,threshold_w_m2=x.equipment_threshold_w_m2))
    return {"burning_rate_kg_m2_s":rate,**area,"flame_length_m":flame["flame_length_m"],"flame_tilt_rad":flame["flame_tilt_rad"],
            "surface_emissive_power_w_m2":emitted["surface_emissive_power_w_m2"],
            "personnel_area_m2":personnel["consequence_area_m2"],"equipment_area_m2":equipment["consequence_area_m2"],
            "personnel_safe_surface_distance_m":personnel["safe_surface_distance_m"],"equipment_safe_surface_distance_m":equipment["safe_surface_distance_m"],
            "personnel_status":personnel["status"],"equipment_status":equipment["status"],
            "equation_basis":x.equation_basis,"distance_convention":x.distance_convention}
