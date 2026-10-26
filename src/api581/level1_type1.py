"""Type1 SI flammable tables; no Type0 continuous/instantaneous or AIT blending."""
from typing import Literal
from .core import Model, NonNegative, Fraction, calculation, ensure
from .level1 import Coefficients, coefficients, Energy, energy, ControlledRelease, controlled_release

Type1Fluid = Literal["Aromatics","Styrene","CO","DEE","Methanol","PO","EEA","EE","EG","EO"]

# (continuous AINL, continuous AIL, instantaneous AINL, instantaneous AIL),
# first equipment then personnel. None is a blank; (0,b) is a real zero.
TYPE1_COEFFICIENTS = {
    "Aromatics":{
        "gas":[(3.952,1.097),(80.11,1.055),(1.804,.667),(83.68,.713), (12.76,.963),(261.9,.937),(2.889,.686),(83.68,.713)],
        "liquid":[(21.10,1),None,(14.36,1),(143.6,1), (66.01,.883),(56,.268),(.027,.935),(.273,.935)]},
    "CO":{"gas":[(.040,1.752),None,(10.97,.667),None, (5.491,.991),None,(16.91,.692),None]},
    "DEE":{
        "gas":[(9.072,1.134),(67.42,1.033),(24.51,.667),None, (26.76,1.025),(241.5,.997),(31.71,.682),(128.3,.657)],
        "liquid":[(164.2,1.106),(976,.649),(.981,.919),(1.090,.919), (236.7,1.219),(488.9,.864),(8.333,.814),(9.258,.814)]},
    "Methanol":{
        "gas":[(.005,.909),None,(4.425,.667),None, (0,1.008),None,(6.035,.688),None],
        "liquid":[(340.4,.934),None,(.363,.900),None, (849.9,.902),None,(1.157,.871),None]},
    "PO":{
        "gas":[(3.277,1.114),None,(10.32,.667),None, (8.239,1.047),None,(13.33,.682),None],
        "liquid":[(257,.960),None,(.629,.869),None, (352.8,.840),None,(2.732,.834),None]},
    "EEA":{
        "gas":[(0,1.035),None,(1.261,.667),None, (0,.946),None,(1.825,.687),None],
        "liquid":[(23.96,1),None,(14.13,1),None, (79.66,.835),None,(.030,.924),None]},
    "EE":{
        "gas":[(2.595,1.005),None,(6.119,.667),None, (7.107,.969),None,(25.36,.660),None],
        "liquid":[(35.45,1),None,(14.79,1),None, (8.142,.800),None,(.029,.927),None]},
    "EG":{
        "gas":[(1.548,.973),None,(1.027,.667),None, (5.042,.947),None,(1.435,.687),None],
        "liquid":[(22.12,1),None,(14.13,1),None, (59.96,.869),None,(.027,.922),None]},
    "EO":{"gas":[(6.712,1.069),None,(21.46,.667),None, (11,1.105),None,(34.70,.665),None]},
}
TYPE1_COEFFICIENTS["Styrene"] = {phase:list(rows) for phase,rows in TYPE1_COEFFICIENTS["Aromatics"].items()}


class Type1Area(Coefficients):
    fluid: Type1Fluid
    adjusted_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    mitigation_fraction: Fraction


@calculation("level1/type1-flammable-area", "Type1 single-effect flammable consequence area", Type1Area,
             ["Part 3 §4.1.5(b),§4.8.4,§4.8.8; Tables4.8M,4.9M; PDF pp484,492,522,524"],
             limitations=["Ten Type1 flammable fluids. Caller selects phase, release type and AINL/AIL branch; no Type0 IC or AIT blending. Instantaneous energy correction follows STEP8.2 and §4.8.4. Blank cells are rejected, printed zero retained. Equipment/personnel are callable separately when only one source cell exists."])
def type1_area(x):
    ensure(x.fluid in TYPE1_COEFFICIENTS,"Not a supported Type1 flammable reference fluid")
    cell = coefficients(Coefficients(**{k:getattr(x,k) for k in ("fluid","release_phase","effect","release_type","autoignition")}))
    correction = energy(Energy(released_mass_kg=x.released_mass_kg))["energy_efficiency_factor"] if x.release_type == "instantaneous" else 1
    magnitude = x.adjusted_rate_kg_s if x.release_type == "continuous" else x.released_mass_kg
    return {"area_m2":cell["a"]*magnitude**cell["b"]*(1-x.mitigation_fraction)/correction,
            "coefficient_a":cell["a"],"coefficient_b":cell["b"],"energy_efficiency_factor":correction}


class Type1Consequence(Model):
    fluid: Type1Fluid
    release_phase: Literal["gas","liquid"]
    release_type: Literal["continuous","instantaneous"]
    autoignition: Literal["not_likely","likely"]
    adjusted_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    mitigation_fraction: Fraction


@calculation("level1/type1-flammable-consequence", "Type1 equipment and personnel flammable areas", Type1Consequence,
             ["Part 3 §4.1.5(b),§4.8.8; Tables4.8M,4.9M"],
             limitations=["Unblended Type1 branch selected explicitly by caller. Requires populated equipment and personnel cells; use type1-flammable-area to query just one effect. Energy/mitigation applied once; coefficients already incorporate event probabilities."])
def type1_consequence(x):
    values = {effect:type1_area(Type1Area(effect=effect,**x.model_dump())) for effect in ("equipment","personnel")}
    return {"equipment_area_m2":values["equipment"]["area_m2"],"personnel_area_m2":values["personnel"]["area_m2"],
            "energy_efficiency_factor":values["equipment"]["energy_efficiency_factor"],"fluid_type":1}


class ReleaseToType1(ControlledRelease):
    fluid: Type1Fluid
    final_release_phase: Literal["gas","liquid"]
    autoignition: Literal["not_likely","likely"]
    mitigation_fraction: Fraction


@calculation("level1/release-to-type1-flammable", "Compose controlled release and Type1 flammable consequence", ReleaseToType1,
             ["Part 3 §§4.3-4.8; §4.1.5(b)"],
             limitations=["Single qualified hole. Uses gas/liquid source, inventory and detection/isolation duration; Type1 phase/AIT branch is caller-qualified. No Type0 blending. Toxic/financial/other-hole aggregation remain separate composable functions."])
def release_to_type1(x):
    released = controlled_release(x)
    consequence = type1_consequence(Type1Consequence(fluid=x.fluid,release_phase=x.final_release_phase,
        release_type=released["release_type"],autoignition=x.autoignition,adjusted_rate_kg_s=released["adjusted_rate_kg_s"],
        released_mass_kg=released["released_mass_kg"],mitigation_fraction=x.mitigation_fraction))
    return {**released,**consequence}
