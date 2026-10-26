import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.AcsccScreeningInput(**(dict(material='carbon_steel',water_present=True,water_ph=7.5,
        fccu_feed_sulfur_reduced=False,fccu_feed_nitrogen_increased=False,screening_basis='Qualified service and FCCU feed review')|changes))


@pytest.mark.parametrize('material',['carbon_steel','low_alloy_steel','other_material'])
@pytest.mark.parametrize('ph',[7.4,7.5,7.6])
def test_material_ph_strict_trigger(material,ph):
    r=damage.acscc_screening(request(material=material,water_ph=ph)).outputs
    assert r.evaluate_acscc==(material!='other_material' and ph>7.5)


@pytest.mark.parametrize('field',['fccu_feed_sulfur_reduced','fccu_feed_nitrogen_increased'])
def test_independent_feed_review_trigger(field):
    r=damage.acscc_screening(request(water_present=False,water_ph=None,**{field:True})).outputs
    assert r.evaluate_acscc and r.evaluation_triggers==[field]


@pytest.mark.parametrize('changes',[dict(water_ph=None),dict(water_present=False),dict(screening_basis=' ')])
def test_missing_conflicting_or_unqualified_water_data(changes):
    with pytest.raises(DomainError):
        damage.acscc_screening(request(**changes))
