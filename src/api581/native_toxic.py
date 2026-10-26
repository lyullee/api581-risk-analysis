"""Qualified historical toxic criterion -> native long-duration pure-species pool."""
from typing import Literal
from pydantic import Field, model_validator
from .core import Model, Positive, Fraction, REGISTRY, calculation, ensure, finite_tree
from .slabx_adapter import NativeSubstance, NativeAtmosphere, NativePoolFootprint, native_pool_footprint
from .toxic_criteria import ToxicCriterion, select_criterion
from .toxic_level2 import ToxicDuration, toxic_duration, ToxicCloudArea, ToxicCase, toxic_case


class ToxicPoolSource(Model):
    substance: NativeSubstance
    atmosphere: NativeAtmosphere
    vapor_source_rate_kg_s: Positive
    source_area_m2: Positive
    available_mass_kg: Positive
    detection_maximum_duration_s: Positive
    receptor_height_m: Literal[0.0]
    plume_distance_limit_m: Positive = Field(le=1e6)
    puff_time_limit_s: Positive | None = None
    puff_steps: int = Field(default=40,ge=10,le=1000,strict=True)
    crosswind_half_span_m: Positive
    crosswind_points_per_side: int = Field(default=65,ge=3,le=501,strict=True)
    source_qualification: str = Field(min_length=1,max_length=1000)
    meander_closure: Literal["ermak","sigma_theta"]
    timeout_s: Positive = Field(default=120,le=600)

    @model_validator(mode="after")
    def qualification(self):
        if not self.source_qualification.strip() or not self.substance.property_source.strip():
            raise ValueError("Source and property qualifications must be nonblank")
        return self


class NativeToxicPool(Model):
    criterion: ToxicCriterion
    source: ToxicPoolSource
    non_ignition_probability: Fraction
    exposure_model_basis: Literal["constant_exposure_equivalent_native_time_average"]


@calculation("dispersion/native-pool-toxic-consequence", "Historical toxic criterion through native pure-pool footprint and conditional toxic consequence", NativeToxicPool,
    ["Part3 §§5.9.2-5.9.6,eqs(3.186)-(3.189); PDF pp565-567", "SLABx1.0.8 native time-averaged planar field"],
    origin="api581_criterion_to_native_time_average_toxic_screen",
    limitations=[*REGISTRY["consequence/select-toxic-criterion"].limitations,
        "Pure species only: selected fluid_id must equal native substance.fluid_id and toxic mole fraction must be1. Mixture criteria remain callable independently but mixture thermodynamics/species-resolved source mapping is not inferred. Uses native slabx1.0.8 ground-level constant vapor pool with explicit properties/atmosphere/spatial grid; no automatic LH2 toxicity or asphyxiation model.",
        "Eq3.186 bounds source duration by3600s,inventory/rate,detection duration. Selected exposure window must not exceed this source duration; native averaging equals that exposure. Short pulses fail explicitly, not zero consequence. Constant-exposure-equivalent TWA is a declared engineering screening assumption: nonlinear probit dose from C(t) is not generally equal to dose from average C. Native cloud passage does not prove time-above-threshold at every receptor.",
        "Ground-level receptor height0 is required by §5.9.6. Censored/premise-invalid spatial footprints fail before toxic consequence. Valid sampled area is multiplied by non-ignition probability exactly once, with toxic equipment area0 per eq3.188. No mixture maximum, additional event/GFF weighting or actual exposure-history/dose integration beyond this single pure component. Historical criteria are not current exposure advice or model/site certification."])
def native_toxic_pool(x):
    ensure(x.criterion.toxic_mole_fraction == 1,"Native pure-pool toxic bridge requires mole fraction1","unsupported_mixture_source")
    ensure(x.criterion.fluid_id == x.source.substance.fluid_id,"Toxic species and native substance id must match","toxic_species_mismatch")
    selected = select_criterion(x.criterion)
    finite_tree(selected)
    ensure(selected["component_present"] and selected["attainable_in_mixture"],"Selected toxic criterion is not physically attainable","toxic_criterion_unattainable")
    duration = toxic_duration(ToxicDuration(available_mass_kg=x.source.available_mass_kg,
        mixture_release_rate_kg_s=x.source.vapor_source_rate_kg_s,detection_maximum_duration_s=x.source.detection_maximum_duration_s))
    ensure(duration["release_duration_s"] >= x.criterion.exposure_duration_s,
        "Source duration shorter than selected exposure window; transient exposure model required","toxic_exposure_duration_unsupported")
    values = x.source.model_dump(exclude={"available_mass_kg","detection_maximum_duration_s"})
    native = native_pool_footprint(NativePoolFootprint(**values,engine="slabx",lh2_plume_width_coupling=False,
        release_duration_s=duration["release_duration_s"],averaging_time_s=x.criterion.exposure_duration_s,
        threshold_volume_fraction=selected["threshold_volume_fraction"],threshold_source=selected["criterion_source"]))
    ensure(native["threshold_area_m2"] is not None,"Native toxic footprint unusable: "+native["footprint_status"],"dispersion_footprint_unusable")
    toxic = toxic_case(ToxicCase(components=[ToxicCloudArea(component_id=x.criterion.fluid_id,
        selected_criterion_source=selected["criterion_source"],cloud_area_m2=native["threshold_area_m2"])],
        non_ignition_probability=x.non_ignition_probability))
    return {**native,**selected,**toxic,"release_duration_s":duration["release_duration_s"],
        "release_duration_governing_limit":duration["governing_limit"],"exposure_model_basis":x.exposure_model_basis}
