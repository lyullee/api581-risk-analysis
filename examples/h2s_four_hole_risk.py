"""Four-hole H2S source -> flammable/toxic COF -> financial consequence -> risk.

Demonstration inputs, including DF, nonignition probabilities, pricing and outage
overrides, require owner qualification. Not automatic damage applicability/FFS.
"""
from api581 import Context
from api581.api import level1, release, financial, frequency, risk


def main():
    context=Context(asset_id="h2s-example-drum",source_revision="illustrative-owner-inputs")
    holes=[]
    for name,diameter in (("small",.00635),("medium",.0254),("large",.1016),("rupture",.2)):
        source=release.GasInput(diameter_m=diameter,upstream_pressure_pa_abs=1e6,temperature_k=300,
            molecular_weight_kg_kmol=34,heat_capacity_ratio=1.3)
        flame=level1.release_to_flammable(level1.ReleaseToFlammableInput(source=source,
            operating_temperature_k=300,component_mass_kg=9000,inventory_group_mass_kg=15000,
            detection="A",isolation="A",duration_hole=name,rupture_maximum_duration_s=600 if name == "rupture" else None,
            fluid="H2S",final_release_phase="gas",autoignition_temperature_k=533.15,mitigation_fraction=0),context=context)
        toxic=level1.toxic_component_consequence(level1.ToxicComponentConsequenceInput(
            fluid="h2s",release_phase="gas",release_type=flame.outputs.release_type,
            theoretical_rate_kg_s=flame.outputs.theoretical_rate_kg_s,released_mass_kg=flame.outputs.released_mass_kg,
            toxic_mass_fraction=1,available_mass_kg=flame.outputs.available_mass_kg,
            detection_maximum_duration_s=flame.outputs.maximum_duration_s,
            nonignition_probability=.9 if flame.outputs.release_type == "continuous" else .5),context=context)
        holes.append(level1.HoleAreasInput(hole=name,flammable_equipment_area_m2=flame.outputs.equipment_area_m2,
            flammable_personnel_area_m2=flame.outputs.personnel_area_m2,
            toxic_personnel_area_m2=toxic.outputs.personnel_area_m2,nfnt_personnel_area_m2=0))
    area=level1.consequence_summary(level1.ConsequenceSummaryInput(component_type="DRUM",holes=holes),context=context)
    costs=financial.level1_consequence(financial.Level1ConsequenceInput(
        repair=financial.ComponentRepairInput(component_type="DRUM",material_id="carbon_steel",
            price_factor_since_2001=2,usd_to_output_currency=1,cost_basis_year=2026,currency="USD"),
        outage=financial.ComponentOutageInput(component_type="DRUM",outage_multiplier=1,
            override_days={"small":2,"medium":5,"large":10,"rupture":30}),
        equipment_area_m2=area.outputs.equipment_area_m2,personnel_area_m2=area.outputs.personnel_area_m2,
        equipment_cost_per_m2=1000,production_cost_per_day=10000,population_density_per_m2=.001,
        cost_per_injury=1e6,weighted_cleanup_volume_m3=0,cleanup_cost_per_m3=0),context=context)
    generic=frequency.generic(frequency.GenericInput(component_type="DRUM"),context=context)
    occurrence=frequency.adjusted(frequency.AdjustedInput(generic_frequency_per_year=generic.outputs.total_per_year,
        total_damage_factor=10,management_factor=1),context=context)
    result=risk.aggregate(risk.AggregateInput(currency="USD",scenarios=[risk.RiskScenarioInput(scenario_id="weighted-four-hole-component",
        annual_failure_frequency=occurrence.outputs.annual_failure_frequency,
        equipment_area_m2=area.outputs.equipment_area_m2,personnel_area_m2=area.outputs.personnel_area_m2,
        financial_consequence=costs.outputs.financial_consequence)]),context=context)
    print("Mechanism-weighted final area (m2):",area.outputs.consequence_area_m2)
    print("Financial consequence (2026 USD, illustrative prices):",costs.outputs.financial_consequence)
    print("Annual failure frequency (1/year):",result.outputs.annual_failure_frequency)
    print("Annual financial risk (2026 USD/year):",result.outputs.financial_risk_per_year)
    return result


if __name__ == "__main__":
    main()
