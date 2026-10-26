"""Lining source tables, explicit age interpretation and minimum-thinning rule."""
from datetime import date, timedelta
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def history(**changes):
    return dict(lining_family="inorganic",installed_on=date(2000,1,1),evaluated_on=date(2000,1,1)+timedelta(days=3650),
        inspections=[],age_basis_policy="step1_installation_or_last_ab",year_length_days=365)|changes


def inspection(**changes):
    return dict(inspection_id="inspection-1",inspected_on=date(2000,1,1)+timedelta(days=1825),effectiveness="b",
        qualified_for_age_reset=True,qualification_basis="Qualified A/B lining inspection fixture")|changes


def request(**changes):
    return damage.LiningAssessmentInput(**(dict(lining_type="glass_lined",applicability_basis="Qualified protective glass lining fixture",
        age=history(inspections=[inspection()]),lookup_policy="exact_rows_only",first_year_policy="reject_below_first_year",
        condition=dict(condition="average"),monitoring=dict(monitoring_used=True,known_effective_for_lining_deterioration=True,
            effectiveness_basis="Qualified early lining-failure detection and orderly shutdown fixture"),
        base_material_thinning_damage_factor=50.,base_material_thinning_basis="Independent section4 thinning assessment fixture")|changes))


@pytest.mark.parametrize("kind,values",[
    ("strip_lined_resistant_alloy",[.3,.5,.7,1,1,2,3,4,6,9,12,16,22,30,40,53,69,89,115,146,184,230,286,351,428]),
    ("castable_refractory",[.5,1,2,4,9,16,30,53,89,146,230,351,518,738,1017,1358,1758,2209,2697,3000,3000,3000,3000,3000,3000]),
    ("castable_refractory_severe",[9,40,146,428,1017,1978]+[3000]*19),
    ("glass_lined",[3,4,6,7,9,11,13,16,20,25,30,36,44,53,63,75,89,105,124,146,170,199,230,266,306]),
    ("acid_brick",[.01,.03,.05,.15,1,1,1,1,2,3,4,5,7,9,11,15,19,25,31,40,50,63,78,97,119]),
    ("fiberglass",[1,1,1,1,1,1,2,3,7,13,26,47,82,139,228,359,548,808,1151,1587,2119,2743,3000,3000,3000]),
    ("organic_low_quality",[30,89,230,518,1017,1758,2697]+[3000]*18),
    ("organic_medium_quality",[1,4,16,53,146,351,738,1358,2209]+[3000]*16),
    ("organic_high_quality",[.1,.13,.15,.17,.2,1,4,16,53,146,351,738,1358,2209]+[3000]*11)])
def test_all_225_printed_table_cells(kind,values):
    assert len(values)==25
    for age,value in enumerate(values,1):
        r=damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type=kind,age_years=age,
            lookup_policy="exact_rows_only",first_year_policy="reject_below_first_year")).outputs
        assert r.base_damage_factor==value
        assert r.source_table==("5.5" if kind.startswith("organic_") else "5.4")


@pytest.mark.parametrize("policy,value",[("linear_between_rows",4.5),("conservative_upper_row",6.)])
def test_between_year_policy(policy,value):
    r=damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type="glass_lined",age_years=2.25,
        lookup_policy=policy,first_year_policy="reject_below_first_year")).outputs
    assert r.base_damage_factor==value and r.age_interpolation_weight==.25
    with pytest.raises(DomainError):
        damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type="glass_lined",age_years=2.25,
            lookup_policy="exact_rows_only",first_year_policy="reject_below_first_year"))


@pytest.mark.parametrize("age",[0.,.5,.999999])
def test_below_first_year_never_invents_zero_or_extrapolation(age):
    with pytest.raises(DomainError) as error:
        damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type="acid_brick",age_years=age,
            lookup_policy="linear_between_rows",first_year_policy="reject_below_first_year"))
    assert error.value.code=="lining_age_below_first_row"
    r=damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type="acid_brick",age_years=age,
        lookup_policy="linear_between_rows",first_year_policy="qualified_first_year_value",first_year_qualification_basis="Owner-qualified first-year estimate")).outputs
    assert r.base_damage_factor==.01 and r.first_year_value_used


@pytest.mark.parametrize("kind",["organic_low_quality","strip_lined_resistant_alloy"])
def test_no_after_25_extrapolation_even_plateau_columns(kind):
    with pytest.raises(DomainError) as error:
        damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type=kind,age_years=25.01,
            lookup_policy="conservative_upper_row",first_year_policy="reject_below_first_year"))
    assert error.value.code=="lining_table_age_exceeded"


@pytest.mark.parametrize("policy,basis",[("qualified_first_year_value",None),("qualified_first_year_value"," "),("reject_below_first_year","override")])
def test_first_year_policy_basis_consistency(policy,basis):
    with pytest.raises(DomainError):
        damage.lining_base_factor(damage.LiningBaseFactorInput(lining_type="glass_lined",age_years=1.,
            lookup_policy="exact_rows_only",first_year_policy=policy,first_year_qualification_basis=basis))


def test_latest_qualified_ab_inspection_resets_but_unqualified_or_cd_does_not():
    visits=[inspection(inspection_id="early",inspected_on=date(2001,1,1)),inspection(),
        inspection(inspection_id="recent-c",inspected_on=date(2008,1,1),effectiveness="c",qualified_for_age_reset=False,qualification_basis=None),
        inspection(inspection_id="unqualified-a",inspected_on=date(2009,1,1),effectiveness="a",qualified_for_age_reset=False,qualification_basis=None)]
    r=damage.lining_effective_age(damage.LiningEffectiveAgeInput(**history(inspections=visits))).outputs
    assert r.effective_age_years==5 and r.elapsed_service_years==10
    assert r.reset_inspection_id=="inspection-1" and r.qualified_ab_inspection_count==2


@pytest.mark.parametrize("policy,expected",[("step1_installation_or_last_ab",5),("figure51_organic_service_only",10)])
def test_organic_source_age_interpretations_are_explicit(policy,expected):
    r=damage.lining_effective_age(damage.LiningEffectiveAgeInput(**history(lining_family="organic",inspections=[inspection()],age_basis_policy=policy))).outputs
    assert r.effective_age_years==expected
    assert (r.reset_inspection_id is None)==(expected==10)


def test_day_year_basis_and_same_day_installation():
    r=damage.lining_effective_age(damage.LiningEffectiveAgeInput(**history(year_length_days=365.25))).outputs
    assert r.effective_age_years==pytest.approx(3650/365.25)
    r=damage.lining_effective_age(damage.LiningEffectiveAgeInput(**history(evaluated_on=date(2000,1,1)))).outputs
    assert r.effective_age_years==0 and r.age_baseline_source=="installation"


@pytest.mark.parametrize("changes",[dict(evaluated_on=date(1999,1,1)),dict(age_basis_policy="figure51_organic_service_only"),
    dict(inspections=[inspection(effectiveness="c")]),dict(inspections=[inspection(qualification_basis=" ")]),
    dict(inspections=[inspection(),inspection()]),dict(inspections=[inspection(inspected_on=date(1999,1,1))]),
    dict(inspections=[inspection(inspected_on=date(2020,1,1))]),
    dict(inspections=[inspection(qualified_for_age_reset=False)])])
def test_invalid_history_and_reset_claims(changes):
    with pytest.raises(DomainError):
        damage.lining_effective_age(damage.LiningEffectiveAgeInput(**history(**changes)))


@pytest.mark.parametrize("condition,value",[("good",1),("average",2),("poor",10)])
def test_condition_table(condition,value):
    assert damage.lining_condition_factor(damage.LiningConditionFactorInput(condition=condition)).outputs.condition_factor==value


@pytest.mark.parametrize("used,effective,basis,value",[(False,False,None,1),(True,False,None,1),(True,True,"Qualified early detection",.1)])
def test_monitoring_credit(used,effective,basis,value):
    assert damage.lining_monitoring_factor(damage.LiningMonitoringFactorInput(monitoring_used=used,
        known_effective_for_lining_deterioration=effective,effectiveness_basis=basis)).outputs.monitoring_factor==value


@pytest.mark.parametrize("used,effective,basis",[(False,True,"fixture"),(True,True,None),(True,True," "),(True,False,"fixture")])
def test_monitoring_requires_actual_effectiveness_basis(used,effective,basis):
    with pytest.raises(DomainError):
        damage.lining_monitoring_factor(damage.LiningMonitoringFactorInput(monitoring_used=used,
            known_effective_for_lining_deterioration=effective,effectiveness_basis=basis))


@pytest.mark.parametrize("thin,lining,value,source",[(50,1.8,1.8,"lining"),(1,1.8,1,"base_material_thinning"),(1,1,1,"equal"),(0,10,0,"base_material_thinning")])
def test_minimum_not_product_or_sum(thin,lining,value,source):
    r=damage.lining_governing_thinning(damage.LiningGoverningThinningInput(base_material_thinning_damage_factor=thin,lining_damage_factor=lining)).outputs
    assert r.governing_thinning_damage_factor==value and r.governing_source==source


def test_assessment_matches_independent_tables_and_existing_equation():
    r=damage.lining_assessment(request()).outputs
    assert r.effective_age_years==5 and r.base_damage_factor==9 and r.lining_damage_factor==pytest.approx(1.8)
    independent=damage.lining_adjust(damage.LiningAdjustInput(base_damage_factor=9.,condition="average",effective_online_monitoring=True)).outputs
    assert r.lining_damage_factor==independent.lining_damage_factor
    assert r.governing_thinning_damage_factor==r.lining_damage_factor


def test_organic_assumptions_and_small_lining_df_not_floored():
    flags=dict(organic_compatible_with_environment=True,organic_within_design_temperature_including_steamout=True,organic_properly_applied_and_cured=True)
    r=damage.lining_assessment(request(lining_type="organic_high_quality",age=history(lining_family="organic",evaluated_on=date(2000,1,1)+timedelta(days=365)),
        condition=dict(condition="good"),**flags)).outputs
    assert r.lining_damage_factor==pytest.approx(.01) and r.governing_thinning_damage_factor==pytest.approx(.01)
    for key in flags:
        for bad in [False,None]:
            with pytest.raises(DomainError):
                damage.lining_assessment(request(lining_type="organic_high_quality",age=history(lining_family="organic"),**(flags|{key:bad})))


@pytest.mark.parametrize("changes",[dict(applicability_basis=" "),dict(base_material_thinning_basis=" "),
    dict(age=history(lining_family="organic")),dict(organic_properly_applied_and_cured=True)])
def test_assessment_qualification_and_family_mismatch(changes):
    with pytest.raises(DomainError):
        damage.lining_assessment(request(**changes))


def test_invalid_numeric_and_unknown_types():
    for changes in [dict(lining_type="cladding"),dict(base_material_thinning_damage_factor=-1),dict(base_material_thinning_damage_factor=True),dict(base_material_thinning_damage_factor=float("inf"))]:
        with pytest.raises(ValidationError):
            request(**changes)
