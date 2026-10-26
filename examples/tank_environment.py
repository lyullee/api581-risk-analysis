"""Independent AST environmental and repair APIs; scenario assumptions are explicit."""
from api581.api import tank, financial

# Deliberate qualification fixture, NOT a built-in tank GFF lookup.
frequencies = {"small": 7.2e-4, "medium": 0., "large": 0., "rupture": 2e-6}
costs = tank.environment_cost_table(tank.EnvironmentCostTableInput(sensitivity="medium")).outputs
arrival = tank.groundwater_arrival(tank.GroundwaterArrivalInput(
    distance_to_groundwater_m=5, seepage_velocity_m_day=.1)).outputs
environment = tank.bottom_environment_cost(tank.BottomEnvironmentCostInput(
    generic_frequency_by_hole_per_year=frequencies,
    cost_by_location_per_bbl=costs.cost_by_location_usd_per_bbl,
    cost_basis="Table6.6 medium source estimates; price year unspecified; example only",
    currency="USD", fraction_leaving_dike=.8, fraction_on_site=.25, fraction_off_site=.5,
    leaked_volume_by_hole_bbl={"small":1000., "medium":0., "large":0.},
    total_tank_volume_bbl=50000., detection_time_days=360,
    groundwater_arrival_time_days=arrival.arrival_time_days,
))
repair_table = financial.repair_table(financial.RepairTableInput(component_type="TANKBOTTOM")).outputs
repair = tank.bottom_repair_cost(tank.BottomRepairCostInput(
    generic_frequency_by_hole_per_year=frequencies, tank_diameter_m=61,
    repair_cost_by_hole=repair_table.cost_by_hole_usd_2001, material_factor=1,
    currency="USD",cost_basis="Table4.15 USD2001; no escalation"))
print("groundwater arrival days:", arrival.arrival_time_days)
print("environment consequence:", environment.outputs.model_dump())
print("repair consequence:", repair.outputs.model_dump())
# These two costs deliberately retain different source valuations; qualify them
# to a common monetary basis before combining into total financial consequence.
