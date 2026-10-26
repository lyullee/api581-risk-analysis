"""Physical explosion/BLEVE and Level2 NFNT aggregation in explicit SI units."""
import math
from typing import Annotated, Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .blast import (BlastFitDomain, BlastDistance, distance,
                    BuildingPressureThreshold, building_threshold)

Hole = Literal["small", "medium", "large", "rupture"]
Gamma = Annotated[float,Field(gt=1,strict=True,allow_inf_nan=False)]


class RuptureConditions(Model):
    burst_pressure_pa_abs: Positive
    ambient_pressure_pa_abs: Positive = 101325


def _pressure_difference(x):
    ensure(x.burst_pressure_pa_abs >= x.ambient_pressure_pa_abs,
           "Burst pressure must be at least ambient absolute pressure")
    return x.burst_pressure_pa_abs-x.ambient_pressure_pa_abs


class PhysicalTnt(RuptureConditions):
    vapor_volume_m3: NonNegative
    heat_capacity_ratio: Gamma


@calculation("effects/physical-explosion-tnt", "Gas-vessel Brode energy and TNT equivalent", PhysicalTnt,
             ["Part3 eq(3.192), Annex3.B C29; PDF pp569,648; pressure units PDF578"],
             limitations=["C29=4.303e-4 with source pressures in kPa; Pa inputs therefore use4.303e-7 kg/J. Uses vapor space volume, not total two-phase vessel volume. k>1, absolute burst pressure>=ambient. Returns potential rupture energy, not ignition-dependent combustion energy; no real-gas or vessel fragmentation calculation."])
def physical_tnt(x):
    delta=_pressure_difference(x)
    energy=x.vapor_volume_m3*delta/(x.heat_capacity_ratio-1)
    equivalent=4.303e-7*energy
    ensure(math.isfinite(energy) and math.isfinite(equivalent),"Physical rupture energy exceeds numerical domain","numerical_failure")
    ensure(equivalent > 0 or delta == 0 or x.vapor_volume_m3 == 0,
           "Physical rupture energy underflow","numerical_failure")
    return {"vapor_stored_energy_j":energy,"tnt_equivalent_mass_kg":equivalent}


class FlashedAmount(Model):
    stored_liquid_mass_kg: NonNegative
    liquid_flash_mass_fraction: Fraction
    molecular_weight_kg_kmol: Positive


@calculation("release/bleve-flashed-amount", "Flashed liquid mass and amount for BLEVE", FlashedAmount,
             ["Part3 STEP10.3(1), nomenclature nv/MW; PDF pp571,576"],
             origin="api581_input_preparation",
             limitations=["Caller supplies liquid flash mass fraction qualified at atmospheric release; this is not an EOS/isenthalpic flash solver. Amount is kmol (source kg-mol), not mol. Only stored liquid is counted; pre-existing vapor is handled separately."])
def flashed_amount(x):
    mass=x.stored_liquid_mass_kg*x.liquid_flash_mass_fraction
    amount=mass/x.molecular_weight_kg_kmol
    ensure(math.isfinite(amount),"Flashed amount exceeds numerical domain","numerical_failure")
    ensure(amount > 0 or x.stored_liquid_mass_kg == 0 or x.liquid_flash_mass_fraction == 0,
           "Flashed amount underflow","numerical_failure")
    return {"flashed_liquid_mass_kg":mass,"flashed_amount_kmol":amount}


class BleveLiquidTnt(RuptureConditions):
    flashed_amount_kmol: NonNegative
    storage_temperature_k: Positive


@calculation("effects/bleve-liquid-tnt", "Flashed-liquid BLEVE expansion energy and TNT equivalent", BleveLiquidTnt,
             ["Part3 eq(3.195), Annex3.B C30; PDF pp569,648; nv/R units PDF576,578"],
             limitations=["Uses printed C30=9.76e-8 kg/J and R=8314 J/(kmol*K), nv in kmol, storage temperature K, natural log of absolute burst/ambient pressure. Does not infer flash amount from fluid properties. Vapor-space contribution is excluded and must be added separately for two-phase contents. No combustion/fireball energy included."])
def bleve_liquid_tnt(x):
    delta=_pressure_difference(x)
    # log1p preserves tiny positive overpressure; logarithm difference avoids
    # overflow of the pressure ratio for widely separated positive pressures.
    log_ratio=(math.log1p(delta/x.ambient_pressure_pa_abs) if delta <= x.ambient_pressure_pa_abs
               else math.log(x.burst_pressure_pa_abs)-math.log(x.ambient_pressure_pa_abs))
    energy=x.flashed_amount_kmol*8314*x.storage_temperature_k*log_ratio
    equivalent=9.76e-8*energy
    ensure(math.isfinite(energy) and math.isfinite(equivalent),"BLEVE expansion energy exceeds numerical domain","numerical_failure")
    ensure(equivalent > 0 or delta == 0 or x.flashed_amount_kmol == 0,
           "BLEVE expansion energy underflow","numerical_failure")
    return {"liquid_expansion_energy_j":energy,"tnt_equivalent_mass_kg":equivalent}


class BlastTargets(Model):
    hole: Hole
    fit_domain: BlastFitDomain
    personnel_building_collapse_probability: Fraction = .5
    equipment_threshold_overpressure_pa: Positive = 34500
    distance_tolerance_m: Positive = 1e-5
    maximum_iterations: int = Field(default=100,ge=10,le=300,strict=True)


def _targets(x,potential):
    event=potential if x.hole == "rupture" else 0
    pressure=building_threshold(BuildingPressureThreshold(
        building_collapse_probability=x.personnel_building_collapse_probability))["side_on_overpressure_pa"]
    setup=dict(tnt_equivalent_mass_kg=event,fit_domain=x.fit_domain,
        distance_tolerance_m=x.distance_tolerance_m,maximum_iterations=x.maximum_iterations)
    personnel=distance(BlastDistance(**setup,threshold_overpressure_pa=pressure))
    equipment=distance(BlastDistance(**setup,threshold_overpressure_pa=x.equipment_threshold_overpressure_pa))
    return {"potential_tnt_equivalent_mass_kg":potential,"event_tnt_equivalent_mass_kg":event,
            "personnel_threshold_overpressure_pa":pressure,"equipment_threshold_overpressure_pa":x.equipment_threshold_overpressure_pa,
            "personnel_building_collapse_probability":x.personnel_building_collapse_probability,
            "personnel_safe_distance_m":personnel["safe_distance_m"],"equipment_safe_distance_m":equipment["safe_distance_m"],
            "personnel_area_m2":personnel["consequence_area_m2"],"equipment_area_m2":equipment["consequence_area_m2"],
            "personnel_status":personnel["status"] if x.hole == "rupture" else "not_rupture",
            "equipment_status":equipment["status"] if x.hole == "rupture" else "not_rupture","hole":x.hole}


class PhysicalConsequence(PhysicalTnt,BlastTargets):
    pass


@calculation("effects/physical-explosion-consequence", "Gas-vessel rupture blast consequence", PhysicalConsequence,
             ["Part3 eqs(3.192)-(3.194), STEP10.2; PDF pp569-571"],
             origin="api581_physical_explosion_composition",
             limitations=["Only rupture hole produces blast area; other holes return not_rupture with zero event equivalent and area while retaining potential inventory rupture energy. Personnel default is probit5 (50% building collapse), equipment default34500Pa. Reuses caller-qualified TNT fit domain; no extrapolation, direct lethality, fragmentation or LH2 validation."])
def physical_consequence(x):
    energy=physical_tnt(PhysicalTnt(**x.model_dump(include=set(PhysicalTnt.model_fields))))
    return {"vapor_stored_energy_j":energy["vapor_stored_energy_j"],**_targets(x,energy["tnt_equivalent_mass_kg"])}


class VaporPortion(Model):
    vapor_volume_m3: NonNegative
    heat_capacity_ratio: Gamma


class BleveConsequence(BleveLiquidTnt,BlastTargets):
    stored_vapor: VaporPortion | None = None


@calculation("effects/bleve-consequence", "Liquid/two-phase BLEVE blast consequence", BleveConsequence,
             ["Part3 eqs(3.192),(3.195)-(3.197), STEP10.3; PDF pp569-572"],
             origin="api581_bleve_composition",
             limitations=["Sums liquid and pre-existing vapor TNT equivalents using their distinct printed C30/C29 coefficients. Shared absolute burst/ambient pressure; vapor volume must exclude liquid, flashed amount must exclude pre-existing vapor. No automatic EOS, superheat applicability, fireball or combustion calculation. Only rupture produces blast area. Caller-qualified fit domain and building-collapse proxy limits apply; LH2 validation outstanding."])
def bleve_consequence(x):
    liquid=bleve_liquid_tnt(BleveLiquidTnt(**x.model_dump(include=set(BleveLiquidTnt.model_fields))))
    vapor={"vapor_stored_energy_j":0,"tnt_equivalent_mass_kg":0}
    if x.stored_vapor is not None:
        vapor=physical_tnt(PhysicalTnt(**x.stored_vapor.model_dump(),burst_pressure_pa_abs=x.burst_pressure_pa_abs,
            ambient_pressure_pa_abs=x.ambient_pressure_pa_abs))
    total=liquid["tnt_equivalent_mass_kg"]+vapor["tnt_equivalent_mass_kg"]
    ensure(math.isfinite(total),"Combined BLEVE TNT equivalent exceeds numerical domain","numerical_failure")
    return {"liquid_expansion_energy_j":liquid["liquid_expansion_energy_j"],"vapor_stored_energy_j":vapor["vapor_stored_energy_j"],
            "liquid_tnt_equivalent_mass_kg":liquid["tnt_equivalent_mass_kg"],"vapor_tnt_equivalent_mass_kg":vapor["tnt_equivalent_mass_kg"],
            **_targets(x,total)}


class NfntCase(Model):
    hole: Hole
    non_ignition_probability: Fraction
    physical_equipment_area_m2: NonNegative = 0
    physical_personnel_area_m2: NonNegative = 0
    bleve_equipment_area_m2: NonNegative = 0
    bleve_personnel_area_m2: NonNegative = 0
    steam_chemical_personnel_area_m2: NonNegative = 0


@calculation("consequence/level2-nfnt-case", "Level2 NFNT maximum areas and non-ignition weighting", NfntCase,
             ["Part3 eqs(3.198)-(3.199), §5.10.5; PDF p570"],
             limitations=["Inputs are event-conditional unweighted areas. Uses maximum, not sum, then applies non-ignition probability once. Physical/BLEVE areas must be zero for non-rupture holes. Steam/chemical area can be supplied by Level1 NFNT calculation. This does not infer event-tree probabilities."])
def nfnt_case(x):
    ensure(x.hole == "rupture" or not any((x.physical_equipment_area_m2,x.physical_personnel_area_m2,
        x.bleve_equipment_area_m2,x.bleve_personnel_area_m2)),"Physical/BLEVE areas must be zero outside rupture case")
    equipment=max(x.physical_equipment_area_m2,x.bleve_equipment_area_m2)
    personnel=max(x.physical_personnel_area_m2,x.bleve_personnel_area_m2,x.steam_chemical_personnel_area_m2)
    return {"equipment_area_m2":x.non_ignition_probability*equipment,"personnel_area_m2":x.non_ignition_probability*personnel}


class NfntFrequencyCase(NfntCase):
    generic_frequency_per_year: NonNegative


class NfntSummary(Model):
    cases: list[NfntFrequencyCase] = Field(min_length=4,max_length=4)


@calculation("consequence/level2-nfnt-summary", "Four-hole Level2 NFNT GFF-weighted final areas", NfntSummary,
             ["Part3 eqs(3.198)-(3.201); PDF p570"],
             origin="api581_nfnt_four_hole_composition",
             limitations=["Requires small,medium,large,rupture once each, including zero-frequency holes. Weights per-case non-ignition-adjusted maximum areas by supplied generic frequencies, not DF-adjusted failure frequencies. No annual risk or financial consequence is computed by this area average."])
def nfnt_summary(x):
    ensure({c.hole for c in x.cases} == {"small","medium","large","rupture"},"Require four distinct canonical hole sizes")
    total=math.fsum(c.generic_frequency_per_year for c in x.cases)
    ensure(math.isfinite(total) and total > 0,"Total generic frequency must be finite and positive")
    areas={c.hole:nfnt_case(NfntCase(**c.model_dump(exclude={"generic_frequency_per_year"}))) for c in x.cases}
    return {"total_generic_frequency_per_year":total,
            "equipment_area_m2":math.fsum(c.generic_frequency_per_year/total*areas[c.hole]["equipment_area_m2"] for c in x.cases),
            "personnel_area_m2":math.fsum(c.generic_frequency_per_year/total*areas[c.hole]["personnel_area_m2"] for c in x.cases),
            "by_hole_equipment_area_m2":{h:v["equipment_area_m2"] for h,v in areas.items()},
            "by_hole_personnel_area_m2":{h:v["personnel_area_m2"] for h,v in areas.items()}}
