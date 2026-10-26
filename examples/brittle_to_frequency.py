"""Brittle DF -> governing DF -> frequency using only Python functions.

Illustrative qualified inputs, not an automatic material/CET assessment.
"""
from api581 import Context
from api581.api import damage, frequency


def main():
    context = Context(asset_id="example-vessel", source_revision="brittle-example-1")
    reference = damage.BrittleReferenceTemperatureInput(material_group="carbon_steel",
        minimum_yield_strength_pa=40*6894757.293168, exemption_curve="B", interpolation="exact")
    service = damage.BrittleServiceFactorInput(component_thickness_m=.0508,
        nominal_uncorroded_thickness_m=.0508, equipment_type="pressure_vessel",
        p1_or_p3_steel=True, design_temperature_k=600, construction_code_satisfied=True,
        stable_conditions_no_more_severe_future=True, cet_at_mawp_k=277.59444444444443,
        cyclic_fatigue_or_vibration_design_service=False, environmental_cracking=False, shock_chilling=False)
    brittle = damage.brittle_fracture(damage.BrittleFractureInput(reference=reference, service=service,
        critical_exposure_temperature_k=277.59444444444443, post_weld_heat_treated=False,
        interpolation="exact"), context=context)
    # This example explicitly declares the other mechanisms inapplicable/zero.
    combined = damage.combine(damage.CombineInput(thinning=0, external=[], scc=[], htha=0, fatigue=0,
        brittle_fracture=brittle.outputs.damage_factor, temper_embrittlement=0,
        embrittlement_885f=0, sigma_embrittlement=0, thinning_external_distribution="local"), context=context)
    generic = frequency.generic(frequency.GenericInput(component_type="DRUM"), context=context)
    result = frequency.adjusted(frequency.AdjustedInput(
        generic_frequency_per_year=generic.outputs.total_per_year,
        total_damage_factor=combined.outputs.total_damage_factor, management_factor=1), context=context)
    print("Brittle damage factor:", brittle.outputs.damage_factor)
    print("Annual failure frequency:", result.outputs.annual_failure_frequency)
    print("Brittle calculation limitations:", brittle.limitations)


if __name__ == "__main__":
    main()
