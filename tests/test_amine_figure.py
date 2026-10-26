import math
import runpy
import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.AmineFigureSusceptibilityInput(**(dict(confirmed_cracking=False,unrepaired_cracks=False,
        stress_relieved=False,solution='lean',amine_group='mea_or_dipa',maximum_metal_temperature_k=300.,
        heat_traced=False,steamed_out_before_water_flush=False,applicability_basis='Qualified Figure7.1 service fixture')|changes))


@pytest.mark.parametrize('group,expected',[
    ('mea_or_dipa',['low','medium','medium','medium','medium','high']),
    ('dea',['none','none','none','low','low','medium']),
    ('other_treating_amine',['none','none','none','none','none','low'])])
def test_printed_temperature_thresholds(group,expected):
    for fahrenheit,level in zip([99.,100.,139.,140.,180.,181.],expected):
        output=damage.amine_figure_susceptibility(request(amine_group=group,
            maximum_metal_temperature_k=(fahrenheit-32)*5/9+273.15)).outputs
        assert output.susceptibility==level


@pytest.mark.parametrize('group,expected',[('mea_or_dipa','medium'),('dea','low'),('other_treating_amine','low')])
@pytest.mark.parametrize('heating',['heat_traced','steamed_out_before_water_flush'])
def test_low_temperature_upset_heating_routes(group,expected,heating):
    output=damage.amine_figure_susceptibility(request(amine_group=group,**{heating:True})).outputs
    assert output.susceptibility==expected


@pytest.mark.parametrize('solution',['fresh','rich'])
def test_nonlean_route_and_confirmed_crack_priority(solution):
    output=damage.amine_figure_susceptibility(request(solution=solution,maximum_metal_temperature_k=400.)).outputs
    assert output.susceptibility=='none'
    high=damage.amine_figure_susceptibility(request(solution=solution,stress_relieved=True,confirmed_cracking=True)).outputs
    assert high.susceptibility=='high'


def test_both_exposures_route_lean_and_stress_relief():
    assert damage.amine_figure_susceptibility(request(solution='lean_and_rich')).outputs.susceptibility=='low'
    assert damage.amine_figure_susceptibility(request(stress_relieved=True)).outputs.susceptibility=='none'


def test_ffs_and_qualification():
    with pytest.raises(DomainError) as caught:
        damage.amine_figure_susceptibility(request(unrepaired_cracks=True,applicability_basis=' '))
    assert caught.value.code=='ffs_required'
    with pytest.raises(DomainError):
        damage.amine_figure_susceptibility(request(applicability_basis=' '))


def test_figure_to_df_known_result():
    r=damage.amine_figure_assessment(damage.AmineFigureAssessmentInput(
        screening=dict(material='carbon_steel',acid_gas_treating_amine_present=True,screening_basis='Qualified exposure'),
        service=request(heat_traced=True),years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified amine-specific inspection age and coverage')).outputs
    assert r.susceptibility=='medium' and r.severity_index==100 and r.base_damage_factor==5.
    assert r.damage_factor==pytest.approx(5*2**1.1)


@pytest.mark.parametrize('group,threshold,below,at,above',[
    ('mea_or_dipa',100.,'low','medium','medium'),
    ('mea_or_dipa',180.,'medium','medium','high'),
    ('dea',140.,'none','low','low'),
    ('dea',180.,'low','low','medium'),
    ('other_treating_amine',180.,'none','none','low')])
def test_adjacent_representable_kelvin_boundary_values(group,threshold,below,at,above):
    boundary=(threshold-32)*5/9+273.15
    for temperature,expected in [(math.nextafter(boundary,-math.inf),below),(boundary,at),
            (math.nextafter(boundary,math.inf),above)]:
        result=damage.amine_figure_susceptibility(request(amine_group=group,maximum_metal_temperature_k=temperature)).outputs
        assert result.susceptibility==expected


def test_published_typed_example():
    result=runpy.run_path('examples/amine_figure_assessment.py')['main']()
    assert result.decision_branch=='dea_lean' and result.lean_exposure_selected
