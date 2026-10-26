"""AST source integration checked against source tables and independent formulas."""
import math
import pytest
from api581 import DomainError
from api581.api import tank


def bottom(**changes):
    return tank.BottomSourceAssessmentInput(**(dict(tank_diameter_m=61.,fill_height_m=10.,fluid="gasoline",soil="coarse_sand",
        water_density_kg_m3=1000.,water_dynamic_viscosity_pa_s=.001,foundation="other",
        has_release_prevention_barrier=False,transition_hole_basis="api581_printed")|changes))


def shell(**changes):
    return tank.ShellSourceAssessmentInput(**(dict(tank_diameter_m=61.,fill_height_m=10.,course_index=2,
        course_height_m=2.,fluid="gasoline",diameter_boundary_basis="inch_0_125")|changes))


def test_shell_table_diameter_quarter_rupture_and_areas():
    r = tank.shell_hole_sizes(tank.ShellHoleSizesInput(tank_diameter_m=61)).outputs
    assert r.diameter_by_hole_m == dict(small=.003175,medium=.00635,large=.0508,rupture=15.25)
    assert r.area_by_hole_m2["rupture"] == pytest.approx(math.pi*15.25**2/4)


@pytest.mark.parametrize("rpb,diameter",[(False,.0127),(True,.003175)])
def test_bottom_table_zero_disabled_holes_and_quarter_rupture(rpb,diameter):
    r = tank.bottom_hole_sizes(tank.BottomHoleSizesInput(tank_diameter_m=61,has_release_prevention_barrier=rpb)).outputs
    assert r.diameter_by_hole_m == dict(small=diameter,medium=0,large=0,rupture=15.25)


def test_shell_source_manual_geometry_flow_and_release():
    r = tank.shell_source_assessment(shell()).outputs
    inventory = math.pi/4*61**2*8
    q = .543*.61*(math.pi/4*.003175**2*1e6)*math.sqrt(2*9.81*8)
    assert r.available_volume_m3 == pytest.approx(inventory)
    assert r.available_liquid_head_m == 8 and r.course_bottom_elevation_m == 2
    assert r.native_rate_by_hole_bbl_day["small"] == pytest.approx(q)
    assert r.released_volume_by_hole_bbl["small"] == pytest.approx(q*7)
    assert r.released_volume_by_hole_m3["small"] == pytest.approx(36.56359542215443)
    assert r.released_volume_by_hole_m3["rupture"] == pytest.approx(inventory)
    assert r.detection_time_by_hole_days == dict(small=7,medium=1,large=1,rupture=None)
    assert r.release_duration_by_hole_days["rupture"] is None
    # Eq3.209 nominal rupture rate scales by diameter squared, not inventory/time.
    assert r.native_rate_by_hole_bbl_day["rupture"]/q == pytest.approx((15.25/.003175)**2)


def test_shell_detection_boundary_changes_leak_not_rupture():
    a = tank.shell_source_assessment(shell()).outputs
    b = tank.shell_source_assessment(shell(diameter_boundary_basis="printed_3_17_mm")).outputs
    assert b.released_volume_by_hole_bbl["small"]*7 == pytest.approx(a.released_volume_by_hole_bbl["small"])
    assert a.released_volume_by_hole_bbl["rupture"] == b.released_volume_by_hole_bbl["rupture"]


@pytest.mark.parametrize("fill,index",[(0,1),(2,2),(2,3)])
def test_dry_course_has_no_inventory_or_release(fill,index):
    r = tank.shell_source_assessment(shell(fill_height_m=fill,course_index=index)).outputs
    assert not r.course_wet
    assert all(v == 0 for v in r.released_volume_by_hole_bbl.values())
    assert all(v == 0 for v in r.native_rate_by_hole_bbl_day.values())


def test_bottom_source_matches_independent_prior_source_anchor():
    r = tank.bottom_source_assessment(bottom()).outputs
    assert r.small_hole_count == 4
    assert r.product_hydraulic_conductivity_m_day == pytest.approx(47.52*684.018/1000*.001/.00401)
    assert r.seepage_velocity_m_day == pytest.approx(r.product_hydraulic_conductivity_m_day/.33)
    assert r.bottom_flow_equation == "3.212" and r.applied_small_hole_multiplier == 1
    assert r.native_rate_by_hole_bbl_day["small"] == pytest.approx(272.3323831447272)
    assert r.released_volume_by_hole_m3["small"] == pytest.approx(15586.591086184704)
    assert r.released_mass_by_hole_kg["small"] == pytest.approx(10661508.86158989)
    assert r.released_volume_by_hole_bbl["rupture"] == r.available_volume_bbl
    assert r.native_rate_by_hole_bbl_day["rupture"] is None
    assert r.mass_rate_by_hole_kg_s["rupture"] is None
    assert r.release_duration_by_hole_days["rupture"] is None
    assert r.released_volume_by_hole_bbl["medium"] == r.released_volume_by_hole_bbl["large"] == 0
    assert r.generic_total_per_year == pytest.approx(7.22e-4)
    assert r.printed_generic_total_per_year == 7.2e-4


def test_rpb_and_foundation_overlap_is_never_implicitly_resolved():
    with pytest.raises(DomainError):
        tank.bottom_source_assessment(bottom(has_release_prevention_barrier=True,foundation="concrete_asphalt"))
    r = tank.bottom_source_assessment(bottom(has_release_prevention_barrier=True,foundation="concrete_asphalt",
        detection_overlap_basis="foundation_priority")).outputs
    assert r.detection_time_days == 7 and r.detection_selected_basis == "concrete_asphalt"
    assert r.diameter_by_hole_m["small"] == .003175


def test_empty_rpb_tank_has_zero_release_and_undefined_rupture_rate():
    r = tank.bottom_source_assessment(bottom(fill_height_m=0,has_release_prevention_barrier=True)).outputs
    assert r.bottom_flow_equation == "zero_flow"
    assert r.released_volume_by_hole_bbl == dict(small=0,medium=0,large=0,rupture=0)
    assert r.native_rate_by_hole_bbl_day["rupture"] is None


def test_explicit_transition_count_basis_changes_rate_before_inventory_cap():
    a = tank.bottom_source_assessment(bottom()).outputs
    b = tank.bottom_source_assessment(bottom(transition_hole_basis="per_hole_scaled")).outputs
    assert b.native_rate_by_hole_bbl_day["small"] == pytest.approx(a.native_rate_by_hole_bbl_day["small"]*4)
    assert b.released_volume_by_hole_bbl["small"] <= b.available_volume_bbl
    assert b.released_volume_by_hole_bbl["rupture"] == a.released_volume_by_hole_bbl["rupture"]


@pytest.mark.parametrize("diameter,count",[(30.5,1),(61,4),(91.4,9),(10,1)])
def test_composed_hole_count_uses_whole_tank_diameter(diameter,count):
    r = tank.bottom_source_assessment(bottom(tank_diameter_m=diameter)).outputs
    assert r.small_hole_count == count
    assert r.outside_tabulated_diameter_range == (diameter < 30.5 or diameter > 91.4)


def test_source_numerical_failure_does_not_escape_as_nested_validation_error():
    with pytest.raises(DomainError):
        tank.shell_source_assessment(shell(tank_diameter_m=1e308))
    with pytest.raises(DomainError):
        tank.bottom_source_assessment(bottom(water_dynamic_viscosity_pa_s=1e308))
    with pytest.raises(DomainError):
        tank.shell_hole_sizes(tank.ShellHoleSizesInput(tank_diameter_m=5e-324))


def economics():
    return dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,usd_to_output_currency=1.,cost_basis_year=2026),
        outage_multiplier=1.,production_cost_per_day=1000.,currency="USD",cost_basis="Qualified illustrative 2026 USD fixture",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5)


def test_geometry_to_risk_matches_explicit_source_arrival_financial_chain():
    source = tank.bottom_source_assessment(bottom()).outputs
    arrival = tank.groundwater_arrival(tank.GroundwaterArrivalInput(distance_to_groundwater_m=5.,
        seepage_velocity_m_day=source.seepage_velocity_m_day)).outputs
    direct = tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(management_score=500.,total_damage_factor=3.,
        damage_factor_source="fixture",financial=dict(**economics(),
            generic_frequency_by_hole_per_year=source.generic_frequency_by_hole_per_year,generic_frequency_source="source chain",
            tank_diameter_m=61.,leaked_volume_by_hole_bbl={h:source.released_volume_by_hole_bbl[h] for h in ("small","medium","large")},
            total_tank_volume_bbl=source.available_volume_bbl,detection_time_days=source.detection_time_days,
            groundwater_arrival_time_days=arrival.arrival_time_days))).outputs
    combined = tank.bottom_integrated_assessment(tank.BottomIntegratedAssessmentInput(source=bottom(),distance_to_groundwater_m=5.,
        economics=economics(),management_score=500.,total_damage_factor=3.,damage_factor_source="fixture")).outputs
    assert combined.financial_consequence == direct.financial_consequence
    assert combined.financial_risk_per_year == direct.financial_risk_per_year
    assert combined.released_mass_by_hole_kg == source.released_mass_by_hole_kg
    assert combined.groundwater_arrival_time_days == arrival.arrival_time_days
    assert combined.annual_failure_frequency == pytest.approx(7.22e-4*3)


def test_empty_geometry_retains_full_inventory_rupture_zero_but_repair_nonzero():
    r = tank.bottom_integrated_assessment(tank.BottomIntegratedAssessmentInput(source=bottom(fill_height_m=0),
        distance_to_groundwater_m=0.,economics=economics(),management_score=500.,total_damage_factor=1.,damage_factor_source="fixture")).outputs
    assert r.environmental_cost == 0 and r.groundwater_arrival_time_days == 0
    assert r.component_repair_cost > 0 and r.financial_risk_per_year > 0
