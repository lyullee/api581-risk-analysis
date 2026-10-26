"""AST-specific pool bounds, NFNT omission, Level2 aggregation and integration."""
import copy
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import tank, effects

EVENTS = ("pool_fire","jet_fire","fireball","vce","flash_fire")


def pool(**changes):
    return tank.DikedPoolConsequenceInput(**(dict(burning=dict(heat_of_combustion_j_kg=46e6,
        latent_heat_j_kg=350000,boiling=True),liquid_rate_kg_s=100.,available_liquid_mass_kg=50000.,
        liquid_density_kg_m3=700.,dike_area_m2=25.,dike_limit_basis="burning_pool_area",
        air_density_kg_m3=1.2,vapor_density_kg_m3=2.,wind_speed_m_s=2.,
        atmosphere=dict(transmissivity_model="constant",constant_transmissivity=.8),
        equation_basis="geometry_checked",distance_convention="surface_to_axis",maximum_surface_distance_m=1000.)|changes))


def case(hole="small",scale=1.,**changes):
    return tank.ShellLevel2CaseInput(**(dict(hole=hole,non_ignition_probability=.8,
        outcomes=[dict(event=e,probability=.2 if e == "pool_fire" else 0.,
            equipment_area_m2=100.*scale if e == "pool_fire" else 0.,
            personnel_area_m2=200.*scale if e == "pool_fire" else 0.) for e in EVENTS],
        event_tree_source="Qualified fixture terminal probabilities",consequence_source="Qualified raw footprint fixture",
        toxic_components=[dict(component_id="component-A",cloud_area_m2=50.*scale,selected_criterion_source="Qualified exposure fixture")],
        toxic_applicability="evaluated",toxic_applicability_source="Fixture toxic assessment",
        dike_area_m2=1000.,burning_pool_area_m2=20.,pool_dike_limit_basis="burning_pool_area")|changes))


def source(**changes):
    return dict(tank_diameter_m=61.,fill_height_m=10.,course_index=2,course_height_m=2.,fluid="gasoline",
        diameter_boundary_basis="inch_0_125")|changes


def economics():
    return dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,usd_to_output_currency=1.,cost_basis_year=2026),
        outage_multiplier=1.,production_cost_per_day=1000.,currency="USD",cost_basis="Qualified illustrative 2026 USD fixture",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5,equipment_cost_per_m2=100.,
        population_density_per_m2=.01,cost_per_injury=100000.)


def test_dike_bounds_burning_pool_before_geometry_and_keeps_radiation_extent():
    x = pool()
    r = tank.diked_pool_consequence(x).outputs
    assert r.pool_area_m2 == 25 and r.pool_radius_m == pytest.approx(math.sqrt(25/math.pi))
    assert r.personnel_area_m2 == r.unclipped_personnel_area_m2 > 25
    assert not r.personnel_area_clipped
    plain = effects.pool_fire_consequence(effects.PoolFireConsequenceInput(**{
        k:v for k,v in x.model_dump().items() if k not in {"dike_area_m2","dike_limit_basis","site_maximum_area_m2"}},
        site_maximum_area_m2=25)).outputs
    assert r.personnel_area_m2 == plain.personnel_area_m2
    assert r.unclipped_personnel_safe_surface_distance_m == plain.personnel_safe_surface_distance_m


def test_literal_consequence_cap_preserves_uncapped_root_and_area():
    physical = tank.diked_pool_consequence(pool()).outputs
    literal = tank.diked_pool_consequence(pool(dike_limit_basis="burning_and_consequence_area")).outputs
    assert literal.personnel_area_m2 == 25
    assert literal.personnel_area_clipped
    assert literal.unclipped_personnel_area_m2 == physical.personnel_area_m2
    assert literal.unclipped_personnel_safe_surface_distance_m == physical.unclipped_personnel_safe_surface_distance_m
    assert literal.pool_area_m2 == physical.pool_area_m2


def test_smaller_independent_site_limit_wins_and_empty_pool_stays_zero():
    r = tank.diked_pool_consequence(pool(site_maximum_area_m2=10)).outputs
    assert r.pool_area_m2 == r.effective_pool_area_limit_m2 == 10
    r = tank.diked_pool_consequence(pool(available_liquid_mass_kg=0)).outputs
    assert r.personnel_area_m2 == r.equipment_area_m2 == 0 and r.personnel_status == "no_pool"


def test_case_weights_flammable_and_shared_nonignition_toxic_once():
    r = tank.shell_level2_case(case()).outputs
    assert r.flammable_equipment_area_m2 == 20
    assert r.flammable_personnel_area_m2 == 40
    assert r.toxic_personnel_area_m2 == 40
    assert r.nfnt_status == "not_determined_for_ast"
    assert not any(k.startswith("nfnt_") and k != "nfnt_status" for k in r.model_dump())


def test_summary_has_table_hole_weights_and_level2_sum_not_level1_max():
    cases = [case(hole=h,scale=i+1) for i,h in enumerate(("small","medium","large","rupture"))]
    r = tank.shell_level2_summary(tank.ShellLevel2SummaryInput(cases=cases)).outputs
    mean_scale = (7e-5+2*2.5e-5+3*5e-6+4*1e-7)/1.001e-4
    assert r.equipment_area_m2 == pytest.approx(20*mean_scale)
    assert r.personnel_area_m2 == pytest.approx((40+40)*mean_scale)
    assert r.consequence_area_m2 == r.personnel_area_m2
    assert r.generic_frequency_per_year == pytest.approx(1.001e-4)


@pytest.mark.parametrize("changes",[
    dict(burning_pool_area_m2=1001.),dict(burning_pool_area_m2=0.),
    dict(pool_dike_limit_basis="burning_and_consequence_area",dike_area_m2=100.),
    dict(toxic_applicability="not_applicable"),dict(toxic_applicability_source="   ")])
def test_invalid_pool_or_toxic_basis_rejected(changes):
    with pytest.raises(DomainError):
        tank.shell_level2_case(case(**changes))


def test_ast_cannot_accept_nfnt_or_instantaneous_release():
    with pytest.raises(ValidationError):
        case(release_type="instantaneous")
    with pytest.raises(ValidationError):
        case(nfnt=dict(physical_equipment_area_m2=123))
    x = case().model_dump()
    x["outcomes"][2].update(probability=.1,equipment_area_m2=1.,personnel_area_m2=1.)
    x["non_ignition_probability"] = .7
    with pytest.raises(DomainError):
        tank.shell_level2_case(tank.ShellLevel2CaseInput(**x))


def test_empty_toxic_components_require_explicit_not_applicable():
    r = tank.shell_level2_case(case(toxic_components=[],toxic_applicability="not_applicable")).outputs
    assert r.toxic_personnel_area_m2 == 0


def test_correlated_jet_pool_keeps_single_branch_and_checks_pool_dike():
    x = case().model_dump()
    x["outcomes"][0].update(probability=0.,equipment_area_m2=0.,personnel_area_m2=0.)
    x["correlated_jet_pool"] = dict(probability=.2,jet_equipment_area_m2=150.,jet_personnel_area_m2=100.,
        pool_equipment_area_m2=100.,pool_personnel_area_m2=200.,consequence_source="Qualified concurrent fixture")
    r = tank.shell_level2_case(tank.ShellLevel2CaseInput(**x)).outputs
    assert r.flammable_equipment_area_m2 == 30 and r.flammable_personnel_area_m2 == 40
    x["pool_dike_limit_basis"] = "burning_and_consequence_area"
    x["dike_area_m2"] = 100.
    with pytest.raises(DomainError):
        tank.shell_level2_case(tank.ShellLevel2CaseInput(**x))


def test_all_four_cases_and_common_dike_required():
    cases = [case(hole=h).model_dump() for h in ("small","medium","large","rupture")]
    cases[-1]["dike_area_m2"] = 1001.
    with pytest.raises(DomainError):
        tank.shell_level2_summary(tank.ShellLevel2SummaryInput(cases=cases))
    cases[-1] = copy.deepcopy(cases[0])
    with pytest.raises(DomainError):
        tank.shell_level2_summary(tank.ShellLevel2SummaryInput(cases=cases))


def test_integrated_matches_explicit_source_area_financial_chain():
    cases = [case(hole=h) for h in ("small","medium","large","rupture")]
    s = tank.shell_source_assessment(tank.ShellSourceAssessmentInput(**source())).outputs
    a = tank.shell_level2_summary(tank.ShellLevel2SummaryInput(cases=cases)).outputs
    f = tank.shell_risk_assessment(tank.ShellRiskAssessmentInput(financial=dict(**economics(),
        generic_frequency_by_hole_per_year=s.generic_frequency_by_hole_per_year,generic_frequency_source="Fixture source chain",
        released_volume_by_hole_bbl=s.released_volume_by_hole_bbl,equipment_area_m2=a.equipment_area_m2,personnel_area_m2=a.personnel_area_m2),
        management_score=500.,total_damage_factor=3.,damage_factor_source="External fixture DF")).outputs
    result = tank.shell_integrated_assessment(tank.ShellIntegratedAssessmentInput(source=source(),cases=cases,economics=economics(),
        management_score=500.,total_damage_factor=3.,damage_factor_source="External fixture DF")).outputs
    assert result.financial_consequence == f.financial_consequence
    assert result.financial_risk_per_year == f.financial_risk_per_year
    assert result.personnel_area_m2 == a.personnel_area_m2
    assert result.annual_failure_frequency == pytest.approx(1.001e-4*3)
    assert result.personnel_area_risk_m2_per_year == pytest.approx(1.001e-4*3*80)


def test_dry_source_rejects_nonzero_external_footprints():
    with pytest.raises(DomainError):
        tank.shell_integrated_assessment(tank.ShellIntegratedAssessmentInput(source=source(fill_height_m=0),
            cases=[case(hole=h) for h in ("small","medium","large","rupture")],economics=economics(),
            management_score=500.,total_damage_factor=1.,damage_factor_source="fixture"))


def test_dry_source_and_zero_footprints_keep_repair_risk_only():
    cases = [case(hole=h,scale=0.,burning_pool_area_m2=0.) for h in ("small","medium","large","rupture")]
    r = tank.shell_integrated_assessment(tank.ShellIntegratedAssessmentInput(source=source(fill_height_m=0),cases=cases,
        economics=economics(),management_score=500.,total_damage_factor=1.,damage_factor_source="fixture")).outputs
    assert r.environmental_cost == r.personnel_area_m2 == r.equipment_area_m2 == 0
    assert r.component_repair_cost > 0 and r.financial_risk_per_year > 0
