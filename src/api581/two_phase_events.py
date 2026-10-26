"""Explicit two-phase probability weighting and correlated figure event paths."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .ignition import (TemperatureReference, SinglePhaseIgnition, single_phase_ignition,
    TwoPhaseProbability, two_phase_probability, FlammableRates, flammable_rates)


class FireballConditional(Model):
    phase: Literal["liquid","vapor","two_phase"]
    release_type: Literal["continuous","instantaneous"]
    case_type: Literal["leakage","rupture"]
    applicability_basis: Literal["rupture_only_text","figure53_instantaneous"]


@calculation("events/fireball-given-immediate", "Fireball conditional applicability from text or figure basis", FireballConditional,
             ["Part3 eqs(3.123)-(3.124),Figure5.3; PDF pp549,586"],
             origin="api581_fireball_conditional_with_explicit_applicability",
             limitations=["Conditional on immediate ignition. Text basis requires instantaneous rupture of vapor/two-phase; explicit figure53 basis also allows instantaneous leakage. Liquid and continuous cases give0. Correlation does not establish thermal-model applicability or certify leakage fireballs."])
def fireball_given_immediate(x):
    allowed=(x.phase in {"vapor","two_phase"} and x.release_type == "instantaneous" and (
        x.case_type == "rupture" or x.applicability_basis == "figure53_instantaneous"))
    return {"fireball_given_immediate":1 if allowed else 0}


class TwoPhaseContext(Model):
    release_type: Literal["continuous","instantaneous"]
    case_type: Literal["leakage","rupture"]
    qualified_rupture_fireball_fraction: Fraction | None = None
    rupture_fireball_source: str | None = Field(default=None,min_length=1,max_length=1000)


class TwoPhaseTree(TwoPhaseContext):
    ignition_probability: Fraction
    immediate_given_ignition: Fraction
    vce_given_delayed: Fraction
    branch_probability_source: str = Field(min_length=1,max_length=1000)


@calculation("events/two-phase-tree", "Two-phase figure paths including one correlated jet/pool event", TwoPhaseTree,
             ["Part3 Figures5.3/5.4,eqs(3.123)-(3.126); PDF pp549,586-587"],
             origin="api581_two_phase_printed_figure_event_tree",
             limitations=["Continuous leakage immediate branch is one jet_pool_max terminal, not independent jet and pool fires. Instantaneous leakage immediate branch is fireball per figure53 despite text conflict. Rupture instantaneous immediate fireball fraction defaults1 per eq3.123; figure54 alternative requires explicit fraction/source, remaining immediate probability goes to pool. Continuous rupture unsupported. Non-ignition still requires toxic/NFNT analysis."])
def two_phase_tree(x):
    ensure(x.branch_probability_source.strip(),"Branch probability source must be nonblank")
    ensure(x.case_type != "rupture" or x.release_type == "instantaneous","Continuous rupture tree unsupported")
    ensure((x.qualified_rupture_fireball_fraction is None) == (x.rupture_fireball_source is None),
           "Qualified rupture fireball fraction and source must be supplied together")
    if x.qualified_rupture_fireball_fraction is not None:
        ensure(x.case_type == "rupture" and x.rupture_fireball_source.strip(),"Fireball fraction override only for qualified rupture branch")
    basis="figure53_instantaneous" if x.case_type == "leakage" and x.release_type == "instantaneous" else "rupture_only_text"
    conditional=fireball_given_immediate(FireballConditional(phase="two_phase",release_type=x.release_type,
        case_type=x.case_type,applicability_basis=basis))["fireball_given_immediate"]
    if x.qualified_rupture_fireball_fraction is not None:
        conditional=x.qualified_rupture_fireball_fraction
    pi,immediate,vce=x.ignition_probability,x.immediate_given_ignition,x.vce_given_delayed
    probabilities={event:0.0 for event in ["pool_fire","jet_fire","fireball","vce","flash_fire","jet_pool_max"]}
    if x.release_type == "continuous":
        probabilities["jet_pool_max"]=pi*immediate
    else:
        probabilities["fireball"]=pi*immediate*conditional
        probabilities["pool_fire"]=pi*immediate*(1-conditional)
    probabilities["vce"]=pi*(1-immediate)*vce
    probabilities["flash_fire"]=pi*(1-immediate)*(1-vce)
    nonignition=1-pi
    return {"terminal_probabilities":probabilities,"non_ignition_probability":nonignition,
            "probability_sum":math.fsum([*probabilities.values(),nonignition]),"fireball_given_immediate":conditional,
            "fireball_probability_basis":"api581_eq3_123_124" if x.qualified_rupture_fireball_fraction is None else "qualified_figure54_branch",
            "fireball_applicability_basis":basis}


class TwoPhaseIgnition(TwoPhaseContext,TemperatureReference):
    adjusted_mass_rate_kg_s: NonNegative
    flammable_mass_fraction: Fraction
    flash_mass_fraction: Fraction
    liquid_flash_point_temperature_k: Positive
    vapor_flash_point_temperature_k: Positive
    vapor_molecular_weight_kg_kmol: Positive
    storage_temperature_k: Positive
    autoignition_temperature_k: Positive
    correlation_basis_source: str = Field(min_length=1,max_length=1000)
    mixing_basis: Literal["api581_printed_liquid_weight","qualified_vapor_weight"]
    weighting_source: str = Field(min_length=1,max_length=1000)


@calculation("events/two-phase-ignition", "Phase rates and ignition correlations to two-phase terminal paths", TwoPhaseIgnition,
             ["Part3 eqs(3.106)-(3.124),Table5.3,Figures5.3/5.4; PDF pp546-549,583,586-587"],
             origin="api581_two_phase_ignition_composition_with_explicit_bases",
             limitations=["Requires strictly mixed atmospheric flash fraction0<f<1; endpoints belong to single-phase model. Composes phase-specific flammable rates, flash points, vapor MW, common qualified AIT/reference, Table5.3 and explicit phase weighting. Printed liquid-weight basis is preserved as source interpretation, not validated physical phase weighting. Zero fuel gives zero ignition. No EOS, two-phase hydraulics, effect footprints or LH2 validation; correlated jet_pool_max must remain one area branch."])
def two_phase_ignition(x):
    ensure(0 < x.flash_mass_fraction < 1,"Two-phase ignition requires0<flash fraction<1; use single-phase at endpoints")
    rates=flammable_rates(FlammableRates(adjusted_mass_rate_kg_s=x.adjusted_mass_rate_kg_s,
        flammable_mass_fraction=x.flammable_mass_fraction,flash_mass_fraction=x.flash_mass_fraction))
    setup=x.model_dump(include=set(TemperatureReference.model_fields))
    setup.update(release_type=x.release_type,case_type=x.case_type,storage_temperature_k=x.storage_temperature_k,
        autoignition_temperature_k=x.autoignition_temperature_k,correlation_basis_source=x.correlation_basis_source)
    phase_results={}
    for phase in ["liquid","vapor"]:
        rate=rates[f"flammable_{phase}_rate_kg_s"]
        ensure(rate > 0 or rates["flammable_rate_kg_s"] == 0,"Positive phase fuel rate underflow","numerical_failure")
        phase_results[phase]=single_phase_ignition(SinglePhaseIgnition(**setup,phase=phase,flammable_rate_kg_s=rate,
            flash_point_temperature_k=x.liquid_flash_point_temperature_k if phase == "liquid" else x.vapor_flash_point_temperature_k,
            molecular_weight_kg_kmol=x.vapor_molecular_weight_kg_kmol if phase == "vapor" else None))
    def mix(field):
        return two_phase_probability(TwoPhaseProbability(liquid_probability=phase_results["liquid"][field],
            vapor_probability=phase_results["vapor"][field],flash_mass_fraction=x.flash_mass_fraction,
            mixing_basis=x.mixing_basis,weighting_source=x.weighting_source))["probability"]
    ignition,immediate,vce=mix("ignition_probability"),mix("immediate_given_ignition"),mix("vce_given_delayed")
    tree=two_phase_tree(TwoPhaseTree(**x.model_dump(include=set(TwoPhaseContext.model_fields)),
        ignition_probability=ignition,immediate_given_ignition=immediate,vce_given_delayed=vce,
        branch_probability_source="Composed phase correlations/Table5.3 and explicit mixing basis"))
    return {**tree,**rates,"ignition_probability":ignition,"immediate_given_ignition":immediate,
            "vce_given_delayed":vce,"flash_given_delayed":1-vce,"mixing_basis":x.mixing_basis,
            "liquid_ignition_probability":phase_results["liquid"]["ignition_probability"],
            "vapor_ignition_probability":phase_results["vapor"]["ignition_probability"],
            "liquid_immediate_given_ignition":phase_results["liquid"]["immediate_given_ignition"],
            "vapor_immediate_given_ignition":phase_results["vapor"]["immediate_given_ignition"],
            "reference_temperature_k":phase_results["liquid"]["reference_temperature_k"],
            "temperature_weight":phase_results["liquid"]["temperature_weight"]}
