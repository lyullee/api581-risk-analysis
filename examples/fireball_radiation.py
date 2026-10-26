"""Import-only fireball calculation: illustrative hydrocarbon, no LH2 validation."""
from api581 import Context
from api581.api import effects, properties


def main():
    context=Context(asset_id="illustrative-rupture",source_revision="fireball-inputs-1")
    water=properties.water_partial_pressure(properties.WaterPartialPressureInput(
        ambient_temperature_k=300,relative_humidity_fraction=.5),context=context)
    result=effects.fireball_consequence(effects.FireballConsequenceInput(
        available_mass_kg=2000,flammable_mass_fraction=.5,heat_of_combustion_j_kg=46e6,
        burst_pressure_pa_abs=1e6,
        atmosphere=effects.AtmosphereInput(transmissivity_model="api_water_vapor",
            water_partial_pressure_pa=water.outputs.water_partial_pressure_pa),
        geometry_basis="elevated_sphere_maximum",maximum_distance_m=1000),context=context)
    print("Fireball mass/diameter/duration (kg,m,s):",result.outputs.flammable_mass_kg,
          result.outputs.diameter_m,result.outputs.duration_s)
    print("Personnel distance/area/status:",result.outputs.personnel_safe_distance_m,
          result.outputs.personnel_area_m2,result.outputs.personnel_status)
    print("Equipment distance/area/status:",result.outputs.equipment_safe_distance_m,
          result.outputs.equipment_area_m2,result.outputs.equipment_status)
    print("Selected geometry:",result.outputs.geometry_basis)
    return result


if __name__ == "__main__":
    main()
