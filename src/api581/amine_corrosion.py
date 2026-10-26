"""2016 Annex2.B section8 amine tables, chemistry policies and thinning."""
from bisect import bisect_left
from itertools import product
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure, finite_tree
from ._amine_tables import TABLES
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Amine = Literal["mea","dea","mdea"]
Units = Literal["printed_si","printed_us_converted"]
Lookup = Literal["exact_nodes_only","linear_loading_temperature","maximum_bracketing_value"]
_RICH = (.15,.25,.35,.45,.55,.65,.7)


def _qualified(value,message):
    ensure(bool(value.strip()),message)


def _bracket(nodes,value):
    value=next((n for n in nodes if abs(n-value)<=1e-10),value)
    ensure(nodes[0]<=value<=nodes[-1],"Outside amine table; no extrapolation")
    i=bisect_left(nodes,value)
    return (i,i,0.) if value==nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


class AmineAcidGasLoading(Model):
    h2s_amount_mol: NonNegative
    co2_amount_mol: NonNegative
    active_amine_amount_mol: Positive
    common_sample_basis: str = Field(min_length=1)


@calculation("damage/amine-acid-gas-loading", "Combined H2S and CO2 loading per mole of active amine", AmineAcidGasLoading,
    ["Part2 Annex2.B §8.1,Table8.1; PDF pp382-383"],limitations=[
        "Both acid gases on same representative sample basis divided by active, not total or degraded amine. No HSAS-to-active-amine subtraction, equilibrium or rich/lean process-state inference. Zero acid-gas loading valid; denominator strictly positive. Owner process analysis/qualification required."])
def acid_gas_loading(x):
    _qualified(x.common_sample_basis,"Common sample and active-amine analytical basis required")
    result=(x.h2s_amount_mol+x.co2_amount_mol)/x.active_amine_amount_mol
    finite_tree(result)
    return {"acid_gas_loading_mol_mol":result}


class AmineLoadingSelection(Model):
    acid_gas_loading_mol_mol: NonNegative
    loading_gap_policy: Literal["reject_unassigned_0p10_to_0p15","qualified_lean_row","qualified_first_rich_row"]
    loading_gap_qualification_basis: str | None = None


@calculation("damage/amine-loading-selection", "Amine lean/rich source loading rows and explicit gap selection", AmineLoadingSelection,
    ["Part2 Tables2.B.8.2-8.3M; PDF pp384-387"],limitations=[
        "Carbon tables have lean<0.1 and rich nodes0.15..0.7.0.1<=loading<0.15 is unassigned, default rejected; owner-qualified nearest lean/first-rich mapping flagged, never interpolation across incompatible velocity thresholds. Rich nodes may be numerically bracketed; rate lookup separately selects interpolation. Loading>0.7 rejected. Returned row indices0lean,1..7rich are table coordinates, not process rich/lean designation."])
def loading_selection(x):
    q=x.loading_gap_policy!="reject_unassigned_0p10_to_0p15"
    ensure((x.loading_gap_qualification_basis is not None and bool(x.loading_gap_qualification_basis.strip())) if q else x.loading_gap_qualification_basis is None,
        "Loading gap policy and qualification basis must agree")
    value=x.acid_gas_loading_mol_mol
    gap=.1<=value<.15
    if value<.1:
        a=b=0; w=0.
    elif gap:
        ensure(q,"Carbon amine loading0.10..0.15 lacks printed row","amine_loading_gap")
        a=b=0 if x.loading_gap_policy=="qualified_lean_row" else 1; w=0.
    else:
        a,b,w=_bracket(_RICH,value)
        a+=1; b+=1
    return {"lower_loading_row_index":a,"upper_loading_row_index":b,"loading_interpolation_weight":w,
        "table_loading_regime":"lean" if a==0 else "rich","loading_gap_mapping_used":gap}


class AmineContaminantSelection(Model):
    amine_type: Amine
    contaminant_mass_fraction: Fraction
    mdea_scale_policy: Literal["not_mdea","qualified_basic_data_organic_ppm_bands","qualified_printed_wt_percent_nodes"]
    mdea_scale_qualification_basis: str | None = None
    four_percent_boundary_policy: Literal["basic_data_middle_band","printed_four_percent_high_row"] | None = None
    four_percent_qualification_basis: str | None = None


@calculation("damage/amine-contaminant-row", "Select amine HSAS or MDEA organic-acid contamination row", AmineContaminantSelection,
    ["Part2 Table2.B.8.1,Tables8.2-8.3M; PDF pp383-387"],limitations=[
        "MEA/DEA basic-data<=2wt%,2..4,>4 maplow/middle/high table rows2/3/4. Exact4 conflicts with printed high-row4: explicit middle/high policy/basis required. MDEA basic-data organic-acid<500,500..4000,>4000wppm differs from tableHSAS0.5/2.25/4wt%; explicit qualified basic-data band mapping or literal exactwt%node policy required. Never treat500ppm as0.5wt%. No hidden HSAS composition or active-amine correction. No interpolation between contaminant categories."])
def contaminant_row(x):
    c=x.contaminant_mass_fraction
    if x.amine_type=="mdea":
        ensure(x.mdea_scale_policy!="not_mdea" and x.mdea_scale_qualification_basis is not None and bool(x.mdea_scale_qualification_basis.strip()),"MDEA source scale conflict needs explicit policy and basis")
        ensure(x.four_percent_boundary_policy is None and x.four_percent_qualification_basis is None,"MEA/DEA boundary fields do not apply to MDEA")
        if x.mdea_scale_policy=="qualified_basic_data_organic_ppm_bands":
            ppm=c*1e6
            row="low" if ppm<500 else "middle" if ppm<=4000 else "high"
        else:
            index=next((i for i,n in enumerate((.005,.0225,.04)) if abs(c-n)<=1e-12),None)
            ensure(index is not None,"Printed MDEA wt% policy accepts only literal0.5/2.25/4wt% nodes")
            row=("low","middle","high")[index]
    else:
        ensure(x.mdea_scale_policy=="not_mdea" and x.mdea_scale_qualification_basis is None,"MDEA fields unused for MEA/DEA")
        if c==.04:
            ensure(x.four_percent_boundary_policy is not None and x.four_percent_qualification_basis is not None and bool(x.four_percent_qualification_basis.strip()),"Exact4wt% HSAS requires source boundary policy and basis")
            row="middle" if x.four_percent_boundary_policy=="basic_data_middle_band" else "high"
        else:
            ensure(x.four_percent_boundary_policy is None and x.four_percent_qualification_basis is None,"Four-percent boundary policy applies only at4wt%")
            row="low" if c<=.02 else "middle" if c<.04 else "high"
    return {"contaminant_row":row,"printed_hsas_row_mass_fraction":((.005,.0225,.04) if x.amine_type=="mdea" else (.02,.03,.04))[("low","middle","high").index(row)]}


class AmineStrength(Model):
    amine_type: Amine
    amine_mass_fraction: Fraction


@calculation("damage/amine-strength-factor", "Carbon-steel amine concentration multiplier", AmineStrength,
    ["Part2 Table2.B.8.4; PDF p388"],limitations=[
        "MEA<=20wt%:1,21..25:1.5,>25:2;DEA<=30:1,31..40:1.2,>40:1.5;MDEA<=50:1 only. Continuous20..21 and30..31 gaps rejected, no rounding/interpolation. MDEA>50 not supplied. Positive active process solution concentration required. Carbon-table factor, not extra stainless multiplier or concentration derating credit."])
def strength_factor(x):
    c=x.amine_mass_fraction
    ensure(c>0,"Amine concentration must be positive")
    if x.amine_type=="mea":
        ensure(c<=.2 or c>=.21,"MEA20..21wt% multiplier gap")
        f=1. if c<=.2 else 1.5 if c<=.25 else 2.
    elif x.amine_type=="dea":
        ensure(c<=.3 or c>=.31,"DEA30..31wt% multiplier gap")
        f=1. if c<=.3 else 1.2 if c<=.4 else 1.5
    else:
        ensure(c<=.5,"No MDEA strength factor above50wt%")
        f=1.
    return {"amine_strength_factor":f}


class AmineCarbonBaseRate(Model):
    table_family: Literal["mea_dea","mdea"]
    loading: AmineLoadingSelection
    contaminant_row: Literal["low","middle","high"]
    maximum_temperature_k: Positive
    velocity_m_s: NonNegative
    unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/amine-carbon-base-rate", "Carbon-steel amine loading temperature contamination velocity tables", AmineCarbonBaseRate,
    ["Part2 Tables2.B.8.2-8.3M; PDF pp384-387"],limitations=[
        "1152physical source cells:2families x2units x8loading rows x3contamination rows x6temperatures x2velocity. Base rates before strength factor. Lean velocity low<=6.1m/s or20ft/s,rich<=1.5m/s or5ft/s; equality low, no velocity interpolation. Rich loading/temperature interpolation explicit, not across lean gap. Contaminant row is source table coordinate; process classification independent API. Unit differences preserved, temperature outside table rejected. No local evaporation/metal-temperature prediction, film transient or automatic amineSCC."])
def carbon_base_rate(x):
    selected=loading_selection(x.loading)
    lean=selected["table_loading_regime"]=="lean"
    threshold=(6.1 if lean else 1.5) if x.unit_basis=="printed_si" else (20 if lean else 5)*.3048
    high=x.velocity_m_s>threshold
    temps=tuple(t+273.15 for t in (88,93,104,116,127,132)) if x.unit_basis=="printed_si" else tuple((t-32)*5/9+273.15 for t in (190,200,220,240,260,270))
    a,b,v=_bracket(temps,x.maximum_temperature_k)
    i,j,w=selected["lower_loading_row_index"],selected["upper_loading_row_index"],selected["loading_interpolation_weight"]
    ensure(x.lookup_policy!="exact_nodes_only" or (a==b and i==j),"Exact amine table policy does not interpolate")
    data=TABLES[x.table_family+("_si" if x.unit_basis=="printed_si" else "_us")]
    row=("low","middle","high").index(x.contaminant_row)
    def cell(l,t):
        return data[3*l+row][2*t+int(high)]
    native=max(cell(l,t) for l,t in product((i,j),(a,b))) if x.lookup_policy=="maximum_bracketing_value" else (1-w)*((1-v)*cell(i,a)+v*cell(i,b))+w*((1-v)*cell(j,a)+v*cell(j,b))
    return {**selected,"base_corrosion_rate_m_year":native*(.001 if x.unit_basis=="printed_si" else .0000254),
        "velocity_band":"high" if high else "low","velocity_threshold_m_s":threshold,
        "source_table_id":"2.B.8."+("2" if x.table_family=="mea_dea" else "3")+("M" if x.unit_basis=="printed_si" else "")}


class AmineStainlessRate(Model):
    acid_gas_loading_mol_mol: NonNegative
    maximum_temperature_k: Positive
    unit_basis: Units
    lookup_policy: Lookup
    low_loading_policy: Literal["reject_below_0p1","qualified_first_row"]
    low_loading_qualification_basis: str | None = None
    normal_service_conditions_qualified: bool
    qualification_basis: str = Field(min_length=1)


@calculation("damage/amine-stainless-rate", "Type300 stainless amine loading corrosion table", AmineStainlessRate,
    ["Part2 Table2.B.8.5,§8.3,Figure8.1; PDF pp382,388-389"],limitations=[
        "8loading x2unit cells,temperature<=149C or300F explicitly selected. Below0.1loading not printed: reject or qualified first-row screening value flagged, not guaranteed bound. No loading>0.7 or high-temperature extrapolation. Normal service qualification required: source says extreme concentration/temperature/degradation can cause up to200x, not fixed multiplier or guaranteed upper bound. No carbon strength factor on stainless and no inferred HSAS/velocity modifier. Source figure Type300 scope; not all chromium/nickel/copper alloys."])
def stainless_rate(x):
    _qualified(x.qualification_basis,"Stainless material and normal service qualification required")
    ensure(x.normal_service_conditions_qualified,"Extreme stainless conditions require separate qualified corrosion assessment; no automatic200x factor")
    q=x.low_loading_policy=="qualified_first_row"
    ensure((x.low_loading_qualification_basis is not None and bool(x.low_loading_qualification_basis.strip())) if q else x.low_loading_qualification_basis is None,"Stainless low-loading policy and basis must agree")
    threshold=149+273.15 if x.unit_basis=="printed_si" else (300-32)*5/9+273.15
    ensure(x.maximum_temperature_k<=threshold,"Above stainless amine table temperature limit")
    below=x.acid_gas_loading_mol_mol<.1
    ensure(not below or q,"Stainless loading below first printed0.1 node")
    data=TABLES["stainless"]
    a,b,w=_bracket(tuple(r[0] for r in data),max(x.acid_gas_loading_mol_mol,.1))
    ensure(x.lookup_policy!="exact_nodes_only" or a==b,"Exact stainless table policy does not interpolate")
    col=1 if x.unit_basis=="printed_si" else 2
    native=max(data[a][col],data[b][col]) if x.lookup_policy=="maximum_bracketing_value" else (1-w)*data[a][col]+w*data[b][col]
    return {"corrosion_rate_m_year":native*(.001 if x.unit_basis=="printed_si" else .0000254),"low_loading_first_row_used":below,"source_table_id":"2.B.8.5"}


class AmineCarbonService(Model):
    method: Literal["carbon_table"]
    material: Literal["carbon_steel","low_alloy_steel"]
    low_alloy_qualification_basis: str | None = None
    solution: AmineStrength
    contaminants: AmineContaminantSelection
    loading: AmineLoadingSelection
    maximum_temperature_k: Positive
    velocity_m_s: NonNegative
    unit_basis: Units
    lookup_policy: Lookup
    classification_qualification_basis: str = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)


class AmineStainlessService(AmineStainlessRate):
    method: Literal["type300_stainless_table"]
    amine_type: Amine


class AmineAssessment(Model):
    amine_service_present: bool
    applicability_basis: str = Field(min_length=1)
    rate_model: AmineCarbonService | AmineStainlessService | None = Field(default=None,discriminator="method")


@calculation("damage/amine-corrosion-assessment", "Qualified amine chemistry and material corrosion assessment", AmineAssessment,
    ["Part2 Annex2.B §8,Tables8.1-8.5,Figure8.1,Table1.2; PDF pp323,382-389"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "MEA/DEA/MDEA chemical gas-treating amines only; no physical solvent/DIPA extension. Same amine in strength/contaminants required. CS table and qualified figurelow-alloy branch use base*strength once;Type300 stainless uses normal-service table without carbon multiplier. CS classification explicitly qualified to rate-table velocity columns: overviewstrict boundaries/body6.01vs6.1/1.52vs1.5 differ; equality follows rate-table low, not unqualified universal limit. Stainless source type not inferred without velocity:None. No-service0 specific, not totalDF0. Maximum local metal temperature/amine concentration, active loading and contaminant applicability external; no amineSCC."])
def assessment(x):
    _qualified(x.applicability_basis,"Amine service and process applicability qualification required")
    if not x.amine_service_present:
        ensure(x.rate_model is None,"No-amine branch cannot carry unused rate model")
        return {"corrosion_rate_m_year":0.,"base_corrosion_rate_m_year":None,"amine_strength_factor":None,"contaminant_row":None,
            "printed_hsas_row_mass_fraction":None,"table_loading_regime":None,"loading_gap_mapping_used":False,"velocity_band":None,
            "velocity_threshold_m_s":None,"low_loading_first_row_used":False,"source_table_id":None,"source_thinning_type":None,"calculation_branch":"no_amine_service"}
    ensure(x.rate_model is not None,"Exposed amine service requires qualified rate model")
    m=x.rate_model
    _qualified(m.qualification_basis,"Maximum local conditions and material qualification required")
    if m.method=="carbon_table":
        low=m.material=="low_alloy_steel"
        ensure((m.low_alloy_qualification_basis is not None and bool(m.low_alloy_qualification_basis.strip())) if low else m.low_alloy_qualification_basis is None,"Figure low-alloy/table carbon-steel difference needs qualified material basis")
        ensure(m.solution.amine_type==m.contaminants.amine_type,"Solution and contaminant amine types must match")
        _qualified(m.classification_qualification_basis,"Explicit rate-table velocity classification and inspection basis required")
        contaminant=contaminant_row(m.contaminants)
        base=carbon_base_rate(AmineCarbonBaseRate(table_family="mdea" if m.solution.amine_type=="mdea" else "mea_dea",loading=m.loading,
            contaminant_row=contaminant["contaminant_row"],maximum_temperature_k=m.maximum_temperature_k,velocity_m_s=m.velocity_m_s,unit_basis=m.unit_basis,lookup_policy=m.lookup_policy))
        factor=strength_factor(m.solution)["amine_strength_factor"]
        return {"corrosion_rate_m_year":base["base_corrosion_rate_m_year"]*factor,"base_corrosion_rate_m_year":base["base_corrosion_rate_m_year"],
            "amine_strength_factor":factor,**contaminant,"table_loading_regime":base["table_loading_regime"],"loading_gap_mapping_used":base["loading_gap_mapping_used"],
            "velocity_band":base["velocity_band"],"velocity_threshold_m_s":base["velocity_threshold_m_s"],"low_loading_first_row_used":False,
            "source_table_id":base["source_table_id"],"source_thinning_type":"general" if base["velocity_band"]=="low" else "local","calculation_branch":"carbon_amine_model"}
    result=stainless_rate(m)
    return {**result,"base_corrosion_rate_m_year":result["corrosion_rate_m_year"],"amine_strength_factor":None,"contaminant_row":None,
        "printed_hsas_row_mass_fraction":None,"table_loading_regime":None,"loading_gap_mapping_used":False,"velocity_band":None,
        "velocity_threshold_m_s":None,"source_thinning_type":None,"calculation_branch":"type300_stainless_model"}


class AmineThinning(Model):
    corrosion: AmineAssessment
    assessment_distribution: Literal["general","local"]
    distribution_qualification_basis: str = Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/amine-thinning-assessment", "Amine rate through qualified non-AST unclad thinning DF", AmineThinning,
    ["Part2 Annex2.B §8,Table1.2; §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same final base*strength rate drives wall loss; amine monitoring row must match table velocity band when carbon model supplies one. Monitoring regime basis and actual inspection distribution qualified explicitly. Stainless has no rate-table velocity classification; owner monitoring regime remains separately qualified. No-amine0 does not bypass generalDF floor/uncertainty. Non-AST unclad only; no amineSCC, process equilibrium, code/FFS or all-mechanism risk inference."])
def thinning_assessment(x):
    _qualified(x.distribution_qualification_basis,"Actual general/local distribution and inspection qualification required")
    corrosion=assessment(x.corrosion)
    monitor=x.conditions.monitoring.row
    ensure(monitor.mechanism=="amine","Amine corrosion requires amine monitoring row")
    if corrosion["velocity_band"] is not None:
        ensure(monitor.amine_velocity_regime==corrosion["velocity_band"],"Monitoring and corrosion must use same qualified amine velocity band")
    result=qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}
