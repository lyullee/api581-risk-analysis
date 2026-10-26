"""Portfolio-level risk aggregation for digital-twin and site assessments.

This is an integration calculation: each component risk is supplied by a
qualified component assessment and is not recomputed here.  Component
scenarios must be disjoint (or the caller must partition them before calling).
"""
import math

from pydantic import Field

from .core import Model, NonNegative, calculation, ensure


class PortfolioComponent(Model):
    component_id: str = Field(min_length=1, max_length=200)
    annual_failure_frequency: NonNegative
    equipment_area_risk_m2_per_year: NonNegative
    personnel_area_risk_m2_per_year: NonNegative
    financial_risk_per_year: NonNegative


class PortfolioRisk(Model):
    components: list[PortfolioComponent] = Field(min_length=1, max_length=100000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    disjointness_basis: str = Field(min_length=1, max_length=1000)


@calculation(
    "risk/portfolio",
    "Aggregate qualified component risks for a site or digital-twin portfolio",
    PortfolioRisk,
    ["Part 1 §4.3.1; Part 1 §4.3.2"],
    origin="engineering_utility",
    limitations=[
        "Each component row must already be a mutually exclusive annual risk contribution on the same currency and consequence basis.",
        "This API does not deduplicate shared release scenarios, normalize currencies, or infer individual/societal risk.",
        "The disjointness_basis is an auditable owner declaration, not an automatic proof of independence.",
    ],
)
def portfolio(x: PortfolioRisk):
    ensure(
        len({row.component_id for row in x.components}) == len(x.components),
        "Duplicate component_id",
    )
    frequency = math.fsum(row.annual_failure_frequency for row in x.components)
    equipment = math.fsum(row.equipment_area_risk_m2_per_year for row in x.components)
    personnel = math.fsum(row.personnel_area_risk_m2_per_year for row in x.components)
    financial = math.fsum(row.financial_risk_per_year for row in x.components)
    contributions = {
        row.component_id: {
            "annual_failure_frequency": row.annual_failure_frequency,
            "equipment_area_risk_m2_per_year": row.equipment_area_risk_m2_per_year,
            "personnel_area_risk_m2_per_year": row.personnel_area_risk_m2_per_year,
            "financial_risk_per_year": row.financial_risk_per_year,
        }
        for row in x.components
    }
    return {
        "component_count": len(x.components),
        "annual_failure_frequency": frequency,
        "equipment_area_risk_m2_per_year": equipment,
        "personnel_area_risk_m2_per_year": personnel,
        "area_risk_m2_per_year": max(equipment, personnel),
        "financial_risk_per_year": financial,
        "currency": x.currency,
        "disjointness_basis": x.disjointness_basis,
        "component_contributions": contributions,
    }
