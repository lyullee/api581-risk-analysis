"""Printed reference anchors, credit logic, table trends and composition checks."""
import pytest
from api581 import DomainError
from api581.api import damage

KSI_PA = 6894757.293168


@pytest.mark.parametrize("material,yield_ksi,curve,temp_f", [
    ("carbon_steel",30,"A",104), ("carbon_steel",30,"D",2),
    ("carbon_steel",40,"B",40), ("carbon_steel",50,"D",-39),
    ("low_alloy_steel",30,"A",124), ("low_alloy_steel",40,"C",16),
    ("low_alloy_steel",58,"B",29), ("low_alloy_steel",80,"D",-51),
])
def test_reference_us_table_anchors_converted_to_kelvin(material,yield_ksi,curve,temp_f):
    result = damage.brittle_reference_temperature(damage.BrittleReferenceTemperatureInput(
        material_group=material, minimum_yield_strength_pa=yield_ksi*KSI_PA,
        exemption_curve=curve, interpolation="exact"))
    assert result.outputs.reference_temperature_k == pytest.approx((temp_f-32)*5/9+273.15)
    assert result.outputs.table_basis == "20.3_US_converted_to_SI"


def test_reference_linear_and_unavailable_domain():
    inputs = dict(material_group="carbon_steel", minimum_yield_strength_pa=31*KSI_PA, exemption_curve="A")
    result = damage.brittle_reference_temperature(damage.BrittleReferenceTemperatureInput(**inputs,interpolation="linear"))
    assert result.outputs.reference_temperature_k == pytest.approx((100.5-32)*5/9+273.15)
    with pytest.raises(DomainError) as error:
        damage.brittle_reference_temperature(damage.BrittleReferenceTemperatureInput(**inputs,interpolation="exact"))
    assert error.value.code == "interpolation_required"
    for outside in (29,51):
        with pytest.raises(DomainError):
            damage.brittle_reference_temperature(damage.BrittleReferenceTemperatureInput(
                **{**inputs, "minimum_yield_strength_pa":outside*KSI_PA}, interpolation="linear"))


def service(**updates):
    return damage.BrittleServiceFactorInput(**{
        "component_thickness_m":.0254, "nominal_uncorroded_thickness_m":.0254,
        "equipment_type":"pressure_vessel", "p1_or_p3_steel":True, "design_temperature_k":616.15,
        "construction_code_satisfied":True, "stable_conditions_no_more_severe_future":True,
        "cet_at_mawp_k":244.15, "cyclic_fatigue_or_vibration_design_service":False,
        "environmental_cracking":False, "shock_chilling":False, **updates})


@pytest.mark.parametrize("field,value", [
    ("p1_or_p3_steel",False), ("design_temperature_k",616.16),
    ("construction_code_satisfied",False), ("stable_conditions_no_more_severe_future",False),
    ("cet_at_mawp_k",244.14), ("nominal_uncorroded_thickness_m",.05081),
    ("cyclic_fatigue_or_vibration_design_service",True), ("environmental_cracking",True), ("shock_chilling",True),
])
def test_each_service_requirement_is_required_unless_independent_thin_credit(field,value):
    assert damage.brittle_service_factor(service()).outputs.service_experience_factor == .01
    assert damage.brittle_service_factor(service(**{field:value})).outputs.service_experience_factor == 1
    thin = damage.brittle_service_factor(service(**{field:value,"component_thickness_m":.0127}))
    assert thin.outputs.service_experience_factor == .01
    assert thin.outputs.thin_component_credit


def test_piping_has_distinct_cet_threshold_and_thin_limit_is_inclusive():
    assert damage.brittle_service_factor(service(equipment_type="piping", cet_at_mawp_k=169.15)).outputs.service_experience_factor == .01
    assert damage.brittle_service_factor(service(equipment_type="piping", cet_at_mawp_k=169.14)).outputs.service_experience_factor == 1
    assert damage.brittle_service_factor(service(component_thickness_m=.01270001, shock_chilling=True)).outputs.service_experience_factor == 1


@pytest.mark.parametrize("pwht,delta,thickness_mm,df", [
    (False,56,101.6,1.2), (False,44,38.1,.8), (False,0,6.4,.9),
    (False,0,50.8,424), (False,-33,63.5,2479), (False,-56,101.6,5000),
    (True,56,101.6,0), (True,44,101.6,.2), (True,11,25.4,.6),
    (True,0,50.8,6), (True,-33,63.5,153), (True,-56,101.6,962),
])
def test_brittle_base_printed_si_anchors(pwht,delta,thickness_mm,df):
    out = damage.brittle_base(damage.BrittleBaseInput(component_thickness_m=thickness_mm/1000,
        cet_minus_reference_k=delta, post_weld_heat_treated=pwht, interpolation="exact")).outputs
    assert out.base_damage_factor == df
    assert out.table == ("20.5M" if pwht else "20.4M")


def test_bilinear_interpolation_uses_df_not_logarithm():
    # Four printed non-PWHT cells: (delta=0,11)*(thickness=25.4,38.1): 39,175,10,49.
    result = damage.brittle_base(damage.BrittleBaseInput(component_thickness_m=.03175,
        cet_minus_reference_k=5.5, post_weld_heat_treated=False, interpolation="linear"))
    assert result.outputs.base_damage_factor == pytest.approx((39+175+10+49)/4)
    with pytest.raises(DomainError) as error:
        damage.brittle_base(damage.BrittleBaseInput(component_thickness_m=.03175,
            cet_minus_reference_k=5.5, post_weld_heat_treated=False, interpolation="exact"))
    assert error.value.code == "interpolation_required"


@pytest.mark.parametrize("delta,thickness", [(-56.01,.0254),(56.01,.0254),(0,.00639),(0,.10161)])
def test_no_brittle_table_extrapolation(delta,thickness):
    with pytest.raises(DomainError):
        damage.brittle_base(damage.BrittleBaseInput(component_thickness_m=thickness,
            cet_minus_reference_k=delta,post_weld_heat_treated=False,interpolation="linear"))


def test_heat_treatment_and_warming_never_increase_base_df():
    # Cross-grid physical trends detect row reversal and heat-treatment selection errors.
    for thickness in (.0064,.0127,.0254,.0508,.1016):
        previous = None
        for delta in (-56,-44,-33,-22,-11,0,11,22,33,44,56):
            values = [damage.brittle_base(damage.BrittleBaseInput(component_thickness_m=thickness,
                cet_minus_reference_k=delta,post_weld_heat_treated=pwht,interpolation="exact")).outputs.base_damage_factor
                for pwht in (False,True)]
            assert values[1] <= values[0]
            if previous is not None:
                assert all(new <= old for new,old in zip(values,previous))
            previous = values


def test_brittle_full_calculation_reference_to_service_credit():
    # Table20.3: carbon, 40ksi, B => 40F => 277.59444K.
    reference_k = (40-32)*5/9+273.15
    result = damage.brittle_fracture(damage.BrittleFractureInput(
        reference=damage.BrittleReferenceTemperatureInput(material_group="carbon_steel",
            minimum_yield_strength_pa=40*KSI_PA,exemption_curve="B",interpolation="exact"),
        service=service(component_thickness_m=.0508, nominal_uncorroded_thickness_m=.0508),
        critical_exposure_temperature_k=reference_k,post_weld_heat_treated=False,interpolation="exact"))
    assert result.outputs.cet_minus_reference_k == pytest.approx(0)
    assert result.outputs.base_damage_factor == 424
    assert result.outputs.damage_factor == pytest.approx(4.24)
    assert result.references and result.limitations


@pytest.mark.parametrize("delta,df", [(-56,1381),(-44,1216),(-33,1022),(-22,806),(-11,581),
    (0,371),(11,200),(22,87),(33,30),(44,8),(56,2),(56.001,0),(100,0)])
def test_885f_table_and_open_upper_row(delta,df):
    result = damage.embrittlement_885f(damage.Embrittlement885fInput(
        minimum_evaluation_temperature_k=301.15+delta, interpolation="exact"))
    assert result.outputs.damage_factor == df
    assert result.outputs.reference_temperature_k == 301.15


def test_885f_custom_reference_interpolation_and_lower_rejection():
    assert damage.embrittlement_885f(damage.Embrittlement885fInput(minimum_evaluation_temperature_k=310,
        reference_temperature_k=304.5, interpolation="linear")).outputs.damage_factor == pytest.approx((371+200)/2)
    with pytest.raises(DomainError):
        damage.embrittlement_885f(damage.Embrittlement885fInput(minimum_evaluation_temperature_k=245.14, interpolation="linear"))


@pytest.mark.parametrize("fraction,category", [(.010001,"low"),(.04999,"low"),(.05,"medium"),(.09999,"medium"),(.1,"high"),(1,"high")])
def test_sigma_content_boundaries(fraction,category):
    assert damage.sigma_content(damage.SigmaContentInput(sigma_fraction=fraction)).outputs.sigma_category == category


@pytest.mark.parametrize("fraction", [0,.005,.01])
def test_unresolved_low_sigma_has_no_invented_zero(fraction):
    with pytest.raises(DomainError) as error:
        damage.sigma_content(damage.SigmaContentInput(sigma_fraction=fraction))
    assert error.value.code == "unresolved_applicability"


@pytest.mark.parametrize("temp_c,category,df", [(-46,"low",1.1),(-18,"medium",20),(38,"high",4196),
    (66,"high",3871),(93,"medium",3),(204,"high",1333),(427,"medium",.2),(649,"high",18)])
def test_sigma_si_table_anchors(temp_c,category,df):
    assert damage.sigma_embrittlement(damage.SigmaEmbrittlementInput(evaluation_temperature_k=temp_c+273.15,
        sigma_category=category,interpolation="exact")).outputs.damage_factor == df


def test_sigma_interpolation_and_no_extrapolation():
    assert damage.sigma_embrittlement(damage.SigmaEmbrittlementInput(evaluation_temperature_k=533.15,
        sigma_category="high",interpolation="linear")).outputs.damage_factor == pytest.approx((1333+481)/2)
    for temp_c in (-46.001,649.001):
        with pytest.raises(DomainError):
            damage.sigma_embrittlement(damage.SigmaEmbrittlementInput(evaluation_temperature_k=temp_c+273.15,
                sigma_category="high",interpolation="linear"))


def test_sigma_categories_order_and_temperature_trend():
    previous = None
    for temp_c in (-46,-18,10,38,66,93,204,316,427,538,649):
        values = [damage.sigma_embrittlement(damage.SigmaEmbrittlementInput(evaluation_temperature_k=temp_c+273.15,
            sigma_category=category,interpolation="exact")).outputs.damage_factor for category in ("low","medium","high")]
        assert values == sorted(values)
        if previous:
            assert all(new <= old for new,old in zip(values,previous))
        previous=values
