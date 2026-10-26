"""AST source, inventory and seepage calculations with printed native units."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

Fluid=Literal["gasoline","light_diesel","heavy_diesel","fuel_oil","crude_oil","heavy_fuel_oil","heavy_crude_oil"]
Soil=Literal["coarse_sand","fine_sand","very_fine_sand","silt","sandy_clay","clay","concrete_asphalt","gravel"]
_FLUIDS={"gasoline":(100,684.018,.00401),"light_diesel":(149,734.011,.00104),"heavy_diesel":(205,764.527,.00246),
    "fuel_oil":(280,775.019,.0369),"crude_oil":(280,775.019,.0369),"heavy_fuel_oil":(422,900.026,.046),"heavy_crude_oil":(422,900.026,.046)}
_SOILS={"coarse_sand":(.1,.01,.33),"fine_sand":(.01,.001,.33),"very_fine_sand":(.001,.00001,.33),
    "silt":(1e-5,1e-6,.41),"sandy_clay":(1e-6,1e-7,.45),"clay":(1e-7,1e-8,.50),
    "concrete_asphalt":(1e-10,1e-11,.3),"gravel":(1,10,.4)}
BBL_PER_M3=6.29  # Printed C13, not a silently substituted exact oil-barrel conversion.


class FluidLookup(Model):
    fluid: Fluid


@calculation("tank/fluid-table", "AST SI representative fluid properties", FluidLookup,
             ["Part3 Table6.1M; PDF p604"],limitations=["Historical representative liquid properties, not an operating-temperature EOS. Printed SI density/viscosity retained. No automatic alias to a Level1 representative fluid or LH2 properties."])
def fluid_table(x):
    mw,rho,mu=_FLUIDS[x.fluid]
    return {"molecular_weight_kg_kmol":mw,"liquid_density_kg_m3":rho,"dynamic_viscosity_pa_s":mu}


class SoilLookup(Model):
    soil: Soil


@calculation("tank/soil-table", "AST SI soil conductivity bounds and porosity", SoilLookup,
             ["Part3 Table6.2M; PDF p605"],limitations=["Printed lower/upper labels are reversed for most rows; fields preserve printed labels and values without sorting. Eq3.207 arithmetic mean is symmetric. Raw conductivity units cm/s, not m/day. Representative soil values need site qualification."])
def soil_table(x):
    lower,upper,porosity=_SOILS[x.soil]
    return {"printed_lower_bound_cm_s":lower,"printed_upper_bound_cm_s":upper,"porosity":porosity}


class WaterConductivity(Model):
    printed_lower_bound_cm_s: NonNegative
    printed_upper_bound_cm_s: NonNegative


@calculation("tank/soil-water-conductivity", "Mean water hydraulic conductivity in m/day", WaterConductivity,
             ["Part3 eq(3.207),Annex3.B C31; PDF pp593,648"],limitations=["Uses arithmetic mean, not geometric mean: C31=864 converts cm/s to m/day. Accepts reversed printed bound ordering without relabeling it."])
def water_conductivity(x):
    return {"water_hydraulic_conductivity_m_day":432*x.printed_lower_bound_cm_s+432*x.printed_upper_bound_cm_s}


class FluidConductivity(Model):
    water_hydraulic_conductivity_m_day: NonNegative
    liquid_density_kg_m3: Positive
    dynamic_viscosity_pa_s: Positive
    water_density_kg_m3: Positive
    water_dynamic_viscosity_pa_s: Positive


@calculation("tank/fluid-conductivity", "Product hydraulic conductivity from water reference", FluidConductivity,
             ["Part3 eq(3.205); PDF p592"],limitations=["Water density/viscosity must be supplied at qualified reference conditions. Product/water density ratio and inverse viscosity ratio applied; no hidden standard-water defaults or temperature correction."])
def fluid_conductivity(x):
    if x.water_hydraulic_conductivity_m_day == 0:
        return {"product_hydraulic_conductivity_m_day":0}
    value=math.exp(math.log(x.water_hydraulic_conductivity_m_day)+math.log(x.liquid_density_kg_m3)-math.log(x.water_density_kg_m3)
        +math.log(x.water_dynamic_viscosity_pa_s)-math.log(x.dynamic_viscosity_pa_s))
    ensure(value > 0,"Product conductivity underflow","numerical_failure")
    return {"product_hydraulic_conductivity_m_day":value}


class Seepage(Model):
    product_hydraulic_conductivity_m_day: NonNegative
    porosity: Fraction


@calculation("tank/seepage-velocity", "AST product seepage velocity through soil", Seepage,
             ["Part3 eq(3.206); PDF p592"],limitations=["Conductivity divided by strictly positive porosity. Representative porous-medium approximation; no groundwater plume or capillary/unsaturated transport solver."])
def seepage(x):
    ensure(x.porosity > 0,"Porosity must be strictly positive")
    return {"seepage_velocity_m_day":x.product_hydraulic_conductivity_m_day/x.porosity}


class BottomHoleCount(Model):
    tank_diameter_m: Positive


@calculation("tank/bottom-hole-count", "AST bottom small-hole count from diameter", BottomHoleCount,
             ["Part3 Table6.5,Annex3.B C36; PDF pp607,649"],limitations=["max(1,nint((D/30.5)^2)) with positive half-up nearest-integer rounding, not Python bankers rounding. Medium/large counts0. Formula evaluated outside tabulated30.5-91.4m range is flagged; no extrapolation validity claimed."])
def bottom_hole_count(x):
    value=(x.tank_diameter_m/30.5)**2
    ensure(math.isfinite(value),"Hole count outside numerical domain","numerical_failure")
    return {"small_hole_count":max(1,math.floor(value+.5)),"medium_hole_count":0,"large_hole_count":0,
            "outside_tabulated_diameter_range":not 30.5 <= x.tank_diameter_m <= 91.4}


class BottomInventory(Model):
    tank_diameter_m: Positive
    fill_height_m: NonNegative
    liquid_density_kg_m3: Positive


def _inventory(diameter,head,density):
    volume=math.pi/4*diameter**2*head if head > 0 else 0
    ensure(volume > 0 or head == 0,"Positive tank inventory underflow","numerical_failure")
    mass=volume*density
    ensure(mass > 0 or volume == 0,"Positive inventory mass underflow","numerical_failure")
    return {"available_volume_m3":volume,"available_volume_bbl":volume*BBL_PER_M3,"available_mass_kg":mass}


@calculation("tank/bottom-inventory", "Full cylindrical AST bottom inventory", BottomInventory,
             ["Part3 eqs(3.219)-(3.221); PDF p596"],limitations=["Vertical cylindrical tank, full contents above bottom. Printed C13=6.29bbl/m3 retained. No roof volume, dished geometry or connected inventory."])
def bottom_inventory(x):
    return _inventory(x.tank_diameter_m,x.fill_height_m,x.liquid_density_kg_m3)


class ShellInventory(BottomInventory):
    course_index: int = Field(ge=1,strict=True)
    course_height_m: Positive


@calculation("tank/shell-course-inventory", "Inventory and head above AST shell-course lower edge", ShellInventory,
             ["Part3 eqs(3.214)-(3.218); PDF pp595-596"],limitations=["Leak located at course lower edge, equal course heights, index starts1. Above-fill courses return physical dry head/inventory0 instead of negative fluid. This dry-course handling is explicit geometry interpretation. Printed C13=6.29 retained."])
def shell_inventory(x):
    elevation=(x.course_index-1)*x.course_height_m
    head=max(0,x.fill_height_m-elevation)
    return {**_inventory(x.tank_diameter_m,head,x.liquid_density_kg_m3),"course_bottom_elevation_m":elevation,
            "available_liquid_head_m":head,"course_wet":head > 0}


def _flow(native,density):
    volume=native/(BBL_PER_M3*86400)
    mass=volume*density
    ensure(volume > 0 and mass > 0 or native == 0,"Positive tank flow conversion underflow","numerical_failure")
    return {"native_rate_bbl_day":native,"volume_rate_m3_s":volume,"mass_rate_kg_s":mass}


class ShellFlow(Model):
    hole_diameter_m: NonNegative
    liquid_head_m: NonNegative
    liquid_density_kg_m3: Positive
    discharge_coefficient: Fraction = .61
    gravity_m_s2: Positive = 9.81


@calculation("tank/shell-flow", "Constant-head AST shell-course liquid discharge", ShellFlow,
             ["Part3 eq(3.209),Annex3.B C32; PDF pp593-594,648"],limitations=["Printed C32=.543 with orifice area mm2, g/head in SI, native result bbl/day. Converts result to m3/s with C13=6.29; rounded constants differ slightly from exact Torricelli units. Cd constrained to source fully-turbulent.60-.65 range, default.61. Constant head, not tank drainage transient or detection/isolation reduction."])
def shell_flow(x):
    ensure(.60 <= x.discharge_coefficient <= .65,"Shell discharge coefficient outside source.60-.65 range")
    area=math.pi*x.hole_diameter_m**2/4
    native=.543*x.discharge_coefficient*(area*1e6)*math.sqrt(2*x.gravity_m_s2*x.liquid_head_m)
    ensure(native > 0 or x.hole_diameter_m == 0 or x.liquid_head_m == 0,"Shell source rate underflow","numerical_failure")
    return {**_flow(native,x.liquid_density_kg_m3),"hole_area_m2":area}


class BottomFlow(Model):
    hole_diameter_m: NonNegative
    liquid_height_m: NonNegative
    product_hydraulic_conductivity_m_day: NonNegative
    liquid_density_kg_m3: Positive
    number_of_holes: int = Field(ge=0,strict=True)
    has_release_prevention_barrier: bool
    transition_hole_basis: Literal["api581_printed","per_hole_scaled"]
    soil_contact_factor: Positive = .21
    gravity_m_s2: Positive = 9.81


@calculation("tank/bottom-flow", "AST bottom Bernoulli/Giraud/transition discharge", BottomFlow,
             ["Part3 eqs(3.210)-(3.212),Annex3.B C33-C40; PDF pp594,649"],
             origin="api581_bottom_flow_with_explicit_transition_count_basis",
             limitations=["Native units d mm, head m, Kh m/day, result bbl/day. Printed C37 SI/US regime thresholds disagree under conversion; SI threshold used literally, no cross-unit regime equivalence claimed. Eq3.210/211 multiply number of holes; printed3.212 omits it. Required api581_printed preserves omission; per_hole_scaled is explicit alternative, not authorized erratum. RPB substitutes head.0762m when liquid exists; empty tank remains zero. Soil-contact factor.21-1.15. Small-hole constant-head soil leak model, not rupture inventory or groundwater transport."])
def bottom_flow(x):
    ensure(.21 <= x.soil_contact_factor <= 1.15,"Soil contact factor outside source.21-1.15 range")
    d=x.hole_diameter_m*1000
    h=0 if x.liquid_height_m == 0 else .0762 if x.has_release_prevention_barrier else x.liquid_height_m
    kh=x.product_hydraulic_conductivity_m_day
    if d == 0 or h == 0 or kh == 0 or x.number_of_holes == 0:
        return {**_flow(0,x.liquid_density_kg_m3),"per_hole_native_rate_bbl_day":0,"equation":"zero_flow","liquid_head_used_m":h,
                "lower_conductivity_threshold_m_day":None,"upper_conductivity_threshold_m_day":None,
                "applied_hole_multiplier":0,"transition_hole_basis":x.transition_hole_basis}
    upper=86.4*d**2
    lower=1.408e-8*math.exp((1.8*math.log(d)-math.log(x.soil_contact_factor)-.4*math.log(h))/.74)
    ensure(math.isfinite(upper) and math.isfinite(lower) and 0 < lower <= upper,"Bottom-flow threshold ordering outside model domain")
    if kh > upper:
        single=.0815*math.pi*d**2*math.sqrt(2*x.gravity_m_s2*h)
        equation="3.210"
    elif kh <= lower:
        single=29.6195*x.soil_contact_factor*d**.2*h**.9*kh**.74
        equation="3.211"
    else:
        ld,lh,lk=math.log10(d),math.log10(h),math.log10(kh)
        m=5.9352-.4324*ld+.5405*lh
        ensure(m > 0,"Transition exponent m must be positive")
        base=(3.9365+2*ld-lk)/m
        ensure(base > 0,"Transition fractional-power base must be positive")
        single=1.1341*10**(2*ld+.5*lh-.74*base**m)
        equation="3.212"
    multiplier=1 if equation == "3.212" and x.transition_hole_basis == "api581_printed" else x.number_of_holes
    ensure(single > 0,"Positive bottom discharge underflow","numerical_failure")
    return {**_flow(single*multiplier,x.liquid_density_kg_m3),"per_hole_native_rate_bbl_day":single,"equation":equation,
            "liquid_head_used_m":h,"lower_conductivity_threshold_m_day":lower,"upper_conductivity_threshold_m_day":upper,
            "applied_hole_multiplier":multiplier,"transition_hole_basis":x.transition_hole_basis}


class ShellDetection(Model):
    hole_diameter_m: NonNegative
    diameter_boundary_basis: Literal["printed_3_17_mm","inch_0_125"]


@calculation("tank/shell-detection-time", "AST shell leak detection-time criterion", ShellDetection,
             ["Part3 §6.7.2 STEP7.2,eq(3.223); PDF pp596-597"],limitations=["Source prints3.17mm paired with.125inch=3.175mm; required basis preserves selection. Diameter at/below selected boundary7days, above1day. AST does not apply generic detection/isolation reduction factors."])
def shell_detection(x):
    boundary=.00317 if x.diameter_boundary_basis == "printed_3_17_mm" else .003175
    return {"detection_time_days":7 if x.hole_diameter_m <= boundary else 1,"diameter_boundary_m":boundary}


class BottomDetection(Model):
    foundation: Literal["concrete_asphalt","other"]
    has_release_prevention_barrier: bool
    overlap_basis: Literal["foundation_priority","barrier_priority"] | None = None


@calculation("tank/bottom-detection-time", "AST bottom leak detection-time criterion", BottomDetection,
             ["Part3 §6.7.3 STEP7.2; PDF p597"],limitations=["Concrete/asphalt7days, RPB30days, otherwise360days. Conditions overlap if concrete/asphalt AND RPB: explicit priority required instead of inventing precedence. This is source detection time, not a generic isolation-system factor."])
def bottom_detection(x):
    concrete=x.foundation == "concrete_asphalt"
    if concrete and x.has_release_prevention_barrier:
        ensure(x.overlap_basis is not None,"Concrete/asphalt with RPB requires explicit detection priority")
        return {"detection_time_days":7 if x.overlap_basis == "foundation_priority" else 30,
                "selected_basis":"concrete_asphalt" if x.overlap_basis == "foundation_priority" else "barrier"}
    return {"detection_time_days":7 if concrete else 30 if x.has_release_prevention_barrier else 360,
            "selected_basis":"concrete_asphalt" if concrete else "barrier" if x.has_release_prevention_barrier else "unprotected"}


class ReleaseVolume(Model):
    release_case: Literal["leak","rupture"]
    native_rate_bbl_day: NonNegative
    available_volume_m3: NonNegative
    liquid_density_kg_m3: Positive
    detection_time_days: NonNegative


@calculation("tank/release-volume", "Inventory-limited AST leakage or full-volume rupture", ReleaseVolume,
             ["Part3 eqs(3.223)-(3.230),§6.5; PDF pp596-598"],
             origin="api581_release_volume_with_dimensional_mass_conversion",
             limitations=["Leak volume is min(rate*min(inventory/rate,detection time),inventory); rupture uses all available volume without invented duration. Source AST release type remains continuous. Eq3.225/227 print mass=Bbl without density/conversion; printed_mass_index preserves that number separately. released_mass_kg uses(volume m3*density) from3.218/221, an explicit dimensional interpretation, not an authorized erratum. C13=6.29 retained."])
def release_volume(x):
    available=x.available_volume_m3*BBL_PER_M3
    if x.release_case == "rupture":
        native=available
        duration=None
    elif x.native_rate_bbl_day == 0 or available == 0:
        native=duration=0
    else:
        duration=min(available/x.native_rate_bbl_day,x.detection_time_days)
        ensure(duration > 0 or x.detection_time_days == 0,"Positive AST leak duration underflow","numerical_failure")
        native=min(available,x.native_rate_bbl_day*duration)
        ensure(native > 0 or x.detection_time_days == 0,"Positive AST release volume underflow","numerical_failure")
    volume=x.available_volume_m3 if native == available else native/BBL_PER_M3
    mass=volume*x.liquid_density_kg_m3
    ensure(volume > 0 and mass > 0 or native == 0,"AST volume/mass conversion underflow","numerical_failure")
    return {"release_duration_days":duration,"released_volume_bbl":native,"released_volume_m3":volume,
            "released_mass_kg":mass,"printed_mass_index":native,"release_type":"continuous"}
