"""Level1 HF/H2S and miscellaneous toxic tables, explicit units and mitigation."""
from bisect import bisect_left
import math
from typing import Annotated, Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure
from .consequences import ToxicSource, toxic_source, ToxicDuration, toxic_duration, ToxicArea, toxic_area

Finite = Annotated[float,Field(strict=True,allow_inf_nan=False)]
LB_PER_KG = 2.205
M2_PER_FT2 = .0929
HF_H2S_TIMES = (300,600,1200,2400,3600)
HF_H2S = {
    "hf":((1.1401,3.5683),(1.1031,3.8431),(1.0816,4.1040),(1.0942,4.3295),(1.1031,4.4576)),
    "h2s":((1.2411,3.9686),(1.2410,4.0948),(1.2370,4.238),(1.2297,4.3626),(1.2266,4.4365)),
}


def _bracket(times,value):
    for i,node in enumerate(times):
        if math.isclose(value,node,rel_tol=0,abs_tol=1e-9):
            return ((i,1.0),)
    ensure(times[0] < value < times[-1],"Toxic exposure duration outside tabulated range; no extrapolation")
    upper=bisect_left(times,value)
    w=(value-times[upper-1])/(times[upper]-times[upper-1])
    return ((upper-1,1-w),(upper,w))


class HfH2sCoefficients(Model):
    fluid: Literal["hf","h2s"]
    release_type: Literal["continuous","instantaneous"]
    duration_s: NonNegative = 0
    hf_instantaneous_intercept: Finite | None = None
    intercept_qualification: str | None = Field(default=None,min_length=1,max_length=1000)


def _check_override(x):
    ensure((x.hf_instantaneous_intercept is None) == (x.intercept_qualification is None),"HF intercept override and qualification must be supplied together")
    ensure(x.hf_instantaneous_intercept is None or (x.fluid == "hf" and x.release_type == "instantaneous"),
           "Intercept override is only for instantaneous HF")
    if x.intercept_qualification is not None:
        ensure(bool(x.intercept_qualification.strip()),"Intercept qualification must not be blank")


@calculation("level1/hf-h2s-toxic-coefficients", "HF/H2S native toxic log-correlation coefficients", HfH2sCoefficients,
             ["Part3 Table4.11; eqs(3.63)-(3.64); PDF pp497-498,525"],
             limitations=["Native log10 correlation uses lb/s or lb and ft2; conversion factors2.205 and.0929 returned. Continuous lookup requires a printed duration node. HF instantaneous d is printed33,606: returned as33606 with ambiguous_print status, never silently changed to3.3606. Qualified caller override is explicit and traceable."])
def hf_h2s_coefficients(x):
    _check_override(x)
    status="clear"
    if x.release_type == "instantaneous":
        c,d=(.9674,2.7840) if x.fluid == "h2s" else (1.4056,33606)
        if x.fluid == "hf":
            status="ambiguous_print"
            if x.hf_instantaneous_intercept is not None:
                d,status=x.hf_instantaneous_intercept,"qualified_override"
    else:
        bracket=_bracket(HF_H2S_TIMES,x.duration_s)
        ensure(len(bracket)==1,"Coefficient lookup requires printed duration; area function interpolates curves", "interpolation_required")
        c,d=HF_H2S[x.fluid][bracket[0][0]]
    return {"c":c,"d":d,"native_magnitude_unit":"lb/s" if x.release_type == "continuous" else "lb",
            "native_area_unit":"ft2","si_mass_multiplier":LB_PER_KG,"si_area_multiplier":M2_PER_FT2,
            "source_cell_status":status}


class HfH2sArea(HfH2sCoefficients):
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    nonignition_probability: Fraction


@calculation("level1/hf-h2s-toxic-area", "HF/H2S duration-dependent toxic consequence area", HfH2sArea,
             ["Part3 §4.9.6,§4.9.11; eqs(3.63)-(3.64); Table4.11; PDF pp497-499,525"],
             origin="api581_equations_with_explicit_qualified_override_support",
             limitations=["Gas/vapor toxic consequence assumption. Continuous 5-60minute curves interpolate areas, not coefficients. Nonignition weighting applies once. Positive instantaneous HF mass requires qualified intercept override because printed33,606 is unresolved. No extrapolation or automatic spray/IDLH credit."])
def hf_h2s_area(x):
    _check_override(x)
    value=x.toxic_rate_kg_s if x.release_type == "continuous" else x.toxic_mass_kg
    if value == 0 or (x.release_type == "continuous" and x.duration_s == 0):
        return {"unweighted_personnel_area_m2":0,"personnel_area_m2":0}
    if x.release_type == "instantaneous":
        cell=hf_h2s_coefficients(x)
        ensure(cell["source_cell_status"] != "ambiguous_print","Instantaneous HF source intercept unresolved; qualified override required", "unsupported_table_cell")
        pairs=((cell["c"],cell["d"],1.0),)
    else:
        pairs=tuple((*HF_H2S[x.fluid][i],w) for i,w in _bracket(HF_H2S_TIMES,x.duration_s))
    logmag=math.log10(LB_PER_KG*value)
    area=math.fsum(w*M2_PER_FT2*10**(c*logmag+d) for c,d,w in pairs)
    return {"unweighted_personnel_area_m2":area,"personnel_area_m2":area*x.nonignition_probability}


TIMES=(180,300,600,1200,2400,3600)
LONG_TIMES=(90,*TIMES)
# Printed SI Table4.13M, kg/s and m2. None preserves N/A cells.
MISC = {
    "alcl3":{"powder":((),((3.4531,.9411),))},
    "co":{"gas":(TIMES,((9.55,1.15),(60.09,1.06),(189.42,1.13),(651.49,1.11),(1252.67,1.17),(1521.89,1.21)))},
    "hcl":{"gas":(TIMES,((47.39,1.09),(123.67,1.15),(531.45,1.10),(950.02,1.18),(1851.8,1.20),(2118.87,1.23)))},
    "nitric_acid":{
        "gas":(TIMES,((13230.9,1.25),(17146,1.25),(23851.3,1.24),(31185,1.23),(35813.7,1.22),(38105.8,1.22))),
        "liquid":(TIMES,((1114.96,1.08),(2006.1,1.02),(2674.47,1.06),(4112.65,1.06),(6688.99,1.06),(9458.29,1.12)))},
    "no2":{
        "gas":(TIMES,((1071.74,.70),(1466.57,.68),(1902.9,.68),(2338.76,.72),(3621.1,.70),(4070.48,.71))),
        "liquid":(TIMES,((430,.98),(610.31,1.04),(1340.93,1.07),(3020.54,1.08),(6110.67,1.12),(9455.68,1.13)))},
    "phosgene":{
        "gas":(TIMES,((3095.33,1.20),(5918.49,1.29),(12129.3,1.24),(27459.6,1.27),(63526.4,1.30),(96274.2,1.31))),
        "liquid":(TIMES,((733.39,1.06),(1520.02,1.10),(4777.72,1.12),(14727.5,1.16),(42905,1.20),(77287.7,1.23)))},
    "tdi":{"liquid":(TIMES,((793.04,1.06),(846.54,1.09),(1011.9,1.10),(1026.06,1.06),(1063.8,1.06),(1252.57,1.03)))},
    "ee":{
        "gas":(LONG_TIMES,((.8954,1.171),(1.7578,1.181),(4.0002,1.122),(7.5400,1.111),(24.56,.971),(31.22,.995),(59.67,.899))),
        "liquid":(LONG_TIMES,(None,None,None,(.6857,1.105),(3.6389,1.065),(9.8422,1.132),(23.513,1.104)))},
    "eo":{"gas":(LONG_TIMES,((.5085,1.222),(2.9720,1.207),(7.9931,1.271),(47.69,1.2909),(237.57,1.2849),(1088.4,1.1927),(1767.5,1.203)))},
    "po":{
        "gas":(TIMES,((.0008,1.913),(.0864,1.217),(.1768,1.2203),(.4172,1.2164),(.9537,1.2097),(1.2289,1.2522))),
        "liquid":(TIMES,(None,(2.4084,1.198),(9.0397,1.111),(17.425,1.114),(34.255,1.118),(367.06,.9855)))},
}
MiscFluid=Literal["alcl3","co","hcl","nitric_acid","no2","phosgene","tdi","ee","eo","po"]


class MiscCoefficients(Model):
    fluid: MiscFluid
    release_phase: Literal["gas","liquid","powder"]
    duration_s: NonNegative


def _misc_rows(x):
    ensure(x.release_phase in MISC[x.fluid],"Unsupported toxic fluid/phase", "unsupported_table_cell")
    return MISC[x.fluid][x.release_phase]


@calculation("level1/misc-toxic-coefficients", "Miscellaneous continuous toxic SI coefficients", MiscCoefficients,
             ["Part3 §4.9.8; Table4.13M; PDF pp498-499,529-530"],
             limitations=["Ten chemicals, printed SI kg/s and m2 coefficients. Exact printed duration nodes only. AlCl3 powder uses gas-column coefficients for all positive durations per §4.9.8. N/A cells never become zero. Uses SI table directly rather than guessing inconsistent US punctuation/exponents or reconverting US coefficients."])
def misc_coefficients(x):
    times,rows=_misc_rows(x)
    bracket=((0,1),) if not times else _bracket(times,x.duration_s)
    ensure(len(bracket)==1,"Coefficient lookup requires a printed duration node", "interpolation_required")
    pair=rows[bracket[0][0]]
    ensure(pair is not None,"Source toxic coefficient cell is N/A or unresolved", "unsupported_table_cell")
    return {"e":pair[0],"f":pair[1],"native_rate_unit":"kg/s","native_area_unit":"m2",
            "si_mass_multiplier":1,"si_area_multiplier":1}


class MiscArea(MiscCoefficients):
    release_type: Literal["continuous"] = "continuous"
    toxic_rate_kg_s: NonNegative
    nonignition_probability: Fraction


@calculation("level1/misc-toxic-area", "Ten additional chemical continuous toxic consequence areas", MiscArea,
             ["Part3 §4.9.8,§4.9.11; eq(3.65); Table4.13M; PDF pp498-499,529-530"],
             limitations=["Continuous only; no invented instantaneous correlation. Printed SI coefficients used directly; no additional unit conversion. N/A cells block interpolation that touches them. AlCl3 powder is duration-independent for positive duration. Caller qualifies phase and nonignition probability; no automatic spray credit."])
def misc_area(x):
    times,rows=_misc_rows(x)
    if x.toxic_rate_kg_s == 0 or x.duration_s == 0:
        return {"unweighted_personnel_area_m2":0,"personnel_area_m2":0}
    bracket=((0,1),) if not times else _bracket(times,x.duration_s)
    area=0.0
    for i,w in bracket:
        ensure(rows[i] is not None,"Toxic interpolation touches N/A or unresolved coefficient", "unsupported_table_cell")
        e,f=rows[i]
        area+=w*e*x.toxic_rate_kg_s**f
    return {"unweighted_personnel_area_m2":area,"personnel_area_m2":area*x.nonignition_probability}


class ToxicCutoff(Model):
    fluid: Literal["hf","h2s","ammonia","chlorine"]
    concentration_ppm_on_idlh_basis: NonNegative


@calculation("level1/toxic-cutoff", "Historical Level1 toxic concentration screening", ToxicCutoff,
             ["Part3 §4.9.9; PDF p499"],
             limitations=["2016 printed IDLH values: HF30,H2S100,NH3 300,Cl10ppm. Stored-fluid concentration must be on matching IDLH ppm basis, not silently inferred from mass fraction. At or below cutoff evaluation is not required by this source rule. Not a current occupational exposure limit or an atmospheric dispersion safety claim."])
def toxic_cutoff(x):
    value={"hf":30,"h2s":100,"ammonia":300,"chlorine":10}[x.fluid]
    return {"idlh_ppm":value,"requires_toxic_evaluation":x.concentration_ppm_on_idlh_basis > value}


class MitigationCredits(Model):
    rate_reduction_fraction: Fraction = 0
    duration_reduction_fraction: Fraction = 0
    mass_reduction_fraction: Fraction = 0


class ToxicMitigation(MitigationCredits):
    toxic_rate_kg_s: NonNegative
    toxic_mass_kg: NonNegative
    duration_s: NonNegative


@calculation("level1/toxic-mitigation", "Apply explicit toxic source mitigation credits", ToxicMitigation,
             ["Part3 §4.9.13; PDF pp499-500"],
             limitations=["Owner-qualified reductions only; no fixed default water-spray efficiency. Rate/duration apply to continuous release, mass to instantaneous. These are not the flammable Table4.6 detection magnitude credit. The caller controls the explicit credit basis and avoids applying the same measure twice."])
def toxic_mitigation(x):
    return {"toxic_rate_kg_s":x.toxic_rate_kg_s*(1-x.rate_reduction_fraction),
            "toxic_mass_kg":x.toxic_mass_kg*(1-x.mass_reduction_fraction),
            "duration_s":x.duration_s*(1-x.duration_reduction_fraction)}


class ToxicComponent(Model):
    fluid: Literal["hf","h2s","ammonia","chlorine","alcl3","co","hcl","nitric_acid","no2","phosgene","tdi","ee","eo","po"]
    release_phase: Literal["gas","liquid","powder"]
    release_type: Literal["continuous","instantaneous"]
    theoretical_rate_kg_s: NonNegative
    released_mass_kg: NonNegative
    toxic_mass_fraction: Fraction
    available_mass_kg: NonNegative
    detection_maximum_duration_s: NonNegative
    nonignition_probability: Fraction
    mitigation: MitigationCredits = Field(default_factory=MitigationCredits)
    concentration_ppm_on_idlh_basis: NonNegative | None = None
    hf_instantaneous_intercept: Finite | None = None
    intercept_qualification: str | None = Field(default=None,min_length=1,max_length=1000)


class ToxicMixtureComponentArea(Model):
    component_id: str = Field(min_length=1, max_length=100)
    personnel_area_m2: NonNegative


class ToxicMixtureAreas(Model):
    components: list[ToxicMixtureComponentArea] = Field(min_length=1, max_length=100)


@calculation("level1/toxic-component-consequence", "Compose toxic source/duration/mitigation and per-component area", ToxicComponent,
             ["Part3 §4.9; eqs(3.61)-(3.67); Tables4.11-4.13"],
             origin="api581_equations_with_explicit_qualified_mitigation",
             limitations=["Single toxic component; mixture maximum and four-hole aggregation are separate. Uses theoretical total leak rate without flammable magnitude reduction. HF/H2S/NH3/Cl use gas/vapor exposure assumptions; miscellaneous phases follow Table4.13. Optional printed IDLH screening only supports four refinery toxins. All interpolation domains and HF ambiguity still apply; mitigation may shorten duration below a supported table range and then evaluation is rejected."])
def toxic_component(x):
    common=x.fluid in ("hf","h2s","ammonia","chlorine")
    ensure(not common or x.release_phase == "gas","Common refinery toxic correlations assume gas/vapor consequence phase")
    ensure(x.fluid in ("hf","h2s") or x.hf_instantaneous_intercept is None and x.intercept_qualification is None,
           "HF intercept parameters apply only to HF instantaneous releases")
    if x.fluid in ("hf","h2s"):
        _check_override(x)
    if not common:
        ensure(x.release_type == "continuous","Miscellaneous toxic correlations support continuous releases only")
        _misc_rows(x)
    screening=x.concentration_ppm_on_idlh_basis is not None
    if screening:
        ensure(common,"Built-in IDLH cutoff is not provided for this chemical")
        required=toxic_cutoff(ToxicCutoff(fluid=x.fluid,concentration_ppm_on_idlh_basis=x.concentration_ppm_on_idlh_basis))["requires_toxic_evaluation"]
    else:
        required=True
    source=toxic_source(ToxicSource(theoretical_rate_kg_s=x.theoretical_rate_kg_s,released_mass_kg=x.released_mass_kg,toxic_mass_fraction=x.toxic_mass_fraction))
    duration=toxic_duration(ToxicDuration(available_mass_kg=x.available_mass_kg,theoretical_rate_kg_s=x.theoretical_rate_kg_s,
        detection_maximum_duration_s=x.detection_maximum_duration_s))["duration_s"]
    mitigated=toxic_mitigation(ToxicMitigation(**source,duration_s=duration,**x.mitigation.model_dump()))
    if not required:
        area={"unweighted_personnel_area_m2":0,"personnel_area_m2":0}
    elif x.fluid in ("hf","h2s"):
        area=hf_h2s_area(HfH2sArea(fluid=x.fluid,release_type=x.release_type,**mitigated,
            nonignition_probability=x.nonignition_probability,hf_instantaneous_intercept=x.hf_instantaneous_intercept,
            intercept_qualification=x.intercept_qualification))
    elif common:
        area=toxic_area(ToxicArea(fluid=x.fluid,release_type=x.release_type,**mitigated,nonignition_probability=x.nonignition_probability))
    else:
        area=misc_area(MiscArea(fluid=x.fluid,release_phase=x.release_phase,duration_s=mitigated["duration_s"],
            toxic_rate_kg_s=mitigated["toxic_rate_kg_s"],nonignition_probability=x.nonignition_probability))
    return {**mitigated,**area,"unmitigated_duration_s":duration,"screening_applied":screening,
            "requires_toxic_evaluation":required}


@calculation(
    "level1/toxic-mixture-consequence",
    "Largest individual Level 1 toxic consequence area for a mixture",
    ToxicMixtureAreas,
    ["Part 3 §4.9.12, §4.9.15(f), eq (3.68); PDF pp500-501"],
    limitations=[
        "Takes already calculated individual toxic component areas and returns the largest; it does not add overlapping clouds, recalculate species release rates, or perform dispersion. For four-hole weighting use the separate hole-weighted/Level 2 composition API."
    ],
)
def toxic_mixture_consequence(x):
    ensure(len({c.component_id for c in x.components}) == len(x.components), "Duplicate toxic component id")
    critical = max(x.components, key=lambda c: c.personnel_area_m2)
    return {
        "personnel_area_m2": critical.personnel_area_m2,
        "critical_component_id": critical.component_id,
        "component_areas_m2": {c.component_id: c.personnel_area_m2 for c in x.components},
        "component_count": len(x.components),
    }


class ToxicHoleCase(Model):
    hole: Literal["small", "medium", "large", "rupture"]
    generic_frequency_per_year: NonNegative
    components: list[ToxicMixtureComponentArea] = Field(min_length=1, max_length=100)


class ToxicHoleSummary(Model):
    cases: list[ToxicHoleCase] = Field(min_length=4, max_length=4)


@calculation(
    "level1/toxic-hole-summary",
    "Four-hole GFF-weighted Level 1 toxic consequence",
    ToxicHoleSummary,
    ["Part 3 §4.9.14-§4.9.15(f), eq (3.68); PDF pp500-501"],
    limitations=[
        "Requires one case for each canonical hole. Within each hole the largest individual toxic-component area is used, then areas are weighted by the supplied generic failure frequencies. Detection/DF-adjusted frequencies, dispersion and financial risk are outside this consequence-area API."
    ],
)
def toxic_hole_summary(x):
    ensure({c.hole for c in x.cases} == {"small", "medium", "large", "rupture"}, "Require four canonical hole cases")
    areas = {}
    for case in x.cases:
        ensure(len({c.component_id for c in case.components}) == len(case.components), "Duplicate toxic component id in hole case")
        areas[case.hole] = max(c.personnel_area_m2 for c in case.components)
    total = math.fsum(c.generic_frequency_per_year for c in x.cases)
    ensure(math.isfinite(total) and total > 0, "Total generic frequency must be finite and positive")
    weighted = math.fsum(c.generic_frequency_per_year / total * areas[c.hole] for c in x.cases)
    return {"personnel_area_m2": weighted, "total_generic_frequency_per_year": total,
            "by_hole_personnel_area_m2": areas}
