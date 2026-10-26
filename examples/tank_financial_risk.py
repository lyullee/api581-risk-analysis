"""One AST bottom: source GFF -> qualified inputs -> financial consequence/risk."""
from api581 import Context
from api581.api import tank

gff = tank.generic_frequency(tank.GenericFrequencyInput(component_type="TANKBOTTOM"))
arrival = tank.groundwater_arrival(tank.GroundwaterArrivalInput(
    distance_to_groundwater_m=5., seepage_velocity_m_day=.1))
# Monetary numbers below are an explicit illustrative 2026 USD valuation fixture.
# They are not automatically escalated Table6.6 prices or external market data.
financial_input = tank.BottomFinancialConsequenceInput(
    generic_frequency_by_hole_per_year=gff.outputs.by_hole_per_year,
    generic_frequency_source="Part2 Table3.1; sum eq3.208",
    cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,
        subsoil=1500.,groundwater=5000.,surface_water=1500.),
    currency="USD",cost_basis="Owner-qualified illustrative 2026 USD fixture, not market prices",
    fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5,
    leaked_volume_by_hole_bbl=dict(small=1000.,medium=0.,large=0.),total_tank_volume_bbl=50000.,
    detection_time_days=360.,groundwater_arrival_time_days=arrival.outputs.arrival_time_days,
    tank_diameter_m=61.,repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,
        usd_to_output_currency=1.,cost_basis_year=2026),
    outage_multiplier=1.,production_cost_per_day=10000.,
)
consequence = tank.bottom_financial_consequence(financial_input)
risk = tank.bottom_risk_assessment(tank.BottomRiskAssessmentInput(
    financial=financial_input,management_score=500.,total_damage_factor=3.,
    damage_factor_source="Externally assessed example DF fixture"),
    context=Context(asset_id="ast-001",component_id="bottom",source_revision="example-fixture-v1"))
assert risk.outputs.financial_consequence == consequence.outputs.financial_consequence
print("GFF printed and equation totals:",gff.outputs.printed_total_per_year,gff.outputs.total_per_year)
print("Financial consequence:",consequence.outputs.financial_consequence,consequence.outputs.currency)
print("Annual frequency:",risk.outputs.annual_failure_frequency)
print("Financial risk/year:",risk.outputs.financial_risk_per_year,risk.outputs.currency)
print("Component-only integration scope:",risk.outputs.integration_scope)
