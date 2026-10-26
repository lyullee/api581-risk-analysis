"""Conservative two-phase orifice -> controls -> rainout -> jet/pool handoff.

Flash fractions, fluid properties and controls are explicit fixture assumptions;
the draft dispersion request is prepared, not sent to an engine.
"""
from api581 import Context
from api581.api import release, properties
from api581.dispersion import DispersionRequest, SourcePoint, capabilities


def main():
    context=Context(asset_id="illustrative-flashing-mixture",source_revision="partition-inputs-1")
    source=release.level2_orifice_rate(release.Level2OrificeRateInput(diameter_m=.0254,
        storage_pressure_pa_abs=1e6,saturation_pressure_at_storage_pa_abs=5e5,liquid_density_kg_m3=700),context=context)
    controlled=release.magnitude(release.MagnitudeInput(theoretical_rate_kg_s=source.outputs.mass_rate_kg_s,
        reduction_fraction=.15,available_mass_kg=5000,maximum_duration_s=600),context=context)
    rainout=release.kletz_rainout_fraction(release.KletzRainoutFractionInput(flash_mass_fraction=.25),context=context)
    partition=release.level2_source_partition(release.Level2SourcePartitionInput(
        adjusted_mass_rate_kg_s=controlled.outputs.adjusted_rate_kg_s,released_mass_kg=controlled.outputs.released_mass_kg,
        rainout_mass_fraction=rainout.outputs.rainout_mass_fraction,equation_basis="post_flash_mass_balance",
        post_flash_vapor_mass_fraction=.25,rainout_basis_source="API581 eq3.98 with illustrative flash fraction.25",
        flash_property_source="Owner-supplied illustrative post-flash total vapor fraction, not EOS execution"),context=context)
    ground=properties.pool_surface_interaction(properties.PoolSurfaceInteractionInput(surface="concrete"),context=context)
    pool=release.boiling_pool_steady_source(release.BoilingPoolSteadySourceInput(bubble_temperature_k=250,ground_temperature_k=300,
        latent_heat_j_kg=300000,surface=release.SurfaceInteractionInput(**ground.outputs.model_dump()),
        liquid_feed_rate_kg_s=partition.outputs.pool_liquid_rate_kg_s,pool_vapor_density_kg_m3=2,
        supply_duration_s=controlled.outputs.duration_s,maximum_pool_area_m2=1000),context=context)
    request=DispersionRequest(context=context,engine="slabx",fluid_id="illustrative-mixture",release_height_m=1,
        wind_speed_m_s=2,wind_reference_height_m=10,ambient_temperature_k=300,
        source_profile=[SourcePoint(time_s=t,mass_rate_kg_s=partition.outputs.jet_total_rate_kg_s,
            temperature_k=250,vapor_mass_fraction=partition.outputs.jet_vapor_mass_fraction)
            for t in [0,controlled.outputs.duration_s]],requested_outputs=["concentration_field","flammable_cloud_mass"])
    print("Orifice phase/method:",source.outputs.release_phase,source.outputs.rate_method)
    print("Pool/jet-total/vapor/aerosol rates:",partition.outputs.pool_liquid_rate_kg_s,partition.outputs.jet_total_rate_kg_s,
        partition.outputs.jet_vapor_rate_kg_s,partition.outputs.jet_liquid_rate_kg_s)
    print("Pool evaporation support/source:",pool.outputs.support_status,pool.outputs.vapor_source_rate_kg_s)
    print("Prepared draft jet dispersion request:",request.engine,request.source_profile[0].vapor_mass_fraction)
    print("Engine states:",[(c["engine"],c["status"]) for c in capabilities()])
    return partition,request


if __name__ == "__main__":
    main()
