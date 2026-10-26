"""2016 toxic table snapshot, exposure calculations and dispersion-area handoff."""
import math
import sys
from statistics import NormalDist
from typing import Annotated, Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure

Fluid = Literal["acrolein","acrylonitrile","aluminum_trichloride","ammonia","benzene","bromine",
    "carbon_monoxide","carbon_tetrachloride","chlorine","ethylene_glycol_monoethyl_ether","ethylene_oxide",
    "formaldehyde","hydrogen_chloride","hydrogen_cyanide","hydrogen_fluoride","hydrogen_sulfide","methanol",
    "methyl_bromide","methyl_isocyanate","nitric_acid","nitrogen_dioxide","phosgene","propylene_oxide",
    "styrene","sulphur_dioxide","toluene","toluene_diisocyanate"]
# A,B,N,IDLH ppm,AEGL3(10/30/60min) ppm,EPA mg/L,ERPG3 ppm.
# Dashes remain None. Historical printed values are not current exposure limits.
_ROWS={
    "acrolein":(-9.93,2.05,1,2,None,None,None,.50,None),
    "acrylonitrile":(-29.42,3.01,1.43,85,None,None,None,.08,75),
    "aluminum_trichloride":(-14.65,2,1,None,None,None,None,None,None),
    "ammonia":(-35.90,1.85,2,10,None,None,None,.14,750),
    "benzene":(-109.8,5.30,2,500,None,None,None,None,1000),
    "bromine":(-9.04,.92,2,3,None,None,None,.01,5),
    "carbon_monoxide":(-37.98,3.70,1,1200,1700,600,330,None,500),
    "carbon_tetrachloride":(-6.29,.41,2.5,200,None,None,None,None,750),
    "chlorine":(-8.29,.92,2,10,None,28,20,.01,20),
    "ethylene_glycol_monoethyl_ether":(-15.54,1,2,None,None,None,None,None,None),
    "ethylene_oxide":(-6.21,1,1,800,None,None,None,None,None),
    "formaldehyde":(-12.24,1.30,2,20,None,None,None,.01,25),
    "hydrogen_chloride":(-16.85,2,1,50,620,210,100,.03,150),
    "hydrogen_cyanide":(-29.42,3.01,1.43,50,27,21,15,None,25),
    "hydrogen_fluoride":(-48.33,4.853,1,30,170,62,44,None,None),
    "hydrogen_sulfide":(-31.42,3.01,1.43,100,76,60,50,None,100),
    "methanol":(None,None,None,None,15000,15000,7900,None,None),
    "methyl_bromide":(-56.81,5.27,1,None,None,None,None,None,200),
    "methyl_isocyanate":(-5.64,1.64,.65,None,1.2,.4,.2,None,5),
    "nitric_acid":(-5.48,1,2,None,None,None,None,None,None),
    "nitrogen_dioxide":(-13.79,1.40,2,20,None,None,None,None,None),
    "phosgene":(-19.27,3.69,1,2,3.6,1.5,.75,None,1),
    "propylene_oxide":(-7.415,.509,2,400,None,None,None,.59,750),
    "styrene":(None,None,None,700,None,None,None,None,1000),
    "sulphur_dioxide":(-15.67,2.10,1,100,None,None,None,None,None),
    "toluene":(-6.79,.41,2.5,500,1600,900,630,None,None),
    "toluene_diisocyanate":(-4.49,1,2,None,None,None,None,None,None),
}
_TABLE_LIMIT="Historical2016 Table4.14 snapshot, not current occupational/emergency exposure guidance. Printed ammonia IDLH10ppm retained. Dashes are unavailable, not zero. Probit concentration ppm and time seconds follow Annex3.A nomenclature; caller must qualify coefficient/species applicability. EPA mg/L is not implicitly converted to ppm."


class ToxicFluid(Model):
    fluid: Fluid


@calculation("properties/toxic-impact-table", "2016 Table4.14 toxic criteria and probit parameters", ToxicFluid,
             ["Part3 Table4.14; PDF p531; Annex3.A nomenclature PDF624"],limitations=[_TABLE_LIMIT])
def impact_table(x):
    a,b,n,idlh,a10,a30,a60,epa,erpg=_ROWS[x.fluid]
    return {"probit_intercept":a,"probit_slope":b,"concentration_exponent":n,"probit_available":a is not None,
            "probit_concentration_unit":"ppm","probit_duration_unit":"s","idlh_ppm":idlh,
            "aegl3_ppm":{duration:value for duration,value in [("600",a10),("1800",a30),("3600",a60)] if value is not None},
            "epa_toxic_endpoint_mg_l":epa,"erpg3_ppm":erpg}


def _coefficients(fluid):
    a,b,n=_ROWS[fluid][:3]
    ensure(a is not None,"No printed probit parameters for selected fluid","toxic_probit_unavailable")
    return a,b,n


def _effect(fluid,logdose):
    a,b,_=_coefficients(fluid)
    if logdose is None:
        return {"probit":None,"fatality_probability":0}
    probit=a+b*logdose
    return {"probit":probit,"fatality_probability":.5*math.erfc(-(probit-5)/math.sqrt(2))}


PPM = Annotated[float,Field(ge=0,le=1e6,strict=True,allow_inf_nan=False)]


class SpeciesProbit(ToxicFluid):
    concentration_ppm: PPM
    exposure_duration_s: NonNegative


@calculation("effects/toxic-species-probit", "Table4.14 constant-exposure toxic probit", SpeciesProbit,
             ["Part3 Table4.14, Annex3.A eq(3.A.5); PDF pp531,620,624"],limitations=[_TABLE_LIMIT,
                          "Pr=A+B*ln(C^N*t); probability=Phi(Pr-5). Constant species concentration, not whole-mixture concentration. Zero exposure gives zero probability with no finite probit. No dispersion, escape or dose-response validation for a particular installation."])
def species_probit(x):
    _,_,n=_coefficients(x.fluid)
    logdose=None if x.concentration_ppm == 0 or x.exposure_duration_s == 0 else n*math.log(x.concentration_ppm)+math.log(x.exposure_duration_s)
    return _effect(x.fluid,logdose)


class SpeciesThreshold(ToxicFluid):
    exposure_duration_s: Positive
    target_fatality_probability: Fraction = .5


@calculation("effects/toxic-species-threshold", "Species concentration for target toxic probit probability", SpeciesThreshold,
             ["Part3 Table4.14, Annex3.A eq(3.A.5) inverse; PDF pp531,620,624"],
             origin="api581_toxic_probit_inverse",limitations=[_TABLE_LIMIT,
                          "Default50% fatality corresponds to Pr5. Probability must be strictly between0 and1. Reports whether mathematical threshold is within pure-species1e6ppm limit; values above this are not silently capped."])
def species_threshold(x):
    a,b,n=_coefficients(x.fluid)
    ensure(0 < x.target_fatality_probability < 1,"Target probability must be strictly between0 and1")
    probit=5+NormalDist().inv_cdf(x.target_fatality_probability)
    concentration=math.exp(((probit-a)/b-math.log(x.exposure_duration_s))/n)
    ensure(concentration > 0,"Toxic threshold underflow","numerical_failure")
    return {"concentration_ppm":concentration,"probit":probit,"within_pure_species_limit":concentration <= 1e6}


class ConcentrationPoint(Model):
    time_s: NonNegative
    concentration_ppm: PPM


class DoseProfile(ToxicFluid):
    profile: list[ConcentrationPoint] = Field(min_length=2,max_length=10000)
    interpolation: Literal["previous","linear"]
    profile_source: str = Field(min_length=1,max_length=1000)


@calculation("effects/toxic-dose-profile", "Time-varying species dose and Table4.14 probit", DoseProfile,
             ["Part3 Annex3.A eq(3.A.5); PDF pp531,620,624"],
             origin="engineering_transient_extension_of_api581_probit",limitations=[_TABLE_LIMIT,
                          "Explicit extension: replaces constant C^N*t with integral C(t)^N dt. Previous holds each left concentration; final point only closes last interval. Linear integrates concentration power analytically, not a trapezoid of C^N. Not a printed transient API581 equation or an actual slabx run. No tail outside supplied profile and no automatic exposure cap."])
def dose_profile(x):
    _,_,n=_coefficients(x.fluid)
    ensure(bool(x.profile_source.strip()),"Profile source must be nonblank")
    ensure(x.profile[0].time_s == 0 and all(b.time_s > a.time_s for a,b in zip(x.profile,x.profile[1:])),
           "Concentration profile must start at0 with strictly increasing times")
    logs=[]
    for a,b in zip(x.profile,x.profile[1:]):
        dt=b.time_s-a.time_s
        if x.interpolation == "previous":
            if a.concentration_ppm == 0:
                continue
            average_log=n*math.log(a.concentration_ppm)
        else:
            high=max(a.concentration_ppm,b.concentration_ppm)
            if high == 0:
                continue
            ratio=min(a.concentration_ppm,b.concentration_ppm)/high
            factor=(1 if ratio == 1 else 1/(n+1) if ratio == 0
                    else -math.expm1((n+1)*math.log(ratio))/((n+1)*(1-ratio)))
            average_log=n*math.log(high)+math.log(factor)
        logs.append(math.log(dt)+average_log)
    duration=x.profile[-1].time_s
    if not logs:
        return {**_effect(x.fluid,None),"dose_ppm_power_n_s":0,"log_dose":None,"dose_representable":True,
                "duration_s":duration,"equivalent_constant_concentration_ppm":0}
    largest=max(logs)
    logdose=largest+math.log(math.fsum(math.exp(value-largest) for value in logs))
    dose=math.exp(logdose) if math.log(math.ulp(0.0)) <= logdose <= math.log(sys.float_info.max) else None
    return {**_effect(x.fluid,logdose),"dose_ppm_power_n_s":dose,"log_dose":logdose,"dose_representable":dose is not None,
            "duration_s":duration,"equivalent_constant_concentration_ppm":math.exp((logdose-math.log(duration))/n)}


class ToxicDuration(Model):
    available_mass_kg: NonNegative
    mixture_release_rate_kg_s: NonNegative
    detection_maximum_duration_s: NonNegative


@calculation("release/level2-toxic-duration", "Level2 toxic release duration bound", ToxicDuration,
             ["Part3 eq(3.186), §5.9.3; PDF p566"],
             limitations=["Minimum of3600s, full inventory/full mixture rate, detection/isolation duration. Do not divide full inventory by toxic-component rate. Constant-rate source approximation; no transient depressurization. Release duration is not automatically receptor exposure duration."])
def toxic_duration(x):
    if x.mixture_release_rate_kg_s == 0 or x.available_mass_kg == 0:
        return {"release_duration_s":0,"governing_limit":"no_release" if x.mixture_release_rate_kg_s == 0 else "no_inventory"}
    values=[(3600,"one_hour"),(x.available_mass_kg/x.mixture_release_rate_kg_s,"inventory"),
            (x.detection_maximum_duration_s,"detection_isolation")]
    duration,limit=min(values,key=lambda item:item[0])
    ensure(duration > 0 or x.detection_maximum_duration_s == 0,
           "Positive toxic release duration underflow","numerical_failure")
    return {"release_duration_s":duration,"governing_limit":limit}


class MixtureLimit(Model):
    pure_component_limit_ppm: Positive
    toxic_mole_fraction: Fraction


@calculation("consequence/toxic-mixture-limit", "Homogeneous mixture cloud toxic concentration criterion", MixtureLimit,
             ["Part3 eqs(3.189)-(3.190); PDF p567"],limitations=["Divides pure-component ppm criterion by toxic mole fraction, not mass fraction. Applies when dispersion concentration represents entire homogeneous mixture using full release rate. Species-resolved concentration must not be divided again. Zero mole fraction means absent component; no finite modified criterion is returned."])
def mixture_limit(x):
    if x.toxic_mole_fraction == 0:
        return {"modified_mixture_limit_ppm":None,"component_present":False,"attainable_in_mixture":False}
    modified=x.pure_component_limit_ppm/x.toxic_mole_fraction
    return {"modified_mixture_limit_ppm":modified,"component_present":True,"attainable_in_mixture":modified <= 1e6}


class ToxicCloudArea(Model):
    component_id: str = Field(min_length=1,max_length=100)
    selected_criterion_source: str = Field(min_length=1,max_length=1000)
    cloud_area_m2: NonNegative


class ToxicCase(Model):
    components: list[ToxicCloudArea] = Field(min_length=1,max_length=100)
    non_ignition_probability: Fraction


@calculation("consequence/level2-toxic-case", "Selected toxic cloud footprints to conditional toxic consequence", ToxicCase,
             ["Part3 §§5.9.2,5.9.4-5.9.6 eq(3.188); PDF pp565-567"],
             limitations=["Caller supplies one chosen criterion and qualified footprint per toxic component. Criteria hierarchy: probit/LC50, then ERPG3/AEGL3/TEEL3, then IDLH/EPA endpoint. Selection within a tier is caller-qualified, not maximum across incomparable exposure criteria. Takes largest component area and applies non-ignition probability once; equipment toxic damage area is0. Does not run dispersion or sum overlapping clouds."])
def toxic_case(x):
    ensure(len({c.component_id for c in x.components}) == len(x.components),"Duplicate toxic component")
    ensure(all(c.component_id.strip() and c.selected_criterion_source.strip() for c in x.components),"Component and criterion source must be nonblank")
    critical=max(x.components,key=lambda c:c.cloud_area_m2)
    return {"equipment_area_m2":0,"personnel_area_m2":x.non_ignition_probability*critical.cloud_area_m2,
            "unweighted_cloud_area_m2":critical.cloud_area_m2,"critical_component_id":critical.component_id,
            "component_cloud_areas_m2":{c.component_id:c.cloud_area_m2 for c in x.components}}


class ToxicFrequencyCase(ToxicCase):
    hole: Literal["small","medium","large","rupture"]
    generic_frequency_per_year: NonNegative


class ToxicSummary(Model):
    cases: list[ToxicFrequencyCase] = Field(min_length=4,max_length=4)


@calculation("consequence/level2-toxic-summary", "Four-hole GFF-weighted Level2 toxic consequence", ToxicSummary,
             ["Part3 eqs(3.188),(3.191); PDF p567"],origin="api581_toxic_four_hole_composition",
             limitations=["Requires all four canonical holes once. Takes component maximum and non-ignition weighting within each hole, then generic-frequency average. No DF-adjusted frequency substitution or financial/individual-risk computation. Cloud footprints and selected exposure criteria remain externally qualified inputs."])
def toxic_summary(x):
    ensure({c.hole for c in x.cases} == {"small","medium","large","rupture"},"Require four distinct canonical hole sizes")
    total=math.fsum(c.generic_frequency_per_year for c in x.cases)
    ensure(math.isfinite(total) and total > 0,"Total generic frequency must be finite and positive")
    areas={c.hole:toxic_case(ToxicCase(**c.model_dump(include=set(ToxicCase.model_fields))))["personnel_area_m2"] for c in x.cases}
    return {"equipment_area_m2":0,"personnel_area_m2":math.fsum(c.generic_frequency_per_year/total*areas[c.hole] for c in x.cases),
            "total_generic_frequency_per_year":total,"by_hole_personnel_area_m2":areas}
