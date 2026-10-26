"""API 581 Part 3 Table 4.2/4.2M representative-fluid properties.

The table is intentionally kept as source data rather than hidden inside a
consequence calculation.  This makes the selection reusable by release,
phase, flash and consequence APIs.  The printed Table 4.2M heat-capacity
polynomials and the printed note 2 hyperbolic form are evaluated directly
from the table. No silently substituted property package is used.
"""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, Fraction, calculation, ensure

FluidId = Literal[
    "C1-C2", "C3-C4", "C5", "C6-C8", "C9-C12", "C13-C16", "C17-C25", "C25+",
    "Water", "Steam", "Acid", "H2", "H2S", "HF", "CO", "DEE", "HCL",
    "Nitric Acid", "ALCL3", "NO2", "Phosgene", "TDI", "Methanol", "PO",
    "Styrene", "EEA", "EE", "EG", "EO", "Pyrophoric"
]


class AcidCausticSelection(Model):
    """Table 4.1.3 decision for acid/caustic nonflammable releases."""
    is_acid_or_caustic: bool
    is_flammable: bool
    is_toxic: bool
    personnel_contact_hazard: bool


@calculation(
    "properties/acid-caustic-representative-fluid",
    "API 581 acid/caustic representative-fluid selection",
    AcidCausticSelection,
    ["Part 3 §4.1.3, §4.1.6; PDF p483-484"],
    limitations=[
        "Implements only the printed screening rule: ACID is selected for a nonflammable, nontoxic acid/caustic that still presents personnel contact hazard. It does not determine chemistry, concentration, toxicity, flammability or splash hazard from plant data."
    ],
)
def acid_caustic_representative_fluid(x):
    selected = x.is_acid_or_caustic and not x.is_flammable and not x.is_toxic and x.personnel_contact_hazard
    return {
        "selection": "acid_reference" if selected else "not_applicable",
        "representative_fluid": "Acid" if selected else None,
        "release_phase": "liquid" if selected else None,
        "consequence_model": "acid_splash" if selected else None,
        "selection_basis": "Part 3 §4.1.3 printed ACID rule" if selected else "caller must select another representative fluid or consequence route",
    }


class MixturePropertyComponent(Model):
    fluid: FluidId
    mole_fraction: Fraction
    consequence_relevant: bool = True


class MixtureRepresentativeFluid(Model):
    components: list[MixturePropertyComponent] = Field(min_length=1, max_length=100)


@calculation(
    "properties/mixture-representative-fluid",
    "Annex 3.A mole-weighted representative-fluid selection",
    MixtureRepresentativeFluid,
    ["Part 3 Annex A §3.1.2.1, §3.1.2.3-§3.1.2.4, eq (3.A.1); PDF pp614-615"],
    limitations=[
        "Uses Table 4.2M properties and mole-fraction weighting for MW, NBP, density and AIT. Inert/non-consequence-relevant components are excluded as the printed conservative Level 1 rule directs. Hydrocarbon pseudo-components are selected only from the hydrocarbon rows; selection then prioritizes the highest candidate NBP that does not exceed the weighted NBP. Chemistry outside the table remains Level 2 recommended and is not silently mapped."
    ],
)
def mixture_representative_fluid(x):
    ensure(abs(math.fsum(c.mole_fraction for c in x.components) - 1.0) <= 1e-9, "Mixture mole fractions must sum to 1")
    relevant = [c for c in x.components if c.consequence_relevant and c.mole_fraction > 0]
    ensure(relevant, "At least one consequence-relevant mixture component is required")
    relevant_total = math.fsum(c.mole_fraction for c in relevant)
    weighted = {
        "molecular_weight_kg_kmol": math.fsum(c.mole_fraction * TABLE_4_2M[c.fluid][0] for c in relevant) / relevant_total,
        "normal_boiling_point_k": 273.15 + math.fsum(c.mole_fraction * TABLE_4_2M[c.fluid][2] for c in relevant) / relevant_total,
        "liquid_density_kg_m3": math.fsum(c.mole_fraction * TABLE_4_2M[c.fluid][1] for c in relevant) / relevant_total,
    }
    ait_values = [(c, TABLE_4_2M[c.fluid][6]) for c in relevant]
    ensure(all(value is not None for _, value in ait_values), "AIT is unavailable for a relevant mixture component")
    weighted["autoignition_temperature_k"] = 273.15 + math.fsum(c.mole_fraction * value for c, value in ait_values) / relevant_total
    weighted_nbp_c = weighted["normal_boiling_point_k"] - 273.15
    # Annex 3.A examples are pseudo-component mixtures.  Do not select an
    # unrelated chemical merely because its boiling point happens to be close.
    hydrocarbon_rows = {"C1-C2", "C3-C4", "C5", "C6-C8", "C9-C12", "C13-C16", "C17-C25", "C25+"}
    relevant_fluids = {c.fluid for c in relevant}
    if relevant_fluids <= hydrocarbon_rows:
        candidate_fluids = hydrocarbon_rows
    elif len(relevant_fluids) == 1:
        candidate_fluids = relevant_fluids
    else:
        candidate_fluids = set(TABLE_4_2M)
    candidates = [(fluid, TABLE_4_2M[fluid]) for fluid in candidate_fluids if TABLE_4_2M[fluid][2] <= weighted_nbp_c]
    ensure(candidates, "No Table 4.2M representative fluid has NBP at or below the weighted mixture NBP", "unsupported_representative_fluid")
    selected, _ = max(candidates, key=lambda item: (item[1][2], -abs(item[1][0] - weighted["molecular_weight_kg_kmol"])))
    return {**weighted, "selected_fluid": selected,
            "relevant_mole_fraction": relevant_total,
            "selection_basis": "highest_same_family_table_NBP_not_exceeding_weighted_NBP",
            "level2_recommended": False}

# MW kg/kmol, liquid density kg/m3, NBP °C, ambient state, Cp note,
# A..E as printed, AIT °C.  N/A is represented by None.
TABLE_4_2M = {
    "C1-C2": (23, 250.512, -125, "Gas", 1, (12.3, .115, -2.87e-5, -1.30e-9, None), 558),
    "C3-C4": (51, 538.379, -21, "Gas", 1, (2.632, .3188, -1.35e-4, 1.47e-8, None), 369),
    "C5": (72, 625.199, 36, "Liquid", 1, (-3.626, .4873, -2.60e-4, 5.30e-8, None), 284),
    "C6-C8": (100, 684.018, 99, "Liquid", 1, (-5.146, .676, -3.65e-4, 7.66e-8, None), 223),
    "C9-C12": (149, 734.012, 184, "Liquid", 1, (-8.5, 1.01, -5.56e-4, 1.18e-7, None), 208),
    "C13-C16": (205, 764.527, 261, "Liquid", 1, (-11.7, 1.39, -7.72e-4, 1.67e-7, None), 202),
    "C17-C25": (280, 775.019, 344, "Liquid", 1, (-22.4, 1.94, -1.12e-3, -2.53e-7, None), 202),
    "C25+": (422, 900.026, 527, "Liquid", 1, (-22.4, 1.94, -1.12e-3, -2.53e-7, None), 202),
    "Water": (18, 997.947, 100, "Liquid", 3, (2.76e5, -2.09e3, 8.125, -1.41e-2, 9.37e-6), None),
    "Steam": (18, 997.947, 100, "Gas", 3, (3.34e4, 2.68e4, 2.61e3, 8.90e3, 1.17e3), None),
    "Acid": (18, 997.947, 100, "Liquid", 3, (2.76e5, -2.09e3, 8.125, -1.41e-2, 9.37e-6), None),
    "H2": (2, 71.010, -253, "Gas", 1, (27.1, 9.27e-3, -1.38e-5, 7.65e-9, None), 400),
    "H2S": (34, 993.029, -59, "Gas", 1, (31.9, 1.44e-3, 2.43e-5, -1.18e-8, None), 260),
    "HF": (20, 967.031, 20, "Gas", 1, (29.1, 6.61e-4, -2.03e-6, 2.50e-9, None), 17760),
    "CO": (28, 800.920, -191, "Gas", 2, (2.91e4, 8.77e3, 3.09e3, 8.46e3, 1.54e3), 609),
    "DEE": (74, 720.828, 35, "Liquid", 2, (8.62e4, 2.55e5, 1.54e3, 1.44e5, -6.89e2), 160),
    "HCL": (36, 1185.362, -85, "Gas", None, None, None),
    "Nitric Acid": (63, 1521.749, 121, "Liquid", None, None, None),
    "ALCL3": (133.5, 2434.798, 194, "Powder", 1, (4.34e4, 3.97e4, 4.17e2, 2.40e4, None), 558),
    "NO2": (90, 929.068, 135, "Liquid", None, None, None),
    "Phosgene": (99, 1377.583, 83, "Liquid", None, None, None),
    "TDI": (174, 1217.399, 251, "Liquid", None, None, 620),
    "Methanol": (32, 800.920, 65, "Liquid", 2, (3.93e4, 8.79e4, 1.92e3, 5.37e4, 8.97e2), 464),
    "PO": (58, 832.957, 34, "Liquid", 2, (4.95e4, 1.74e5, 1.56e3, 1.15e5, 7.02e2), 449),
    "Styrene": (104, 683.986, 145, "Liquid", 2, (8.93e4, 2.15e5, 7.72e2, 9.99e4, 2.44e3), 490),
    "EEA": (132, 977.123, 156, "Liquid", 2, (1.06e5, 2.40e5, 6.59e2, 1.50e5, 1.97e3), 379),
    "EE": (90, 929.068, 135, "Liquid", 2, (3.25e4, 3.00e5, 1.17e3, 2.08e5, 4.73e2), 235),
    "EG": (62, 1105.270, 197, "Liquid", 2, (6.30e4, 1.46e5, 1.67e3, 9.73e4, 7.74e2), 396),
    "EO": (44, 881.013, 11, "Gas", 2, (3.35e4, 1.21e5, 1.61e3, 8.24e4, 7.37e2), 429),
    "Pyrophoric": (149, 734.012, 184, "Liquid", 1, (-8.5, 1.01, -5.56e-4, 1.18e-7, None), None),
}


class RepresentativeFluid(Model):
    fluid: FluidId
    temperature_k: Positive


@calculation(
    "properties/representative-fluid",
    "API 581 Table 4.2M representative-fluid properties",
    RepresentativeFluid,
    ["Part 3 §4.1.1-§4.1.2, Table 4.2/Table 4.2M; PDF pp515-517"],
    limitations=[
        "Returns tabulated representative properties, not a real-fluid property package. Cp note 1 and note 3 are evaluated as printed polynomials; note 2 uses Cp=A+B((C/T)/sinh(C/T))²+D((E/T)/cosh(E/T))². Rows with --- have no tabulated Cp or AIT. Ambient-state and phase-selection rules remain a separate Table 4.3 decision."
    ],
)
def representative_fluid(x):
    mw, density, nbp_c, ambient_state, note, coefficients, ait_c = TABLE_4_2M[x.fluid]
    cp = None
    cp_basis = "not_available"
    t = x.temperature_k
    if coefficients is not None and note in (1, 3):
        a, b, c, d, e = coefficients
        cp = a + b*t + c*t*t + d*t*t*t + ((e or 0.0)*t*t*t*t if note == 3 else 0.0)
        cp_basis = f"table_note_{note}_polynomial"
    elif coefficients is not None and note == 2:
        a, b, c, d, e = coefficients
        cp = a + b*((c/t)/math.sinh(c/t))**2 + d*((e/t)/math.cosh(e/t))**2
        cp_basis = "table_note_2_hyperbolic"
    ensure(cp is None or cp == cp and abs(cp) < 1e12, "Representative-fluid Cp is non-finite or outside supported range")
    return {
        "fluid": x.fluid, "molecular_weight_kg_kmol": mw,
        "liquid_density_kg_m3": density, "normal_boiling_point_k": nbp_c + 273.15,
        "ambient_state": ambient_state, "cp_note": note,
        "cp_value_table_units": cp, "cp_basis": cp_basis,
        "autoignition_temperature_k": None if ait_c is None else ait_c + 273.15,
        "source_table": "Table 4.2M",
    }
