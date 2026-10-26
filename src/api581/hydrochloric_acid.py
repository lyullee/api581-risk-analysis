"""2016 dilute HCl tables, chemistry conversion and qualified thinning composition."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Units = Literal["printed_si", "printed_us_converted"]
Lookup = Literal["exact_nodes_only", "bilinear", "maximum_bracketing_value"]
PHMaterial = Literal["carbon_steel", "ss_304", "ss_316", "ss_321", "ss_347"]
Alloy = Literal["alloy_825", "alloy_20", "alloy_625", "alloy_c276", "alloy_b2", "alloy_400"]
_PH = (.5,.8,1.25,1.75,2.25,2.75,3.25,3.75,4.25,4.75,5.25,5.75,6.25,6.8)
_CONCENTRATION = (.005,.0075,.01)
# ppm intervals are deliberately not made contiguous; the printed integer gaps remain.
_BANDS = ((0.,1.,5.),(1.,2.,4.5),(3.,5.,4.),(6.,15.,3.5),(16.,35.,3.),
          (36.,120.,2.5),(121.,360.,2.),(361.,1200.,1.5),(1201.,3600.,1.),(3601.,12000.,.5))
_CS_US = ((999,999,999,999),(900,999,999,999),(400,999,999,999),(200,700,999,999),
    (100,300,400,560),(60,130,200,280),(40,70,100,140),(30,50,90,125),(20,40,70,100),
    (10,30,50,70),(7,20,30,40),(4,15,20,30),(3,10,15,20),(2,5,7,10))
_CS_SI = ((25.37,25.37,25.37,25.37),(22.86,25.37,25.37,25.37),(10.16,25.37,25.37,25.37),
    (5.08,17.78,25.37,25.37),(2.54,7.62,10.16,14.22),(1.52,3.30,5.08,7.11),(1.02,1.78,2.54,3.56),
    (.76,1.27,2.29,3.18),(.51,1.02,1.78,2.54),(.25,.76,1.27,1.78),(.18,.51,.76,1.02),
    (.10,.38,.51,.76),(.08,.25,.38,.51),(.05,.13,.18,.25))
_SS_US = ((900,999,999,999),(500,999,999,999),(300,500,700,999),(150,260,400,500),
    (80,140,200,250),(50,70,100,120),(30,40,50,65),(20,25,30,35),(10,15,20,25),
    (5,7,10,12),(4,5,6,7),(3,4,5,6),(2,3,4,5),(1,2,3,4))
_SS_SI = ((22.86,25.37,25.37,25.37),(12.70,25.37,25.37,25.37),(7.62,12.70,17.78,25.37),
    (3.81,6.60,10.16,12.70),(2.03,3.56,5.08,6.35),(1.27,1.78,2.54,3.05),(.76,1.02,1.27,1.65),
    (.51,.64,.76,.89),(.25,.38,.51,.64),(.13,.18,.25,.30),(.10,.13,.15,.18),
    (.08,.10,.13,.15),(.05,.08,.10,.13),(.03,.05,.08,.10))
_HIGH_US = {
    "825_20":((1,3,40,200),(2,5,80,400),(10,70,300,999)),
    "625":((1,2,15,75),(1,5,25,125),(2,70,200,400)),
    "c276":((1,2,8,30),(1,2,15,75),(2,10,60,300)),
    "b2_no":((1,1,2,4),(1,1,5,20),(2,5,10,25)),
    "b2_yes":((4,4,8,16),(4,4,20,80),(8,20,40,100)),
    "400_no":((1,3,30,300),(2,5,80,800),(19,25,150,900)),
    "400_yes":((4,12,120,999),(10,20,320,999),(40,100,600,999))}
_HIGH_SI = {
    "825_20":((.03,.08,1.02,5.08),(.05,.13,2.03,10.16),(.25,1.78,7.62,25.37)),
    "625":((.03,.05,.38,1.91),(.03,.13,.64,3.18),(.05,1.78,5.08,10.16)),
    "c276":((.03,.05,.20,.76),(.03,.05,.38,1.91),(.05,.25,1.52,7.62)),
    "b2_no":((.03,.03,.05,.1),(.03,.03,.13,.51),(.05,.13,.25,.64)),
    "b2_yes":((.1,.1,.2,.41),(.1,.1,.51,2.03),(.2,.51,1.02,2.54)),
    "400_no":((.03,.08,.76,7.62),(.05,.13,2.03,20.32),(.48,.64,3.81,22.86)),
    "400_yes":((.1,.3,3.05,25.37),(.25,.51,8.13,25.37),(1.02,2.54,15.24,25.37))}


def _qualified(text, message):
    ensure(bool(text.strip()), message)


class HClPHFromChloride(Model):
    chloride_mass_fraction: Fraction
    no_alkaline_agents_qualified: bool
    qualification_basis: str = Field(min_length=1)


@calculation("damage/hcl-ph-from-chloride", "Dilute HCl pH estimate from printed chloride concentration bands", HClPHFromChloride,
    ["Part2 Table2.B.2.2; PDF p325"], limitations=[
        "Mass fraction converted to wppm. Assumes no ammonia, neutralizing amines or caustic: explicit qualification required. Literal bands contain continuous gaps, e.g.2..3 and35..36ppm; gaps and>12000ppm rejected without rounding or band extension. This is table approximation for separated acid phase, not acid equilibrium, HCl wt% or measured pH."])
def ph_from_chloride(x):
    ensure(x.no_alkaline_agents_qualified,"Source pH estimate requires absence of alkaline agents")
    _qualified(x.qualification_basis,"Chloride/neutralization qualification required")
    ppm = x.chloride_mass_fraction*1e6
    # Snap only floating-point roundoff at a printed endpoint, not analytical uncertainty.
    ppm = next((n for lo,hi,_ in _BANDS for n in (lo,hi) if abs(ppm-n) <= 1e-10),ppm)
    for lo,hi,ph in _BANDS:
        if lo <= ppm and (ppm < hi if ph == 5 else ppm <= hi):
            return {"estimated_ph":ph,"chloride_band_lower_wppm":lo,"chloride_band_upper_wppm":hi,"chloride_band_upper_inclusive":ph != 5}
    ensure(False,"Chloride falls in unassigned source band gap or exceeds table","hcl_chloride_band_unassigned")


class HClChlorideInterval(Model):
    ph: float = Field(ge=.5,le=5,strict=True,allow_inf_nan=False)
    no_alkaline_agents_qualified: bool
    qualification_basis: str = Field(min_length=1)


@calculation("damage/hcl-chloride-interval-from-ph", "Printed chloride interval corresponding to a tabulated HCl pH", HClChlorideInterval,
    ["Part2 Table2.B.2.2,Figure2.B.2.1; PDF pp325,330"], limitations=[
        "Inverse table is an interval, not unique concentration. Only printed pH values0.5,1,...5 allowed; no log-law, midpoint or invented interpolation. Requires no alkaline agents. High-alloy use must explicitly select/qualify concentration inside interval and rate-table range; lower-pH/high-chloride assumptions cannot be inferred from unrelated aqueous chemistry."])
def chloride_interval(x):
    ensure(x.no_alkaline_agents_qualified,"Source inverse estimate requires absence of alkaline agents")
    _qualified(x.qualification_basis,"Inverse chemistry qualification required")
    for lo,hi,ph in _BANDS:
        if x.ph == ph:
            return {"chloride_band_lower_wppm":lo,"chloride_band_upper_wppm":hi,"chloride_band_upper_inclusive":ph != 5}
    ensure(False,"No inverse chloride band for this pH","hcl_ph_inverse_unassigned")


def _bracket(nodes,value):
    value = next((n for n in nodes if abs(n-value) <= 1e-10),value)
    ensure(nodes[0] <= value <= nodes[-1],"Outside printed HCl rate table; extrapolation disabled")
    i = bisect_left(nodes,value)
    return (i,i,0.) if value == nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


def _lookup(table,us_table,nodes,value,temp,units,policy):
    temperatures = tuple(c+273.15 for c in (38,52,79,93)) if units == "printed_si" else tuple((f-32)*5/9+273.15 for f in (100,125,175,200))
    a,b,w = _bracket(nodes,value)
    c,d,v = _bracket(temperatures,temp)
    ensure(policy != "exact_nodes_only" or (a == b and c == d),"Exact-node policy does not interpolate")
    corners = [table[i][j] for i in (a,b) for j in (c,d)]
    native = max(corners) if policy == "maximum_bracketing_value" else (1-w)*((1-v)*table[a][c]+v*table[a][d])+w*((1-v)*table[b][c]+v*table[b][d])
    return {"corrosion_rate_m_year":native*(.001 if units == "printed_si" else .0000254),
        "source_999_corner_used":any(us_table[i][j] == 999 for i in (a,b) for j in (c,d))}


class HClPHRate(Model):
    material: PHMaterial
    ph: float = Field(ge=.5,le=6.8,strict=True,allow_inf_nan=False)
    maximum_temperature_k: Positive
    unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/hcl-ph-rate", "HCl carbon-steel and 304/316/321/347 pH-temperature rate tables", HClPHRate,
    ["Part2 Tables2.B.2.3/2.3M,2.4/2.4M; PDF pp326-327"], limitations=[
        "14pH x4temperature x2materials x2unit tables,224physical cells. Named four stainless grades share source table; other300 grades/low-alloy not inferred. Stainless values already10x general for localized pitting: do not multiply10 again or divide to claim qualified general rate. Printed999mpy/25.37mm/y retained literally and flagged for any contributing cell; not infinity, missing or immunity. Explicit interpolation policy only; no extrapolation. Unit tables preserve rounding. SCC/crevice corrosion not calculated."])
def ph_rate(x):
    cs = x.material == "carbon_steel"
    us = _CS_US if cs else _SS_US
    table = (_CS_SI if cs else _SS_SI) if x.unit_basis == "printed_si" else us
    return {**_lookup(table,us,_PH,x.ph,x.maximum_temperature_k,x.unit_basis,x.lookup_policy),
        "localized_pitting_already_included":not cs,"source_table_id":"2.B.2."+("3" if cs else "4")+("M" if x.unit_basis == "printed_si" else "")}


class HClAlloyRate(Model):
    material: Alloy
    chloride_mass_fraction: Fraction
    maximum_temperature_k: Positive
    oxidants_present: bool | None = None
    unit_basis: Units
    lookup_policy: Lookup


@calculation("damage/hcl-alloy-rate", "HCl high-alloy chloride-temperature and oxidant rate tables", HClAlloyRate,
    ["Part2 Tables2.B.2.5/2.5M,2.6/2.6M; PDF pp328-329"], limitations=[
        "Chloride-ion mass fraction .005/.0075/.01 (0.5/0.75/1wt%), not HCl acid fraction.825/20 share table;625/C276 distinct. B2/400 require explicit oxidant state; supplied oxidant field on other table rejected as unused. All168physical SI/US high-alloy cells preserved, including400 no-oxidant1wt%,100F=19mpy. No universal4x oxidant multiplier. Source999 literal/rounding retained and flagged. No extrapolation or oxidant interpolation; heat-treatment, salt deposits and actual process qualification external."])
def alloy_rate(x):
    affected = x.material in ("alloy_b2","alloy_400")
    ensure((x.oxidants_present is not None) if affected else x.oxidants_present is None,"B2/400 require oxidant state; other table cannot use oxidant input")
    key = "825_20" if x.material in ("alloy_825","alloy_20") else x.material.removeprefix("alloy_")
    if affected:
        key += "_yes" if x.oxidants_present else "_no"
    us = _HIGH_US[key]
    table = _HIGH_SI[key] if x.unit_basis == "printed_si" else us
    return {**_lookup(table,us,_CONCENTRATION,x.chloride_mass_fraction,x.maximum_temperature_k,x.unit_basis,x.lookup_policy),
        "localized_pitting_already_included":False,"source_table_id":"2.B.2."+("6" if affected else "5")+("M" if x.unit_basis == "printed_si" else "")}


class MeasuredHClPH(Model):
    method: Literal["supplied_ph"]
    ph: float = Field(ge=.5,le=6.8,strict=True,allow_inf_nan=False)
    qualification_basis: str = Field(min_length=1)


class EstimatedHClPH(HClPHFromChloride):
    method: Literal["chloride_table"]


class SuppliedHClChloride(Model):
    method: Literal["supplied_chloride"]
    chloride_mass_fraction: Fraction
    qualification_basis: str = Field(min_length=1)


class SelectedHClChloride(HClChlorideInterval):
    method: Literal["ph_interval_selection"]
    chloride_mass_fraction: Fraction
    selection_qualification_basis: str = Field(min_length=1)


class HClPHWet(Model):
    model_family: Literal["ph_table"]
    material: PHMaterial
    acidity: MeasuredHClPH | EstimatedHClPH = Field(discriminator="method")
    maximum_temperature_k: Positive
    unit_basis: Units
    lookup_policy: Lookup
    qualification_basis: str = Field(min_length=1)


class HClAlloyWet(Model):
    model_family: Literal["alloy_table"]
    material: Alloy
    chloride: SuppliedHClChloride | SelectedHClChloride = Field(discriminator="method")
    maximum_temperature_k: Positive
    oxidants_present: bool | None = None
    material_heat_treatment_qualified: bool
    unit_basis: Units
    lookup_policy: Lookup
    qualification_basis: str = Field(min_length=1)


class HClAssessment(Model):
    free_water_present: bool
    dilute_hcl_service_qualified: bool
    applicability_basis: str = Field(min_length=1)
    wet_model: HClPHWet | HClAlloyWet | None = Field(default=None,discriminator="model_family")


@calculation("damage/hcl-assessment", "Qualified dilute HCl chemistry material and corrosion-rate assessment", HClAssessment,
    ["Part2 Annex2.B §2,Tables2.1-2.6M,Figure2.1; Table1.2; PDF pp323-330"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Only qualified dilute free-water HCl service and listed materials. Supplied separated acid-phase pH preferred; chloride-derived pH gated on no alkaline agents. Inverse pH route returns band and requires explicitly selected qualified chloride inside it; no unique inverse inferred. Maximum local temperature and material/heat-treatment applicability qualified externally. Source class local, stainless pitting already included. Dry0 HCl-specific, diagnosticsNone; not total damage. No shock-condensation/salt deposition dynamics, SCC or concentrated acid extrapolation."])
def assessment(x):
    _qualified(x.applicability_basis,"Dilute acid phase/applicability qualification required")
    if not x.free_water_present:
        ensure(x.wet_model is None,"Dry HCl branch cannot carry unused wet model")
        return {"corrosion_rate_m_year":0.,"source_999_corner_used":False,"localized_pitting_already_included":False,
            "source_table_id":None,"ph_used":None,"chloride_mass_fraction_used":None,"chemistry_method":None,
            "source_thinning_type":None,"calculation_branch":"no_free_water"}
    ensure(x.dilute_hcl_service_qualified and x.wet_model is not None,"Wet model requires qualified dilute HCl service")
    m = x.wet_model
    _qualified(m.qualification_basis,"Maximum local temperature and material applicability required")
    ph = None
    chloride = None
    if m.model_family == "ph_table":
        c = m.acidity
        if c.method == "supplied_ph":
            _qualified(c.qualification_basis,"Separated acid-phase pH qualification required")
            ph = c.ph
        else:
            ph = ph_from_chloride(c)["estimated_ph"]
            chloride = c.chloride_mass_fraction
        result = ph_rate(HClPHRate(material=m.material,ph=ph,maximum_temperature_k=m.maximum_temperature_k,unit_basis=m.unit_basis,lookup_policy=m.lookup_policy))
    else:
        ensure(m.material_heat_treatment_qualified,"High-alloy material/heat-treatment qualification required")
        c = m.chloride
        chloride = c.chloride_mass_fraction
        if c.method == "supplied_chloride":
            _qualified(c.qualification_basis,"Separated acid-phase chloride qualification required")
        else:
            chloride_interval(c)
            _qualified(c.selection_qualification_basis,"Inverse chloride selection requires explicit engineering basis")
            # Reuse the forward classifier, including exact endpoint tolerance.
            selected = ph_from_chloride(HClPHFromChloride(chloride_mass_fraction=chloride,
                no_alkaline_agents_qualified=c.no_alkaline_agents_qualified,qualification_basis=c.qualification_basis))
            ensure(selected["estimated_ph"] == c.ph,"Selected chloride is outside inverse pH interval")
            ph = c.ph
        result = alloy_rate(HClAlloyRate(material=m.material,chloride_mass_fraction=chloride,
            maximum_temperature_k=m.maximum_temperature_k,oxidants_present=m.oxidants_present,unit_basis=m.unit_basis,lookup_policy=m.lookup_policy))
    return {**result,"ph_used":ph,"chloride_mass_fraction_used":chloride,"chemistry_method":c.method,
        "source_thinning_type":"local","calculation_branch":"wet_dilute_hcl_model"}


class HClThinning(Model):
    corrosion: HClAssessment
    assessment_distribution: Literal["general","local"]
    distribution_qualification_basis: str = Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/hcl-thinning-assessment", "Dilute HCl rate through qualified non-AST unclad thinning DF", HClThinning,
    ["Part2 Annex2.B §2,Table1.2; §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same HCl rate drives wall loss with HCl monitoring row and explicit inspection/distribution qualification. Source local class retained apart from owner assessment distribution. Stainless pitting factor already in table, never added again. Dry0 not DF0; general thinning uncertainty/floor still applies. Non-AST unclad only; no crack/crevice/SCC/FFS or automatic all-mechanism risk."])
def thinning_assessment(x):
    _qualified(x.distribution_qualification_basis,"Actual distribution and inspection qualification required")
    corrosion = assessment(x.corrosion)
    ensure(x.conditions.monitoring.row.mechanism == "hydrochloric_acid","HCl model requires HCl monitoring row")
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}
