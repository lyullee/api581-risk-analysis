"""High-temperature H2S/H2 source coordinates, composition and independent anchors."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

CELLS=json.loads((Path(__file__).parent/'fixtures/h2sh2_source_tables.json').read_text(encoding='utf-8'))['cells']
MATERIALS={'carbon_low_alloy':'carbon_steel','cr5':'cr5_0p5mo','cr7':'cr7','cr9':'cr9_1mo','cr12':'cr12','stainless':'ss_304'}


def service(**changes):
    return dict(material='cr5_0p5mo',unit_basis='printed_si',h2s_mole_fraction=.003,maximum_temperature_k=686.15,
        stream_case='gas_oil',lookup_policy='exact_nodes_only',hydrogen_sulfidation_environment_qualified=True,
        material_and_stream_qualification_basis='Qualified hydroprocessing environment, material and gas-oil curve')|changes


def request(**changes):
    return damage.H2sh2CorrosionAssessmentInput(**(dict(h2s_h2_service_present=True,applicability_basis='Qualified high-temperature hydrogen-sulfidation service',service_model=service())|changes))


@pytest.mark.parametrize('cell',CELLS)
def test_all1920_physical_si_us_source_coordinates(cell):
    r=damage.h2sh2_table_rate(damage.H2sh2TableRateInput(material=MATERIALS[cell['table_group']],unit_basis=cell['unit_basis'],h2s_mole_fraction=cell['h2s_mole_fraction'],
        maximum_temperature_k=cell['maximum_temperature_k'],stream_case=cell['curve'],lookup_policy='exact_nodes_only')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    assert r.selected_hydrocarbon_curve==cell['curve'] and r.source_thinning_type=='general'


@pytest.mark.parametrize('material',['carbon_steel','cr1_0p2mo','cr1_0p5mo','cr1p25_0p5mo','cr2p25_1mo','cr3_1mo'])
def test_six_source_cs_low_alloy_names_share_table(material):
    r=damage.h2sh2_table_axes(damage.H2sh2TableAxesInput(material=material,unit_basis='printed_si')).outputs
    assert r.table_group=='carbon_low_alloy' and r.source_table_id=='2.B.4.2M'


@pytest.mark.parametrize('material',['ss_304','ss_304l','ss_316','ss_316l','ss_321','ss_347'])
def test_six_named_stainless_grades_share_source_table_without_stream_input(material):
    r=damage.h2sh2_corrosion_assessment(request(service_model=service(material=material,stream_case=None))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00003) and r.source_table_id=='2.B.4.7M'
    with pytest.raises(DomainError):
        damage.h2sh2_corrosion_assessment(request(service_model=service(material=material)))


def test_mole_percent_converted_once_and_si_us_rounding_retained():
    axes=damage.h2sh2_table_axes(damage.H2sh2TableAxesInput(material='carbon_steel',unit_basis='printed_si')).outputs
    assert axes.h2s_mole_fraction_nodes[0]==.00002 and axes.h2s_mole_fraction_nodes[-1]==.01
    args=dict(material='carbon_steel',h2s_mole_fraction=.00002,stream_case='naphtha',lookup_policy='exact_nodes_only')
    si=damage.h2sh2_table_rate(damage.H2sh2TableRateInput(**args,unit_basis='printed_si',maximum_temperature_k=491.15)).outputs
    us=damage.h2sh2_table_rate(damage.H2sh2TableRateInput(**args,unit_basis='printed_us_converted',maximum_temperature_k=(425-32)*5/9+273.15)).outputs
    assert si.corrosion_rate_m_year==pytest.approx(.00003) and us.corrosion_rate_m_year==pytest.approx(.0000254)
    assert si.corrosion_rate_m_year!=us.corrosion_rate_m_year


def test_independent_bilinear_and_max_anchor():
    # PDF357,5Cr gas oil0.08/.30mole%,T385/413C: .91,1.30,1.32,1.85mm/year.
    args=dict(material='cr5_0p5mo',unit_basis='printed_si',h2s_mole_fraction=(.0008+.003)/2,
        maximum_temperature_k=(385+413)/2+273.15,stream_case='gas_oil')
    r=damage.h2sh2_table_rate(damage.H2sh2TableRateInput(**args,lookup_policy='bilinear')).outputs
    assert r.corrosion_rate_m_year==pytest.approx((.91+1.30+1.32+1.85)/4/1000)
    r=damage.h2sh2_table_rate(damage.H2sh2TableRateInput(**args,lookup_policy='maximum_bracketing_value')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00185)
    with pytest.raises(DomainError):
        damage.h2sh2_table_rate(damage.H2sh2TableRateInput(**args,lookup_policy='exact_nodes_only'))


def test_hydrocarbon_free_qualified_curve_no_extra50percent_multiplier():
    direct=damage.h2sh2_corrosion_assessment(request()).outputs
    r=damage.h2sh2_corrosion_assessment(request(service_model=service(stream_case='hydrocarbon_free',hydrocarbon_free_curve='gas_oil',
        hydrocarbon_free_qualification_basis='Qualified source curve for hydrocarbon-free hydrogen service'))).outputs
    assert r.corrosion_rate_m_year==direct.corrosion_rate_m_year==pytest.approx(.00185)
    assert r.hydrocarbon_free_curve_selection_used and r.selected_hydrocarbon_curve=='gas_oil'
    for changes in [dict(stream_case=None),dict(stream_case='hydrocarbon_free'),dict(hydrocarbon_free_curve='naphtha'),
        dict(stream_case='hydrocarbon_free',hydrocarbon_free_curve='gas_oil',hydrocarbon_free_qualification_basis=' ')]:
        with pytest.raises(DomainError):
            damage.h2sh2_corrosion_assessment(request(service_model=service(**changes)))


@pytest.mark.parametrize('changes',[dict(h2s_mole_fraction=0.),dict(h2s_mole_fraction=.000019),dict(h2s_mole_fraction=.01001),
    dict(maximum_temperature_k=480.),dict(maximum_temperature_k=800.),dict(hydrogen_sulfidation_environment_qualified=False),
    dict(material_and_stream_qualification_basis=' ')])
def test_no_trace_concentration_or_onset_gap_extrapolation_and_qualification(changes):
    with pytest.raises(DomainError):
        damage.h2sh2_corrosion_assessment(request(service_model=service(**changes)))


def test_no_service_specific_zero_and_unlisted_materials_not_inferred():
    r=damage.h2sh2_corrosion_assessment(request(h2s_h2_service_present=False,service_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.source_table_id is None and r.source_thinning_type is None
    with pytest.raises(DomainError):
        damage.h2sh2_corrosion_assessment(request(h2s_h2_service_present=False))
    for material in ['ss_310','cr4','unknown']:
        with pytest.raises(ValidationError):
            request(service_model=service(material=material))


def test_same_rate_thinning_dedicated_monitoring_no_service_df_floor():
    args=dict(corrosion=request(),assessment_distribution='general',distribution_qualification_basis='Qualified actual general distribution and inspection',
        starting_thickness_m=.02,elapsed_years=2.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.02,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='high_temperature_h2s_h2'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified common non-AST unclad baseline')
    r=damage.h2sh2_thinning_assessment(damage.H2sh2ThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.185)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Same independent baseline',
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00185,elapsed_years=2.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    no_service=request(h2s_h2_service_present=False,service_model=None)
    assert damage.h2sh2_thinning_assessment(damage.H2sh2ThinningAssessmentInput(**(args|dict(corrosion=no_service)))).outputs.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='other'),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.h2sh2_thinning_assessment(damage.H2sh2ThinningAssessmentInput(**(args|dict(conditions=bad))))
