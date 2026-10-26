"""Illustrative total-release TNT equivalence -> blast damage areas.

Numerically admissible fit interval is supplied explicitly; experimental validity
and LH2 applicability are not established by this example.
"""
from api581 import Context
from api581.api import effects


def main():
    result=effects.vce_blast_consequence(effects.VceBlastConsequenceInput(
        flammable_cloud_mass_kg=1000,combustion_heat_j_kg=46e6,explosion_yield=.03,
        tnt_heat_j_kg=4.648e6,tnt_heat_source="Illustrative caller-selected4.648MJ/kg; printed SI value is inconsistent",
        mass_basis="total_released_flammable",yield_engineering_basis="Illustrative hydrocarbon total-release yield per5.8.5.4",
        personnel_building_collapse_probability=.5,
        fit_domain=effects.BlastFitDomainInput(minimum_scaled_distance_m_kg13=1.5,
            maximum_scaled_distance_m_kg13=1000,
            engineering_basis="Illustrative numerical bracket only; experimental fit validity requires engineering qualification")),
        context=Context(asset_id="illustrative-vce",source_revision="blast-inputs-1"))
    print("TNT equivalent mass (kg):",result.outputs.tnt_equivalent_mass_kg)
    print("Personnel building-collapse target pressure (Pa):",result.outputs.personnel_threshold_overpressure_pa)
    print("Personnel distance/area (m,m2):",result.outputs.personnel_safe_distance_m,result.outputs.personnel_area_m2)
    print("Equipment distance/area (m,m2):",result.outputs.equipment_safe_distance_m,result.outputs.equipment_area_m2)
    return result


if __name__ == "__main__":
    main()
