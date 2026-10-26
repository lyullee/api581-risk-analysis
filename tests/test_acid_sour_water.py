"""Acid sour route,40table cells,piecewise oxygen/velocity and thinning."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def route(**changes):
    return dict(free_water_present=True,ph=5.75,chlorides_present=False,chloride_policy="figure_any_presence_routes_hcl",
        neutral_ph_policy="detailed_body_inclusive",qualification_basis="Qualified free water and lowest separated-water pH fixture")|changes


def model(**changes):
    return dict(maximum_water_temperature_k=79+273.15,unit_basis="printed_si",lookup_policy="exact_nodes_only",ph_edge_policy="reject_unprinted_ph",
        oxygen_content_ppb=50.,velocity_m_s=1.5,velocity_equation_basis="printed_si",qualification_basis="Qualified maximum water temperature including local heating and separated-phase pH")|changes


def request(**changes):
    return damage.AcidSourWaterAssessmentInput(**(dict(screening=route(),material="carbon_steel",primary_h2s_and_insignificant_other_corrosives_qualified=True,
        applicability_basis="Qualified primary H2S with insignificant NH3/CO2/cyanides/other chemistry fixture",carbon_model=model())|changes))


@pytest.mark.parametrize("ph,expected",[(math.nextafter(4.5,0),"hydrochloric_acid"),(4.5,"acid_sour_water"),
    (7.,"acid_sour_water"),(math.nextafter(7.,14.),"alkaline_sour_water")])
def test_detailed_ph_route_boundaries(ph,expected):
    assert damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(ph=ph))).outputs.corrosion_route==expected


def test_neutral_overview_policy_and_dry_branch():
    assert damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(ph=7.,neutral_ph_policy="unclassified_at_neutral"))).outputs.corrosion_route=="neutral_boundary_unclassified"
    r=damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(free_water_present=False,qualification_basis="Qualified absent free water")).outputs
    assert r.corrosion_route=="no_free_water"


def test_figure_chloride_and_qualified_annex_threshold_policies():
    strict=damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(chlorides_present=True,chloride_concentration_ppm=1.))).outputs
    assert strict.corrosion_route=="hydrochloric_acid"
    for ppm,expected in [(1.,"acid_sour_water"),(math.nextafter(50.,0),"acid_sour_water"),(50.,"hydrochloric_acid")]:
        r=damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(chlorides_present=True,chloride_concentration_ppm=ppm,
            chloride_policy="qualified_below_50ppm",chloride_qualification_basis="Qualified insignificant chloride below Annex screen threshold"))).outputs
        assert r.corrosion_route==expected
    # Figure tests pH>7 before chloride presence.
    assert damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(ph=8.,chlorides_present=True))).outputs.corrosion_route=="alkaline_sour_water"


@pytest.mark.parametrize("changes",[dict(chloride_policy="qualified_below_50ppm"),dict(chlorides_present=True,chloride_concentration_ppm=0.),
    dict(chlorides_present=False,chloride_concentration_ppm=1.),dict(qualification_basis=" "),dict(free_water_present=False)])
def test_route_missing_or_conflicting_inputs(changes):
    with pytest.raises(DomainError):
        damage.acid_sour_water_route(damage.AcidSourWaterRouteInput(**route(**changes)))


@pytest.mark.parametrize("ph,si,us",[(4.75,[.03,.08,.13,.18],[1,3,5,7]),(5.25,[.02,.05,.08,.1],[.7,2,3,4]),
    (5.75,[.01,.04,.05,.08],[.4,1.5,2,3]),(6.25,[.01,.03,.04,.05],[.3,1,1.5,2]),(6.75,[.01,.01,.02,.03],[.2,.5,.7,1])])
def test_all_40_printed_base_cells(ph,si,us):
    for basis,values,nodes,convert in [("printed_si",si,[38+273.15,52+273.15,79+273.15,93+273.15],.001),
        ("printed_us_converted",us,[(f-32)*5/9+273.15 for f in [100,125,175,200]],.0000254)]:
        for t,value in zip(nodes,values):
            r=damage.acid_sour_water_base_rate(damage.AcidSourWaterBaseRateInput(ph=ph,maximum_water_temperature_k=t,unit_basis=basis,
                lookup_policy="exact_nodes_only",ph_edge_policy="reject_unprinted_ph")).outputs
            assert r.base_corrosion_rate_m_year==pytest.approx(value*convert)


@pytest.mark.parametrize("policy,expected",[("bilinear",(.08+.13+.05+.08)/4/1000),("maximum_bracketing_value",.00013)])
def test_explicit_bilinear_or_conservative_corner(policy,expected):
    r=damage.acid_sour_water_base_rate(damage.AcidSourWaterBaseRateInput(ph=5.,maximum_water_temperature_k=(52+79)/2+273.15,unit_basis="printed_si",
        lookup_policy=policy,ph_edge_policy="reject_unprinted_ph")).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(expected)


@pytest.mark.parametrize("ph,used",[(4.5,4.75),(4.7,4.75),(6.8,6.75),(7.,6.75)])
def test_unprinted_scope_edge_requires_qualification(ph,used):
    args=dict(ph=ph,maximum_water_temperature_k=79+273.15,unit_basis="printed_si",lookup_policy="exact_nodes_only")
    with pytest.raises(DomainError):
        damage.acid_sour_water_base_rate(damage.AcidSourWaterBaseRateInput(**args,ph_edge_policy="reject_unprinted_ph"))
    r=damage.acid_sour_water_base_rate(damage.AcidSourWaterBaseRateInput(**args,ph_edge_policy="qualified_nearest_edge_row",ph_edge_qualification_basis="Owner qualified scope edge estimate")).outputs
    assert r.ph_edge_row_used and r.ph_for_lookup==used


@pytest.mark.parametrize("oxygen,factor",[(0.,1),(50.,1),(math.nextafter(50.,math.inf),2)])
def test_oxygen_threshold(oxygen,factor):
    r=damage.acid_sour_water_oxygen_factor(damage.AcidSourWaterOxygenFactorInput(oxygen_content_ppb=oxygen)).outputs
    assert r.oxygen_factor==factor and r.high_oxygen_localized_review==(oxygen>50)


@pytest.mark.parametrize("basis,lo,hi,slope",[("printed_si",1.83,6.1,.82),("printed_us_converted",6*.3048,20*.3048,.25)])
def test_velocity_threshold_inclusivity_and_actual_discontinuity(basis,lo,hi,slope):
    for value in [math.nextafter(lo,0),lo,math.nextafter(lo,math.inf),hi,math.nextafter(hi,math.inf)]:
        middle=slope*(value if basis=="printed_si" else value/.3048)-.5
        expected=1 if value<lo else middle if value<=hi else 5
        r=damage.acid_sour_water_velocity_factor(damage.AcidSourWaterVelocityFactorInput(velocity_m_s=value,equation_basis=basis)).outputs
        assert r.velocity_factor==pytest.approx(expected)
    at=damage.acid_sour_water_velocity_factor(damage.AcidSourWaterVelocityFactorInput(velocity_m_s=hi,equation_basis=basis)).outputs.velocity_factor
    above=damage.acid_sour_water_velocity_factor(damage.AcidSourWaterVelocityFactorInput(velocity_m_s=math.nextafter(hi,math.inf),equation_basis=basis)).outputs.velocity_factor
    assert at<above==5


def test_other_material_body_bound_vs_figure_point():
    common=dict(service_suitability_qualified=True,other_degradation_assessed=True,qualification_basis="Qualified material suitability and cracking/ClSCC review")
    for basis,value in [("printed_si",.00005),("printed_us_converted",.0000508)]:
        r=damage.acid_sour_water_other_material_rate(damage.AcidSourWaterOtherMaterialRateInput(**common,rate_policy="body_upper_bound_screening",body_unit_basis=basis)).outputs
        assert r.corrosion_rate_m_year==value and r.selected_rate_is_screening_bound
    r=damage.acid_sour_water_other_material_rate(damage.AcidSourWaterOtherMaterialRateInput(**common,rate_policy="figure_nominal_2mpy")).outputs
    assert r.corrosion_rate_m_year==.0000508 and not r.selected_rate_is_screening_bound


def test_assessment_independent_rate_anchor_high_oxygen_and_velocity():
    r=damage.acid_sour_water_assessment(request(carbon_model=model(oxygen_content_ppb=60.,velocity_m_s=3.))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00005*2*(.82*3-.5))
    assert r.localized_attack_review_required and r.default_thinning_type=="general"


def test_low_alloy_table_scope_and_other_material_parent_branch():
    r=damage.acid_sour_water_assessment(request(material="low_alloy_steel",total_alloy_mass_fraction=.06)).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00005)
    for fraction in [None,.06001]:
        with pytest.raises(DomainError):
            damage.acid_sour_water_assessment(request(material="low_alloy_steel",total_alloy_mass_fraction=fraction))
    r=damage.acid_sour_water_assessment(request(material="other_material",carbon_model=None,other_material_model=dict(service_suitability_qualified=True,
        other_degradation_assessed=True,rate_policy="figure_nominal_2mpy",qualification_basis="Qualified other material fixture"))).outputs
    assert r.corrosion_rate_m_year==.0000508 and r.base_corrosion_rate_m_year is None


@pytest.mark.parametrize("changes",[dict(screening=route(ph=4.49)),dict(screening=route(ph=7.01)),dict(primary_h2s_and_insignificant_other_corrosives_qualified=False),
    dict(carbon_model=None),dict(total_alloy_mass_fraction=.01),dict(applicability_basis=" ")])
def test_different_routes_and_unqualified_scope_not_silently_zero(changes):
    with pytest.raises(DomainError):
        damage.acid_sour_water_assessment(request(**changes))


def test_dry_specific_zero_has_null_model_diagnostics():
    r=damage.acid_sour_water_assessment(request(screening=dict(free_water_present=False,qualification_basis="Qualified no free water"),carbon_model=None)).outputs
    assert r.corrosion_route=="no_free_water" and r.corrosion_rate_m_year==0 and r.base_corrosion_rate_m_year is None


def test_rate_to_thinning_with_local_review_and_same_velocity_monitoring():
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="sour_water",velocity_m_s=3.),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    args=dict(corrosion=request(carbon_model=model(velocity_m_s=3.)),assessment_distribution="local",localized_attack_review_basis="Qualified high-velocity/local inspection review",
        starting_thickness_m=.01,elapsed_years=10.,strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,qualification_basis="Qualified common non-AST baseline")
    r=damage.acid_sour_water_thinning_assessment(damage.AcidSourWaterThinningAssessmentInput(**args)).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",
        wall=dict(starting_thickness_m=.01,corrosion_rate_m_year=r.corrosion_rate_m_year,elapsed_years=10.),strength=strength,inspections=args["inspections"],conditions=conditions)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    with pytest.raises(DomainError):
        damage.acid_sour_water_thinning_assessment(damage.AcidSourWaterThinningAssessmentInput(**(args|dict(localized_attack_review_basis=None))))
    wrong=conditions|dict(monitoring=dict(row=dict(mechanism="sour_water",velocity_m_s=2.),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.acid_sour_water_thinning_assessment(damage.AcidSourWaterThinningAssessmentInput(**(args|dict(conditions=wrong))))


def test_numerical_contract_and_rate_overflow():
    with pytest.raises(ValidationError):
        damage.AcidSourWaterBaseRateInput(ph=4.49,maximum_water_temperature_k=352.15,unit_basis="printed_si",lookup_policy="exact_nodes_only",ph_edge_policy="reject_unprinted_ph")
    with pytest.raises(ValidationError):
        damage.AcidSourWaterVelocityFactorInput(velocity_m_s=True,equation_basis="printed_si")
    with pytest.raises(DomainError):
        damage.acid_sour_water_rate_equation(damage.AcidSourWaterRateEquationInput(base_corrosion_rate_m_year=1e308,oxygen_factor=2.,velocity_factor=5.))
