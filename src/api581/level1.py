"""Level 1 release controls and flammable-area tables, explicitly bounded by support."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure
from .release import Gas, Liquid, gas, liquid, AvailableInventory, inventory, ReleaseType, release_type, ReleaseMagnitude, magnitude
from .consequences import Acid, acid, Steam, steam
from .level1_toxic import ToxicComponent, MitigationCredits, toxic_component

# Four (a,b) pairs in order: continuous AINL, continuous AIL, instantaneous AINL, instantaneous AIL.
# SI Tables 4.8M / 4.9M, PDF pp522,524. None represents a blank, never zero.
COEFFICIENTS = {
    "C1-C2": {"gas": [(8.669,.98),(55.13,.95),(6.469,.67),(163.7,.62), (21.83,.96),(143.2,.92),(12.46,.67),(473.9,.63)]},
    "C3-C4": {"gas": [(10.13,1),(64.23,1),(4.590,.72),(79.94,.63), (25.64,1),(171.4,1),(9.702,.75),(270.4,.63)]},
    "C5": {"gas": [(5.115,.99),(62.41,1),(2.214,.73),(41.38,.61), (12.71,1),(166.1,1),(4.820,.76),(146.7,.63)],
           "liquid": [(100.6,.89),None,(.271,.85),None, (290.1,.89),None,(.790,.85),None]},
    "C6-C8": {"gas": [(5.846,.98),(63.98,1),(2.188,.66),(41.49,.61), (13.49,.96),(169.7,1),(4.216,.67),(147.2,.63)],
              "liquid": [(34.17,.89),(103.4,.95),(.749,.78),(8.180,.55), (96.88,.89),(252.8,.92),(2.186,.78),(31.89,.54)]},
    "C9-C12": {"gas": [(2.419,.98),(76.98,.95),(1.111,.66),(42.28,.61), (5.755,.96),(188.6,.92),(2.035,.66),(151.0,.63)],
               "liquid": [(24.60,.90),(110.3,.95),(.559,.76),(.848,.53), (70.03,.89),(269.4,.92),(1.609,.76),(2.847,.54)]},
    "C13-C16": {"liquid": [(12.11,.90),(196.7,.92),(.086,.88),(1.714,.88), (34.36,.89),(539.4,.90),(.242,.88),(4.843,.88)]},
    "C17-C25": {"liquid": [(3.785,.90),(165.5,.92),(.021,.91),(1.068,.91), (10.70,.89),(458.0,.90),(.061,.91),(3.052,.91)]},
    "C25+": {"liquid": [(2.098,.91),(103.0,.90),(.006,.99),(.284,.99), (6.196,.89),(303.6,.90),(.016,.99),(.833,.99)]},
    "H2": {"gas": [(13.13,.992),(86.02,1),(9.605,.657),(216.5,.618), (32.05,.933),(228.8,1),(18.43,.652),(636.5,.621)]},
    "H2S": {"gas": [(6.554,1),(38.11,.89),(22.63,.63),(53.72,.61), (10.65,1),(73.25,.94),(41.43,.63),(191.5,.63)]},
}
COEFFICIENTS["Pyrophoric"] = {phase:list(rows) for phase,rows in COEFFICIENTS["C9-C12"].items()}
COEFFICIENTS["HF"] = {"gas":[None]*8,"liquid":[None]*8}


class Coefficients(Model):
    fluid: str
    release_phase: Literal["gas", "liquid"]
    effect: Literal["equipment", "personnel"]
    release_type: Literal["continuous", "instantaneous"]
    autoignition: Literal["not_likely", "likely"]


@calculation("level1/flammable-coefficients", "SI flammable consequence coefficients", Coefficients,
             ["Part 3 Tables 4.8M, 4.9M; PDF pp522,524"],
             limitations=["Type0 and Type1 table lookup only; blank cells are unsupported while printed zero coefficients are valid. Coefficients include original event weighting; do not multiply ignition probability again. Type1 areas must use the separate unblended calculation."])
def coefficients(x):
    table = COEFFICIENTS
    if x.fluid not in table:
        from .level1_type1 import TYPE1_COEFFICIENTS
        table = TYPE1_COEFFICIENTS
    ensure(x.fluid in table and x.release_phase in table[x.fluid], "Unsupported reference fluid/phase")
    offset = (4 if x.effect == "personnel" else 0) + (2 if x.release_type == "instantaneous" else 0) + (1 if x.autoignition == "likely" else 0)
    cell = table[x.fluid][x.release_phase][offset]
    ensure(cell is not None, "Selected coefficient cell is blank in the source table", "unsupported_table_cell")
    return {"a": cell[0], "b": cell[1], "magnitude_unit": "kg/s" if x.release_type == "continuous" else "kg", "area_unit": "m2"}


class Detection(Model):
    detection: Literal["A", "B", "C"]
    isolation: Literal["A", "B", "C"]


@calculation("release/detection-reduction", "Detection/isolation reduction factor", Detection,
             ["Part 3 Table 4.6; PDF p519"], limitations=["All nine A/B/C detection-isolation combinations are represented explicitly from Table 4.6; ratings themselves remain qualified inputs."])
def detection_reduction(x):
    # Table 4.6 lists B/A with the same 10% reduction as B/C, and C with
    # any isolation rating as no adjustment.  Keep every printed cell
    # explicit rather than rejecting valid combinations as "unlisted".
    factors = {("A","A"):.25, ("A","B"):.20, ("A","C"):.10,
               ("B","A"):.10, ("B","B"):.15, ("B","C"):.10,
               ("C","A"):0., ("C","B"):0., ("C","C"):0.}
    return {"reduction_fraction": factors[x.detection,x.isolation]}


class LeakDuration(Detection):
    hole: Literal["small", "medium", "large"]


@calculation("release/detection-duration", "Detection/isolation maximum duration", LeakDuration,
             ["Part 3 Table 4.7; PDF p520"], limitations=["No rupture-duration entry in this table; returned duration is seconds."])
def detection_duration(x):
    if x.detection == "A":
        values = {"A": (20,10,5), "B": (30,20,10), "C": (40,30,20)}[x.isolation]
    elif x.detection == "B":
        values = (60,30,20) if x.isolation == "C" else (40,30,20)
    else:
        values = (60,40,20)
    return {"maximum_duration_s": values[("small","medium","large").index(x.hole)] * 60}


class FinalPhase(Model):
    stored_phase: Literal["gas", "liquid"]
    ambient_phase: Literal["gas", "liquid"]
    normal_boiling_point_k: Positive


@calculation("level1/release-phase", "Level 1 final consequence phase", FinalPhase,
             ["Part 3 Table 4.3; PDF p518"], limitations=["Level 1 approximation only; steam/acid overrides must be selected separately. No two-phase flash calculation."])
def final_phase(x):
    phase = "gas" if x.stored_phase == "gas" else ("liquid" if x.ambient_phase == "liquid" or x.normal_boiling_point_k > (80-32)*5/9+273.15 else "gas")
    return {"release_phase": phase}


class Energy(Model):
    released_mass_kg: NonNegative


@calculation("level1/energy-efficiency", "Instantaneous energy efficiency correction", Energy,
             ["Part 3 eq (3.18), Annex 3.B C4A"], limitations=["Applied to instantaneous-release area only; below 4536 kg the correction is 1."])
def energy(x):
    return {"energy_efficiency_factor": 4 * math.log10(2.205 * x.released_mass_kg) - 15 if x.released_mass_kg > 4536 else 1}


class Blending(Model):
    release_type: Literal["continuous", "instantaneous"]
    adjusted_rate_kg_s: NonNegative
    instantaneous_coefficients_available: bool
    operating_temperature_k: Positive
    autoignition_temperature_k: Positive


@calculation("level1/blending-factors", "Type 0 release/AIT blending factors", Blending,
             ["Part 3 eqs (3.19)-(3.26), Annex 3.B C5,C6"], limitations=["Type 0 fluids only. Type 1 correlations already incorporate smoothing."])
def blending(x):
    ic = (1 if x.release_type == "instantaneous" else min(x.adjusted_rate_kg_s / 25.2, 1)) if x.instantaneous_coefficients_available else 0
    ait = min(1, max(0, (x.operating_temperature_k - x.autoignition_temperature_k + 55.6) / (2 * 55.6)))
    return {"instantaneous_weight": ic, "autoignition_likely_weight": ait}


class Area(Model):
    fluid: str
    release_phase: Literal["gas", "liquid"]
    release_type: Literal["continuous", "instantaneous"]
    adjusted_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    operating_temperature_k: Positive
    autoignition_temperature_k: Positive
    mitigation_fraction: Fraction


@calculation("level1/flammable-area", "Type 0 per-hole blended flammable consequence", Area,
             ["Part 3 §4.8.8 eqs (3.29)-(3.58), Tables 4.8M/4.9M"],
             limitations=["Per-hole flammable consequence only; no toxic/NFNT/financial or hole-frequency weighting. Initial Type 0 set. Caller supplies final phase/AIT/mitigation; LH2 Level 2 behavior is not represented."])
def flammable_area(x):
    ensure(x.fluid in COEFFICIENTS and x.release_phase in COEFFICIENTS[x.fluid], "Unsupported fluid/phase")
    rows = COEFFICIENTS[x.fluid][x.release_phase]
    factors = blending(Blending(**{k:getattr(x,k) for k in ["release_type","adjusted_rate_kg_s","operating_temperature_k","autoignition_temperature_k"]}, instantaneous_coefficients_available=rows[2] is not None))
    ic, ait = factors["instantaneous_weight"], factors["autoignition_likely_weight"]
    correction = energy(Energy(released_mass_kg=x.released_mass_kg))["energy_efficiency_factor"]
    weights = [(1-ic)*(1-ait),(1-ic)*ait,ic*(1-ait),ic*ait]
    outputs = {}
    for effect, offset in [("equipment",0),("personnel",4)]:
        terms = []
        for i,w in enumerate(weights):
            if w == 0:
                terms.append(0)
                continue
            cell = rows[offset+i]
            ensure(cell is not None, f"Required {effect} coefficient cell is blank", "unsupported_table_cell")
            magnitude = x.adjusted_rate_kg_s if i < 2 else x.released_mass_kg
            terms.append(w * cell[0] * magnitude ** cell[1] / (correction if i >= 2 else 1) * (1-x.mitigation_fraction))
        outputs[effect+"_area_m2"] = math.fsum(terms)
    return {**outputs, **factors, "energy_efficiency_factor": correction}


class ControlledRelease(Model):
    source: Gas | Liquid
    operating_temperature_k: Positive
    component_mass_kg: NonNegative
    inventory_group_mass_kg: NonNegative
    detection: Literal["A", "B", "C"]
    isolation: Literal["A", "B", "C"]
    duration_hole: Literal["small", "medium", "large", "rupture"]
    rupture_maximum_duration_s: Positive | None = None


@calculation("release/controlled-scenario", "Per-hole source, inventory, detection/isolation and release magnitude", ControlledRelease,
             ["Part 3 §§4.3-4.7"],
             limitations=["Single qualified representative hole. Constant ideal-gas/incompressible-liquid source; caller supplies controls and inventory. Rupture duration must be explicit. Adjusted flammable rate is not the toxic source rate."])
def controlled_release(x):
    if x.duration_hole != "rupture":
        sizes = {"small":(.00635,.0064),"medium":(.025,.0254),"large":(.1016,.102)}[x.duration_hole]
        ensure(any(math.isclose(x.source.diameter_m,d,rel_tol=0,abs_tol=1e-9) for d in sizes),
               "Duration table category must match a standard representative hole diameter")
    if isinstance(x.source, Gas):
        ensure(x.source.temperature_k == x.operating_temperature_k, "Gas source and operating temperatures must match")
    calculator = gas if isinstance(x.source, Gas) else liquid
    flow = calculator(x.source)
    eight_inch = x.source.model_copy(update={"diameter_m": math.sqrt(4*.03245/math.pi)})
    maximum_supply = calculator(eight_inch)["mass_rate_kg_s"]
    mass = inventory(AvailableInventory(component_mass_kg=x.component_mass_kg,inventory_group_mass_kg=x.inventory_group_mass_kg,
                     release_rate_kg_s=flow["mass_rate_kg_s"],eight_inch_rate_kg_s=maximum_supply))
    kind = release_type(ReleaseType(diameter_m=x.source.diameter_m,theoretical_rate_kg_s=flow["mass_rate_kg_s"],available_mass_kg=mass["available_mass_kg"]))
    controls = detection_reduction(Detection(detection=x.detection,isolation=x.isolation))
    if x.duration_hole == "rupture":
        ensure(x.rupture_maximum_duration_s is not None,"Rupture maximum duration must be explicitly supplied")
        duration = x.rupture_maximum_duration_s
    else:
        ensure(x.rupture_maximum_duration_s is None,"Rupture duration is only valid for rupture")
        duration = detection_duration(LeakDuration(detection=x.detection,isolation=x.isolation,hole=x.duration_hole))["maximum_duration_s"]
    released = magnitude(ReleaseMagnitude(theoretical_rate_kg_s=flow["mass_rate_kg_s"],reduction_fraction=controls["reduction_fraction"],
                          available_mass_kg=mass["available_mass_kg"],maximum_duration_s=duration))
    return {"theoretical_rate_kg_s":flow["mass_rate_kg_s"],"available_mass_kg":mass["available_mass_kg"],
            "release_type":kind["release_type"],"reduction_fraction":controls["reduction_fraction"],
            "maximum_duration_s":duration,**released}


class ReleaseToFlammable(ControlledRelease):
    fluid: str
    final_release_phase: Literal["gas", "liquid"]
    autoignition_temperature_k: Positive
    mitigation_fraction: Fraction


@calculation("level1/release-to-flammable", "Compose source, inventory, controls and per-hole flammable area", ReleaseToFlammable,
             ["Part 3 §§4.3-4.8"],
             limitations=["Type0 only, single selected hole; caller selects fluid, phase, AIT and mitigation. No toxic/NFNT/cost assessment. Rupture duration must be explicit; Type1 uses release-to-type1-flammable."])
def release_to_flammable(x):
    released = controlled_release(x)
    consequence = flammable_area(Area(fluid=x.fluid,release_phase=x.final_release_phase,release_type=released["release_type"],
                                  adjusted_rate_kg_s=released["adjusted_rate_kg_s"],released_mass_kg=released["released_mass_kg"],
                                  operating_temperature_k=x.operating_temperature_k,autoignition_temperature_k=x.autoignition_temperature_k,
                                  mitigation_fraction=x.mitigation_fraction))
    return {**released,**consequence}


class ReleaseToAcid(ControlledRelease):
    differential_pressure_pa: NonNegative


@calculation(
    "level1/release-to-acid",
    "Compose controlled release and ACID splash consequence",
    ReleaseToAcid,
    ["Part 3 §§4.1.3,4.3-4.7,4.10.3; PDF pp483-484,490,502"],
    limitations=[
        "ACID representative-fluid route only. The caller must qualify the nonflammable/nontoxic acid-or-caustic selection and the differential pressure. The splash correlation is valid only for the documented 103.4-413.7 kPa range; no toxic, flammable or Level 2 dispersion consequence is inferred."
    ],
)
def release_to_acid(x):
    released = controlled_release(x)
    consequence = acid(
        Acid(
            adjusted_rate_kg_s=released["adjusted_rate_kg_s"],
            differential_pressure_pa=x.differential_pressure_pa,
        )
    )
    return {**released, **consequence, "representative_fluid": "Acid", "release_phase": "liquid"}


class ReleaseToSteam(ControlledRelease):
    """Controlled steam release routed to the Level 1 steam correlation."""
    pass


@calculation(
    "level1/release-to-steam",
    "Compose controlled release and Level 1 steam consequence",
    ReleaseToSteam,
    ["Part 3 §§4.3-4.7,4.10.2; PDF pp485-490,501-502"],
    limitations=[
        "Steam NFNT correlation only. Steam is treated as gas/vapor; the source must be qualified as steam and the returned area is personnel-only with equipment area zero. No condensation, jet dispersion, two-phase flash or Level 2 consequence is inferred."
    ],
)
def release_to_steam(x):
    released = controlled_release(x)
    consequence = steam(
        Steam(
            adjusted_rate_kg_s=released["adjusted_rate_kg_s"],
            released_mass_kg=released["released_mass_kg"],
        )
    )
    return {**released, **consequence, "representative_fluid": "Steam", "release_phase": "gas"}


class ReleaseToToxic(ControlledRelease):
    fluid: Literal["hf", "h2s", "ammonia", "chlorine", "alcl3", "co", "hcl", "nitric_acid", "no2", "phosgene", "tdi", "ee", "eo", "po"]
    release_phase: Literal["gas", "liquid", "powder"]
    toxic_mass_fraction: Fraction
    nonignition_probability: Fraction
    mitigation: MitigationCredits = Field(default_factory=MitigationCredits)
    concentration_ppm_on_idlh_basis: NonNegative | None = None
    hf_instantaneous_intercept: float | None = None
    intercept_qualification: str | None = Field(default=None, min_length=1, max_length=1000)


@calculation(
    "level1/release-to-toxic",
    "Compose controlled release and Level 1 toxic consequence",
    ReleaseToToxic,
    ["Part 3 §§4.3-4.7,4.9; PDF pp485-500"],
    limitations=[
        "Uses the controlled source for one representative hole and passes the theoretical rate (not flammable-adjusted rate) to the toxic component calculation. Single toxic component only; mixture maximum, four-hole aggregation, dispersion and Level 2 source partition remain separate."
    ],
)
def release_to_toxic(x):
    released = controlled_release(x)
    toxic = toxic_component(
        ToxicComponent(
            fluid=x.fluid,
            release_phase=x.release_phase,
            release_type=released["release_type"],
            theoretical_rate_kg_s=released["theoretical_rate_kg_s"],
            released_mass_kg=released["released_mass_kg"],
            toxic_mass_fraction=x.toxic_mass_fraction,
            available_mass_kg=released["available_mass_kg"],
            detection_maximum_duration_s=released["maximum_duration_s"],
            nonignition_probability=x.nonignition_probability,
            mitigation=x.mitigation,
            concentration_ppm_on_idlh_basis=x.concentration_ppm_on_idlh_basis,
            hf_instantaneous_intercept=x.hf_instantaneous_intercept,
            intercept_qualification=x.intercept_qualification,
        )
    )
    return {**released, **toxic}
