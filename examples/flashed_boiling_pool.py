"""Requires [flash,slabx]: qualified propane steady-window centreline example."""
from api581 import Context
from api581.api import dispersion, properties


def request(**changes):
    surface=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface='concrete')).outputs
    return dispersion.FlashedBoilingPoolCentrelineInput(**(dict(
        fluid='Propane',storage_pressure_pa_abs=1e6,storage_temperature_k=300.,final_pressure_pa_abs=101325.,
        method='isentropic',qualification_basis='Pure-propane EOS demonstration; not site validation',
        adjusted_mass_rate_kg_s=2.,released_mass_kg=120.,equation_basis='post_flash_mass_balance',
        atmospheric_partition_basis='Qualified illustrative Kletz rainout and constant feed; no startup/jet dispersion',
        ground_temperature_k=300.,surface=surface.model_dump(),maximum_pool_area_m2=10000.,
        engine='slabx',atmosphere=dict(wind_speed_m_s=3.,wind_reference_height_m=10.,temperature_k=300.,
            pressure_pa_abs=101325.,relative_humidity_fraction=.5,roughness_length_m=.01,stability='D'),
        receptor_height_m=1.,averaging_time_s=1.,plume_distance_limit_m=1000.,puff_steps=40,
        threshold_volume_fraction=.0001,threshold_source='Illustrative100ppmv concentration; not LFL/toxic criterion',
        meander_closure='ermak',lh2_plume_width_coupling=False,
        native_property_basis='Owner-qualified demonstration of constant saturated normal-boiling EOS properties',timeout_s=120.)|changes))


def main():
    output=dispersion.flashed_boiling_pool_centreline(request(),context=Context(
        asset_id='propane-steady-pool-demonstration',source_revision='qualified-eos-steady-window-v1')).outputs
    print('Steady window start/duration:',output.steady_window_start_s,output.steady_window_duration_s)
    print('Steady evaporated/startup unmodeled pool mass:',output.steady_evaporated_mass_kg,output.startup_unmodeled_pool_mass_kg)
    print('Separate jet mass:',output.jet_total_mass_kg)
    print('Native threshold:',output.threshold_status,output.threshold_distance_m)
    print('Engine provenance:',output.engine_versions)
    return output


if __name__=='__main__':
    main()
