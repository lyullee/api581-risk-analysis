"""Printed SI anchors, US cross-unit check, steady-state inversion and support."""
import math
import pytest
from api581 import DomainError
from api581.api import properties, release


def surface():
    values=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface="concrete")).outputs
    return release.SurfaceInteractionInput(**values.model_dump())


def boiling(**updates):
    return dict(bubble_temperature_k=250,ground_temperature_k=300,latent_heat_j_kg=300000,
        surface=surface(),gravity_m_s2=9.81)|updates


def nonboiling(**updates):
    return dict(bubble_temperature_k=350,ground_temperature_k=300,storage_temperature_k=310,
        bubble_pressure_at_ground_pa_abs=10000,ambient_pressure_pa_abs=101325,
        molecular_weight_kg_kmol=100,wind_speed_m_s=2)|updates


@pytest.mark.parametrize("name,k,a,rough",[("concrete",.92,4.16e-7,1),("soil_average",.96,4.59e-7,3),
    ("soil_sandy_dry",.26,1.98e-7,3),("soil_sandy_moist_8pct",.59,3.36e-7,3)])
def test_printed_si_ground_table(name,k,a,rough):
    value=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface=name)).outputs
    assert value.thermal_conductivity_w_m_k == k
    assert value.thermal_diffusivity_m2_s == a
    assert value.roughness_factor == rough


@pytest.mark.parametrize("bubble,expected",[(250,"boiling"),(350,"non_boiling"),(300,"boundary_requires_qualification")])
def test_pool_regime_and_undefined_equality(bubble,expected):
    value=release.pool_evaporation_regime(release.PoolEvaporationRegimeInput(bubble_temperature_k=bubble,ground_temperature_k=300)).outputs
    assert value.regime == expected


def test_boiling_rate_uses_pi_power_and_vapor_volume():
    value=release.boiling_pool_evaporation(release.BoilingPoolEvaporationInput(**boiling(),
        vapor_volumetric_rate_m3_s=.5,time_to_steady_s=2)).outputs
    expected=math.pi**1.5*(1*.92*50/(300000*math.sqrt(math.pi*4.16e-7)))*math.sqrt(2*9.81*.5)*2
    assert value.evaporation_rate_kg_s == pytest.approx(expected)
    assert value.latent_heat_rate_w == pytest.approx(expected*300000)
    assert value.evaporation_rate_kg_s != pytest.approx(expected*1.5/math.pi**1.5)


def test_radius_source_formula_and_homogeneity():
    value=release.boiling_pool_radius(release.BoilingPoolRadiusInput(vapor_volumetric_rate_m3_s=.5,time_to_steady_s=2)).outputs
    expected=math.sqrt(2/3)*(8*9.81*.5/math.pi)**.25*2**.75
    assert value.pool_radius_m == pytest.approx(expected)
    assert value.pool_area_m2 == pytest.approx(math.pi*expected**2)
    later=release.boiling_pool_radius(release.BoilingPoolRadiusInput(vapor_volumetric_rate_m3_s=.5,time_to_steady_s=4)).outputs
    assert later.pool_radius_m/value.pool_radius_m == pytest.approx(2**.75)


def boiling_source(**updates):
    return release.BoilingPoolSteadySourceInput(**(boiling()|dict(liquid_feed_rate_kg_s=1,pool_vapor_density_kg_m3=2,
        supply_duration_s=100,maximum_pool_area_m2=1000)|updates))


def test_boiling_steady_state_reconstructs_evaporation_and_spreading_primitives():
    result=release.boiling_pool_steady_source(boiling_source()).outputs
    assert result.support_status == "supported" and result.vapor_source_rate_kg_s == 1
    assert result.vapor_volumetric_rate_m3_s == .5  # feed / VAPOR density.
    evaporation=release.boiling_pool_evaporation(release.BoilingPoolEvaporationInput(**boiling(),
        vapor_volumetric_rate_m3_s=result.vapor_volumetric_rate_m3_s,time_to_steady_s=result.time_to_steady_s)).outputs
    radius=release.boiling_pool_radius(release.BoilingPoolRadiusInput(vapor_volumetric_rate_m3_s=result.vapor_volumetric_rate_m3_s,
        time_to_steady_s=result.time_to_steady_s)).outputs
    assert evaporation.evaporation_rate_kg_s == pytest.approx(result.equilibrium_evaporation_rate_kg_s)
    assert radius.pool_radius_m == result.pool_radius_m


def test_boiling_vapor_density_and_feed_scaling_laws():
    baseline=release.boiling_pool_steady_source(boiling_source()).outputs
    dense=release.boiling_pool_steady_source(boiling_source(pool_vapor_density_kg_m3=8)).outputs
    faster=release.boiling_pool_steady_source(boiling_source(liquid_feed_rate_kg_s=4)).outputs
    assert dense.time_to_steady_s/baseline.time_to_steady_s == pytest.approx(2)
    assert dense.pool_radius_m/baseline.pool_radius_m == pytest.approx(4**.125)
    assert faster.time_to_steady_s/baseline.time_to_steady_s == pytest.approx(2)
    assert faster.pool_radius_m/baseline.pool_radius_m == pytest.approx(4**.625)


@pytest.mark.parametrize("duration,area,status",[(.001,1000,"duration_limited"),(100,.001,"area_limited"),(.001,.001,"duration_and_area_limited")])
def test_unsupported_boiling_equilibrium_does_not_return_usable_feed_source(duration,area,status):
    result=release.boiling_pool_steady_source(boiling_source(supply_duration_s=duration,maximum_pool_area_m2=area)).outputs
    assert result.support_status == status
    assert result.vapor_source_rate_kg_s is None
    assert result.equilibrium_evaporation_rate_kg_s == 1 and result.pool_area_m2 > 0


def test_feed_ending_exactly_at_steady_state_has_no_sustained_source():
    steady=release.boiling_pool_steady_source(boiling_source()).outputs
    result=release.boiling_pool_steady_source(boiling_source(supply_duration_s=steady.time_to_steady_s)).outputs
    assert result.support_status == "duration_limited" and result.vapor_source_rate_kg_s is None


def test_nonboiling_rate_printed_pressure_temperature_and_exponents():
    value=release.nonboiling_pool_evaporation(release.NonboilingPoolEvaporationInput(**nonboiling(),pool_radius_m=5)).outputs
    expected=4.685*(10*100/(8314*310))*2**.78*5**1.89
    assert value.evaporation_rate_kg_s == pytest.approx(expected)
    warmer=release.nonboiling_pool_evaporation(release.NonboilingPoolEvaporationInput(**nonboiling(storage_temperature_k=620),pool_radius_m=5)).outputs
    assert warmer.evaporation_rate_kg_s == pytest.approx(expected/2)


def test_nonboiling_si_rate_matches_independent_printed_us_calculation():
    si=release.nonboiling_pool_evaporation(release.NonboilingPoolEvaporationInput(**nonboiling(),pool_radius_m=5)).outputs.evaporation_rate_kg_s
    # US C15=1, P psia, R1545, temperature R, wind ft/s, radius ft, rate lb/s.
    us=(10000/6894.757293168*100/(1545*(310*1.8)))*(2/0.3048)**.78*(5/0.3048)**1.89
    assert si == pytest.approx(us*.45359237,rel=.002)


def nonboiling_source(**updates):
    return release.NonboilingPoolSteadySourceInput(**(nonboiling()|dict(liquid_feed_rate_kg_s=.05,maximum_pool_area_m2=1000)|updates))


def test_nonboiling_steady_state_matches_independent_bracketed_forward_curve():
    result=release.nonboiling_pool_steady_source(nonboiling_source()).outputs
    assert result.support_status == "supported" and result.vapor_source_rate_kg_s == .05
    reconstructed=release.nonboiling_pool_evaporation(release.NonboilingPoolEvaporationInput(**nonboiling(),pool_radius_m=result.pool_radius_m)).outputs
    assert reconstructed.evaporation_rate_kg_s == pytest.approx(.05)
    # Independent bisection of forward correlation, not the production logarithmic inverse.
    low,high=0,100
    for _ in range(80):
        mid=(low+high)/2
        rate=4.685*(10*100/(8314*310))*2**.78*mid**1.89
        if rate > .05:
            high=mid
        else:
            low=mid
    assert result.pool_radius_m == pytest.approx((low+high)/2)


def test_nonboiling_site_limit_preserves_equilibrium_geometry_and_blocks_source():
    result=release.nonboiling_pool_steady_source(nonboiling_source(maximum_pool_area_m2=.001)).outputs
    assert result.support_status == "area_limited" and result.vapor_source_rate_kg_s is None
    assert result.pool_area_m2 > .001


@pytest.mark.parametrize("updates",[{"wind_speed_m_s":0},{"bubble_pressure_at_ground_pa_abs":0}])
def test_no_finite_nonboiling_equilibrium_when_forced_evaporation_coefficient_is_zero(updates):
    result=release.nonboiling_pool_steady_source(nonboiling_source(**updates)).outputs
    assert result.support_status == "no_finite_steady_state"
    assert result.pool_radius_m is result.pool_area_m2 is result.vapor_source_rate_kg_s is None
    zero=release.nonboiling_pool_evaporation(release.NonboilingPoolEvaporationInput(**nonboiling(**updates),pool_radius_m=5)).outputs
    assert zero.evaporation_rate_kg_s == 0


def test_zero_feed_is_explicit_and_zero_source():
    boiling_result=release.boiling_pool_steady_source(boiling_source(liquid_feed_rate_kg_s=0)).outputs
    nonboiling_result=release.nonboiling_pool_steady_source(nonboiling_source(liquid_feed_rate_kg_s=0)).outputs
    assert boiling_result.support_status == nonboiling_result.support_status == "no_feed"
    assert boiling_result.vapor_source_rate_kg_s == nonboiling_result.vapor_source_rate_kg_s == 0
    assert boiling_result.time_to_steady_s is None


@pytest.mark.parametrize("bubble",[300,350])
def test_boiling_rejects_equality_and_wrong_regime(bubble):
    with pytest.raises(DomainError):
        release.boiling_pool_steady_source(boiling_source(bubble_temperature_k=bubble))


def test_nonboiling_rejects_wrong_regime_and_superatmospheric_vapor_pressure():
    with pytest.raises(DomainError):
        release.nonboiling_pool_steady_source(nonboiling_source(bubble_temperature_k=250))
    with pytest.raises(DomainError):
        release.nonboiling_pool_steady_source(nonboiling_source(bubble_pressure_at_ground_pa_abs=101325))


@pytest.mark.parametrize("model",["boiling","nonboiling"])
def test_positive_pool_geometry_underflow_is_not_reported_as_zero_area(model):
    with pytest.raises(DomainError) as exc:
        if model == "boiling":
            release.boiling_pool_radius(release.BoilingPoolRadiusInput(vapor_volumetric_rate_m3_s=1e-300,time_to_steady_s=1e-300))
        else:
            release.nonboiling_pool_steady_source(nonboiling_source(liquid_feed_rate_kg_s=math.ulp(0.0)))
    assert exc.value.code == "numerical_failure"
