"""Part 2 §§20,22,23 brittle-fracture and embrittlement calculations.

SI tables are used as printed, except Table 20.3 where the unambiguous US
table is converted to SI explicitly. Material qualification is caller supplied.
"""
from bisect import bisect_left
import math
from typing import Annotated, Literal
from pydantic import Field, StrictBool
from .core import Model, Positive, Fraction, calculation, ensure

Finite = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Interpolation = Literal["exact", "linear"]
KSI_PA = 6894757.293168

# Rows: CET - Tref, K (= Celsius difference). Columns: printed SI thickness, mm.
DELTA_K = (56, 44, 33, 22, 11, 0, -11, -22, -33, -44, -56)
THICKNESS_MM = (6.4, 12.7, 25.4, 38.1, 50.8, 63.5, 76.2, 88.9, 101.6)
NON_PWHT = (
    (0,0,0,0,0,0,.9,1.1,1.2),
    (0,0,0,.8,1.1,2,2,4,6),
    (0,0,1,2,4,9,19,36,60),
    (0,.7,2,9,29,69,133,224,338),
    (.1,1.3,10,49,143,296,500,741,1008),
    (.9,3,39,175,424,759,1142,1545,1950),
    (1.2,7,109,405,850,1366,1897,2415,2903),
    (2,16,220,697,1317,1969,2596,3176,3703),
    (2,30,350,988,1740,2479,3160,3769,4310),
    (3,46,474,1239,2080,2873,3581,4203,4746),
    (4,61,579,1436,2336,3160,3883,4509,5000),
)
PWHT = (
    (0,0,0,0,0,0,0,0,0),
    (0,0,0,0,0,0,0,0,.2),
    (0,0,0,0,0,.5,.9,1.1,1.3),
    (0,0,0,.5,1.1,1.3,2,3,4),
    (0,0,.6,1.2,2,4,7,13,23),
    (0,0,1.1,2,6,14,29,53,88),
    (0,.4,2,5,17,41,83,144,224),
    (0,.9,3,12,38,90,171,281,416),
    (0,1.1,5,22,68,153,277,436,623),
    (0,1.2,7,34,102,219,382,582,810),
    (0,1.3,9,46,133,277,472,704,962),
)


def _weights(nodes, value, mode):
    """Ascending grid; snap only floating-point roundoff at printed nodes."""
    for i, node in enumerate(nodes):
        if math.isclose(value, node, rel_tol=1e-12, abs_tol=1e-9):
            return ((i, 1.0),)
    ensure(nodes[0] < value < nodes[-1], "Input outside tabulated domain; extrapolation is not supported")
    ensure(mode == "linear", "Input is not a printed table node; explicitly select linear interpolation", "interpolation_required")
    upper = bisect_left(nodes, value)
    weight = (value - nodes[upper-1]) / (nodes[upper] - nodes[upper-1])
    return ((upper-1, 1-weight), (upper, weight))


def _lookup(nodes, values, value, mode):
    return sum(values[i] * weight for i, weight in _weights(nodes, value, mode))


class BrittleReference(Model):
    material_group: Literal["carbon_steel", "low_alloy_steel"]
    minimum_yield_strength_pa: Positive
    exemption_curve: Literal["A", "B", "C", "D"]
    interpolation: Interpolation


@calculation("damage/brittle-reference-temperature", "Brittle fracture reference temperature", BrittleReference,
             ["Part 2 §20.6.3 STEP 3; Table 20.3; PDF p268"],
             limitations=["Caller qualifies material and assigns ASME exemption curve. Uses the printed US Table 20.3 (ksi, F), explicitly converted to Pa and K; not rounded SI Table 20.3M. Linear interpolation is a caller-selected engineering interpolation; no extrapolation."])
def brittle_reference(x):
    base = ((104,97,91,86,81,78,74,71,68,66,63) if x.material_group == "carbon_steel"
            else (124,115,107,101,96,92,88,85,81,79,76,73,71,69,67,65,63,62,60,58,57,56,54,53,52,51))
    yield_nodes = tuple(range(30, 30 + 2*len(base), 2))
    offset = {"A":0, "B":38, "C":76, "D":102}[x.exemption_curve]
    temp_f = _lookup(yield_nodes, tuple(v-offset for v in base), x.minimum_yield_strength_pa/KSI_PA, x.interpolation)
    return {"reference_temperature_k": (temp_f-32)*5/9+273.15, "table_basis": "20.3_US_converted_to_SI"}


class BrittleService(Model):
    component_thickness_m: Positive
    nominal_uncorroded_thickness_m: Positive
    equipment_type: Literal["pressure_vessel", "piping"]
    p1_or_p3_steel: StrictBool
    design_temperature_k: Positive
    construction_code_satisfied: StrictBool
    stable_conditions_no_more_severe_future: StrictBool
    cet_at_mawp_k: Positive
    cyclic_fatigue_or_vibration_design_service: StrictBool
    environmental_cracking: StrictBool
    shock_chilling: StrictBool


@calculation("damage/brittle-service-factor", "Brittle fracture service-experience adjustment", BrittleService,
             ["Part 2 §20.6.3 STEP 6; eq (2.86); PDF pp264-265"],
             limitations=["Owner qualifies code compliance, operating history and service exclusions. Thin-component criterion is an independent OR; all eight service criteria are otherwise required. Printed SI thresholds are used."])
def brittle_service(x):
    checks = {
        "p1_p3_and_design_temperature": x.p1_or_p3_steel and x.design_temperature_k <= 616.15,
        "construction_code": x.construction_code_satisfied,
        "stable_service": x.stable_conditions_no_more_severe_future,
        "cet_at_mawp": x.cet_at_mawp_k >= (244.15 if x.equipment_type == "pressure_vessel" else 169.15),
        "nominal_thickness": x.nominal_uncorroded_thickness_m <= .0508,
        "no_cyclic_service": not x.cyclic_fatigue_or_vibration_design_service,
        "no_environmental_cracking": not x.environmental_cracking,
        "no_shock_chilling": not x.shock_chilling,
    }
    thin = x.component_thickness_m <= .0127
    return {"service_experience_factor": .01 if thin or all(checks.values()) else 1,
            "thin_component_credit": thin, "service_criteria": checks}


class BrittleBase(Model):
    component_thickness_m: Positive
    cet_minus_reference_k: Finite
    post_weld_heat_treated: StrictBool
    interpolation: Interpolation


@calculation("damage/brittle-base", "Brittle fracture base damage table", BrittleBase,
             ["Part 2 Tables 20.4M,20.5M; PDF pp270-271"],
             limitations=["Printed SI grid: thickness 6.4-101.6 mm and CET-Tref -56 to 56 K. Linear mode is caller-selected bilinear interpolation of DF, not log DF. No extrapolation or service credit applied here."])
def brittle_base(x):
    table = PWHT if x.post_weld_heat_treated else NON_PWHT
    rows = _weights(tuple(reversed(DELTA_K)), x.cet_minus_reference_k, x.interpolation)
    cols = _weights(THICKNESS_MM, x.component_thickness_m*1000, x.interpolation)
    value = sum(table[len(DELTA_K)-1-r][c]*rw*cw for r,rw in rows for c,cw in cols)
    return {"base_damage_factor": value, "table": "20.5M" if x.post_weld_heat_treated else "20.4M"}


class BrittleFracture(Model):
    reference: BrittleReference
    service: BrittleService
    critical_exposure_temperature_k: Positive
    post_weld_heat_treated: StrictBool
    interpolation: Interpolation


@calculation("damage/brittle-fracture", "Brittle fracture reference/base/service calculation", BrittleFracture,
             ["Part 2 §20.6.3; Tables 20.3,20.4M,20.5M; eq (2.86)"],
             limitations=["Caller establishes applicability, ASME curve and CET (including credited controls) per API 579. No inspection credit. Uses US reference-temperature table converted to SI plus printed SI base-DF tables. Caller selects interpolation separately for yield and base-DF grids; no extrapolation."])
def brittle_fracture(x):
    reference = brittle_reference(x.reference)
    delta = x.critical_exposure_temperature_k-reference["reference_temperature_k"]
    base = brittle_base(BrittleBase(component_thickness_m=x.service.component_thickness_m,
        cet_minus_reference_k=delta, post_weld_heat_treated=x.post_weld_heat_treated, interpolation=x.interpolation))
    service = brittle_service(x.service)
    return {**reference, **base, **service, "cet_minus_reference_k": delta,
            "damage_factor": base["base_damage_factor"]*service["service_experience_factor"]}


class Embrittlement885(Model):
    minimum_evaluation_temperature_k: Positive
    reference_temperature_k: Positive = 301.15
    interpolation: Interpolation


@calculation("damage/embrittlement-885f", "885 F embrittlement damage factor", Embrittlement885,
             ["Part 2 §22.6.3; Table 22.3; PDF pp279-280"],
             limitations=["Qualified susceptible ferritic material and evaluation temperature supplied by caller; no inspection credit. Default reference is printed 28 C (301.15 K), which is not the exact conversion of printed 80 F. Uses printed SI delta-temperature rows. Above +56 K DF=0; at +56 K DF=2. Below -56 K rejected. Linear interpolation is an explicit caller choice."])
def embrittlement_885(x):
    delta = x.minimum_evaluation_temperature_k-x.reference_temperature_k
    # Preserve the explicit open-ended row; never interpolate across its discontinuity.
    if delta > 56 and not math.isclose(delta, 56, rel_tol=0, abs_tol=1e-9):
        factor = 0.0
    else:
        factor = _lookup(tuple(reversed(DELTA_K)), (1381,1216,1022,806,581,371,200,87,30,8,2), delta, x.interpolation)
    return {"reference_temperature_k": x.reference_temperature_k, "minimum_minus_reference_k": delta,
            "damage_factor": factor}


class SigmaContent(Model):
    sigma_fraction: Fraction


@calculation("damage/sigma-content", "Sigma-phase content category", SigmaContent,
             ["Part 2 Table 23.1; PDF p284"],
             limitations=["Content >1% is tabulated: low >1 to <5%, medium >=5 to <10%, high >=10%. At or below 1% the printed categories are unresolved and rejected; no assumed zero DF."])
def sigma_content(x):
    ensure(x.sigma_fraction > .01, "Sigma content at or below 1% has no unique category in Table 23.1", "unresolved_applicability")
    return {"sigma_category": "low" if x.sigma_fraction < .05 else ("medium" if x.sigma_fraction < .1 else "high")}


SIGMA_TEMP_C = (-46,-18,10,38,66,93,204,316,427,538,649)
SIGMA_FACTORS = {
    "low": (1.1,1,.9,.6,.3,.1,0,0,0,0,0),
    "medium": (34,20,11,7,5,3,1.3,.9,.2,0,0),
    "high": (4196,4196,4196,4196,3871,3202,1333,481,160,53,18),
}


class SigmaDamage(Model):
    evaluation_temperature_k: Positive
    sigma_category: Literal["low", "medium", "high"]
    interpolation: Interpolation


@calculation("damage/sigma-embrittlement", "Sigma-phase embrittlement damage factor", SigmaDamage,
             ["Part 2 §23.6.3; Table 23.3; PDF pp283,285"],
             limitations=["Qualified sigmatized austenitic stainless steel and content category supplied. No automatic exposure-to-sigma kinetics model or inspection credit. Printed SI evaluation-temperature grid -46 to 649 C; no extrapolation. Linear interpolation is caller-selected."])
def sigma_damage(x):
    return {"damage_factor": _lookup(SIGMA_TEMP_C, SIGMA_FACTORS[x.sigma_category], x.evaluation_temperature_k-273.15, x.interpolation),
            "sigma_category": x.sigma_category}
