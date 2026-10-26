import math
import pytest
from api581 import evaluate, DomainError


def c(id,**x):
    return evaluate(id,x)["outputs"]


@pytest.mark.parametrize("system,factor",[("inventory_blowdown",.25),("deluge_and_monitors",.2),("monitors",.05),("foam",.15),("none",0)])
def test_single_mitigation_credit(system,factor):
    assert c("level1/mitigation",system=system,isolation_class="B")["mitigation_fraction"]==factor


def test_blowdown_requires_adequate_isolation():
    with pytest.raises(DomainError): c("level1/mitigation",system="inventory_blowdown",isolation_class="C")


def test_toxic_source_uses_theoretical_rate_and_mass_fraction():
    assert c("level1/toxic-source",theoretical_rate_kg_s=10,released_mass_kg=200,toxic_mass_fraction=.1)=={"toxic_rate_kg_s":1,"toxic_mass_kg":20}


@pytest.mark.parametrize("mass,rate,detect,expected",[(10000,1,10000,3600),(100,1,1000,100),(10000,1,600,600),(100,0,600,0)])
def test_toxic_duration_limits(mass,rate,detect,expected):
    assert c("level1/toxic-duration",available_mass_kg=mass,theoretical_rate_kg_s=rate,detection_maximum_duration_s=detect)["duration_s"]==expected


@pytest.mark.parametrize("fluid,duration,area",[("ammonia",300,636.7),("ammonia",3600,2714),("chlorine",300,3350),("chlorine",3600,10994)])
def test_toxic_si_table_anchors(fluid,duration,area):
    out=c("level1/toxic-area",fluid=fluid,release_type="continuous",toxic_rate_kg_s=1,toxic_mass_kg=100,duration_s=duration,nonignition_probability=.8)
    assert out["unweighted_personnel_area_m2"]==area
    assert out["personnel_area_m2"]==pytest.approx(.8*area)


def test_duration_interpolates_curves_not_coefficients():
    out=c("level1/toxic-area",fluid="ammonia",release_type="continuous",toxic_rate_kg_s=2,toxic_mass_kg=100,duration_s=450,nonignition_probability=1)
    assert out["personnel_area_m2"]==pytest.approx((636.7*2**1.183+846.3*2**1.181)/2)


def test_no_toxic_extrapolation_and_no_zero_log():
    args=dict(fluid="ammonia",release_type="continuous",toxic_rate_kg_s=1,toxic_mass_kg=100,duration_s=299,nonignition_probability=1)
    with pytest.raises(DomainError): c("level1/toxic-area",**args)
    assert c("level1/toxic-area",**{**args,"toxic_rate_kg_s":0})["personnel_area_m2"]==0


def test_instant_toxic_mass_power_law():
    out=c("level1/toxic-area",fluid="chlorine",release_type="instantaneous",toxic_rate_kg_s=0,toxic_mass_kg=1,duration_s=0,nonignition_probability=.5)
    assert out["personnel_area_m2"]==pytest.approx(3.528*.5)


def test_steam_blending_and_zero_equipment_damage():
    out=c("level1/steam-area",adjusted_rate_kg_s=12.6,released_mass_kg=100)
    assert out["instantaneous_weight"]==.5
    assert out["personnel_area_m2"]==pytest.approx((.123*12.6+9.744*100**.6384)/2)
    assert out["equipment_area_m2"]==0


def test_acid_splash_correlation_squares_pressure_offset():
    # Dimensionless C11*dP=40; then h=0.31 exactly.
    out=c("level1/acid-caustic-area",adjusted_rate_kg_s=1/2.205,differential_pressure_pa=40/.145*1000)
    assert out["exponent_h"]==pytest.approx(.31)
    assert out["personnel_area_m2"]==pytest.approx(.2*.0929*(2696-21.9*40+1.474*1600))
    with pytest.raises(DomainError): c("level1/acid-caustic-area",adjusted_rate_kg_s=1,differential_pressure_pa=1e6)


def test_final_area_does_not_add_overlapping_toxic_areas():
    out=c("consequence/final-area",flammable_equipment_area_m2=20,flammable_personnel_area_m2=30,toxic_personnel_areas_m2=[100,200],nfnt_personnel_area_m2=50)
    assert out=={"equipment_area_m2":20,"personnel_area_m2":200,"consequence_area_m2":200}


def test_four_hole_weighting_and_missing_hole_rejection():
    holes=[dict(hole=h,generic_frequency_per_year=f,value=v) for h,f,v in [("small",1,10),("medium",2,20),("large",3,30),("rupture",4,40)]]
    assert c("consequence/hole-weighted",holes=holes,value_unit="m2")["weighted_value"]==30
    with pytest.raises(DomainError): c("consequence/hole-weighted",holes=holes[:3]+[holes[0]],value_unit="m2")


def test_financial_dimensions_and_mass_volume_cleanup():
    assert c("financial/surrounding-damage",equipment_area_m2=20,replacement_cost_per_m2=100,currency="KRW")["cost"]==2000
    assert c("financial/production-loss",component_outage_days=2,surrounding_outage_days=3,production_cost_per_day=100,currency="KRW")["cost"]==500
    assert c("financial/injury",personnel_area_m2=100,population_density_per_m2=.01,cost_per_injury=1000,currency="KRW")["cost"]==1000
    spill=c("financial/spill-cleanup",released_mass_kg=1000,liquid_density_kg_m3=500,evaporated_fraction=.25,cleanup_cost_per_m3=100,currency="KRW")
    assert spill=={"remediation_volume_m3":1.5,"cost":150,"currency":"KRW"}


def test_mechanism_maximum_is_after_hole_weighting():
    # For PIPE-8, small and medium weights are 8/30.6 and 20/30.6.
    # Selecting a maximum per hole would produce 28/30.6*100; API final max is 20/30.6*100.
    rows=[dict(hole=h,flammable_equipment_area_m2=0,flammable_personnel_area_m2=100 if h=="small" else 0,
               toxic_personnel_area_m2=100 if h=="medium" else 0,nfnt_personnel_area_m2=0) for h in ["small","medium","large","rupture"]]
    out=c("level1/consequence-summary",component_type="PIPE-8",holes=rows)
    assert out["personnel_area_m2"]==pytest.approx(20/30.6*100)
    assert out["generic_frequency_per_year"]==pytest.approx(3.06e-5)
