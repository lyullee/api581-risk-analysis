"""API581 qualified flash/rainout partition -> actual native jet plane."""
from pathlib import Path
import runpy
from api581 import Context
from api581.api import dispersion


def main():
    factory = runpy.run_path(str(Path(__file__).with_name('native_jet_dispersion.py')))['request']
    # Source state/area has independently qualified atmospheric expansion; the
    # source-partition API does not solve an EOS or infer that exit area.
    geometry = {k:v for k,v in factory(source_temperature_k=231.).model_dump().items()
        if k not in {'mass_source_rate_kg_s','release_duration_s','jet_liquid_mass_fraction'}}
    geometry.update(crosswind_half_span_m=30.,crosswind_points_per_side=129)
    r = dispersion.partitioned_jet_footprint(dispersion.PartitionedJetFootprintInput(
        partition=dict(adjusted_mass_rate_kg_s=2.,released_mass_kg=120.,rainout_mass_fraction=.25,
            equation_basis='post_flash_mass_balance',post_flash_vapor_mass_fraction=.5,
            rainout_basis_source='Qualified illustrative rainout fixture',flash_property_source='Qualified illustrative flash fixture'),
        jet=geometry),context=Context(asset_id='partitioned-jet-fixture',source_revision='qualified-source-v1')).outputs
    print('Pool/jet rate:',r.pool_liquid_rate_kg_s,r.jet_total_rate_kg_s)
    print('Native liquid mass fraction/duration:',r.native_jet_liquid_mass_fraction,r.release_duration_s)
    print('Requested/used temperature:',r.requested_source_temperature_k,r.used_source_temperature_k)
    print('Footprint:',r.footprint_status,r.threshold_area_m2)
    print('Engine provenance:',r.engine_versions)


if __name__ == '__main__':
    main()
