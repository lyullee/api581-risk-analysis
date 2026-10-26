"""Independent source cells, conversion gaps, chemistry composition and HCl routing."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

CELLS = json.loads((Path(__file__).parent/'fixtures/hcl_source_tables.json').read_text(encoding='utf-8'))['cells']


def ph_model(**changes):
    return dict(model_family='ph_table',material='carbon_steel',acidity=dict(method='supplied_ph',ph=3.25,qualification_basis='Separated aqueous phase fixture'),
        maximum_temperature_k=352.15,unit_basis='printed_si',lookup_policy='exact_nodes_only',qualification_basis='Qualified local maximum temperature and material')|changes


def alloy_model(**changes):
    return dict(model_family='alloy_table',material='alloy_400',chloride=dict(method='supplied_chloride',chloride_mass_fraction=.0075,qualification_basis='Qualified separated-phase chloride'),
        maximum_temperature_k=352.15,oxidants_present=True,material_heat_treatment_qualified=True,unit_basis='printed_si',
        lookup_policy='exact_nodes_only',qualification_basis='Qualified alloy condition and local temperature')|changes


def assessment(**changes):
    return damage.HclAssessmentInput(**(dict(free_water_present=True,dilute_hcl_service_qualified=True,
        applicability_basis='Qualified dilute HCl aqueous service',wet_model=ph_model())|changes))


def screen(**changes):
    return dict(free_water_present=True,ph=3.25,chlorides_present=True,chloride_policy='figure_any_presence_routes_hcl',
        neutral_ph_policy='detailed_body_inclusive',qualification_basis='Qualified shared acid phase')|changes


@pytest.mark.parametrize('cell',CELLS)
def test_every_physical_table_cell_against_independent_source_extraction(cell):
    common = dict(material=cell['material'],maximum_temperature_k=cell['maximum_temperature_k'],unit_basis=cell['unit_basis'],lookup_policy='exact_nodes_only')
    if cell['ph'] is not None:
        result = damage.hcl_ph_rate(damage.HclPhRateInput(**common,ph=cell['ph'])).outputs
        assert result.localized_pitting_already_included == (cell['material'] != 'carbon_steel')
    else:
        result = damage.hcl_alloy_rate(damage.HclAlloyRateInput(**common,chloride_mass_fraction=cell['chloride_mass_fraction'],oxidants_present=cell['oxidants_present'])).outputs
    assert result.corrosion_rate_m_year == pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    sentinel = cell['native_rate'] == (25.37 if cell['unit_basis']=='printed_si' else 999)
    assert result.source_999_corner_used == sentinel


@pytest.mark.parametrize('ppm,ph',[(0,5),(.99,5),(1,4.5),(2,4.5),(3,4),(5,4),(6,3.5),(15,3.5),(16,3),(35,3),
    (36,2.5),(120,2.5),(121,2),(360,2),(361,1.5),(1200,1.5),(1201,1),(3600,1),(3601,.5),(12000,.5)])
def test_forward_band_endpoints_and_inverse_interval(ppm,ph):
    r=damage.hcl_ph_from_chloride(damage.HclPhFromChlorideInput(chloride_mass_fraction=ppm/1e6,
        no_alkaline_agents_qualified=True,qualification_basis='Qualified no alkaline agents')).outputs
    assert r.estimated_ph==ph
    inverse=damage.hcl_chloride_interval_from_ph(damage.HclChlorideIntervalFromPhInput(ph=ph,
        no_alkaline_agents_qualified=True,qualification_basis='Qualified inverse fixture')).outputs
    assert inverse.chloride_band_lower_wppm==r.chloride_band_lower_wppm
    assert inverse.chloride_band_upper_wppm==r.chloride_band_upper_wppm
    assert inverse.chloride_band_upper_inclusive==(ph!=5)


@pytest.mark.parametrize('ppm',[2.5,5.5,15.5,35.5,120.5,360.5,1200.5,3600.5,12001])
def test_unassigned_continuous_concentration_gaps_never_filled(ppm):
    with pytest.raises(DomainError):
        damage.hcl_ph_from_chloride(damage.HclPhFromChlorideInput(chloride_mass_fraction=ppm/1e6,
            no_alkaline_agents_qualified=True,qualification_basis='Qualified concentration'))


def test_conversion_qualification_and_inverse_not_invented():
    for value in [False,True]:
        with pytest.raises(DomainError):
            damage.hcl_ph_from_chloride(damage.HclPhFromChlorideInput(chloride_mass_fraction=.005,
                no_alkaline_agents_qualified=value,qualification_basis=' ' if value else 'Alkaline agent present'))
    with pytest.raises(DomainError):
        damage.hcl_chloride_interval_from_ph(damage.HclChlorideIntervalFromPhInput(ph=2.25,
            no_alkaline_agents_qualified=True,qualification_basis='No inverse row'))


@pytest.mark.parametrize('material',['ss_304','ss_316','ss_321','ss_347'])
def test_stainless_shared_grades_do_not_apply_pitting_factor_twice(material):
    r=damage.hcl_assessment(assessment(wet_model=ph_model(material=material))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00127)
    assert r.localized_pitting_already_included and r.source_thinning_type=='local'


def test_825_and_20_share_table_and_b2_400_oxidants_are_separate_cells():
    args=dict(chloride_mass_fraction=.0075,maximum_temperature_k=311.15,unit_basis='printed_us_converted',lookup_policy='bilinear')
    assert damage.hcl_alloy_rate(damage.HclAlloyRateInput(material='alloy_825',**args)).outputs.corrosion_rate_m_year==damage.hcl_alloy_rate(damage.HclAlloyRateInput(material='alloy_20',**args)).outputs.corrosion_rate_m_year
    rates=[]
    for oxidants in (False,True):
        rates.append(damage.hcl_alloy_rate(damage.HclAlloyRateInput(material='alloy_400',oxidants_present=oxidants,
            chloride_mass_fraction=.0075,maximum_temperature_k=(100-32)*5/9+273.15,unit_basis='printed_us_converted',lookup_policy='exact_nodes_only')).outputs.corrosion_rate_m_year)
    assert rates[1]/rates[0]==5 # printed cell2->10mpy, not a universal4x multiplier


@pytest.mark.parametrize('material,oxidants',[('alloy_400',None),('alloy_b2',None),('alloy_825',False),('alloy_c276',True)])
def test_missing_or_unused_oxidant_input_rejected(material,oxidants):
    with pytest.raises(DomainError):
        damage.hcl_alloy_rate(damage.HclAlloyRateInput(material=material,oxidants_present=oxidants,
            chloride_mass_fraction=.005,maximum_temperature_k=311.15,unit_basis='printed_si',lookup_policy='exact_nodes_only'))


def test_bilinear_max_and_999_corner_flag():
    args=dict(material='carbon_steel',ph=3.5,maximum_temperature_k=(52+79)/2+273.15,unit_basis='printed_si')
    bilinear=damage.hcl_ph_rate(damage.HclPhRateInput(**args,lookup_policy='bilinear')).outputs
    assert bilinear.corrosion_rate_m_year==pytest.approx((1.78+2.54+1.27+2.29)/4/1000)
    maximum=damage.hcl_ph_rate(damage.HclPhRateInput(**args,lookup_policy='maximum_bracketing_value')).outputs
    assert maximum.corrosion_rate_m_year==pytest.approx(.00254)
    with pytest.raises(DomainError):
        damage.hcl_ph_rate(damage.HclPhRateInput(**args,lookup_policy='exact_nodes_only'))
    flagged=damage.hcl_ph_rate(damage.HclPhRateInput(material='carbon_steel',ph=1.5,maximum_temperature_k=352.15,
        unit_basis='printed_si',lookup_policy='bilinear')).outputs
    assert flagged.source_999_corner_used


@pytest.mark.parametrize('changes',[dict(ph=.49),dict(ph=6.81),dict(maximum_temperature_k=300.),dict(maximum_temperature_k=400.)])
def test_no_ph_or_temperature_extrapolation(changes):
    with pytest.raises((DomainError,ValidationError)):
        damage.hcl_ph_rate(damage.HclPhRateInput(**(dict(material='carbon_steel',ph=3.25,maximum_temperature_k=352.15,
            unit_basis='printed_si',lookup_policy='bilinear')|changes)))


def test_assessment_supplied_and_derived_ph_and_inverse_selected_chloride():
    r=damage.hcl_assessment(assessment()).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00254) and r.ph_used==3.25 and r.chloride_mass_fraction_used is None
    derived=dict(method='chloride_table',chloride_mass_fraction=100/1e6,no_alkaline_agents_qualified=True,qualification_basis='No neutralizers')
    r=damage.hcl_assessment(assessment(wet_model=ph_model(acidity=derived,lookup_policy='bilinear'))).outputs
    assert r.ph_used==2.5 and r.chemistry_method=='chloride_table'
    chloride=dict(method='ph_interval_selection',ph=.5,no_alkaline_agents_qualified=True,qualification_basis='No neutralizers',
        chloride_mass_fraction=.0075,selection_qualification_basis='Qualified selection inside inverse chloride band')
    r=damage.hcl_assessment(assessment(wet_model=alloy_model(chloride=chloride))).outputs
    assert r.ph_used==.5 and r.corrosion_rate_m_year==pytest.approx(.00813)
    for changes in [dict(ph=1.),dict(selection_qualification_basis=' '),dict(no_alkaline_agents_qualified=False)]:
        with pytest.raises(DomainError):
            damage.hcl_assessment(assessment(wet_model=alloy_model(chloride=chloride|changes)))


@pytest.mark.parametrize('changes',[dict(dilute_hcl_service_qualified=False),dict(wet_model=None),dict(applicability_basis=' '),
    dict(wet_model=alloy_model(material_heat_treatment_qualified=False)),dict(wet_model=ph_model(qualification_basis=' '))])
def test_wet_applicability_is_required(changes):
    with pytest.raises(DomainError):
        damage.hcl_assessment(assessment(**changes))


def test_dry_specific_zero_and_unused_model_rejection():
    r=damage.hcl_assessment(assessment(free_water_present=False,wet_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.ph_used is None and r.source_table_id is None
    with pytest.raises(DomainError):
        damage.hcl_assessment(assessment(free_water_present=False))


def test_hcl_router_and_shared_phase_consistency():
    args=dict(screening=screen(),hcl_model=assessment(),hcl_shared_phase_qualification_basis='Same separated acid phase fixture')
    r=damage.sour_water_assessment(damage.SourWaterAssessmentInput(**args)).outputs
    assert r.corrosion_route=='hydrochloric_acid' and r.corrosion_rate_m_year==pytest.approx(.00254)
    assert r.localized_attack_review_required
    for changes in [dict(screening=screen(ph=3.)),dict(hcl_shared_phase_qualification_basis=None),dict(hcl_shared_phase_qualification_basis=' '),
        dict(screening=screen(ph=8.)),dict(hcl_model=assessment(free_water_present=False,wet_model=None))]:
        with pytest.raises(DomainError):
            damage.sour_water_assessment(damage.SourWaterAssessmentInput(**(args|changes)))
    high=dict(screening=screen(ph=.5,chloride_concentration_ppm=7500.),hcl_model=assessment(wet_model=alloy_model()),
        hcl_shared_phase_qualification_basis='Same separated acid phase fixture')
    assert damage.sour_water_assessment(damage.SourWaterAssessmentInput(**high)).outputs.corrosion_rate_m_year==pytest.approx(.00813)
    with pytest.raises(DomainError):
        damage.sour_water_assessment(damage.SourWaterAssessmentInput(**(high|dict(screening=screen(ph=.5,chloride_concentration_ppm=5000.)))))


def test_thinning_same_rate_hcl_monitor_and_nonzero_dry_df():
    args=dict(corrosion=assessment(),assessment_distribution='local',distribution_qualification_basis='Qualified localized inspection coverage',
        starting_thickness_m=.02,elapsed_years=1.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.02,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='hydrochloric_acid'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified non-AST unclad baseline')
    r=damage.hcl_thinning_assessment(damage.HclThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.127)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Independent composition',
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00254,elapsed_years=1.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    r=damage.hcl_thinning_assessment(damage.HclThinningAssessmentInput(**(args|dict(corrosion=assessment(free_water_present=False,wet_model=None))))).outputs
    assert r.corrosion_rate_m_year==0 and r.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='other'),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.hcl_thinning_assessment(damage.HclThinningAssessmentInput(**(args|dict(conditions=bad))))


@pytest.mark.parametrize('material',['ss_310','low_alloy_steel','alloy_unknown'])
def test_unlisted_material_not_inferred(material):
    with pytest.raises(ValidationError):
        assessment(wet_model=ph_model(material=material))
