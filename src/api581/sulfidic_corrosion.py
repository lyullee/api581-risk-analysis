"""2016 modified McConomy/naphthenic source tables and explicit edge policies."""
from bisect import bisect_left
from itertools import product
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from ._sulfidic_tables import TABLES
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Material=Literal['carbon_steel','cr1_0p2mo','cr1_0p5mo','cr1p25_0p5mo','cr2p25_1mo','cr3_1mo',
    'cr5_0p5mo','cr7_1mo','cr9_1mo','cr12','austenitic_without_mo','ss_304','ss_304l','ss_321','ss_347','ss_316','ss_316l','ss_316h','ss_317']
Group=Literal['carbon_steel','low_alloy','cr5','cr7','cr9','cr12','stainless_no_mo','stainless_low_mo','stainless_high_mo']
Units=Literal['printed_si','printed_us_converted']
_GROUPS=Group.__args__


class SulfidicMaterial(Model):
    material: Material
    molybdenum_mass_fraction: Fraction | None=None


@calculation('damage/sulfidic-material-selection','Sulfidic/naphthenic material and316 molybdenum source group',SulfidicMaterial,
    ['Part2 Table2.B.3.1,Tables3.2-3.10M; PDF pp333-351'],limitations=[
        'Named alloys only, no continuousCr interpolation.316/316L/316H withMo>=2.5wt% use high-Mo group, below use low; unknownMo assumes<2.5wt% per source and flags assumption.317source high-Mo group;Mo input only used for316family and rejected elsewhere. Austenitic-withoutMo includes304/304L/321/347. Actual composition/material suitability remains owner-qualified.'])
def material_selection(x):
    family=x.material in ('ss_316','ss_316l','ss_316h')
    ensure(family or x.molybdenum_mass_fraction is None,'Mo concentration input applies only to316-family selection')
    assumed=family and x.molybdenum_mass_fraction is None
    if family:
        group='stainless_low_mo' if assumed or x.molybdenum_mass_fraction<.025 else 'stainless_high_mo'
    elif x.material=='ss_317': group='stainless_high_mo'
    elif x.material.startswith('ss_') or x.material=='austenitic_without_mo': group='stainless_no_mo'
    else: group={'carbon_steel':'carbon_steel','cr5_0p5mo':'cr5','cr7_1mo':'cr7','cr9_1mo':'cr9','cr12':'cr12'}.get(x.material,'low_alloy')
    return {'table_group':group,'unknown_molybdenum_low_assumed':assumed}


class SulfidicAxes(SulfidicMaterial):
    unit_basis: Units


@calculation('damage/sulfidic-table-axes','Sulfidic/naphthenic sulfur TAN and temperature-bin axes',SulfidicAxes,
    ['Part2 Tables2.B.3.2-3.10M; PDF pp334-351'],limitations=[
        'Material-specific sulfur andTAN grids, not common axes. CS sulfur0.6wt% versus5Cr0.75wt% and most others0.8wt% preserved. Lower temperature column<=232C/450F is interval, upper>399C/750F interval; neither invented finite node. Interior six temperature nodes exposed separately. Interpolation near first bin needs explicit threshold-anchor qualification. SI/US rates/temperatures retain rounding.'])
def table_axes(x):
    selected=material_selection(x)
    data=TABLES[selected['table_group']+'_'+x.unit_basis]
    temps=[t+273.15 for t in (232,260,288,315,343,371,399)] if x.unit_basis=='printed_si' else [(t-32)*5/9+273.15 for t in (450,500,550,600,650,700,750)]
    return {**selected,'sulfur_mass_fraction_nodes':list(data['sulfur_mass_fractions']),'tan_nodes_mg_koh_g':list(data['tan_mg_koh_g']),
        'lower_temperature_bin_upper_k':temps[0],'interior_temperature_nodes_k':temps[1:],'upper_temperature_bin_lower_exclusive_k':temps[-1],
        'source_table_id':'2.B.3.'+str(_GROUPS.index(selected['table_group'])+2)+('M' if x.unit_basis=='printed_si' else '')}


def _bracket(nodes,value):
    tolerance=1e-14 if nodes[-1]<=.1 else 1e-10
    value=next((n for n in nodes if abs(n-value)<=tolerance),value)
    ensure(nodes[0]<=value<=nodes[-1],'Outside sulfidic sulfur/TAN/table range; no extrapolation')
    i=bisect_left(nodes,value)
    return (i,i,0.) if value==nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


class SulfidicTableRate(SulfidicAxes):
    sulfur_mass_fraction: Fraction
    tan_mg_koh_g: NonNegative
    maximum_temperature_k: Positive
    lookup_policy: Literal['exact_nodes_only','trilinear','maximum_bracketing_value']
    temperature_edge_policy: Literal['reject_edge_bins_and_first_gap','qualified_source_bins_and_threshold_anchor']
    temperature_edge_qualification_basis: str | None=None
    low_tan_policy: Literal['reject_below_first_tan','qualified_first_tan_row']
    low_tan_qualification_basis: str | None=None


@calculation('damage/sulfidic-table-rate','Sulfidic/naphthenic sulfur TAN temperature base rate',SulfidicTableRate,
    ['Part2 Annex2.B §3.3,Tables3.2-3.10M; PDF pp332-351'],limitations=[
        '3840physical SI/US cells before velocity correction. Low/high temperature bins require qualified applicability and flag;232..260C/450..500F first-gap interpolation additionally uses qualified lower-bin threshold anchor, not invented source point. No interpolation from750F into open-ended>750bin; exact750 is interior last node, immediatelyabove uses upper bin. FirstTAN rows are literal nodes, not<=:below-first requires owner-qualified first-row extension/flag;above-last and sulfur outside table rejected. Concentration/TAN nonmonotonicities retained, including12Cr rate declines: no smoothing. Explicit trilinear/max-corner policy, not validated physical correlation. Naphthenic-influenced values only order-of-magnitude per source. No automatic gas-only acidity suppression or unknown-sulfur default.'])
def table_rate(x):
    axes=table_axes(x)
    data=TABLES[axes['table_group']+'_'+x.unit_basis]
    tq=x.temperature_edge_policy=='qualified_source_bins_and_threshold_anchor'
    ensure((x.temperature_edge_qualification_basis is not None and bool(x.temperature_edge_qualification_basis.strip())) if tq else x.temperature_edge_qualification_basis is None,'Temperature policy and qualification basis must agree')
    lq=x.low_tan_policy=='qualified_first_tan_row'
    ensure((x.low_tan_qualification_basis is not None and bool(x.low_tan_qualification_basis.strip())) if lq else x.low_tan_qualification_basis is None,'Below-first TAN policy and basis must agree')
    s0,s1,ws=_bracket(axes['sulfur_mass_fraction_nodes'],x.sulfur_mass_fraction)
    below=x.tan_mg_koh_g<axes['tan_nodes_mg_koh_g'][0]
    ensure(not below or lq,'TAN below first printed material-specific row')
    a,b,wa=_bracket(axes['tan_nodes_mg_koh_g'],max(x.tan_mg_koh_g,axes['tan_nodes_mg_koh_g'][0]))
    temp=x.maximum_temperature_k
    nodes=[axes['lower_temperature_bin_upper_k']]+axes['interior_temperature_nodes_k']
    bin_used=None; anchor=False
    if temp<=nodes[0]:
        ensure(tq,'Lower source temperature bin requires qualified high-temperature applicability')
        i=j=0; wt=0.; bin_used='lower'
    elif temp>nodes[-1]:
        ensure(tq,'Open-ended upper temperature bin requires qualified applicability')
        i=j=7; wt=0.; bin_used='upper'
    else:
        anchor=temp<nodes[1]
        ensure(not anchor or tq,'First-bin-to-interior gap requires qualified threshold anchor')
        i,j,wt=_bracket(nodes,temp)
    ensure(x.lookup_policy!='exact_nodes_only' or (s0==s1 and a==b and i==j),'Exact sulfidic policy does not interpolate')
    nt=len(axes['tan_nodes_mg_koh_g'])
    def cell(s,t,c): return data['rates'][s*nt+t][c]
    if x.lookup_policy=='maximum_bracketing_value':
        native=max(cell(s,t,c) for s,t,c in product((s0,s1),(a,b),(i,j)))
    else:
        native=sum(fs*ft*fc*cell(s,t,c) for (s,fs),(t,ft),(c,fc) in product(((s0,1-ws),(s1,ws)),((a,1-wa),(b,wa)),((i,1-wt),(j,wt))))
    return {'base_corrosion_rate_m_year':native*(.001 if x.unit_basis=='printed_si' else .0000254),'source_table_id':axes['source_table_id'],
        'table_group':axes['table_group'],'unknown_molybdenum_low_assumed':axes['unknown_molybdenum_low_assumed'],
        'source_temperature_bin_used':bin_used,'first_temperature_threshold_anchor_used':anchor,'below_first_tan_row_used':below}


class SulfidicVelocity(Model):
    velocity_m_s: NonNegative
    boundary_interpretation: Literal['body_strictly_above_100ft_s','figure_at_or_above_100ft_s']
    qualification_basis: str=Field(min_length=1)


@calculation('damage/sulfidic-velocity-factor','Sulfidic/naphthenic high-velocity factor with100ft/s boundary policy',SulfidicVelocity,
    ['Part2 Annex2.B §3.3,Figure3.1; PDF pp332,352'],limitations=[
        'Factor5 above30.48m/s(100ft/s),1below. Body saysstrictly> while figure< test sends equality to5: explicit interpretation/basis determines exact boundary and conflict flag. No continuous velocity interpolation,hydraulic phase-velocity calculation or repeated5x in composition. Maximum nozzle/stream velocity applicability external.'])
def velocity_factor(x):
    ensure(bool(x.qualification_basis.strip()),'Velocity basis and source boundary interpretation qualification required')
    boundary=x.velocity_m_s==30.48
    high=x.velocity_m_s>30.48 or (boundary and x.boundary_interpretation=='figure_at_or_above_100ft_s')
    return {'velocity_factor':5. if high else 1.,'velocity_boundary_conflict_encountered':boundary}


class SulfidicThinningClassification(Model):
    tan_mg_koh_g: NonNegative


@calculation('damage/sulfidic-thinning-classification','Sulfidic/naphthenic TAN general/local source classification',SulfidicThinningClassification,
    ['Part2 Table2.B.1.2; PDF p323'],limitations=[
        'TAN<=0.5mgKOH/g general,>0.5local. Actual liquid-phaseTAN required,not whole-crude average or acid fraction. Classification does not establish mechanism presence or actual pit/inspection distribution; no velocity boundary from another table substituted.'])
def thinning_classification(x):
    return {'source_thinning_type':'general' if x.tan_mg_koh_g<=.5 else 'local'}


class SulfidicService(Model):
    table: SulfidicTableRate
    velocity: SulfidicVelocity
    liquid_phase_present: bool
    hydrogen_free_sulfidation_and_tan_basis_qualified: bool
    qualification_basis: str=Field(min_length=1)


class SulfidicAssessment(Model):
    sulfidic_service_present: bool
    applicability_basis: str=Field(min_length=1)
    service_model: SulfidicService | None=None


@calculation('damage/sulfidic-corrosion-assessment','Qualified high-temperature sulfidic/naphthenic corrosion assessment',SulfidicAssessment,
    ['Part2 Annex2.B §3,Tables3.1-3.10M,Figure3.1,Table1.2; PDF pp323,331-352'],origin='api581_composition_with_explicit_source_policies',limitations=[
        'Same table rate*velocity factor once. Source hydrogen-free sulfidation and actual liquid-phaseTAN/material/process qualification required; highTAN>0.5 gas-only rejected,naphthenic attack needs liquid. Explicit working high-temperature scope>=204C or400F;below rejected,not immunity/zero. Above399C table upper bin retained with qualification,not automatic naphthenic decomposition discount. Source lowTAN first-row/Mo assumptions and edge flags retained. No-service0 specific,not totalDF0. No catalyticH2S/H2 substitution,phase equilibrium,McConomy curve digitization beyond printed tables or model certification.'])
def assessment(x):
    ensure(bool(x.applicability_basis.strip()),'Sulfidic mechanism and service applicability basis required')
    if not x.sulfidic_service_present:
        ensure(x.service_model is None,'No-sulfidic branch cannot carry unused source model')
        return {'corrosion_rate_m_year':0.,'base_corrosion_rate_m_year':None,'source_table_id':None,'table_group':None,'unknown_molybdenum_low_assumed':False,
            'source_temperature_bin_used':None,'first_temperature_threshold_anchor_used':False,'below_first_tan_row_used':False,
            'velocity_factor':None,'velocity_boundary_conflict_encountered':False,'source_thinning_type':None,'calculation_branch':'no_sulfidic_service'}
    ensure(x.service_model is not None,'Sulfidic service requires source model')
    m=x.service_model
    ensure(m.hydrogen_free_sulfidation_and_tan_basis_qualified and bool(m.qualification_basis.strip()),'Qualified hydrogen-free environment,material and actual phaseTAN required')
    onset=204+273.15 if m.table.unit_basis=='printed_si' else (400-32)*5/9+273.15
    ensure(m.table.maximum_temperature_k>=onset,'Below declared high-temperature sulfidic scope; no source-specific zero inferred')
    ensure(m.liquid_phase_present or m.table.tan_mg_koh_g<=.5,'High-TAN naphthenic model needs liquid hydrocarbon phase')
    base=table_rate(m.table); factor=velocity_factor(m.velocity)
    return {**base,**factor,**thinning_classification(SulfidicThinningClassification(tan_mg_koh_g=m.table.tan_mg_koh_g)),
        'corrosion_rate_m_year':base['base_corrosion_rate_m_year']*factor['velocity_factor'],'calculation_branch':'qualified_sulfidic_naphthenic_service'}


class SulfidicThinning(Model):
    corrosion: SulfidicAssessment
    assessment_distribution: Literal['general','local']
    distribution_qualification_basis: str=Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength=Field(discriminator='method')
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str=Field(min_length=1)


@calculation('damage/sulfidic-thinning-assessment','Sulfidic/naphthenic rate through qualified unclad thinning DF',SulfidicThinning,
    ['Part2 Annex2.B §3,Table1.2; §4.5.7,Table4.8'],origin='api581_composition_with_explicit_source_policies',limitations=[
        'Same base*velocity-corrected rate drives wall loss once,dedicated high-temperature sulfidic/naphthenic monitoring row required. Actual distribution/inspection coverage owner-qualified independently of sourceTAN classification. Non-AST unclad only,no additional5x or unrelated H2S/H2 model. No-service0 retains generalDF floor/uncertainty;no all-mechanismDF,code/FFS acceptance or source-condition certification.'])
def thinning_assessment(x):
    ensure(bool(x.distribution_qualification_basis.strip()),'Actual distribution/inspection qualification required')
    corrosion=assessment(x.corrosion)
    ensure(x.conditions.monitoring.row.mechanism=='high_temperature_sulfidic_naphthenic','Sulfidic source requires dedicated monitoring row')
    result=qualified_unclad(QualifiedUnclad(assessment_scope='non_ast_unclad',qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion['corrosion_rate_m_year'],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,'assessment_distribution':x.assessment_distribution}
