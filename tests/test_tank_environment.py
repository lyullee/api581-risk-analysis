"""Hand-calculated AST environmental allocation and cost verification."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import tank, financial

RATES = dict(small=1., medium=2., large=3., rupture=4.)
VOLUMES = dict(small=100., medium=200., large=300., rupture=1000.)
COSTS = dict(in_dike=10., surface_on_site=50., surface_off_site=250., subsoil=1500., groundwater=5000., surface_water=1500.)
BASIS = dict(generic_frequency_by_hole_per_year=RATES, cost_by_location_per_bbl=COSTS,
    fraction_leaving_dike=.8, fraction_on_site=.25, fraction_off_site=.5,
    currency="USD", cost_basis="2016 Table6.6 medium source estimates; price year unspecified")


@pytest.mark.parametrize("sensitivity,expected", [
    ("low", [10,50,100,500,1000,500]), ("medium", [10,50,250,1500,5000,1500]),
    ("high", [10,50,500,3000,10000,5000])])
def test_all_table_66_cells(sensitivity, expected):
    result = tank.environment_cost_table(tank.EnvironmentCostTableInput(sensitivity=sensitivity))
    assert list(result.outputs.cost_by_location_usd_per_bbl.values()) == expected
    assert "no explicit price year" in result.limitations[0]


def test_sequential_conditional_fractions_hand_anchor():
    result = tank.surface_spill_partition(tank.SurfaceSpillPartitionInput(released_volume_bbl=100,
        fraction_leaving_dike=.8, fraction_on_site=.25, fraction_off_site=.5)).outputs
    assert result.model_dump() == pytest.approx(dict(in_dike_bbl=20, surface_on_site_bbl=20,
        surface_off_site_bbl=30, surface_water_bbl=30))


@pytest.mark.parametrize("leave,on_site,off_site", [(0,0,0),(1,1,1),(1,0,1),(1,0,0),(.8,.9,.7)])
def test_surface_conservation_and_fraction_boundaries(leave,on_site,off_site):
    r = tank.surface_spill_partition(tank.SurfaceSpillPartitionInput(released_volume_bbl=73,
        fraction_leaving_dike=leave, fraction_on_site=on_site, fraction_off_site=off_site)).outputs
    assert math.fsum(r.model_dump().values()) == pytest.approx(73)
    assert min(r.model_dump().values()) >= 0


@pytest.mark.parametrize("distance,velocity,arrival,status", [
    (10,2,5,"finite_travel"), (0,0,0,"already_at_groundwater"), (10,0,None,"no_finite_arrival")])
def test_groundwater_arrival_zero_cases(distance, velocity, arrival, status):
    r = tank.groundwater_arrival(tank.GroundwaterArrivalInput(distance_to_groundwater_m=distance,
        seepage_velocity_m_day=velocity)).outputs
    assert (r.arrival_time_days,r.arrival_status) == (arrival,status)


@pytest.mark.parametrize("arrival,expected", [(None,0),(0,100),(3,70),(10,0),(11,0)])
def test_subsurface_detection_time_piecewise(arrival,expected):
    r = tank.subsurface_spill_partition(tank.SubsurfaceSpillPartitionInput(leaked_volume_bbl=100,
        detection_time_days=10,groundwater_arrival_time_days=arrival)).outputs
    assert r.groundwater_bbl == pytest.approx(expected)
    assert r.subsoil_bbl+r.groundwater_bbl == pytest.approx(100)


def test_shell_weight_once_including_rupture_in_leak_denominator():
    r = tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**BASIS,released_volume_by_hole_bbl=VOLUMES)).outputs
    # (1*100+2*200+3*300)/10=140, and 4*1000/10=400.
    # Partition per bbl: .2,.2,.3,.3 -> 2+10+75+450=537 currency/bbl.
    assert r.weighted_leak_volume_bbl == pytest.approx(140)
    assert r.weighted_rupture_volume_bbl == pytest.approx(400)
    assert r.leak_environment_cost == pytest.approx(75180)
    assert r.rupture_environment_cost == pytest.approx(214800)
    assert r.environment_cost == pytest.approx(289980)
    # Independent scenario-by-scenario costs yield the same total.
    assert r.environment_cost == pytest.approx(sum(RATES[h]*VOLUMES[h]*537 for h in RATES)/10)


def test_bottom_groundwater_partition_and_surface_rupture_hand_anchor():
    r = tank.bottom_environment_cost(tank.BottomEnvironmentCostInput(**BASIS,
        leaked_volume_by_hole_bbl={h:VOLUMES[h] for h in ("small","medium","large")},
        total_tank_volume_bbl=1000,detection_time_days=10,groundwater_arrival_time_days=3)).outputs
    assert r.weighted_groundwater_volume_bbl == pytest.approx(98)
    assert r.weighted_subsoil_volume_bbl == pytest.approx(42)
    assert r.leak_environment_cost == pytest.approx(553000)
    assert r.rupture_environment_cost == pytest.approx(214800)
    assert r.environment_cost == pytest.approx(767800)


def test_frequency_scale_invariance_and_large_rates():
    def call(rates):
        return tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**(BASIS|dict(generic_frequency_by_hole_per_year=rates)),
            released_volume_by_hole_bbl=VOLUMES)).outputs.environment_cost
    assert call({h:v*1e-6 for h,v in RATES.items()}) == pytest.approx(call(RATES))
    # Direct sum would overflow; scale-free normalization still works.
    assert call(dict.fromkeys(RATES,1e308)) == pytest.approx(400*537)


def test_currency_and_price_conversion_affects_only_cost():
    a = tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**BASIS,released_volume_by_hole_bbl=VOLUMES)).outputs
    b = tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**(BASIS|dict(
        cost_by_location_per_bbl={k:v*1300 for k,v in COSTS.items()},currency="KRW",cost_basis="qualified scenario FX=1300")),
        released_volume_by_hole_bbl=VOLUMES)).outputs
    assert b.environment_cost == pytest.approx(a.environment_cost*1300)
    assert b.weighted_leak_surface_volumes_bbl == a.weighted_leak_surface_volumes_bbl


def test_bottom_repair_only_rupture_scales_and_material_multiplies():
    costs = financial.repair_table(financial.RepairTableInput(component_type="TANKBOTTOM")).outputs
    factor = financial.material_factor(financial.MaterialFactorInput(material_id="304_ss")).outputs.material_factor
    r = tank.bottom_repair_cost(tank.BottomRepairCostInput(generic_frequency_by_hole_per_year=RATES,
        tank_diameter_m=61,repair_cost_by_hole=costs.cost_by_hole_usd_2001,material_factor=factor,
        currency="USD",cost_basis="Table4.15 USD2001")).outputs
    assert r.component_repair_cost == pytest.approx((.1*5000+.4*120000*4)*3.2)


@pytest.mark.parametrize("field,value", [
    ("generic_frequency_by_hole_per_year",dict(small=1)),
    ("generic_frequency_by_hole_per_year",dict.fromkeys(RATES,0)),
    ("cost_by_location_per_bbl",dict(in_dike=10)), ("cost_basis","   ")])
def test_incomplete_or_empty_basis_rejected(field,value):
    with pytest.raises(DomainError):
        tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**(BASIS|{field:value}),released_volume_by_hole_bbl=VOLUMES))


@pytest.mark.parametrize("value", [True,"0.8",float("inf"),float("nan"),-1,80])
def test_fraction_validation(value):
    with pytest.raises(ValidationError):
        tank.SurfaceSpillPartitionInput(released_volume_bbl=100,fraction_leaving_dike=value,
            fraction_on_site=0,fraction_off_site=0)


def test_numerical_extremes_are_explicit_domain_failures():
    with pytest.raises(DomainError) as exc:
        tank.groundwater_arrival(tank.GroundwaterArrivalInput(distance_to_groundwater_m=1e308,seepage_velocity_m_day=1e-308))
    assert exc.value.code == "numerical_failure"
    with pytest.raises(DomainError):
        tank.shell_environment_cost(tank.ShellEnvironmentCostInput(**(BASIS|dict(cost_by_location_per_bbl=dict.fromkeys(COSTS,1e308))),
            released_volume_by_hole_bbl=VOLUMES))


def test_zero_detection_not_silently_substituted():
    with pytest.raises(ValidationError):
        tank.SubsurfaceSpillPartitionInput(leaked_volume_bbl=0,detection_time_days=0,groundwater_arrival_time_days=None)
