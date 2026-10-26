"""HF physical cells, rounded thresholds, residual columns and source conflicts."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

CELLS = json.loads((Path(__file__).parent/'fixtures/hf_source_tables.json').read_text(encoding='utf-8'))['cells']
REJECT = 'reject_above_81wt_percent'


def carbon(**changes):
    return dict(method='carbon_steel_table',hf_mass_fraction=.81,concentrated_extension_policy=REJECT,
        maximum_temperature_k=333.15,velocity_m_s=1.,velocity_basis='printed_si',residual_category='high',
        residual_qualification_basis='Qualified residual metallurgy category, not numeric cutoff',unit_basis='printed_si',lookup_policy='exact_nodes_only',
        established_scale_and_stable_operation_qualified=True,material_residual_content_qualified=True,
        qualification_basis='Qualified established fluoride scale, stable temperature and metallurgy')|changes


def alloy(**changes):
    return dict(method='alloy400_table',hf_mass_fraction=.64,concentrated_extension_policy=REJECT,
        maximum_temperature_k=352.15,aerated_or_oxidants_present=True,unit_basis='printed_si',lookup_policy='exact_nodes_only',
        material_and_aeration_qualified=True,qualification_basis='Qualified Alloy400 and actual aeration state')|changes


def request(**changes):
    return damage.HfAssessmentInput(**(dict(hf_exposure_present=True,applicability_basis='Qualified HF service and exposure',rate_model=carbon(),
        galvanic_coupling_present=False,thinning_classification_policy='overview_local',
        classification_qualification_basis='Explicit overview local classification and inspection review')|changes))


@pytest.mark.parametrize('cell',CELLS)
def test_all380_physical_si_us_cells_from_independent_source_fixture(cell):
    args=dict(hf_mass_fraction=cell['hf_mass_fraction'],maximum_temperature_k=cell['maximum_temperature_k'],
        unit_basis=cell['unit_basis'],concentrated_extension_policy=REJECT,lookup_policy='exact_nodes_only')
    if cell['material']=='carbon_steel':
        result=damage.hf_carbon_rate(damage.HfCarbonRateInput(**args,velocity_m_s=cell['velocity_m_s'],velocity_basis=cell['unit_basis'],
            residual_category=cell['residual_category'],residual_qualification_basis='Independent source residual column' if cell['residual_category'] else None)).outputs
    else:
        result=damage.hf_alloy400_rate(damage.HfAlloy400RateInput(**args,aerated_or_oxidants_present=cell['aerated_or_oxidants_present'])).outputs
    assert result.corrosion_rate_m_year==pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    assert result.source_999_corner_used==(cell['native_rate']==(25.37 if cell['unit_basis']=='printed_si' else 999))
    assert not result.concentrated_81_node_extension_used


@pytest.mark.parametrize('velocity,basis,band',[(3.049,'printed_si','low'),(3.05,'printed_si','high'),
    (3.048,'printed_us_converted','high'),(3.0479,'printed_us_converted','low'),(3.049,'printed_us_converted','high')])
def test_velocity_equality_is_high_and_si_us_thresholds_are_distinct(velocity,basis,band):
    r=damage.hf_carbon_velocity_band(damage.HfCarbonVelocityBandInput(velocity_m_s=velocity,velocity_basis=basis)).outputs
    assert r.velocity_band==band


def test_concentration_extension_is_not_automatic_anhydrous_immunity():
    for c in [.009,.81001,1.]:
        with pytest.raises(DomainError):
            damage.hf_concentration_selection(damage.HfConcentrationSelectionInput(hf_mass_fraction=c,concentrated_extension_policy=REJECT))
    r=damage.hf_concentration_selection(damage.HfConcentrationSelectionInput(hf_mass_fraction=1.,
        concentrated_extension_policy='qualified_81wt_percent_node',concentrated_extension_qualification_basis='Explicit anhydrous table extension review')).outputs
    assert r.hf_mass_fraction_for_lookup==.81 and r.concentrated_81_node_extension_used
    r=damage.hf_assessment(request(rate_model=carbon(hf_mass_fraction=.98,concentrated_extension_policy='qualified_81wt_percent_node',
        concentrated_extension_qualification_basis='Owner-qualified concentrated acid and81-column applicability'))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00076) and r.concentrated_81_node_extension_used
    with pytest.raises(ValidationError):
        request(free_water_present=False) # no free-water-based zero branch in HF model


@pytest.mark.parametrize('policy,basis',[(REJECT,'unused'),('qualified_81wt_percent_node',None),('qualified_81wt_percent_node',' ')])
def test_concentration_extension_policy_basis_pair(policy,basis):
    with pytest.raises(DomainError):
        damage.hf_concentration_selection(damage.HfConcentrationSelectionInput(hf_mass_fraction=.81,
            concentrated_extension_policy=policy,concentrated_extension_qualification_basis=basis))


def test_80_81_residual_interpolation_and_no_unqualified_category():
    args=dict(hf_mass_fraction=.805,concentrated_extension_policy=REJECT,maximum_temperature_k=333.15,velocity_m_s=1.,
        velocity_basis='printed_si',unit_basis='printed_si',lookup_policy='bilinear')
    low=damage.hf_carbon_rate(damage.HfCarbonRateInput(**args,residual_category='low',residual_qualification_basis='Qualified low category')).outputs
    high=damage.hf_carbon_rate(damage.HfCarbonRateInput(**args,residual_category='high',residual_qualification_basis='Qualified high category')).outputs
    assert low.corrosion_rate_m_year==pytest.approx((.76+.25)/2/1000)
    assert high.corrosion_rate_m_year==pytest.approx(.00076)
    with pytest.raises(DomainError):
        damage.hf_carbon_rate(damage.HfCarbonRateInput(**args))
    with pytest.raises(DomainError):
        damage.hf_carbon_rate(damage.HfCarbonRateInput(**(args|dict(hf_mass_fraction=.8)),residual_category='high',residual_qualification_basis='Unused'))
    exact80=damage.hf_carbon_rate(damage.HfCarbonRateInput(**(args|dict(hf_mass_fraction=.8)))).outputs
    assert exact80.residual_column_used is None


def test_bilinear_max_and_no_temperature_or_concentration_extrapolation():
    args=dict(hf_mass_fraction=.015,concentrated_extension_policy=REJECT,maximum_temperature_k=(27+41)/2+273.15,
        velocity_m_s=1.,velocity_basis='printed_si',unit_basis='printed_si')
    r=damage.hf_carbon_rate(damage.HfCarbonRateInput(**args,lookup_policy='bilinear')).outputs
    assert r.corrosion_rate_m_year==pytest.approx((.05+3.81+.25+12.7)/4/1000)
    r=damage.hf_carbon_rate(damage.HfCarbonRateInput(**args,lookup_policy='maximum_bracketing_value')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.0127)
    for changes in [dict(lookup_policy='exact_nodes_only'),dict(maximum_temperature_k=299.,lookup_policy='bilinear'),
        dict(maximum_temperature_k=370.,lookup_policy='bilinear'),dict(hf_mass_fraction=.009,lookup_policy='bilinear')]:
        with pytest.raises(DomainError):
            damage.hf_carbon_rate(damage.HfCarbonRateInput(**(args|changes)))


def test_alloy400_aeration_is_table_specific_and_has_no_velocity_input():
    r=damage.hf_assessment(request(rate_model=alloy())).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00127) and r.velocity_band is None and r.source_table_id=='2.B.6.3M'
    with pytest.raises(ValidationError):
        request(rate_model=alloy(velocity_m_s=1.))
    r=damage.hf_assessment(request(rate_model=alloy(aerated_or_oxidants_present=False))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00025)


def test_source_thinning_conflict_explicit_and_galvanic_not_quantified_by_tables():
    overview=damage.hf_assessment(request()).outputs
    body=damage.hf_assessment(request(thinning_classification_policy='detailed_general_without_galvanic')).outputs
    assert overview.source_thinning_type=='local' and body.source_thinning_type=='general'
    assert overview.corrosion_rate_m_year==body.corrosion_rate_m_year
    for changes in [dict(galvanic_coupling_present=True),dict(thinning_classification_policy=None),dict(classification_qualification_basis=None),
        dict(classification_qualification_basis=' '),dict(galvanic_coupling_present=None),dict(rate_model=None)]:
        with pytest.raises(DomainError):
            damage.hf_assessment(request(**changes))


@pytest.mark.parametrize('changes',[dict(established_scale_and_stable_operation_qualified=False),dict(material_residual_content_qualified=False),
    dict(qualification_basis=' '),dict(residual_qualification_basis=' ')])
def test_carbon_scale_and_residual_metallurgy_not_assumed(changes):
    with pytest.raises(DomainError):
        damage.hf_assessment(request(rate_model=carbon(**changes)))


def test_alloy400_material_and_aeration_qualification_required():
    with pytest.raises(DomainError):
        damage.hf_assessment(request(rate_model=alloy(material_and_aeration_qualified=False)))


def test_published_rate_path_for_other_material_or_galvanic_conditions_preserves_source():
    m=dict(method='qualified_published_rate',material_description='Owner qualified other alloy fixture',hf_mass_fraction=.95,
        maximum_temperature_k=390.,velocity_m_s=2.,corrosion_rate_m_year=.0002,
        published_source_reference='Illustrative published material/conditions data reference',qualification_basis='Qualified same HF concentration, temperature and galvanic conditions')
    r=damage.hf_assessment(request(rate_model=m,galvanic_coupling_present=True)).outputs
    assert r.corrosion_rate_m_year==.0002 and r.rate_source=='qualified_published_rate' and r.source_table_id is None
    assert r.hf_mass_fraction_for_lookup is None and not r.concentrated_81_node_extension_used
    for changes in [dict(published_source_reference=' '),dict(material_description=' '),dict(qualification_basis=' '),dict(hf_mass_fraction=0.)]:
        with pytest.raises(DomainError):
            damage.hf_assessment(request(rate_model=m|changes))
    with pytest.raises(DomainError):
        damage.hf_assessment(request(rate_model=m,galvanic_coupling_present=True,thinning_classification_policy='detailed_general_without_galvanic'))


def test_no_hf_exposure_specific_zero_rejects_unused_conditions():
    r=damage.hf_assessment(damage.HfAssessmentInput(hf_exposure_present=False,applicability_basis='Qualified no HF exposure')).outputs
    assert r.corrosion_rate_m_year==0 and r.source_thinning_type is None and r.source_table_id is None
    with pytest.raises(DomainError):
        damage.hf_assessment(request(hf_exposure_present=False))


def test_same_rate_thinning_and_hf_monitoring_with_no_exposure_df_floor():
    args=dict(corrosion=request(),assessment_distribution='local',distribution_qualification_basis='Qualified local pit/inspection distribution',
        starting_thickness_m=.02,elapsed_years=2.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.02,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='hydrofluoric_acid'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified common non-AST unclad baseline')
    r=damage.hf_thinning_assessment(damage.HfThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.076)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Independent equivalent baseline',
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00076,elapsed_years=2.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    no_hf=dict(hf_exposure_present=False,applicability_basis='Qualified no HF exposure')
    r=damage.hf_thinning_assessment(damage.HfThinningAssessmentInput(**(args|dict(corrosion=no_hf)))).outputs
    assert r.corrosion_rate_m_year==0 and r.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='other'),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.hf_thinning_assessment(damage.HfThinningAssessmentInput(**(args|dict(conditions=bad))))
