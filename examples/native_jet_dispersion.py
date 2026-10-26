"""Qualified effective atmospheric jet fixture; not a vessel-orifice EOS model."""
import argparse
from api581 import Context
from api581.api import dispersion


def request(engine='slabx',orientation='horizontal_downwind',**changes):
    hydrogen = engine == 'slabx-lh2'
    values = dict(engine=engine,substance=dict(fluid_id='hydrogen' if hydrogen else 'propane',
        molecular_weight_kg_kmol=2.016 if hydrogen else 44.096,
        vapor_heat_capacity_j_kg_k=14300. if hydrogen else 1670.,liquid_heat_capacity_j_kg_k=9700. if hydrogen else 2500.,
        latent_heat_j_kg=445000. if hydrogen else 425000.,normal_boiling_point_k=20.3 if hydrogen else 231.,
        liquid_density_kg_m3=70.8 if hydrogen else 580.,property_source='Qualified illustrative constant-property jet fixture'),
        atmosphere=dict(wind_speed_m_s=5. if hydrogen else 3.,wind_reference_height_m=10.,temperature_k=293.,pressure_pa_abs=101325.,
            relative_humidity_fraction=.5,roughness_length_m=.01,stability='D'),
        orientation=orientation,mass_source_rate_kg_s=.1 if hydrogen else 1.,jet_exit_area_m2=.01,
        release_height_m=3.,source_temperature_k=20.3 if hydrogen else 240.,jet_liquid_mass_fraction=0.,
        temperature_basis='require_consistent',release_duration_s=60.,receptor_height_m=1.,averaging_time_s=10.,
        plume_distance_limit_m=1000.,threshold_volume_fraction=.04 if hydrogen else .02,
        threshold_source='Qualified illustrative concentration endpoint',source_qualification='Effective atmospheric exit state/area after expansion, not upstream pressure or hole geometry',
        meander_closure='ermak',lh2_plume_width_coupling=hydrogen)
    return dispersion.NativeJetCentrelineInput(**(values|changes))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine',choices=('slabx','slabx-lh2'),default='slabx')
    parser.add_argument('--orientation',choices=('horizontal_downwind','vertical_up'),default='horizontal_downwind')
    args = parser.parse_args()
    r = dispersion.native_jet_centreline(request(args.engine,args.orientation),context=Context(asset_id='native-jet-fixture')).outputs
    print('Native engine:',r.engine_versions,r.orientation)
    print('Requested/used temperature:',r.requested_source_temperature_k,r.used_source_temperature_k)
    print('Exit velocity:',r.native_exit_velocity_m_s)
    print('Endpoint:',r.threshold_status,r.threshold_distance_m)
    print('Premise:',r.premise_status,r.maximum_vertical_to_horizontal_velocity_ratio)


if __name__ == '__main__':
    main()
