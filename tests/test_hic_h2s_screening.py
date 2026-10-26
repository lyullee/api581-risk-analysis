import pytest
from api581 import DomainError
from api581.api import damage


@pytest.mark.parametrize('material',['carbon_steel','low_alloy_steel','other_material'])
@pytest.mark.parametrize('water',[False,True])
@pytest.mark.parametrize('h2s',[False,True])
def test_hic_specific_material_exposure_screen(material,water,h2s):
    result=damage.hic_h2s_screening(damage.HicH2sScreeningInput(material=material,water_present=water,
        h2s_present=h2s,exposure_basis='Qualified HIC/SOHIC wet-H2S service')).outputs
    assert result.evaluate_hic_sohic_h2s==(material!='other_material' and water and h2s)
    assert 'evaluate_ssc' not in result.model_dump()


def test_hic_screen_exposure_basis_required():
    with pytest.raises(DomainError):
        damage.hic_h2s_screening(damage.HicH2sScreeningInput(material='carbon_steel',water_present=True,
            h2s_present=True,exposure_basis=' '))
