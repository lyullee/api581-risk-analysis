"""Optional installed native engines; no area inferred from centreline distance."""
import argparse
from api581 import Context
from api581.api import dispersion


def request(engine="slabx"):
    hydrogen = engine == "slabx-lh2"
    return dispersion.NativePoolCentrelineInput(
        engine=engine,substance=dict(fluid_id="hydrogen" if hydrogen else "methane",
            molecular_weight_kg_kmol=2.016 if hydrogen else 16.043,
            vapor_heat_capacity_j_kg_k=14300. if hydrogen else 2238.,
            liquid_heat_capacity_j_kg_k=9700. if hydrogen else 3348.5,
            latent_heat_j_kg=445000. if hydrogen else 509900.,normal_boiling_point_k=20.3 if hydrogen else 111.7,
            liquid_density_kg_m3=70.8 if hydrogen else 424.1,property_source="Explicit illustrative constant-property fixture"),
        atmosphere=dict(wind_speed_m_s=5. if hydrogen else 1.94,wind_reference_height_m=10. if hydrogen else 3.,
            temperature_k=293. if hydrogen else 290.,pressure_pa_abs=101325.,relative_humidity_fraction=.5,
            roughness_length_m=.01 if hydrogen else .0002,stability="D" if hydrogen else "E"),
        vapor_source_rate_kg_s=.1 if hydrogen else 116.93,source_area_m2=1. if hydrogen else 116.93/.167,
        release_duration_s=60. if hydrogen else 107.,receptor_height_m=1.,averaging_time_s=1. if hydrogen else 80.,
        plume_distance_limit_m=300. if hydrogen else 2000.,threshold_volume_fraction=.04 if hydrogen else .05,
        threshold_source="Qualified example concentration criterion; no regulatory endpoint claim",
        source_qualification="Ground-level pure vapor at normal boiling point; constant finite release fixture",
        meander_closure="ermak",lh2_plume_width_coupling=hydrogen)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine",choices=("slabx","slabx-lh2"),default="slabx")
    args = parser.parse_args()
    result = dispersion.native_pool_centreline(request(args.engine),context=Context(asset_id="native-pool-fixture"))
    output = result.outputs
    print("Native versions:",output.engine_versions)
    print("Native nodes:",len(output.downwind_distance_m))
    print("Threshold:",output.threshold_status,output.threshold_distance_m)
    print("LH2 premise:",output.premise_status,output.maximum_vertical_to_horizontal_velocity_ratio)
    print("Spatial scope:",output.spatial_output_scope)


if __name__ == "__main__":
    main()
