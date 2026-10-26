"""Qualified liquid pool -> radiation thresholds; explicit geometric interpretation."""
from api581 import Context
from api581.api import effects, properties


def main():
    context=Context(asset_id="illustrative-liquid-pool",source_revision="pool-inputs-1")
    water=properties.water_partial_pressure(properties.WaterPartialPressureInput(
        ambient_temperature_k=300,relative_humidity_fraction=.5),context=context)
    result=effects.pool_fire_consequence(effects.PoolFireConsequenceInput(
        burning=effects.PoolBurningInput(heat_of_combustion_j_kg=46e6,latent_heat_j_kg=350000,boiling=True),
        liquid_rate_kg_s=5,available_liquid_mass_kg=5000,liquid_density_kg_m3=700,
        pool_depth_m=.005,site_maximum_area_m2=500,air_density_kg_m3=1.2,
        vapor_density_kg_m3=2,wind_speed_m_s=2,
        atmosphere=effects.AtmosphereInput(transmissivity_model="api_water_vapor",
            water_partial_pressure_pa=water.outputs.water_partial_pressure_pa),
        equation_basis="geometry_checked",distance_convention="surface_to_axis",
        maximum_surface_distance_m=1000),context=context)
    print("Water partial pressure (Pa):",water.outputs.water_partial_pressure_pa)
    print("Pool radius / flame length (m):",result.outputs.pool_radius_m,result.outputs.flame_length_m)
    print("Personnel area/status:",result.outputs.personnel_area_m2,result.outputs.personnel_status)
    print("Equipment area/status:",result.outputs.equipment_area_m2,result.outputs.equipment_status)
    print("Geometry choice:",result.outputs.equation_basis,result.outputs.distance_convention)
    print("Geometry-checked model is an explicit interpretation, not an authorized API erratum or LH2 validation.")
    return result


if __name__ == "__main__":
    main()
