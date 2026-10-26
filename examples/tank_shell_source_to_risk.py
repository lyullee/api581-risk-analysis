"""AST shell source -> qualified diked-pool scenarios -> Level2 financial risk.

Pool-only .2 ignition/.8 non-ignition is a deliberate example assumption, not
automatically derived ignition probability or a complete fuel hazard assessment.
"""
from api581 import Context
from api581.api import tank

geometry = dict(tank_diameter_m=61.,fill_height_m=10.,course_index=2,course_height_m=2.,
    fluid="gasoline",diameter_boundary_basis="inch_0_125")
source = tank.shell_source_assessment(tank.ShellSourceAssessmentInput(**geometry)).outputs
cases = []
for hole in ("small","medium","large","rupture"):
    # Example assumes stored liquid enters pool with no flash/rainout correction.
    # Thermodynamic data, view-factor basis and source suitability require qualification.
    pool = tank.diked_pool_consequence(tank.DikedPoolConsequenceInput(
        burning=dict(heat_of_combustion_j_kg=46e6,latent_heat_j_kg=350000,boiling=False,
            specific_heat_j_kg_k=2200.,boiling_temperature_k=372.,ambient_temperature_k=293.),
        liquid_rate_kg_s=source.mass_rate_by_hole_kg_s[hole],
        available_liquid_mass_kg=source.released_mass_by_hole_kg[hole],
        liquid_density_kg_m3=source.liquid_density_kg_m3,dike_area_m2=25.,dike_limit_basis="burning_pool_area",
        air_density_kg_m3=1.2,vapor_density_kg_m3=2.,wind_speed_m_s=2.,
        atmosphere=dict(transmissivity_model="constant",constant_transmissivity=.8),
        equation_basis="geometry_checked",distance_convention="surface_to_axis",maximum_surface_distance_m=1000.)).outputs
    cases.append(dict(hole=hole,non_ignition_probability=.8,
        outcomes=[dict(event=event,probability=.2 if event == "pool_fire" else 0.,
            equipment_area_m2=pool.equipment_area_m2 if event == "pool_fire" else 0.,
            personnel_area_m2=pool.personnel_area_m2 if event == "pool_fire" else 0.)
            for event in ("pool_fire","jet_fire","fireball","vce","flash_fire")],
        event_tree_source="Qualified example pool-only .2/.8 assumption; other paths excluded by fixture",
        consequence_source="Computed from same shell source via tank.diked_pool_consequence; explicit thermodynamic fixture",
        toxic_components=[],toxic_applicability="not_applicable",
        toxic_applicability_source="Example assumes no applicable toxic species; requires material qualification",
        dike_area_m2=25.,burning_pool_area_m2=pool.pool_area_m2,pool_dike_limit_basis="burning_pool_area"))

result = tank.shell_integrated_assessment(tank.ShellIntegratedAssessmentInput(source=geometry,cases=cases,
    economics=dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,usd_to_output_currency=1.,cost_basis_year=2026),
        outage_multiplier=1.,production_cost_per_day=1000.,currency="USD",cost_basis="Owner-qualified illustrative 2026 USD fixture",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5,
        equipment_cost_per_m2=100.,population_density_per_m2=.01,cost_per_injury=100000.),
    management_score=500.,total_damage_factor=3.,damage_factor_source="Externally assessed example DF fixture"),
    context=Context(asset_id="ast-001",component_id="course-2",source_revision="shell-pool-fixture-v1"))
print("Scope:",result.outputs.integration_scope)
print("NFNT:",result.outputs.nfnt_status)
print("Equipment/personnel area m2:",result.outputs.equipment_area_m2,result.outputs.personnel_area_m2)
print("Financial consequence:",result.outputs.financial_consequence,result.outputs.currency)
print("Annual financial risk:",result.outputs.financial_risk_per_year,result.outputs.currency)
