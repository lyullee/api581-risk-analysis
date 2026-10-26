"""CO2 Figure13.1 screening, source defaults and SI input preparation."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure, finite_tree
from .co2_corrosion import CO2Assessment, CO2WetModel, assessment
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad


class CO2PartialPressure(Model):
    total_pressure_pa_abs: Positive
    co2_mole_fraction: Fraction


@calculation("properties/co2-partial-pressure", "CO2 partial pressure from absolute total pressure and mole fraction", CO2PartialPressure,
    ["Part2 Table2.B.13.1; PDF p427"],limitations=[
        "pCO2=mole fraction*absolute total pressure. Input is fraction0..1, not mole percent or gauge pressure. No fugacity/EOS calculation or clamping to4MPa integrated model limit. Pure input conversion does not establish free-water or material applicability."])
def partial_pressure(x):
    value = x.total_pressure_pa_abs*x.co2_mole_fraction
    ensure(value > 0 or x.co2_mole_fraction == 0,"Partial pressure underflow","numerical_failure")
    return {"co2_partial_pressure_pa_abs":value}


class CO2MassFlowReynolds(Model):
    diameter_m: Positive
    cross_sectional_area_m2: Positive
    mass_flow_kg_s: NonNegative
    mixture_viscosity_pa_s: Positive


@calculation("damage/co2-reynolds-mass-flow", "CO2 mixture Reynolds number from mass flow and area", CO2MassFlowReynolds,
    ["Part2 eq(2.B.35); PDF p425"],limitations=[
        "Re=mass_flow*diameter/(area*viscosity); mass flux=mass_flow/area. Source wording calls dottedm mass flux although printed formula divides byarea; API names dimensional quantities explicitly rather than dividing an already-area-normalized flux again. Area/hydraulic diameter and effective viscosity externally qualified; no mixture-property model or laminar correlation."])
def mass_flow_reynolds(x):
    flux = x.mass_flow_kg_s/x.cross_sectional_area_m2
    re = flux*x.diameter_m/x.mixture_viscosity_pa_s
    finite_tree([flux,re])
    ensure((flux > 0 and re > 0) or x.mass_flow_kg_s == 0,"Mass-flow Reynolds underflow","numerical_failure")
    return {"mass_flux_kg_m2_s":flux,"reynolds_number":re}


class CO2MaterialScreen(Model):
    material_category: Literal["carbon_steel","low_alloy_steel","stainless_steel","copper_alloy","other"]
    interpretation: Literal["figure_13cr_ferrous","table_resistant_alloys"]
    chromium_mass_fraction: Fraction | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/co2-material-screen", "CO2 figure chromium or table material screening", CO2MaterialScreen,
    ["Part2 Figure2.B.13.1,Table2.B.13.1; PDF pp427,429"],limitations=[
        "Figure screens carbon steel orCr<13%; equality13% is source-assumed resistant. Chromium threshold applied only to qualified ferrous categories, not copper with nominalCr0. Table interpretation lists stainless/copper assumed resistant and carbon/low-alloy evaluated. Other material remains not_covered, never automatic zero. Explicit interpretation preserves differences between named-alloy table and elemental figure. Source-assumed resistance is CO2-specific, not immunity to other corrosion/SCC or a verified material-performance conclusion."])
def material_screen(x):
    ensure(bool(x.qualification_basis.strip()),"Material identification/screening qualification required")
    category = x.material_category
    if x.interpretation == "table_resistant_alloys":
        ensure(x.chromium_mass_fraction is None,"Chromium fraction is unused in table-only classification")
        decision = "evaluate_co2" if category in ("carbon_steel","low_alloy_steel") else "source_assumed_resistant" if category in ("stainless_steel","copper_alloy") else "not_covered"
    elif category == "carbon_steel":
        ensure(x.chromium_mass_fraction is None,"Carbon-steel figure branch does not require competing chromium input")
        decision = "evaluate_co2"
    elif category in ("low_alloy_steel","stainless_steel"):
        ensure(x.chromium_mass_fraction is not None,"Ferrous figure screen requires known chromium fraction")
        decision = "evaluate_co2" if x.chromium_mass_fraction < .13 else "source_assumed_resistant"
    else:
        ensure(x.chromium_mass_fraction is None,"Figure chromium screen not generalized to non-ferrous/unknown material")
        decision = "not_covered"
    return {"material_screen_decision":decision,"source_material_resistance_assumed":decision == "source_assumed_resistant"}


class CO2HydrocarbonWetting(Model):
    liquid_hydrocarbons_present: bool
    water_cut_policy: Literal["explicit_qualified_percent","source_default_30_percent"] | None = None
    water_content_percent: float | None = Field(default=None,ge=0,le=100,strict=True,allow_inf_nan=False)
    water_content_basis: str | None = None
    mixture_velocity_m_s: NonNegative | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/co2-hydrocarbon-wetting-screen", "CO2 low-water high-velocity hydrocarbon figure screen", CO2HydrocarbonWetting,
    ["Part2 Figure2.B.13.1,Table2.B.13.1; PDF pp427,429"],limitations=[
        "LiquidHC AND water<20% AND velocity>1m/s gives source figure exemption. Equality20%/1m/s proceeds to moisture/water check. Percentage basis is not identified precisely in figure: explicit qualified water-cut percent/basis required; do not substitute gas water mass fraction or glycol composition. Missing liquid-system water cut can use explicit source default30%, which never grants exemption. NoHC proceeds to moisture check. This is a qualified legacy figure rule, not proof metal is oil-wet under actual multiphase flow."])
def hydrocarbon_screen(x):
    ensure(bool(x.qualification_basis.strip()),"Hydrocarbon/wetting applicability basis required")
    if not x.liquid_hydrocarbons_present:
        ensure(x.water_cut_policy is None and x.water_content_percent is None and x.water_content_basis is None and x.mixture_velocity_m_s is None,
            "No-liquid-HC branch cannot contain unused liquid-system water/velocity fields")
        water,default,exempt = None,False,False
    else:
        ensure(x.water_cut_policy is not None,"Liquid-HC water-cut policy required")
        default = x.water_cut_policy == "source_default_30_percent"
        if default:
            ensure(x.water_content_percent is None and x.water_content_basis is None,"Default30% cannot have competing explicit water cut")
            water = 30.
        else:
            ensure(x.water_content_percent is not None and x.water_content_basis is not None and bool(x.water_content_basis.strip()),"Explicit liquid water cut requires value and qualified percentage basis")
            water = x.water_content_percent
        if water < 20:
            ensure(x.mixture_velocity_m_s is not None,"Low water cut requires velocity to resolve figure branch")
        exempt = water < 20 and x.mixture_velocity_m_s > 1
    return {"wetting_screen_decision":"figure_low_water_high_velocity_exemption" if exempt else "proceed_to_water_check",
        "water_content_percent_used":water,"source_water_default_used":default}


class CO2MoistureScreen(Model):
    temperature_k: Positive
    evidence: Literal["qualified_dew_point","qualified_free_water_present","qualified_no_free_water","source_missing_moisture_assume_wet"]
    dew_point_temperature_k: Positive | None = None
    dew_point_uncertainty_k: NonNegative | None = None
    equality_policy: Literal["figure_strict_less","indeterminate_at_saturation"] | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/co2-moisture-screen", "CO2 free-water or dew-point screening with explicit uncertainty", CO2MoistureScreen,
    ["Part2 §13.3.2,Table2.B.13.1,Figure2.B.13.1; PDF pp423-424,427,429"],limitations=[
        "Known free-water presence/absence can be supplied with basis. Missing gas moisture can explicitly assume wet per table, flagged as source assumption. Qualified dew point requires owner uncertainty and equality policy: outside uncertainty interval classify; inside interval indeterminate. At zero uncertainty and equalT, figure_strict_less uses absent, alternative leaves indeterminate. Approximate eq2.B.25 is not assumed accurate within±10F: no automatic zero-uncertainty adoption of its output. Free-water states concern CO2 only, not all corrosion."])
def moisture_screen(x):
    ensure(bool(x.qualification_basis.strip()),"Moisture/free-water evidence basis required")
    assumed = x.evidence == "source_missing_moisture_assume_wet"
    if x.evidence == "qualified_dew_point":
        ensure(x.dew_point_temperature_k is not None and x.dew_point_uncertainty_k is not None and x.equality_policy is not None,"Dew-point screen requires value, uncertainty and equality policy")
        delta = x.temperature_k-x.dew_point_temperature_k
        u = x.dew_point_uncertainty_k
        state = "present" if delta < -u else "absent" if delta > u else "absent" if u == 0 and delta == 0 and x.equality_policy == "figure_strict_less" else "indeterminate"
    else:
        ensure(x.dew_point_temperature_k is None and x.dew_point_uncertainty_k is None and x.equality_policy is None,"Direct/default water evidence cannot carry competing dew-point inputs")
        state = "absent" if x.evidence == "qualified_no_free_water" else "present"
    return {"free_water_screen_state":state,"free_water_assumed_from_missing_data":assumed}


class CO2ScreenedAssessment(Model):
    temperature_k: Positive
    pressure: CO2PartialPressure
    material: CO2MaterialScreen
    hydrocarbon_wetting: CO2HydrocarbonWetting | None = None
    moisture: CO2MoistureScreen | None = None
    wet_model: CO2WetModel | None = None
    qualification_basis: str = Field(min_length=1)


def _zero():
    return {"corrosion_rate_m_year":0.,"base_corrosion_rate_m_year":0.,"model_ph":None,"temperature_ph_factor":None,
        "fugacity_pa":None,"requested_shear_stress_pa":None,"applied_shear_stress_pa":None,"shear_cap_applied":False,
        "glycol_factor":1.,"inhibitor_factor":1.,"applied_reduction_factor":1.,"sharp_temperature_interval_interpolated":False}


@calculation("damage/co2-screened-assessment", "CO2 material hydrocarbon moisture screening through corrosion model", CO2ScreenedAssessment,
    ["Part2 Annex2.B §13,Figure2.B.13.1,Table2.B.13.1; PDF pp423-429"],origin="api581_composition_with_explicit_figure_policies",limitations=[
        "Explicit 2016 material/HC-water-velocity/dew-point policies, source defaults and qualified wet model; no autonomous metallurgy or actual wetting/EOS judgment. Source resistance/exemption yields CO2-specific0 with flags, not measured immunity or zero total DF. Indeterminate moisture errors rather than asserts dry. Unused downstream inputs on screened branches rejected; no hidden model fallback. Low-Cr stainless figure evaluation is not silently reclassified low-alloy: current quantitative model supports only named carbon/low-alloy steel. Same pressure/temperature/known velocity drives screens and wet kernel. Explicit free-water evidence or source wet assumption supersedes approximate dew-point generation."])
def screened_assessment(x):
    ensure(bool(x.qualification_basis.strip()),"Screened model applicability basis required")
    pressure = partial_pressure(x.pressure)
    p = pressure["co2_partial_pressure_pa_abs"]
    material = material_screen(x.material)
    state = material["material_screen_decision"]
    ensure(state != "not_covered","Material not covered by selected source screening interpretation")
    water = {"wetting_screen_decision":None,"water_content_percent_used":None,"source_water_default_used":False}
    moisture = {"free_water_screen_state":None,"free_water_assumed_from_missing_data":False}
    if state == "source_assumed_resistant" or p == 0:
        ensure(x.hydrocarbon_wetting is None and x.moisture is None and x.wet_model is None,"Material/no-CO2 branch cannot carry unused downstream model inputs")
        result,branch = _zero(),"source_material_resistance" if state == "source_assumed_resistant" else "no_co2"
    else:
        ensure(x.hydrocarbon_wetting is not None,"Susceptible nonzero-CO2 case requires qualified HC/water screen")
        water = hydrocarbon_screen(x.hydrocarbon_wetting)
        if water["wetting_screen_decision"] == "figure_low_water_high_velocity_exemption":
            ensure(x.moisture is None and x.wet_model is None,"Figure HC exemption cannot carry unused moisture/wet model")
            result,branch = _zero(),"figure_hydrocarbon_exemption"
        else:
            ensure(x.moisture is not None,"Water check requires direct evidence, dew point or explicit source assumption")
            ensure(x.moisture.temperature_k == x.temperature_k,"Moisture screen and model temperatures must agree")
            moisture = moisture_screen(x.moisture)
            ensure(moisture["free_water_screen_state"] != "indeterminate","Moisture uncertainty interval unresolved; no automatic zero corrosion","co2_moisture_indeterminate")
            if moisture["free_water_screen_state"] == "absent":
                ensure(x.wet_model is None,"Dry branch cannot contain unused wet-model inputs")
                result,branch = _zero(),"qualified_no_free_water"
            else:
                ensure(x.material.material_category in ("carbon_steel","low_alloy_steel"),"Quantitative CO2 kernel does not reclassify low-Cr stainless as low-alloy steel")
                if x.wet_model is not None and x.wet_model.flow.method == "turbulent_flow" and x.hydrocarbon_wetting.mixture_velocity_m_s is not None:
                    ensure(x.wet_model.flow.mixture_velocity_m_s == x.hydrocarbon_wetting.mixture_velocity_m_s,"HC screen and wet flow velocities must agree")
                result = assessment(CO2Assessment(material=x.material.material_category,temperature_k=x.temperature_k,co2_partial_pressure_pa_abs=p,
                    free_liquid_water_present=True,applicability_basis=x.qualification_basis,wet_model=x.wet_model))
                result.pop("calculation_branch")
                branch = "wet_carbonic_acid_model"
    return {**result,**pressure,**material,**water,**moisture,"screened_calculation_branch":branch}


class CO2ScreenedThinning(Model):
    corrosion: CO2ScreenedAssessment
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/co2-screened-thinning", "Screened CO2 rate through non-AST unclad thinning DF", CO2ScreenedThinning,
    ["Part2 Annex2.B §13,Figure2.B.13.1; Part2 §4.5.7"],origin="api581_composition_with_explicit_figure_policies",limitations=[
        "Unclad non-AST component and owner-qualified strength/inspection baseline. Retains material/HC exemption, moisture uncertainty/default flags and source-specific rate through DF. Zero CO2 rate is not total DF0 or omission of other mechanisms. No independent confirmation of legacy material/wetting rules, oil-water phase distribution, chromium chemistry, actual moisture or field conditions."])
def screened_thinning(x):
    rate = screened_assessment(x.corrosion)
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=rate["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**rate,**result}
