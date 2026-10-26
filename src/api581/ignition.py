"""Level2 ignition correlations, explicit temperature reference, figure trees."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

Phase=Literal["liquid","vapor"]
ReleaseType=Literal["continuous","instantaneous"]
_COEFFICIENTS={
    "liquid":(-.1368924,-.007598764,8.282163e-6,-6.124231e-9,.06876128,1.193736e-4,2.081034e-7,-4.057289e-11),
    "vapor":(-.06053124,-.009958413,1.518603e-5,-1.386705e-8,.04564953,7.912392e-4,-6.489157e-7,7.159409e-10),
}
_TABLE={
    ("continuous","liquid"):(.2,.25), ("continuous","vapor"):(.5,.5),
    ("instantaneous","liquid"):(.2,.125), ("instantaneous","vapor"):(.1,.25),
}


class FlammableRates(Model):
    adjusted_mass_rate_kg_s: NonNegative
    flammable_mass_fraction: Fraction
    flash_mass_fraction: Fraction


@calculation("release/flammable-phase-rates", "Flammable total/liquid/vapor rates for ignition", FlammableRates,
             ["Part3 eqs(3.106)-(3.108); PDF p546"],
             limitations=["Flash fraction supplied by qualified thermodynamics. Phase liquid rate is not pool rainout rate; aerosol/rainout partition is separate. Flammable mass fraction, not mole fraction, multiplies total adjusted rate."])
def flammable_rates(x):
    total=x.adjusted_mass_rate_kg_s*x.flammable_mass_fraction
    vapor=total*x.flash_mass_fraction
    liquid=total*(1-x.flash_mass_fraction)
    ensure(total > 0 or x.adjusted_mass_rate_kg_s == 0 or x.flammable_mass_fraction == 0,
           "Positive flammable rate underflow","numerical_failure")
    ensure(vapor > 0 or total == 0 or x.flash_mass_fraction == 0,
           "Positive flammable vapor rate underflow","numerical_failure")
    ensure(liquid > 0 or total == 0 or x.flash_mass_fraction == 1,
           "Positive flammable liquid rate underflow","numerical_failure")
    return {"flammable_rate_kg_s":total,"flammable_vapor_rate_kg_s":vapor,"flammable_liquid_rate_kg_s":liquid}


class AmbientIgnition(Model):
    phase: Phase
    flammable_rate_kg_s: NonNegative
    flash_point_temperature_k: Positive
    correlation_basis_source: str = Field(min_length=1,max_length=1000)


@calculation("events/ambient-ignition", "Flash-point/rate ambient ignition correlation", AmbientIgnition,
             ["Part3 eqs(3.109)-(3.110),C4B/C5/C12; PDF pp546-547,647"],
             limitations=["Printed C12=1.8 converts Kelvin flash point to Rankine; C4B=2.205 converts capped kg/s to lb/s inside natural log. Uses C5=25.2kg/s even though adjacent text also says25.22. Fit range is not certified by accepting source text: requires positive rate exponent and probability<=1, rejects nonphysical extrapolation. Zero rate uses limiting probability0. No LH2 ignition validation."])
def ambient_ignition(x):
    ensure(x.correlation_basis_source.strip(),"Ignition correlation basis must be nonblank")
    t=1.8*x.flash_point_temperature_k
    c=_COEFFICIENTS[x.phase]
    a=((c[3]*t+c[2])*t+c[1])*t+c[0]
    b=((c[7]*t+c[6])*t+c[5])*t+c[4]
    ensure(math.isfinite(a) and math.isfinite(b) and b > 0,"Ignition polynomial outside finite increasing-rate domain")
    rate=min(25.2,x.flammable_rate_kg_s)
    if rate == 0:
        probability=0
    else:
        logp=a+b*(math.log(2.205)+math.log(rate))
        ensure(logp <= 0,"Ambient ignition correlation exceeds probability1; no implicit clamp")
        probability=math.exp(logp)
        ensure(probability > 0,"Ambient ignition probability underflow","numerical_failure")
    return {"ambient_ignition_probability":probability,"evaluated_rate_kg_s":rate,"rate_capped":x.flammable_rate_kg_s > 25.2}


class MaximumIgnition(Model):
    phase: Phase
    molecular_weight_kg_kmol: Positive | None = None


@calculation("events/ait-ignition-maximum", "Ignition probability at autoignition temperature", MaximumIgnition,
             ["Part3 eqs(3.111)-(3.112); PDF pp547-548"],
             limitations=["Liquid maximum1; vapor follows printed molecular-weight interpolation with lower floor.7. MW2 gives.9 and MW>=170 gives.7. This is a release ignition probability correlation, not deterministic autoignition physics or a hydrogen certification."])
def ignition_maximum(x):
    if x.phase == "liquid":
        return {"maximum_ignition_probability":1}
    ensure(x.molecular_weight_kg_kmol is not None,"Vapor maximum requires molecular weight")
    return {"maximum_ignition_probability":max(.7,.7+.2*(170-x.molecular_weight_kg_kmol)/168)}


class TemperatureReference(Model):
    reference_basis: Literal["api581_printed_c16","qualified_reference"]
    qualified_reference_temperature_k: Positive | None = None
    reference_source: str = Field(min_length=1,max_length=1000)


def _reference(x):
    ensure(x.reference_source.strip(),"Temperature reference source must be nonblank")
    ensure((x.reference_basis == "qualified_reference") == (x.qualified_reference_temperature_k is not None),
           "Provide temperature only for qualified_reference basis")
    return 30.89 if x.reference_basis == "api581_printed_c16" else x.qualified_reference_temperature_k


class TemperatureProbability(TemperatureReference):
    probability_at_reference: Fraction
    probability_at_ait: Fraction
    storage_temperature_k: Positive
    autoignition_temperature_k: Positive


@calculation("events/probability-temperature", "Reference-to-AIT probability interpolation", TemperatureProbability,
             ["Part3 eqs(3.113)-(3.114),(3.116)-(3.117),C16; PDF pp548,648"],
             origin="api581_interpolation_with_explicit_temperature_reference",
             limitations=["Printed C16=30.89K and US70R conflict with ambient-temperature discussion; no silent conversion to70F. Required basis chooses literal C16 or a caller-qualified reference. Ts below reference and AIT<=reference rejected; Ts>=AIT returns AIT limit. AIT probability must be at least reference probability. Qualified reference is not an authorized erratum."])
def temperature_probability(x):
    reference=_reference(x)
    ensure(x.autoignition_temperature_k > reference and x.storage_temperature_k >= reference,
           "Temperature interpolation requires AIT>reference and Ts>=reference")
    ensure(x.probability_at_ait >= x.probability_at_reference,"AIT maximum is below reference probability")
    weight=min(1,(x.storage_temperature_k-reference)/(x.autoignition_temperature_k-reference))
    probability=x.probability_at_ait if weight == 1 else x.probability_at_reference+(x.probability_at_ait-x.probability_at_reference)*weight
    return {"probability":probability,"temperature_weight":weight,"reference_temperature_k":reference}


class ConditionalTable(Model):
    phase: Phase
    release_type: ReleaseType


@calculation("events/conditional-table", "Table5.3 conditional event probabilities", ConditionalTable,
             ["Part3 Table5.3; PDF p583"],limitations=["Historical expert-opinion defaults by phase/release type. Immediate probability at reference, not automatically at current storage temperature. VCE and flash columns are conditional on delayed ignition, not unconditional outcomes."])
def conditional_table(x):
    immediate,vce=_TABLE[x.release_type,x.phase]
    return {"immediate_at_reference":immediate,"immediate_at_ait":1,"vce_given_delayed":vce,"flash_given_delayed":1-vce}


class TwoPhaseProbability(Model):
    liquid_probability: Fraction
    vapor_probability: Fraction
    flash_mass_fraction: Fraction
    mixing_basis: Literal["api581_printed_liquid_weight","qualified_vapor_weight"]
    weighting_source: str = Field(min_length=1,max_length=1000)


@calculation("events/two-phase-probability", "Explicit-basis liquid/vapor conditional probability mixing", TwoPhaseProbability,
             ["Part3 eqs(3.115),(3.118)-(3.119),(3.122); PDF pp548-549"],
             origin="api581_with_explicit_two_phase_probability_weight",
             limitations=["Printed equations weight LIQUID by flash fraction and VAPOR by its complement, despite flash-as-vapor wording. Literal and separately qualified vapor weighting are explicit alternatives; neither is silently selected or asserted as an erratum. Inputs must be probabilities of the same conditional quantity. No complete two-phase terminal tree or correlated max(jet,pool) consequence representation here."])
def two_phase_probability(x):
    ensure(x.weighting_source.strip(),"Two-phase probability weighting source must be nonblank")
    liquid_weight=x.flash_mass_fraction if x.mixing_basis == "api581_printed_liquid_weight" else 1-x.flash_mass_fraction
    return {"probability":liquid_weight*x.liquid_probability+(1-liquid_weight)*x.vapor_probability,"mixing_basis":x.mixing_basis}


class SinglePhaseTree(Model):
    phase: Phase
    release_type: ReleaseType
    case_type: Literal["leakage","rupture"]
    ignition_probability: Fraction
    immediate_given_ignition: Fraction
    vce_given_delayed: Fraction
    branch_probability_source: str = Field(min_length=1,max_length=1000)


@calculation("events/single-phase-tree", "Single-phase terminal paths from Figures5.3/5.4", SinglePhaseTree,
             ["Part3 Figures5.3/5.4; PDF pp586-587; conflicting example eq(3.125) PDF549"],
             origin="api581_printed_figure_event_tree",
             limitations=["Follows figure VCE path factor pvcedi, not conflicting printed example1-pvcedi. Figure5.3 labels instantaneous vapor leakage as fireball, although text restricts fireballs to rupture; output explicitly reports figure53_instantaneous applicability when needed. Rupture tree supported only for instantaneous release. Non-ignition is not automatically safe: toxic/NFNT must be evaluated separately."])
def single_phase_tree(x):
    ensure(x.branch_probability_source.strip(),"Branch probability source must be nonblank")
    ensure(x.case_type != "rupture" or x.release_type == "instantaneous","Continuous rupture tree not specified by this implementation")
    pi,immediate,vce=x.ignition_probability,x.immediate_given_ignition,x.vce_given_delayed
    probabilities={event:0.0 for event in ["pool_fire","jet_fire","fireball","vce","flash_fire"]}
    fire="pool_fire" if x.phase == "liquid" else "jet_fire" if x.release_type == "continuous" else "fireball"
    probabilities[fire]=pi*immediate
    probabilities["vce"]=pi*(1-immediate)*vce
    probabilities["flash_fire"]=pi*(1-immediate)*(1-vce)
    nonignition=1-pi
    return {"terminal_probabilities":probabilities,"non_ignition_probability":nonignition,
            "probability_sum":math.fsum([*probabilities.values(),nonignition]),
            "fireball_applicability_basis":"figure53_instantaneous" if x.case_type == "leakage" and fire == "fireball" else "rupture_only_text"}


class SinglePhaseIgnition(AmbientIgnition,TemperatureReference):
    release_type: ReleaseType
    case_type: Literal["leakage","rupture"]
    molecular_weight_kg_kmol: Positive | None = None
    storage_temperature_k: Positive
    autoignition_temperature_k: Positive


@calculation("events/single-phase-ignition", "Rate/flash-point/temperature to single-phase terminal probabilities", SinglePhaseIgnition,
             ["Part3 eqs(3.109)-(3.117),Table5.3,Figures5.3/5.4; PDF pp547-549,583,586-587"],
             origin="api581_single_phase_ignition_composition",
             limitations=["Composes supplied phase flammable rate and qualified flash point, printed or qualified temperature reference, AIT maximum and Table5.3. Does not infer release phase, flash properties, two-phase mixture or probability validation from process data. Zero source has zero ignition even above AIT. Figure/text fireball conflict is reported via applicability basis. Continuous rupture and below-reference temperature unsupported."])
def single_phase_ignition(x):
    ambient=ambient_ignition(AmbientIgnition(**x.model_dump(include=set(AmbientIgnition.model_fields))))
    maximum=ignition_maximum(MaximumIgnition(phase=x.phase,molecular_weight_kg_kmol=x.molecular_weight_kg_kmol))
    reference=x.model_dump(include=set(TemperatureReference.model_fields))
    setup=dict(**reference,storage_temperature_k=x.storage_temperature_k,autoignition_temperature_k=x.autoignition_temperature_k)
    corrected=temperature_probability(TemperatureProbability(**setup,probability_at_reference=ambient["ambient_ignition_probability"],
        probability_at_ait=maximum["maximum_ignition_probability"]))
    table=conditional_table(ConditionalTable(phase=x.phase,release_type=x.release_type))
    immediate=temperature_probability(TemperatureProbability(**setup,probability_at_reference=table["immediate_at_reference"],probability_at_ait=1))["probability"]
    pi=corrected["probability"] if x.flammable_rate_kg_s > 0 else 0
    tree=single_phase_tree(SinglePhaseTree(phase=x.phase,release_type=x.release_type,case_type=x.case_type,
        ignition_probability=pi,immediate_given_ignition=immediate,vce_given_delayed=table["vce_given_delayed"],
        branch_probability_source="Composed source correlations/Table5.3 with explicit reference basis"))
    return {**ambient,**maximum,**tree,"ignition_probability":pi,"immediate_given_ignition":immediate,
            "vce_given_delayed":table["vce_given_delayed"],"flash_given_delayed":table["flash_given_delayed"],
            "reference_temperature_k":corrected["reference_temperature_k"],"temperature_weight":corrected["temperature_weight"]}
