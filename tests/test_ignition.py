"""Printed coefficients, explicit reference choices and complete figure paths."""
import math
from decimal import Decimal, localcontext
import pytest
from api581 import DomainError
from api581.api import release, events, level2


def decimal_ambient(phase,rate,temperature):
    rows={"liquid":['-.1368924','-.007598764','8.282163e-6','-6.124231e-9','.06876128','1.193736e-4','2.081034e-7','-4.057289e-11'],
          "vapor":['-.06053124','-.009958413','1.518603e-5','-1.386705e-8','.04564953','7.912392e-4','-6.489157e-7','7.159409e-10']}
    with localcontext() as context:
        context.prec=70
        t=Decimal('1.8')*Decimal(str(temperature))
        c=list(map(Decimal,rows[phase]))
        a=sum(c[i]*t**i for i in range(4))
        b=sum(c[4+i]*t**i for i in range(4))
        return float((a+b*(Decimal('2.205')*Decimal(str(min(rate,25.2)))).ln()).exp())


def test_flammable_phase_rates_are_not_rainout_rates():
    r=release.flammable_phase_rates(release.FlammablePhaseRatesInput(adjusted_mass_rate_kg_s=10,
        flammable_mass_fraction=.8,flash_mass_fraction=.25)).outputs
    assert r.flammable_rate_kg_s == 8 and r.flammable_vapor_rate_kg_s == 2 and r.flammable_liquid_rate_kg_s == 6


@pytest.mark.parametrize("phase",["liquid","vapor"])
@pytest.mark.parametrize("rate",[.01,1,25.2,100])
def test_ambient_ignition_matches_independent_high_precision_source_sum(phase,rate):
    r=events.ambient_ignition(events.AmbientIgnitionInput(phase=phase,flammable_rate_kg_s=rate,
        flash_point_temperature_k=300,correlation_basis_source="Printed source numerical fixture")).outputs
    assert r.ambient_ignition_probability == pytest.approx(decimal_ambient(phase,rate,300),rel=1e-13)
    assert r.rate_capped == (rate > 25.2)
    assert r.evaluated_rate_kg_s == min(rate,25.2)


def test_zero_rate_and_nonphysical_extrapolation_are_distinct():
    r=events.ambient_ignition(events.AmbientIgnitionInput(phase="vapor",flammable_rate_kg_s=0,
        flash_point_temperature_k=300,correlation_basis_source="Zero source fixture")).outputs
    assert r.ambient_ignition_probability == 0
    with pytest.raises(DomainError):
        events.ambient_ignition(events.AmbientIgnitionInput(phase="liquid",flammable_rate_kg_s=25.2,
            flash_point_temperature_k=1,correlation_basis_source="Nonphysical extrapolation fixture"))


@pytest.mark.parametrize("phase,mw,expected",[("liquid",None,1),("vapor",2,.9),("vapor",86,.8),("vapor",170,.7),("vapor",500,.7)])
def test_ait_maximum_source_anchors(phase,mw,expected):
    r=events.ait_ignition_maximum(events.AitIgnitionMaximumInput(phase=phase,molecular_weight_kg_kmol=mw)).outputs
    assert r.maximum_ignition_probability == pytest.approx(expected)


def temperature(**updates):
    return events.ProbabilityTemperatureInput(**(dict(reference_basis="qualified_reference",qualified_reference_temperature_k=300,
        reference_source="Illustrative qualified reference",storage_temperature_k=400,autoignition_temperature_k=500,
        probability_at_reference=.2,probability_at_ait=.8)|updates))


def test_temperature_endpoints_interpolation_and_above_ait_limit():
    middle=events.probability_temperature(temperature()).outputs
    assert middle.probability == pytest.approx(.5) and middle.temperature_weight == .5
    assert events.probability_temperature(temperature(storage_temperature_k=300)).outputs.probability == .2
    assert events.probability_temperature(temperature(storage_temperature_k=700)).outputs.probability == .8


def test_literal_c16_and_qualified_reference_are_not_silently_equated():
    literal=events.probability_temperature(temperature(reference_basis="api581_printed_c16",qualified_reference_temperature_k=None,
        storage_temperature_k=300))
    qualified=events.probability_temperature(temperature(storage_temperature_k=300))
    assert literal.outputs.reference_temperature_k == 30.89
    assert literal.outputs.probability == pytest.approx(.2+.6*(300-30.89)/(500-30.89))
    assert qualified.outputs.probability == .2
    assert literal.input_hash != qualified.input_hash


@pytest.mark.parametrize("updates",[{"storage_temperature_k":200},{"autoignition_temperature_k":300},
    {"probability_at_ait":.1},{"reference_basis":"api581_printed_c16"},{"reference_source":" "}])
def test_unqualified_temperature_domains_rejected(updates):
    with pytest.raises(DomainError):
        events.probability_temperature(temperature(**updates))


@pytest.mark.parametrize("kind,phase,immediate,vce",[("continuous","liquid",.2,.25),("continuous","vapor",.5,.5),
    ("instantaneous","liquid",.2,.125),("instantaneous","vapor",.1,.25)])
def test_all_table53_rows(kind,phase,immediate,vce):
    r=events.conditional_table(events.ConditionalTableInput(phase=phase,release_type=kind)).outputs
    assert r.immediate_at_reference == immediate and r.immediate_at_ait == 1
    assert r.vce_given_delayed == vce and r.flash_given_delayed == 1-vce


def test_two_phase_probability_bases_preserve_printed_liquid_flash_weight():
    values=dict(liquid_probability=.2,vapor_probability=.8,flash_mass_fraction=.25,weighting_source="Explicit weighting fixture")
    literal=events.two_phase_probability(events.TwoPhaseProbabilityInput(**values,mixing_basis="api581_printed_liquid_weight"))
    vapor=events.two_phase_probability(events.TwoPhaseProbabilityInput(**values,mixing_basis="qualified_vapor_weight"))
    assert literal.outputs.probability == pytest.approx(.65)
    assert vapor.outputs.probability == pytest.approx(.35)
    assert literal.input_hash != vapor.input_hash


@pytest.mark.parametrize("phase,kind,case,fire",[("liquid","continuous","leakage","pool_fire"),
    ("vapor","continuous","leakage","jet_fire"),("liquid","instantaneous","leakage","pool_fire"),
    ("vapor","instantaneous","leakage","fireball"),("liquid","instantaneous","rupture","pool_fire"),
    ("vapor","instantaneous","rupture","fireball")])
def test_figure_paths_are_exhaustive_and_vce_uses_correct_conditional_factor(phase,kind,case,fire):
    r=events.single_phase_tree(events.SinglePhaseTreeInput(phase=phase,release_type=kind,case_type=case,
        ignition_probability=.4,immediate_given_ignition=.3,vce_given_delayed=.25,
        branch_probability_source="Qualified conditional branch fixture")).outputs
    assert r.terminal_probabilities[fire] == pytest.approx(.12)
    assert r.terminal_probabilities["vce"] == pytest.approx(.07)
    assert r.terminal_probabilities["flash_fire"] == pytest.approx(.21)
    assert r.non_ignition_probability == .6 and r.probability_sum == pytest.approx(1)


def test_figure53_instantaneous_leakage_fireball_requires_explicit_area_basis():
    tree=events.single_phase_tree(events.SinglePhaseTreeInput(phase="vapor",release_type="instantaneous",case_type="leakage",
        ignition_probability=.4,immediate_given_ignition=.3,vce_given_delayed=.25,branch_probability_source="Figure5.3 fixture")).outputs
    data=dict(hole="small",release_type="instantaneous",non_ignition_probability=tree.non_ignition_probability,
        event_tree_source="Explicit Figure5.3 selection",consequence_source="Illustrative raw area fixture",
        outcomes=[level2.FlammableOutcomeInput(event=event,probability=p,equipment_area_m2=100 if p else 0,
            personnel_area_m2=100 if p else 0) for event,p in tree.terminal_probabilities.items()])
    with pytest.raises(DomainError):
        level2.flammable_case(level2.FlammableCaseInput(**data))
    selected=level2.flammable_case(level2.FlammableCaseInput(**data,fireball_applicability_basis=tree.fireball_applicability_basis))
    assert selected.outputs.flammable_personnel_area_m2 == pytest.approx(40)


def ignition(**updates):
    return events.SinglePhaseIgnitionInput(**(dict(phase="vapor",release_type="continuous",case_type="leakage",
        flammable_rate_kg_s=2,flash_point_temperature_k=300,correlation_basis_source="Qualified illustrative flash point",
        molecular_weight_kg_kmol=44,reference_basis="qualified_reference",qualified_reference_temperature_k=300,
        reference_source="Qualified reference fixture",storage_temperature_k=400,autoignition_temperature_k=600)|updates))


def test_composite_reconstructs_source_ignition_and_terminal_paths():
    r=events.single_phase_ignition(ignition()).outputs
    base=decimal_ambient("vapor",2,300)
    peak=.7+.2*(170-44)/168
    expected=base+(peak-base)/3
    assert r.ignition_probability == pytest.approx(expected)
    assert r.immediate_given_ignition == pytest.approx(2/3)
    assert r.terminal_probabilities["jet_fire"] == pytest.approx(expected*2/3)
    assert r.terminal_probabilities["vce"] == pytest.approx(expected/3*.5)
    assert r.non_ignition_probability == pytest.approx(1-expected)


def test_zero_source_does_not_ignite_above_ait():
    r=events.single_phase_ignition(ignition(flammable_rate_kg_s=0,storage_temperature_k=700)).outputs
    assert r.ignition_probability == 0 and r.non_ignition_probability == 1
    assert all(value == 0 for value in r.terminal_probabilities.values())


def test_continuous_rupture_tree_not_silently_assumed():
    with pytest.raises(DomainError):
        events.single_phase_ignition(ignition(case_type="rupture"))
