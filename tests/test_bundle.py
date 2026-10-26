"""Source examples and reliability/renewal invariants for bundle APIs."""
import math
import pytest
from api581 import DomainError
from api581.api import bundle


def cycle(age,failed):
    return {"duration_years":age,"failed":failed}


def test_specific_bundle_history_printed_example():
    result=bundle.weibayes_history(bundle.WeibayesHistoryInput(shape=2.568,
        cycles=[cycle(18,True),cycle(22,True),cycle(16,False)])).outputs
    assert result.characteristic_life_years == pytest.approx(22.16,abs=.01)
    assert result.failure_count == 2 and result.record_count == 3


def test_condition_update_adds_failure_and_exposure():
    # Table8.2 plus predicted 44.1-year failure: eq(1.77) eta=27.2 years.
    records=[cycle(t,f) for t,f in [(18,True),(22,True),(16,False),(10,True),
        (12,False),(13,False),(14,True),(25,False),(8,True)]]
    result=bundle.condition_update(bundle.ConditionUpdateInput(shape=2.568,cycles=records,predicted_failure_life_years=44.1)).outputs
    assert result.characteristic_life_years == pytest.approx(27.2,abs=.1)
    assert result.failure_count == 6 and result.record_count == 10


def test_zero_failures_is_not_a_finite_eta():
    with pytest.raises(DomainError) as error:
        bundle.weibayes_history(bundle.WeibayesHistoryInput(shape=3,cycles=[cycle(10,False),cycle(20,False)]))
    assert error.value.code == "insufficient_failure_data"


def test_weibayes_scaling_and_large_shape():
    def estimate(scale,shape):
        return bundle.weibayes_history(bundle.WeibayesHistoryInput(shape=shape,
            cycles=[cycle(10*scale,True),cycle(20*scale,False)])).outputs.characteristic_life_years
    assert estimate(100,3) == pytest.approx(100*estimate(1,3))
    assert estimate(1,1000) == pytest.approx(20)
    assert estimate(1,3) > 10  # surviving exposure increases fitted scale.


def thickness(**updates):
    return bundle.ThicknessLifeInput(**dict(original_thickness_m=.12*.0254,
        measured_thickness_m=.104*.0254,service_duration_years=11.75,
        remaining_wall_failure_fraction=.5,formula_basis="printed_eq_1_72",**updates))


def test_wall_thickness_source_example():
    out=bundle.thickness_life(thickness()).outputs
    assert out.thinning_rate_m_year == pytest.approx(.016*.0254/11.75)
    assert out.predicted_bundle_life_years == pytest.approx(44.0625)
    assert out.remaining_life_years == pytest.approx(32.3125)
    assert not out.remaining_wall_threshold_reached


def test_nonhalf_wall_fraction_exposes_source_disagreement():
    values=thickness().model_dump()
    values["remaining_wall_failure_fraction"] = .3
    printed=bundle.thickness_life(bundle.ThicknessLifeInput(**values)).outputs
    physical=bundle.thickness_life(bundle.ThicknessLifeInput(**{**values,"formula_basis":"remaining_wall_threshold"})).outputs
    assert printed.predicted_bundle_life_years == pytest.approx(.3*.12/(.016/11.75))
    assert physical.predicted_bundle_life_years == pytest.approx(.7*.12/(.016/11.75))


def test_no_measured_thinning_and_threshold_already_reached():
    same=thickness().model_dump();same["measured_thickness_m"]=same["original_thickness_m"]
    result=bundle.thickness_life(bundle.ThicknessLifeInput(**same)).outputs
    assert result.thinning_rate_m_year == 0
    assert result.predicted_bundle_life_years is None and result.remaining_life_years is None
    same["measured_thickness_m"] = .001
    result=bundle.thickness_life(bundle.ThicknessLifeInput(**same)).outputs
    assert result.remaining_wall_threshold_reached and result.remaining_life_years == 0
    same["measured_thickness_m"] = .1
    with pytest.raises(DomainError):
        bundle.thickness_life(bundle.ThicknessLifeInput(**same))


def test_estimated_life_and_extension_are_distinct_operations():
    assert bundle.estimated_life(bundle.EstimatedLifeInput(service_duration_years=10,estimated_remaining_life_years=5)).outputs.predicted_bundle_life_years == 15
    out=bundle.life_extension(bundle.LifeExtensionInput(age_at_action_years=10,life_extension_factor=.4,years_since_action=3)).outputs
    assert out.adjusted_age_at_action_years == 6 and out.effective_age_years == 9
    assert out.installation_shift_years == 4


def test_financial_consequence_source_example_and_risk_target_round_trip():
    cof=bundle.consequence(bundle.ConsequenceInput(daily_production_margin=100000,
        production_rate_reduction_fraction=.25,shutdown_days=4,environmental_cost=0,
        replacement_cost=25000,maintenance_cost=25000,currency="USD",cost_basis_year=2016)).outputs
    assert cof.production_loss_cost == 100000 and cof.financial_consequence == 150000
    target=bundle.target_age(bundle.TargetAgeInput(shape=2.568,characteristic_life_years=20.45,
        target_probability_weighted_consequence=75000,financial_consequence=cof.financial_consequence)).outputs
    assert target.target_failure_probability == .5
    risk=bundle.risk(bundle.RiskInput(shape=2.568,characteristic_life_years=20.45,age_years=target.target_age_years,
        financial_consequence=cof.financial_consequence,currency="USD")).outputs
    assert risk.probability_weighted_consequence == pytest.approx(75000)


@pytest.mark.parametrize("target", [150000,200000])
def test_no_finite_risk_target_crossing(target):
    out=bundle.target_age(bundle.TargetAgeInput(shape=3,characteristic_life_years=20,
        target_probability_weighted_consequence=target,financial_consequence=150000)).outputs
    assert out.target_age_years is None and out.status == "no_finite_crossing"


def test_deferral_uses_conditional_survival_not_cdf_difference():
    out=bundle.deferral_decision(bundle.DeferralDecisionInput(shape=1,characteristic_life_years=10,
        first_turnaround_age_years=10,second_turnaround_age_years=20,financial_consequence=100000,
        inspection_cost=5000,replacement_cost=80000,maintenance_cost=5000,hurdle_rate=.1,currency="USD")).outputs
    assert out.conditional_failure_probability == pytest.approx(1-math.exp(-1))
    assert out.inspection_economically_justified
    assert not out.replacement_economically_justified
    assert out.inspection_hurdle_cost == 11000


def test_deferral_survival_underflow_is_stable():
    # Both unconditional survival values underflow, but conditional hazard difference is 1.
    out=bundle.deferral_decision(bundle.DeferralDecisionInput(shape=1,characteristic_life_years=1,
        first_turnaround_age_years=1000,second_turnaround_age_years=1001,financial_consequence=1,
        inspection_cost=0,replacement_cost=0,maintenance_cost=0,currency="USD")).outputs
    assert out.conditional_failure_probability == pytest.approx(1-math.exp(-1))


def test_deferral_does_not_take_log_of_underflowed_time_ratio():
    out=bundle.deferral_decision(bundle.DeferralDecisionInput(shape=1,characteristic_life_years=1e300,
        first_turnaround_age_years=1e-300,second_turnaround_age_years=1e300,financial_consequence=1,
        inspection_cost=0,replacement_cost=0,maintenance_cost=0,currency="USD")).outputs
    assert out.conditional_failure_probability == pytest.approx(1-math.exp(-1))


def test_replacement_cost_grid_converges_to_exponential_renewal_value():
    out=bundle.replacement_optimization(bundle.ReplacementOptimizationInput(shape=1,characteristic_life_years=10,
        unplanned_failure_consequence=150000,planned_replacement_consequence=50000,
        step_days=7,maximum_replacement_age_years=20,currency="USD")).outputs
    last=out.samples[-1]
    age=last["replacement_age_years"]
    exact_life=10*(1-math.exp(-age/10))
    # Right-endpoint integration overestimates actual service by < one time step.
    assert exact_life <= last["expected_service_life_years"] < exact_life+7/365.24
    assert out.minimum_at_grid_boundary


def test_replacement_finds_interior_minimum_and_limits_search_claim():
    out=bundle.replacement_optimization(bundle.ReplacementOptimizationInput(shape=3,characteristic_life_years=20,
        unplanned_failure_consequence=150000,planned_replacement_consequence=25000,
        step_days=7,maximum_replacement_age_years=40,currency="USD")).outputs
    assert not out.minimum_at_grid_boundary
    assert 5 < out.optimal_grid_age_years < 25
    assert out.minimum_cost_per_day == min(row["total_cost_per_day"] for row in out.samples)
    with pytest.raises(DomainError):
        bundle.replacement_optimization(bundle.ReplacementOptimizationInput(shape=3,characteristic_life_years=20,
            unplanned_failure_consequence=150000,planned_replacement_consequence=25000,
            step_days=1,maximum_replacement_age_years=100,currency="USD"))


@pytest.mark.parametrize("material,factor", [("Carbon Steel",1),("304L/321/347 SS",2.8),
    ("Alloy 625",11),("Zeron 100",4),("Titanium Gr. 16",14),("Zirconium Alloy",15)])
def test_material_factor_printed_anchors(material,factor):
    assert bundle.material_factor(bundle.MaterialFactorInput(material=material)).outputs.material_factor == factor


def test_volume_cost_scaling_currency_and_price_basis():
    def estimate(diameter,fx):
        return bundle.replacement_cost(bundle.ReplacementCostInput(shell_inside_diameter_m=diameter,
            tube_length_m=6,material_factor=1,price_index_multiplier=2,output_currency_per_usd=fx,
            output_currency="USD" if fx == 1 else "KRW",output_cost_basis_year=2026)).outputs
    base=estimate(.8,1)
    assert base.reference_basis_cost_usd == pytest.approx(22000,rel=.0001)
    assert base.replacement_cost == 2*base.reference_basis_cost_usd
    assert estimate(1.6,1).replacement_cost == pytest.approx(4*base.replacement_cost)
    assert estimate(.8,1400).replacement_cost == pytest.approx(1400*base.replacement_cost)
    assert estimate(.8,1400).cost_basis_year == 2026


@pytest.mark.parametrize("method,factor", [("plug_tubes",.1),("rotate_180",.5),("partial_retube",.5),
    ("total_retube",.9),("install_spare",.5)])
def test_suggested_life_extension_methods(method,factor):
    assert bundle.life_extension_factor(bundle.LifeExtensionFactorInput(method=method)).outputs.life_extension_factor == factor


def test_ferrule_credit_requires_specific_damage_applicability():
    with pytest.raises(DomainError):
        bundle.life_extension_factor(bundle.LifeExtensionFactorInput(method="tube_ferrules"))
    assert bundle.life_extension_factor(bundle.LifeExtensionFactorInput(method="tube_ferrules",
        ferrules_for_localized_tube_end_damage=True)).outputs.life_extension_factor == .75


@pytest.mark.parametrize("p,cost,pc,cc", [(0,0,1,"A"),(.1,10000,1,"A"),(.2,50000,2,"B"),
    (.3,150000,3,"C"),(.5,1000000,4,"D"),(.5001,1000001,5,"E")])
def test_bundle_category_inclusive_upper_limits(p,cost,pc,cc):
    out=bundle.categories(bundle.CategoriesInput(cumulative_failure_probability=p,financial_consequence_usd=cost,
        consequence_basis="printed_table_USD_basis")).outputs
    assert out.probability_category == pc and out.consequence_category == cc
