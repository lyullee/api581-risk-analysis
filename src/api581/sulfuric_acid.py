"""2016 sulfuric source tables, explicit header/cell conflicts and thinning."""
from bisect import bisect_left
from itertools import product
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from ._sulfuric_tables import TABLES
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Material=Literal["carbon_steel","ss_304","ss_316","alloy_20","alloy_c276","alloy_b2"]
Group=Literal["carbon_steel","stainless_steel","higher_alloy"]
Units=Literal["printed_si","printed_us_converted"]


def _qualified(value,message):
    ensure(bool(value.strip()),message)


def _group(material):
    return "carbon_steel" if material=="carbon_steel" else "stainless_steel" if material.startswith("ss_") else "higher_alloy"


class SulfuricAxes(Model):
    material: Material
    unit_basis: Units
    carbon_si_velocity_policy: Literal["reject_ambiguous_header","qualified_printed_m_s","qualified_us_ft_s_header"]="reject_ambiguous_header"
    carbon_si_velocity_qualification_basis: str | None=None


@calculation("damage/sulfuric-table-axes", "Sulfuric material table concentration temperature and velocity axes", SulfuricAxes,
    ["Part2 Tables2.B.5.2-5.7M; PDF pp365-372"],limitations=[
        "Six named materials only. CS SI header saysm/s but repeats US numericft/s headings0,1,2,3,4.5,6.5,8.5,11.5,12: default reject, qualified literalSI or US-header interpretation explicit. SI/US temperature axes retained literally, includingAlloy20 SI70C versus US163.5F. No automatic temperature/unit repair, extrapolation or cross-material substitution. Axes alone do not establish table applicability."])
def table_axes(x):
    ambiguous=x.material=="carbon_steel" and x.unit_basis=="printed_si"
    if ambiguous:
        ensure(x.carbon_si_velocity_policy!="reject_ambiguous_header" and x.carbon_si_velocity_qualification_basis is not None and bool(x.carbon_si_velocity_qualification_basis.strip()),
            "Carbon-steel SI velocity header requires explicit qualified interpretation","sulfuric_si_velocity_header")
    else:
        ensure(x.carbon_si_velocity_policy=="reject_ambiguous_header" and x.carbon_si_velocity_qualification_basis is None,"Carbon SI header policy unused for this table")
    data=TABLES[x.material+"_"+x.unit_basis]
    velocity=list(data["velocities_m_s"])
    if ambiguous and x.carbon_si_velocity_policy=="qualified_us_ft_s_header":
        velocity=[v*.3048 for v in velocity]
    return {"acid_mass_fraction_nodes":sorted(data["concentrations"]),"temperature_nodes_k":list(data["temperatures_k"]),
        "velocity_nodes_m_s":velocity,"source_table_id":"2.B.5."+str(("carbon_steel","ss_304","ss_316","alloy_20","alloy_c276","alloy_b2").index(x.material)+2)+("M" if x.unit_basis=="printed_si" else ""),
        "carbon_si_velocity_interpretation":x.carbon_si_velocity_policy if ambiguous else "not_applicable"}


def _bracket(nodes,value):
    value=next((n for n in nodes if abs(n-value)<=1e-10),value)
    ensure(nodes[0]<=value<=nodes[-1],"Outside sulfuric table; extrapolation not permitted")
    i=bisect_left(nodes,value)
    return (i,i,0.) if value==nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


class SulfuricRate(SulfuricAxes):
    acid_mass_fraction: Fraction
    maximum_temperature_k: Positive
    velocity_m_s: NonNegative
    lookup_policy: Literal["exact_nodes_only","trilinear","maximum_bracketing_value"]
    oxidants_present: bool | None=None
    disputed_304_cell_policy: Literal["reject_disputed_cell","qualified_printed_literal"]="reject_disputed_cell"
    disputed_304_qualification_basis: str | None=None


@calculation("damage/sulfuric-table-rate", "Sulfuric concentration temperature velocity material corrosion table", SulfuricRate,
    ["Part2 Annex2.B §5,Tables5.2-5.7M,Figure5.1; PDF pp363-373"],limitations=[
        "1776physical SI/US cells. Rates are source maximum estimates, not certified universal bounds. CS turbulent localized enhancement already included, no added3x multiplier or automatic20..50% actual-rate discount. Literal999mpy/25.37mm/y flagged, not infinity/missing.30475wt%,middleT,highestv prints99mpy/2.51mm/y amid999: default reject exact cell/any bracketing corner; qualified printed literal requires basis and flag, no invented999 correction. B2 requires explicit no-oxidant state; oxidizingB2 rejected to source specialist route. Other tables reject unused oxidant input, no oxidant improvement credit. Trilinear/max-corner are explicit numerical policies, not original interpolation instruction; nonmonotonic concentration cannot be replaced by global monotonic rule."])
def table_rate(x):
    axes=table_axes(x)
    if x.material=="alloy_b2":
        ensure(x.oxidants_present is not None and not x.oxidants_present,"Oxidizing/unknown B2 sulfuric service requires specialist estimate","sulfuric_b2_oxidizing")
    else:
        ensure(x.oxidants_present is None,"Oxidant input only used for B2 table")
    q=x.disputed_304_cell_policy=="qualified_printed_literal"
    ensure((x.disputed_304_qualification_basis is not None and bool(x.disputed_304_qualification_basis.strip()) and x.material=="ss_304") if q else x.disputed_304_qualification_basis is None,
        "304 disputed cell policy and material/qualification basis must agree")
    data=TABLES[x.material+"_"+x.unit_basis]
    a,b,w=_bracket(axes["acid_mass_fraction_nodes"],x.acid_mass_fraction)
    i,j,v=_bracket(axes["temperature_nodes_k"],x.maximum_temperature_k)
    l,m,u=_bracket(axes["velocity_nodes_m_s"],x.velocity_m_s)
    ensure(x.lookup_policy!="exact_nodes_only" or (a==b and i==j and l==m),"Exact sulfuric policy does not interpolate")
    corners=list(product((a,b),(i,j),(l,m)))
    def rate(c,t,s):
        return data["rates"][len(data["concentrations"])-1-c][t][s]
    disputed=x.material=="ss_304" and any(axes["acid_mass_fraction_nodes"][c]==.75 and t==1 and s==2 for c,t,s in corners)
    ensure(not disputed or q,"Sulfuric304 lookup touches disputed99mpy/2.51mm/y cell","sulfuric_disputed_304_cell")
    if x.lookup_policy=="maximum_bracketing_value":
        native=max(rate(*p) for p in corners)
    else:
        native=sum(wc*wt*wv*rate(c,t,s) for (c,wc),(t,wt),(s,wv) in product(((a,1-w),(b,w)),((i,1-v),(j,v)),((l,1-u),(m,u))))
    return {"corrosion_rate_m_year":native*(.001 if x.unit_basis=="printed_si" else .0000254),"source_table_id":axes["source_table_id"],
        "carbon_si_velocity_interpretation":axes["carbon_si_velocity_interpretation"],"source_999_corner_used":any(rate(*p)==(25.37 if x.unit_basis=="printed_si" else 999) for p in corners),
        "disputed_304_cell_used":disputed,"source_localized_enhancement_already_included":x.material=="carbon_steel" and m>3}


class SulfuricThinningClassification(Model):
    material_group: Group
    velocity_m_s: NonNegative
    threshold_basis: Literal["overview_printed_si","overview_us_converted","detailed_carbon_body_si"]
    equality_policy: Literal["reject_ambiguous_boundary","qualified_general","qualified_local"]
    equality_qualification_basis: str | None=None


@calculation("damage/sulfuric-thinning-classification", "Sulfuric source general/local thinning velocity classification", SulfuricThinningClassification,
    ["Part2 Table2.B.1.2,Annex2.B §5.1; PDF pp323,363"],limitations=[
        "Overview SI thresholdsCS.61/SS1.22/higher1.83m/s versus2/4/6ft/s; detailed CS bodyapprox.91m/s. Explicit basis preserves differences. Overview CS/SS equality overlaps; general equality resolution requires qualified policy, never guessed. Distinct from online-monitoring Table4.8 thresholds3/5/7ft/s and table velocity nodes; do not force all classifications equal. Actual distribution and inspection coverage external."])
def thinning_classification(x):
    q=x.equality_policy!="reject_ambiguous_boundary"
    ensure((x.equality_qualification_basis is not None and bool(x.equality_qualification_basis.strip())) if q else x.equality_qualification_basis is None,"Equality policy and basis must agree")
    if x.threshold_basis=="detailed_carbon_body_si":
        ensure(x.material_group=="carbon_steel","Detailed carbon-body threshold only applies to carbon steel")
        threshold=.91
    else:
        index=("carbon_steel","stainless_steel","higher_alloy").index(x.material_group)
        threshold=(.61,1.22,1.83)[index] if x.threshold_basis=="overview_printed_si" else (2,4,6)[index]*.3048
    equal=x.velocity_m_s==threshold
    if equal:
        ensure(q,"Sulfuric exact velocity boundary needs qualified general/local resolution","sulfuric_thinning_boundary")
        kind="general" if x.equality_policy=="qualified_general" else "local"
    else:
        kind="general" if x.velocity_m_s<threshold else "local"
    return {"source_thinning_type":kind,"thinning_velocity_threshold_m_s":threshold,"thinning_velocity_boundary_resolved":equal}


class SulfuricTableService(Model):
    method: Literal["source_table"]
    table: SulfuricRate
    table_conditions_and_passivity_qualified: bool
    qualification_basis: str = Field(min_length=1)


class SulfuricSpecialistRate(Model):
    method: Literal["qualified_specialist_rate"]
    material_description: str = Field(min_length=1)
    material_group: Group
    acid_mass_fraction: Fraction
    maximum_temperature_k: Positive
    velocity_m_s: NonNegative
    oxidants_present: bool
    corrosion_rate_m_year: NonNegative
    source_reference: str = Field(min_length=1)
    qualification_basis: str = Field(min_length=1)


class SulfuricAssessment(Model):
    sulfuric_service_present: bool
    applicability_basis: str = Field(min_length=1)
    rate_model: SulfuricTableService | SulfuricSpecialistRate | None=Field(default=None,discriminator="method")
    classification: SulfuricThinningClassification | None=None


@calculation("damage/sulfuric-corrosion-assessment", "Qualified sulfuric material rate and thinning classification assessment", SulfuricAssessment,
    ["Part2 Annex2.B §5,Tables5.1-5.7M,Figure5.1,Table1.2; PDF pp323,363-373"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same velocity/material group must drive supplied classification and selected rate. Table conditions including concentration,maximum local/nozzle conditions,passivity and impurity applicability owner-qualified. No-service0 is sulfuric-specific, not based on free-water absence;100wt% sulfuric table remains valid. OxidizingB2 uses explicit qualified specialist rate/provenance, not fictitious oxidant multiplier or source table prediction. Specialist route may cover other qualified material/conditions. Source maximum estimates retained without extra3x or automatic actual-rate discount. General/local thresholds and online-monitoring thresholds intentionally distinct; no all-mechanismDF/FFS or corrosion equilibrium inferred."])
def assessment(x):
    _qualified(x.applicability_basis,"Sulfuric service and concentration applicability qualification required")
    if not x.sulfuric_service_present:
        ensure(x.rate_model is None and x.classification is None,"No-sulfuric branch cannot carry unused rate/classification")
        return {"corrosion_rate_m_year":0.,"source_table_id":None,"carbon_si_velocity_interpretation":"not_applicable","source_999_corner_used":False,
            "disputed_304_cell_used":False,"source_localized_enhancement_already_included":False,"source_thinning_type":None,"thinning_velocity_threshold_m_s":None,
            "thinning_velocity_boundary_resolved":False,"rate_source":None,"calculation_branch":"no_sulfuric_service"}
    ensure(x.rate_model is not None and x.classification is not None,"Sulfuric service requires rate model and classification")
    m=x.rate_model
    _qualified(m.qualification_basis,"Actual material/conditions and selected rate qualification required")
    if m.method=="source_table":
        ensure(m.table_conditions_and_passivity_qualified,"Source table conditions/passivity must be qualified")
        velocity=m.table.velocity_m_s; group=_group(m.table.material)
        result=table_rate(m.table)
    else:
        _qualified(m.material_description,"Specialist material identification required")
        _qualified(m.source_reference,"Specialist rate source reference required")
        ensure(m.acid_mass_fraction>0,"Exposed sulfuric service requires positive acid concentration")
        velocity=m.velocity_m_s; group=m.material_group
        result={"corrosion_rate_m_year":m.corrosion_rate_m_year,"source_table_id":None,"carbon_si_velocity_interpretation":"not_applicable",
            "source_999_corner_used":False,"disputed_304_cell_used":False,"source_localized_enhancement_already_included":False}
    ensure(x.classification.velocity_m_s==velocity and x.classification.material_group==group,"Rate and thinning classification must use same velocity/material group")
    return {**result,**thinning_classification(x.classification),"rate_source":"source_maximum_estimate" if m.method=="source_table" else "qualified_specialist_estimate","calculation_branch":"qualified_sulfuric_service"}


class SulfuricThinning(Model):
    corrosion: SulfuricAssessment
    assessment_distribution: Literal["general","local"]
    distribution_qualification_basis: str = Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength=Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/sulfuric-thinning-assessment", "Qualified sulfuric corrosion through non-AST unclad thinning DF", SulfuricThinning,
    ["Part2 Annex2.B §5,Table1.2; §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same final rate drives wall loss; same physical velocity/material group must be used for sulfuric monitoring and source classification, but their threshold values differ. Source general/local and actual owner-qualified inspection distribution retained separately. No extra localized3x multiplication or rate discount. No-service0 not DF0; uncertainty/floor retained. Non-AST unclad only, no source condition certification,all-mechanismDF or code/FFS acceptance."])
def thinning_assessment(x):
    _qualified(x.distribution_qualification_basis,"Actual inspection coverage and general/local distribution qualification required")
    corrosion=assessment(x.corrosion)
    row=x.conditions.monitoring.row
    ensure(row.mechanism=="sulfuric_acid","Sulfuric corrosion requires sulfuric monitoring row")
    if x.corrosion.classification is not None:
        ensure(row.velocity_m_s==x.corrosion.classification.velocity_m_s and row.sulfuric_material_group==x.corrosion.classification.material_group,
            "Monitoring and corrosion must use same physical velocity/material group")
    result=qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}
