import pytest
from api581 import DomainError
from api581.api import damage


@pytest.mark.parametrize('material',['austenitic_stainless_steel','nickel_based_alloy','other_material'])
@pytest.mark.parametrize('exposure',[False,True])
def test_material_sulfur_matrix(material,exposure):
    output=damage.pascc_screening(damage.PasccScreeningInput(material=material,sulfur_bearing_compounds_exposure=exposure,
        exposure_basis='Qualified alloy and sulfur exposure including shutdown history')).outputs
    assert output.evaluate_pascc==(material!='other_material' and exposure)


def test_qualification_required():
    with pytest.raises(DomainError):
        damage.pascc_screening(damage.PasccScreeningInput(material='nickel_based_alloy',sulfur_bearing_compounds_exposure=True,
            exposure_basis=' '))
