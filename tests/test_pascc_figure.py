import runpy
import pytest
from api581 import DomainError
from api581.api import damage


def service(**changes):
    return damage.PasccFigureSusceptibilityInput(**(dict(alloy=dict(operating_temperature_k=650.,
        material_group='regular_300ss_or_alloy600_800',heat_treatment='solution_annealed'),
        sulfur_oxygen_water_during_operation=False,sulfur_oxygen_water_during_shutdown=True,
        qualified_rp0170_downtime_protection=False,confirmed_cracking=False,unrepaired_cracks=False,
        service_alloy_basis='Qualified alloy, thermal history and shutdown exposure')|changes))


@pytest.mark.parametrize('group,raw,reduced',[('h_grade_300ss','high','medium'),
    ('regular_300ss_or_alloy600_800','medium','low'),('l_grade_300ss','low','none')])
def test_one_level_downtime_reduction(group,raw,reduced):
    alloy=service().alloy.model_dump()|dict(material_group=group)
    r=damage.pascc_figure_susceptibility(service(alloy=alloy,qualified_rp0170_downtime_protection=True,
        protection_basis='Qualified RP0170 implementation')).outputs
    assert r.table_or_override_susceptibility==raw and r.susceptibility==reduced and r.downtime_reduction_applied


def test_confirmed_cracks_override_exposure_and_protection():
    r=damage.pascc_figure_susceptibility(service(confirmed_cracking=True,sulfur_oxygen_water_during_shutdown=False,
        qualified_rp0170_downtime_protection=True,protection_basis='Qualified protection')).outputs
    assert r.susceptibility=='high' and not r.downtime_reduction_applied
    assert damage.pascc_figure_susceptibility(service(sulfur_oxygen_water_during_shutdown=False)).outputs.susceptibility=='none'


def test_ffs_and_protection_basis():
    with pytest.raises(DomainError) as caught:
        damage.pascc_figure_susceptibility(service(unrepaired_cracks=True))
    assert caught.value.code=='ffs_required'
    with pytest.raises(DomainError):
        damage.pascc_figure_susceptibility(service(qualified_rp0170_downtime_protection=True))


def test_qualified_df():
    r=damage.pascc_qualified_assessment(damage.PasccQualifiedAssessmentInput(
        screening=dict(material='austenitic_stainless_steel',sulfur_bearing_compounds_exposure=True,exposure_basis='Qualified sulfur history'),
        service=service(),years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified PASCC-specific inspection')).outputs
    assert r.severity_index==500 and r.base_damage_factor==25.
    assert r.damage_factor==pytest.approx(25*2**1.1)


def test_protection_applies_once_before_df_and_matches_independent_call():
    example=runpy.run_path('examples/pascc_qualified_assessment.py')
    integrated=example['main']()
    direct=damage.pascc(damage.PasccInput(susceptibility='low',confirmed_cracking=False,unrepaired_cracks=False,
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0))).outputs
    assert integrated.damage_factor==direct.damage_factor
    assert integrated.age_factor==direct.age_factor


@pytest.mark.parametrize('group',['h_grade_300ss','l_grade_300ss','321ss'])
def test_nickel_screen_cannot_use_stainless_only_row(group):
    factory=runpy.run_path('examples/pascc_qualified_assessment.py')['request']
    values=factory().model_dump()
    values['screening']['material']='nickel_based_alloy'
    values['service']['alloy']['material_group']=group
    with pytest.raises(DomainError) as caught:
        damage.pascc_qualified_assessment(damage.PasccQualifiedAssessmentInput(**values))
    assert caught.value.code=='pascc_material_mismatch'


def test_integrated_unrepaired_cracking_never_issues_df():
    factory=runpy.run_path('examples/pascc_qualified_assessment.py')['request']
    values=factory().model_dump()
    values['service']['unrepaired_cracks']=True
    values['inspection_basis']=' '
    with pytest.raises(DomainError) as caught:
        damage.pascc_qualified_assessment(damage.PasccQualifiedAssessmentInput(**values))
    assert caught.value.code=='ffs_required'
