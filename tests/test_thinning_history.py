import runpy
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


example=runpy.run_path('examples/thinning_history_assessment.py')


def history(**changes):
    return damage.ThinningInspectionHistoryInput(**(example['history']().model_dump()|changes))


def test_measured_baseline_uses_its_own_age_and_eligible_counts():
    result=damage.thinning_inspection_history(history()).outputs
    assert result.elapsed_days==1461. and result.elapsed_years==4.
    assert result.baseline_thickness_m==.01
    assert result.eligible_inspection_ids==['b1','c1']
    assert result.excluded_inspection_reasons=={'old':'before_baseline','baseline':'baseline_boundary',
        'unqualified':'unqualified','later':'after_assessment','e1':'ineffective_e'}
    assert (result.inspections_a,result.inspections_b,result.inspections_c,result.inspections_d)==(0,1,1,0)


def test_furnished_age_starts_at_installation_and_zero_age_allowed():
    values=history().model_dump(include=set(damage.ThinningAssessmentPeriodInput.model_fields))
    values.update(baseline_type='furnished',measured_baseline=None,furnished_thickness_m=.02,
        installed_at='2025-01-01T00:00:00Z')
    result=damage.thinning_assessment_period(damage.ThinningAssessmentPeriodInput(**values)).outputs
    assert result.elapsed_years==0. and result.baseline_thickness_m==.02 and result.baseline_inspection_id is None


def test_baseline_boundary_policy_and_utc_equivalent_timestamps():
    values=history().model_dump()
    values['inspections'][1]['performed_at']='2021-01-01T09:00:00+09:00'
    result=damage.thinning_inspection_history(history(**(values|dict(baseline_boundary_policy='include_baseline_time')))).outputs
    assert result.inspections_a==1 and 'baseline' in result.eligible_inspection_ids


def test_offset_transition_uses_elapsed_utc_hours():
    result=damage.thinning_assessment_period(damage.ThinningAssessmentPeriodInput(
        installed_at='2024-03-10T01:30:00-05:00',assessment_at='2024-03-10T03:30:00-04:00',baseline_type='furnished',
        furnished_thickness_m=.01,days_per_year=365.25,period_and_year_basis='UTC elapsed-hour fixture')).outputs
    assert result.elapsed_days==pytest.approx(1/24)


def test_assessment_time_inspection_is_included():
    values=history().model_dump()
    values['inspections'].append(dict(inspection_id='at_end',performed_at='2025-01-01T09:00:00+09:00',
        effectiveness='d',qualified_for_component_mechanism=True,inspection_basis='Qualified performed end-time fixture'))
    result=damage.thinning_inspection_history(history(**values)).outputs
    assert result.inspections_d==1 and 'at_end' in result.eligible_inspection_ids


@pytest.mark.parametrize('field',['installed_at','assessment_at'])
def test_naive_timestamps_rejected(field):
    with pytest.raises(ValidationError):
        history(**{field:'2025-01-01T00:00:00'})


@pytest.mark.parametrize('problem',['before_install','after_assessment','quality','accuracy','blank_reset','competing_furnished','missing_measurement','blank_period'])
def test_invalid_baseline_or_quality_rejected(problem):
    values=history().model_dump()
    if problem=='before_install': values['measured_baseline']['measured_at']='2009-01-01T00:00:00Z'
    elif problem=='after_assessment': values['measured_baseline']['measured_at']='2026-01-01T00:00:00Z'
    elif problem=='quality': values['measured_baseline']['high_quality_inspection']=False
    elif problem=='accuracy': values['measured_baseline']['high_confidence_accuracy']=False
    elif problem=='blank_reset': values['measured_baseline']['reset_basis']=' '
    elif problem=='competing_furnished': values['furnished_thickness_m']=.02
    elif problem=='missing_measurement': values['measured_baseline']=None
    else: values['period_and_year_basis']=' '
    with pytest.raises(DomainError):
        damage.thinning_inspection_history(history(**values))


@pytest.mark.parametrize('problem',['duplicate','blank_id','conflicting_baseline_time','blank_basis'])
def test_history_identity_and_qualification_rejected(problem):
    values=history().model_dump()
    if problem=='duplicate': values['inspections'][0]['inspection_id']='b1'
    elif problem=='blank_id': values['inspections'][0]['inspection_id']=' '
    elif problem=='conflicting_baseline_time': values['inspections'][1]['performed_at']='2021-01-02T00:00:00Z'
    else: values['inspections'][0]['inspection_basis']=' '
    with pytest.raises(DomainError):
        damage.thinning_inspection_history(history(**values))


def test_history_drives_bayes_and_strength_baseline_must_agree():
    output=example['main']()
    assert output.posterior_probabilities==pytest.approx([.28/.29,.009/.29,.001/.29])
    values=example['request']().model_dump()
    values['strength']['starting_thickness_m']=.02
    with pytest.raises(DomainError,match='thickness must match'):
        damage.thinning_history_assessment(damage.ThinningHistoryAssessmentInput(**values))
