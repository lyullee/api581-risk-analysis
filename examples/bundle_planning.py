"""Source-based bundle history -> consequence -> target age -> replacement grid."""
from api581 import Context
from api581.api import bundle


def main():
    context=Context(asset_id="191-X-25A",source_revision="source-example")
    fitted=bundle.weibayes_history(bundle.WeibayesHistoryInput(shape=2.568,cycles=[
        bundle.LifeRecordInput(duration_years=18,failed=True),
        bundle.LifeRecordInput(duration_years=22,failed=True),
        bundle.LifeRecordInput(duration_years=16,failed=False)]),context=context)
    consequence=bundle.consequence(bundle.ConsequenceInput(daily_production_margin=100000,
        production_rate_reduction_fraction=.25,shutdown_days=4,environmental_cost=0,
        replacement_cost=25000,maintenance_cost=25000,currency="USD",cost_basis_year=2016),context=context)
    target=bundle.target_age(bundle.TargetAgeInput(shape=fitted.outputs.shape,
        characteristic_life_years=fitted.outputs.characteristic_life_years,
        target_probability_weighted_consequence=75000,
        financial_consequence=consequence.outputs.financial_consequence),context=context)
    planned=bundle.consequence(bundle.ConsequenceInput(daily_production_margin=100000,
        production_rate_reduction_fraction=.25,shutdown_days=1,environmental_cost=0,
        replacement_cost=25000,maintenance_cost=25000,currency="USD",cost_basis_year=2016),context=context)
    optimum=bundle.replacement_optimization(bundle.ReplacementOptimizationInput(shape=fitted.outputs.shape,
        characteristic_life_years=fitted.outputs.characteristic_life_years,
        unplanned_failure_consequence=consequence.outputs.financial_consequence,
        planned_replacement_consequence=planned.outputs.financial_consequence,
        maximum_replacement_age_years=50,currency="USD"),context=context)
    print("Fixed-shape characteristic life (years):",fitted.outputs.characteristic_life_years)
    print("Target age on supplied raw curve (years):",target.outputs.target_age_years)
    print("Minimum-cost grid replacement age (years):",optimum.outputs.optimal_grid_age_years)
    print("Minimum at grid boundary:",optimum.outputs.minimum_at_grid_boundary)
    print("No Fisher lower-confidence-bound or inspection-uncertainty adjustment is included.")


if __name__ == "__main__":
    main()
