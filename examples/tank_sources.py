"""AST soil/fluid -> bottom and shell inventory/rate/release volume.

Source interpretations are explicit. This is not full AST environmental COF,
damage applicability, tank GFF assessment or dynamic drainage simulation.
"""
from api581 import Context
from api581.api import tank


def main():
    context=Context(asset_id="illustrative-ast",source_revision="tank-source-inputs-1")
    fluid=tank.fluid_table(tank.FluidTableInput(fluid="gasoline"),context=context).outputs
    soil=tank.soil_table(tank.SoilTableInput(soil="coarse_sand"),context=context).outputs
    water=tank.soil_water_conductivity(tank.SoilWaterConductivityInput(**soil.model_dump(exclude={"porosity"})),context=context)
    product=tank.fluid_conductivity(tank.FluidConductivityInput(water_hydraulic_conductivity_m_day=water.outputs.water_hydraulic_conductivity_m_day,
        liquid_density_kg_m3=fluid.liquid_density_kg_m3,dynamic_viscosity_pa_s=fluid.dynamic_viscosity_pa_s,
        water_density_kg_m3=1000,water_dynamic_viscosity_pa_s=.001),context=context)
    velocity=tank.seepage_velocity(tank.SeepageVelocityInput(product_hydraulic_conductivity_m_day=product.outputs.product_hydraulic_conductivity_m_day,
        porosity=soil.porosity),context=context)
    holes=tank.bottom_hole_count(tank.BottomHoleCountInput(tank_diameter_m=61),context=context)
    inventory=tank.bottom_inventory(tank.BottomInventoryInput(tank_diameter_m=61,fill_height_m=10,liquid_density_kg_m3=fluid.liquid_density_kg_m3),context=context)
    bottom=tank.bottom_flow(tank.BottomFlowInput(hole_diameter_m=.0127,liquid_height_m=10,liquid_density_kg_m3=fluid.liquid_density_kg_m3,
        product_hydraulic_conductivity_m_day=product.outputs.product_hydraulic_conductivity_m_day,number_of_holes=holes.outputs.small_hole_count,
        has_release_prevention_barrier=False,transition_hole_basis="api581_printed"),context=context)
    detection=tank.bottom_detection_time(tank.BottomDetectionTimeInput(foundation="other",has_release_prevention_barrier=False),context=context)
    leak=tank.release_volume(tank.ReleaseVolumeInput(release_case="leak",native_rate_bbl_day=bottom.outputs.native_rate_bbl_day,
        available_volume_m3=inventory.outputs.available_volume_m3,liquid_density_kg_m3=fluid.liquid_density_kg_m3,
        detection_time_days=detection.outputs.detection_time_days),context=context)
    shell_inventory=tank.shell_course_inventory(tank.ShellCourseInventoryInput(tank_diameter_m=61,fill_height_m=10,
        liquid_density_kg_m3=fluid.liquid_density_kg_m3,course_index=2,course_height_m=2),context=context)
    shell=tank.shell_flow(tank.ShellFlowInput(hole_diameter_m=.003175,liquid_head_m=shell_inventory.outputs.available_liquid_head_m,
        liquid_density_kg_m3=fluid.liquid_density_kg_m3),context=context)
    shell_detect=tank.shell_detection_time(tank.ShellDetectionTimeInput(hole_diameter_m=.003175,diameter_boundary_basis="inch_0_125"),context=context)
    shell_leak=tank.release_volume(tank.ReleaseVolumeInput(release_case="leak",native_rate_bbl_day=shell.outputs.native_rate_bbl_day,
        available_volume_m3=shell_inventory.outputs.available_volume_m3,liquid_density_kg_m3=fluid.liquid_density_kg_m3,
        detection_time_days=shell_detect.outputs.detection_time_days),context=context)
    print("Product conductivity/seepage (m/day):",product.outputs.product_hydraulic_conductivity_m_day,velocity.outputs.seepage_velocity_m_day)
    print("Bottom flow equation/count multiplier/native bbl/day:",bottom.outputs.equation,bottom.outputs.applied_hole_multiplier,bottom.outputs.native_rate_bbl_day)
    print("Bottom leak volume/mass (m3,kg):",leak.outputs.released_volume_m3,leak.outputs.released_mass_kg)
    print("Shell leak volume/mass (m3,kg):",shell_leak.outputs.released_volume_m3,shell_leak.outputs.released_mass_kg)
    print("Printed mass=Bbl index is separate from SI mass; source choices are not authorized errata.")
    return leak,shell_leak


if __name__ == "__main__":
    main()
