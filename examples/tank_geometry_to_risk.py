"""Single bottom from geometry/soil to risk; DF and monetary valuation are supplied."""
import _bootstrap  # noqa: F401
from api581 import Context
from api581.api import tank

result = tank.bottom_integrated_assessment(tank.BottomIntegratedAssessmentInput(
    source=dict(tank_diameter_m=61.,fill_height_m=10.,fluid="gasoline",soil="coarse_sand",
        water_density_kg_m3=1000.,water_dynamic_viscosity_pa_s=.001,foundation="other",
        has_release_prevention_barrier=False,transition_hole_basis="api581_printed"),
    distance_to_groundwater_m=5.,
    economics=dict(repair=dict(material_id="carbon_steel",price_factor_since_2001=2.,
        usd_to_output_currency=1.,cost_basis_year=2026),outage_multiplier=1.,production_cost_per_day=1000.,
        currency="USD",cost_basis="Owner-qualified illustrative 2026 USD fixture; not market prices",
        cost_by_location_per_bbl=dict(in_dike=10.,surface_on_site=50.,surface_off_site=250.,
            subsoil=1500.,groundwater=5000.,surface_water=1500.),
        fraction_leaving_dike=.8,fraction_on_site=.25,fraction_off_site=.5),
    management_score=500.,total_damage_factor=3.,damage_factor_source="Externally assessed example DF fixture"),
    context=Context(asset_id="ast-001",component_id="bottom",source_revision="geometry-soil-fixture-v1"))
print("Scope:",result.outputs.integration_scope)
print("Leak bbl:",result.outputs.released_volume_by_hole_bbl["small"])
print("Rupture rate (undefined):",result.outputs.native_rate_by_hole_bbl_day["rupture"])
print("Groundwater arrival days:",result.outputs.groundwater_arrival_time_days)
print("Financial consequence:",result.outputs.financial_consequence,result.outputs.currency)
print("Annual frequency:",result.outputs.annual_failure_frequency)
print("Annual financial risk:",result.outputs.financial_risk_per_year,result.outputs.currency)
