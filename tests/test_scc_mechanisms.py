import pytest
from api581 import evaluate,DomainError


def c(id,**x):
    return evaluate(id,x)["outputs"]


def assessment():
    return dict(susceptibility="high",confirmed_cracking=False,unrepaired_cracks=False,
                years_since_qualifying_inspection=10,inspections=dict(a=1,b=0,c=0,d=0))


@pytest.mark.parametrize("mechanism,svi,base",[("caustic",5000,250),("amine",1000,50),("ssc",100,5),("hic-sohic-h2s",100,5),
    ("acscc",1000,50),("pascc",5000,250),("clscc",5000,250),("hsc-hf",100,5),("hic-sohic-hf",100,5)])
def test_each_mechanism_uses_its_own_severity_scale(mechanism,svi,base):
    inputs=assessment()
    if mechanism.startswith("hic-sohic"): inputs["monitoring"]="none"
    out=c("damage/"+mechanism,**inputs)
    assert out["severity_index"]==svi
    assert out["base_damage_factor"]==base
    assert out["damage_factor"]==pytest.approx(base*10**1.1)


def test_qualified_inspection_equivalence_is_composed():
    inputs=assessment(); inputs["inspections"]=dict(a=0,b=2,c=0,d=0)
    out=c("damage/amine",**inputs)
    assert out["equivalent_inspection_grade"]=="A" and out["equivalent_inspection_count"]==1
    assert out["base_damage_factor"]==50


def test_known_cracking_forces_high_and_unrepaired_requires_ffs():
    inputs={**assessment(),"susceptibility":"none","confirmed_cracking":True}
    assert c("damage/amine",**inputs)["effective_susceptibility"]=="high"
    with pytest.raises(DomainError,match="FFS"):
        c("damage/amine",**{**inputs,"unrepaired_cracks":True})


def test_age_floor_and_monitoring_division():
    inputs={**assessment(),"years_since_qualifying_inspection":.5,"monitoring":"both"}
    out=c("damage/hic-sohic-h2s",**inputs)
    assert out["damage_factor"]==1.25
    assert c("damage/hic-monitoring-factor",monitoring="process_variables")["monitoring_factor"]==2


def test_unsupported_count_and_ambiguous_cell_remain_visible():
    with pytest.raises(DomainError): c("damage/amine",**{**assessment(),"inspections":dict(a=7,b=0,c=0,d=0)})
    with pytest.raises(DomainError,match="ambiguous"):
        c("damage/pascc",**{**assessment(),"susceptibility":"medium","inspections":dict(a=0,b=0,c=0,d=0)})


@pytest.mark.parametrize("hardness,pwht,expected",[(199,False,"low"),(200,False,"medium"),(237,False,"medium"),(238,False,"high"),
    (199,True,"none"),(200,True,"low"),(238,True,"high")])
def test_hsc_hf_hardness_boundaries(hardness,pwht,expected):
    assert c("damage/hsc-hf-susceptibility",measured_brinnell_hardness=hardness,pwht=pwht)["susceptibility"]==expected


def test_ssc_and_hic_have_different_heat_treatment_response():
    assert c("damage/ssc-susceptibility",environmental_severity="moderate",measured_brinnell_hardness=220,pwht=True)["susceptibility"]=="none"
    assert c("damage/hic-h2s-susceptibility",environmental_severity="moderate",steel_sulfur_weight_percent=.02,
             product_form="plate_or_welded",pwht=True)["susceptibility"]=="medium"


def test_hic_sulfur_boundary_and_product_form():
    common=dict(product_form="plate_or_welded",pwht=True)
    assert c("damage/hic-hf-susceptibility",**common,steel_sulfur_weight_percent=.01)["susceptibility"]=="medium"
    assert c("damage/hic-hf-susceptibility",**common,steel_sulfur_weight_percent=.011)["susceptibility"]=="high"
    assert c("damage/hic-hf-susceptibility",**{**common,"product_form":"seamless_or_extruded_pipe"},steel_sulfur_weight_percent=.02)["susceptibility"]=="low"


def test_clscc_temperature_matrix_and_source_overlap():
    assert c("damage/clscc-susceptibility",temperature_k=311.15,ph_over_10=False,chloride_band_ppm=">1000")["susceptibility"]=="medium"
    assert c("damage/clscc-susceptibility",temperature_k=311.15,ph_over_10=True,chloride_band_ppm=">1000")["susceptibility"]=="none"
    assert c("damage/clscc-susceptibility",temperature_k=423.15,ph_over_10=True,chloride_band_ppm=">1000")["susceptibility"]=="high"
    with pytest.raises(DomainError): c("damage/clscc-susceptibility",temperature_k=366.15,ph_over_10=True,chloride_band_ppm=">1000")


def test_severity_lookup_is_available_independently():
    assert c("damage/scc-severity",mechanism="amine",susceptibility="low")["severity_index"]==10
    assert c("damage/scc-severity",mechanism="clscc",susceptibility="low")["severity_index"]==50


def test_wet_h2s_environment_and_cyanide_apply_at_different_stages():
    out=c("damage/wet-h2s-environment",water_ph=8.5,h2s_in_water_ppm=2000,cyanides_present=True)
    assert out=={"environmental_severity":"moderate","susceptibility_upgrade_required":True}
    assert c("damage/wet-h2s-environment",water_ph=6,h2s_in_water_ppm=2000,cyanides_present=True)["susceptibility_upgrade_required"] is False
    for ph,h2s in [(7.55,100),(9,100),(8.5,1000)]:
        with pytest.raises(DomainError): c("damage/wet-h2s-environment",water_ph=ph,h2s_in_water_ppm=h2s,cyanides_present=False)


def test_acscc_carbonate_boundary_and_pwht():
    common=dict(water_ph_band="7.5_to_8",pwht=False)
    assert c("damage/acscc-susceptibility",**common,carbonate_ppm=99)["susceptibility"]=="low"
    assert c("damage/acscc-susceptibility",**common,carbonate_ppm=100)["susceptibility"]=="medium"
    assert c("damage/acscc-susceptibility",water_ph_band="at_least_9",pwht=True,carbonate_ppm=1000)["susceptibility"]=="none"


def test_pascc_operating_sensitization_boundary():
    args=dict(material_group="l_grade_300ss",heat_treatment="solution_annealed")
    assert c("damage/pascc-susceptibility",**args,operating_temperature_k=700.14)["susceptibility"]=="low"
    assert c("damage/pascc-susceptibility",**args,operating_temperature_k=700.15)["susceptibility"]=="medium"
    assert c("damage/pascc-susceptibility",material_group="321ss",heat_treatment="stabilized_after_welding",operating_temperature_k=800)["susceptibility"]=="low"
    with pytest.raises(DomainError):
        c("damage/pascc-susceptibility",material_group="regular_300ss_or_alloy600_800",heat_treatment="stabilized_before_welding",operating_temperature_k=500)
