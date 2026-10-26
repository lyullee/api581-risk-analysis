"""API RP 520 (7th ed., Jan 2000) pressure-relief sizing primitives.

The public functions intentionally expose the individual sizing steps so they can
be used by API 581 PRD calculations or by a digital-twin caller.  Inputs use SI
units unless a field name explicitly says ``psig``/``psia``.  This is a sizing
calculation aid; valve selection, certified capacity, two-phase DIERS methods,
and installation hydraulics remain separate engineering checks.
"""
from math import sqrt
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure


ATM_KPA = 101.325


class CriticalRatio(Model):
    heat_capacity_ratio: Positive


@calculation("api520/critical-pressure-ratio", "API 520 critical-flow pressure ratio", CriticalRatio,
             ["API RP 520 7th ed. §3.6.1.4, Eq. 3.1"],
             origin="engineering_utility",
             limitations=["Ideal-gas relation; use qualified property data for real-gas/high-pressure service."])
def critical_pressure_ratio(x):
    k = x.heat_capacity_ratio
    ensure(k > 1.0, "Heat-capacity ratio must exceed one")
    return {"critical_pressure_ratio": (2.0 / (k + 1.0)) ** (k / (k - 1.0))}


class FlowCoefficient(Model):
    heat_capacity_ratio: Positive


@calculation("api520/flow-coefficient-c", "API 520 gas/vapor flow coefficient C", FlowCoefficient,
             ["API RP 520 7th ed. §3.6.2, Eq. 3.2-3.4; Fig. 32"],
             origin="engineering_utility",
             limitations=["Ideal-gas coefficient; API 520 recommends qualified data or C=315 when k is unavailable."])
def flow_coefficient_c(x):
    k = x.heat_capacity_ratio
    ensure(k > 1.0, "Heat-capacity ratio must exceed one")
    return {"flow_coefficient_c": 520.0 * sqrt(k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))}


class RelievingPressure(Model):
    set_pressure_psig: Positive
    allowable_overpressure_fraction: Fraction
    atmospheric_pressure_kpa: Positive = ATM_KPA


@calculation("api520/relieving-pressure", "API 520 relieving pressure", RelievingPressure,
             ["API RP 520 7th ed. §3.5, Tables 1-6"], origin="engineering_utility",
             limitations=["Overpressure fraction is supplied by the contingency/code basis; no automatic ASME scenario selection."])
def relieving_pressure(x):
    gauge = x.set_pressure_psig * (1.0 + x.allowable_overpressure_fraction)
    return {"relieving_pressure_psig": gauge,
            "relieving_pressure_kpaa": gauge * 6.894757293168 + x.atmospheric_pressure_kpa}


class GasCriticalArea(Model):
    required_mass_flow_kg_h: Positive
    relieving_temperature_k: Positive
    compressibility_factor: Positive = 1.0
    molecular_weight_kg_kmol: Positive
    relief_pressure_kpaa: Positive
    heat_capacity_ratio: Positive
    discharge_coefficient: Fraction = 0.975
    back_pressure_factor: Positive = 1.0
    combination_factor: Positive = 1.0


@calculation("api520/gas-critical-area", "API 520 critical gas/vapor effective area", GasCriticalArea,
             ["API RP 520 7th ed. §3.6.2, Eqs. 3.2-3.4"], origin="engineering_utility",
             limitations=["SI mass-flow form; assumes critical ideal-gas/nozzle behavior and supplied correction factors."])
def gas_critical_area(x):
    ensure(x.compressibility_factor > 0 and x.molecular_weight_kg_kmol > 0, "Invalid gas property")
    k = x.heat_capacity_ratio
    ensure(k > 1.0, "Heat-capacity ratio must exceed one")
    c = 520.0 * sqrt(k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))
    return {"required_area_mm2": 13160.0 * x.required_mass_flow_kg_h * sqrt(x.relieving_temperature_k * x.compressibility_factor / x.molecular_weight_kg_kmol) / (c * x.discharge_coefficient * x.relief_pressure_kpaa * x.back_pressure_factor * x.combination_factor)}


class GasSubcriticalArea(GasCriticalArea):
    downstream_pressure_kpaa: Positive


@calculation("api520/gas-subcritical-area", "API 520 subcritical gas/vapor effective area", GasSubcriticalArea,
             ["API RP 520 7th ed. §3.6.3, Eqs. 3.5-3.7"], origin="engineering_utility",
             limitations=["SI mass-flow form; conventional/pilot valve route only; use balanced-bellows manufacturer factors where applicable."])
def gas_subcritical_area(x):
    k = x.heat_capacity_ratio
    p1, p2 = x.relief_pressure_kpaa, x.downstream_pressure_kpaa
    ensure(k > 1.0 and 0 < p2 < p1, "Subcritical flow requires 0 < P2 < P1 and k > 1")
    r = p2 / p1
    f2 = sqrt((k / (k - 1.0)) * r ** (2.0 / k) * (1.0 - r ** ((k - 1.0) / k)) / (1.0 - r))
    area = 17.9 * x.required_mass_flow_kg_h * sqrt(x.relieving_temperature_k * x.compressibility_factor / x.molecular_weight_kg_kmol) / (f2 * x.discharge_coefficient * x.combination_factor * sqrt(p1 * (p1 - p2)))
    return {"required_area_mm2": area, "back_pressure_ratio": r, "subcritical_flow_factor": f2}


class LiquidArea(Model):
    required_flow_l_min: Positive
    specific_gravity: Positive
    set_pressure_kpag: Positive
    back_pressure_kpag: NonNegative = 0.0
    discharge_coefficient: Positive = 0.65
    back_pressure_factor: Positive = 1.0
    combination_factor: Positive = 1.0
    viscosity_factor: Positive = 1.0
    overpressure_factor: Positive = 1.0


@calculation("api520/liquid-area", "API 520 liquid relief effective area", LiquidArea,
             ["API RP 520 7th ed. §3.8-3.9, Eqs. 3.9 and 3.12"], origin="engineering_utility",
             limitations=["SI form; Kp/Kv/Kw are supplied or separately calculated; certified capacity and two-phase flashing are separate routes."])
def liquid_area(x):
    ensure(x.set_pressure_kpag > x.back_pressure_kpag, "Set pressure must exceed back pressure")
    dp = x.set_pressure_kpag - x.back_pressure_kpag
    area = 11.78 * x.required_flow_l_min * sqrt(x.specific_gravity) / (x.discharge_coefficient * x.back_pressure_factor * x.combination_factor * x.viscosity_factor * x.overpressure_factor * sqrt(dp))
    return {"required_area_mm2": area}


class ViscosityFactor(Model):
    reynolds_number: Positive


@calculation("api520/liquid-viscosity-factor", "API 520 liquid viscosity correction Kv", ViscosityFactor,
             ["API RP 520 7th ed. §3.8.1.3, Eqs. 3.10-3.11; Fig. 36"], origin="engineering_utility",
             limitations=["Correlation is not recommended below 100 SSU when using the alternate viscosity basis."])
def liquid_viscosity_factor(x):
    r = x.reynolds_number
    return {"viscosity_factor": 1.0 / (0.9935 + 2.878 / sqrt(r) + 342.75 / (r ** 1.5))}


class GasCriticalCapacity(Model):
    effective_area_mm2: Positive
    relieving_temperature_k: Positive
    compressibility_factor: Positive = 1.0
    molecular_weight_kg_kmol: Positive
    relief_pressure_kpaa: Positive
    heat_capacity_ratio: Positive
    discharge_coefficient: Fraction = 0.975
    back_pressure_factor: Positive = 1.0
    combination_factor: Positive = 1.0


@calculation("api520/gas-critical-capacity", "API 520 critical gas/vapor mass capacity", GasCriticalCapacity,
             ["API RP 520 7th ed. §3.6.2, Eqs. 3.2-3.4 (inverse sizing)"], origin="engineering_utility",
             limitations=["Inverse of the SI effective-area relation; use certified valve capacity and qualified real-gas data for selection."])
def gas_critical_capacity(x):
    ensure(x.compressibility_factor > 0 and x.molecular_weight_kg_kmol > 0, "Invalid gas property")
    k = x.heat_capacity_ratio
    ensure(k > 1.0, "Heat-capacity ratio must exceed one")
    c = 520.0 * sqrt(k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))
    rate = x.effective_area_mm2 * c * x.discharge_coefficient * x.relief_pressure_kpaa * x.back_pressure_factor * x.combination_factor
    rate /= 13160.0 * sqrt(x.relieving_temperature_k * x.compressibility_factor / x.molecular_weight_kg_kmol)
    return {"mass_capacity_kg_h": rate}


class GasSubcriticalCapacity(Model):
    effective_area_mm2: Positive
    relieving_temperature_k: Positive
    compressibility_factor: Positive = 1.0
    molecular_weight_kg_kmol: Positive
    relief_pressure_kpaa: Positive
    heat_capacity_ratio: Positive
    discharge_coefficient: Fraction = 0.975
    combination_factor: Positive = 1.0
    downstream_pressure_kpaa: Positive


@calculation("api520/gas-subcritical-capacity", "API 520 subcritical gas/vapor mass capacity", GasSubcriticalCapacity,
             ["API RP 520 7th ed. §3.6.3, Eqs. 3.5-3.7 (inverse sizing)"], origin="engineering_utility",
             limitations=["Inverse of the SI effective-area relation; downstream pressure and manufacturer correction factors remain caller-qualified."])
def gas_subcritical_capacity(x):
    k = x.heat_capacity_ratio
    p1, p2 = x.relief_pressure_kpaa, x.downstream_pressure_kpaa
    ensure(k > 1.0 and 0 < p2 < p1, "Subcritical flow requires 0 < P2 < P1 and k > 1")
    r = p2 / p1
    f2 = sqrt((k / (k - 1.0)) * r ** (2.0 / k) * (1.0 - r ** ((k - 1.0) / k)) / (1.0 - r))
    rate = x.effective_area_mm2 * f2 * x.discharge_coefficient * x.combination_factor * sqrt(p1 * (p1 - p2))
    rate /= 17.9 * sqrt(x.relieving_temperature_k * x.compressibility_factor / x.molecular_weight_kg_kmol)
    return {"mass_capacity_kg_h": rate, "back_pressure_ratio": r, "subcritical_flow_factor": f2}


class LiquidCapacity(Model):
    effective_area_mm2: Positive
    specific_gravity: Positive
    set_pressure_kpag: Positive
    back_pressure_kpag: NonNegative = 0.0
    discharge_coefficient: Positive = 0.65
    back_pressure_factor: Positive = 1.0
    combination_factor: Positive = 1.0
    viscosity_factor: Positive = 1.0
    overpressure_factor: Positive = 1.0


@calculation("api520/liquid-capacity", "API 520 liquid relief volumetric capacity", LiquidCapacity,
             ["API RP 520 7th ed. §3.8-3.9, Eqs. 3.9 and 3.12 (inverse sizing)"], origin="engineering_utility",
             limitations=["Inverse of the SI effective-area relation; flashing/two-phase capacity and certified valve coefficients remain separate routes."])
def liquid_capacity(x):
    ensure(x.set_pressure_kpag > x.back_pressure_kpag, "Set pressure must exceed back pressure")
    dp = x.set_pressure_kpag - x.back_pressure_kpag
    rate = x.effective_area_mm2 * x.discharge_coefficient * x.back_pressure_factor * x.combination_factor * x.viscosity_factor * x.overpressure_factor * sqrt(dp)
    rate /= 11.78 * sqrt(x.specific_gravity)
    return {"flow_capacity_l_min": rate}

