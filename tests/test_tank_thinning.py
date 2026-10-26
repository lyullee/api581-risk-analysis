"""2016 source AST anchors, one-credit rules, Art and complete risk composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import tank


def basis(**changes):
    return dict(starting_thickness_m=.006,elapsed_years=10.,baseline_basis="Qualified furnished thickness and elapsed service fixture",
        corrosion_allowance_m=.00346,minimum_thickness=dict(release_prevention_barrier=False,thickness_basis="api581_2016_default"),
        inspections=dict(eligible_inspection_grades=["b","b","d"],eligibility_basis="Owner-qualified in-period inspections fixture"),
        lookup_policy="linear_between_rows",adjustments=dict(construction="welded",maintained_per_api653=True,settlement_category="meets_api653"))|changes


def corrosion(**changes):
    return dict(material="carbon_steel",applicability_basis="Unlined carbon-steel AST floor fixture",
        soil_base_corrosion_rate_m_year=.00013,product_base_corrosion_rate_m_year=.00005,
        soil_base_rate_source="SI reference base fixture",product_base_rate_source="SI reference base fixture",bottom_type="single_bottom",
        soil_resistivity_ohm_m=50.,pad=dict(pad_type="continuous_asphalt"),drainage=dict(drainage_category="storm_water_collects"),
        cathodic_protection=dict(protection_category="present_per_api651",effectiveness_verified_by_high_level_inspection=True,verification_basis="Qualified High Level inspection fixture"),
        temperature=dict(highest_operating_temperature_k=323.15,threshold_basis="printed_si"),product_condition=dict(product_condition="wet"),
        steam_coil=dict(steam_coil_present=True),water_draw=dict(water_draw_practice="weekly"),product_distribution="general",
        minimum_rate_policy="apply_2_mpy_recommendation")|changes


def risk_request(**changes):
    return tank.BottomCorrosionRiskAssessmentInput(**(dict(damage=dict(corrosion=corrosion(),thinning=basis()),
        source=dict(tank_diameter_m=61.,fill_height_m=10.,fluid="gasoline",soil="coarse_sand",water_density_kg_m3=1000.,
            water_dynamic_viscosity_pa_s=.001,foundation="concrete_asphalt",has_release_prevention_barrier=False,transition_hole_basis="api581_printed"),
        distance_to_groundwater_m=5.,management_score=500.,damage_scope="qualified_thinning_only",
        other_mechanisms_exclusion_basis="Illustrative owner scope: no other applicable damage mechanisms; not a site conclusion",
        economics=dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,usd_to_output_currency=1.,cost_basis_year=2026),
            outage_multiplier=1.,production_cost_per_day=1000.,currency="USD",cost_basis="Illustrative owner-qualified USD2026 fixture",
            cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,subsoil=1500.,groundwater=5000.,surface_water=1500.),
            fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5))|changes))


@pytest.mark.parametrize("rpb,value",[(False,.00254),(True,.00127)])
def test_historical_minimum_thickness(rpb,value):
    assert tank.bottom_minimum_thickness(tank.BottomMinimumThicknessInput(release_prevention_barrier=rpb,thickness_basis="api581_2016_default")).outputs.minimum_thickness_m==value


def test_owner_documented_minimum():
    r=tank.bottom_minimum_thickness(tank.BottomMinimumThicknessInput(release_prevention_barrier=False,thickness_basis="documented_owner_method",owner_minimum_thickness_m=.003,owner_method_basis="Qualified asset method")).outputs
    assert r.minimum_thickness_m==.003


@pytest.mark.parametrize("extra",[dict(thickness_basis="documented_owner_method"),
    dict(thickness_basis="documented_owner_method",owner_minimum_thickness_m=.003,owner_method_basis=" "),
    dict(thickness_basis="api581_2016_default",owner_minimum_thickness_m=.003)])
def test_minimum_method_requires_consistent_basis(extra):
    with pytest.raises(DomainError):
        tank.bottom_minimum_thickness(tank.BottomMinimumThicknessInput(release_prevention_barrier=False,**extra))


@pytest.mark.parametrize("start,rate,age,minimum,allowance,art,remaining",[
    (.006,.0002,10,.00254,.00346,1/3,.004),(.008,0,20,.00254,.00346,0,.008),
    (.006,0,0,.00254,.00346,0,.006),(.004,.0004,10,.00254,.00346,1,0),
    (.004,.0005,10,.00254,.00346,7/6,-.001)])
def test_ast_equation_not_unclad_loss(start,rate,age,minimum,allowance,art,remaining):
    r=tank.bottom_wall_parameter(tank.BottomWallParameterInput(starting_thickness_m=start,corrosion_rate_m_year=rate,
        elapsed_years=age,minimum_thickness_m=minimum,corrosion_allowance_m=allowance)).outputs
    assert r.art_parameter==pytest.approx(art) and r.predicted_remaining_thickness_m==pytest.approx(remaining)
    assert r.predicted_penetration==(remaining<=0)


@pytest.mark.parametrize("grades,selected,credit",[([],"e",0),(["e","e"],"e",0),(["d"],"d",1),
    (["c","c","c","c"],"c",1),(["d","b","a","b"],"a",1)])
def test_best_one_inspection_only(grades,selected,credit):
    r=tank.bottom_inspection_selection(tank.BottomInspectionSelectionInput(eligible_inspection_grades=grades,eligibility_basis="Eligible fixture")).outputs
    assert (r.selected_inspection_grade,r.credited_inspection_count,r.eligible_inspection_count)==(selected,credit,len(grades))


@pytest.mark.parametrize("art,expected",[
    (0,[.1,.1,.1,.1,.1]),(.05,[4,1,.5,.4,.4]),(.1,[14,3,1,.7,.7]),(.15,[32,8,2,1,1]),
    (.2,[56,18,6,2,1]),(.25,[87,32,11,4,3]),(.3,[125,53,21,9,6]),(.35,[170,80,36,16,12]),
    (.4,[222,115,57,29,21]),(.45,[281,158,86,47,36]),(.5,[347,211,124,73,58]),
    (.55,[420,273,173,109,89]),(.6,[500,346,234,158,133]),(.65,[587,430,309,222,192]),
    (.7,[681,527,401,305,270]),(.75,[782,635,510,409,370]),(.8,[890,757,638,538,498]),
    (.85,[1005,893,789,696,658]),(.9,[1126,1044,963,888,856]),(.95,[1255,1209,1163,1118,1098]),(1,[1390]*5)])
def test_all_105_printed_ast_damage_cells(art,expected):
    for grade,value in zip("edcba",expected):
        r=tank.bottom_thinning_base(tank.BottomThinningBaseInput(art_parameter=art,inspection_grade=grade,lookup_policy="exact_rows_only")).outputs
        assert r.base_damage_factor==value and r.lower_art_row==r.upper_art_row==art


def test_explicit_between_row_policies():
    for policy,value in [("linear_between_rows",196.),("conservative_upper_row",222.)]:
        r=tank.bottom_thinning_base(tank.BottomThinningBaseInput(art_parameter=.375,inspection_grade="e",lookup_policy=policy)).outputs
        assert r.base_damage_factor==pytest.approx(value) and r.interpolation_weight==pytest.approx(.5)
    with pytest.raises(DomainError) as err:
        tank.bottom_thinning_base(tank.BottomThinningBaseInput(art_parameter=.375,inspection_grade="e",lookup_policy="exact_rows_only"))
    assert err.value.code=="ast_damage_between_rows"


@pytest.mark.parametrize("policy",["linear_between_rows","exact_rows_only","conservative_upper_row"])
def test_no_extrapolation_or_clamp_after_penetration(policy):
    with pytest.raises(DomainError) as err:
        tank.bottom_thinning_base(tank.BottomThinningBaseInput(art_parameter=math.nextafter(1,math.inf),inspection_grade="a",lookup_policy=policy))
    assert err.value.code=="ast_damage_table_exceeded"


@pytest.mark.parametrize("construction,maintained,settlement,factor",[
    ("welded",True,"meets_api653",1),("riveted",True,"meets_api653",10),
    ("welded",False,"meets_api653",5),("welded",True,"exceeds_api653",2),
    ("welded",True,"never_evaluated",1.5),("welded",True,"concrete_no_settlement",1),
    ("riveted",False,"exceeds_api653",100)])
def test_ast_adjustment_factors(construction,maintained,settlement,factor):
    r=tank.bottom_thinning_adjustment_factors(tank.BottomThinningAdjustmentFactorsInput(construction=construction,maintained_per_api653=maintained,settlement_category=settlement)).outputs
    assert r.welded_construction_factor*r.maintenance_factor*r.settlement_factor==factor


def test_thinning_independent_composition():
    x=tank.BottomThinningAssessmentInput(**basis(),corrosion_rate_m_year=.0002,corrosion_rate_basis="Qualified net rate")
    r=tank.bottom_thinning_assessment(x).outputs
    # Art=1/3 between.30/.35; B factors9/16.
    expected=9+(1/3-.3)/.05*7
    assert r.art_parameter==pytest.approx(1/3) and r.base_damage_factor==pytest.approx(expected)
    assert r.thinning_damage_factor==pytest.approx(expected) and r.credited_inspection_count==1
    assert r.online_monitoring_factor==1


def test_low_art_minimum_factor_and_unacceptable_thickness_diagnostic():
    low=tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(elapsed_years=0),corrosion_rate_m_year=0,corrosion_rate_basis="fixture")).outputs
    assert low.thinning_damage_factor==.1 and low.art_parameter==0
    bad=tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(starting_thickness_m=.002,elapsed_years=0),corrosion_rate_m_year=0,corrosion_rate_basis="fixture")).outputs
    assert bad.at_or_below_minimum_thickness and not bad.predicted_penetration
    with pytest.raises(DomainError):
        tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(elapsed_years=100),corrosion_rate_m_year=.0002,corrosion_rate_basis="fixture"))


def test_corrosion_to_thinning_same_rate():
    x=tank.BottomCorrosionThinningAssessmentInput(corrosion=corrosion(),thinning=basis())
    r=tank.bottom_corrosion_thinning_assessment(x).outputs
    rate=tank.bottom_corrosion_assessment(tank.BottomCorrosionAssessmentInput(**corrosion())).outputs.combined_corrosion_rate_m_year
    direct=tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(),corrosion_rate_m_year=rate,corrosion_rate_basis="same source rate")).outputs
    assert r.combined_corrosion_rate_m_year==pytest.approx(.0001890229)
    assert r.thinning_damage_factor==direct.thinning_damage_factor


def test_corrosion_and_thinning_rpb_must_agree():
    with pytest.raises(DomainError):
        tank.bottom_corrosion_thinning_assessment(tank.BottomCorrosionThinningAssessmentInput(corrosion=corrosion(bottom_type="rpb_per_api650"),thinning=basis()))


def test_full_risk_equals_independent_steps():
    x=risk_request()
    r=tank.bottom_corrosion_risk_assessment(x).outputs
    damage=tank.bottom_corrosion_thinning_assessment(tank.BottomCorrosionThinningAssessmentInput(**x.damage.model_dump())).outputs
    direct=tank.bottom_integrated_assessment(tank.BottomIntegratedAssessmentInput(source=x.source,distance_to_groundwater_m=x.distance_to_groundwater_m,
        economics=x.economics,management_score=x.management_score,total_damage_factor=damage.thinning_damage_factor,damage_factor_source="Independent calculated fixture")).outputs
    assert r.total_damage_factor==r.thinning_damage_factor==damage.thinning_damage_factor
    assert r.financial_risk_per_year==direct.financial_risk_per_year
    assert r.annual_failure_frequency==pytest.approx(.000722*r.thinning_damage_factor)
    assert r.financial_risk_per_year==pytest.approx(r.annual_failure_frequency*r.financial_consequence)
    assert r.integration_scope=="bottom_corrosion_thinning_source_financial_risk_qualified_thinning_only"


def test_risk_rpb_mismatch_and_scope_basis_rejected():
    with pytest.raises(DomainError):
        tank.bottom_corrosion_risk_assessment(risk_request(other_mechanisms_exclusion_basis=" "))
    x=risk_request()
    source=x.source.model_dump()|dict(has_release_prevention_barrier=True,detection_overlap_basis="barrier_priority")
    with pytest.raises(DomainError):
        tank.bottom_corrosion_risk_assessment(risk_request(source=source))


@pytest.mark.parametrize("changes",[dict(starting_thickness_m=0),dict(corrosion_allowance_m=-1),dict(elapsed_years=True),dict(elapsed_years=float("inf"))])
def test_invalid_thinning_inputs(changes):
    with pytest.raises(ValidationError):
        tank.BottomThinningAssessmentInput(**basis(**changes),corrosion_rate_m_year=.0002,corrosion_rate_basis="fixture")


def test_blank_baseline_rate_and_inspection_basis():
    for kw in [dict(baseline_basis=" "),dict(inspections=dict(eligible_inspection_grades=[],eligibility_basis=" "))]:
        with pytest.raises(DomainError):
            tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(**kw),corrosion_rate_m_year=.0002,corrosion_rate_basis="fixture"))
    with pytest.raises(DomainError):
        tank.bottom_thinning_assessment(tank.BottomThinningAssessmentInput(**basis(),corrosion_rate_m_year=.0002,corrosion_rate_basis=" "))


def test_numerical_overflow_not_zero_damage():
    with pytest.raises(DomainError):
        tank.bottom_wall_parameter(tank.BottomWallParameterInput(starting_thickness_m=.006,corrosion_rate_m_year=1e308,
            elapsed_years=10,minimum_thickness_m=.00254,corrosion_allowance_m=0))
