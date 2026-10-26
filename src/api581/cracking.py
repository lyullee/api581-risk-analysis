"""SCC base table and caustic escalation; susceptibility screening is external."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, calculation, ensure

# Columns are D,C,B,A for each of 1..6 inspections. PDF p175 visually checked.
SCC = {
    0: [(0, 0, 0, 0)] * 6,
    1: [(1, 1, 1, 1)] * 6,
    10: [(8, 3, 1, 1), (6, 2, 1, 1), (4, 1, 1, 1), (2, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)],
    50: [(40, 17, 5, 3), (30, 10, 2, 1), (20, 5, 1, 1), (10, 2, 1, 1), (5, 1, 1, 1), (1, 1, 1, 1)],
    100: [(80, 33, 10, 5), (60, 20, 4, 1), (40, 10, 2, 1), (20, 5, 1, 1), (10, 2, 1, 1), (5, 1, 1, 1)],
    500: [(400, 170, 50, 25), (300, 100, 20, 5), (200, 50, 8, 1), (100, 25, 2, 1), (50, 10, 1, 1), (25, 5, 1, 1)],
    1000: [(800, 330, 100, 50), (600, 200, 40, 10), (400, 100, 16, 2), (200, 50, 5, 1), (100, 25, 2, 1), (50, 10, 1, 1)],
    5000: [(4000, 1670, 500, 250), (3000, 1000, 250, 50), (2000, 500, 80, 10), (1000, 250, 25, 2), (500, 125, 5, 1), (250, 50, 2, 1)],
}


class SccBase(Model):
    severity_index: Literal[0, 1, 10, 50, 100, 500, 1000, 5000]
    inspection_grade: Literal["A", "B", "C", "D", "E"]
    inspection_count: int = Field(ge=0, le=6)


@calculation("damage/scc-base", "SCC base damage factor lookup", SccBase,
             ["Part 2 Table 6.3; PDF p175"],
             limitations=["Severity and highest equivalent inspection category supplied by caller. Count >6 is not extrapolated. Ambiguous E/500 cell is rejected."])
def scc_base(x):
    if x.inspection_grade == "E":
        ensure(x.inspection_count == 0, "E means no effective inspections; count must be 0")
        ensure(x.severity_index != 500, "Published E/500 cell is ambiguous; requires source reconciliation", "ambiguous_source")
        value = x.severity_index
    else:
        ensure(x.inspection_count >= 1, "A-D lookup requires at least one inspection")
        value = SCC[x.severity_index][x.inspection_count - 1]["DCBA".index(x.inspection_grade)]
    return {"base_damage_factor": value}


class CausticSeverity(Model):
    susceptibility: Literal["none", "low", "medium", "high"]


@calculation("damage/caustic-severity", "Caustic cracking severity index", CausticSeverity,
             ["Part 2 Table 6.2; PDF p174"], limitations=["This low-level severity lookup accepts qualified susceptibility; use damage/caustic-screening, damage/caustic-figure-susceptibility or damage/caustic-screened-assessment for the implemented material/exposure and Figure 6.2 routing. It does not infer applicability from chemistry."])
def caustic_severity(x):
    return {"severity_index": {"none": 0, "low": 50, "medium": 500, "high": 5000}[x.susceptibility]}


class CausticEscalation(Model):
    base_damage_factor: NonNegative
    years_since_qualifying_inspection: NonNegative


@calculation("damage/caustic-escalation", "Caustic cracking time escalation", CausticEscalation,
             ["Part 2 §6.6.3 eq (2.25); PDF p173"],
             limitations=["Age must follow qualifying A/B/C inspection or repair criteria; detected unrepaired cracks require a separate FFS evaluation."])
def caustic_escalation(x):
    return {"damage_factor": x.base_damage_factor * max(x.years_since_qualifying_inspection, 1) ** 1.1}


class LiningAdjustment(Model):
    base_damage_factor: NonNegative
    condition: Literal["good", "average", "poor"]
    effective_online_monitoring: bool


@calculation("damage/lining-adjust", "Lining condition and monitoring adjustment", LiningAdjustment,
             ["Part 2 eq (2.24), Table 5.6; PDF pp167,171"],
             limitations=["Base DF supplied by caller; lining-type/age Tables 5.4/5.5 not selected automatically."])
def lining_adjust(x):
    condition = {"good": 1, "average": 2, "poor": 10}[x.condition]
    monitoring = .1 if x.effective_online_monitoring else 1
    return {"condition_factor": condition, "monitoring_factor": monitoring,
            "lining_damage_factor": x.base_damage_factor * condition * monitoring}
