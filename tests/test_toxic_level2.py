"""Printed table anchors, inverse probit, independent exposure integration."""
import math
from typing import get_args
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import effects, properties, release, consequence
from api581.toxic_level2 import Fluid


@pytest.mark.parametrize("fluid",get_args(Fluid))
def test_every_printed_row_and_available_probit_round_trip(fluid):
    row=properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid=fluid)).outputs
    assert row.probit_concentration_unit == "ppm" and row.probit_duration_unit == "s"
    if fluid in ["methanol","styrene"]:
        assert not row.probit_available
        assert row.probit_intercept is row.probit_slope is row.concentration_exponent is None
        with pytest.raises(DomainError) as exc:
            effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid=fluid,exposure_duration_s=600))
        assert exc.value.code == "toxic_probit_unavailable"
    else:
        assert row.probit_available and row.probit_slope > 0 and row.concentration_exponent > 0
        threshold=effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid=fluid,exposure_duration_s=600)).outputs
        assert threshold.within_pure_species_limit
        result=effects.toxic_species_probit(effects.ToxicSpeciesProbitInput(fluid=fluid,concentration_ppm=threshold.concentration_ppm,
            exposure_duration_s=600)).outputs
        assert result.probit == pytest.approx(5,abs=2e-14)
        assert result.fatality_probability == pytest.approx(.5,abs=1e-14)


def test_table_reference_anchors_and_missing_cells_are_not_zero():
    hf=properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid="hydrogen_fluoride")).outputs
    assert (hf.probit_intercept,hf.probit_slope,hf.concentration_exponent)==(-48.33,4.853,1)
    assert hf.aegl3_ppm == {"600":170,"1800":62,"3600":44}
    assert hf.erpg3_ppm is None and hf.epa_toxic_endpoint_mg_l is None
    chlorine=properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid="chlorine")).outputs
    assert chlorine.aegl3_ppm == {"1800":28,"3600":20}
    assert chlorine.epa_toxic_endpoint_mg_l == .01
    assert properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid="ammonia")).outputs.idlh_ppm == 10
    assert properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid="methanol")).outputs.aegl3_ppm == {"600":15000,"1800":15000,"3600":7900}


def test_constant_probit_seconds_anchor_and_zero_exposure():
    result=effects.toxic_species_probit(effects.ToxicSpeciesProbitInput(fluid="hydrogen_sulfide",concentration_ppm=100,exposure_duration_s=600)).outputs
    assert result.probit == pytest.approx(-31.42+3.01*math.log(100**1.43*600))
    for c,t in [(0,600),(100,0)]:
        zero=effects.toxic_species_probit(effects.ToxicSpeciesProbitInput(fluid="hydrogen_sulfide",concentration_ppm=c,exposure_duration_s=t)).outputs
        assert zero.probit is None and zero.fatality_probability == 0


@pytest.mark.parametrize("probability",[0,1])
def test_inverse_rejects_infinite_target_endpoints(probability):
    with pytest.raises(DomainError):
        effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid="chlorine",exposure_duration_s=600,target_fatality_probability=probability))


def test_threshold_time_scaling_and_unattainable_pure_concentration_flag():
    short=effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid="chlorine",exposure_duration_s=60)).outputs
    long=effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid="chlorine",exposure_duration_s=240)).outputs
    assert short.concentration_ppm == pytest.approx(2*long.concentration_ppm)
    tiny=effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(fluid="chlorine",exposure_duration_s=1e-30)).outputs
    assert tiny.concentration_ppm > 1e6 and not tiny.within_pure_species_limit


def profile(fluid="hydrogen_sulfide",values=((0,100),(600,100)),interpolation="linear"):
    return effects.ToxicDoseProfileInput(fluid=fluid,profile=[effects.ConcentrationPointInput(time_s=t,concentration_ppm=c) for t,c in values],
        interpolation=interpolation,profile_source="Explicit numerical fixture, not a slabx result")


@pytest.mark.parametrize("interpolation",["previous","linear"])
def test_constant_profile_matches_constant_exposure_probit(interpolation):
    integrated=effects.toxic_dose_profile(profile(interpolation=interpolation)).outputs
    constant=effects.toxic_species_probit(effects.ToxicSpeciesProbitInput(fluid="hydrogen_sulfide",concentration_ppm=100,exposure_duration_s=600)).outputs
    assert integrated.probit == pytest.approx(constant.probit)
    assert integrated.dose_ppm_power_n_s == pytest.approx(600*100**1.43)
    assert integrated.equivalent_constant_concentration_ppm == pytest.approx(100)


def test_linear_concentration_power_is_not_trapezoid_of_power():
    result=effects.toxic_dose_profile(profile(fluid="chlorine",values=((0,0),(60,100)))).outputs
    assert result.dose_ppm_power_n_s == pytest.approx(60*10000/3)
    assert result.dose_ppm_power_n_s != pytest.approx(60*10000/2)
    assert result.equivalent_constant_concentration_ppm == pytest.approx(100/math.sqrt(3))


@pytest.mark.parametrize("fluid,n",[("hydrogen_sulfide",1.43),("methyl_isocyanate",.65),("carbon_tetrachloride",2.5)])
def test_fractional_power_profile_matches_independent_simpson_quadrature(fluid,n):
    result=effects.toxic_dose_profile(profile(fluid=fluid,values=((0,1),(600,300)))).outputs
    steps=20000
    dt=600/steps
    values=[(1+299*i/steps)**n for i in range(steps+1)]
    integral=dt/3*(values[0]+values[-1]+4*sum(values[1:-1:2])+2*sum(values[2:-1:2]))
    assert result.dose_ppm_power_n_s == pytest.approx(integral,rel=2e-8)
    reversed_profile=effects.toxic_dose_profile(profile(fluid=fluid,values=((0,300),(600,1)))).outputs
    assert reversed_profile.dose_ppm_power_n_s == pytest.approx(result.dose_ppm_power_n_s)


def test_previous_interpolation_uses_left_values_and_final_point_closes_interval():
    a=effects.toxic_dose_profile(profile(values=((0,10),(10,20),(30,0)),interpolation="previous")).outputs
    b=effects.toxic_dose_profile(profile(values=((0,10),(10,20),(30,1e6)),interpolation="previous")).outputs
    assert a.dose_ppm_power_n_s == pytest.approx(10*10**1.43+20*20**1.43)
    assert a.dose_ppm_power_n_s == b.dose_ppm_power_n_s


def test_zero_profile_has_no_finite_probit_and_zero_dose():
    result=effects.toxic_dose_profile(profile(values=((0,0),(600,0)))).outputs
    assert result.probit is None and result.log_dose is None
    assert result.fatality_probability == result.dose_ppm_power_n_s == result.equivalent_constant_concentration_ppm == 0


@pytest.mark.parametrize("values",[((1,100),(600,100)),((0,100),(0,100)),((0,100),(600,100),(500,100))])
def test_invalid_time_profiles_are_rejected(values):
    with pytest.raises(DomainError):
        effects.toxic_dose_profile(profile(values=values))


@pytest.mark.parametrize("concentration,duration",[(1e6,1e308),(1e-300,1e-300)])
def test_log_dose_remains_usable_when_dose_cannot_be_represented(concentration,duration):
    result=effects.toxic_dose_profile(profile(fluid="carbon_tetrachloride",values=((0,concentration),(duration,concentration)))).outputs
    assert result.dose_ppm_power_n_s is None and not result.dose_representable
    assert math.isfinite(result.log_dose) and math.isfinite(result.probit)
    assert result.equivalent_constant_concentration_ppm == pytest.approx(concentration)


@pytest.mark.parametrize("mass,rate,maximum,expected,reason",[
    (10000,1,10000,3600,"one_hour"),(100,2,1000,50,"inventory"),(10000,1,600,600,"detection_isolation"),
    (100,0,600,0,"no_release"),(0,2,600,0,"no_inventory"),(100,2,0,0,"detection_isolation")])
def test_duration_uses_full_mixture_rate_and_three_bounds(mass,rate,maximum,expected,reason):
    result=release.level2_toxic_duration(release.Level2ToxicDurationInput(available_mass_kg=mass,
        mixture_release_rate_kg_s=rate,detection_maximum_duration_s=maximum)).outputs
    assert result.release_duration_s == expected and result.governing_limit == reason


def test_mixture_mole_fraction_matches_printed_5percent_example():
    result=consequence.toxic_mixture_limit(consequence.ToxicMixtureLimitInput(pure_component_limit_ppm=100,toxic_mole_fraction=.05)).outputs
    assert result.modified_mixture_limit_ppm == 2000 and result.attainable_in_mixture
    absent=consequence.toxic_mixture_limit(consequence.ToxicMixtureLimitInput(pure_component_limit_ppm=100,toxic_mole_fraction=0)).outputs
    assert absent.modified_mixture_limit_ppm is None and not absent.component_present
    unattainable=consequence.toxic_mixture_limit(consequence.ToxicMixtureLimitInput(pure_component_limit_ppm=100,toxic_mole_fraction=1e-8)).outputs
    assert not unattainable.attainable_in_mixture


def cloud(component,area):
    return consequence.ToxicCloudAreaInput(component_id=component,cloud_area_m2=area,selected_criterion_source="Caller-selected probit50%, supplied footprint fixture")


def test_multicomponent_cloud_maximum_and_nonignition_weight_once():
    result=consequence.level2_toxic_case(consequence.Level2ToxicCaseInput(components=[cloud("h2s",100),cloud("co",200)],non_ignition_probability=.3)).outputs
    assert result.equipment_area_m2 == 0 and result.personnel_area_m2 == 60
    assert result.unweighted_cloud_area_m2 == 200 and result.critical_component_id == "co"


def test_duplicate_components_and_blank_sources_are_rejected():
    with pytest.raises(DomainError):
        consequence.level2_toxic_case(consequence.Level2ToxicCaseInput(components=[cloud("h2s",100),cloud("h2s",200)],non_ignition_probability=1))
    with pytest.raises(DomainError):
        consequence.level2_toxic_case(consequence.Level2ToxicCaseInput(components=[cloud(" ",100)],non_ignition_probability=1))


def cases():
    return [consequence.ToxicFrequencyCaseInput(hole=hole,generic_frequency_per_year=i,non_ignition_probability=.5,
        components=[cloud("h2s",i*100),cloud("co",i*50)]) for i,hole in enumerate(["small","medium","large","rupture"],start=1)]


def test_four_hole_average_and_complete_hole_contract():
    result=consequence.level2_toxic_summary(consequence.Level2ToxicSummaryInput(cases=cases())).outputs
    assert result.total_generic_frequency_per_year == 10
    assert result.personnel_area_m2 == 150 and result.equipment_area_m2 == 0
    assert result.by_hole_personnel_area_m2 == dict(small=50,medium=100,large=150,rupture=200)
    with pytest.raises(DomainError):
        consequence.level2_toxic_summary(consequence.Level2ToxicSummaryInput(cases=[cases()[0]]*4))
    with pytest.raises(DomainError):
        consequence.level2_toxic_summary(consequence.Level2ToxicSummaryInput(cases=[c.model_copy(update={"generic_frequency_per_year":0}) for c in cases()]))


def test_unknown_fluid_and_invalid_ppm_are_not_coerced():
    with pytest.raises(ValidationError):
        properties.ToxicImpactTableInput(fluid="unknown")
    with pytest.raises(ValidationError):
        effects.ToxicSpeciesProbitInput(fluid="chlorine",concentration_ppm=1e6+1,exposure_duration_s=600)


def test_positive_release_duration_underflow_is_not_reported_as_zero_exposure():
    with pytest.raises(DomainError) as exc:
        release.level2_toxic_duration(release.Level2ToxicDurationInput(available_mass_kg=1e-300,
            mixture_release_rate_kg_s=1e300,detection_maximum_duration_s=600))
    assert exc.value.code == "numerical_failure"
