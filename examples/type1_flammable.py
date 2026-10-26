"""Type1 CO controlled source -> equipment/personnel flammable areas."""
from api581 import Context
from api581.api import level1, release


def main():
    result=level1.release_to_type1_flammable(level1.ReleaseToType1FlammableInput(
        source=release.GasInput(diameter_m=.0254,upstream_pressure_pa_abs=1e6,temperature_k=300,
            molecular_weight_kg_kmol=28,heat_capacity_ratio=1.4),
        operating_temperature_k=300,component_mass_kg=1000,inventory_group_mass_kg=2000,
        detection="A",isolation="A",duration_hole="medium",fluid="CO",final_release_phase="gas",
        autoignition="not_likely",mitigation_fraction=0),context=Context(asset_id="type1-example"))
    print("Theoretical/adjusted mass rate (kg/s):",result.outputs.theoretical_rate_kg_s,result.outputs.adjusted_rate_kg_s)
    print("Type1 equipment/personnel flammable area (m2):",result.outputs.equipment_area_m2,result.outputs.personnel_area_m2)
    print("No Type0 release/AIT blending applied; toxic CO consequence is a separate module.")


if __name__ == "__main__":
    main()
