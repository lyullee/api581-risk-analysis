"""Unignited pool -> qualified equilibrium vapor source, without a dispersion run."""
from api581 import Context
from api581.api import properties, release


def main():
    context=Context(asset_id="illustrative-unignited-pool",source_revision="pool-vapor-inputs-1")
    ground=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface="concrete"),context=context)
    boiling=release.boiling_pool_steady_source(release.BoilingPoolSteadySourceInput(
        bubble_temperature_k=250,ground_temperature_k=300,latent_heat_j_kg=300000,
        surface=release.SurfaceInteractionInput(**ground.outputs.model_dump()),liquid_feed_rate_kg_s=1,
        pool_vapor_density_kg_m3=2,supply_duration_s=100,maximum_pool_area_m2=1000),context=context)
    nonboiling=release.nonboiling_pool_steady_source(release.NonboilingPoolSteadySourceInput(
        bubble_temperature_k=350,ground_temperature_k=300,storage_temperature_k=310,
        bubble_pressure_at_ground_pa_abs=10000,molecular_weight_kg_kmol=100,wind_speed_m_s=2,
        liquid_feed_rate_kg_s=.05,maximum_pool_area_m2=1000),context=context)
    unsupported=release.boiling_pool_steady_source(release.BoilingPoolSteadySourceInput(
        bubble_temperature_k=250,ground_temperature_k=300,latent_heat_j_kg=300000,
        surface=release.SurfaceInteractionInput(**ground.outputs.model_dump()),liquid_feed_rate_kg_s=1,
        pool_vapor_density_kg_m3=2,supply_duration_s=.001,maximum_pool_area_m2=.001),context=context)
    print("Boiling support/time/radius/source:",boiling.outputs.support_status,boiling.outputs.time_to_steady_s,
          boiling.outputs.pool_radius_m,boiling.outputs.vapor_source_rate_kg_s)
    print("Non-boiling support/radius/source:",nonboiling.outputs.support_status,nonboiling.outputs.pool_radius_m,
          nonboiling.outputs.vapor_source_rate_kg_s)
    print("Unsupported equilibrium source:",unsupported.outputs.support_status,unsupported.outputs.vapor_source_rate_kg_s)
    print("Illustrative properties; no transient pool, flash/EOS, LH2 validation or dispersion execution.")
    return boiling,nonboiling,unsupported


if __name__ == "__main__":
    main()
