import math
import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.ClsccScreeningInput(**(dict(material='austenitic_stainless_steel',actual_or_potential_wet_chloride_exposure=True,
        operating_temperature_k=350.,temperature_basis='printed_si',exposure_basis='Qualified upset/hydrotest/drift exposure review')|changes))


@pytest.mark.parametrize('basis,threshold',[('printed_si',311.15),('printed_us_converted',(100.-32)*5/9+273.15)])
def test_strict_temperature_boundaries(basis,threshold):
    for temperature,expected in [(math.nextafter(threshold,-math.inf),False),(threshold,False),(math.nextafter(threshold,math.inf),True)]:
        r=damage.clscc_screening(request(temperature_basis=basis,operating_temperature_k=temperature)).outputs
        assert r.evaluate_clscc==expected and r.screening_temperature_threshold_k==threshold


@pytest.mark.parametrize('material',['austenitic_stainless_steel','other_material'])
@pytest.mark.parametrize('exposed',[False,True])
def test_material_and_potential_exposure(material,exposed):
    r=damage.clscc_screening(request(material=material,actual_or_potential_wet_chloride_exposure=exposed)).outputs
    assert r.evaluate_clscc==(material=='austenitic_stainless_steel' and exposed)


def test_printed_si_us_rounding_difference_preserved():
    assert not damage.clscc_screening(request(operating_temperature_k=311.)).outputs.evaluate_clscc
    assert damage.clscc_screening(request(operating_temperature_k=311.,temperature_basis='printed_us_converted')).outputs.evaluate_clscc


def test_exposure_review_required():
    with pytest.raises(DomainError):
        damage.clscc_screening(request(exposure_basis=' '))


@pytest.mark.parametrize('fahrenheit,expected', [
    (100., 'low'), (150., 'medium'), (200., 'high'), (300., 'high'), (301., 'high')])
def test_us_susceptibility_uses_printed_temperature_rows(fahrenheit, expected):
    result = damage.clscc_susceptibility(damage.ClsccSusceptibilityInput(
        temperature_k=(fahrenheit - 32.) * 5. / 9. + 273.15,
        temperature_basis='printed_us_converted', ph_over_10=False,
        chloride_band_ppm='101-1000')).outputs
    assert result.susceptibility == expected


def test_si_overlap_still_rejected_but_us_200f_is_defined():
    with pytest.raises(DomainError) as caught:
        damage.clscc_susceptibility(damage.ClsccSusceptibilityInput(
            temperature_k=366.15, temperature_basis='printed_si', ph_over_10=True,
            chloride_band_ppm='1-10'))
    assert caught.value.code == 'ambiguous_source'
    result = damage.clscc_susceptibility(damage.ClsccSusceptibilityInput(
        temperature_k=(200. - 32.) * 5. / 9. + 273.15,
        temperature_basis='printed_us_converted', ph_over_10=True,
        chloride_band_ppm='1-10')).outputs
    assert result.susceptibility == 'low'
