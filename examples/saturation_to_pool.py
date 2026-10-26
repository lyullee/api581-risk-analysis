"""Optional [flash] dependency: equilibrium properties to two pool source APIs.

Illustrative qualified pure-fluid cases; no assertion of site applicability.
"""
from api581.api import properties, release

basis='Pure-fluid EOS demonstration; owner must qualify physical/site applicability'
for fluid in ['Propane','Water']:
    saturation=properties.pure_fluid_saturation_pressure(properties.PureFluidSaturationPressureInput(
        fluid=fluid,pressure_pa_abs=101325.,qualification_basis=basis)).outputs
    ground=300.
    regime=release.pool_evaporation_regime(release.PoolEvaporationRegimeInput(
        bubble_temperature_k=saturation.bubble_temperature_k,ground_temperature_k=ground)).outputs.regime
    common=dict(bubble_temperature_k=saturation.bubble_temperature_k,ground_temperature_k=ground,
        liquid_feed_rate_kg_s=.1,maximum_pool_area_m2=1e6)
    if regime=='boiling':
        surface=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface='concrete')).outputs
        source=release.boiling_pool_steady_source(release.BoilingPoolSteadySourceInput(**common,
            latent_heat_j_kg=saturation.latent_heat_j_kg,pool_vapor_density_kg_m3=saturation.vapor_density_kg_m3,
            surface=release.SurfaceInteractionInput(**surface.model_dump()),supply_duration_s=1e6)).outputs
    elif regime=='non_boiling':
        ground_sat=properties.pure_fluid_saturation_temperature(properties.PureFluidSaturationTemperatureInput(
            fluid=fluid,temperature_k=ground,qualification_basis=basis)).outputs
        source=release.nonboiling_pool_steady_source(release.NonboilingPoolSteadySourceInput(**common,
            bubble_pressure_at_ground_pa_abs=ground_sat.saturation_pressure_pa_abs,ambient_pressure_pa_abs=101325.,
            molecular_weight_kg_kmol=saturation.molecular_weight_kg_kmol,storage_temperature_k=300.,wind_speed_m_s=2.)).outputs
    else:
        raise RuntimeError('Equal ground/bubble temperature requires a qualified boundary decision')
    print(fluid,regime,source.model_dump())
