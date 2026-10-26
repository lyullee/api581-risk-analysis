"""Source units plus independent numerical surface integration of oblique cylinder."""
import math
import pytest
from api581 import DomainError
from api581.api import effects, properties


def integrated_view_factors(length,distance,tilt,axial_steps=180,angular_steps=240):
    """Direct Lambertian side-surface integral, not the production closed form.

    Radius1. Surface p(t,phi)=(t*sin(theta)+cos(phi),sin(phi),t*cos(theta)).
    Oriented area is cross(dp/dphi,dp/dt); receiver is ground-level in tilt plane.
    Visibility limits follow n_source dot(target-p)>0.
    """
    sin,cos=math.sin(tilt),math.cos(tilt)
    phi_max=math.acos(1/distance)
    dt=length/axial_steps
    dp=2*phi_max/angular_steps
    vertical=horizontal=0.0
    for j in range(angular_steps):
        angle=-phi_max+(j+.5)*dp
        cp,sp=math.cos(angle),math.sin(angle)
        oriented_area=(cp*cos,sp*cos,-cp*sin)
        for i in range(axial_steps):
            t=(i+.5)*dt
            point=(t*sin+cp,sp,t*cos)
            ray=(distance-point[0],-point[1],-point[2])
            squared=sum(value*value for value in ray)
            source_dot=sum(a*b for a,b in zip(oriented_area,ray))
            kernel=max(0,source_dot)/(math.pi*squared*squared)*dt*dp
            vertical+=kernel*max(0,distance-point[0])
            horizontal+=kernel*max(0,point[2])
    return vertical,horizontal


@pytest.mark.parametrize("length,distance,tilt", [(3,4,0),(3,4,.3),(3,5,.7),(10,15,.5)])
def test_geometry_checked_closed_form_matches_independent_surface_integral(length,distance,tilt):
    result=effects.pool_cylinder_view_factor(effects.PoolCylinderViewFactorInput(length_radius_ratio=length,
        distance_radius_ratio=distance,flame_tilt_rad=tilt,equation_basis="geometry_checked")).outputs
    vertical,horizontal=integrated_view_factors(length,distance,tilt)
    assert result.vertical_view_factor == pytest.approx(vertical,rel=2e-5)
    assert result.horizontal_view_factor == pytest.approx(horizontal,rel=2e-5)
    assert result.maximum_view_factor == pytest.approx(math.hypot(vertical,horizontal),rel=2e-5)
    assert result.physical_range


def test_literal_printed_fv_is_retained_as_distinct_model_not_silently_fixed():
    printed=effects.pool_cylinder_view_factor(effects.PoolCylinderViewFactorInput(length_radius_ratio=3,
        distance_radius_ratio=4,flame_tilt_rad=.3,equation_basis="api581_printed"))
    checked=effects.pool_cylinder_view_factor(effects.PoolCylinderViewFactorInput(length_radius_ratio=3,
        distance_radius_ratio=4,flame_tilt_rad=.3,equation_basis="geometry_checked"))
    assert printed.outputs.vertical_view_factor == pytest.approx(.20544889634842856)
    assert checked.outputs.vertical_view_factor == pytest.approx(.12447492698662549)
    assert printed.outputs.horizontal_view_factor == checked.outputs.horizontal_view_factor
    assert printed.input_hash != checked.input_hash


def test_view_factor_domain_excludes_flame_projection():
    with pytest.raises(DomainError):
        effects.pool_cylinder_view_factor(effects.PoolCylinderViewFactorInput(length_radius_ratio=3,
            distance_radius_ratio=2,flame_tilt_rad=.5,equation_basis="geometry_checked"))


def test_humidity_percent_conversion_and_physical_pressure_bound():
    half=properties.water_partial_pressure(properties.WaterPartialPressureInput(ambient_temperature_k=300,relative_humidity_fraction=.5)).outputs.water_partial_pressure_pa
    full=properties.water_partial_pressure(properties.WaterPartialPressureInput(ambient_temperature_k=300,relative_humidity_fraction=1)).outputs.water_partial_pressure_pa
    assert half == pytest.approx(1779.5121090521502)
    assert 1500 < half < 2000  # fraction/percent error would be a factor100.
    assert full == 2*half
    assert properties.water_partial_pressure(properties.WaterPartialPressureInput(ambient_temperature_k=300,relative_humidity_fraction=0)).outputs.water_partial_pressure_pa == 0
    with pytest.raises(DomainError):
        properties.water_partial_pressure(properties.WaterPartialPressureInput(ambient_temperature_k=500,relative_humidity_fraction=1))


def test_transmissivity_units_cap_dry_limit_and_underflow():
    def tau(pressure,distance):
        return effects.atmospheric_transmissivity(effects.AtmosphericTransmissivityInput(water_partial_pressure_pa=pressure,path_length_m=distance)).outputs
    assert tau(1000,100).transmissivity == pytest.approx(1.085*100**(-.09))
    assert tau(2000,50).transmissivity == tau(1000,100).transmissivity
    capped=tau(1000,1)
    assert capped.transmissivity == 1 and capped.uncapped_transmissivity == 1.085
    dry=tau(0,10)
    assert dry.transmissivity == 1 and dry.uncapped_transmissivity is None and dry.dry_air_limit
    assert tau(5e-324,1e300).transmissivity == 1


def flame(**changes):
    return effects.PoolFlameGeometryInput(**{**dict(pool_radius_m=5,burning_rate_kg_m2_s=.05,
        air_density_kg_m3=1.2,vapor_density_kg_m3=2,wind_speed_m_s=0),**changes})


def test_flame_length_wind_floor_and_distinct_density_roles():
    calm=effects.pool_flame_geometry(flame()).outputs
    weak=effects.pool_flame_geometry(flame(wind_speed_m_s=.01)).outputs
    windy=effects.pool_flame_geometry(flame(wind_speed_m_s=5)).outputs
    assert calm.nondimensional_wind_speed == weak.nondimensional_wind_speed == 1
    assert calm.flame_tilt_rad == 0 and calm.flame_length_m == weak.flame_length_m
    assert windy.flame_tilt_rad > 0 and windy.flame_length_m < calm.flame_length_m
    denser_air=effects.pool_flame_geometry(flame(wind_speed_m_s=5,air_density_kg_m3=2.4)).outputs
    assert denser_air.nondimensional_wind_speed == windy.nondimensional_wind_speed
    assert denser_air.flame_length_m/windy.flame_length_m == pytest.approx(2**(-.67))
    assert math.cos(windy.flame_tilt_rad) == pytest.approx(windy.nondimensional_wind_speed**(-.5))


def test_unrepresentable_flame_geometry_is_a_numerical_error():
    with pytest.raises(DomainError) as error:
        effects.pool_flame_geometry(flame(wind_speed_m_s=1e308))
    assert error.value.code == "numerical_failure"


def test_surface_emission_conserves_radiated_power_and_has_flux_units():
    out=effects.pool_surface_emissive_power(effects.PoolSurfaceEmissivePowerInput(pool_radius_m=5,flame_length_m=15,
        burning_rate_kg_m2_s=.05,heat_of_combustion_j_kg=46e6,radiative_fraction=.35)).outputs
    assert out.burning_mass_rate_kg_s == pytest.approx(.05*math.pi*25)
    assert out.surface_emissive_power_w_m2*out.emitting_surface_area_m2 == pytest.approx(out.radiated_power_w)
    assert out.radiated_power_w == pytest.approx(.35*out.burning_mass_rate_kg_s*46e6)


def test_mixture_burning_is_mole_weighted_and_not_renormalized():
    out=effects.pool_mixture_burning_rate(effects.PoolMixtureBurningRateInput(components=[
        effects.MixtureComponentInput(mole_fraction=.25,burning_rate_kg_m2_s=.04),
        effects.MixtureComponentInput(mole_fraction=.75,burning_rate_kg_m2_s=.08)])).outputs
    assert out.burning_rate_kg_m2_s == pytest.approx(.07)
    with pytest.raises(DomainError):
        effects.pool_mixture_burning_rate(effects.PoolMixtureBurningRateInput(components=[
            effects.MixtureComponentInput(mole_fraction=.3,burning_rate_kg_m2_s=.04)]))


def setup(**changes):
    return {**dict(pool_radius_m=2,flame_length_m=6,flame_tilt_rad=0,surface_emissive_power_w_m2=100000,
        atmosphere=effects.AtmosphereInput(transmissivity_model="constant",constant_transmissivity=.8),
        equation_basis="geometry_checked",distance_convention="surface_to_axis"),**changes}


def test_surface_axis_conversion_is_explicit_and_transmission_is_separate():
    physical=effects.pool_radiation_flux(effects.PoolRadiationFluxInput(**setup(),surface_distance_m=10)).outputs
    printed_distance=effects.pool_radiation_flux(effects.PoolRadiationFluxInput(**setup(distance_convention="printed_surface_ratio"),surface_distance_m=10)).outputs
    assert physical.view_factor_distance_m == 12 and printed_distance.view_factor_distance_m == 10
    assert physical.received_flux_w_m2 < printed_distance.received_flux_w_m2
    assert physical.received_flux_w_m2 == pytest.approx(.8*100000*physical.maximum_view_factor)


def test_nonphysical_printed_view_factor_cannot_feed_a_flux():
    raw=effects.pool_cylinder_view_factor(effects.PoolCylinderViewFactorInput(length_radius_ratio=10,
        distance_radius_ratio=5.8,flame_tilt_rad=.5,equation_basis="api581_printed")).outputs
    assert not raw.physical_range
    with pytest.raises(DomainError) as error:
        effects.pool_radiation_flux(effects.PoolRadiationFluxInput(**setup(pool_radius_m=1,flame_length_m=10,
            flame_tilt_rad=.5,equation_basis="api581_printed"),surface_distance_m=4.8))
    assert error.value.code == "invalid_view_factor"


@pytest.mark.parametrize("water_pressure", [None,1500])
def test_threshold_root_reproduces_selected_flux_and_area(water_pressure):
    atmosphere=(effects.AtmosphereInput(transmissivity_model="constant",constant_transmissivity=.8) if water_pressure is None else
        effects.AtmosphereInput(transmissivity_model="api_water_vapor",water_partial_pressure_pa=water_pressure))
    settings=setup(atmosphere=atmosphere)
    out=effects.pool_fire_distance(effects.PoolFireDistanceInput(**settings,threshold_w_m2=12600,maximum_surface_distance_m=100)).outputs
    received=effects.pool_radiation_flux(effects.PoolRadiationFluxInput(**settings,surface_distance_m=out.safe_surface_distance_m)).outputs.received_flux_w_m2
    assert out.status == "threshold_solved"
    assert received <= 12600 and received == pytest.approx(12600,rel=1e-5)
    assert out.consequence_area_m2 == pytest.approx(math.pi*(out.safe_surface_distance_m+2)**2)


def test_two_distance_conventions_move_constant_tau_root_by_one_radius():
    physical=effects.pool_fire_distance(effects.PoolFireDistanceInput(**setup(),threshold_w_m2=12600,maximum_surface_distance_m=100)).outputs
    printed=effects.pool_fire_distance(effects.PoolFireDistanceInput(**setup(distance_convention="printed_surface_ratio"),
        threshold_w_m2=12600,maximum_surface_distance_m=100)).outputs
    assert printed.safe_surface_distance_m-physical.safe_surface_distance_m == pytest.approx(2,abs=2e-5)


def test_boundary_case_is_not_a_claimed_threshold_solution():
    out=effects.pool_fire_distance(effects.PoolFireDistanceInput(**setup(),threshold_w_m2=1e6,maximum_surface_distance_m=100)).outputs
    assert out.status == "below_limit_at_domain_boundary"
    assert out.safe_surface_distance_m == 0 and out.consequence_area_m2 == pytest.approx(math.pi*4)
    assert out.flux_residual_w_m2 is None and out.iterations == 0


def test_bracket_and_convergence_failures_are_explicit():
    with pytest.raises(DomainError) as error:
        effects.pool_fire_distance(effects.PoolFireDistanceInput(**setup(),threshold_w_m2=100,maximum_surface_distance_m=1))
    assert error.value.code == "unbracketed_threshold"
    with pytest.raises(DomainError) as error:
        effects.pool_fire_distance(effects.PoolFireDistanceInput(**setup(),threshold_w_m2=12600,
            maximum_surface_distance_m=100,maximum_iterations=10,distance_tolerance_m=1e-12))
    assert error.value.code == "nonconvergent_threshold"


@pytest.mark.parametrize("tilt", [0,.3,.7])
def test_checked_flux_decreases_in_external_domain(tilt):
    boundary=6*math.sin(tilt)
    values=[effects.pool_radiation_flux(effects.PoolRadiationFluxInput(**setup(flame_tilt_rad=tilt),
        surface_distance_m=boundary+d)).outputs.received_flux_w_m2 for d in (.01,.1,1,2,5,10,30,100)]
    assert values == sorted(values,reverse=True)


def request(**changes):
    return effects.PoolFireConsequenceInput(**{**dict(burning=effects.PoolBurningInput(heat_of_combustion_j_kg=46e6,
        latent_heat_j_kg=350000,boiling=True),liquid_rate_kg_s=5,available_liquid_mass_kg=5000,liquid_density_kg_m3=700,
        site_maximum_area_m2=500,air_density_kg_m3=1.2,vapor_density_kg_m3=2,wind_speed_m_s=2,
        atmosphere=effects.AtmosphereInput(transmissivity_model="constant",constant_transmissivity=.8),
        equation_basis="geometry_checked",distance_convention="surface_to_axis",maximum_surface_distance_m=1000),**changes})


def test_composed_pool_consequence_includes_full_geometry_and_status():
    out=effects.pool_fire_consequence(request()).outputs
    assert out.pool_area_m2 <= min(out.burning_area_m2,out.inventory_limited_area_m2,500)
    assert out.personnel_area_m2 >= out.equipment_area_m2 >= out.pool_area_m2
    assert out.personnel_status == "threshold_solved"
    assert out.equipment_status == "below_limit_at_domain_boundary"
    assert out.flame_length_m > 0 and out.flame_tilt_rad > 0


def test_no_pool_has_zero_consequence_and_still_checks_atmosphere_contract():
    out=effects.pool_fire_consequence(request(available_liquid_mass_kg=0)).outputs
    assert out.personnel_area_m2 == out.equipment_area_m2 == 0
    assert out.personnel_status == out.equipment_status == "no_pool"
    with pytest.raises(DomainError):
        effects.pool_fire_consequence(request(available_liquid_mass_kg=0,
            atmosphere=effects.AtmosphereInput(transmissivity_model="constant")))
