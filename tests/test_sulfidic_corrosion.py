"""Sulfidic/naphthenic source cells, material axes, interval policies and composition."""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

CELLS=json.loads((Path(__file__).parent/'fixtures/sulfidic_source_tables.json').read_text(encoding='utf-8'))['cells']
MATERIALS={'carbon_steel':'carbon_steel','low_alloy':'cr1_0p2mo','cr5':'cr5_0p5mo','cr7':'cr7_1mo','cr9':'cr9_1mo',
    'cr12':'cr12','stainless_no_mo':'austenitic_without_mo','stainless_low_mo':'ss_316','stainless_high_mo':'ss_317'}


def table(**changes):
    return dict(material='cr5_0p5mo',unit_basis='printed_si',sulfur_mass_fraction=.015,tan_mg_koh_g=1.75,maximum_temperature_k=644.15,
        lookup_policy='exact_nodes_only',temperature_edge_policy='reject_edge_bins_and_first_gap',low_tan_policy='reject_below_first_tan')|changes


def velocity(**changes):
    return dict(velocity_m_s=31.,boundary_interpretation='body_strictly_above_100ft_s',qualification_basis='Qualified maximum stream/nozzle velocity and boundary interpretation')|changes


def request(**changes):
    return damage.SulfidicCorrosionAssessmentInput(**(dict(sulfidic_service_present=True,applicability_basis='Qualified hydrogen-free high-temperature sulfidic service',
        service_model=dict(table=table(),velocity=velocity(),liquid_phase_present=True,hydrogen_free_sulfidation_and_tan_basis_qualified=True,
            qualification_basis='Qualified actual stream sulfur, liquid TAN, material and phase conditions'))|changes))


@pytest.mark.parametrize('cell',CELLS)
def test_all3840_physical_source_cells_and_temperature_bin_semantics(cell):
    args={k:cell[k] for k in ('unit_basis','sulfur_mass_fraction','tan_mg_koh_g','maximum_temperature_k')}
    args.update(material=MATERIALS[cell['table_group']],lookup_policy='exact_nodes_only',low_tan_policy='reject_below_first_tan',
        temperature_edge_policy='qualified_source_bins_and_threshold_anchor',temperature_edge_qualification_basis='Qualified edge-bin test applicability')
    if cell['table_group']=='stainless_low_mo': args['molybdenum_mass_fraction']=.02
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args)).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(cell['expected_rate_m_year'],rel=1e-14)
    assert r.source_temperature_bin_used==('lower' if cell['temperature_column_index']==0 else 'upper' if cell['temperature_column_index']==7 else None)
    assert not r.first_temperature_threshold_anchor_used and not r.below_first_tan_row_used


@pytest.mark.parametrize('material',['ss_316','ss_316l','ss_316h'])
def test_316_mo_boundary_and_unknown_source_assumption(material):
    assumed=damage.sulfidic_material_selection(damage.SulfidicMaterialSelectionInput(material=material)).outputs
    assert assumed.table_group=='stainless_low_mo' and assumed.unknown_molybdenum_low_assumed
    for mo,group in [(.024999,'stainless_low_mo'),(.025,'stainless_high_mo'),(.03,'stainless_high_mo')]:
        r=damage.sulfidic_material_selection(damage.SulfidicMaterialSelectionInput(material=material,molybdenum_mass_fraction=mo)).outputs
        assert r.table_group==group and not r.unknown_molybdenum_low_assumed


def test_material_specific_sulfur_tan_axes_and_unused_mo_rejected():
    axes={m:damage.sulfidic_table_axes(damage.SulfidicTableAxesInput(material=m,unit_basis='printed_si')).outputs for m in ('carbon_steel','cr5_0p5mo','cr7_1mo','ss_317')}
    assert axes['carbon_steel'].sulfur_mass_fraction_nodes[2]==.006
    assert axes['cr5_0p5mo'].sulfur_mass_fraction_nodes[2]==.0075
    assert axes['cr7_1mo'].sulfur_mass_fraction_nodes[2]==.008
    assert axes['ss_317'].tan_nodes_mg_koh_g==[4.,5.,6.]
    assert axes['carbon_steel'].lower_temperature_bin_upper_k==505.15 and axes['carbon_steel'].interior_temperature_nodes_k[0]==533.15
    assert axes['carbon_steel'].upper_temperature_bin_lower_exclusive_k==672.15
    with pytest.raises(DomainError):
        damage.sulfidic_material_selection(damage.SulfidicMaterialSelectionInput(material='ss_317',molybdenum_mass_fraction=.03))


@pytest.mark.parametrize('temperature,bin_used',[(500.,'lower'),(505.15,'lower'),(673.,'upper'),(800.,'upper')])
def test_temperature_bins_need_qualification_not_invented_finite_nodes(temperature,bin_used):
    args=table(maximum_temperature_k=temperature)
    with pytest.raises(DomainError):
        damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args))
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(temperature_edge_policy='qualified_source_bins_and_threshold_anchor',
        temperature_edge_qualification_basis='Qualified actual interval conditions')))).outputs
    assert r.source_temperature_bin_used==bin_used


def test_first_gap_threshold_anchor_qualified_and_no_last_bin_interpolation():
    args=table(maximum_temperature_k=(232+260)/2+273.15,lookup_policy='trilinear')
    with pytest.raises(DomainError):
        damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args))
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(temperature_edge_policy='qualified_source_bins_and_threshold_anchor',temperature_edge_qualification_basis='Qualified first threshold anchor')))).outputs
    assert r.first_temperature_threshold_anchor_used and r.source_temperature_bin_used is None
    assert r.base_corrosion_rate_m_year==pytest.approx((.13+.25)/2/1000)
    at=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**table(maximum_temperature_k=672.15))).outputs
    above=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**table(maximum_temperature_k=672.1501,
        temperature_edge_policy='qualified_source_bins_and_threshold_anchor',temperature_edge_qualification_basis='Qualified upper bin'))).outputs
    assert at.base_corrosion_rate_m_year==pytest.approx(.00102) and above.base_corrosion_rate_m_year==pytest.approx(.00114)


def test_lower_tan_extension_not_silently_assumed_and_upper_not_extrapolated():
    args=table(material='ss_317',tan_mg_koh_g=3.)
    with pytest.raises(DomainError):
        damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args))
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(low_tan_policy='qualified_first_tan_row',low_tan_qualification_basis='Qualified below-firstTAN screening assumption')))).outputs
    assert r.below_first_tan_row_used
    for changes in [dict(tan_mg_koh_g=7.),dict(sulfur_mass_fraction=.001),dict(sulfur_mass_fraction=.031)]:
        with pytest.raises(DomainError):
            damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(table()|changes)))


def test_independent_trilinear_and_max_expectations_not_fixture_copy():
    # PDF339,5Cr,S.4/.75wt%,TAN.7/1.1,T260/288C: .05,.08,.08,.10 / .05,.10,.10,.15mm/y.
    args=table(sulfur_mass_fraction=(.004+.0075)/2,tan_mg_koh_g=(.7+1.1)/2,maximum_temperature_k=(260+288)/2+273.15,lookup_policy='trilinear')
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args)).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx((.05+.08+.08+.10+.05+.10+.10+.15)/8/1000)
    r=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(lookup_policy='maximum_bracketing_value')))).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(.00015)
    with pytest.raises(DomainError):
        damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(lookup_policy='exact_nodes_only'))))


def test_source_nonmonotonic12cr_temperature_cells_not_repaired():
    args=table(material='cr12',sulfur_mass_fraction=.002,tan_mg_koh_g=3.)
    at371=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**args)).outputs
    at399=damage.sulfidic_table_rate(damage.SulfidicTableRateInput(**(args|dict(maximum_temperature_k=672.15)))).outputs
    assert at371.base_corrosion_rate_m_year==pytest.approx(.00076) and at399.base_corrosion_rate_m_year==pytest.approx(.00064)


@pytest.mark.parametrize('value,body,figure',[(30.479,1.,1.),(30.48,1.,5.),(30.481,5.,5.)])
def test_100ft_velocity_body_figure_exact_boundary_conflict(value,body,figure):
    for policy,f in [('body_strictly_above_100ft_s',body),('figure_at_or_above_100ft_s',figure)]:
        r=damage.sulfidic_velocity_factor(damage.SulfidicVelocityFactorInput(**velocity(velocity_m_s=value,boundary_interpretation=policy))).outputs
        assert r.velocity_factor==f and r.velocity_boundary_conflict_encountered==(value==30.48)


@pytest.mark.parametrize('tan,kind',[(0.,'general'),(.5,'general'),(.500001,'local')])
def test_tan_source_classification_boundary(tan,kind):
    assert damage.sulfidic_thinning_classification(damage.SulfidicThinningClassificationInput(tan_mg_koh_g=tan)).outputs.source_thinning_type==kind


def test_assessment_one_velocity_factor_and_liquid_process_qualification():
    r=damage.sulfidic_corrosion_assessment(request()).outputs
    assert r.base_corrosion_rate_m_year==pytest.approx(.00089) and r.velocity_factor==5.
    assert r.corrosion_rate_m_year==pytest.approx(.00445) and r.source_thinning_type=='local'
    m=request().service_model.model_dump()
    for changes in [dict(liquid_phase_present=False),dict(hydrogen_free_sulfidation_and_tan_basis_qualified=False),dict(qualification_basis=' ')]:
        with pytest.raises(DomainError):
            damage.sulfidic_corrosion_assessment(request(service_model=m|changes))
    below=m|dict(table=table(maximum_temperature_k=470.,temperature_edge_policy='qualified_source_bins_and_threshold_anchor',temperature_edge_qualification_basis='Owner basis'))
    with pytest.raises(DomainError):
        damage.sulfidic_corrosion_assessment(request(service_model=below))


def test_no_service_specific_zero_and_invalid_material():
    r=damage.sulfidic_corrosion_assessment(request(sulfidic_service_present=False,service_model=None)).outputs
    assert r.corrosion_rate_m_year==0 and r.base_corrosion_rate_m_year is None
    with pytest.raises(DomainError):
        damage.sulfidic_corrosion_assessment(request(sulfidic_service_present=False))
    with pytest.raises(ValidationError):
        damage.SulfidicMaterialSelectionInput(material='ss_310')


def test_thinning_same_rate_no_extra5x_and_dedicated_monitoring():
    args=dict(corrosion=request(),assessment_distribution='local',distribution_qualification_basis='Qualified actual local distribution and coverage',
        starting_thickness_m=.05,elapsed_years=1.,strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.05,shape='cylinder'),inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='high_temperature_sulfidic_naphthenic'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),qualification_basis='Qualified non-AST unclad common baseline')
    r=damage.sulfidic_thinning_assessment(damage.SulfidicThinningAssessmentInput(**args)).outputs
    assert r.wall_loss_fraction==pytest.approx(.089)
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope='non_ast_unclad',qualification_basis='Same independent baseline',
        wall=dict(starting_thickness_m=.05,corrosion_rate_m_year=.00445,elapsed_years=1.),strength=args['strength'],inspections=args['inspections'],conditions=args['conditions'])).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    no_service=request(sulfidic_service_present=False,service_model=None)
    assert damage.sulfidic_thinning_assessment(damage.SulfidicThinningAssessmentInput(**(args|dict(corrosion=no_service)))).outputs.thinning_damage_factor>=.1
    bad=args['conditions']|dict(monitoring=dict(row=dict(mechanism='high_temperature_h2s_h2'),methods=[],organized_monitoring_plan=False))
    with pytest.raises(DomainError):
        damage.sulfidic_thinning_assessment(damage.SulfidicThinningAssessmentInput(**(args|dict(conditions=bad))))
