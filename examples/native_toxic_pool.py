"""Historical2016 probit50 -> native TWA toxic screening; illustrative inputs."""
from api581 import Context
from api581.api import dispersion


def request():
    return dispersion.NativePoolToxicConsequenceInput(
        criterion=dict(fluid_id="chlorine",exposure_duration_s=600.,
            candidate_availability_basis="Historical Table4.14 plus qualified application review fixture"),
        source=dict(substance=dict(fluid_id="chlorine",molecular_weight_kg_kmol=70.906,
            vapor_heat_capacity_j_kg_k=479.,liquid_heat_capacity_j_kg_k=950.,latent_heat_j_kg=287000.,
            normal_boiling_point_k=239.11,liquid_density_kg_m3=1467.,property_source="Illustrative qualified constant-property fixture"),
            atmosphere=dict(wind_speed_m_s=3.,wind_reference_height_m=10.,temperature_k=293.,pressure_pa_abs=101325.,
                relative_humidity_fraction=.5,roughness_length_m=.01,stability="D"),
            vapor_source_rate_kg_s=1.,source_area_m2=10.,available_mass_kg=1200.,detection_maximum_duration_s=600.,
            receptor_height_m=0.,plume_distance_limit_m=5000.,crosswind_half_span_m=500.,crosswind_points_per_side=129,
            source_qualification="Qualified pure-species normal-boiling finite constant vapor-pool fixture",meander_closure="ermak"),
        non_ignition_probability=.8,exposure_model_basis="constant_exposure_equivalent_native_time_average")


def main():
    r = dispersion.native_pool_toxic_consequence(request(),context=Context(asset_id="native-toxic-pool-fixture")).outputs
    print("Selected historical criterion:",r.selected_criterion_id,r.pure_component_limit_ppm,"ppm")
    print("Release/exposure/average s:",r.release_duration_s,r.exposure_duration_s,r.averaging_time_s)
    print("Footprint:",r.footprint_status,r.threshold_area_m2)
    print("Conditional toxic equipment/personnel area:",r.equipment_area_m2,r.personnel_area_m2)
    print("Exposure interpretation:",r.exposure_model_basis)


if __name__ == "__main__":
    main()
