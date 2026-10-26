import pytest
from api581 import evaluate,DomainError


def c(id,**x):
    return evaluate(id,x)["outputs"]


@pytest.mark.parametrize("kind,celsius,driver,mm_year",[("external",6,"marine_or_cooling_tower",.127),("external",71,"temperate",.051),
    ("cui",71,"severe",.508),("cui",-8,"severe",.076),("cui",176,"severe",0)])
def test_table_reference_cells_and_millimeter_conversion(kind,celsius,driver,mm_year):
    assert c("damage/"+kind+"-base-rate",temperature_k=celsius+273.15,driver=driver)["base_corrosion_rate_m_year"]==pytest.approx(mm_year/1000)


def test_linear_interpolation_and_no_extrapolation():
    out=c("damage/cui-base-rate",temperature_k=(71+107)/2+273.15,driver="marine_or_cooling_tower")
    assert out["base_corrosion_rate_m_year"]==pytest.approx((.254+.127)/2/1000)
    with pytest.raises(DomainError): c("damage/cui-base-rate",temperature_k=500,driver="severe")


def test_conflicting_external_cell_is_not_corrected_implicitly():
    for temperature in [-10,-8,0]:
        with pytest.raises(DomainError): c("damage/external-base-rate",temperature_k=temperature+273.15,driver="severe")
    assert c("damage/external-base-rate",temperature_k=279.15,driver="severe")["base_corrosion_rate_m_year"]==pytest.approx(.000254)


def test_time_weighted_rate_preserves_operating_exposure_fractions():
    out=c("damage/external-time-weighted-rate",mechanism="cui",driver="severe",periods=[
        dict(temperature_k=344.15,duration_fraction=.25),dict(temperature_k=380.15,duration_fraction=.75)])
    assert out["base_corrosion_rate_m_year"]==pytest.approx((.508*.25+.254*.75)/1000)


def test_design_and_interface_factors_use_maximum_not_product():
    out=c("damage/external-rate-adjust",base_corrosion_rate_m_year=.0001,water_retaining_design=True,soil_or_water_interface=True)
    assert out["design_interface_factor"]==2 and out["corrosion_rate_m_year"]==.0002


def test_cui_condition_complexity_and_insulation_factors():
    out=c("damage/cui-rate-adjust",base_corrosion_rate_m_year=.0001,water_retaining_design=True,soil_or_water_interface=True,
          insulation="foamglass",complexity="above_average",insulation_condition="above_average")
    assert out["corrosion_rate_m_year"]==pytest.approx(.0001*.75*1.25*.75*2)


@pytest.mark.parametrize("reading,coating,quality,credit,exposure",[(10,5,"medium",5,5),(10,20,"high",5,5),
    (3,20,"high",0,3),(3,10,"high",3,0),(10,5,"none_or_poor",0,10),(.3,1,"high",.3,0)])
def test_coating_window_overlap_and_floating_boundary(reading,coating,quality,credit,exposure):
    out=c("damage/coating-exposure",years_since_thickness_reading=reading,coating_age_years=coating,coating_quality=quality)
    assert out["coating_credit_years"]==pytest.approx(credit)
    assert out["corrosion_exposure_years"]==pytest.approx(exposure)


def external_input():
    return dict(rate=dict(base_corrosion_rate_m_year=.0001,water_retaining_design=False,soil_or_water_interface=False),
        coating=dict(years_since_thickness_reading=10,coating_age_years=0,coating_quality="none_or_poor"),
        strength=dict(differential_pressure_pa=100000,diameter_m=1,flow_stress_pa=330000000,starting_thickness_m=.01,shape="cylinder"),
        inspections=dict(confidence="low",inspections_a=1))


def test_external_df_exposure_and_shared_limit_state():
    out=c("damage/external-corrosion",**external_input())
    assert out["wall_loss_fraction"]==pytest.approx(.1)
    direct=c("damage/thinning-base",wall_loss_fraction=out["wall_loss_fraction"],strength_ratio=out["strength_ratio"],posterior=out["posterior_probabilities"])
    assert out["damage_factor"]==direct["base_damage_factor"]
    zero=external_input(); zero["rate"]["base_corrosion_rate_m_year"]=0
    assert c("damage/external-corrosion",**zero)["damage_factor"]<.1  # No internal-thinning floor in eq 2.50.


def test_cui_and_external_equal_under_identical_effective_rate():
    data=external_input()
    external=c("damage/external-corrosion",**data)
    data["rate"]={**data["rate"],"insulation":"pearlite","complexity":"average","insulation_condition":"average"}
    cui=c("damage/cui",**data)
    assert cui==external


def test_external_and_cui_chloride_base_susceptibility_differ():
    args=dict(temperature_k=333.15,driver="marine_or_cooling_tower")
    assert c("damage/external-clscc-base-susceptibility",**args,mechanism="external_clscc")["base_susceptibility"]=="medium"
    assert c("damage/external-clscc-base-susceptibility",**args,mechanism="cui_clscc")["base_susceptibility"]=="high"
    with pytest.raises(DomainError): c("damage/external-clscc-base-susceptibility",temperature_k=366.15,driver="severe",mechanism="external_clscc")


def test_external_cracking_uses_external_severity_scale_and_coating_overlap():
    data=dict(susceptibility="high",confirmed_cracking=False,unrepaired_cracks=False,years_since_qualifying_inspection=10,
              coating_age_years=5,coating_quality="medium",inspections=dict(a=1,b=0,c=0,d=0))
    result=c("damage/external-clscc",**data)
    assert result["severity_index"]==50 and result["base_damage_factor"]==3
    assert result["cracking_exposure_years"]==5
    assert result["damage_factor"]==pytest.approx(3*5**1.1)
    assert c("damage/cui-clscc",**data)==result
