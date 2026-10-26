"""Correlated event paths, no double counting and complete two-phase assessment."""
import math
import pytest
from api581 import DomainError
from api581.api import events, level2, release


def tree(**updates):
    return events.TwoPhaseTreeInput(**(dict(release_type="continuous",case_type="leakage",ignition_probability=.6,
        immediate_given_ignition=.4,vce_given_delayed=.25,branch_probability_source="Qualified branch fixture")|updates))


@pytest.mark.parametrize("phase,kind,case,basis,expected",[("two_phase","continuous","leakage","rupture_only_text",0),
    ("two_phase","instantaneous","rupture","rupture_only_text",1),
    ("vapor","instantaneous","leakage","rupture_only_text",0),
    ("vapor","instantaneous","leakage","figure53_instantaneous",1),
    ("liquid","instantaneous","rupture","rupture_only_text",0)])
def test_fireball_conditional_source_equations_and_explicit_figure_basis(phase,kind,case,basis,expected):
    r=events.fireball_given_immediate(events.FireballGivenImmediateInput(phase=phase,release_type=kind,
        case_type=case,applicability_basis=basis)).outputs
    assert r.fireball_given_immediate == expected


def test_continuous_two_phase_tree_has_one_immediate_branch():
    r=events.two_phase_tree(tree()).outputs
    assert r.terminal_probabilities["jet_pool_max"] == pytest.approx(.24)
    assert r.terminal_probabilities["jet_fire"] == r.terminal_probabilities["pool_fire"] == 0
    assert r.terminal_probabilities["vce"] == pytest.approx(.09)
    assert r.terminal_probabilities["flash_fire"] == pytest.approx(.27)
    assert r.non_ignition_probability == .4 and r.probability_sum == pytest.approx(1)


def test_instantaneous_leakage_and_rupture_figure_branches():
    leak=events.two_phase_tree(tree(release_type="instantaneous")).outputs
    rupture=events.two_phase_tree(tree(release_type="instantaneous",case_type="rupture")).outputs
    assert leak.terminal_probabilities["fireball"] == rupture.terminal_probabilities["fireball"] == pytest.approx(.24)
    assert leak.fireball_applicability_basis == "figure53_instantaneous"
    assert rupture.fireball_applicability_basis == "rupture_only_text"
    assert rupture.fireball_given_immediate == 1


def test_qualified_figure54_split_is_not_a_default_invented_probability():
    r=events.two_phase_tree(tree(release_type="instantaneous",case_type="rupture",
        qualified_rupture_fireball_fraction=.75,rupture_fireball_source="Explicit qualified figure54 branch fixture")).outputs
    assert r.fireball_probability_basis == "qualified_figure54_branch"
    assert r.terminal_probabilities["fireball"] == pytest.approx(.18)
    assert r.terminal_probabilities["pool_fire"] == pytest.approx(.06)
    assert r.probability_sum == pytest.approx(1)


@pytest.mark.parametrize("updates",[{"case_type":"rupture"},{"qualified_rupture_fireball_fraction":.75},
    {"qualified_rupture_fireball_fraction":.75,"rupture_fireball_source":"Not allowed on leakage"},
    {"release_type":"instantaneous","case_type":"rupture","qualified_rupture_fireball_fraction":.75,"rupture_fireball_source":" "}])
def test_unqualified_or_unsupported_tree_context_rejected(updates):
    with pytest.raises(DomainError):
        events.two_phase_tree(tree(**updates))


def correlated(**updates):
    return level2.CorrelatedJetPoolInput(**(dict(probability=.24,jet_equipment_area_m2=100,pool_equipment_area_m2=300,
        jet_personnel_area_m2=500,pool_personnel_area_m2=200,consequence_source="Correlated footprint fixture")|updates))


def test_correlated_maximum_is_separate_for_equipment_and_personnel():
    r=level2.correlated_jet_pool(correlated()).outputs
    assert r.equipment_area_m2 == 72 and r.personnel_area_m2 == 120
    assert r.governing_equipment == "pool" and r.governing_personnel == "jet"
    assert r.maximum_equipment_area_m2 == 300 and r.maximum_personnel_area_m2 == 500


def case(**updates):
    probabilities=events.two_phase_tree(tree()).outputs
    values=dict(hole="small",release_type="continuous",non_ignition_probability=probabilities.non_ignition_probability,
        event_tree_source="Two-phase Figure5.3 path fixture",consequence_source="Raw area fixtures",correlated_jet_pool=correlated(),
        outcomes=[level2.FlammableOutcomeInput(event=event,probability=p,equipment_area_m2=1000 if event == "vce" else 40 if event == "flash_fire" else 0,
            personnel_area_m2=2000 if event == "vce" else 160 if event == "flash_fire" else 0)
            for event,p in probabilities.terminal_probabilities.items() if event != "jet_pool_max"])
    return level2.FlammableCaseInput(**(values|updates))


def test_correlated_branch_flows_into_existing_flammable_area_once():
    r=level2.flammable_case(case()).outputs
    assert r.flammable_equipment_area_m2 == pytest.approx(.09*1000+.27*40+.24*300)
    assert r.flammable_personnel_area_m2 == pytest.approx(.09*2000+.27*160+.24*500)
    assert r.terminal_probability_sum == pytest.approx(1)


def test_duplicate_jet_pool_paths_and_wrong_context_are_rejected():
    inputs=case()
    duplicate=[o.model_copy(update={"probability":.24,"equipment_area_m2":100}) if o.event == "jet_fire" else o for o in inputs.outcomes]
    with pytest.raises(DomainError):
        level2.flammable_case(case(outcomes=duplicate))
    with pytest.raises(DomainError):
        level2.flammable_case(case(hole="rupture"))
    with pytest.raises(DomainError):
        level2.flammable_case(case(release_type="instantaneous"))
    with pytest.raises(DomainError):
        level2.flammable_case(case(correlated_jet_pool=None))


def ignition(**updates):
    return events.TwoPhaseIgnitionInput(**(dict(release_type="continuous",case_type="leakage",adjusted_mass_rate_kg_s=10,
        flammable_mass_fraction=.8,flash_mass_fraction=.2,liquid_flash_point_temperature_k=300,vapor_flash_point_temperature_k=300,
        vapor_molecular_weight_kg_kmol=44,storage_temperature_k=400,autoignition_temperature_k=600,
        correlation_basis_source="Qualified illustrative phase properties",reference_basis="qualified_reference",
        qualified_reference_temperature_k=300,reference_source="Explicit reference fixture",
        mixing_basis="qualified_vapor_weight",weighting_source="Qualified vapor weighting fixture")|updates))


@pytest.mark.parametrize("basis,liquid_weight",[("api581_printed_liquid_weight",.2),("qualified_vapor_weight",.8)])
def test_two_phase_composite_matches_manual_phase_weighting_and_table_paths(basis,liquid_weight):
    r=events.two_phase_ignition(ignition(mixing_basis=basis)).outputs
    assert r.flammable_rate_kg_s == 8
    assert r.flammable_liquid_rate_kg_s == pytest.approx(6.4) and r.flammable_vapor_rate_kg_s == pytest.approx(1.6)
    # Independent Table5.3 endpoints and linear temperature interpolation.
    immediate=liquid_weight*(.2+.8/3)+(1-liquid_weight)*(.5+.5/3)
    vce=liquid_weight*.25+(1-liquid_weight)*.5
    p=liquid_weight*r.liquid_ignition_probability+(1-liquid_weight)*r.vapor_ignition_probability
    assert r.immediate_given_ignition == pytest.approx(immediate)
    assert r.vce_given_delayed == pytest.approx(vce)
    assert r.ignition_probability == pytest.approx(p)
    assert r.terminal_probabilities["jet_pool_max"] == pytest.approx(p*immediate)
    assert r.terminal_probabilities["vce"] == pytest.approx(p*(1-immediate)*vce)
    assert r.probability_sum == pytest.approx(1)


def test_composite_phase_ignition_probabilities_match_independent_phase_calculations():
    inputs=ignition()
    r=events.two_phase_ignition(inputs).outputs
    for phase,rate in [("liquid",6.4),("vapor",1.6)]:
        other=events.single_phase_ignition(events.SinglePhaseIgnitionInput(phase=phase,release_type="continuous",case_type="leakage",
            flammable_rate_kg_s=rate,flash_point_temperature_k=300,molecular_weight_kg_kmol=44 if phase == "vapor" else None,
            storage_temperature_k=400,autoignition_temperature_k=600,correlation_basis_source="Independent phase fixture",
            reference_basis="qualified_reference",qualified_reference_temperature_k=300,reference_source="Explicit reference fixture")).outputs
        assert getattr(r,phase+"_ignition_probability") == other.ignition_probability


@pytest.mark.parametrize("updates",[{"adjusted_mass_rate_kg_s":0},{"flammable_mass_fraction":0}])
def test_zero_phase_fuel_cannot_ignite_above_ait(updates):
    r=events.two_phase_ignition(ignition(storage_temperature_k=700,**updates)).outputs
    assert r.ignition_probability == 0 and r.non_ignition_probability == 1
    assert all(p == 0 for p in r.terminal_probabilities.values())


@pytest.mark.parametrize("flash",[0,1])
def test_single_phase_flash_endpoints_require_single_phase_model(flash):
    with pytest.raises(DomainError):
        events.two_phase_ignition(ignition(flash_mass_fraction=flash))


@pytest.mark.parametrize("rate,fuel,flash",[(1e-300,1e-300,.2),(1e-100,1,1e-300)])
def test_positive_fuel_or_phase_rate_underflow_is_not_absent_fuel(rate,fuel,flash):
    with pytest.raises(DomainError) as exc:
        release.flammable_phase_rates(release.FlammablePhaseRatesInput(adjusted_mass_rate_kg_s=rate,
            flammable_mass_fraction=fuel,flash_mass_fraction=flash))
    assert exc.value.code == "numerical_failure"


def test_correlated_max_survives_full_level2_gff_financial_assessment():
    cases=[]
    for hole in ["small","medium","large","rupture"]:
        base=case().model_dump()
        if hole == "rupture":
            # No ignition path in this explicit rupture fixture; all sources zero.
            base.update(hole=hole,release_type="instantaneous",non_ignition_probability=1,correlated_jet_pool=None,
                outcomes=[level2.FlammableOutcomeInput(event=e,probability=0,equipment_area_m2=0,personnel_area_m2=0)
                    for e in ["pool_fire","jet_fire","fireball","vce","flash_fire"]])
        else:
            base["hole"]=hole
        cases.append(level2.ScenarioCaseInput(**base,toxic_components=[],toxic_applicability="not_applicable",
            toxic_applicability_source="Non-toxic test mixture",nfnt=level2.NfntAreasInput(consequence_source="No NFNT footprint in test")))
    r=level2.assessment(level2.AssessmentInput(component_type="DRUM",management_score=500,total_damage_factor=10,
        damage_factor_source="Explicit illustrative DF",cases=cases,
        financial=level2.FinancialBasisInput(repair=level2.RepairCostInput(component_type="DRUM",material_id="carbon_steel",
            price_factor_since_2001=1,usd_to_output_currency=1,cost_basis_year=2026,currency="USD"),
            outage=level2.ComponentOutageInput(component_type="DRUM",outage_multiplier=1,
                override_days={"small":1,"medium":2,"large":3,"rupture":4}),equipment_cost_per_m2=1000,
            production_cost_per_day=10000,population_density_per_m2=.001,cost_per_injury=1e6,
            weighted_cleanup_volume_m3=0,cleanup_cost_per_m3=0))).outputs
    expected=(.09*1000+.27*40+.24*300)*30e-6/30.6e-6
    assert r.equipment_area_m2 == pytest.approx(expected)
    assert r.financial_risk_per_year == pytest.approx(r.financial_consequence*306e-6)
