import pytest
from api581 import DomainError
from api581.api import damage


@pytest.mark.parametrize('material',['carbon_steel','low_alloy_steel','other_material'])
@pytest.mark.parametrize('present',[False,True])
def test_material_exposure_matrix(material,present):
    r=damage.amine_cracking_screening(damage.AmineCrackingScreeningInput(material=material,
        acid_gas_treating_amine_present=present,screening_basis='Qualified treating-amine exposure')).outputs
    assert r.evaluate_amine_cracking==(material!='other_material' and present)


def request(**changes):
    return damage.AmineCrackingScreenedAssessmentInput(**(dict(
        screening=dict(material='carbon_steel',acid_gas_treating_amine_present=True,screening_basis='Qualified exposure'),
        cracking=dict(susceptibility='low',confirmed_cracking=False,unrepaired_cracks=False,
            years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0)),
        susceptibility_and_inspection_basis='Independently qualified Figure7.1/expert susceptibility and eligible A inspection')|changes))


def test_known_svi_base_and_age_and_confirmed_override():
    result=damage.amine_cracking_screened_assessment(request()).outputs
    assert result.severity_index==10 and result.base_damage_factor==1.
    assert result.damage_factor==pytest.approx(2**1.1)
    cracking=request().cracking.model_dump()|dict(confirmed_cracking=True)
    high=damage.amine_cracking_screened_assessment(request(cracking=cracking)).outputs
    assert high.effective_susceptibility=='high' and high.severity_index==1000
    assert high.base_damage_factor==50.


def test_ffs_precedes_conflicting_screen_and_qualification():
    values=request().model_dump()
    values['cracking']['unrepaired_cracks']=True
    values['screening']['acid_gas_treating_amine_present']=False
    values['susceptibility_and_inspection_basis']=' '
    with pytest.raises(DomainError) as caught:
        damage.amine_cracking_screened_assessment(damage.AmineCrackingScreenedAssessmentInput(**values))
    assert caught.value.code=='ffs_required'


def test_screenout_is_not_a_zero_damage_factor():
    values=request().screening.model_dump()|dict(acid_gas_treating_amine_present=False)
    with pytest.raises(DomainError) as caught:
        damage.amine_cracking_screened_assessment(request(screening=values))
    assert caught.value.code=='amine_outside_screen'


def test_blank_qualification_rejected():
    with pytest.raises(DomainError):
        damage.amine_cracking_screened_assessment(request(susceptibility_and_inspection_basis=' '))
