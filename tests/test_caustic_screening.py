import itertools
import runpy
import pytest
from api581 import DomainError
from api581.api import damage


factory=runpy.run_path('examples/caustic_screened_assessment.py')['request']


def susceptibility(**changes):
    return damage.CausticFigureSusceptibilityInput(**(factory().susceptibility.model_dump()|changes))


@pytest.mark.parametrize('material,present',list(itertools.product(['carbon_steel','low_alloy_steel','other_material'],[False,True])))
def test_material_and_any_caustic_screen(material,present):
    output=damage.caustic_screening(damage.CausticScreeningInput(material=material,caustic_present=present,
        screening_basis='Qualified material/exposure fixture')).outputs
    assert output.evaluate_caustic_cracking==(material!='other_material' and present)


# Independent reading of Figure6.2: columns heat/steam=00,01,10,11.
REFERENCE={('A',True):['none','low','medium','medium'],('A',False):['none','medium','high','high'],
    ('B',True):['medium']*4,('C',True):['medium']*4,('B',False):['high']*4,('C',False):['high']*4}


@pytest.mark.parametrize('area,low,heat,steam',list(itertools.product('ABC',[True,False],[False,True],[False,True])))
def test_figure_route_matrix_and_exact5wtpct_branch(area,low,heat,steam):
    plot=factory().susceptibility.plot.model_dump()|dict(chart_area=area,naoh_mass_fraction=.049999 if low else .05,
        heat_traced=heat,steamed_out_before_water_flush=steam)
    output=damage.caustic_figure_susceptibility(susceptibility(plot=plot)).outputs
    assert output.susceptibility==REFERENCE[(area,low)][2*int(heat)+int(steam)]
    assert output.plot_evidence_used


def test_crack_history_overrides_stress_relief_and_clear_inspection_alone():
    for cleared in [False,True]:
        output=damage.caustic_figure_susceptibility(susceptibility(stress_relieved=True,plot=None,
            cracking_history='detected_repaired',adequate_subsequent_clear_inspection=cleared)).outputs
        assert output.susceptibility=='high' and output.historical_high_retained and not output.plot_evidence_used


def test_specialist_reassignment_and_stress_relief_path():
    output=damage.caustic_figure_susceptibility(susceptibility(stress_relieved=True,plot=None,
        cracking_history='specialist_reassigned_after_clear_inspection',adequate_subsequent_clear_inspection=True,
        specialist_reassignment_basis='Qualified specialist reassignment after adequate clear inspection')).outputs
    assert output.susceptibility=='none' and not output.historical_high_retained


@pytest.mark.parametrize('changes',[dict(cracking_history='specialist_reassigned_after_clear_inspection'),
    dict(cracking_history='specialist_reassigned_after_clear_inspection',adequate_subsequent_clear_inspection=True,specialist_reassignment_basis=' '),
    dict(specialist_reassignment_basis='unused'),dict(plot=None),dict(fabrication_history_basis=' ')])
def test_missing_or_conflicting_qualification_rejected(changes):
    with pytest.raises(DomainError):
        damage.caustic_figure_susceptibility(susceptibility(**changes))


def test_unrepaired_cracks_require_ffs():
    with pytest.raises(DomainError) as caught:
        damage.caustic_figure_susceptibility(susceptibility(cracking_history='unrepaired'))
    assert caught.value.code=='ffs_required'


def test_unrepaired_ffs_referral_precedes_conflicting_reassignment_metadata():
    with pytest.raises(DomainError) as caught:
        damage.caustic_figure_susceptibility(susceptibility(cracking_history='unrepaired',
            specialist_reassignment_basis='Conflicting supplied reassignment',fabrication_history_basis=' '))
    assert caught.value.code=='ffs_required'


def test_repaired_history_stays_high_through_complete_df_despite_stress_relief():
    values=factory().model_dump()
    values['susceptibility'].update(stress_relieved=True,plot=None,cracking_history='detected_repaired',
        adequate_subsequent_clear_inspection=True)
    result=damage.caustic_screened_assessment(damage.CausticScreenedAssessmentInput(**values)).outputs
    assert result.historical_high_retained and result.effective_susceptibility=='high'
    assert result.severity_index==5000 and result.base_damage_factor==250.
    assert result.damage_factor==pytest.approx(250*2**1.1)
    values['susceptibility'].update(cracking_history='specialist_reassigned_after_clear_inspection',
        specialist_reassignment_basis='Specialist reassignment following adequate clear inspection')
    reassigned=damage.caustic_screened_assessment(damage.CausticScreenedAssessmentInput(**values)).outputs
    assert not reassigned.historical_high_retained and reassigned.effective_susceptibility=='none'
    assert reassigned.damage_factor==0.


def test_outside_graph_support_and_blank_plot_basis_rejected():
    for change in [dict(naoh_mass_fraction=.6),dict(plot_basis=' ')]:
        with pytest.raises(DomainError):
            damage.caustic_figure_susceptibility(susceptibility(plot=factory().susceptibility.plot.model_dump()|change))


def test_figure_to_existing_scc_df_and_screenout_is_not_zero_df():
    output=runpy.run_path('examples/caustic_screened_assessment.py')['main']()
    assert output.damage_factor==pytest.approx(25*2**1.1)
    values=factory().model_dump()
    values['screening']['caustic_present']=False
    with pytest.raises(DomainError) as caught:
        damage.caustic_screened_assessment(damage.CausticScreenedAssessmentInput(**values))
    assert caught.value.code=='caustic_outside_screen'


def test_existing_ambiguous_medium_no_inspection_cell_remains_rejected():
    with pytest.raises(DomainError) as caught:
        damage.caustic_screened_assessment(factory(inspections=dict(a=0,b=0,c=0,d=0)))
    assert caught.value.code=='ambiguous_source'
