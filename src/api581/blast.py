"""API581 TNT blast fit, bounded inversion and building-collapse probit.

The source provides no fit validity interval. Caller-supplied intervals are
checked for mathematical admissibility, which is not engineering validation.
"""
import math
from functools import lru_cache
from statistics import NormalDist
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .effects import TntEquivalence, tnt_equivalence

_A=(-.059965896,1.1288697,-7.9625216,25.106738,-30.396707,
    19.399862,-6.8853477,1.2825511,-.097705789)
_Q=tuple(i*_A[i] for i in range(1,len(_A)))
_FIT_LIMIT=("Printed inverse-log polynomial, not an exponential of the polynomial. "
    "C26=100 gives kPa; public pressure is Pa. Source specifies no fit validity "
    "interval. Caller must supply bounds and engineering basis; positive pressure "
    "and strictly decreasing behavior are checked over that interval. These checks "
    "do not establish experimental fit validity or LH2 applicability.")


class BlastFitDomain(Model):
    minimum_scaled_distance_m_kg13: Positive
    maximum_scaled_distance_m_kg13: Positive
    engineering_basis: str = Field(min_length=1,max_length=1000)


def _polynomial(coefficients,u):
    value=coefficients[-1]
    for coefficient in reversed(coefficients[:-1]):
        value=value*u+coefficient
    return value


def _pressure(scaled):
    return 100000*_polynomial(_A,1/math.log(scaled))


def _derivative_interval(a,b):
    """Outward-rounded interval Horner enclosure of dP_bar/d(1/ln R)."""
    # Also enclose rounding of integer*A[i] when derivative coefficients form.
    low=math.nextafter(_Q[-1],-math.inf)
    high=math.nextafter(_Q[-1],math.inf)
    for coefficient in reversed(_Q[:-1]):
        products=(low*a,low*b,high*a,high*b)
        low=math.nextafter(math.nextafter(min(products),-math.inf)+math.nextafter(coefficient,-math.inf),-math.inf)
        high=math.nextafter(math.nextafter(max(products),math.inf)+math.nextafter(coefficient,math.inf),math.inf)
    return low,high


@lru_cache(maxsize=128)
def _certify_decreasing(first,last):
    # R>1 -> u>0 and du/dR<0: Q(u)>0 proves pressure decreases with R.
    a=math.nextafter(1/math.log(last),-math.inf)
    b=math.nextafter(1/math.log(first),math.inf)
    pending=[(a,b,0)]
    visits=0
    while pending:
        a,b,depth=pending.pop()
        visits+=1
        low,high=_derivative_interval(a,b)
        if low > 0:
            continue
        ensure(high > 0 and depth < 24 and visits <= 8192,
               "Cannot certify strictly decreasing blast pressure over supplied interval","invalid_blast_fit_domain")
        mid=a+(b-a)/2
        ensure(a < mid < b,"Blast interval certification reached numerical resolution","invalid_blast_fit_domain")
        pending.extend(((a,mid,depth+1),(mid,b,depth+1)))


def _domain(x):
    first,last=x.minimum_scaled_distance_m_kg13,x.maximum_scaled_distance_m_kg13
    ensure(first > 1 and last > first and bool(x.engineering_basis.strip()),
           "Blast fit requires ordered scaled bounds above1 and nonblank engineering basis","invalid_blast_fit_domain")
    pfirst,plast=_pressure(first),_pressure(last)
    ensure(math.isfinite(pfirst) and math.isfinite(plast) and pfirst > plast > 0,
           "Blast fit must have finite positive decreasing endpoint pressures","invalid_blast_fit_domain")
    _certify_decreasing(first,last)
    return first,last,pfirst,plast


class ScaledDistance(Model):
    distance_m: Positive
    tnt_equivalent_mass_kg: Positive


@calculation("effects/vce-scaled-distance", "Hopkinson TNT scaled distance", ScaledDistance,
             ["Part3 eq(3.171), Annex3.B C27=1; PDF pp558,648"],
             limitations=["SI distance m and TNT equivalent mass kg; output units m/kg^(1/3). Scaling alone does not establish blast-curve applicability. Zero TNT mass has no defined scaled distance."])
def scaled_distance(x):
    result=x.distance_m/math.cbrt(x.tnt_equivalent_mass_kg)
    ensure(math.isfinite(result) and result > 0,"Scaled distance outside finite positive numerical domain","numerical_failure")
    return {"scaled_distance_m_kg13":result}


class ScaledOverpressure(Model):
    scaled_distance_m_kg13: Positive
    fit_domain: BlastFitDomain


@calculation("effects/vce-scaled-overpressure", "Hopkinson-scaled blast overpressure fit", ScaledOverpressure,
             ["Part3 eq(3.170), Annex3.B C26=100; PDF pp558,648"],limitations=[_FIT_LIMIT])
def scaled_overpressure(x):
    first,last,_,_=_domain(x.fit_domain)
    scaled=x.scaled_distance_m_kg13
    ensure(first <= scaled <= last,"Scaled distance outside caller blast fit interval","outside_blast_fit_domain")
    pressure=_pressure(scaled)
    ensure(math.isfinite(pressure) and pressure > 0,"Blast pressure outside numerical domain","numerical_failure")
    u=1/math.log(scaled)
    slope=-100000*u*u/scaled*_polynomial(_Q,u)
    return {"side_on_overpressure_pa":pressure,"slope_pa_per_scaled_distance":slope}


class BlastOverpressure(ScaledDistance):
    fit_domain: BlastFitDomain


@calculation("effects/vce-blast-overpressure", "TNT blast pressure at physical distance", BlastOverpressure,
             ["Part3 eqs(3.170)-(3.171); PDF p558"],limitations=[_FIT_LIMIT,
                          "Side-on gauge overpressure, not reflected pressure or absolute pressure. Point-source TNT equivalence has near-field limitations."])
def overpressure(x):
    scaled=scaled_distance(ScaledDistance(distance_m=x.distance_m,tnt_equivalent_mass_kg=x.tnt_equivalent_mass_kg))
    result=scaled_overpressure(ScaledOverpressure(**scaled,fit_domain=x.fit_domain))
    return {**scaled,**result}


class BuildingProbit(Model):
    side_on_overpressure_pa: Positive


@calculation("effects/blast-building-probit", "Blast-induced process-building collapse probit", BuildingProbit,
             ["Part3 eq(3.172), Annex3.B C28=1000/kPa; PDF pp558,648"],
             limitations=["Probit=-23.8+2.92*ln(overpressure in Pa); probability=Phi(probit-5). Building-collapse mechanism used as a serious-injury proxy, not open-air lung hemorrhage, direct fatality, or a pressure-duration/structural-response model."])
def building_probit(x):
    probit=-23.8+2.92*math.log(x.side_on_overpressure_pa)
    probability=.5*math.erfc(-(probit-5)/math.sqrt(2))
    return {"probit":probit,"building_collapse_probability":probability}


class BuildingPressureThreshold(Model):
    building_collapse_probability: Fraction


@calculation("effects/blast-building-pressure-threshold", "Pressure for target building-collapse probability", BuildingPressureThreshold,
             ["Part3 eq(3.172) inverse, STEP8.14; PDF pp558,564"],
             origin="api581_probit_inverse",
             limitations=["Target probability must be strictly between0 and1. This is the building-collapse proxy, not a universal personnel injury threshold. Part3 STEP8.14 uses probit5 (50%); standalone inverse also supports explicitly selected alternative targets."])
def building_threshold(x):
    ensure(0 < x.building_collapse_probability < 1,"Building-collapse target must be strictly between0 and1")
    probit=5+NormalDist().inv_cdf(x.building_collapse_probability)
    pressure=math.exp((probit+23.8)/2.92)
    return {"probit":probit,"side_on_overpressure_pa":pressure}


class BlastDistance(Model):
    tnt_equivalent_mass_kg: NonNegative
    threshold_overpressure_pa: Positive
    fit_domain: BlastFitDomain
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


@calculation("effects/vce-blast-distance", "TNT blast threshold distance and consequence area", BlastDistance,
             ["Part3 eqs(3.170)-(3.171),(3.173)-(3.174); PDF p558"],
             origin="api581_bounded_blast_threshold_iteration",limitations=[_FIT_LIMIT,
                          "Requires threshold bracket within supplied scaled interval; does not extrapolate to source or beyond bounds. Returns safe upper distance bracket with error bounded by distance tolerance. Zero TNT mass returns no_explosion and zero area. Area=pi*distance^2."])
def distance(x):
    first,last,pfirst,plast=_domain(x.fit_domain)
    if x.tnt_equivalent_mass_kg == 0:
        return {"safe_distance_m":0,"consequence_area_m2":0,"scaled_distance_m_kg13":None,
                "status":"no_explosion","iterations":0,"pressure_residual_pa":None}
    threshold=x.threshold_overpressure_pa
    ensure(plast <= threshold <= pfirst,"Threshold not bracketed in supplied blast fit interval","unbracketed_threshold")
    root=math.cbrt(x.tnt_equivalent_mass_kg)
    low,high=first*root,last*root
    ensure(math.isfinite(high) and low > 0,"Blast distance bracket outside numerical domain","numerical_failure")
    iterations=0
    if threshold == pfirst:
        high=low
    elif threshold != plast:
        while high-low > x.distance_tolerance_m and iterations < x.maximum_iterations:
            mid=low+(high-low)/2
            ensure(low < mid < high,"Blast iteration reached floating point resolution","numerical_failure")
            if _pressure(mid/root) > threshold:
                low=mid
            else:
                high=mid
            iterations+=1
        ensure(high-low <= x.distance_tolerance_m,"Blast threshold iteration did not converge","nonconvergent_threshold")
    scaled=high/root
    return {"safe_distance_m":high,"consequence_area_m2":math.pi*high**2,
            "scaled_distance_m_kg13":scaled,"status":"threshold_solved","iterations":iterations,
            "pressure_residual_pa":_pressure(scaled)-threshold}


class BlastConsequence(TntEquivalence):
    mass_basis: Literal["between_flammability_limits", "total_released_flammable"]
    yield_engineering_basis: str = Field(min_length=1,max_length=1000)
    personnel_building_collapse_probability: Fraction = .5
    equipment_threshold_overpressure_pa: Positive = 34500
    fit_domain: BlastFitDomain
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


@calculation("effects/vce-blast-consequence", "Cloud mass to TNT blast personnel/equipment areas", BlastConsequence,
             ["Part3 §§5.8.5.3-5.8.5.6 eqs(3.169)-(3.174), STEP8.14; PDF pp557-558,564"],
             origin="api581_tnt_blast_composition",limitations=[_FIT_LIMIT,
                          "Caller supplies cloud mass at ignition or total released flammable mass and a consistent qualified yield. Source recommends yield1 for mass between LFL/UFL; typical total-release yields.03-.19 are not automatically assigned by material. Dispersion/ignition timing not solved here.",
                          "TNT heat is mandatory because printed4648J/kg conflicts with2000Btu/lb; no silent correction. Personnel target defaults to50% building collapse per Part3 STEP8.14 (probit5), with explicit alternative targets supported. This is not direct lethality. No ignition/event weighting, congestion correction or TNO multi-energy model."])
def consequence(x):
    ensure(bool(x.yield_engineering_basis.strip()) and bool(x.tnt_heat_source.strip()),
           "TNT heat and explosion yield require nonblank engineering source/basis")
    _domain(x.fit_domain)
    tnt=tnt_equivalence(TntEquivalence(**x.model_dump(include=set(TntEquivalence.model_fields))))["tnt_equivalent_mass_kg"]
    ensure(math.isfinite(tnt),"TNT equivalent mass outside numerical domain","numerical_failure")
    ensure(tnt > 0 or x.flammable_cloud_mass_kg == 0 or x.explosion_yield == 0,
           "TNT equivalent mass underflow","numerical_failure")
    personnel_pressure=building_threshold(BuildingPressureThreshold(
        building_collapse_probability=x.personnel_building_collapse_probability))["side_on_overpressure_pa"]
    setup=dict(tnt_equivalent_mass_kg=tnt,fit_domain=x.fit_domain,
        distance_tolerance_m=x.distance_tolerance_m,maximum_iterations=x.maximum_iterations)
    personnel=distance(BlastDistance(**setup,threshold_overpressure_pa=personnel_pressure))
    equipment=distance(BlastDistance(**setup,threshold_overpressure_pa=x.equipment_threshold_overpressure_pa))
    return {"tnt_equivalent_mass_kg":tnt,"personnel_threshold_overpressure_pa":personnel_pressure,
            "personnel_building_collapse_probability":x.personnel_building_collapse_probability,
            "equipment_threshold_overpressure_pa":x.equipment_threshold_overpressure_pa,
            "personnel_safe_distance_m":personnel["safe_distance_m"],"equipment_safe_distance_m":equipment["safe_distance_m"],
            "personnel_area_m2":personnel["consequence_area_m2"],"equipment_area_m2":equipment["consequence_area_m2"],
            "personnel_status":personnel["status"],"equipment_status":equipment["status"],"mass_basis":x.mass_basis}
