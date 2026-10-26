"""Printed source, independent sphere surface integral, and threshold inversion."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import effects


def atmosphere(tau=.8):
    return effects.AtmosphereInput(transmissivity_model="constant",constant_transmissivity=tau)


def integrate_sphere(center_distance,radius=1,steps=20000):
    """Lambertian integral of the visible cap, receiver normal toward center.

    Integrates source cosine, receiver cosine, inverse-square and surface area;
    no production view-factor expression is used in this quadrature.
    """
    dt=math.acos(radius/center_distance)/steps
    total=0
    for i in range(steps):
        theta=(i+.5)*dt
        cosine=math.cos(theta)
        ray_squared=center_distance**2+radius**2-2*center_distance*radius*cosine
        total+=2*radius**2*math.sin(theta)*(center_distance*cosine-radius)*(center_distance-radius*cosine)/ray_squared**2*dt
    return total


@pytest.mark.parametrize("distance",[0,.5,2,10])
def test_elevated_sphere_matches_independent_visible_cap_integral(distance):
    result=effects.fireball_view_factor(effects.FireballViewFactorInput(
        diameter_m=2,distance_m=distance,geometry_basis="elevated_sphere_maximum")).outputs
    center=math.hypot(1.5,distance)
    assert result.view_factor == pytest.approx(integrate_sphere(center),rel=2e-8)
    assert result.attenuation_path_m == pytest.approx(center-1)


def test_printed_geometry_is_distinct_and_preserved_in_provenance():
    kwargs=dict(diameter_m=20,distance_m=30)
    printed=effects.fireball_view_factor(effects.FireballViewFactorInput(**kwargs,geometry_basis="api581_printed"))
    sphere=effects.fireball_view_factor(effects.FireballViewFactorInput(**kwargs,geometry_basis="elevated_sphere_maximum"))
    assert printed.outputs.view_factor == pytest.approx(400/1300)
    assert printed.outputs.model_center_distance_m == pytest.approx(math.sqrt(1300)/2)
    assert printed.outputs.attenuation_path_m == 30
    assert sphere.outputs.view_factor == pytest.approx(100/1125)
    assert printed.input_hash != sphere.input_hash
    assert printed.outputs.geometry_basis == "api581_printed"


@pytest.mark.parametrize("basis",["api581_printed","elevated_sphere_maximum"])
def test_constant_attenuation_inverse_matches_analytic_solution(basis):
    setup=dict(diameter_m=20,surface_emissive_power_w_m2=200000,atmosphere=atmosphere(),geometry_basis=basis)
    threshold=12600
    answer=effects.fireball_distance(effects.FireballDistanceInput(**setup,threshold_w_m2=threshold,
        maximum_distance_m=500,distance_tolerance_m=1e-7)).outputs
    analytic=20*math.sqrt(.8*200000/threshold-1) if basis == "api581_printed" else math.sqrt(100*.8*200000/threshold-225)
    assert 0 <= answer.safe_distance_m-analytic <= 1e-7
    assert answer.consequence_area_m2 == pytest.approx(math.pi*analytic**2,rel=1e-8)
    assert answer.status == "threshold_solved"
    assert answer.flux_residual_w_m2 <= 0


@pytest.mark.parametrize("basis",["api581_printed","elevated_sphere_maximum"])
def test_water_attenuation_threshold_reconstructs_safe_flux(basis):
    setup=dict(diameter_m=20,surface_emissive_power_w_m2=200000,
        atmosphere=effects.AtmosphereInput(transmissivity_model="api_water_vapor",water_partial_pressure_pa=1800),geometry_basis=basis)
    answer=effects.fireball_distance(effects.FireballDistanceInput(**setup,threshold_w_m2=12600,maximum_distance_m=1000)).outputs
    at=effects.fireball_radiation_flux(effects.FireballRadiationFluxInput(**setup,distance_m=answer.safe_distance_m)).outputs
    inside=effects.fireball_radiation_flux(effects.FireballRadiationFluxInput(**setup,distance_m=answer.safe_distance_m-1e-5)).outputs
    assert at.received_flux_w_m2 <= 12600 <= inside.received_flux_w_m2
    assert at.received_flux_w_m2 == pytest.approx(12600,abs=.01)
    assert at.transmissivity == pytest.approx(min(1,1.085*(1.8*at.attenuation_path_m)**(-.09)))


@pytest.mark.parametrize("basis,expected",[("api581_printed",1),("elevated_sphere_maximum",4/9)])
def test_origin_geometry_and_capped_zero_path_limit(basis,expected):
    result=effects.fireball_radiation_flux(effects.FireballRadiationFluxInput(diameter_m=20,distance_m=0,
        surface_emissive_power_w_m2=1000,geometry_basis=basis,
        atmosphere=effects.AtmosphereInput(transmissivity_model="api_water_vapor",water_partial_pressure_pa=0))).outputs
    assert result.view_factor == pytest.approx(expected)
    assert result.transmissivity == 1
    assert result.received_flux_w_m2 == pytest.approx(1000*expected)


@pytest.mark.parametrize("tau,power",[(0,200000),(1,0),(1,100)])
def test_no_threshold_crossing_reports_no_root(tau,power):
    result=effects.fireball_distance(effects.FireballDistanceInput(diameter_m=20,surface_emissive_power_w_m2=power,
        atmosphere=atmosphere(tau),geometry_basis="api581_printed",threshold_w_m2=12600,maximum_distance_m=100)).outputs
    assert result.status == "below_limit_at_origin"
    assert result.safe_distance_m == result.consequence_area_m2 == 0
    assert result.flux_residual_w_m2 is None


def test_bracket_and_iteration_failures_are_explicit():
    setup=dict(diameter_m=20,surface_emissive_power_w_m2=200000,atmosphere=atmosphere(),
        geometry_basis="api581_printed",threshold_w_m2=12600)
    with pytest.raises(DomainError) as exc:
        effects.fireball_distance(effects.FireballDistanceInput(**setup,maximum_distance_m=1))
    assert exc.value.code == "unbracketed_threshold"
    with pytest.raises(DomainError) as exc:
        effects.fireball_distance(effects.FireballDistanceInput(**setup,maximum_distance_m=1000,
            maximum_iterations=10,distance_tolerance_m=1e-10))
    assert exc.value.code == "nonconvergent_threshold"


def consequence_request(**updates):
    values=dict(available_mass_kg=2000,flammable_mass_fraction=.5,heat_of_combustion_j_kg=46e6,
        burst_pressure_pa_abs=1e6,atmosphere=atmosphere(),geometry_basis="elevated_sphere_maximum",maximum_distance_m=1000)
    return effects.FireballConsequenceInput(**(values|updates))


def test_composite_reconstructs_individual_calculations():
    result=effects.fireball_consequence(consequence_request()).outputs
    mass=effects.fireball_mass(effects.FireballMassInput(available_mass_kg=2000,flammable_mass_fraction=.5)).outputs.flammable_mass_kg
    geometry=effects.fireball_geometry(effects.FireballGeometryInput(flammable_mass_kg=mass)).outputs
    beta=effects.fireball_radiative_fraction(effects.FireballRadiativeFractionInput(burst_pressure_pa_abs=1e6)).outputs.radiative_fraction
    emissive=effects.fireball_emissive_power(effects.FireballEmissivePowerInput(flammable_mass_kg=mass,
        heat_of_combustion_j_kg=46e6,radiative_fraction=beta,diameter_m=geometry.diameter_m,duration_s=geometry.duration_s)).outputs.surface_emissive_power_w_m2
    assert result.flammable_mass_kg == mass == 1000
    assert result.diameter_m == geometry.diameter_m
    assert result.surface_emissive_power_w_m2 == emissive
    for label,threshold in [("personnel",12600),("equipment",37800)]:
        distance=effects.fireball_distance(effects.FireballDistanceInput(diameter_m=geometry.diameter_m,
            surface_emissive_power_w_m2=emissive,atmosphere=atmosphere(),geometry_basis="elevated_sphere_maximum",
            threshold_w_m2=threshold,maximum_distance_m=1000)).outputs
        assert getattr(result,label+"_area_m2") == distance.consequence_area_m2
        assert getattr(result,label+"_safe_distance_m") == distance.safe_distance_m
    assert result.personnel_area_m2 > result.equipment_area_m2 > 0


@pytest.mark.parametrize("updates",[{"available_mass_kg":0},{"flammable_mass_fraction":0}])
def test_zero_flammable_mass_is_explicit(updates):
    result=effects.fireball_consequence(consequence_request(**updates)).outputs
    assert result.personnel_status == result.equipment_status == "no_flammable_mass"
    assert result.diameter_m == result.duration_s == result.personnel_area_m2 == result.equipment_area_m2 == 0


def test_invalid_atmosphere_is_rejected_even_for_zero_mass():
    with pytest.raises(DomainError):
        effects.fireball_consequence(consequence_request(available_mass_kg=0,
            atmosphere=effects.AtmosphereInput(transmissivity_model="constant")))


def test_pressure_correlation_above_unity_is_rejected():
    with pytest.raises(DomainError):
        effects.fireball_consequence(consequence_request(burst_pressure_pa_abs=1e10))


def test_geometry_choice_is_mandatory_and_negative_distance_rejected():
    with pytest.raises(ValidationError):
        effects.FireballViewFactorInput(diameter_m=10,distance_m=1)
    with pytest.raises(ValidationError):
        effects.FireballViewFactorInput(diameter_m=10,distance_m=-1,geometry_basis="api581_printed")


def test_fireball_duration_source_branch_boundary():
    for mass in [29937,29937.01]:
        result=effects.fireball_geometry(effects.FireballGeometryInput(flammable_mass_kg=mass)).outputs
        assert result.duration_s == pytest.approx(.45*mass**.333 if mass <= 29937 else 2.6*mass**.167)


def test_view_factor_underflow_raises_domain_error():
    with pytest.raises(DomainError) as exc:
        effects.fireball_view_factor(effects.FireballViewFactorInput(diameter_m=1e-200,distance_m=1e200,geometry_basis="api581_printed"))
    assert exc.value.code == "numerical_failure"
