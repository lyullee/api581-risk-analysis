import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage, frequency


def test_j_and_xbar_composition_units():
    # wt% Si=.3 Mn=.5 P=.01 Sn=.02: .8*.03*10000 = 240.
    j = damage.temper_j_factor(damage.TemperJFactorInput(silicon_weight_percent=.3,
        manganese_weight_percent=.5,phosphorus_weight_percent=.01,tin_weight_percent=.02))
    assert j.outputs.j_factor == pytest.approx(240)
    # wt% P=.01 Sb=.002 Sn=.005 As=.001: (.1+.01+.02+.001)*100 = 13.1.
    xbar = damage.temper_xbar(damage.TemperXbarInput(phosphorus_weight_percent=.01,
        antimony_weight_percent=.002,tin_weight_percent=.005,arsenic_weight_percent=.001))
    assert xbar.outputs.xbar_factor == pytest.approx(13.1)


def test_composition_mass_balance():
    with pytest.raises(ValidationError):
        damage.TemperJFactorInput(silicon_weight_percent=60,manganese_weight_percent=41,
            phosphorus_weight_percent=0,tin_weight_percent=0)
    with pytest.raises(ValidationError):
        damage.TemperXbarInput(phosphorus_weight_percent=40,antimony_weight_percent=40,
            tin_weight_percent=30,arsenic_weight_percent=0)


def test_xbar_temperature_difference_and_invalid_correlation_result():
    # xbar=20: -87.335 + 228.74 - 58.88 = 82.525 Celsius difference = 82.525 K.
    result = damage.temper_xbar_shift(damage.TemperXbarShiftInput(xbar_factor=20))
    assert result.outputs.delta_fatt_k == pytest.approx(82.525)
    for xbar in (0,100):
        with pytest.raises(DomainError) as error:
            damage.temper_xbar_shift(damage.TemperXbarShiftInput(xbar_factor=xbar))
        assert error.value.code == "outside_correlation_domain"


@pytest.mark.parametrize("year,generation,c,f", [
    (1965,1,177,350),(1972,1,177,350),(1973,2,149,300),(1980,2,149,300),
    (1981,3,121,250),(1987,3,121,250),(1989,4,66,150),(2026,4,66,150)])
def test_generation_shift_explicit_source_basis(year,generation,c,f):
    result_c = damage.temper_generation_shift(damage.TemperGenerationShiftInput(fabrication_year=year,source_basis="printed_C"))
    result_f = damage.temper_generation_shift(damage.TemperGenerationShiftInput(fabrication_year=year,source_basis="printed_F_difference_converted"))
    assert result_c.outputs.generation == generation
    assert result_c.outputs.delta_fatt_k == c
    assert result_f.outputs.delta_fatt_k == pytest.approx(f*5/9)
    assert result_c.outputs.source_basis != result_f.outputs.source_basis
    assert result_c.input_hash != result_f.input_hash


def test_generation_gaps_and_no_implicit_unit_selection():
    with pytest.raises(DomainError) as error:
        damage.temper_generation_shift(damage.TemperGenerationShiftInput(fabrication_year=1988,source_basis="printed_C"))
    assert error.value.code == "unresolved_applicability"
    with pytest.raises(ValidationError):
        damage.TemperGenerationShiftInput(fabrication_year=1964,source_basis="printed_C")
    with pytest.raises(ValidationError):
        damage.TemperGenerationShiftInput(fabrication_year=2000)


def test_temper_full_damage_has_no_brittle_service_credit():
    ref = damage.BrittleReferenceTemperatureInput(material_group="low_alloy_steel",
        minimum_yield_strength_pa=40*6894757.293168,exemption_curve="A",interpolation="exact")
    reference_k=(92-32)*5/9+273.15
    result=damage.temper_embrittlement(damage.TemperEmbrittlementInput(reference=ref,
        minimum_pressurization_temperature_k=reference_k+20,delta_fatt_k=20,
        component_thickness_m=.0508,post_weld_heat_treated=True,interpolation="exact"))
    assert result.outputs.reference_temperature_k == pytest.approx(reference_k)
    assert result.outputs.shifted_reference_temperature_k == pytest.approx(reference_k+20)
    assert result.outputs.minimum_minus_shifted_reference_k == pytest.approx(0)
    assert result.outputs.damage_factor == 6  # Table 20.5M; no .01 service factor.
    assert result.outputs.table == "20.5M"
    with pytest.raises(DomainError):
        damage.temper_embrittlement(damage.TemperEmbrittlementInput(
            reference=ref.model_copy(update={"material_group":"carbon_steel"}),
            minimum_pressurization_temperature_k=reference_k+20,delta_fatt_k=20,
            component_thickness_m=.0508,post_weld_heat_treated=True,interpolation="exact"))


def test_brittle_family_integrates_into_frequency():
    # Existing governing equation: max(brittle+temper, 885F, sigma), inactive <=1 excluded.
    combined=damage.combine(damage.CombineInput(thinning=0,external=[],scc=[],htha=0,fatigue=0,
        brittle_fracture=4.24,temper_embrittlement=6,embrittlement_885f=2,sigma_embrittlement=.6,
        thinning_external_distribution="local"))
    assert combined.outputs.governing_brittle == pytest.approx(10.24)
    assert combined.outputs.total_damage_factor == pytest.approx(10.24)
    gff=frequency.generic(frequency.GenericInput(component_type="PIPE-8"))
    result=frequency.adjusted(frequency.AdjustedInput(generic_frequency_per_year=gff.outputs.total_per_year,
        total_damage_factor=combined.outputs.total_damage_factor,management_factor=1))
    assert result.outputs.annual_failure_frequency == pytest.approx(3.06e-5*10.24)
