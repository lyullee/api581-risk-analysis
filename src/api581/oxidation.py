"""2016 high-temperature oxidation tables, screen and non-AST thinning."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, calculation, ensure
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Material = Literal["carbon_steel","cr_1_25","cr_2_25","cr_5","cr_7","cr_9","cr_12","ss_304","ss_309","ss_310_hk","alloy_800h_hp"]
Units = Literal["printed_si","printed_us_converted"]
_C = (496,524,552,579,607,635,663,691,718,746,774,802,829,857,885,913,941,968,996,1024,1052,1079,1107,1135)
_F = tuple(range(925,2076,50))
_US = (
    (2,4,6,9,14,22,33,48),
    (2,3,4,7,12,18,30,46),
    (1,1,2,4,9,14,24,41),
    (1,1,1,2,4,6,15,35,65),
    (1,1,1,1,1,2,3,6,17,37,60),
    (1,1,1,1,1,1,1,2,5,11,23,40,60),
    (1,1,1,1,1,1,1,1,3,8,15,30,50),
    (1,1,1,1,1,1,1,1,1,2,3,4,6,9,13,18,25,35,48),
    (1,1,1,1,1,1,1,1,1,1,2,3,4,6,8,10,13,16,20,30,40,50),
    (1,1,1,1,1,1,1,1,1,1,1,2,3,4,5,7,8,10,13,15,19,23,27,31),
    (1,1,1,1,1,1,1,1,1,1,1,2,3,4,6,8,10,13,17,21,27,33,41,50))
_SI = (
    (.05,.1,.15,.23,.36,.56,.84,1.22),
    (.05,.08,.1,.18,.3,.46,.76,1.17),
    (.03,.03,.05,.1,.23,.36,.61,1.04),
    (.03,.03,.03,.05,.1,.15,.38,.89,1.65),
    (.03,.03,.03,.03,.03,.05,.08,.15,.43,.94,1.52),
    (.03,.03,.03,.03,.03,.03,.03,.05,.13,.28,.58,1.02,1.52),
    (.03,.03,.03,.03,.03,.03,.03,.03,.08,.2,.38,.76,1.27),
    (.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.23,.33,.46,.64,.89,1.22),
    (.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.2,.25,.33,.41,.51,.76,1.02,1.27),
    (.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.13,.18,.2,.25,.33,.38,.48,.58,.69,.79),
    (.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.2,.25,.33,.43,.53,.69,.84,1.04,1.27))


class OxidationScreen(Model):
    maximum_metal_temperature_k: Positive
    oxygen_present: bool
    threshold_basis: Units


@calculation("damage/oxidation-screen", "High-temperature oxidation temperature and oxygen screening", OxidationScreen,
    ["Part2 Annex2.B Table1.1,§9.1; PDF pp322,389"],limitations=[
        "Annex screen requires metal temperature>=482C(900F) AND oxygen present. Printed SI482C differs from exact900F conversion: basis explicit. Screening out does not assert rate0 or no other damage; description says onset approximately482C forCS and higher for alloys. Maximum METAL temperature controls, including furnace tube metal, not bulk gas/fluid temperature."])
def screen(x):
    threshold = 482+273.15 if x.threshold_basis == "printed_si" else (900-32)*5/9+273.15
    return {"screen_temperature_threshold_k":threshold,"temperature_screen_met":x.maximum_metal_temperature_k >= threshold,
        "evaluate_high_temperature_oxidation":x.maximum_metal_temperature_k >= threshold and x.oxygen_present}


class OxidationTableRow(Model):
    material: Material
    unit_basis: Units


@calculation("damage/oxidation-table-row", "Full oxidation table row with explicit unavailable cells", OxidationTableRow,
    ["Part2 Tables2.B.9.2/9.2M/9.3/9.3M; PDF pp390-391"],limitations=[
        "11 named material rows,24 temperature columns,SI andUS. Combined source material labels310SS/HK and800H/HP preserved as grouped categories, not arbitrary alloy equivalence. Rounded SI temperatures/rates differ from exact US conversions. Printed dashes returnedNone, never0 or material failure-temperature certification. No continuous interpolation in chromium composition."])
def table_row(x):
    i = Material.__args__.index(x.material)
    native = (_SI if x.unit_basis == "printed_si" else _US)[i]
    rates = list(native)+[None]*(24-len(native))
    nodes = [c+273.15 for c in _C] if x.unit_basis == "printed_si" else [(f-32)*5/9+273.15 for f in _F]
    conversion = .001 if x.unit_basis == "printed_si" else .0000254
    return {"temperature_nodes_k":nodes,"corrosion_rates_m_year":[v*conversion if v is not None else None for v in rates],
        "native_rates":rates,"native_rate_unit":"mm/year" if x.unit_basis == "printed_si" else "mpy",
        "source_table_ids":["2.B.9.2M","2.B.9.3M"] if x.unit_basis == "printed_si" else ["2.B.9.2","2.B.9.3"]}


class OxidationRate(OxidationTableRow):
    maximum_metal_temperature_k: Positive
    lookup_policy: Literal["exact_nodes_only","linear_between_nodes","upper_temperature_node"]
    below_table_policy: Literal["reject_below_table","qualified_first_node_value"]
    first_node_qualification_basis: str | None = None


@calculation("damage/oxidation-rate", "Material and maximum-metal-temperature oxidation rate", OxidationRate,
    ["Part2 §9.3,Tables2.B.9.2-9.3M; PDF pp389-391"],limitations=[
        "No source interpolation rule: exact,linear or upper-temperature-node numerical policy must be selected. No high-temperature extrapolation or interpolation touching unavailable dash. Below first printed node496C/925F is rejected or explicitly qualified first-node estimate; source screening begins482C/900F, does not supply this gap's rate. First-node policy not a zero/ambient-corrosion assumption. Adjacent tables are joined only where both bordering cells exist. Primitive lookup does not itself qualify oxygen or actual metal-temperature identification."])
def rate(x):
    qualified = x.below_table_policy == "qualified_first_node_value"
    ensure((x.first_node_qualification_basis is not None and bool(x.first_node_qualification_basis.strip())) if qualified else x.first_node_qualification_basis is None,
        "First-node policy and qualification basis must agree")
    row = table_row(x)
    nodes,values = row["temperature_nodes_k"],row["corrosion_rates_m_year"]
    t = next((n for n in nodes if abs(n-x.maximum_metal_temperature_k) <= 1e-9),x.maximum_metal_temperature_k)
    ensure(t <= nodes[-1],"Temperature exceeds oxidation table; no extrapolation","oxidation_table_range")
    first = t < nodes[0]
    ensure(not first or qualified,"Temperature below first oxidation row; explicit qualified estimate required","oxidation_table_range")
    if first:
        lo = hi = 0
        weight,basis = 0.,"qualified_first_node"
    else:
        hi = bisect_left(nodes,t)
        lo = hi if t == nodes[hi] else hi-1
        weight = 0. if lo == hi else (t-nodes[lo])/(nodes[hi]-nodes[lo])
        ensure(lo == hi or x.lookup_policy != "exact_nodes_only","Exact oxidation-node policy does not interpolate")
        basis = "exact_cell" if lo == hi else "upper_temperature_node" if x.lookup_policy == "upper_temperature_node" else "linear_between_nodes"
    ensure(values[lo] is not None and values[hi] is not None,"Oxidation table cell unavailable; no zero or dash interpolation","oxidation_rate_unavailable")
    value = values[hi] if basis == "upper_temperature_node" else values[lo]+weight*(values[hi]-values[lo])
    return {"corrosion_rate_m_year":value,"lower_temperature_node_k":nodes[lo],"upper_temperature_node_k":nodes[hi],
        "interpolation_weight":weight,"rate_calculation_basis":basis,"first_node_value_used":first}


class OxidationAssessment(Model):
    oxidation: OxidationRate
    oxygen_present: bool
    screening_threshold_basis: Units
    applicability_basis: str = Field(min_length=1)


@calculation("damage/oxidation-assessment", "Screened qualified maximum-metal-temperature oxidation estimate", OxidationAssessment,
    ["Part2 Annex2.B Table1.1,§9,Tables2.B.9.2-9.3M; PDF pp322,389-391"],origin="api581_composition_with_explicit_table_policy",limitations=[
        "Owner qualifies named material, oxygen and actual maximum exposed metal temperature. Screen-out rejects quantitative estimate instead of reporting invented rate0. One assessed surface/exposure; no implicit second-side loss or duplicate atmospheric/CUI corrosion DF. Source calls oxidation general thinning. Does not evaluate creep, thermal fatigue, oxide spallation cycling, carburization/sulfidation, metallurgy, service suitability or total damage."])
def oxidation_assessment(x):
    ensure(bool(x.applicability_basis.strip()),"Oxygen/material/maximum-metal-temperature qualification basis required")
    screened = screen(OxidationScreen(maximum_metal_temperature_k=x.oxidation.maximum_metal_temperature_k,oxygen_present=x.oxygen_present,threshold_basis=x.screening_threshold_basis))
    ensure(screened["evaluate_high_temperature_oxidation"],"Oxidation screening criteria not met; no quantitative zero rate inferred")
    return {**screened,**rate(x.oxidation),"thinning_type":"general"}


class OxidationThinning(Model):
    corrosion: OxidationAssessment
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/oxidation-thinning-assessment", "Oxidation rate through qualified non-AST unclad thinning DF", OxidationThinning,
    ["Part2 Annex2.B §9; Part2 §4.5.7"],origin="api581_composition_with_explicit_table_policy",limitations=[
        "Same qualified oxidation rate drives single constant-baseline unclad non-AST thinning. Strength/allowable stress/flow stress/minimum thickness must be qualified at governing design temperature; no room-temperature strength assumption. Monitoring row must be other, table factor1; qualified experience replacement remains available underTable4.8 note1. Liquid-corrosion rows cannot supply borrowed credits. Inspection eligibility needs owner qualification for oxidation. No AST/cladding, automatic creep/high-temperature code evaluation, FFS or all-mechanism DF."])
def oxidation_thinning(x):
    ensure(x.conditions.monitoring.row.mechanism == "other","Oxidation uses other-mechanism monitoring row; liquid-corrosion credits cannot be borrowed")
    corrosion = oxidation_assessment(x.corrosion)
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result}
