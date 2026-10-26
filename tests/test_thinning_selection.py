import runpy
import pytest
from api581 import DomainError
from api581.api import damage


def choice(**changes):
    factory=runpy.run_path('examples/multiple_thinning_mechanisms.py')['selection']
    return damage.ThinningRateSelectionInput(**(factory().model_dump()|changes))


def test_measured_priority_maximum_not_sum_and_local_type_independent():
    output=damage.thinning_rate_selection(choice()).outputs
    assert output.corrosion_rate_m_year==.0003
    assert output.selection_source_by_mechanism=={'uniform_mechanism':'measured','localized_mechanism':'estimated'}
    assert output.fallback_ignored_by_mechanism=={'uniform_mechanism':True,'localized_mechanism':False}
    assert output.governing_rate_mechanism_ids==['uniform_mechanism']
    assert output.governing_type_mechanism_ids==['localized_mechanism']
    assert output.assessment_distribution=='local'


def test_zero_measurement_is_not_missing_and_ignored_fallback_is_not_selected():
    items=choice().model_dump()['mechanisms'][:1]
    items[0]['measured']['corrosion_rate_m_year']=0.
    items[0]['fallback']['rate_basis']=' '
    output=damage.thinning_rate_selection(choice(mechanisms=items)).outputs
    assert output.corrosion_rate_m_year==0.
    assert output.selection_source_by_mechanism['uniform_mechanism']=='measured'
    assert output.assessment_distribution=='general'


def test_ties_report_all_ids_deterministically():
    items=choice().model_dump()['mechanisms']
    items[1]['fallback']['corrosion_rate_m_year']=.0003
    first=damage.thinning_rate_selection(choice(mechanisms=items)).outputs
    second=damage.thinning_rate_selection(choice(mechanisms=list(reversed(items)))).outputs
    assert first.governing_rate_mechanism_ids==second.governing_rate_mechanism_ids==['localized_mechanism','uniform_mechanism']


@pytest.mark.parametrize('problem',['duplicate','blank_id','missing_rate','unrepresentative','blank_measurement_basis','blank_fallback_basis'])
def test_unqualified_or_ambiguous_candidates_rejected(problem):
    items=choice().model_dump()['mechanisms']
    if problem=='duplicate': items[1]['mechanism_id']=items[0]['mechanism_id']
    elif problem=='blank_id': items[0]['mechanism_id']=' '
    elif problem=='missing_rate': items[0]['measured']=items[0]['fallback']=None
    elif problem=='unrepresentative': items[0]['measured']['representative_for_current_period']=False
    elif problem=='blank_measurement_basis': items[0]['measured']['measurement_basis']=' '
    else: items[1]['fallback']['rate_basis']=' '
    with pytest.raises(DomainError):
        damage.thinning_rate_selection(choice(mechanisms=items))


def test_common_period_qualification_required():
    with pytest.raises(DomainError):
        damage.thinning_rate_selection(choice(applicability_and_period_basis=' '))


def test_same_selection_drives_wall_loss_and_no_borrowed_monitoring():
    example=runpy.run_path('examples/multiple_thinning_mechanisms.py')
    output=example['main']()
    assert output.online_monitoring_factor==1. and output.thinning_damage_factor>0.
    values=example['request']().model_dump()
    values['conditions']['monitoring']['row']={'mechanism':'hydrochloric_acid'}
    with pytest.raises(DomainError,match='other monitoring row'):
        damage.thinning_selected_mechanisms(damage.ThinningSelectedMechanismsInput(**values))
