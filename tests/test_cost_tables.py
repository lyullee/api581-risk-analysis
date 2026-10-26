import pytest
from api581 import evaluate,DomainError


def c(id,**x):
    return evaluate(id,x)["outputs"]


def test_historical_repair_table_and_basis_are_preserved():
    out=c("financial/repair-table",component_type="PIPE-8")
    assert out=={"cost_by_hole_usd_2001":{"small":5,"medium":30,"large":60,"rupture":180},"cost_basis_year":2001,"currency":"USD"}
    assert c("financial/repair-table",component_type="COMPC")["cost_by_hole_usd_2001"]["rupture"]==300000


@pytest.mark.parametrize("material,value",[("carbon_steel",1),("304_ss",3.2),("alloy_625",26),("tantalum",535)])
def test_material_table_reference_cells(material,value):
    assert c("financial/material-factor",material_id=material)["material_factor"]==value


def test_weighted_repair_retains_2001_basis_before_conversion():
    out=c("financial/component-repair",component_type="PIPE-8",material_id="304_ss",price_factor_since_2001=2,
          usd_to_output_currency=1000,cost_basis_year=2026,currency="KRW")
    expected=(8*5+20*30+2*60+.6*180)/30.6*3.2
    assert out["weighted_repair_cost_usd_2001"]==pytest.approx(expected)
    assert out["cost"]==pytest.approx(expected*2000)
    assert out["cost_basis_year"]==2026


def test_na_is_distinct_from_zero_outage():
    out=c("financial/outage-table",component_type="PIPE-1")
    assert out["days_by_hole"]=={"small":0,"medium":None,"large":None,"rupture":1}
    # Medium/large frequencies are zero; missing cells contribute no downtime.
    assert c("financial/component-outage",component_type="PIPE-1",outage_multiplier=1)["component_outage_days"]==pytest.approx(2.6/30.6)


def test_nonzero_frequency_na_requires_override():
    with pytest.raises(DomainError,match="supply override"):
        c("financial/component-outage",component_type="COMPR",outage_multiplier=1)
    out=c("financial/component-outage",component_type="COMPR",outage_multiplier=2,override_days={"small":1,"rupture":10})
    assert out["component_outage_days"]==pytest.approx(2*(8*1+20*3+2*7+.6*10)/30.6)
    with pytest.raises(DomainError): c("financial/component-outage",component_type="PUMP2S",outage_multiplier=1)


def test_surrounding_outage_correlation_and_zero_limit():
    assert c("financial/surrounding-outage",surrounding_damage_cost_usd=1000000)["surrounding_outage_days"]==pytest.approx(10**1.242)
    assert c("financial/surrounding-outage",surrounding_damage_cost_usd=0)["surrounding_outage_days"]==0


def test_remediation_properties_are_not_gas_density():
    out=c("properties/leak-table",fluid="H2")
    assert out["tabulated_liquid_density_kg_m3"]==71.010
    assert out["normal_boiling_point_k"]==pytest.approx(20.15)
    assert out["evaporated_fraction_24h"]==1
    assert c("properties/leak-table",fluid="C25+")["evaporated_fraction_24h"]==.02


@pytest.mark.parametrize("phase,temperature,ignition,expected",[("gas",400,False,False),("liquid",366.14,False,False),
    ("liquid",366.15,False,True),("liquid",400,True,False)])
def test_cleanup_screening(phase,temperature,ignition,expected):
    assert c("financial/cleanup-eligibility",release_phase=phase,normal_boiling_point_k=temperature,autoignition_likely=ignition)["include_cleanup_cost"]==expected


def test_composed_financial_cost_is_currency_invariant_and_sums_categories():
    inputs=dict(repair=dict(component_type="PIPE-8",material_id="carbon_steel",price_factor_since_2001=2,usd_to_output_currency=1,
                           cost_basis_year=2026,currency="USD"),outage=dict(component_type="PIPE-8",outage_multiplier=1),
                equipment_area_m2=100,personnel_area_m2=200,equipment_cost_per_m2=1000,production_cost_per_day=100,
                population_density_per_m2=.01,cost_per_injury=10000,weighted_cleanup_volume_m3=2,cleanup_cost_per_m3=100)
    usd=c("financial/level1-consequence",**inputs)
    krw_inputs={**inputs,"repair":{**inputs["repair"],"usd_to_output_currency":1000,"currency":"KRW"}}
    for field in ["equipment_cost_per_m2","production_cost_per_day","cost_per_injury","cleanup_cost_per_m3"]:
        krw_inputs[field]*=1000
    krw=c("financial/level1-consequence",**krw_inputs)
    assert krw["financial_consequence"]==pytest.approx(usd["financial_consequence"]*1000)
    assert krw["surrounding_outage_days"]==usd["surrounding_outage_days"]
    assert usd["surrounding_cost_reference_usd_2001"]==50000
    assert usd["financial_consequence"]==pytest.approx(sum(usd[k] for k in ["component_repair_cost","surrounding_equipment_cost","business_interruption_cost","injury_cost","environmental_cost"]))
