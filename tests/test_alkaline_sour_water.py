"""NH4HS source ambiguities,40cells,phase velocity,pressure and acid routing."""
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage, properties

PSI=6894.757293168


def estimate(**changes):
    return dict(h2s_mass_fraction=.02,nh3_mass_fraction=.015,analytical_basis="Qualified condensed-water common analytical mass basis",
        excess_h2s_policy="reject_disputed_branch",equality_policy="reject_unassigned_equality")|changes


def model(**changes):
    return dict(concentration=dict(method="supplied",nh4hs_mass_fraction=.1,qualification_basis="Qualified ionic-model concentration fixture"),
        velocity=dict(phase_regime="two_phase",vapor_velocity_m_s=7.62,liquid_velocity_m_s=1.,qualification_basis="Qualified phase-specific flow fixture"),
        h2s_partial_pressure_pa_abs=621000.,baseline_unit_basis="printed_si",pressure_equation_basis="printed_si",lookup_policy="exact_nodes_only",
        thinning_threshold_basis="printed_si",qualification_basis="Qualified NH4HS/pressure/model applicability")|changes


def request(**changes):
    return damage.AlkalineSourWaterAssessmentInput(**(dict(material="carbon_steel",free_water_present=True,ph=8.,h2s_ammonia_service_qualified=True,
        applicability_basis="Qualified alkaline aqueous NH4HS carbon-steel service",wet_model=model())|changes))


def screen(ph=8.):
    return dict(free_water_present=True,ph=ph,chlorides_present=False,chloride_policy="figure_any_presence_routes_hcl",neutral_ph_policy="detailed_body_inclusive",
        qualification_basis="Qualified shared separated-water pH/water fixture")


def test_h2s_partial_pressure_uses_fraction_and_absolute_units():
    r=properties.h2s_partial_pressure(properties.H2sPartialPressureInput(total_pressure_pa_abs=10e6,h2s_mole_fraction=.0621)).outputs
    assert r.h2s_partial_pressure_pa_abs==621000.


def test_lower_nh4hs_approximation_and_excess_literal_not_silently_repaired():
    r=damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate())).outputs
    assert r.estimated_nh4hs_mass_fraction==.03 and r.concentration_estimate_branch=="printed_lower_h2s"
    with pytest.raises(DomainError) as error:
        damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(nh3_mass_fraction=.001)))
    assert error.value.code=="nh4hs_disputed_formula"
    r=damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(nh3_mass_fraction=.001,
        excess_h2s_policy="qualified_printed_literal",excess_h2s_qualification_basis="Owner requests disputed printed3*H2S, not inferred3*NH3"))).outputs
    assert r.estimated_nh4hs_mass_fraction==.06


@pytest.mark.parametrize("policy,value",[("qualified_lower_branch",.03),("qualified_upper_branch",.06)])
def test_unassigned_equality_requires_policy_and_basis(policy,value):
    with pytest.raises(DomainError):
        damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(nh3_mass_fraction=.01)))
    r=damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(nh3_mass_fraction=.01,
        equality_policy=policy,equality_qualification_basis="Explicit owner boundary interpretation",excess_h2s_policy="qualified_printed_literal",
        excess_h2s_qualification_basis="Owner acknowledges disputed upper branch"))).outputs
    assert r.estimated_nh4hs_mass_fraction==value


def test_literal_result_over100percent_retained_flagged_not_clipped():
    r=damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(h2s_mass_fraction=.4,nh3_mass_fraction=.01,
        excess_h2s_policy="qualified_printed_literal",excess_h2s_qualification_basis="Literal source diagnostic only"))).outputs
    assert r.estimated_nh4hs_mass_fraction==pytest.approx(1.2) and r.estimated_fraction_exceeds_one


@pytest.mark.parametrize("changes",[dict(h2s_mass_fraction=.8,nh3_mass_fraction=.3),dict(analytical_basis=" "),
    dict(excess_h2s_policy="qualified_printed_literal"),dict(equality_policy="qualified_lower_branch")])
def test_estimate_invalid_basis_or_mass_analysis(changes):
    with pytest.raises(DomainError):
        damage.alkaline_sour_water_nh4hs_estimate(damage.AlkalineSourWaterNh4hsEstimateInput(**estimate(**changes)))


def test_phase_specific_velocity_is_not_bulk_or_lower_liquid_velocity():
    two=damage.alkaline_sour_water_velocity_selection(damage.AlkalineSourWaterVelocitySelectionInput(phase_regime="two_phase",vapor_velocity_m_s=7.62,
        liquid_velocity_m_s=1.,qualification_basis="Qualified two-phase velocities")).outputs
    assert two.selected_velocity_m_s==7.62 and two.selected_velocity_phase=="vapor"
    liquid=damage.alkaline_sour_water_velocity_selection(damage.AlkalineSourWaterVelocitySelectionInput(phase_regime="liquid_full",liquid_velocity_m_s=4.57,
        qualification_basis="Qualified liquid-full velocity")).outputs
    assert liquid.selected_velocity_m_s==4.57 and liquid.selected_velocity_phase=="liquid"
    for values in [dict(phase_regime="two_phase",liquid_velocity_m_s=5.),dict(phase_regime="liquid_full",liquid_velocity_m_s=5.,vapor_velocity_m_s=2.)]:
        with pytest.raises(DomainError):
            damage.alkaline_sour_water_velocity_selection(damage.AlkalineSourWaterVelocitySelectionInput(**values,qualification_basis="fixture"))


@pytest.mark.parametrize("concentration,si,us",[(.02,[.08,.10,.13,.20,.28],[3,4,5,8,11]),(.05,[.15,.23,.30,.38,.46],[6,9,12,15,18]),
    (.10,[.51,.69,.89,1.09,1.27],[20,27,35,43,50]),(.15,[1.14,1.78,2.54,3.81,5.08],[45,70,100,150,200])])
def test_all_40_baseline_cells(concentration,si,us):
    for basis,values,nodes,convert in [("printed_si",si,[3.05,4.57,6.1,7.62,9.14],.001),
        ("printed_us_converted",us,[v*.3048 for v in [10,15,20,25,30]],.0000254)]:
        for value,v in zip(values,nodes):
            r=damage.alkaline_sour_water_base_rate(damage.AlkalineSourWaterBaseRateInput(nh4hs_mass_fraction=concentration,selected_velocity_m_s=v,unit_basis=basis,
                lookup_policy="exact_nodes_only")).outputs
            assert r.baseline_corrosion_rate_m_year==pytest.approx(value*convert)


@pytest.mark.parametrize("policy,expected",[("bilinear",(.08+.1+.15+.23)/4/1000),("maximum_bracketing_value",.00023)])
def test_bilinear_and_conservative_corner(policy,expected):
    r=damage.alkaline_sour_water_base_rate(damage.AlkalineSourWaterBaseRateInput(nh4hs_mass_fraction=.035,selected_velocity_m_s=(3.05+4.57)/2,
        unit_basis="printed_si",lookup_policy=policy)).outputs
    assert r.baseline_corrosion_rate_m_year==pytest.approx(expected)


@pytest.mark.parametrize("concentration,velocity",[(.019,5.),(.151,5.),(.1,3.),(.1,10.)])
def test_no_baseline_extrapolation(concentration,velocity):
    with pytest.raises(DomainError):
        damage.alkaline_sour_water_base_rate(damage.AlkalineSourWaterBaseRateInput(nh4hs_mass_fraction=concentration,selected_velocity_m_s=velocity,
            unit_basis="printed_si",lookup_policy="bilinear"))


@pytest.mark.parametrize("basis,p,expected,clamped",[("printed_si",0.,0.,True),("printed_si",172000.,0.,False),
    ("printed_si",345000.,1.,False),("printed_si",621000.,2.,False),("printed_us_converted",0.,0.,True),
    ("printed_us_converted",25*PSI,0.,False),("printed_us_converted",50*PSI,1.,False),("printed_us_converted",90*PSI,2.,False)])
def test_pressure_reference_slopes_and_actual_zero_clamp(basis,p,expected,clamped):
    r=damage.alkaline_sour_water_pressure_adjustment(damage.AlkalineSourWaterPressureAdjustmentInput(baseline_corrosion_rate_m_year=.001,
        h2s_partial_pressure_pa_abs=p,equation_basis=basis)).outputs
    assert r.pressure_correction_factor==pytest.approx(expected) and r.corrosion_rate_m_year==pytest.approx(.001*expected)
    assert r.negative_pressure_factor_clamped==clamped


def test_integrated_phase_baseline_pressure_and_classification():
    r=damage.alkaline_sour_water_assessment(request()).outputs
    assert r.baseline_corrosion_rate_m_year==pytest.approx(.00109) and r.corrosion_rate_m_year==pytest.approx(.00218)
    assert r.selected_velocity_phase=="vapor" and r.source_thinning_type=="local"
    for basis,kind in [("printed_si","general"),("printed_us_converted","local")]:
        r=damage.alkaline_sour_water_assessment(request(wet_model=model(velocity=dict(phase_regime="liquid_full",liquid_velocity_m_s=6.1,
            qualification_basis="Qualified liquid-full fixture"),thinning_threshold_basis=basis))).outputs
        assert r.source_thinning_type==kind


def test_integrated_source_concentration_approximation():
    c=estimate()|dict(method="source_approximation")
    r=damage.alkaline_sour_water_assessment(request(wet_model=model(concentration=c,lookup_policy="bilinear"))).outputs
    assert r.nh4hs_mass_fraction_used==.03 and r.concentration_source=="source_approximation"


@pytest.mark.parametrize("changes",[dict(wet_model=None),dict(h2s_ammonia_service_qualified=False),dict(applicability_basis=" "),
    dict(wet_model=model(qualification_basis=" "))])
def test_wet_applicability_gates(changes):
    with pytest.raises(DomainError):
        damage.alkaline_sour_water_assessment(request(**changes))


def test_dry_specific_zero_and_absence_of_model_diagnostics():
    r=damage.alkaline_sour_water_assessment(request(free_water_present=False,ph=None,wet_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.baseline_corrosion_rate_m_year is None and r.calculation_branch=="no_free_water"


def test_acid_and_alkaline_router_matches_independent_calculations():
    alkaline=request()
    routed=damage.sour_water_assessment(damage.SourWaterAssessmentInput(screening=screen(),alkaline_model=alkaline)).outputs
    assert routed.corrosion_route=="alkaline_sour_water" and routed.corrosion_rate_m_year==damage.alkaline_sour_water_assessment(alkaline).outputs.corrosion_rate_m_year
    acid_screen=screen(5.75)
    acid=dict(screening=acid_screen,material="carbon_steel",primary_h2s_and_insignificant_other_corrosives_qualified=True,applicability_basis="Qualified acid sour chemistry",
        carbon_model=dict(maximum_water_temperature_k=352.15,unit_basis="printed_si",lookup_policy="exact_nodes_only",ph_edge_policy="reject_unprinted_ph",oxygen_content_ppb=50.,
            velocity_m_s=1.5,velocity_equation_basis="printed_si",qualification_basis="Qualified separated water pH and temperature"))
    routed=damage.sour_water_assessment(damage.SourWaterAssessmentInput(screening=acid_screen,acid_model=acid)).outputs
    assert routed.corrosion_route=="acid_sour_water" and routed.corrosion_rate_m_year==pytest.approx(.00005)
    dry=damage.sour_water_assessment(damage.SourWaterAssessmentInput(screening=dict(free_water_present=False,qualification_basis="Qualified dry service"))).outputs
    assert dry.corrosion_rate_m_year==0 and dry.selected_model_base_rate_m_year is None


def test_router_requires_matching_child_and_does_not_fake_hcl_or_missing_model():
    for values in [dict(screening=screen()),dict(screening=screen(8.1),alkaline_model=request()),dict(screening=screen(4.))]:
        with pytest.raises(DomainError):
            damage.sour_water_assessment(damage.SourWaterAssessmentInput(**values))


def test_thinning_same_rate_and_phase_velocity_with_clamp_flag_retained():
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.02,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="sour_water",velocity_m_s=7.62),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    args=dict(corrosion=request(),assessment_distribution="local",distribution_qualification_basis="Qualified local inspection coverage",starting_thickness_m=.02,elapsed_years=2.,
        strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,qualification_basis="Qualified common non-AST baseline")
    r=damage.alkaline_sour_water_thinning_assessment(damage.AlkalineSourWaterThinningAssessmentInput(**args)).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=r.corrosion_rate_m_year,elapsed_years=2.),strength=strength,inspections=args["inspections"],conditions=conditions)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor and r.wall_loss_fraction==pytest.approx(.218)
    zero=damage.alkaline_sour_water_thinning_assessment(damage.AlkalineSourWaterThinningAssessmentInput(**(args|dict(corrosion=request(wet_model=model(h2s_partial_pressure_pa_abs=0.)))))).outputs
    assert zero.corrosion_rate_m_year==0 and zero.negative_pressure_factor_clamped and zero.thinning_damage_factor >= .1


@pytest.mark.parametrize("changes",[dict(material="stainless_steel"),dict(ph=7.),dict(ph=True)])
def test_material_ph_numeric_contract(changes):
    with pytest.raises(ValidationError):
        request(**changes)
