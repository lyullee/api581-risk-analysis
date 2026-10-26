"""Cooling-water figure11.1 source selection with measured-rate precedence."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .cooling_water import CoolingFresh, fresh_assessment, CoolingSeawater, seawater_rate, CoolingCoupon, coupon_rate
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Distribution = Literal["general","local"]
Material = Literal["carbon_steel","low_alloy_steel","other_material"]


class CoolingSystemType(Model):
    system: Literal["once_through", "closed_recirculated", "open_recirculated"]
    water_source: Literal["fresh", "seawater", "brackish", "unknown"]
    reuses_heated_water: bool
    continual_makeup_required: bool
    blowdown_or_evaporation_loss: bool
    qualification_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-system-type", "Cooling-water system type and operating premise", CoolingSystemType,
    ["Part2 Annex2.B §§11.1.2-11.1.5; PDF pp397-398"], limitations=[
        "System classification contract only. Once-through, closed-recirculated and open-recirculated definitions are validated from supplied operating facts; water treatment, corrosion rate, material suitability and source chemistry are not inferred."])
def system_type(x):
    ensure(bool(x.qualification_basis.strip()), "Cooling-system qualification basis must not be blank")
    if x.system == "once_through":
        ensure(not x.reuses_heated_water and not x.blowdown_or_evaporation_loss,
            "Once-through system must not reuse heated water or claim recirculating loss")
    elif x.system == "closed_recirculated":
        ensure(x.reuses_heated_water and not x.continual_makeup_required,
            "Closed recirculated system requires reuse and no continual makeup")
    else:
        ensure(x.reuses_heated_water and x.continual_makeup_required and x.blowdown_or_evaporation_loss,
            "Open recirculated system requires reuse, continual makeup and evaporation/blowdown loss")
    return {"system": x.system, "water_source": x.water_source,
        "requires_continual_makeup": x.continual_makeup_required,
        "has_evaporation_or_blowdown_loss": x.blowdown_or_evaporation_loss,
        "classification_basis": "supplied_operating_premise"}


class TreatedCooling(Model):
    material: Literal["carbon_steel","low_alloy_steel"]
    system: Literal["open_recirculating","closed_recirculating","once_through_fresh"]
    qualified_effective_treatment_program: bool
    actual_ph: float = Field(ge=6.5,le=9.5,strict=True,allow_inf_nan=False)
    effective_microbiological_control: bool
    no_deposits_or_local_low_flow: bool
    qualification_basis: str = Field(min_length=1)
    once_through_interpretation: Literal["body_untreated_only","qualified_figure_treatment"] | None = None


@calculation("damage/cooling-water-treatment-bounds", "Qualified treated cooling-water strict corrosion bounds", TreatedCooling,
    ["Part2 §11.1.10,§11.3.2.2,Figure2.B.11.1; PDF pp401,404,414"],limitations=[
        "Figure treated branch gives general<3mpy and pitting<15mpy, not exact measured rates. Bounds converted exactly to m/year and returned with strict-less relation. Qualified effective treatment, MIC control, no deposits/local low flow and pH6.5..9.5 required. Figure allows once-through fresh to enter treatment branch but detailed body assumes no chemical treatment except biocide: explicit qualified-figure interpretation required for treated once-through. No automatic program-efficacy or alloy-degradation assessment."])
def treatment_bounds(x):
    ensure(x.qualified_effective_treatment_program and x.effective_microbiological_control and x.no_deposits_or_local_low_flow,
        "Source treatment/MIC/deposit assumptions not met")
    ensure(bool(x.qualification_basis.strip()),"Treatment qualification basis must not be blank")
    if x.system == "once_through_fresh":
        ensure(x.once_through_interpretation == "qualified_figure_treatment","Treated once-through requires explicit qualified figure interpretation","ambiguous_source")
    else:
        ensure(x.once_through_interpretation is None,"Once-through interpretation cannot accompany recirculating system")
    return {"general_upper_bound_m_year":3*.0000254,"pitting_upper_bound_m_year":15*.0000254,"source_rate_relation":"strictly_less_than"}


class OtherCoolingMaterial(Model):
    material: Literal["other_material"]
    qualified_for_resistant_material_nominal_estimate: bool
    other_degradation_assessed: bool
    applicability_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-other-material-estimate", "Cooling-water non-carbon/low-alloy nominal figure estimate", OtherCoolingMaterial,
    ["Part2 §11.1.10-11.1.11,Figure2.B.11.1; PDF pp401,414"],limitations=[
        "Figure non-carbon/non-low-alloy branch estimates.5mpy=.0000127m/year. This is not treated closed-system rate. Detailed text has no quantitative SCC/pitting/dealloying model for other alloys; explicit owner qualification and separate assessment of other degradation required. No automatic assertion stainless/copper/titanium or any nonmetal is immune, and no selection of this estimate solely from material name."])
def other_material(x):
    ensure(x.qualified_for_resistant_material_nominal_estimate and x.other_degradation_assessed and bool(x.applicability_basis.strip()),
        "Nominal other-material estimate requires applicability and other-degradation assessment")
    return {"nominal_corrosion_rate_m_year":.5*.0000254}


class CoolingMeasurement(Model):
    measurement_type: Literal["component_general","component_local","coupon_weight_loss_general"]
    measured_rate_m_year: NonNegative
    representative_for_assessed_component: bool
    representativeness_basis: str = Field(min_length=1)
    pitting_multiplier: Positive | None = Field(default=None,ge=5,le=10)


class MeasuredCoolingSelection(Model):
    measurement: CoolingMeasurement
    assessment_distribution: Distribution


def _measurement(measurement,distribution):
    ensure(measurement.representative_for_assessed_component and bool(measurement.representativeness_basis.strip()),
        "Measured-rate priority requires qualified component representativeness")
    if measurement.measurement_type == "coupon_weight_loss_general" and distribution == "local":
        ensure(measurement.pitting_multiplier is not None,"Local coupon estimate requires explicit5-10 pitting multiplier")
        rate = coupon_rate(CoolingCoupon(coupon_general_corrosion_rate_m_year=measurement.measured_rate_m_year,
            pitting_multiplier=measurement.pitting_multiplier,representativeness_basis=measurement.representativeness_basis))["pitting_corrosion_rate_m_year"]
        return rate,"coupon_pitting_rule"
    ensure(measurement.pitting_multiplier is None,"Pit multiplier applies only to local estimate from general weight-loss coupon")
    if measurement.measurement_type == "coupon_weight_loss_general":
        return measurement.measured_rate_m_year,"coupon_general"
    ensure(measurement.measurement_type == "component_"+distribution,"Component measurement general/local distribution must match assessment")
    return measurement.measured_rate_m_year,"component_measurement"


@calculation("damage/cooling-water-measured-rate", "Qualified representative measured cooling-water rate", MeasuredCoolingSelection,
    ["Part2 §11.1.10(c),Figure2.B.11.1; PDF pp401,414"],limitations=[
        "Representative component/coupon measurements take priority over model. General/local component rate must match assessment. General weight-loss coupon used for local assessment requires explicit5-10 multiplier; already-local component measurements must never be multiplied again. Coupon coverage of deposits/stagnant/MIC areas is not inferred. Zero measured rate remains a valid explicit input, not treated as missing."])
def measured_rate(x):
    rate,source = _measurement(x.measurement,x.assessment_distribution)
    return {"corrosion_rate_m_year":rate,"selection_source":source}


class FreshChoice(Model):
    kind: Literal["freshwater_model"]
    model: CoolingFresh


class SeawaterChoice(Model):
    kind: Literal["seawater_model"]
    model: CoolingSeawater


class TreatmentChoice(Model):
    kind: Literal["treated"]
    treatment: TreatedCooling
    rate_policy: Literal["screen_at_strict_upper_bound","qualified_rate_below_bound"]
    owner_rate_m_year: NonNegative | None = None
    rate_selection_basis: str = Field(min_length=1)


class OtherChoice(Model):
    kind: Literal["other_material_nominal"]
    model: OtherCoolingMaterial


class CoolingRateSelection(Model):
    material: Material
    assessment_distribution: Distribution
    selection_basis: str = Field(min_length=1)
    measurement: CoolingMeasurement | None = None
    fallback: FreshChoice | SeawaterChoice | TreatmentChoice | OtherChoice | None = Field(default=None,discriminator="kind")


@calculation("damage/cooling-water-rate-selection", "Select measured treated freshwater seawater or other-material cooling rate", CoolingRateSelection,
    ["Part2 §11.1.10,§11.3,Figure2.B.11.1; PDF pp401-405,414"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Qualified measured rate always selected before fallback; malformed/unrepresentative measurement errors instead of silently switching to model. Supplied fallback input structure is validated, but fallback calculation/assumption gates are not executed when measurement selected. Without measurement, explicit fallback required; no material/water/treatment guess. Model general/local representativeness must be owner-qualified. Treated strict bound is either an explicitly labeled conservative screening rate at the bound or an owner rate strictly below it, not automatic exact prediction. Main quantitative fresh/seawater models remain carbon-steel-only; other-material nominal path needs separate qualification. No all-mechanism/whole-component immunity conclusion."])
def select_rate(x):
    ensure(bool(x.selection_basis.strip()),"Rate-selection/distribution qualification basis must not be blank")
    if x.measurement is not None:
        rate,source = _measurement(x.measurement,x.assessment_distribution)
        bound,screen = None,False
    else:
        choice = x.fallback
        ensure(choice is not None,"No representative measurement or explicit model fallback supplied")
        bound,screen = None,False
        if choice.kind in ("freshwater_model","seawater_model"):
            ensure(x.material == "carbon_steel","Quantitative water models require carbon-steel material scope")
            result = fresh_assessment(choice.model) if choice.kind == "freshwater_model" else seawater_rate(choice.model)
            rate,source = result["corrosion_rate_m_year"],choice.kind
        elif choice.kind == "other_material_nominal":
            ensure(x.material == "other_material","Other-material nominal branch cannot replace carbon/low-alloy model")
            rate,source = other_material(choice.model)["nominal_corrosion_rate_m_year"],choice.kind
        else:
            ensure(x.material == choice.treatment.material,"Treatment and overall material scopes must agree")
            bounds = treatment_bounds(choice.treatment)
            bound = bounds["general_upper_bound_m_year" if x.assessment_distribution == "general" else "pitting_upper_bound_m_year"]
            ensure(bool(choice.rate_selection_basis.strip()),"Treated numerical rate selection requires owner basis")
            if choice.rate_policy == "screen_at_strict_upper_bound":
                ensure(choice.owner_rate_m_year is None,"Screening bound cannot have competing owner rate")
                rate,source,screen = bound,"treated_screening_bound",True
            else:
                ensure(choice.owner_rate_m_year is not None and choice.owner_rate_m_year < bound,"Owner treated rate must be strictly below source bound")
                rate,source = choice.owner_rate_m_year,"treated_owner_rate"
    return {"corrosion_rate_m_year":rate,"selection_source":source,"assessment_distribution":x.assessment_distribution,
        "source_strict_upper_bound_m_year":bound,"selected_rate_is_screening_bound":screen,
        "fallback_ignored_due_to_measurement":x.measurement is not None and x.fallback is not None}


class SelectedCoolingThinning(Model):
    selection: CoolingRateSelection
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/cooling-water-selected-thinning", "Selected cooling-water measured or model rate through non-AST thinning DF", SelectedCoolingThinning,
    ["Part2 Annex2.B §11,Figure2.B.11.1; Part2 §4.5.7"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same selected measured/model/bound rate drives unclad non-AST thinning; general/local classification and inspection coverage are qualified inputs. Retains screening-bound flag through final DF, never presents it as a measured rate. No second pitting multiplier, treatment credit or duplicated monitoring adjustment. Either strength-ratio method supported with same thickness baseline. Other-material nominal rate does not exclude SCC/pitting/dealloying DFs; apply other applicable mechanisms separately. No AST, cladding, bundle or all-mechanism/whole-system risk assessment."])
def selected_thinning(x):
    rate = select_rate(x.selection)
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=rate["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**rate,**result}
