import pytest
from api581 import DomainError
from api581.api import damage


def request(**changes):
    return damage.ClsccQualifiedAssessmentInput(**(dict(screening=dict(material='austenitic_stainless_steel',
        actual_or_potential_wet_chloride_exposure=True,operating_temperature_k=323.15,temperature_basis='printed_si',
        exposure_basis='Qualified wet-chloride review'),ph_over_10=False,chloride_band_ppm='11-100',
        chemistry_basis='Qualified local chloride ion band and pH fixture',confirmed_cracking=False,unrepaired_cracks=False,
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified CLSCC inspection period/coverage')|changes))


def test_known_si_table_to_df():
    r=damage.clscc_qualified_assessment(request()).outputs
    assert r.susceptibility=='medium' and r.severity_index==500 and r.base_damage_factor==25.
    assert r.damage_factor==pytest.approx(25*2**1.1)
    high=damage.clscc_qualified_assessment(request(confirmed_cracking=True)).outputs
    assert high.effective_susceptibility=='high' and high.base_damage_factor==250.


@pytest.mark.parametrize('change,code',[(dict(operating_temperature_k=311.15),'clscc_outside_screen'),
    (dict(actual_or_potential_wet_chloride_exposure=False),'clscc_outside_screen')])
def test_incompatible_screen_and_table_rejected(change,code):
    with pytest.raises(DomainError) as caught:
        damage.clscc_qualified_assessment(request(screening=request().screening.model_dump()|change))
    assert caught.value.code==code


def test_source_overlap_propagates_and_ffs_has_priority():
    with pytest.raises(DomainError) as caught:
        damage.clscc_qualified_assessment(request(ph_over_10=True,
            screening=request().screening.model_dump()|dict(operating_temperature_k=366.15)))
    assert caught.value.code=='ambiguous_source'
    with pytest.raises(DomainError) as caught:
        damage.clscc_qualified_assessment(request(unrepaired_cracks=True,chemistry_basis=' '))
    assert caught.value.code=='ffs_required'


def test_us_table_is_selected_without_si_reinterpretation():
    r = damage.clscc_qualified_assessment(request(
        screening=request().screening.model_dump() | dict(
            temperature_basis='printed_us_converted',
            operating_temperature_k=(200. - 32.) * 5. / 9. + 273.15),
        ph_over_10=True,
        chloride_band_ppm='1-10',
        years_since_qualifying_inspection=0., inspections=dict(a=1,b=0,c=0,d=0))).outputs
    # 200 F / pH>10 / 1-10 ppm is the low US-table cell; the corresponding
    # SI boundary is an ambiguous 93 C source overlap.
    assert r.selected_temperature_basis == 'printed_us_converted'
    assert r.susceptibility == 'low'
    assert r.base_damage_factor == 3.
