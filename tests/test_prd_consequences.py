"""Leakage duration/cost units, source alternatives and PRD risk ordering."""
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import prd

MONEY={"currency":"USD","cost_basis_year":2026}


def test_all_leak_rate_interpretations_are_distinct():
    out=prd.leakage_rates(prd.LeakageRatesInput(operating_capacity_kg_s=10)).outputs
    assert out.minor_rate_kg_s == .1
    assert out.mild_moderate_equation_rate_kg_s == .1
    assert out.moderate_table_rate_kg_s == 1
    assert out.stuck_open_rate_kg_s == 2.5


@pytest.mark.parametrize("nps,closed_days,air_days", [(.75,60,8),(.7501,30,4),(1.5,30,4),
    (1.5001,15,2),(3,15,2),(3.0001,7,1),(6,7,1),(6.0001,2,.33)])
def test_duration_table_inclusive_bounds_and_exact_si(nps,closed_days,air_days):
    for discharge,days in [("closed_system",closed_days),("flare",closed_days),("atmosphere",air_days)]:
        out=prd.leakage_duration(prd.LeakageDurationInput(inlet_size_nps=nps,discharge=discharge)).outputs
        assert out.mild_moderate_duration_s == days*86400
        assert out.stuck_open_duration_s == 1800


@pytest.mark.parametrize("discharge,recovery,factor", [("atmosphere",False,1),("flare",False,1),
    ("flare",True,.5),("closed_system",False,0)])
def test_loss_factor_is_residual_cost_factor(discharge,recovery,factor):
    assert prd.inventory_loss_factor(prd.InventoryLossFactorInput(discharge=discharge,
        flare_recovery_installed=recovery)).outputs.inventory_loss_factor == factor


def test_flare_recovery_cannot_be_assigned_to_another_destination():
    with pytest.raises(DomainError):
        prd.inventory_loss_factor(prd.InventoryLossFactorInput(discharge="atmosphere",flare_recovery_installed=True))


def test_inventory_loss_uses_seconds_not_hourly_day_factor():
    out=prd.inventory_loss(prd.InventoryLossInput(leakage_rate_kg_s=2,duration_s=86400,
        fluid_cost_per_kg=3,inventory_loss_factor=.5,**MONEY)).outputs
    assert out.leaked_mass_kg == 172800
    assert out.inventory_loss_equivalent_mass_kg == 86400
    assert out.inventory_loss_cost == 259200


@pytest.mark.parametrize("nps,reference", [(5.999,1000),(6,2000),(8,2000)])
def test_repair_reference_boundary_and_explicit_financial_adjustment(nps,reference):
    out=prd.repair_cost(prd.RepairCostInput(inlet_size_nps=nps,price_index_multiplier=2,
        output_currency_per_usd=1400,currency="KRW",cost_basis_year=2026)).outputs
    assert out.reference_cost_usd == reference
    assert out.repair_cost == reference*2*1400


@pytest.mark.parametrize("case,online,expected", [("mild_moderate",True,0),("mild_moderate",False,20000),
    ("stuck_open",True,20000),("stuck_open",False,20000)])
def test_mild_online_exemption_does_not_remove_stuck_open_shutdown(case,online,expected):
    out=prd.production_loss(prd.ProductionLossInput(daily_production_margin=10000,shutdown_duration_days=2,
        leak_case=case,mild_leak_tolerated_or_online_repair=online,**MONEY)).outputs
    assert out.production_loss_cost == expected


def consequence(**changes):
    inputs={**MONEY,"operating_capacity_kg_s":1,"inlet_size_nps":2,"discharge":"atmosphere",
        "fluid_cost_per_kg":2,"environmental_cost":100,"repair_cost":1000,
        "daily_production_margin":10000,"shutdown_duration_days":1,
        "mild_leak_tolerated_or_online_repair":True,"model_basis":"two_case_equations"}
    return prd.leakage_consequence(prd.LeakageConsequenceInput(**{**inputs,**changes}))


def test_two_case_equations_and_details():
    out=consequence().outputs
    assert out.costs_by_case["mild_moderate"]["inventory_loss_cost"] == 3456
    assert out.costs_by_case["mild_moderate"]["financial_consequence"] == 4556
    assert out.costs_by_case["stuck_open"]["leaked_mass_kg"] == 450
    assert out.costs_by_case["stuck_open"]["financial_consequence"] == 12000
    assert out.financial_consequence == pytest.approx(5300.4)
    assert sum(out.case_weights.values()) == 1


def test_three_case_table_resolves_moderate_rate_explicitly():
    two=consequence()
    three=consequence(model_basis="three_case_table_7_15")
    assert three.outputs.costs_by_case["moderate"]["inventory_loss_cost"] == 34560
    assert three.outputs.financial_consequence == pytest.approx(17742)
    assert three.outputs.financial_consequence > two.outputs.financial_consequence
    assert three.input_hash != two.input_hash
    assert sum(three.outputs.case_weights.values()) == 1


def test_online_flag_only_changes_mild_production_and_recovery_only_inventory():
    offline=consequence(mild_leak_tolerated_or_online_repair=False).outputs
    assert offline.financial_consequence == pytest.approx(14300.4)
    closed=consequence(discharge="closed_system").outputs
    for case in closed.costs_by_case.values():
        assert case["inventory_loss_cost"] == 0
        assert case["leaked_mass_kg"] > 0
        assert case["environmental_cost"] == 100 and case["repair_cost"] == 1000
    assert closed.financial_consequence == 2100  # common1100 + .1*10000 stuck production.


def test_no_implicit_source_model_basis():
    values=consequence().normalized_inputs
    del values["model_basis"]
    with pytest.raises(ValidationError):
        prd.LeakageConsequenceInput(**values)


@pytest.mark.parametrize("area,total,factor", [(1,1,1),(1,4,.5),(1,16,.25),(1,100,.25)])
def test_multiple_device_pressure_keeps_original_for_fop(area,total,factor):
    out=prd.multiple_device_pressure(prd.MultipleDevicePressureInput(analyzed_orifice_area_m2=area,
        total_installed_orifice_area_m2=total,scenario_pressure_pa_gauge=4e6)).outputs
    assert out.multiple_device_factor == factor
    assert out.protected_equipment_pressure_pa_gauge == 4e6*factor
    assert out.unreduced_pressure_for_fop_pa_gauge == 4e6
    with pytest.raises(DomainError):
        prd.multiple_device_pressure(prd.MultipleDevicePressureInput(analyzed_orifice_area_m2=2,
            total_installed_orifice_area_m2=1,scenario_pressure_pa_gauge=4e6))


def equipment():
    return [prd.ProtectedRiskInput(equipment_id="A",cases=[
        prd.FailRiskCaseInput(case_id="fire",annual_failure_frequency=.01,financial_consequence=10000),
        prd.FailRiskCaseInput(case_id="blocked",annual_failure_frequency=.02,financial_consequence=20000)]),
        prd.ProtectedRiskInput(equipment_id="B",cases=[
        prd.FailRiskCaseInput(case_id="fire",annual_failure_frequency=.02,financial_consequence=20000)])]


def test_sum_cases_before_maximum_across_protected_equipment():
    out=prd.fail_risk(prd.FailRiskInput(protected_equipment=equipment(),**MONEY)).outputs
    assert out.protected_equipment_risks_per_year == {"A":500,"B":400}
    assert out.maximum_fail_risk_per_year == 500  # neither900 (sum items) nor400 (max case).
    assert out.governing_equipment_ids == ["A"]


def test_duplicate_items_and_cases_rejected():
    items=equipment()
    with pytest.raises(DomainError):
        prd.fail_risk(prd.FailRiskInput(protected_equipment=[items[0],items[0]],**MONEY))
    items[0].cases.append(items[0].cases[0])
    with pytest.raises(DomainError):
        prd.fail_risk(prd.FailRiskInput(protected_equipment=items,**MONEY))


def test_annual_and_source_cumulative_risk_are_not_silently_conflated():
    def run(basis):
        return prd.risk_assessment(prd.RiskAssessmentInput(protected_equipment=equipment(),leakage_measure=.1,
            leakage_financial_consequence=10000,leakage_measure_basis=basis,**MONEY)).outputs
    annual=run("annual_frequency")
    source=run("source_cumulative_probability")
    assert annual.annual_financial_risk == 1500 and annual.source_total_risk_index is None
    assert source.annual_financial_risk is None and source.source_total_risk_index == 1500
    assert source.leakage_risk_unit == "currency" and annual.leakage_risk_unit == "currency/year"
    with pytest.raises(DomainError):
        prd.leakage_risk(prd.LeakageRiskInput(leakage_measure=1.01,financial_consequence=1000,
            measure_basis="source_cumulative_probability",**MONEY))
    assert prd.leakage_risk(prd.LeakageRiskInput(leakage_measure=2,financial_consequence=1000,
        measure_basis="annual_frequency",**MONEY)).outputs.leakage_risk_value == 2000


def test_currency_scaling_applies_to_all_conditional_costs():
    usd=consequence().outputs
    krw=consequence(currency="KRW",fluid_cost_per_kg=2800,environmental_cost=140000,
        repair_cost=1400000,daily_production_margin=14000000).outputs
    assert krw.financial_consequence == pytest.approx(usd.financial_consequence*1400)
