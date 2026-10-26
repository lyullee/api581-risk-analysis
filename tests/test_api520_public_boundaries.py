"""Direct public evaluate() coverage for each API 520 primitive."""

from api581 import evaluate


def test_api520_all_public_boundaries():
    assert evaluate("api520/critical-pressure-ratio", {"heat_capacity_ratio": 1.4})["outputs"]["critical_pressure_ratio"] > 0
    assert evaluate("api520/flow-coefficient-c", {"heat_capacity_ratio": 1.4})["outputs"]["flow_coefficient_c"] > 0
    assert evaluate("api520/relieving-pressure", {"set_pressure_psig": 75.0, "allowable_overpressure_fraction": 0.1})["outputs"]["relieving_pressure_psig"] > 0
    gas = {"required_mass_flow_kg_h": 1000.0, "relieving_temperature_k": 400.0, "compressibility_factor": 1.0, "molecular_weight_kg_kmol": 30.0, "relief_pressure_kpaa": 700.0, "heat_capacity_ratio": 1.3}
    assert evaluate("api520/gas-critical-area", gas)["outputs"]["required_area_mm2"] > 0
    sub = dict(gas, downstream_pressure_kpaa=500.0)
    assert evaluate("api520/gas-subcritical-area", sub)["outputs"]["required_area_mm2"] > 0
    liquid = {"required_flow_l_min": 1000.0, "specific_gravity": 0.9, "set_pressure_kpag": 1800.0}
    assert evaluate("api520/liquid-area", liquid)["outputs"]["required_area_mm2"] > 0
    assert evaluate("api520/liquid-viscosity-factor", {"reynolds_number": 4525.0})["outputs"]["viscosity_factor"] > 0
    gas_capacity = {k: v for k, v in gas.items() if k != "required_mass_flow_kg_h"}
    sub_capacity = {k: v for k, v in sub.items() if k != "required_mass_flow_kg_h"}
    liquid_capacity = {k: v for k, v in liquid.items() if k != "required_flow_l_min"}
    assert evaluate("api520/gas-critical-capacity", dict(gas_capacity, effective_area_mm2=100.0))["outputs"]["mass_capacity_kg_h"] > 0
    assert evaluate("api520/gas-subcritical-capacity", dict(sub_capacity, effective_area_mm2=100.0))["outputs"]["mass_capacity_kg_h"] > 0
    assert evaluate("api520/liquid-capacity", dict(liquid_capacity, effective_area_mm2=100.0))["outputs"]["flow_capacity_l_min"] > 0

