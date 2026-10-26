"""Source cell access, chemistry ambiguity policies and amine/thinning composition."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

FIXTURE=json.loads((Path(__file__).parent/'fixtures/amine_source_tables.json').read_text(encoding='utf-8'))
GAP='reject_unassigned_0p10_to_0p15'


def loading(value=.35,**changes):
    return dict(acid_gas_loading_mol_mol=value,loading_gap_policy=GAP)|changes


def carbon(**changes):
    return dict(method='carbon_table',material='carbon_steel',solution=dict(amine_type='mea',amine_mass_fraction=.25),
        contaminants=dict(amine_type='mea',contaminant_mass_fraction=.03,mdea_scale_policy='not_mdea'),loading=loading(),
        maximum_temperature_k=389.15,velocity_m_s=2.,unit_basis='printed_si',lookup_policy='exact_nodes_only',
        classification_qualification_basis='Qualified rate-table velocity columns including equality interpretation',
        qualification_basis='Qualified same active amine, local temperature and concentration')|changes


def stainless(**changes):
    return dict(method='type300_stainless_table',amine_type='mea',acid_gas_loading_mol_mol=.35,maximum_temperature_k=400.,
        unit_basis='printed_si',lookup_policy='exact_nodes_only',low_loading_policy='reject_below_0p1',normal_service_conditions_qualified=True,
        qualification_basis='Qualified Type300 normal non-extreme service')|changes


def request(**changes):
    return damage.AmineCorrosionAssessmentInput(**(dict(amine_service_present=True,applicability_basis='Qualified chemical gas-treating amine service',rate_model=carbon())|changes))


@pytest.mark.parametrize('cell',FIXTURE['carbon_cells'])
def test_every1152_physical_carbon_cell_access_and_si_conversion(cell):
    r=damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(table_family=cell['table_family'],loading=loading(cell['loading_mol_mol']),
        contaminant_row=cell['contaminant_row'],maximum_temperature_k=cell['maximum_temperature_k'],velocity_m_s=cell['velocity_m_s'],
        unit_basis=cell['unit_basis'],lookup_policy='exact_nodes_only')).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    assert r.velocity_band==('low' if cell['velocity_m_s']==0 else 'high')
    assert r.source_table_id==('2.B.8.2' if cell['table_family']=='mea_dea' else '2.B.8.3')+('M' if cell['unit_basis']=='printed_si' else '')


@pytest.mark.parametrize('row',FIXTURE['stainless_rows'])
@pytest.mark.parametrize('units,col,scale',[('printed_si',1,.001),('printed_us_converted',2,.0000254)])
def test_stainless16_cells(row,units,col,scale):
    args=stainless(acid_gas_loading_mol_mol=row[0],unit_basis=units)
    args.pop('method');args.pop('amine_type')
    r=damage.amine_stainless_rate(damage.AmineStainlessRateInput(**args)).outputs
    assert r.corrosion_rate_m_year==pytest.approx(row[col]*scale)


def test_active_amine_loading_both_gases_and_nonzero_denominator():
    r=damage.amine_acid_gas_loading(damage.AmineAcidGasLoadingInput(h2s_amount_mol=20.,co2_amount_mol=15.,active_amine_amount_mol=100.,common_sample_basis='Same representative sample active moles')).outputs
    assert r.acid_gas_loading_mol_mol==.35
    with pytest.raises(ValidationError):
        damage.AmineAcidGasLoadingInput(h2s_amount_mol=20.,co2_amount_mol=15.,active_amine_amount_mol=0.,common_sample_basis='Invalid denominator')
    with pytest.raises(DomainError):
        damage.amine_acid_gas_loading(damage.AmineAcidGasLoadingInput(h2s_amount_mol=0.,co2_amount_mol=0.,active_amine_amount_mol=100.,common_sample_basis=' '))


@pytest.mark.parametrize('value',[.1,.12,.149999])
def test_loading_gap_explicit_mapping_only(value):
    with pytest.raises(DomainError):
        damage.amine_loading_selection(damage.AmineLoadingSelectionInput(**loading(value)))
    for policy,regime in [('qualified_lean_row','lean'),('qualified_first_rich_row','rich')]:
        r=damage.amine_loading_selection(damage.AmineLoadingSelectionInput(**loading(value,loading_gap_policy=policy,loading_gap_qualification_basis='Qualified source gap assignment'))).outputs
        assert r.table_loading_regime==regime and r.loading_gap_mapping_used
    with pytest.raises(DomainError):
        damage.amine_loading_selection(damage.AmineLoadingSelectionInput(**loading(value,loading_gap_policy='qualified_lean_row')))


def test_loading_bounds_and_interpolation():
    r=damage.amine_loading_selection(damage.AmineLoadingSelectionInput(**loading(.3))).outputs
    assert r.lower_loading_row_index==2 and r.upper_loading_row_index==3 and r.loading_interpolation_weight==pytest.approx(.5)
    with pytest.raises(DomainError):
        damage.amine_loading_selection(damage.AmineLoadingSelectionInput(**loading(.701)))


@pytest.mark.parametrize('amine,c,row',[('mea',.02,'low'),('dea',.020001,'middle'),('mea',.039,'middle'),('dea',.040001,'high')])
def test_mea_dea_hsas_basic_bands(amine,c,row):
    r=damage.amine_contaminant_row(damage.AmineContaminantRowInput(amine_type=amine,contaminant_mass_fraction=c,mdea_scale_policy='not_mdea')).outputs
    assert r.contaminant_row==row


def test_four_percent_boundary_not_silently_assigned():
    args=dict(amine_type='mea',contaminant_mass_fraction=.04,mdea_scale_policy='not_mdea')
    with pytest.raises(DomainError):
        damage.amine_contaminant_row(damage.AmineContaminantRowInput(**args))
    for policy,row in [('basic_data_middle_band','middle'),('printed_four_percent_high_row','high')]:
        r=damage.amine_contaminant_row(damage.AmineContaminantRowInput(**args,four_percent_boundary_policy=policy,four_percent_qualification_basis='Qualified exact-four interpretation')).outputs
        assert r.contaminant_row==row


@pytest.mark.parametrize('ppm,row',[(499.,'low'),(500.,'middle'),(4000.,'middle'),(4001.,'high')])
def test_mdea_organic_ppm_categories_and_explicit_scale_conflict(ppm,row):
    args=dict(amine_type='mdea',contaminant_mass_fraction=ppm/1e6,mdea_scale_policy='qualified_basic_data_organic_ppm_bands',mdea_scale_qualification_basis='Qualified organic-acid basic-data categories')
    assert damage.amine_contaminant_row(damage.AmineContaminantRowInput(**args)).outputs.contaminant_row==row
    with pytest.raises(DomainError):
        damage.amine_contaminant_row(damage.AmineContaminantRowInput(**(args|dict(mdea_scale_policy='not_mdea'))))


def test_mdea_literal_nodes_are_not_ppm_unit_repair():
    args=dict(amine_type='mdea',mdea_scale_policy='qualified_printed_wt_percent_nodes',mdea_scale_qualification_basis='Explicit literal printed wt% basis')
    for c,row in [(.005,'low'),(.0225,'middle'),(.04,'high')]:
        assert damage.amine_contaminant_row(damage.AmineContaminantRowInput(**args,contaminant_mass_fraction=c)).outputs.contaminant_row==row
    with pytest.raises(DomainError):
        damage.amine_contaminant_row(damage.AmineContaminantRowInput(**args,contaminant_mass_fraction=.0005))


@pytest.mark.parametrize('amine,c,f',[('mea',.2,1.),('mea',.21,1.5),('mea',.25,1.5),('mea',.25001,2.),
    ('dea',.3,1.),('dea',.31,1.2),('dea',.4,1.2),('dea',.40001,1.5),('mdea',.5,1.)])
def test_strength_factor_source_nodes_and_bands(amine,c,f):
    assert damage.amine_strength_factor(damage.AmineStrengthFactorInput(amine_type=amine,amine_mass_fraction=c)).outputs.amine_strength_factor==f


@pytest.mark.parametrize('amine,c',[('mea',.205),('dea',.305),('mdea',.5001),('mea',0.)])
def test_strength_unassigned_or_unsupported_not_interpolated(amine,c):
    with pytest.raises(DomainError):
        damage.amine_strength_factor(damage.AmineStrengthFactorInput(amine_type=amine,amine_mass_fraction=c))


@pytest.mark.parametrize('load,v,unit,band',[(.05,6.1,'printed_si','low'),(.05,6.10001,'printed_si','high'),(.15,1.5,'printed_si','low'),
    (.15,1.50001,'printed_si','high'),(.15,1.51,'printed_us_converted','low'),(.05,6.098,'printed_us_converted','high')])
def test_same_loading_regime_velocity_units_equality(load,v,unit,band):
    r=damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(table_family='mea_dea',loading=loading(load),contaminant_row='low',
        maximum_temperature_k=380.,velocity_m_s=v,unit_basis=unit,lookup_policy='linear_loading_temperature')).outputs
    assert r.velocity_band==band


def test_independently_calculated_interpolation_and_anchor_not_shared_fixture():
    args=dict(table_family='mea_dea',loading=loading(.3),contaminant_row='middle',maximum_temperature_k=(104+116)/2+273.15,
        velocity_m_s=2.,unit_basis='printed_si')
    r=damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(**args,lookup_policy='linear_loading_temperature')).outputs
    # PDF385: high-velocity,HSAS3%,loading.25/.35,104/116C ->1.02,1.27,1.14,1.52mm/y.
    assert r.base_corrosion_rate_m_year==pytest.approx((1.02+1.27+1.14+1.52)/4/1000)
    r=damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(**args,lookup_policy='maximum_bracketing_value')).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(.00152)
    with pytest.raises(DomainError):
        damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(**args,lookup_policy='exact_nodes_only'))
    with pytest.raises(DomainError):
        damage.amine_carbon_base_rate(damage.AmineCarbonBaseRateInput(**(args|dict(maximum_temperature_k=350.)),lookup_policy='linear_loading_temperature'))


def test_stainless_normal_service_gate_low_loading_and_si_us_limit():
    m=stainless();m.pop('method');m.pop('amine_type')
    for changes in [dict(normal_service_conditions_qualified=False),dict(qualification_basis=' '),dict(maximum_temperature_k=423.),dict(acid_gas_loading_mol_mol=.05)]:
        with pytest.raises(DomainError):
            damage.amine_stainless_rate(damage.AmineStainlessRateInput(**(m|changes)))
    r=damage.amine_stainless_rate(damage.AmineStainlessRateInput(**(m|dict(acid_gas_loading_mol_mol=.05,low_loading_policy='qualified_first_row',low_loading_qualification_basis='Qualified below-first source bound')))).outputs
    assert r.low_loading_first_row_used and r.corrosion_rate_m_year==pytest.approx(.00003)
    si=damage.amine_stainless_rate(damage.AmineStainlessRateInput(**(m|dict(maximum_temperature_k=422.1)))).outputs
    assert si.corrosion_rate_m_year==pytest.approx(.00005)
    with pytest.raises(DomainError):
        damage.amine_stainless_rate(damage.AmineStainlessRateInput(**(m|dict(maximum_temperature_k=422.1,unit_basis='printed_us_converted'))))


def test_carbon_composition_once_and_stainless_no_carbon_factor():
    r=damage.amine_corrosion_assessment(request()).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(.00152) and r.amine_strength_factor==1.5
    assert r.corrosion_rate_m_year==pytest.approx(.00228) and r.source_thinning_type=='local'
    r=damage.amine_corrosion_assessment(request(rate_model=stainless())).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00005) and r.amine_strength_factor is None and r.source_thinning_type is None


def test_composition_material_and_same_amine_are_qualified():
    with pytest.raises(DomainError):
        damage.amine_corrosion_assessment(request(rate_model=carbon(solution=dict(amine_type='dea',amine_mass_fraction=.3))))
    with pytest.raises(DomainError):
        damage.amine_corrosion_assessment(request(rate_model=carbon(material='low_alloy_steel')))
    assert damage.amine_corrosion_assessment(request(rate_model=carbon(material='low_alloy_steel',low_alloy_qualification_basis='Qualified source-figure low-alloy material applicability'))).outputs.corrosion_rate_m_year==pytest.approx(.00228)
    for changes in [dict(rate_model=None),dict(applicability_basis=' '),dict(rate_model=carbon(classification_qualification_basis=' '))]:
        with pytest.raises(DomainError):
            damage.amine_corrosion_assessment(request(**changes))


def test_mdea_full_service_and_no_amine_specific_zero():
    m=carbon(solution=dict(amine_type='mdea',amine_mass_fraction=.5),contaminants=dict(amine_type='mdea',contaminant_mass_fraction=.001,
        mdea_scale_policy='qualified_basic_data_organic_ppm_bands',mdea_scale_qualification_basis='Qualified organic-acid mapping'))
    r=damage.amine_corrosion_assessment(request(rate_model=m)).outputs
    assert r.source_table_id=='2.B.8.3M' and r.contaminant_row=='middle' and r.corrosion_rate_m_year==pytest.approx(.00152)
    r=damage.amine_corrosion_assessment(request(amine_service_present=False,rate_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.base_corrosion_rate_m_year is None
    with pytest.raises(DomainError):
        damage.amine_corrosion_assessment(request(amine_service_present=False))


def test_thinning_same_rate_and_monitoring_band_no_service_not_zero_df():
    args=dict(corrosion=request(),assessment_distribution='local',distribution_qualification_basis='Qualified local inspection coverage',
        starting_thickness_m=.02,elapsed_years=2.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.02,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='amine',amine_velocity_regime='high',amine_regime_basis='Same qualified rich high-velocity rate-table band'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified common non-AST unclad baseline')
    r=damage.amine_thinning_assessment(damage.AmineThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.228)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Same independent baseline',
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00228,elapsed_years=2.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    no_service=request(amine_service_present=False,rate_model=None)
    assert damage.amine_thinning_assessment(damage.AmineThinningAssessmentInput(**(args|dict(corrosion=no_service)))).outputs.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='amine',amine_velocity_regime='low',amine_regime_basis='Mismatched band'),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.amine_thinning_assessment(damage.AmineThinningAssessmentInput(**(args|dict(conditions=bad))))
