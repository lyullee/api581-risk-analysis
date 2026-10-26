"""Sulfuric source-cell routing, ambiguous units/cells and qualified composition."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

CELLS=json.loads((Path(__file__).parent/'fixtures/sulfuric_source_tables.json').read_text(encoding='utf-8'))['cells']


def table(**changes):
    return dict(material='ss_316',unit_basis='printed_si',acid_mass_fraction=.98,maximum_temperature_k=313.15,velocity_m_s=.61,lookup_policy='exact_nodes_only')|changes


def classification(**changes):
    return dict(material_group='stainless_steel',velocity_m_s=.61,threshold_basis='overview_printed_si',equality_policy='reject_ambiguous_boundary')|changes


def request(**changes):
    return damage.SulfuricCorrosionAssessmentInput(**(dict(sulfuric_service_present=True,applicability_basis='Qualified sulfuric process service',
        rate_model=dict(method='source_table',table=table(),table_conditions_and_passivity_qualified=True,qualification_basis='Qualified material and maximum local conditions'),classification=classification())|changes))


@pytest.mark.parametrize('cell',CELLS)
def test_all1776_physical_source_cell_coordinates_and_si_conversion(cell):
    args={k:cell[k] for k in ('material','unit_basis','acid_mass_fraction','maximum_temperature_k','velocity_m_s')}
    if cell['material']=='carbon_steel' and cell['unit_basis']=='printed_si':
        args.update(carbon_si_velocity_policy='qualified_printed_m_s',carbon_si_velocity_qualification_basis='Explicit literal SI header fixture')
    if cell['material']=='alloy_b2':
        args['oxidants_present']=False
    if cell['material']=='ss_304':
        args.update(disputed_304_cell_policy='qualified_printed_literal',disputed_304_qualification_basis='Explicit printed-literal source fixture')
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args,lookup_policy='exact_nodes_only')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    assert r.source_999_corner_used==(cell['native_rate']==(25.37 if cell['unit_basis']=='printed_si' else 999))
    assert r.disputed_304_cell_used==cell['disputed_304_cell']


def test_carbon_si_header_rejected_and_both_qualified_interpretations_retained():
    args=dict(material='carbon_steel',unit_basis='printed_si')
    with pytest.raises(DomainError):
        damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(**args))
    a=damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(**args,carbon_si_velocity_policy='qualified_printed_m_s',carbon_si_velocity_qualification_basis='Literal SI interpretation')).outputs
    b=damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(**args,carbon_si_velocity_policy='qualified_us_ft_s_header',carbon_si_velocity_qualification_basis='Qualified corresponding US velocity headers')).outputs
    assert a.velocity_nodes_m_s[1]==1. and b.velocity_nodes_m_s[1]==.3048
    assert a.velocity_nodes_m_s[-1]==12. and b.velocity_nodes_m_s[-1]==pytest.approx(3.6576)
    base=dict(material='carbon_steel',unit_basis='printed_si',acid_mass_fraction=.98,maximum_temperature_k=288.15,lookup_policy='exact_nodes_only')
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**base,velocity_m_s=.3048,carbon_si_velocity_policy='qualified_us_ft_s_header',carbon_si_velocity_qualification_basis='US header interpretation')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00025)
    assert not r.source_localized_enhancement_already_included
    for changes in [dict(carbon_si_velocity_qualification_basis=None),dict(carbon_si_velocity_qualification_basis=' '),dict(material='ss_316')]:
        with pytest.raises(DomainError):
            damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(**(args|dict(carbon_si_velocity_policy='qualified_us_ft_s_header',carbon_si_velocity_qualification_basis='Valid')|changes)))


@pytest.mark.parametrize('unit,t,v,expected',[('printed_si',313.15,2.13,.00251),('printed_us_converted',(104.5-32)*5/9+273.15,7*.3048,99*.0000254)])
def test_304_disputed99_literal_or_reject_never_silently999(unit,t,v,expected):
    args=table(material='ss_304',unit_basis=unit,acid_mass_fraction=.75,maximum_temperature_k=t,velocity_m_s=v)
    with pytest.raises(DomainError):
        damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args))
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args,disputed_304_cell_policy='qualified_printed_literal',disputed_304_qualification_basis='Qualified printed99 interpretation')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(expected) and r.disputed_304_cell_used and not r.source_999_corner_used
    with pytest.raises(DomainError):
        damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**(args|dict(lookup_policy='maximum_bracketing_value',acid_mass_fraction=.76))))


def test_independent_trilinear_and_max_anchor():
    # PDF370,316 conc92.5/98%,T30/40C,v.61/1.83 -> .13,.25,.38,.76 / .25,.51,.76,1.52mm/y.
    args=table(acid_mass_fraction=(.925+.98)/2,maximum_temperature_k=308.15,velocity_m_s=(.61+1.83)/2)
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**(args|dict(lookup_policy='trilinear')))).outputs
    assert r.corrosion_rate_m_year==pytest.approx((.13+.25+.38+.76+.25+.51+.76+1.52)/8/1000)
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**(args|dict(lookup_policy='maximum_bracketing_value')))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00152)
    with pytest.raises(DomainError):
        damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args))


def test_carbon_localized_enhancement_already_in_table_no_extra3x():
    r=damage.sulfuric_table_rate(damage.SulfuricTableRateInput(material='carbon_steel',unit_basis='printed_us_converted',
        acid_mass_fraction=1.,maximum_temperature_k=(42-32)*5/9+273.15,velocity_m_s=4.5*.3048,lookup_policy='exact_nodes_only')).outputs
    assert r.corrosion_rate_m_year==pytest.approx(45*.0000254) and r.source_localized_enhancement_already_included


@pytest.mark.parametrize('changes',[dict(acid_mass_fraction=.01),dict(acid_mass_fraction=.99),dict(maximum_temperature_k=299.),dict(maximum_temperature_k=340.),dict(velocity_m_s=.1),dict(velocity_m_s=3.)])
def test_no_concentration_temperature_velocity_extrapolation(changes):
    with pytest.raises(DomainError):
        damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**(table()|changes|dict(lookup_policy='trilinear'))))


def test_literal_temperature_axis_not_unit_repaired():
    si=damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(material='alloy_20',unit_basis='printed_si')).outputs
    us=damage.sulfuric_table_axes(damage.SulfuricTableAxesInput(material='alloy_20',unit_basis='printed_us_converted')).outputs
    assert si.temperature_nodes_k[2]==343.15
    assert us.temperature_nodes_k[2]==pytest.approx((163.5-32)*5/9+273.15)
    assert abs(si.temperature_nodes_k[2]-us.temperature_nodes_k[2])>3.


def test_b2_oxidizing_or_unknown_never_applied_table():
    args=table(material='alloy_b2',acid_mass_fraction=.75,maximum_temperature_k=325.15,velocity_m_s=.91)
    for state in [None,True]:
        with pytest.raises(DomainError):
            damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args,oxidants_present=state))
    assert damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**args,oxidants_present=False)).outputs.corrosion_rate_m_year==pytest.approx(.00005)
    with pytest.raises(DomainError):
        damage.sulfuric_table_rate(damage.SulfuricTableRateInput(**table(),oxidants_present=False))


@pytest.mark.parametrize('group,threshold',[('carbon_steel',.61),('stainless_steel',1.22),('higher_alloy',1.83)])
def test_source_classification_boundary_requires_policy(group,threshold):
    args=classification(material_group=group,velocity_m_s=threshold)
    with pytest.raises(DomainError):
        damage.sulfuric_thinning_classification(damage.SulfuricThinningClassificationInput(**args))
    for policy,kind in [('qualified_general','general'),('qualified_local','local')]:
        r=damage.sulfuric_thinning_classification(damage.SulfuricThinningClassificationInput(**(args|dict(equality_policy=policy,equality_qualification_basis='Qualified boundary distribution')))).outputs
        assert r.source_thinning_type==kind and r.thinning_velocity_boundary_resolved


def test_body_overview_monitoring_thresholds_differ_without_mixing_velocity():
    r=damage.sulfuric_thinning_classification(damage.SulfuricThinningClassificationInput(**classification(material_group='carbon_steel',velocity_m_s=.8))).outputs
    body=damage.sulfuric_thinning_classification(damage.SulfuricThinningClassificationInput(**classification(material_group='carbon_steel',velocity_m_s=.8,threshold_basis='detailed_carbon_body_si'))).outputs
    monitor=damage.thinning_monitoring_row(damage.ThinningMonitoringRowInput(mechanism='sulfuric_acid',sulfuric_material_group='carbon_steel',velocity_m_s=.8)).outputs
    assert r.source_thinning_type=='local' and body.source_thinning_type=='general'
    assert monitor.monitoring_row=='sulfuric_low_velocity'
    with pytest.raises(DomainError):
        damage.sulfuric_thinning_classification(damage.SulfuricThinningClassificationInput(**classification(threshold_basis='detailed_carbon_body_si')))


def test_assessment_same_conditions_and_source_max_estimate():
    r=damage.sulfuric_corrosion_assessment(request()).outputs
    assert r.corrosion_rate_m_year==pytest.approx(.00038) and r.rate_source=='source_maximum_estimate' and r.source_thinning_type=='general'
    for changes in [dict(classification=classification(velocity_m_s=.7)),dict(classification=classification(material_group='higher_alloy')),
        dict(rate_model=None),dict(applicability_basis=' '),dict(classification=None)]:
        with pytest.raises(DomainError):
            damage.sulfuric_corrosion_assessment(request(**changes))
    with pytest.raises(DomainError):
        damage.sulfuric_corrosion_assessment(request(rate_model=dict(method='source_table',table=table(),table_conditions_and_passivity_qualified=False,qualification_basis='Unqualified conditions')))


def test_specialist_oxidizing_b2_path_and_no_service_not_no_water_zero():
    m=dict(method='qualified_specialist_rate',material_description='Alloy B-2 oxidizing service fixture',material_group='higher_alloy',
        acid_mass_fraction=.75,maximum_temperature_k=325.15,velocity_m_s=.91,oxidants_present=True,corrosion_rate_m_year=.003,
        source_reference='Illustrative qualified corrosion specialist estimate',qualification_basis='Qualified oxidizingB2 and same process conditions')
    args=dict(rate_model=m,classification=classification(material_group='higher_alloy',velocity_m_s=.91))
    r=damage.sulfuric_corrosion_assessment(request(**args)).outputs
    assert r.corrosion_rate_m_year==.003 and r.source_table_id is None and r.rate_source=='qualified_specialist_estimate'
    for changes in [dict(source_reference=' '),dict(material_description=' '),dict(acid_mass_fraction=0.)]:
        with pytest.raises(DomainError):
            damage.sulfuric_corrosion_assessment(request(**(args|dict(rate_model=m|changes))))
    r=damage.sulfuric_corrosion_assessment(request(sulfuric_service_present=False,rate_model=None,classification=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.source_thinning_type is None
    with pytest.raises(DomainError):
        damage.sulfuric_corrosion_assessment(request(sulfuric_service_present=False))
    with pytest.raises(ValidationError):
        request(free_water_present=False)


def test_thinning_same_rate_monitoring_velocity_material_and_nonzero_floor():
    args=dict(corrosion=request(),assessment_distribution='general',distribution_qualification_basis='Qualified representative general-thinning coverage',
        starting_thickness_m=.02,elapsed_years=2.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.02,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='sulfuric_acid',sulfuric_material_group='stainless_steel',velocity_m_s=.61),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified common non-AST unclad baseline')
    r=damage.sulfuric_thinning_assessment(damage.SulfuricThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.038)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Same independent baseline',
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00038,elapsed_years=2.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    no_service=request(sulfuric_service_present=False,rate_model=None,classification=None)
    assert damage.sulfuric_thinning_assessment(damage.SulfuricThinningAssessmentInput(**(args|dict(corrosion=no_service)))).outputs.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='sulfuric_acid',sulfuric_material_group='stainless_steel',velocity_m_s=.7),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.sulfuric_thinning_assessment(damage.SulfuricThinningAssessmentInput(**(args|dict(conditions=bad))))
