"""Geometry/soil-to-financial-risk composition for a single AST bottom."""
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, REGISTRY, calculation, finite_tree
from .tank_source import BottomSource, bottom_source
from .tank_environment import Location, GroundwaterArrival, groundwater_arrival
from .tank_financial import TankRepairBasis, DamageBasis, BottomFinancial, BottomAssessment, bottom_assessment
from .tank_environment import Hole


class BottomEconomics(Model):
    repair: TankRepairBasis
    outage_multiplier: Positive
    override_outage_days: dict[Hole, NonNegative] = Field(default_factory=dict)
    production_cost_per_day: NonNegative
    cost_by_location_per_bbl: dict[Location, NonNegative]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    cost_basis: str = Field(min_length=1, max_length=500)
    fraction_leaving_dike: Fraction
    fraction_on_site: Fraction
    fraction_off_site: Fraction


class BottomIntegrated(DamageBasis):
    source: BottomSource
    distance_to_groundwater_m: NonNegative
    economics: BottomEconomics


@calculation("tank/bottom-integrated-assessment", "AST bottom geometry and soil through source, financial consequence and annual risk", BottomIntegrated,
    [*REGISTRY["tank/bottom-source-assessment"].references,"Part3 eq(3.244); PDF p601",
     *REGISTRY["tank/bottom-risk-assessment"].references],
    origin="api581_composition_with_supplied_damage_and_valuation",
    limitations=[*REGISTRY["tank/bottom-source-assessment"].limitations,
                 *REGISTRY["tank/bottom-risk-assessment"].limitations,
                 "Computes source inventory/rates/volumes, summed table GFF and seepage arrival from the same geometry/soil request. DF applicability and monetary qualification are external supplied assumptions. Single bottom only; no shell, whole-tank common-cause or digital-twin sensor assimilation inferred."])
def integrated(x):
    source = bottom_source(x.source)
    finite_tree(source)
    arrival = groundwater_arrival(GroundwaterArrival(distance_to_groundwater_m=x.distance_to_groundwater_m,
        seepage_velocity_m_day=source["seepage_velocity_m_day"]))
    financial = BottomFinancial(**x.economics.model_dump(),
        generic_frequency_by_hole_per_year=source["generic_frequency_by_hole_per_year"],
        generic_frequency_source="Part2 Table3.1; total eq3.208; computed within same bottom source",
        tank_diameter_m=x.source.tank_diameter_m,
        leaked_volume_by_hole_bbl={h:source["released_volume_by_hole_bbl"][h] for h in ("small","medium","large")},
        total_tank_volume_bbl=source["available_volume_bbl"],detection_time_days=source["detection_time_days"],
        groundwater_arrival_time_days=arrival["arrival_time_days"])
    result = bottom_assessment(BottomAssessment(financial=financial,management_score=x.management_score,
        total_damage_factor=x.total_damage_factor,damage_factor_source=x.damage_factor_source))
    return {**source,**result,"groundwater_arrival_time_days":arrival["arrival_time_days"],
        "integration_scope":"bottom_geometry_soil_source_financial_risk_with_supplied_df"}
