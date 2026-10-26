"""AST native units, piecewise hydraulics and dimensional inventory checks."""
import math
import pytest
from api581 import DomainError
from api581.api import tank


@pytest.mark.parametrize("fluid,rho,mu",[("gasoline",684.018,.00401),("light_diesel",734.011,.00104),
    ("heavy_diesel",764.527,.00246),("fuel_oil",775.019,.0369),("crude_oil",775.019,.0369),
    ("heavy_fuel_oil",900.026,.046),("heavy_crude_oil",900.026,.046)])
def test_si_fluid_table_rows(fluid,rho,mu):
    r=tank.fluid_table(tank.FluidTableInput(fluid=fluid)).outputs
    assert r.liquid_density_kg_m3 == rho and r.dynamic_viscosity_pa_s == mu


@pytest.mark.parametrize("soil,lower,upper,porosity",[("coarse_sand",.1,.01,.33),("fine_sand",.01,.001,.33),
    ("very_fine_sand",.001,.00001,.33),("silt",1e-5,1e-6,.41),("sandy_clay",1e-6,1e-7,.45),
    ("clay",1e-7,1e-8,.5),("concrete_asphalt",1e-10,1e-11,.3),("gravel",1,10,.4)])
def test_si_soil_printed_bound_order_and_mean(soil,lower,upper,porosity):
    r=tank.soil_table(tank.SoilTableInput(soil=soil)).outputs
    assert (r.printed_lower_bound_cm_s,r.printed_upper_bound_cm_s,r.porosity) == (lower,upper,porosity)
    mean=tank.soil_water_conductivity(tank.SoilWaterConductivityInput(**r.model_dump(exclude={"porosity"}))).outputs
    assert mean.water_hydraulic_conductivity_m_day == pytest.approx(864*(lower+upper)/2)


def test_fluid_conductivity_density_viscosity_and_seepage():
    r=tank.fluid_conductivity(tank.FluidConductivityInput(water_hydraulic_conductivity_m_day=47.52,
        liquid_density_kg_m3=684.018,dynamic_viscosity_pa_s=.00401,water_density_kg_m3=1000,water_dynamic_viscosity_pa_s=.001)).outputs
    expected=47.52*684.018/1000*.001/.00401
    assert r.product_hydraulic_conductivity_m_day == pytest.approx(expected)
    velocity=tank.seepage_velocity(tank.SeepageVelocityInput(product_hydraulic_conductivity_m_day=expected,porosity=.33)).outputs
    assert velocity.seepage_velocity_m_day == pytest.approx(expected/.33)
    with pytest.raises(DomainError):
        tank.seepage_velocity(tank.SeepageVelocityInput(product_hydraulic_conductivity_m_day=expected,porosity=0))


@pytest.mark.parametrize("diameter,count",[(30.5,1),(61,4),(91.4,9),(10,1)])
def test_bottom_hole_count_table_and_formula(diameter,count):
    r=tank.bottom_hole_count(tank.BottomHoleCountInput(tank_diameter_m=diameter)).outputs
    assert r.small_hole_count == count and r.medium_hole_count == r.large_hole_count == 0
    assert r.outside_tabulated_diameter_range == (diameter < 30.5 or diameter > 91.4)


def test_bottom_and_shell_inventory_use_lower_course_edge_and_si_mass():
    r=tank.bottom_inventory(tank.BottomInventoryInput(tank_diameter_m=30.5,fill_height_m=10,liquid_density_kg_m3=700)).outputs
    assert r.available_volume_m3 == pytest.approx(math.pi*30.5**2/4*10)
    assert r.available_volume_bbl == pytest.approx(r.available_volume_m3*6.29)
    assert r.available_mass_kg == pytest.approx(r.available_volume_m3*700)
    s=tank.shell_course_inventory(tank.ShellCourseInventoryInput(tank_diameter_m=30.5,fill_height_m=10,
        course_index=3,course_height_m=2,liquid_density_kg_m3=700)).outputs
    assert s.available_liquid_head_m == 6 and s.course_bottom_elevation_m == 4
    assert s.available_volume_m3 == pytest.approx(r.available_volume_m3*.6)
    dry=tank.shell_course_inventory(tank.ShellCourseInventoryInput(tank_diameter_m=30.5,fill_height_m=10,
        course_index=7,course_height_m=2,liquid_density_kg_m3=700)).outputs
    assert not dry.course_wet and dry.available_volume_m3 == dry.available_mass_kg == 0


def test_shell_native_rate_mm_area_and_rounded_unit_conversion():
    r=tank.shell_flow(tank.ShellFlowInput(hole_diameter_m=.003175,liquid_head_m=10,liquid_density_kg_m3=700)).outputs
    expected=.543*.61*math.pi*3.175**2/4*math.sqrt(2*9.81*10)
    assert r.native_rate_bbl_day == pytest.approx(expected)
    assert r.volume_rate_m3_s == pytest.approx(expected/6.29/86400)
    assert r.mass_rate_kg_s == pytest.approx(r.volume_rate_m3_s*700)
    torricelli=.61*math.pi*.003175**2/4*math.sqrt(2*9.81*10)
    assert r.volume_rate_m3_s/torricelli == pytest.approx(.543e6/(6.29*86400))


def bottom(**updates):
    return tank.BottomFlowInput(**(dict(hole_diameter_m=.003175,liquid_height_m=10,liquid_density_kg_m3=700,
        product_hydraulic_conductivity_m_day=1,number_of_holes=4,has_release_prevention_barrier=False,
        transition_hole_basis="api581_printed")|updates))


@pytest.mark.parametrize("conductivity,equation",[(1e-8,"3.211"),(1,"3.212"),(10000,"3.210")])
def test_bottom_branch_formulas_and_independent_us_native_rates(conductivity,equation):
    r=tank.bottom_flow(bottom(product_hydraulic_conductivity_m_day=conductivity)).outputs
    assert r.equation == equation
    d,h,k=.125,10/.3048,conductivity/.3048
    if equation == "3.210":
        expected=16.03*math.pi*d*d*math.sqrt(2*32.2*h)*4
    elif equation == "3.211":
        expected=8.0592*.21*d**.2*h**.9*k**.74*4
    else:
        m=5.0489-.4324*math.log10(d)+.5405*math.log10(h)
        expected=403.95*10**(2*math.log10(d)+.5*math.log10(h)-.74*((7.2622+2*math.log10(d)-math.log10(k))/m)**m)
    assert r.native_rate_bbl_day == pytest.approx(expected,rel=.005)


def test_transition_printed_hole_omission_and_qualified_scaling_are_distinct():
    literal=tank.bottom_flow(bottom()).outputs
    scaled=tank.bottom_flow(bottom(transition_hole_basis="per_hole_scaled")).outputs
    assert literal.equation == scaled.equation == "3.212"
    assert literal.applied_hole_multiplier == 1 and scaled.applied_hole_multiplier == 4
    assert scaled.native_rate_bbl_day == 4*literal.native_rate_bbl_day


def test_bottom_threshold_equalities_and_prevention_barrier_head():
    ordinary=tank.bottom_flow(bottom()).outputs
    lower=tank.bottom_flow(bottom(product_hydraulic_conductivity_m_day=ordinary.lower_conductivity_threshold_m_day)).outputs
    upper=tank.bottom_flow(bottom(product_hydraulic_conductivity_m_day=ordinary.upper_conductivity_threshold_m_day)).outputs
    assert lower.equation == "3.211" and upper.equation == "3.212"
    barrier=tank.bottom_flow(bottom(has_release_prevention_barrier=True)).outputs
    assert barrier.liquid_head_used_m == .0762


@pytest.mark.parametrize("updates",[{"hole_diameter_m":0},{"number_of_holes":0},
    {"liquid_height_m":0,"has_release_prevention_barrier":True},{"product_hydraulic_conductivity_m_day":0}])
def test_inactive_or_empty_bottom_source_has_no_logarithm_or_fake_head_flow(updates):
    r=tank.bottom_flow(bottom(**updates)).outputs
    assert r.native_rate_bbl_day == 0 and r.equation == "zero_flow"


def test_shell_detection_printed_si_and_inch_boundary_require_selection():
    literal=tank.shell_detection_time(tank.ShellDetectionTimeInput(hole_diameter_m=.003175,diameter_boundary_basis="printed_3_17_mm")).outputs
    inch=tank.shell_detection_time(tank.ShellDetectionTimeInput(hole_diameter_m=.003175,diameter_boundary_basis="inch_0_125")).outputs
    assert literal.detection_time_days == 1 and inch.detection_time_days == 7


@pytest.mark.parametrize("foundation,barrier,days",[("concrete_asphalt",False,7),("other",True,30),("other",False,360)])
def test_bottom_detection_disjoint_rules(foundation,barrier,days):
    r=tank.bottom_detection_time(tank.BottomDetectionTimeInput(foundation=foundation,has_release_prevention_barrier=barrier)).outputs
    assert r.detection_time_days == days


def test_bottom_detection_overlap_has_no_hidden_precedence():
    with pytest.raises(DomainError):
        tank.bottom_detection_time(tank.BottomDetectionTimeInput(foundation="concrete_asphalt",has_release_prevention_barrier=True))
    for basis,days in [("foundation_priority",7),("barrier_priority",30)]:
        r=tank.bottom_detection_time(tank.BottomDetectionTimeInput(foundation="concrete_asphalt",has_release_prevention_barrier=True,overlap_basis=basis)).outputs
        assert r.detection_time_days == days


@pytest.mark.parametrize("rate,days,expected_bbl",[(10,7,70),(100,100,629),(0,7,0),(100,0,0)])
def test_leak_volume_duration_inventory_and_mass_index(rate,days,expected_bbl):
    r=tank.release_volume(tank.ReleaseVolumeInput(release_case="leak",native_rate_bbl_day=rate,
        available_volume_m3=100,liquid_density_kg_m3=700,detection_time_days=days)).outputs
    assert r.released_volume_bbl == pytest.approx(expected_bbl)
    assert r.printed_mass_index == r.released_volume_bbl
    assert r.released_mass_kg == pytest.approx(expected_bbl/6.29*700)
    assert r.release_type == "continuous"


def test_rupture_uses_inventory_without_inventing_instantaneous_duration():
    r=tank.release_volume(tank.ReleaseVolumeInput(release_case="rupture",native_rate_bbl_day=0,
        available_volume_m3=100,liquid_density_kg_m3=700,detection_time_days=7)).outputs
    assert r.released_volume_m3 == 100 and r.released_mass_kg == 70000
    assert r.printed_mass_index == 629 and r.release_duration_days is None
    assert r.release_type == "continuous"


def test_soil_conversion_retains_small_positive_water_conductivity():
    r=tank.soil_water_conductivity(tank.SoilWaterConductivityInput(printed_lower_bound_cm_s=math.ulp(0.0),printed_upper_bound_cm_s=0)).outputs
    assert r.water_hydraulic_conductivity_m_day > 0


def test_outside_source_contact_and_discharge_domains_rejected():
    with pytest.raises(DomainError):
        tank.bottom_flow(bottom(soil_contact_factor=.1))
    with pytest.raises(DomainError):
        tank.shell_flow(tank.ShellFlowInput(hole_diameter_m=.01,liquid_head_m=10,liquid_density_kg_m3=700,discharge_coefficient=.9))
