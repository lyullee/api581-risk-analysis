"""PRD test update -> one demand/overpressure scenario -> annual financial risk."""
from api581 import Context
from api581.api import prd, frequency, reliability, risk


def main():
    context=Context(asset_id="example-prd",component_id="example-protected-drum")
    base=prd.default_weibull(prd.DefaultWeibullInput(device_type="conventional",
        failure_mode="fail_to_open",severity="severe"),context=context)
    # Six-year field/as-received test with no overhaul; effective age remains six.
    inspection=prd.inspection_update(prd.InspectionUpdateInput(shape=base.outputs.shape,
        prior_characteristic_life_years=base.outputs.design_adjusted_characteristic_life_years,
        duration_years=6,effectiveness="highly",result="pass"),context=context)
    failure=reliability.weibull(reliability.WeibullInput(shape=base.outputs.shape,
        characteristic_life_years=inspection.outputs.updated_characteristic_life_years,age_years=6),context=context)
    adjustment=prd.overpressure_factor(prd.OverpressureFactorInput(overpressure_to_set_pressure_ratio=2.65),context=context)
    gff=frequency.generic(frequency.GenericInput(component_type="DRUM"),context=context)
    protected=prd.protected_equipment(prd.ProtectedEquipmentInput(generic_frequencies_per_year=gff.outputs.by_hole_per_year,
        total_damage_factor=20,management_factor=1,overpressure_to_mawp_ratio=2),context=context)
    demand=prd.demand_rate(prd.DemandRateInput(cases=[prd.DemandCaseInput(
        initiating_event_frequency_per_year=.004,demand_rate_reduction_factor=.1)]),context=context)
    event=prd.fail_frequency(prd.FailFrequencyInput(
        failure_on_demand_probability=failure.outputs.cumulative_failure_probability*adjustment.outputs.overpressure_factor,
        demand_rate_per_year=demand.outputs.total_demand_rate_per_year,
        protected_equipment_loc_probability=protected.outputs.source_model_loc_probability),context=context)
    result=risk.aggregate(risk.AggregateInput(scenarios=[risk.RiskScenarioInput(scenario_id="one-qualified-demand-case",
        annual_failure_frequency=event.outputs.annual_failure_frequency,equipment_area_m2=0,
        personnel_area_m2=0,financial_consequence=1000000)],currency="USD"),context=context)
    print("Inspection-updated characteristic life (years):",inspection.outputs.updated_characteristic_life_years)
    print("Scenario failure frequency (1/year):",event.outputs.annual_failure_frequency)
    print("Scenario annual financial risk (USD/year):",result.outputs.financial_risk_per_year)


if __name__ == "__main__":
    main()
