"""2016 HF tables with explicit concentration, residual and source-conflict policies."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Units = Literal["printed_si", "printed_us_converted"]
Lookup = Literal["exact_nodes_only", "bilinear", "maximum_bracketing_value"]
_C = (.01,.02,.05,.06,.63,.64,.80,.81)
# Paired low/high velocity rows; last two columns are81wt% low/high residual.
_CS_US = (
    (2,150,150,800,800,5,5,2,6),(20,999,999,999,999,50,50,20,60),
    (10,500,500,999,999,30,30,5,15),(200,999,999,999,999,300,300,50,150),
    (10,500,500,999,999,30,30,10,30),(100,999,999,999,999,300,300,100,300),
    (100,999,999,999,999,500,500,20,60),(999,999,999,999,999,999,999,200,600),
    (100,999,999,999,999,500,500,50,150),(999,999,999,999,999,999,999,500,999),
    (100,999,999,999,999,500,500,70,210),(999,999,999,999,999,999,999,700,999),
    (500,999,999,999,999,999,999,100,300),(999,999,999,999,999,999,999,999,999))
_CS_SI = (
    (.05,3.81,3.81,20.32,20.32,.13,.13,.05,.15),(.51,25.37,25.37,25.37,25.37,1.27,1.27,.51,1.52),
    (.25,12.7,12.7,25.37,25.37,.76,.76,.13,.38),(5.08,25.37,25.37,25.37,25.37,7.62,7.62,1.27,3.81),
    (.25,12.7,12.7,25.37,25.37,.76,.76,.25,.76),(2.54,25.37,25.37,25.37,25.37,7.62,7.62,2.54,7.62),
    (2.54,25.37,25.37,25.37,25.37,12.7,12.7,.51,1.52),(25.37,25.37,25.37,25.37,25.37,25.37,25.37,5.08,15.24),
    (2.54,25.37,25.37,25.37,25.37,12.7,12.7,1.27,3.81),(25.37,25.37,25.37,25.37,25.37,25.37,25.37,12.7,25.37),
    (2.54,25.37,25.37,25.37,25.37,12.7,12.7,1.78,5.33),(25.37,25.37,25.37,25.37,25.37,25.37,25.37,17.78,25.37),
    (12.7,25.37,25.37,25.37,25.37,25.37,25.37,2.54,7.62),(25.37,25.37,25.37,25.37,25.37,25.37,25.37,25.37,25.37))
# Paired no/yes aeration rows.
_A400_US = ((1,1,1,10,10,1,1,2),(10,10,10,25,25,10,10,15),
    (1,1,1,15,15,5,5,3),(10,10,10,30,30,20,20,15),
    (5,5,5,20,20,10,10,5),(20,20,20,100,100,50,50,20),
    (10,10,10,20,20,20,20,10),(100,100,100,200,200,200,200,100))
_A400_SI = ((.03,.03,.03,.25,.25,.03,.03,.05),(.25,.25,.25,.64,.64,.25,.25,.38),
    (.03,.03,.03,.38,.38,.13,.13,.08),(.25,.25,.25,.76,.76,.51,.51,.38),
    (.13,.13,.13,.51,.51,.25,.25,.13),(.51,.51,.51,2.54,2.54,1.27,1.27,.51),
    (.25,.25,.25,.51,.51,.51,.51,.25),(2.54,2.54,2.54,5.08,5.08,5.08,5.08,2.54))


def _qualified(value,message):
    ensure(bool(value.strip()),message)


class HFConcentration(Model):
    hf_mass_fraction: Fraction
    concentrated_extension_policy: Literal["reject_above_81wt_percent", "qualified_81wt_percent_node"]
    concentrated_extension_qualification_basis: str | None = None


@calculation("damage/hf-concentration-selection", "HF table concentration with explicit above81wt% extension policy", HFConcentration,
    ["Part2 Annex2.B §6.1,Tables6.2-6.3M; PDF pp374,376-377"],limitations=[
        "HF-in-water mass fraction, not water mass fraction. Source body says>=80wt% equivalent to anhydrous but tables distinguish80/81wt% and stop81. Values>81 default reject; qualified81-node extension requires owner basis and flag, never silent extrapolation or81>= label. Below1wt% rejected.80..81 handled by explicit table interpolation policy. No-free-water is not HF immunity: anhydrous acid remains in scope."])
def concentration_selection(x):
    qualified = x.concentrated_extension_policy == "qualified_81wt_percent_node"
    ensure((x.concentrated_extension_qualification_basis is not None and bool(x.concentrated_extension_qualification_basis.strip())) if qualified else x.concentrated_extension_qualification_basis is None,
        "Concentrated HF extension policy and qualification basis must agree")
    ensure(x.hf_mass_fraction >= .01,"HF concentration below first1wt% table node")
    extended = x.hf_mass_fraction > .81
    ensure(not extended or qualified,"Above81wt% HF requires qualified source-body/table extension","hf_concentrated_extension_required")
    return {"hf_mass_fraction_for_lookup":min(x.hf_mass_fraction,.81),"concentrated_81_node_extension_used":extended}


class HFVelocity(Model):
    velocity_m_s: NonNegative
    velocity_basis: Units


@calculation("damage/hf-carbon-velocity-band", "HF carbon-steel low/high velocity band", HFVelocity,
    ["Part2 Tables2.B.6.2/6.2M; PDF p376"],limitations=[
        "PrintedSI threshold3.05m/s versus10ft/s=3.048m/s explicitly selected. Low strictly below; equality high. No continuous velocity interpolation or generic erosion/film-stripping rate. This rate-table threshold differs from other mechanisms and is not a universal process limit."])
def velocity_band(x):
    threshold = 3.05 if x.velocity_basis == "printed_si" else 10*.3048
    return {"velocity_band": "low" if x.velocity_m_s < threshold else "high","velocity_threshold_m_s":threshold}


def _bracket(nodes,value):
    value = next((n for n in nodes if abs(n-value) <= 1e-10),value)
    ensure(nodes[0] <= value <= nodes[-1],"Outside printed HF table; no extrapolation")
    i = bisect_left(nodes,value)
    return (i,i,0.) if nodes[i] == value else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


def _lookup(table,us,temps,c,temp,branch,units,policy,residual_high=False):
    a,b,w = _bracket(_C,c)
    i,j,v = _bracket(temps,temp)
    ensure(policy != "exact_nodes_only" or (a == b and i == j),"Exact-node HF policy does not interpolate")
    def column(k):
        return 8 if residual_high and k == 7 else k
    corners = [table[2*t+branch][column(k)] for t in (i,j) for k in (a,b)]
    if policy == "maximum_bracketing_value":
        native = max(corners)
    else:
        lower = (1-w)*table[2*i+branch][column(a)]+w*table[2*i+branch][column(b)]
        upper = (1-w)*table[2*j+branch][column(a)]+w*table[2*j+branch][column(b)]
        native = (1-v)*lower+v*upper
    return {"corrosion_rate_m_year":native*(.001 if units == "printed_si" else .0000254),
        "source_999_corner_used":any(us[2*t+branch][column(k)] == 999 for t in (i,j) for k in (a,b))}


class HFCarbonRate(HFConcentration,HFVelocity):
    maximum_temperature_k: Positive
    residual_category: Literal["low", "high"] | None = None
    residual_qualification_basis: str | None = None
    unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/hf-carbon-rate", "HF carbon-steel concentration temperature velocity residual rate table", HFCarbonRate,
    ["Part2 Tables2.B.6.2/6.2M; PDF p376"],limitations=[
        "252SI/US cells at7temperatures x2velocity x9columns. Concentrations1,2,5,6,63,64,80,81wt%;81haslow/high residual. Any lookup using81corner needs qualified residual classification; source supplies no numeric Cu/Ni/Cr cutoff, none inferred. Residual fields outside81-corner region rejected as unused. All999mpy/25.37mm/y literal with flag. Source SI/US rounding explicit, no temperature extrapolation. Initial high corrosion before protective fluoride scale, galvanic coupling and disturbed scale not quantified by table. Figure6.1 swapped table numbers resolved by actual table titles, not treated as official erratum."])
def carbon_rate(x):
    concentration = concentration_selection(x)
    c = concentration["hf_mass_fraction_for_lookup"]
    a,b,_ = _bracket(_C,c)
    residual_used = b == 7
    ensure((x.residual_category is not None and x.residual_qualification_basis is not None and bool(x.residual_qualification_basis.strip())) if residual_used else x.residual_category is None and x.residual_qualification_basis is None,
        "Qualified residual category needed only when lookup touches81wt% column")
    velocity = velocity_band(x)
    temps = tuple(t+273.15 for t in (27,41,60,66,75,86,93)) if x.unit_basis == "printed_si" else tuple((t-32)*5/9+273.15 for t in (80,105,140,150,167.5,187.5,200))
    table = _CS_SI if x.unit_basis == "printed_si" else _CS_US
    return {**concentration,**velocity,**_lookup(table,_CS_US,temps,c,x.maximum_temperature_k,int(velocity["velocity_band"] == "high"),x.unit_basis,x.lookup_policy,x.residual_category == "high"),
        "residual_column_used":x.residual_category if residual_used else None,"source_table_id":"2.B.6.2"+("M" if x.unit_basis == "printed_si" else "")}


class HFAlloy400Rate(HFConcentration):
    maximum_temperature_k: Positive
    aerated_or_oxidants_present: bool
    unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/hf-alloy400-rate", "HF Alloy400 concentration temperature aeration rate table", HFAlloy400Rate,
    ["Part2 Tables2.B.6.3/6.3M,Table6.1; PDF pp375,377"],limitations=[
        "128SI/US cells at4temperatures x2aeration x8HF concentrations. Explicit aeration/oxidants bool, no dissolved-oxygen cutoff supplied or inferred. No blanket aeration multiplier or velocity correction. Actual material and applicable solution conditions external. No extrapolation except flagged qualified above81 extension. Figure6.1 swapped table references resolved using actual Alloy400 table title."])
def alloy400_rate(x):
    concentration = concentration_selection(x)
    temps = tuple(t+273.15 for t in (27,52,79,93)) if x.unit_basis == "printed_si" else tuple((t-32)*5/9+273.15 for t in (80,125,175,200))
    table = _A400_SI if x.unit_basis == "printed_si" else _A400_US
    return {**concentration,**_lookup(table,_A400_US,temps,concentration["hf_mass_fraction_for_lookup"],x.maximum_temperature_k,
        int(x.aerated_or_oxidants_present),x.unit_basis,x.lookup_policy),"source_table_id":"2.B.6.3"+("M" if x.unit_basis == "printed_si" else "")}


class HFCarbonService(HFCarbonRate):
    method: Literal["carbon_steel_table"]
    established_scale_and_stable_operation_qualified: bool
    material_residual_content_qualified: bool
    qualification_basis: str = Field(min_length=1)


class HFAlloy400Service(HFAlloy400Rate):
    method: Literal["alloy400_table"]
    material_and_aeration_qualified: bool
    qualification_basis: str = Field(min_length=1)


class HFPublishedRate(Model):
    method: Literal["qualified_published_rate"]
    material_description: str = Field(min_length=1)
    hf_mass_fraction: Fraction
    maximum_temperature_k: Positive
    velocity_m_s: NonNegative
    corrosion_rate_m_year: NonNegative
    published_source_reference: str = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)


class HFAssessment(Model):
    hf_exposure_present: bool
    applicability_basis: str = Field(min_length=1)
    rate_model: HFCarbonService | HFAlloy400Service | HFPublishedRate | None = Field(default=None,discriminator="method")
    galvanic_coupling_present: bool | None = None
    thinning_classification_policy: Literal["overview_local", "detailed_general_without_galvanic"] | None = None
    classification_qualification_basis: str | None = None


@calculation("damage/hf-assessment", "Qualified HF exposure material and source-classification corrosion assessment", HFAssessment,
    ["Part2 Annex2.B §6,Tables6.1-6.3M,Figure6.1,Table1.2; PDF pp323,374-378"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "HF exposure, not free-water presence controls branch: no free water cannot imply zero because anhydrous HF corrodes. No-HF0 source-specific only. CS table requires stable established fluoride scale/material-residual qualification; table paths reject galvanic coupling whose acceleration is unquantified. Other materials/conditions may use explicit published rate with provenance and applicability qualification per source figure, not an API581 table prediction. Source overviewLocal versus detailedGeneral absent galvanic conflict requires explicit policy/basis; general policy disallowed with galvanic coupling. No HSC/HIC/blistering, SCC, film growth or transient dilution model."])
def assessment(x):
    _qualified(x.applicability_basis,"HF exposure and service applicability qualification required")
    if not x.hf_exposure_present:
        ensure(x.rate_model is None and x.galvanic_coupling_present is None and x.thinning_classification_policy is None and x.classification_qualification_basis is None,
            "No-HF branch cannot carry unused service model or classification")
        return {"corrosion_rate_m_year":0.,"source_table_id":None,"rate_source":None,"source_999_corner_used":False,
            "hf_mass_fraction_for_lookup":None,"concentrated_81_node_extension_used":False,"velocity_band":None,
            "velocity_threshold_m_s":None,"residual_column_used":None,"source_thinning_type":None,"calculation_branch":"no_hf_exposure"}
    ensure(x.rate_model is not None and x.galvanic_coupling_present is not None and x.thinning_classification_policy is not None,
        "HF service requires model, galvanic review and explicit source classification")
    ensure(x.classification_qualification_basis is not None and bool(x.classification_qualification_basis.strip()),"Source classification conflict requires qualified policy basis")
    general = x.thinning_classification_policy == "detailed_general_without_galvanic"
    ensure(not general or not x.galvanic_coupling_present,"Detailed general-thinning branch excludes potential galvanic attack")
    m = x.rate_model
    _qualified(m.qualification_basis,"Material/conditions and source applicability qualification required")
    if m.method == "carbon_steel_table":
        ensure(m.established_scale_and_stable_operation_qualified and m.material_residual_content_qualified,
            "Carbon table requires qualified established scale, stable service and residual metallurgy")
        ensure(not x.galvanic_coupling_present,"HF table does not quantify galvanic acceleration")
        result = carbon_rate(m)
    elif m.method == "alloy400_table":
        ensure(m.material_and_aeration_qualified,"Alloy400 material and aeration qualification required")
        ensure(not x.galvanic_coupling_present,"HF table does not quantify galvanic acceleration")
        result = {**alloy400_rate(m),"velocity_band":None,"velocity_threshold_m_s":None,"residual_column_used":None}
    else:
        _qualified(m.published_source_reference,"Published HF rate reference required")
        _qualified(m.material_description,"Published rate material identification required")
        ensure(m.hf_mass_fraction > 0,"Exposed HF service cannot use zero HF concentration")
        result = {"corrosion_rate_m_year":m.corrosion_rate_m_year,"source_table_id":None,"source_999_corner_used":False,
            "hf_mass_fraction_for_lookup":None,"concentrated_81_node_extension_used":False,"velocity_band":None,
            "velocity_threshold_m_s":None,"residual_column_used":None}
    return {**result,"rate_source":m.method,"source_thinning_type":"general" if general else "local","calculation_branch":"qualified_hf_service"}


class HFThinning(Model):
    corrosion: HFAssessment
    assessment_distribution: Literal["general","local"]
    distribution_qualification_basis: str = Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/hf-thinning-assessment", "Qualified HF rate through non-AST unclad thinning DF", HFThinning,
    ["Part2 Annex2.B §6,Table1.2; §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same selected HF rate drives wall loss and qualified HF monitoring row. Source class conflict policy and owner-qualified actual distribution retained separately. No-HF0 not DF0, uncertainty/floor remain. Non-AST unclad only; no added residual/aeration multipliers, no automatic cracking/totalDF/FFS acceptance. Published rate retains supplied provenance in input snapshot, not relabeled API581 table data."])
def thinning_assessment(x):
    _qualified(x.distribution_qualification_basis,"Actual general/local inspection distribution qualification required")
    corrosion = assessment(x.corrosion)
    ensure(x.conditions.monitoring.row.mechanism == "hydrofluoric_acid","HF calculation requires hydrofluoric-acid monitoring row")
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}
