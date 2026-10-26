"""PRD calendar history -> leakage reliability/COF -> declared-basis risk.

Illustrative inputs; FAIL case frequencies/COF are supplied qualified values.
The source-method CDF risk index is explicitly distinguished from annual risk.
"""
import _bootstrap  # noqa: F401
from api581 import Context
from api581.api import prd


def main():
    context=Context(asset_id="example-prd-leak",source_revision="leak-example-1")
    service=prd.service_age(prd.ServiceAgeInput(installation_date="2020-01-01",evaluation_date="2026-01-01",
        events=[prd.ServiceEventInput(event_date="2024-01-01",event_type="overhaul"),
                prd.ServiceEventInput(event_date="2025-01-01",event_type="test")]),context=context)
    probability=prd.base_reliability(prd.BaseReliabilityInput(
        defaults=prd.DefaultWeibullInput(device_type="conventional",failure_mode="leak",severity="mild"),
        environment=prd.EnvironmentFactorInput(device_type="conventional",failure_mode="leak",operating_temperature_k=300,
            operating_to_set_pressure_ratio=.8,installed_piping_vibration=False,pulsating_or_cyclic_service=False,
            actuations_per_year=0,history_of_chatter=False),age_years=service.outputs.effective_age_years),context=context)
    cof=prd.leakage_consequence(prd.LeakageConsequenceInput(operating_capacity_kg_s=1,inlet_size_nps=2,
        discharge="atmosphere",fluid_cost_per_kg=2,environmental_cost=100,repair_cost=1000,
        daily_production_margin=10000,shutdown_duration_days=1,mild_leak_tolerated_or_online_repair=True,
        model_basis="two_case_equations",currency="USD",cost_basis_year=2026),context=context)
    equipment=[prd.ProtectedRiskInput(equipment_id="example-drum",cases=[
        prd.FailRiskCaseInput(case_id="one-qualified-case",annual_failure_frequency=.0001,financial_consequence=100000)])]
    source=prd.risk_assessment(prd.RiskAssessmentInput(protected_equipment=equipment,
        leakage_measure=probability.outputs.scenario_adjusted_probability,
        leakage_financial_consequence=cof.outputs.financial_consequence,
        leakage_measure_basis="source_cumulative_probability",currency="USD",cost_basis_year=2026),context=context)
    annual=prd.risk_assessment(prd.RiskAssessmentInput(protected_equipment=equipment,
        leakage_measure=.02,  # Illustrative independently supplied annual leakage frequency.
        leakage_financial_consequence=cof.outputs.financial_consequence,
        leakage_measure_basis="annual_frequency",currency="USD",cost_basis_year=2026),context=context)
    print("Effective years since overhaul:",service.outputs.effective_age_years)
    print("Conditional leakage consequence (USD):",cof.outputs.financial_consequence)
    print("Source-method combined index:",source.outputs.source_total_risk_index)
    print("Annual result for cumulative-probability basis:",source.outputs.annual_financial_risk)
    print("Annual risk with supplied annual leak frequency (USD/year):",annual.outputs.annual_financial_risk)


if __name__ == "__main__":
    main()
