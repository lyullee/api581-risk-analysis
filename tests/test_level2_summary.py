"""Level2 addition versus Level1 maximum; event and GFF order; full risk chain."""
import math
import pytest
from pydantic import ValidationError
from api581 import Context, DomainError
from api581.api import level2, consequence, frequency, financial


def outcomes(rupture=False,scale=1):
    rows=[("pool_fire",0 if rupture else .1,300,400),("jet_fire",0 if rupture else .2,100,200),
          ("fireball",.3 if rupture else 0,200,400),("vce",.1,1000,2000),("flash_fire",.1,50,100)]
    return [level2.FlammableOutcomeInput(event=event,probability=p,
        equipment_area_m2=e*scale if p else 0,personnel_area_m2=i*scale if p else 0) for event,p,e,i in rows]


def flame(hole="small",scale=1):
    rupture=hole == "rupture"
    return dict(hole=hole,release_type="instantaneous" if rupture else "continuous",outcomes=outcomes(rupture,scale),
        non_ignition_probability=.5,event_tree_source="Owner-qualified terminal probability fixture",
        consequence_source="Explicit raw event-area fixture")


def scenario(hole="small",scale=1):
    return level2.ScenarioCaseInput(**flame(hole,scale),toxic_applicability="evaluated",
        toxic_applicability_source="Owner-qualified two-component toxic mixture fixture",
        toxic_components=[level2.ToxicCloudAreaInput(component_id=name,cloud_area_m2=area*scale,
            selected_criterion_source="Explicit qualified footprint fixture") for name,area in [("h2s",1000),("co",2000)]],
        nfnt=level2.NfntAreasInput(consequence_source="NFNT footprint fixture",steam_chemical_personnel_area_m2=600*scale,
            physical_equipment_area_m2=300*scale if hole == "rupture" else 0,
            physical_personnel_area_m2=500*scale if hole == "rupture" else 0,
            bleve_equipment_area_m2=400*scale if hole == "rupture" else 0,
            bleve_personnel_area_m2=600*scale if hole == "rupture" else 0))


def test_five_event_weighting_matches_manual_source_equations():
    result=level2.flammable_case(level2.FlammableCaseInput(**flame())).outputs
    assert result.flammable_equipment_area_m2 == pytest.approx(155)
    assert result.flammable_personnel_area_m2 == pytest.approx(290)
    assert result.non_ignition_probability == .5 and result.terminal_probability_sum == 1


def test_instantaneous_rupture_fireball_weighting():
    result=level2.flammable_case(level2.FlammableCaseInput(**flame("rupture"))).outputs
    assert result.flammable_equipment_area_m2 == pytest.approx(165)
    assert result.flammable_personnel_area_m2 == pytest.approx(330)


def test_missing_duplicate_and_nonconserving_terminal_probabilities_rejected():
    data=flame()
    with pytest.raises(ValidationError):
        level2.FlammableCaseInput(**(data|{"outcomes":data["outcomes"][:4]}))
    with pytest.raises(DomainError):
        level2.flammable_case(level2.FlammableCaseInput(**(data|{"outcomes":[data["outcomes"][0]]*5})))
    with pytest.raises(DomainError):
        level2.flammable_case(level2.FlammableCaseInput(**(data|{"non_ignition_probability":.6})))


@pytest.mark.parametrize("hole,release_type,event",[("small","continuous","fireball"),("rupture","continuous","fireball"),
                                                   ("rupture","instantaneous","jet_fire")])
def test_inapplicable_jet_and_fireball_branches_rejected(hole,release_type,event):
    rows=[level2.FlammableOutcomeInput(event=e,probability=.5 if e == event else 0,
        equipment_area_m2=100 if e == event else 0,personnel_area_m2=200 if e == event else 0)
        for e in ["pool_fire","jet_fire","fireball","vce","flash_fire"]]
    with pytest.raises(DomainError):
        level2.flammable_case(level2.FlammableCaseInput(**(flame(hole)|{"release_type":release_type,"outcomes":rows})))


def test_final_level2_adds_flammable_to_non_ignition_maximum():
    result=level2.final_area(level2.FinalAreaInput(flammable_equipment_area_m2=100,flammable_personnel_area_m2=200,
        toxic_personnel_area_m2=500,nfnt_equipment_area_m2=20,nfnt_personnel_area_m2=300)).outputs
    assert result.equipment_area_m2 == 120
    assert result.personnel_area_m2 == result.consequence_area_m2 == 700
    assert result.governing_non_ignition_personnel_mechanism == "toxic"
    # Distinct Level1 function retains its original max-over-mechanisms behavior.
    old=consequence.final_area(consequence.FinalAreaInput(flammable_equipment_area_m2=100,
        flammable_personnel_area_m2=200,toxic_personnel_areas_m2=[500],nfnt_personnel_area_m2=300)).outputs
    assert old.personnel_area_m2 == 500 and old.equipment_area_m2 == 100


@pytest.mark.parametrize("toxic,nfnt,expected",[(50,100,"nfnt"),(100,100,"equal"),(0,0,"equal")])
def test_non_ignition_tie_and_nfnt_selection(toxic,nfnt,expected):
    result=level2.final_area(level2.FinalAreaInput(flammable_equipment_area_m2=0,flammable_personnel_area_m2=0,
        toxic_personnel_area_m2=toxic,nfnt_equipment_area_m2=0,nfnt_personnel_area_m2=nfnt)).outputs
    assert result.governing_non_ignition_personnel_mechanism == expected
    assert result.personnel_area_m2 == max(toxic,nfnt)


def mechanism_holes():
    return [level2.MechanismHoleInput(hole=hole,generic_frequency_per_year=1 if i < 2 else 0,
        flammable_equipment_area_m2=10,flammable_personnel_area_m2=10,toxic_personnel_area_m2=100 if i == 0 else 0,
        nfnt_equipment_area_m2=0,nfnt_personnel_area_m2=100 if i == 1 else 0)
        for i,hole in enumerate(["small","medium","large","rupture"])]


def test_gff_average_precedes_non_ignition_maximum_selection():
    result=level2.consequence_summary(level2.ConsequenceSummaryInput(holes=mechanism_holes())).outputs
    assert result.toxic_personnel_area_m2 == result.nfnt_personnel_area_m2 == 50
    assert result.personnel_area_m2 == 60  # Per-hole max then average would incorrectly yield110.
    assert result.equipment_area_m2 == 10
    assert result.governing_non_ignition_personnel_mechanism == "equal"


def test_summary_rejects_duplicate_missing_and_zero_frequency_holes():
    with pytest.raises(ValidationError):
        level2.ConsequenceSummaryInput(holes=mechanism_holes()[:3])
    with pytest.raises(DomainError):
        level2.consequence_summary(level2.ConsequenceSummaryInput(holes=[mechanism_holes()[0]]*4))
    with pytest.raises(DomainError):
        level2.consequence_summary(level2.ConsequenceSummaryInput(holes=[h.model_copy(update={"generic_frequency_per_year":0}) for h in mechanism_holes()]))


def test_scenario_uses_shared_non_ignition_once_and_keeps_mechanisms_separate():
    result=level2.scenario_consequence(scenario()).outputs
    assert result.flammable_personnel_area_m2 == pytest.approx(290)
    assert result.toxic_personnel_area_m2 == 1000
    assert result.nfnt_personnel_area_m2 == 300 and result.nfnt_equipment_area_m2 == 0
    assert result.non_ignition_probability == .5


def test_nfnt_rupture_maximum_precedes_probability_weighting():
    result=level2.scenario_consequence(scenario("rupture")).outputs
    assert result.nfnt_equipment_area_m2 == 200
    assert result.nfnt_personnel_area_m2 == 300


def test_toxic_omission_requires_explicit_not_applicable():
    with pytest.raises(DomainError):
        level2.scenario_consequence(scenario().model_copy(update={"toxic_components":[]}))
    with pytest.raises(DomainError):
        level2.scenario_consequence(scenario().model_copy(update={"toxic_applicability":"not_applicable"}))
    result=level2.scenario_consequence(scenario().model_copy(update={"toxic_components":[],"toxic_applicability":"not_applicable"})).outputs
    assert result.toxic_personnel_area_m2 == 0


def frequency_scenarios():
    return [level2.FrequencyScenarioInput(**scenario(hole,i).model_dump(),generic_frequency_per_year=i)
        for i,hole in enumerate(["small","medium","large","rupture"],start=1)]


def test_raw_scenarios_summary_matches_independent_manual_mechanism_weights():
    result=level2.scenario_summary(level2.ScenarioSummaryInput(cases=frequency_scenarios())).outputs
    assert result.flammable_equipment_area_m2 == pytest.approx((155*(1+4+9)+165*16)/10)
    assert result.flammable_personnel_area_m2 == pytest.approx((290*(1+4+9)+330*16)/10)
    assert result.toxic_personnel_area_m2 == 3000
    assert result.nfnt_equipment_area_m2 == 320
    assert result.nfnt_personnel_area_m2 == 900
    assert result.personnel_area_m2 == pytest.approx(result.flammable_personnel_area_m2+3000)


def financial_basis():
    return level2.FinancialBasisInput(repair=level2.RepairCostInput(component_type="DRUM",material_id="carbon_steel",
        price_factor_since_2001=2,usd_to_output_currency=1,cost_basis_year=2026,currency="USD"),
        outage=level2.ComponentOutageInput(component_type="DRUM",outage_multiplier=1,
            override_days={"small":1,"medium":2,"large":3,"rupture":4}),
        equipment_cost_per_m2=1000,production_cost_per_day=10000,population_density_per_m2=.001,
        cost_per_injury=1e6,weighted_cleanup_volume_m3=20,cleanup_cost_per_m3=200)


def assessment_request(**updates):
    values=dict(component_type="DRUM",management_score=500,total_damage_factor=10,
        damage_factor_source="Illustrative owner-qualified DF, not automatic damage applicability",
        cases=[scenario(hole,i) for i,hole in enumerate(["small","medium","large","rupture"],start=1)],financial=financial_basis())
    return level2.AssessmentInput(**(values|updates))


def test_assessment_full_financial_and_risk_chain_with_reproducible_context():
    inputs=assessment_request()
    result=level2.assessment(inputs,context=Context(asset_id="level2-test-asset",source_revision="inputs1"))
    r=result.outputs
    assert r.generic_frequency_per_year == pytest.approx(30.6e-6)
    assert r.management_factor == 1
    assert r.annual_failure_frequency == pytest.approx(306e-6)
    assert r.financial_consequence == pytest.approx(sum([r.component_repair_cost,r.surrounding_equipment_cost,
        r.business_interruption_cost,r.injury_cost,r.environmental_cost]))
    assert r.surrounding_equipment_cost == pytest.approx(1000*r.equipment_area_m2)
    assert r.injury_cost == pytest.approx(1000*r.personnel_area_m2)
    assert r.environmental_cost == 4000
    assert r.financial_risk_per_year == pytest.approx(r.annual_failure_frequency*r.financial_consequence)
    assert r.equipment_area_risk_m2_per_year == pytest.approx(r.annual_failure_frequency*r.equipment_area_m2)
    assert r.personnel_area_risk_m2_per_year == pytest.approx(r.annual_failure_frequency*r.personnel_area_m2)
    assert r.currency == "USD" and r.cost_basis_year == 2026
    assert result.context.asset_id == "level2-test-asset" and result.references and result.code_fingerprint
    # Validate composition against independent existing financial API and GFF table.
    independent=financial.level1_consequence(financial.Level1ConsequenceInput(**inputs.financial.model_dump(),
        equipment_area_m2=r.equipment_area_m2,personnel_area_m2=r.personnel_area_m2)).outputs
    assert independent.financial_consequence == r.financial_consequence
    gff=frequency.generic(frequency.GenericInput(component_type="DRUM")).outputs
    manual_toxic=sum(gff.by_hole_per_year[c.hole]*.5*max(v.cloud_area_m2 for v in c.toxic_components) for c in inputs.cases)/gff.total_per_year
    assert r.toxic_personnel_area_m2 == pytest.approx(manual_toxic)


def test_zero_df_retains_consequence_but_returns_zero_annual_risk():
    r=level2.assessment(assessment_request(total_damage_factor=0)).outputs
    assert r.financial_consequence > 0 and r.personnel_area_m2 > 0
    assert r.annual_failure_frequency == r.financial_risk_per_year == r.personnel_area_risk_m2_per_year == 0
    assert r.frequency_weighted_personnel_area_m2 is None


def test_assessment_rejects_component_mismatch_and_blank_damage_source():
    with pytest.raises(DomainError):
        level2.assessment(assessment_request(component_type="REACTOR"))
    with pytest.raises(DomainError):
        level2.assessment(assessment_request(damage_factor_source=" "))


def test_computed_financial_areas_cannot_be_overridden_as_inputs():
    with pytest.raises(ValidationError):
        level2.FinancialBasisInput(**financial_basis().model_dump(),equipment_area_m2=100)


def test_final_area_overflow_is_explicit_domain_error():
    with pytest.raises(DomainError) as exc:
        level2.final_area(level2.FinalAreaInput(flammable_equipment_area_m2=1e308,flammable_personnel_area_m2=0,
            toxic_personnel_area_m2=0,nfnt_equipment_area_m2=1e308,nfnt_personnel_area_m2=0))
    assert exc.value.code == "numerical_failure"
