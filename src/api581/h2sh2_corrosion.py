"""2016 high-temperature H2S/H2 corrosion source tables and thinning."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from ._h2sh2_tables import TABLES
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Material=Literal['carbon_steel','cr1_0p2mo','cr1_0p5mo','cr1p25_0p5mo','cr2p25_1mo','cr3_1mo',
    'cr5_0p5mo','cr7','cr9_1mo','cr12','ss_304','ss_304l','ss_316','ss_316l','ss_321','ss_347']
Units=Literal['printed_si','printed_us_converted']
_CONCENTRATIONS=tuple(c/100 for c in (.002,.0035,.008,.035,.08,.30,.75,1.))


def _group(material):
    if material.startswith('ss_'): return 'stainless'
    return {'cr5_0p5mo':'cr5','cr7':'cr7','cr9_1mo':'cr9','cr12':'cr12'}.get(material,'carbon_low_alloy')


class H2SH2Axes(Model):
    material: Material
    unit_basis: Units


@calculation('damage/h2sh2-table-axes','High-temperature H2S/H2 material and table axes',H2SH2Axes,
    ['Part2 Tables2.B.4.2-4.7M; PDF pp354-362'],limitations=[
        'Six source material groups,16named materials. Public vapor H2S mole fraction, not molepercent/massfraction/partial pressure.0.002mole%=0.00002fraction=20ppmv. SI218..524C and US425..975F nodes retain source rounding. Stream type required onlyCS/lowCr groups, excluded for12Cr and named stainless. Axes not process qualification; no unlisted alloy interpolation.'])
def table_axes(x):
    group=_group(x.material)
    temps=tuple(t+273.15 for t in (218,246,274,302,329,357,385,413,441,468,496,524)) if x.unit_basis=='printed_si' else tuple((t-32)*5/9+273.15 for t in (425,475,525,575,625,675,725,775,825,875,925,975))
    return {'h2s_mole_fraction_nodes':list(_CONCENTRATIONS),'temperature_nodes_k':list(temps),'table_group':group,
        'hydrocarbon_curve_required':group not in ('cr12','stainless'),'source_table_id':'2.B.4.'+str(('carbon_low_alloy','cr5','cr7','cr9','cr12','stainless').index(group)+2)+('M' if x.unit_basis=='printed_si' else '')}


def _bracket(nodes,value):
    # Fraction endpoints need a tighter tolerance than temperature coordinates.
    tolerance=1e-14 if nodes[-1]<=1 else 1e-10
    value=next((n for n in nodes if abs(n-value)<=tolerance),value)
    ensure(nodes[0]<=value<=nodes[-1],'Outside high-temperature H2S/H2 table; no extrapolation')
    i=bisect_left(nodes,value)
    return (i,i,0.) if value==nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


class H2SH2Rate(H2SH2Axes):
    h2s_mole_fraction: Fraction
    maximum_temperature_k: Positive
    stream_case: Literal['naphtha','gas_oil','hydrocarbon_free'] | None=None
    hydrocarbon_free_curve: Literal['naphtha','gas_oil'] | None=None
    hydrocarbon_free_qualification_basis: str | None=None
    lookup_policy: Literal['exact_nodes_only','bilinear','maximum_bracketing_value']


@calculation('damage/h2sh2-table-rate','High-temperature H2S/H2 concentration-temperature corrosion rate',H2SH2Rate,
    ['Part2 Annex2.B §4.1-4.3,Tables4.2-4.7M,Figure4.1; PDF pp353-363'],limitations=[
        '1920physical SI/US cells. Naphtha/gas-oil curves categorical, no fluid blending. Typical boiling430F distinction requires process classification, not automatic maximum-temperature comparison. Hydrocarbon-free source says same correlations adequate despite possible50% greater rates: explicit qualified choice of source curve, no added1.5multiplier.12Cr/stainless tables have no hydrocarbon branch:unused stream fields rejected. Positive H2S below20ppmv or above1mole% and temperatures outside printed table rejected, never zero/cap. Approx204C onset is not first table218C: gap not extrapolated. Bilinear uses linear concentration, not inferred log correlation; explicit numerical policy. No HTHA,wetH2S cracking,catalyst chemistry or automatic material certification.'])
def table_rate(x):
    axes=table_axes(x)
    branch=axes['hydrocarbon_curve_required']
    if not branch:
        ensure(x.stream_case is None and x.hydrocarbon_free_curve is None and x.hydrocarbon_free_qualification_basis is None,'12Cr/stainless table cannot use stream curve inputs')
        curve=None
    elif x.stream_case=='hydrocarbon_free':
        ensure(x.hydrocarbon_free_curve is not None and x.hydrocarbon_free_qualification_basis is not None and bool(x.hydrocarbon_free_qualification_basis.strip()),'Hydrocarbon-free service needs qualified source curve selection')
        curve=x.hydrocarbon_free_curve
    else:
        ensure(x.stream_case in ('naphtha','gas_oil') and x.hydrocarbon_free_curve is None and x.hydrocarbon_free_qualification_basis is None,'LowCr source table needs only applicable naphtha/gas-oil curve')
        curve=x.stream_case
    a,b,w=_bracket(axes['h2s_mole_fraction_nodes'],x.h2s_mole_fraction)
    i,j,v=_bracket(axes['temperature_nodes_k'],x.maximum_temperature_k)
    ensure(x.lookup_policy!='exact_nodes_only' or (a==b and i==j),'Exact H2S/H2 policy does not interpolate')
    data=TABLES[axes['table_group']+'_'+x.unit_basis]
    def cell(c,t): return data[2*c+int(curve=='gas_oil') if branch else c][t]
    native=max(cell(c,t) for c in (a,b) for t in (i,j)) if x.lookup_policy=='maximum_bracketing_value' else (1-w)*((1-v)*cell(a,i)+v*cell(a,j))+w*((1-v)*cell(b,i)+v*cell(b,j))
    return {'corrosion_rate_m_year':native*(.001 if x.unit_basis=='printed_si' else .0000254),'source_table_id':axes['source_table_id'],
        'selected_hydrocarbon_curve':curve,'hydrocarbon_free_curve_selection_used':x.stream_case=='hydrocarbon_free','source_thinning_type':'general'}


class H2SH2Service(H2SH2Rate):
    hydrogen_sulfidation_environment_qualified: bool
    material_and_stream_qualification_basis: str=Field(min_length=1)


class H2SH2Assessment(Model):
    h2s_h2_service_present: bool
    applicability_basis: str=Field(min_length=1)
    service_model: H2SH2Service | None=None


@calculation('damage/h2sh2-corrosion-assessment','Qualified high-temperature H2S/H2 corrosion assessment',H2SH2Assessment,
    ['Part2 Annex2.B §4,Table1.2; PDF pp323,353-363'],origin='api581_composition_with_explicit_source_policies',limitations=[
        'Requires actual high-temperature hydrogen-sulfidation environment and material/stream qualification; sulfur and hydrogen alone do not establish catalytic conversion. Same source rate applies with no extra50% vapor correction. No-service0 is mechanism-specific with absent diagnostics, not all-mechanismDF0 or temperature-based immunity. Actual maximum process temperature and vapor composition external; low-temperature gap,traceH2S or unlisted material not filled by unrelated wet-sour/oxidation model. General source thinning does not validate inspection distribution.'])
def assessment(x):
    ensure(bool(x.applicability_basis.strip()),'Environment and service applicability basis required')
    if not x.h2s_h2_service_present:
        ensure(x.service_model is None,'No-H2S/H2 branch cannot carry unused source model')
        return {'corrosion_rate_m_year':0.,'source_table_id':None,'selected_hydrocarbon_curve':None,'hydrocarbon_free_curve_selection_used':False,
            'source_thinning_type':None,'calculation_branch':'no_h2s_h2_service'}
    ensure(x.service_model is not None,'Exposed high-temperature H2S/H2 service requires model')
    m=x.service_model
    ensure(m.hydrogen_sulfidation_environment_qualified and bool(m.material_and_stream_qualification_basis.strip()),'Qualified hydrogen-sulfidation environment/material/stream required')
    return {**table_rate(m),'calculation_branch':'qualified_high_temperature_h2s_h2'}


class H2SH2Thinning(Model):
    corrosion: H2SH2Assessment
    assessment_distribution: Literal['general','local']
    distribution_qualification_basis: str=Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength=Field(discriminator='method')
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str=Field(min_length=1)


@calculation('damage/h2sh2-thinning-assessment','High-temperature H2S/H2 rate through qualified unclad thinning DF',H2SH2Thinning,
    ['Part2 Annex2.B §4,Table1.2; §4.5.7,Table4.8'],origin='api581_composition_with_explicit_source_policies',limitations=[
        'Same computed rate drives wall loss and dedicated high-temperatureH2S/H2 monitoring row, not amine/wet-sour row. Actual distribution/inspection coverage separately qualified. No-service0 retains generalDF floor/uncertainty. Non-AST unclad only; no wetH2S/HTHA or other mechanism aggregation,code/FFS acceptance or added vapor multiplier.'])
def thinning_assessment(x):
    ensure(bool(x.distribution_qualification_basis.strip()),'Actual distribution and inspection qualification required')
    corrosion=assessment(x.corrosion)
    ensure(x.conditions.monitoring.row.mechanism=='high_temperature_h2s_h2','H2S/H2 source requires dedicated high-temperature monitoring row')
    result=qualified_unclad(QualifiedUnclad(assessment_scope='non_ast_unclad',qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion['corrosion_rate_m_year'],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,'assessment_distribution':x.assessment_distribution}
