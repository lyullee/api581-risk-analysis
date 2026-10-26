"""Part 2 §21 low-alloy temper embrittlement; unresolved correlations stay explicit."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from .core import Model, NonNegative, Positive, calculation, ensure
from .brittle import BrittleReference, BrittleBase, Interpolation, brittle_reference, brittle_base

WeightPercent = Annotated[float, Field(ge=0, le=100, strict=True, allow_inf_nan=False)]


class JComposition(Model):
    silicon_weight_percent: WeightPercent
    manganese_weight_percent: WeightPercent
    phosphorus_weight_percent: WeightPercent
    tin_weight_percent: WeightPercent

    @model_validator(mode="after")
    def total(self):
        if sum((self.silicon_weight_percent,self.manganese_weight_percent,
                self.phosphorus_weight_percent,self.tin_weight_percent)) > 100:
            raise ValueError("Composition weight percentages exceed 100")
        return self


@calculation("damage/temper-j-factor", "Temper embrittlement composition J factor", JComposition,
             ["Part 2 §21.2; eq (2.87); PDF p273"],
             limitations=["Inputs are numerical weight percentages, not 0-1 fractions. Correlation for 2.25Cr-1Mo/3Cr-1Mo susceptibility; factor alone does not determine DF. Printed eq (2.90) has an unresolved 10^4 exponent; automatic J-to-temperature-shift conversion is not enabled."])
def temper_j_factor(x):
    return {"j_factor": (x.silicon_weight_percent+x.manganese_weight_percent)*
            (x.phosphorus_weight_percent+x.tin_weight_percent)*1e4}


class XbarComposition(Model):
    phosphorus_weight_percent: WeightPercent
    antimony_weight_percent: WeightPercent
    tin_weight_percent: WeightPercent
    arsenic_weight_percent: WeightPercent

    @model_validator(mode="after")
    def total(self):
        if sum((self.phosphorus_weight_percent,self.antimony_weight_percent,
                self.tin_weight_percent,self.arsenic_weight_percent)) > 100:
            raise ValueError("Composition weight percentages exceed 100")
        return self


@calculation("damage/temper-xbar", "Temper embrittlement composition X-bar factor", XbarComposition,
             ["Part 2 §21.2; eq (2.88); PDF p273"],
             limitations=["Inputs are numerical weight percentages, not fractions or ppm. Owner qualifies applicability to 1.25Cr-0.5Mo/1Cr-0.5Mo alloys."])
def temper_xbar(x):
    return {"xbar_factor": (10*x.phosphorus_weight_percent+5*x.antimony_weight_percent+
            4*x.tin_weight_percent+x.arsenic_weight_percent)*100}


class XbarShift(Model):
    xbar_factor: NonNegative


@calculation("damage/temper-xbar-shift", "X-bar long-term FATT temperature shift", XbarShift,
             ["Part 2 §21.6.3 STEP 4(3); eq (2.91); §21.7; PDF pp274-275"],
             limitations=["Equation output is a Celsius temperature difference, hence numerically K, per §21.7. Negative predicted shifts are rejected; no implicit zero clipping. Long-term empirical relation; material and exposure applicability require owner qualification."])
def temper_xbar_shift(x):
    shift = -87.335+11.437*x.xbar_factor-.1472*x.xbar_factor**2
    ensure(shift >= 0, "X-bar correlation gives a negative embrittlement shift; supply qualified measured/engineering shift", "outside_correlation_domain")
    return {"delta_fatt_k": shift}


class GenerationShift(Model):
    fabrication_year: int = Field(strict=True, ge=1965)
    source_basis: Literal["printed_C", "printed_F_difference_converted"]


@calculation("damage/temper-generation-shift", "Fabrication-era conservative FATT shift", GenerationShift,
             ["Part 2 §21.6.3 STEP 4(4); PDF p274"],
             limitations=["Printed paired C/F shifts are inconsistent as temperature differences. Caller must choose printed_C or printed_F_difference_converted explicitly; this choice is preserved in output. The text says after 1988 and the preceding band ends 1987: year 1988 is rejected. No pre-1965 rule."])
def temper_generation_shift(x):
    ensure(x.fabrication_year != 1988, "Year 1988 is not uniquely assigned by printed generation bands", "unresolved_applicability")
    if x.fabrication_year >= 1989: generation, c, f = 4,66,150
    elif x.fabrication_year >= 1981: generation, c, f = 3,121,250
    elif x.fabrication_year >= 1973: generation, c, f = 2,149,300
    else: generation, c, f = 1,177,350
    return {"generation": generation, "delta_fatt_k": c if x.source_basis == "printed_C" else f*5/9,
            "source_basis": x.source_basis}


class TemperDamage(Model):
    reference: BrittleReference
    minimum_pressurization_temperature_k: Positive
    delta_fatt_k: NonNegative
    component_thickness_m: Positive
    post_weld_heat_treated: bool = Field(strict=True)
    interpolation: Interpolation


@calculation("damage/temper-embrittlement", "Low-alloy temper embrittlement damage factor", TemperDamage,
             ["Part 2 §21.6.3 STEP 3-6; Tables 20.3,20.4M,20.5M; PDF pp274-275"],
             limitations=["Owner qualifies susceptible alloy/exposure and minimum pressurization temperature. Uses supplied measured/qualified delta-FATT; no automatic ambiguous SCE or J-factor shift. No service-experience reduction or inspection credit is specified in §21 STEP 6, and neither is applied. US reference table converted to SI, printed SI base-DF grids; no extrapolation."])
def temper_damage(x):
    ensure(x.reference.material_group == "low_alloy_steel", "Temper model requires low-alloy-steel reference table")
    reference = brittle_reference(x.reference)
    shifted = reference["reference_temperature_k"]+x.delta_fatt_k
    delta = x.minimum_pressurization_temperature_k-shifted
    base = brittle_base(BrittleBase(component_thickness_m=x.component_thickness_m,
        cet_minus_reference_k=delta,post_weld_heat_treated=x.post_weld_heat_treated,interpolation=x.interpolation))
    return {**reference,"shifted_reference_temperature_k":shifted,"minimum_minus_shifted_reference_k":delta,
            "delta_fatt_k":x.delta_fatt_k,"damage_factor":base["base_damage_factor"],"table":base["table"]}
