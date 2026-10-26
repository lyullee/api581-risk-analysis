import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.AcsccQualifiedAssessmentInput(**(dict(screening=dict(material='carbon_steel',water_present=True,water_ph=8.5,
        fccu_feed_sulfur_reduced=False,fccu_feed_nitrogen_increased=False,screening_basis='Qualified alkaline-water exposure'),
        water=dict(water_ph=8.5,carbonate_ppm=100.,pwht=False,carbonate_measurement_basis='Qualified carbonate-specific analysis',
            traditional_alkalinity_only=False,service_fabrication_basis='Qualified material/PWHT fixture'),
        confirmed_cracking=False,unrepaired_cracks=False,years_since_qualifying_inspection=2.,
        inspections=dict(a=1,b=0,c=0,d=0),inspection_basis='Qualified ACSCC-specific inspection age and coverage')|changes))


def test_water_to_df_known_result_and_pwht_override_by_cracking():
    result=damage.acscc_qualified_assessment(request()).outputs
    assert result.susceptibility=='high' and result.severity_index==1000 and result.base_damage_factor==50.
    assert result.damage_factor==pytest.approx(50*2**1.1)
    water=request().water.model_dump()|dict(pwht=True)
    assert damage.acscc_qualified_assessment(request(water=water)).outputs.damage_factor==0.
    cracked=damage.acscc_qualified_assessment(request(water=water,confirmed_cracking=True)).outputs
    assert cracked.susceptibility=='none' and cracked.effective_susceptibility=='high' and cracked.base_damage_factor==50.


def test_ph_consistency_and_feed_trigger_without_water():
    water=request().water.model_dump()|dict(water_ph=7.7)
    with pytest.raises(DomainError) as caught:
        damage.acscc_qualified_assessment(request(water=water))
    assert caught.value.code=='acscc_ph_mismatch'
    screen=request().screening.model_dump()|dict(water_present=False,water_ph=None,fccu_feed_sulfur_reduced=True)
    with pytest.raises(DomainError) as caught:
        damage.acscc_qualified_assessment(request(screening=screen))
    assert caught.value.code=='acscc_water_required'


def test_unrepaired_ffs_precedes_other_conflicts():
    with pytest.raises(DomainError) as caught:
        damage.acscc_qualified_assessment(request(unrepaired_cracks=True,inspection_basis=' '))
    assert caught.value.code=='ffs_required'
