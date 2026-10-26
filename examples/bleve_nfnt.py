"""Illustrative hot-water rupture -> two-phase BLEVE -> NFNT -> area risk.

Flash fraction, released rates/masses and damage factor are caller assumptions.
No combustion, automatic EOS/flash solver or LH2 validation is implied.
"""
from api581 import Context
from api581.api import effects, release, level1, consequence, frequency, risk


def main():
    context=Context(asset_id="illustrative-hot-water-drum",source_revision="nfnt-inputs-1")
    fit=effects.BlastFitDomainInput(minimum_scaled_distance_m_kg13=1.5,maximum_scaled_distance_m_kg13=1000,
        engineering_basis="Illustrative numerical bracket only; experimental validity must be qualified")
    flashed=release.bleve_flashed_amount(release.BleveFlashedAmountInput(stored_liquid_mass_kg=5000,
        liquid_flash_mass_fraction=.2,molecular_weight_kg_kmol=18.015),context=context)
    bleve=effects.bleve_consequence(effects.BleveConsequenceInput(hole="rupture",fit_domain=fit,
        burst_pressure_pa_abs=2e6,storage_temperature_k=470,flashed_amount_kmol=flashed.outputs.flashed_amount_kmol,
        stored_vapor=effects.VaporPortionInput(vapor_volume_m3=2,heat_capacity_ratio=1.3)),context=context)
    physical=effects.physical_explosion_consequence(effects.PhysicalExplosionConsequenceInput(hole="rupture",fit_domain=fit,
        burst_pressure_pa_abs=2e6,vapor_volume_m3=2,heat_capacity_ratio=1.3),context=context)
    generic=frequency.generic(frequency.GenericInput(component_type="DRUM"),context=context)
    cases=[]
    risk_scenarios=[]
    for hole,rate,mass in [("small",.5,10),("medium",2,100),("large",10,1000),("rupture",30,5000)]:
        steam=level1.steam_area(level1.SteamAreaInput(adjusted_rate_kg_s=rate,released_mass_kg=mass),context=context)
        case=consequence.NfntFrequencyCaseInput(hole=hole,non_ignition_probability=1,
            generic_frequency_per_year=generic.outputs.by_hole_per_year[hole],
            physical_equipment_area_m2=physical.outputs.equipment_area_m2 if hole == "rupture" else 0,
            physical_personnel_area_m2=physical.outputs.personnel_area_m2 if hole == "rupture" else 0,
            bleve_equipment_area_m2=bleve.outputs.equipment_area_m2 if hole == "rupture" else 0,
            bleve_personnel_area_m2=bleve.outputs.personnel_area_m2 if hole == "rupture" else 0,
            steam_chemical_personnel_area_m2=steam.outputs.personnel_area_m2)
        cases.append(case)
        area=consequence.level2_nfnt_case(consequence.Level2NfntCaseInput(
            **case.model_dump(exclude={"generic_frequency_per_year"})),context=context)
        occurrence=frequency.adjusted(frequency.AdjustedInput(generic_frequency_per_year=case.generic_frequency_per_year,
            total_damage_factor=10,management_factor=1),context=context)
        # Financial consequence is intentionally not modeled in this area-risk example.
        risk_scenarios.append(risk.RiskScenarioInput(scenario_id=hole,annual_failure_frequency=occurrence.outputs.annual_failure_frequency,
            equipment_area_m2=area.outputs.equipment_area_m2,personnel_area_m2=area.outputs.personnel_area_m2,financial_consequence=0))
    summary=consequence.level2_nfnt_summary(consequence.Level2NfntSummaryInput(cases=cases),context=context)
    result=risk.aggregate(risk.AggregateInput(scenarios=risk_scenarios,currency="USD"),context=context)
    print("Liquid/vapor BLEVE TNT equivalents (kg):",bleve.outputs.liquid_tnt_equivalent_mass_kg,bleve.outputs.vapor_tnt_equivalent_mass_kg)
    print("NFNT GFF-weighted equipment/personnel area (m2):",summary.outputs.equipment_area_m2,summary.outputs.personnel_area_m2)
    print("Equipment/personnel area risk (m2/year):",result.outputs.equipment_area_risk_m2_per_year,result.outputs.personnel_area_risk_m2_per_year)
    print("DF10 is illustrative; financial risk is not assessed by this example.")
    return result


if __name__ == "__main__":
    main()
