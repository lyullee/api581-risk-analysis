import pytest
from api581 import DomainError
from api581.api import damage


@pytest.mark.parametrize('material',['carbon_steel','low_alloy_steel','other_material'])
@pytest.mark.parametrize('water',[False,True])
@pytest.mark.parametrize('h2s',[False,True])
def test_source_material_water_h2s_screen(material,water,h2s):
    r=damage.ssc_screening(damage.SscScreeningInput(material=material,water_present=water,h2s_present=h2s,
        exposure_basis='Qualified local/current-process wet-H2S fixture')).outputs
    assert r.evaluate_ssc==(material!='other_material' and water and h2s)
    if r.evaluate_ssc:
        assert r.screening_reason=='evaluate'


def test_blank_exposure_qualification_rejected():
    with pytest.raises(DomainError):
        damage.ssc_screening(damage.SscScreeningInput(material='carbon_steel',water_present=True,h2s_present=True,
            exposure_basis=' '))
