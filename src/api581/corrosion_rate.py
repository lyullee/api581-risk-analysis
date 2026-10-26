"""Measured corrosion-rate primitives from API 581 thinning guidance."""

from pydantic import Field

from .core import Model, Positive, NonNegative, calculation, ensure


class MeasuredCorrosionRate(Model):
    initial_thickness_m: Positive
    current_thickness_m: Positive
    elapsed_years: Positive
    measurement_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "damage/measured-corrosion-rate",
    "Measured thickness-loss corrosion rate",
    MeasuredCorrosionRate,
    ["Part 2 Annex B §1.1-§1.2; Part 2 §4.5.5, PDF pp143-152"],
    origin="api581_measured_thickness_loss_rate",
    limitations=[
        "Computes the direct constant-rate interpretation (initial thickness minus current thickness divided by elapsed time). It does not select inspection history, uncertainty distributions, mechanism applicability or a future thinning rate.",
        "Thickness increase is rejected as a measurement/baseline inconsistency rather than silently converted to zero corrosion. The caller must qualify comparable locations, units, dates and measurement quality."
    ],
)
def measured_corrosion_rate(x):
    ensure(x.current_thickness_m <= x.initial_thickness_m,
           "Current thickness cannot exceed the qualified initial thickness", "inconsistent_thickness_baseline")
    loss = x.initial_thickness_m - x.current_thickness_m
    return {
        "metal_loss_m": loss,
        "corrosion_rate_m_year": loss / x.elapsed_years,
        "initial_thickness_m": x.initial_thickness_m,
        "current_thickness_m": x.current_thickness_m,
        "elapsed_years": x.elapsed_years,
        "measurement_basis": x.measurement_basis,
        "rate_basis": "direct_two_thickness_difference",
    }
