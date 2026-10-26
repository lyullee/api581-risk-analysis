"""Qualified EOS -> rainout -> steady boiling pool -> isolated native dispersion."""
from typing import Literal
from pydantic import Field
from .core import Positive, NonNegative, calculation, ensure, REGISTRY
from .flash_solver import PureLiquidFlashPartition, pure_liquid_flash_partition
from .saturation import SaturationPressure, saturation_pressure
from .evaporation import SurfaceInteraction, BoilingSteadySource, boiling_steady_source
from .slabx_adapter import (NativeAtmosphere, NativeSubstance, NativePool, native_pool,
    NativePoolFootprint, native_pool_footprint, NativePoolFlashFire, native_pool_flash_fire)


class FlashedBoilingPool(PureLiquidFlashPartition):
    ground_temperature_k: Positive
    surface: SurfaceInteraction
    maximum_pool_area_m2: Positive
    engine: Literal['slabx','slabx-lh2']
    atmosphere: NativeAtmosphere
    receptor_height_m: NonNegative
    averaging_time_s: Positive
    plume_distance_limit_m: Positive = Field(le=1e6)
    puff_time_limit_s: Positive | None = None
    puff_steps: int = Field(default=40,ge=10,le=1000,strict=True)
    threshold_volume_fraction: Positive = Field(le=1)
    threshold_source: str = Field(min_length=1,max_length=1000)
    meander_closure: Literal['ermak','sigma_theta']
    lh2_plume_width_coupling: bool
    native_property_basis: str = Field(min_length=1,max_length=1000)
    timeout_s: Positive = Field(default=120,le=600)


_SOURCE_LIMITATIONS=[
        'Initially liquid pure fluid only, atmospheric final pressure101325Pa, positive adjusted constant rate and released mass. Boiling pool requires Tb<Tground, area support and time-to-steady shorter than mass/rate supply duration. Unsupported/zero rainout source fails explicitly.',
        'Native constant source covers ONLY the steady window after time-to-steady, not startup, growing pool, depletion, post-release evaporation or simultaneous jet. Startup pool-feed mass is explicitly unmodeled; jet masses remain separate. Native time origin is start of steady window; no combined jet/pool footprint or risk is inferred.',
        'Pure-fluid normal-boiling saturated cp, densities and latent heat map to native constant properties only with an explicit qualification basis. No fluid-wide or LH2 EOS/native model validation. Native LH2 premise and censoring still gate usable spatial results. Threshold is caller supplied, not automatically LFL/toxic.']


@calculation('dispersion/flashed-boiling-pool-centreline','Pure-liquid flash through steady boiling-pool native centreline',FlashedBoilingPool,
    ['Part3 §§5.1.3,5.7.2-5.7.4,5.8.5-5.8.6; PDF pp539-544; external SLABx dispersion'],
    origin='qualified_eos_to_steady_pool_native_composition',limitations=[
        *REGISTRY['dispersion/native-pool-centreline'].limitations,*_SOURCE_LIMITATIONS])
def flashed_boiling_pool(x):
    source,native=_prepare_flashed_boiling_pool(x)
    return {**source,**native_pool(native),'integration_scope':'flashed_pure_liquid_boiling_pool_steady_window_centreline'}


def _prepare_flashed_boiling_pool(x):
    ensure(bool(x.native_property_basis.strip()) and bool(x.threshold_source.strip()),'Native property and threshold qualification required')
    ensure(x.final_pressure_pa_abs==101325.,'Native pool integration requires atmospheric final pressure101325Pa')
    ensure(x.adjusted_mass_rate_kg_s>0 and x.released_mass_kg>0,'Positive adjusted rate and released mass required','no_source_window')
    partition=pure_liquid_flash_partition(PureLiquidFlashPartition(**x.model_dump(include=set(PureLiquidFlashPartition.model_fields))))
    ensure(partition['pool_liquid_rate_kg_s']>0,'No liquid rainout source for boiling pool','no_pool_feed')
    saturation=saturation_pressure(SaturationPressure(fluid=x.fluid,pressure_pa_abs=x.final_pressure_pa_abs,
        qualification_basis=x.qualification_basis))
    supply_duration=x.released_mass_kg/x.adjusted_mass_rate_kg_s
    pool=boiling_steady_source(BoilingSteadySource(bubble_temperature_k=saturation['bubble_temperature_k'],
        ground_temperature_k=x.ground_temperature_k,latent_heat_j_kg=saturation['latent_heat_j_kg'],surface=x.surface,
        liquid_feed_rate_kg_s=partition['pool_liquid_rate_kg_s'],pool_vapor_density_kg_m3=saturation['vapor_density_kg_m3'],
        supply_duration_s=supply_duration,maximum_pool_area_m2=x.maximum_pool_area_m2))
    ensure(pool['support_status']=='supported','Steady boiling pool unsupported: '+pool['support_status'],'pool_source_unsupported')
    start=pool['time_to_steady_s']
    duration=supply_duration-start
    ensure(x.averaging_time_s<=duration,'Averaging time exceeds supported steady-source window','unsupported_averaging_window')
    substance=NativeSubstance(fluid_id=x.fluid.casefold(),molecular_weight_kg_kmol=saturation['molecular_weight_kg_kmol'],
        vapor_heat_capacity_j_kg_k=saturation['vapor_specific_heat_j_kg_k'],liquid_heat_capacity_j_kg_k=saturation['liquid_specific_heat_j_kg_k'],
        latent_heat_j_kg=saturation['latent_heat_j_kg'],normal_boiling_point_k=saturation['bubble_temperature_k'],
        liquid_density_kg_m3=saturation['liquid_density_kg_m3'],property_source='CoolProp8.0.0 saturated normal-boiling properties; '+x.native_property_basis)
    native_keys=('engine','atmosphere','receptor_height_m','averaging_time_s','plume_distance_limit_m','puff_time_limit_s',
        'puff_steps','threshold_volume_fraction','threshold_source','meander_closure','lh2_plume_width_coupling','timeout_s')
    native=NativePool(**x.model_dump(include=set(native_keys)),substance=substance,
        vapor_source_rate_kg_s=pool['vapor_source_rate_kg_s'],source_area_m2=pool['pool_area_m2'],release_duration_s=duration,
        source_qualification='Steady boiling pool only, excludes startup/jet; '+x.atmospheric_partition_basis)
    source={**partition,**saturation,**pool,'steady_window_start_s':start,'steady_window_duration_s':duration,
        'steady_evaporated_mass_kg':pool['vapor_source_rate_kg_s']*duration,
        'startup_unmodeled_pool_mass_kg':partition['pool_liquid_rate_kg_s']*start}
    return source,native


class FlashedBoilingPoolFootprint(FlashedBoilingPool):
    crosswind_half_span_m: Positive
    crosswind_points_per_side: int = Field(default=65,ge=3,le=501,strict=True)


@calculation('dispersion/flashed-boiling-pool-footprint','Pure-liquid flash through steady boiling-pool planar footprint',FlashedBoilingPoolFootprint,
    ['Part3 §§5.7.2-5.7.4,5.8.5-5.8.6; external native planar concentration field'],
    origin='qualified_eos_to_steady_pool_native_footprint',limitations=[
        *_SOURCE_LIMITATIONS,
        *REGISTRY['dispersion/native-pool-footprint'].limitations])
def flashed_boiling_pool_footprint(x):
    source,native=_prepare_flashed_boiling_pool(x)
    footprint=native_pool_footprint(NativePoolFootprint(**native.model_dump(),
        crosswind_half_span_m=x.crosswind_half_span_m,crosswind_points_per_side=x.crosswind_points_per_side))
    return {**source,**footprint,'integration_scope':'flashed_pure_liquid_boiling_pool_steady_window_footprint'}


class FlashedBoilingPoolFlashFire(FlashedBoilingPoolFootprint):
    criterion_role: Literal['qualified_lfl']
    receptor_height_m: Literal[0.0]


@calculation('dispersion/flashed-boiling-pool-flash-fire','Pure-liquid flash through steady boiling-pool flash-fire areas',FlashedBoilingPoolFlashFire,
    ['Part3 §§5.7.2-5.7.4,5.8.6,4.8.2.3; native LFL planar field'],
    origin='qualified_eos_to_steady_pool_native_flash_fire',limitations=[
        *REGISTRY['dispersion/flashed-boiling-pool-footprint'].limitations,
        *REGISTRY['dispersion/native-pool-flash-fire'].limitations,
        'Only this selected steady pool vapor scenario. No startup/jet/post-release pool consequence or ignition/GFF weighting. LFL declaration and averaging require owner qualification; no automatic criterion lookup or final risk.'])
def flashed_boiling_pool_flash_fire(x):
    source,native=_prepare_flashed_boiling_pool(x)
    consequence=native_pool_flash_fire(NativePoolFlashFire(**native.model_dump(),
        crosswind_half_span_m=x.crosswind_half_span_m,crosswind_points_per_side=x.crosswind_points_per_side,
        criterion_role=x.criterion_role))
    return {**source,**consequence,'integration_scope':'flashed_pure_liquid_boiling_pool_steady_window_flash_fire'}
