"""External-engine contracts. No simulated dispersion result is returned."""
from typing import Literal, Protocol
from pydantic import Field, model_validator
from .core import Model, Context, NonNegative, Positive, Fraction, DomainError


class SourcePoint(Model):
    time_s: NonNegative
    mass_rate_kg_s: NonNegative
    temperature_k: Positive
    vapor_mass_fraction: Fraction


class DispersionRequest(Model):
    schema_version: Literal["1.0"] = "1.0"
    context: Context = Field(default_factory=Context)
    engine: Literal["slabx", "slabx-lh2"]
    fluid_id: str = Field(min_length=1, max_length=100)
    release_height_m: NonNegative
    wind_speed_m_s: NonNegative
    wind_reference_height_m: Positive
    ambient_temperature_k: Positive
    source_profile: list[SourcePoint] = Field(min_length=1, max_length=10000)
    requested_outputs: list[Literal["concentration_field", "lfl_area", "flammable_cloud_mass"]] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def times(self):
        if self.source_profile[0].time_s != 0 or any(b.time_s <= a.time_s for a, b in zip(self.source_profile, self.source_profile[1:])):
            raise ValueError("Profile must start at 0 and have strictly increasing times")
        return self


class DispersionProvider(Protocol):
    def capabilities(self) -> dict: ...
    def run(self, request: DispersionRequest) -> dict: ...


def capabilities():
    return [{"engine": name, "status": "not_configured", "available": False,
             "reason": "Draft variable-profile/area contract is unmapped; use separate api581.api.dispersion.native_pool_centreline for the verified constant vapor pool contract",
             "contract_status": "draft_requires_engine_mapping"} for name in ("slabx", "slabx-lh2")]


def execute(request: DispersionRequest):
    raise DomainError("engine_not_configured", f"{request.engine} is not configured; no fallback model was used")
