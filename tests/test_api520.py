import math

from api581 import evaluate


def out(identifier, inputs):
    return evaluate(identifier, inputs)["outputs"]


def test_api520_critical_ratio_and_coefficient_anchor():
    ratio = out("api520/critical-pressure-ratio", {"heat_capacity_ratio": 1.4})["critical_pressure_ratio"]
    coeff = out("api520/flow-coefficient-c", {"heat_capacity_ratio": 1.4})["flow_coefficient_c"]
    assert math.isclose(ratio, 0.52828, rel_tol=2e-4)
    assert math.isclose(coeff, 356.06, rel_tol=2e-4)


def test_api520_relief_pressure_and_gas_example():
    pressure = out("api520/relieving-pressure", {
        "set_pressure_psig": 75.0, "allowable_overpressure_fraction": 0.10,
    })
    assert math.isclose(pressure["relieving_pressure_psig"], 82.5)
    assert math.isclose(pressure["relieving_pressure_kpaa"], 670.14, rel_tol=5e-4)
    area = out("api520/gas-critical-area", {
        "required_mass_flow_kg_h": 24260.0,
        "relieving_temperature_k": 348.0,
        "compressibility_factor": 0.84,
        "molecular_weight_kg_kmol": 65.0,
        "relief_pressure_kpaa": 670.0,
        "heat_capacity_ratio": 1.09,
    })["required_area_mm2"]
    assert math.isclose(area, 3179.0, rel_tol=0.02)


def test_api520_subcritical_and_liquid_primitives():
    sub = out("api520/gas-subcritical-area", {
        "required_mass_flow_kg_h": 1000.0, "relieving_temperature_k": 400.0,
        "compressibility_factor": 1.0, "molecular_weight_kg_kmol": 30.0,
        "relief_pressure_kpaa": 700.0, "heat_capacity_ratio": 1.3,
        "downstream_pressure_kpaa": 500.0,
    })
    assert 0 < sub["back_pressure_ratio"] < 1
    assert sub["required_area_mm2"] > 0
    liquid = out("api520/liquid-area", {
        "required_flow_l_min": 6814.0, "specific_gravity": 0.9,
        "set_pressure_kpag": 1896.0, "back_pressure_kpag": 345.0,
        "back_pressure_factor": 0.97,
    })["required_area_mm2"]
    assert math.isclose(liquid, 3066.0, rel_tol=0.01)
    kv = out("api520/liquid-viscosity-factor", {"reynolds_number": 4525.0})["viscosity_factor"]
    assert math.isclose(kv, 0.964, rel_tol=0.002)


def test_api520_inverse_capacity_round_trips():
    gas = {
        "required_mass_flow_kg_h": 24260.0, "relieving_temperature_k": 348.0,
        "compressibility_factor": 0.84, "molecular_weight_kg_kmol": 65.0,
        "relief_pressure_kpaa": 670.0, "heat_capacity_ratio": 1.09,
    }
    area = out("api520/gas-critical-area", gas)["required_area_mm2"]
    capacity = out("api520/gas-critical-capacity", {k: v for k, v in gas.items()
        if k != "required_mass_flow_kg_h"} | {"effective_area_mm2": area})
    assert math.isclose(capacity["mass_capacity_kg_h"], gas["required_mass_flow_kg_h"], rel_tol=1e-12)
    liquid = {
        "required_flow_l_min": 6814.0, "specific_gravity": 0.9,
        "set_pressure_kpag": 1896.0, "back_pressure_kpag": 345.0,
        "back_pressure_factor": 0.97,
    }
    l_area = out("api520/liquid-area", liquid)["required_area_mm2"]
    l_capacity = out("api520/liquid-capacity", {k: v for k, v in liquid.items()
        if k != "required_flow_l_min"} | {"effective_area_mm2": l_area})
    assert math.isclose(l_capacity["flow_capacity_l_min"], liquid["required_flow_l_min"], rel_tol=1e-12)
