"""AST tabulated hole selection and geometry-to-release source composition."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure
from . import tank as t
from .tank_financial import TankComponent, generic_frequency

HOLES = ("small", "medium", "large", "rupture")


class ShellHoles(Model):
    tank_diameter_m: Positive


class BottomHoles(ShellHoles):
    has_release_prevention_barrier: bool


def _holes(diameters):
    areas = {h: math.pi/4*d*d for h,d in zip(HOLES,diameters)}
    ensure(all(a > 0 or d == 0 for a,d in zip(areas.values(),diameters)), "Hole area underflow", "numerical_failure")
    return {"diameter_by_hole_m": dict(zip(HOLES,diameters)), "area_by_hole_m2": areas}


@calculation("tank/shell-hole-sizes", "AST shell-course representative hole diameters and areas", ShellHoles,
    ["Part3 Tables6.3/6.3M; PDF p606"], limitations=[
        "Small3.175mm, medium6.35mm, large50.8mm, rupture=tank diameter/4. This selects representative holes, not measured-hole classification. Rupture diameter is a source convention, not validation of tank-diameter/4 orifice hydraulics."])
def shell_holes(x):
    ensure(x.tank_diameter_m/4 > 0, "Rupture diameter underflow", "numerical_failure")
    return _holes((.003175,.00635,.0508,x.tank_diameter_m/4))


@calculation("tank/bottom-hole-sizes", "AST bottom representative hole diameters and areas", BottomHoles,
    ["Part3 Tables6.4/6.4M; PDF pp606-607"], limitations=[
        "Small3.175mm with RPB or12.7mm without, medium/large zero, rupture=tank diameter/4. Printed SI Table6.4M rupture row shows only Yes; US Table6.4 explicitly covers Yes/No under shared tank-diameter/4 formula. No-RPB rupture follows that US row converted to SI, not an authorized SI erratum. No rupture flow/hole count inferred from Table6.5."])
def bottom_holes(x):
    ensure(x.tank_diameter_m/4 > 0, "Rupture diameter underflow", "numerical_failure")
    return _holes((.003175 if x.has_release_prevention_barrier else .0127,0.,0.,x.tank_diameter_m/4))


class ShellSource(Model):
    tank_diameter_m: Positive
    fill_height_m: NonNegative
    course_index: int = Field(ge=1,strict=True)
    course_height_m: Positive
    fluid: t.Fluid
    diameter_boundary_basis: Literal["printed_3_17_mm","inch_0_125"]
    discharge_coefficient: Fraction = .61
    gravity_m_s2: Positive = 9.81


class BottomSource(Model):
    tank_diameter_m: Positive
    fill_height_m: NonNegative
    fluid: t.Fluid
    soil: t.Soil
    water_density_kg_m3: Positive
    water_dynamic_viscosity_pa_s: Positive
    foundation: Literal["concrete_asphalt","other"]
    has_release_prevention_barrier: bool
    detection_overlap_basis: Literal["foundation_priority","barrier_priority"] | None = None
    transition_hole_basis: Literal["api581_printed","per_hole_scaled"]
    soil_contact_factor: Positive = .21
    gravity_m_s2: Positive = 9.81


def _release_outputs(holes,inventory,rates,detection,volumes,component_type):
    gff = generic_frequency(TankComponent(component_type=component_type))
    return {**holes,**inventory,"generic_frequency_by_hole_per_year":gff["by_hole_per_year"],
        "generic_total_per_year":gff["total_per_year"],"printed_generic_total_per_year":gff["printed_total_per_year"],
        "generic_total_basis":gff["total_basis"],
        "native_rate_by_hole_bbl_day":{h:rates[h]["native_rate_bbl_day"] if rates[h] is not None else None for h in HOLES},
        "mass_rate_by_hole_kg_s":{h:rates[h]["mass_rate_kg_s"] if rates[h] is not None else None for h in HOLES},
        "detection_time_by_hole_days":detection,
        "release_duration_by_hole_days":{h:volumes[h]["release_duration_days"] for h in HOLES},
        "released_volume_by_hole_bbl":{h:volumes[h]["released_volume_bbl"] for h in HOLES},
        "released_volume_by_hole_m3":{h:volumes[h]["released_volume_m3"] for h in HOLES},
        "released_mass_by_hole_kg":{h:volumes[h]["released_mass_kg"] for h in HOLES},
        "release_type":"continuous"}


_SOURCE_LIMITS = [
    "Uses representative Table6.1M liquid properties, constant head and C13=6.29bbl/m3. No operating-temperature EOS, connected inventory or transient drainage. Source mass=Bbl printing is not used as kg: mass is volume*density, the explicitly qualified dimensional interpretation.",
    "Table3.1 hole frequencies use eq3.208 summed total, with printed total returned separately. One component only; no whole-tank course summation, area consequences or damage applicability inferred. AST release type remains continuous. No generic detection/isolation reduction factors.",
]


@calculation("tank/shell-source-assessment", "Compose AST shell holes, head, inventory, rates and released quantities", ShellSource,
    ["Part3 §§6.1-6.7,Tables6.1M/6.3M,eqs(3.208)-(3.209),(3.214)-(3.227); PDF pp592-597,604,606"], limitations=_SOURCE_LIMITS+[
        "Equal-height courses; source at course lower edge. Above-fill courses use physical dry inventory/head0. Shell3.17mm vs3.175mm detection ambiguity requires explicit boundary basis. Eq3.209 evaluated for all four representative holes as STEP3.3 specifies; nominal rupture rate is a printed constant-head convention, not validated catastrophic-rupture hydraulics. Rupture uses full above-course inventory with null duration/detection; no invented rupture duration."])
def shell_source(x):
    properties = t.fluid_table(t.FluidLookup(fluid=x.fluid))
    rho = properties["liquid_density_kg_m3"]
    holes = shell_holes(ShellHoles(tank_diameter_m=x.tank_diameter_m))
    inventory = t.shell_inventory(t.ShellInventory(tank_diameter_m=x.tank_diameter_m,
        fill_height_m=x.fill_height_m,liquid_density_kg_m3=rho,course_index=x.course_index,course_height_m=x.course_height_m))
    ensure(all(math.isfinite(v) for v in inventory.values()), "Shell inventory overflow", "numerical_failure")
    rates, detection, volumes = {}, {}, {}
    for h in HOLES:
        diameter = holes["diameter_by_hole_m"][h]
        rates[h] = t.shell_flow(t.ShellFlow(hole_diameter_m=diameter,liquid_head_m=inventory["available_liquid_head_m"],
            liquid_density_kg_m3=rho,discharge_coefficient=x.discharge_coefficient,gravity_m_s2=x.gravity_m_s2))
        ensure(all(math.isfinite(v) for v in rates[h].values()), "Shell flow overflow", "numerical_failure")
        detection[h] = None if h == "rupture" else t.shell_detection(t.ShellDetection(
            hole_diameter_m=diameter,diameter_boundary_basis=x.diameter_boundary_basis))["detection_time_days"]
        volumes[h] = t.release_volume(t.ReleaseVolume(release_case="rupture" if h == "rupture" else "leak",
            native_rate_bbl_day=rates[h]["native_rate_bbl_day"],available_volume_m3=inventory["available_volume_m3"],
            liquid_density_kg_m3=rho,detection_time_days=detection[h] if detection[h] is not None else 0))
    return {**_release_outputs(holes,inventory,rates,detection,volumes,"COURSE-1-10"),
        "liquid_density_kg_m3":rho,"source_scope":"single_shell_course"}


@calculation("tank/bottom-source-assessment", "Compose AST soil, holes, inventory, seepage and released quantities", BottomSource,
    ["Part3 §§6.1-6.7,Tables6.1M/6.2M/6.4/6.4M/6.5,eqs(3.205)-(3.212),(3.219)-(3.230); PDF pp592-598,604-607"], limitations=_SOURCE_LIMITS+[
        "Soil arithmetic mean preserves reversed printed bounds; explicit water reference properties required. RPB small-hole head.0762m when filled; empty tank zero. SI C37 threshold retained despite SI/US mismatch. Transition count omission requires explicit printed vs per-hole-scaled basis. No-RPB rupture diameter follows complete US Table6.4 row; SI rupture row is incomplete.",
        "Medium/large holes have zero count/flow. Table6.5 gives no rupture count, so rupture flow and duration are null; rupture volume is whole inventory per eq3.230. Bottom detection with concrete/asphalt AND RPB requires explicit priority. Count outside30.5-91.4m is flagged, not qualified by this composition."])
def bottom_source(x):
    properties = t.fluid_table(t.FluidLookup(fluid=x.fluid))
    rho = properties["liquid_density_kg_m3"]
    soil = t.soil_table(t.SoilLookup(soil=x.soil))
    water = t.water_conductivity(t.WaterConductivity(**{k:soil[k] for k in (
        "printed_lower_bound_cm_s","printed_upper_bound_cm_s")}))["water_hydraulic_conductivity_m_day"]
    conductivity = t.fluid_conductivity(t.FluidConductivity(water_hydraulic_conductivity_m_day=water,
        liquid_density_kg_m3=rho,dynamic_viscosity_pa_s=properties["dynamic_viscosity_pa_s"],
        water_density_kg_m3=x.water_density_kg_m3,water_dynamic_viscosity_pa_s=x.water_dynamic_viscosity_pa_s))["product_hydraulic_conductivity_m_day"]
    ensure(math.isfinite(conductivity), "Product conductivity overflow", "numerical_failure")
    velocity = t.seepage(t.Seepage(product_hydraulic_conductivity_m_day=conductivity,porosity=soil["porosity"]))["seepage_velocity_m_day"]
    holes = bottom_holes(BottomHoles(tank_diameter_m=x.tank_diameter_m,
        has_release_prevention_barrier=x.has_release_prevention_barrier))
    counts = t.bottom_hole_count(t.BottomHoleCount(tank_diameter_m=x.tank_diameter_m))
    inventory = t.bottom_inventory(t.BottomInventory(tank_diameter_m=x.tank_diameter_m,fill_height_m=x.fill_height_m,liquid_density_kg_m3=rho))
    ensure(all(math.isfinite(v) for v in inventory.values()), "Bottom inventory overflow", "numerical_failure")
    detect = t.bottom_detection(t.BottomDetection(foundation=x.foundation,
        has_release_prevention_barrier=x.has_release_prevention_barrier,overlap_basis=x.detection_overlap_basis))
    rates, detection, volumes = {}, {}, {}
    for h in HOLES:
        rates[h] = None if h == "rupture" else t.bottom_flow(t.BottomFlow(hole_diameter_m=holes["diameter_by_hole_m"][h],
            liquid_height_m=x.fill_height_m,product_hydraulic_conductivity_m_day=conductivity,liquid_density_kg_m3=rho,
            number_of_holes=counts[h+"_hole_count"],has_release_prevention_barrier=x.has_release_prevention_barrier,
            transition_hole_basis=x.transition_hole_basis,soil_contact_factor=x.soil_contact_factor,gravity_m_s2=x.gravity_m_s2))
        rate = 0 if rates[h] is None else rates[h]["native_rate_bbl_day"]
        ensure(math.isfinite(rate), "Bottom flow overflow", "numerical_failure")
        detection[h] = None if h == "rupture" else detect["detection_time_days"]
        volumes[h] = t.release_volume(t.ReleaseVolume(release_case="rupture" if h == "rupture" else "leak",
            native_rate_bbl_day=rate,available_volume_m3=inventory["available_volume_m3"],liquid_density_kg_m3=rho,
            detection_time_days=detect["detection_time_days"]))
    return {**_release_outputs(holes,inventory,rates,detection,volumes,"TANKBOTTOM"),**counts,
        "liquid_density_kg_m3":rho,"product_hydraulic_conductivity_m_day":conductivity,"seepage_velocity_m_day":velocity,
        "bottom_flow_equation":rates["small"]["equation"],"applied_small_hole_multiplier":rates["small"]["applied_hole_multiplier"],
        "detection_time_days":detect["detection_time_days"],"detection_selected_basis":detect["selected_basis"],
        "source_scope":"single_tank_bottom"}
