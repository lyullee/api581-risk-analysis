"""AST floor source tables, conditional credit and two-sided rate composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import tank


def fixture(**changes):
    return tank.BottomCorrosionAssessmentInput(**(dict(material="carbon_steel",applicability_basis="AST carbon-steel floor fixture",
        soil_base_corrosion_rate_m_year=.00013,product_base_corrosion_rate_m_year=.00005,
        soil_base_rate_source="2016 SI fallback under reference conditions",product_base_rate_source="2016 SI fallback under reference conditions",
        bottom_type="single_bottom",soil_resistivity_ohm_m=50.,pad=dict(pad_type="continuous_asphalt"),
        drainage=dict(drainage_category="storm_water_collects"),
        cathodic_protection=dict(protection_category="present_per_api651",effectiveness_verified_by_high_level_inspection=True,verification_basis="Qualified inspection fixture"),
        temperature=dict(highest_operating_temperature_k=323.15,threshold_basis="printed_si"),
        product_condition=dict(product_condition="wet"),steam_coil=dict(steam_coil_present=True),
        water_draw=dict(water_draw_practice="weekly"),product_distribution="general",minimum_rate_policy="apply_2_mpy_recommendation")|changes))


@pytest.mark.parametrize("side,si,us",[("soil",.13,5.),("product",.05,2.)])
@pytest.mark.parametrize("basis",["printed_si","printed_us_mpy"])
def test_base_unit_pairs(side,si,us,basis):
    r=tank.bottom_base_corrosion_rate(tank.BottomBaseCorrosionRateInput(side=side,unit_basis=basis)).outputs
    assert r.base_corrosion_rate_m_year == pytest.approx(si/1000 if basis == "printed_si" else us*.0000254)
    assert r.printed_si_rate_mm_year==si and r.printed_us_rate_mpy==us


@pytest.mark.parametrize("v,f",[(1,1.5),(5,1.25),(15,1),(50,.83),(100,.83),(101,.66)])
def test_ast_resistivity(v,f):
    r=tank.bottom_soil_resistivity_factor(tank.BottomSoilResistivityFactorInput(release_prevention_barrier=False,soil_resistivity_ohm_m=v)).outputs
    assert r.resistivity_factor==f


@pytest.mark.parametrize("v,lo,hi",[(10,1.25,1),(20,1,.83)])
def test_shared_resistivity(v,lo,hi):
    with pytest.raises(DomainError):
        tank.bottom_soil_resistivity_factor(tank.BottomSoilResistivityFactorInput(release_prevention_barrier=False,soil_resistivity_ohm_m=v))
    for basis,f in [("lower_resistivity_interval",lo),("higher_resistivity_interval",hi)]:
        r=tank.bottom_soil_resistivity_factor(tank.BottomSoilResistivityFactorInput(release_prevention_barrier=False,soil_resistivity_ohm_m=v,shared_boundary_basis=basis)).outputs
        assert r.resistivity_factor==f


@pytest.mark.parametrize("rpb,v,reason",[(True,1,"rpb"),(True,None,"rpb"),(False,None,"unknown_assume_moderate")])
def test_unknown_and_rpb(rpb,v,reason):
    r=tank.bottom_soil_resistivity_factor(tank.BottomSoilResistivityFactorInput(release_prevention_barrier=rpb,soil_resistivity_ohm_m=v)).outputs
    assert r.resistivity_factor==1 and r.selection_reason==reason


@pytest.mark.parametrize("category,f",[("soil_high_salt",1.5),("crushed_limestone",1.4),("native_soil",1.3),("construction_grade_sand",1.15),
    ("continuous_asphalt",1),("continuous_concrete",1),("oil_sand",.7),("high_resistivity_low_chloride_sand",.7)])
def test_pad_table(category,f):
    assert tank.bottom_pad_factor(tank.BottomPadFactorInput(pad_type=category)).outputs.pad_factor==f


@pytest.mark.parametrize("category,f",[("one_third_frequently_underwater",3),("storm_water_collects",2),("no_storm_water_collects",1)])
def test_drainage_table(category,f):
    assert tank.bottom_drainage_factor(tank.BottomDrainageFactorInput(drainage_category=category)).outputs.drainage_factor==f


@pytest.mark.parametrize("category,f",[("none",1),("present_not_per_api651",.66),("present_per_api651",.33)])
def test_cp_credit_gate(category,f):
    r=tank.bottom_cp_factor(tank.BottomCpFactorInput(protection_category=category,effectiveness_verified_by_high_level_inspection=False)).outputs
    assert r.nominal_table_factor==f and r.cathodic_protection_factor==1 and not r.credit_applied
    if category!="none":
        r=tank.bottom_cp_factor(tank.BottomCpFactorInput(protection_category=category,effectiveness_verified_by_high_level_inspection=True,verification_basis="High Level fixture")).outputs
        assert r.cathodic_protection_factor==f and r.credit_applied


@pytest.mark.parametrize("category,verified,basis",[("none",True,"inspection"),("present_per_api651",True,None),("present_per_api651",True," "),("present_per_api651",False,"inspection")])
def test_cp_contradictions(category,verified,basis):
    with pytest.raises(DomainError):
        tank.bottom_cp_factor(tank.BottomCpFactorInput(protection_category=category,effectiveness_verified_by_high_level_inspection=verified,verification_basis=basis))


@pytest.mark.parametrize("kind,f",[("rpb_not_per_api650",1.4),("rpb_per_api650",1),("single_bottom",1)])
def test_bottom_type(kind,f):
    assert tank.bottom_type_factor(tank.BottomTypeFactorInput(bottom_type=kind)).outputs.bottom_type_factor==f


@pytest.mark.parametrize("basis,thresholds",[("printed_si",[c+273.15 for c in (24,66,93,121)]),
    ("printed_us_converted",[(f-32)*5/9+273.15 for f in (75,150,200,250)])])
def test_every_temperature_boundary(basis,thresholds):
    factors=[1,1.1,1.3,1.4,1]
    for i,b in enumerate(thresholds):
        for t,f in [(math.nextafter(b,-math.inf),factors[i]),(b,factors[i]),(math.nextafter(b,math.inf),factors[i+1])]:
            r=tank.bottom_temperature_factor(tank.BottomTemperatureFactorInput(highest_operating_temperature_k=t,threshold_basis=basis)).outputs
            assert r.temperature_factor==f


def test_product_tables():
    for condition,f in [("wet",2.5),("dry",1)]:
        assert tank.bottom_product_condition_factor(tank.BottomProductConditionFactorInput(product_condition=condition)).outputs.product_condition_factor==f
    for present,f in [(True,1.15),(False,1)]:
        assert tank.bottom_steam_coil_factor(tank.BottomSteamCoilFactorInput(steam_coil_present=present)).outputs.steam_coil_factor==f
    for practice,f in [("none_or_not_regular",1),("weekly",.7),("after_every_receipt",.7)]:
        assert tank.bottom_water_draw_factor(tank.BottomWaterDrawFactorInput(water_draw_practice=practice)).outputs.water_draw_factor==f


@pytest.mark.parametrize("distribution,expected",[("general",.0003),("local",.0002)])
def test_combination_rule(distribution,expected):
    r=tank.bottom_corrosion_rate_combine(tank.BottomCorrosionRateCombineInput(soil_corrosion_rate_m_year=.0001,
        product_corrosion_rate_m_year=.0002,product_distribution=distribution,minimum_rate_policy="apply_2_mpy_recommendation")).outputs
    assert r.combined_corrosion_rate_m_year==pytest.approx(expected) and not r.minimum_applied


@pytest.mark.parametrize("policy,basis,expected",[("apply_2_mpy_recommendation",None,.0000508),("qualified_no_floor","Owner qualified measured rates",0)])
def test_exact_two_mpy_floor_and_bypass(policy,basis,expected):
    r=tank.bottom_corrosion_rate_combine(tank.BottomCorrosionRateCombineInput(soil_corrosion_rate_m_year=0,
        product_corrosion_rate_m_year=0,product_distribution="local",minimum_rate_policy=policy,no_floor_qualification_basis=basis)).outputs
    assert r.combined_corrosion_rate_m_year==expected and r.raw_combined_rate_m_year==0


@pytest.mark.parametrize("policy,basis",[("qualified_no_floor",None),("qualified_no_floor"," "),("apply_2_mpy_recommendation","override")])
def test_floor_basis_conflicts(policy,basis):
    with pytest.raises(DomainError):
        tank.bottom_corrosion_rate_combine(tank.BottomCorrosionRateCombineInput(soil_corrosion_rate_m_year=0,
            product_corrosion_rate_m_year=0,product_distribution="local",minimum_rate_policy=policy,no_floor_qualification_basis=basis))


def test_integrated_equations_independent_arithmetic():
    r=tank.bottom_corrosion_assessment(fixture()).outputs
    soil=.00013*.83*1*2*.33*1*1.1
    product=.00005*2.5*1.1*1.15*.7
    assert r.soil_corrosion_rate_m_year==pytest.approx(soil)
    assert r.product_corrosion_rate_m_year==pytest.approx(product)
    assert r.combined_corrosion_rate_m_year==pytest.approx(soil+product)
    local=tank.bottom_corrosion_assessment(fixture(product_distribution="local")).outputs
    assert local.combined_corrosion_rate_m_year==pytest.approx(max(soil,product))


def test_integrated_rpb_and_unverified_credit():
    r=tank.bottom_corrosion_assessment(fixture(bottom_type="rpb_not_per_api650",soil_resistivity_ohm_m=1,
        cathodic_protection=dict(protection_category="present_per_api651",effectiveness_verified_by_high_level_inspection=False))).outputs
    assert r.resistivity_factor==1 and r.bottom_type_factor==1.4 and r.cathodic_protection_factor==1
    assert r.soil_corrosion_rate_m_year==pytest.approx(.00013*2*1.4*1.1)


@pytest.mark.parametrize("changes",[dict(applicability_basis=" "),dict(soil_base_rate_source=" "),dict(product_base_rate_source=" ")])
def test_blank_qualifications(changes):
    with pytest.raises(DomainError):
        tank.bottom_corrosion_assessment(fixture(**changes))


def test_invalid_material_and_numeric_data():
    for changes in [dict(material="stainless_steel"),dict(soil_base_corrosion_rate_m_year=-1),dict(product_base_corrosion_rate_m_year=float("nan")),dict(soil_base_corrosion_rate_m_year=True)]:
        with pytest.raises(ValidationError):
            fixture(**changes)


def test_overflow_is_domain_failure():
    with pytest.raises(DomainError):
        tank.bottom_corrosion_assessment(fixture(soil_base_corrosion_rate_m_year=1e308,
            pad=dict(pad_type="soil_high_salt"),drainage=dict(drainage_category="one_third_frequently_underwater"),
            cathodic_protection=dict(protection_category="none",effectiveness_verified_by_high_level_inspection=False)))


def test_independent_annex_14_2_rate_equations():
    soil = tank.bottom_soil_rate_equation(tank.BottomSoilRateEquationInput(
        base_corrosion_rate_m_year=.00013, resistivity_factor=1.0, pad_factor=1.2,
        drainage_factor=2.0, cathodic_protection_factor=.66, bottom_type_factor=1.0,
        temperature_factor=1.1)).outputs
    product = tank.bottom_product_rate_equation(tank.BottomProductRateEquationInput(
        base_corrosion_rate_m_year=.00005, product_condition_factor=2.5,
        temperature_factor=1.1, steam_coil_factor=1.15, water_draw_factor=.7)).outputs
    assert soil.soil_corrosion_rate_m_year == pytest.approx(.00013*1.2*2*.66*1.1)
    assert product.product_corrosion_rate_m_year == pytest.approx(.00005*2.5*1.1*1.15*.7)
