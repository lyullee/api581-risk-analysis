"""PRD table anchors, adjustment exclusions, source update example and LOC chain."""
import math
import pytest
from api581 import DomainError
from api581.api import prd, frequency


@pytest.mark.parametrize("device,mode,severity,eta", [
    ("conventional","fail_to_open","mild",50.5),("balanced_bellows","fail_to_open","moderate",23.9),
    ("conventional","fail_to_open","severe",17.6),("pilot_operated","fail_to_open","mild",33.7),
    ("pilot_operated","fail_to_open","moderate",8),("pilot_operated","fail_to_open","severe",3.5),
    ("rupture_disk","fail_to_open","severe",50.5),("conventional","leak","mild",17.5),
    ("balanced_bellows","leak","moderate",14),("balanced_bellows","leak","severe",11.5),
    ("pilot_operated","leak","severe",13.1),("rupture_disk","leak","severe",17.5)])
def test_default_table_anchors(device,mode,severity,eta):
    out=prd.default_weibull(prd.DefaultWeibullInput(device_type=device,failure_mode=mode,severity=severity)).outputs
    assert out.default_characteristic_life_years == eta
    assert out.shape == (1.8 if mode == "fail_to_open" else 1.6)
    assert out.design_factor == 1


@pytest.mark.parametrize("device,mode,closed,soft,factor", [
    ("conventional","fail_to_open",True,True,.75),
    ("balanced_bellows","fail_to_open",True,True,1),
    ("conventional","leak",True,True,1.25),
    ("balanced_bellows","leak",True,True,1.25),
    ("pilot_operated","leak",True,True,1)])
def test_design_modifiers_not_cross_applied(device,mode,closed,soft,factor):
    out=prd.default_weibull(prd.DefaultWeibullInput(device_type=device,failure_mode=mode,severity="mild",
        closed_system_or_flare=closed,soft_seated=soft)).outputs
    assert out.design_factor == factor
    assert out.design_adjusted_characteristic_life_years == out.default_characteristic_life_years*factor


def environment(**updates):
    data=dict(device_type="conventional",failure_mode="leak",operating_temperature_k=300,
        operating_to_set_pressure_ratio=.8,installed_piping_vibration=False,pulsating_or_cyclic_service=False,
        actuations_per_year=0,history_of_chatter=False)
    return prd.EnvironmentFactorInput(**{**data,**updates})


def test_environment_product_and_no_double_counting():
    out=prd.environment_factor(environment(operating_temperature_k=600,operating_to_set_pressure_ratio=.95,
        installed_piping_vibration=True,pulsating_or_cyclic_service=True,actuations_per_year=6,history_of_chatter=True)).outputs
    assert out.environment_factor == pytest.approx(.6*.5*.8*.8*.5)
    assert out.individual_factors["excessive_actuation"] == 1
    out=prd.environment_factor(environment(failure_mode="fail_to_open",operating_temperature_k=600,
        operating_to_set_pressure_ratio=.95,installed_piping_vibration=True,pulsating_or_cyclic_service=True,
        actuations_per_year=6,history_of_chatter=True)).outputs
    assert out.environment_factor == .25


def test_environment_thresholds_and_pilot_exception():
    assert prd.environment_factor(environment(operating_to_set_pressure_ratio=.9,actuations_per_year=5)).outputs.environment_factor == 1
    assert prd.environment_factor(environment(operating_to_set_pressure_ratio=.90001)).outputs.environment_factor == .5
    assert prd.environment_factor(environment(device_type="pilot_operated",operating_to_set_pressure_ratio=.95)).outputs.environment_factor == 1
    assert prd.environment_factor(environment(device_type="pilot_operated",operating_to_set_pressure_ratio=.98,
        qualified_pilot_high_ratio_exception=True)).outputs.environment_factor == 1
    with pytest.raises(DomainError):
        prd.environment_factor(environment(qualified_pilot_high_ratio_exception=True))
    with pytest.raises(DomainError) as error:
        prd.environment_factor(environment(operating_temperature_k=533.15))
    assert error.value.code == "unresolved_applicability"
    assert prd.environment_factor(environment(failure_mode="fail_to_open",operating_temperature_k=533.15)).outputs.environment_factor == 1


@pytest.mark.parametrize("device,ratio,expected", [("conventional",.45,.5),("balanced_bellows",.9,1),
    ("pilot_operated",.475,.5),("pilot_operated",1.2,1),("rupture_disk",0,1)])
def test_set_pressure_factor_applies_to_probability(device,ratio,expected):
    assert prd.set_pressure_factor(prd.SetPressureFactorInput(device_type=device,operating_to_set_pressure_ratio=ratio)).outputs.set_pressure_factor == expected


@pytest.mark.parametrize("ratio,factor", [(1,1),(1.3,1),(2.65,.6),(4,.2),(10,.2)])
def test_overpressure_factor_endpoints_and_interpolation(ratio,factor):
    assert prd.overpressure_factor(prd.OverpressureFactorInput(overpressure_to_set_pressure_ratio=ratio)).outputs.overpressure_factor == pytest.approx(factor)


def test_demand_is_residual_fraction_and_distinct_cases_sum():
    out=prd.demand_rate(prd.DemandRateInput(cases=[
        dict(initiating_event_frequency_per_year=.004,demand_rate_reduction_factor=.1),
        dict(initiating_event_frequency_per_year=.02,demand_rate_reduction_factor=1)])).outputs
    assert out.case_demand_rates_per_year == [.0004,.02]
    assert out.total_demand_rate_per_year == .0204


def update(**changes):
    return prd.InspectionUpdateInput(**{**dict(shape=1.8,prior_characteristic_life_years=17.6,
        duration_years=6,effectiveness="highly",result="pass"),**changes})


def test_inspection_update_printed_example():
    out=prd.inspection_update(update()).outputs
    assert out.prior_failure_probability == pytest.approx(.1342,abs=.0001)
    assert out.conditional_failure_probability == pytest.approx(.08658,abs=.0001)
    assert out.weighted_failure_probability == pytest.approx(.1310,abs=.0001)
    assert out.updated_characteristic_life_years == pytest.approx(17.9,abs=.05)


@pytest.mark.parametrize("grade", ["fairly","usually","highly"])
def test_inspection_direction_restrictions_and_piping_override(grade):
    passed=prd.inspection_update(update(effectiveness=grade)).outputs
    failed=prd.inspection_update(update(effectiveness=grade,result="fail")).outputs
    plugged=prd.inspection_update(update(effectiveness=grade,piping_plugged=True)).outputs
    assert passed.updated_characteristic_life_years >= 17.6
    assert failed.updated_characteristic_life_years <= 17.6
    assert plugged.updated_characteristic_life_years == failed.updated_characteristic_life_years
    assert plugged.effective_failed_result
    # A very early PASS would otherwise decrease eta; retain prior per source rule.
    assert prd.inspection_update(update(effectiveness=grade,duration_years=1)).outputs.updated_characteristic_life_years == 17.6


@pytest.mark.parametrize("changes", [{"effectiveness":"ineffective"},{"duration_years":.999}])
def test_ineffective_or_subyear_test_has_no_credit(changes):
    out=prd.inspection_update(update(**changes)).outputs
    assert not out.update_applied and out.conditional_failure_probability is None
    assert out.updated_characteristic_life_years == 17.6


def test_source_weighted_update_outside_domain_not_clipped():
    with pytest.raises(DomainError) as error:
        prd.inspection_update(update(duration_years=200))
    assert error.value.code == "outside_update_domain"


def test_protected_equipment_probability_cap_and_hole_partition():
    gff=frequency.generic(frequency.GenericInput(component_type="DRUM")).outputs
    def protected(ratio,df=1):
        return prd.protected_equipment(prd.ProtectedEquipmentInput(generic_frequencies_per_year=gff.by_hole_per_year,
            total_damage_factor=df,management_factor=1,overpressure_to_mawp_ratio=ratio)).outputs
    normal=protected(1)
    assert normal.normal_failure_frequency_per_year == pytest.approx(3.06e-5)
    assert normal.source_model_loc_probability == pytest.approx(3.06e-5)
    elevated=protected(2)
    assert elevated.source_model_loc_probability > normal.source_model_loc_probability
    assert sum(elevated.by_hole_loc_probability.values()) == pytest.approx(elevated.source_model_loc_probability)
    assert protected(4).source_model_loc_probability == pytest.approx(1,abs=.001)
    assert protected(10000).source_model_loc_probability == 1  # no exp overflow before cap.
    assert protected(10000,0).source_model_loc_probability == 0


def test_base_reliability_then_fail_frequency_and_leakage_difference():
    base=prd.base_reliability(prd.BaseReliabilityInput(
        defaults=prd.DefaultWeibullInput(device_type="conventional",failure_mode="fail_to_open",severity="severe"),
        environment=environment(failure_mode="fail_to_open"),age_years=6,
        overpressure_to_set_pressure_ratio=2.65)).outputs
    assert base.modified_characteristic_life_years == 17.6
    assert base.scenario_adjusted_probability == pytest.approx(base.unadjusted_cumulative_probability*.6)
    freq=prd.fail_frequency(prd.FailFrequencyInput(failure_on_demand_probability=base.scenario_adjusted_probability,
        demand_rate_per_year=.01,protected_equipment_loc_probability=.2)).outputs
    assert freq.annual_failure_frequency == pytest.approx(base.scenario_adjusted_probability*.002)
    leak=prd.base_reliability(prd.BaseReliabilityInput(
        defaults=prd.DefaultWeibullInput(device_type="conventional",failure_mode="leak",severity="mild"),
        environment=environment(operating_to_set_pressure_ratio=.45),age_years=6)).outputs
    assert leak.modified_characteristic_life_years == 17.5
    assert leak.scenario_adjusted_probability == pytest.approx(leak.unadjusted_cumulative_probability*.5)


def test_base_configuration_mismatch_rejected():
    with pytest.raises(DomainError):
        prd.base_reliability(prd.BaseReliabilityInput(
            defaults=prd.DefaultWeibullInput(device_type="conventional",failure_mode="fail_to_open",severity="mild"),
            environment=environment(failure_mode="leak"),age_years=6))
