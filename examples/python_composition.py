"""Direct function composition for a host project or a digital twin."""
import _bootstrap  # noqa: F401
from api581 import Context, describe
from api581.api import effects, frequency


def main():
    context = Context(asset_id="pipe-001", source_revision="example-1")
    management = frequency.management_factor(frequency.ManagementFactorInput(score=500), context=context)
    print("Management factor:", management.outputs.management_factor)
    power = effects.jet_fire_power(effects.JetFirePowerInput(
        mass_rate_kg_s=10, heat_of_combustion_j_kg=46e6), context=context)
    distance = effects.jet_fire_distance(effects.JetFireDistanceInput(
        radiated_power_w=power.outputs.radiated_power_w,
        threshold_w_m2=12600, transmissivity_model="constant",
        atmospheric_transmissivity=.8), context=context)
    print("Threshold distance (m):", distance.outputs.threshold_distance_m)
    print("Area (m2):", distance.outputs.consequence_area_m2)
    print("References:", distance.references)
    print("Limitations:", distance.limitations)
    print("Input schema:", describe("release/gas").input_type.model_json_schema())
    assert distance.model_dump(mode="json")["context"]["asset_id"] == "pipe-001"


if __name__ == "__main__":
    main()
