"""Computed fire/ignition + supplied cloud footprints/DF -> Level2 risk.

Illustrative owner assumptions, no real dispersion engine or automatic damage
assessment. Gas properties, cloud masses/areas, probabilities and prices require
engineering qualification before any installation use.
"""
import _bootstrap  # noqa: F401
from api581 import Context
from api581.api import release, effects, events, level2


def main():
    context=Context(asset_id="illustrative-level2-drum",source_revision="level2-inputs-1")
    fit=effects.BlastFitDomainInput(minimum_scaled_distance_m_kg13=1.5,maximum_scaled_distance_m_kg13=1000,
        engineering_basis="Illustrative numerical interval; not independently validated")
    cases=[]
    for hole,diameter,cloud_mass,cloud_area,toxic_area in [
        ("small",.00635,5,20,10),("medium",.0254,50,100,100),
        ("large",.1016,100,300,200),("rupture",.2,500,1000,2000)]:
        source=release.gas(release.GasInput(diameter_m=diameter,upstream_pressure_pa_abs=1e6,
            temperature_k=300,molecular_weight_kg_kmol=44,heat_capacity_ratio=1.15),context=context)
        rates=release.flammable_phase_rates(release.FlammablePhaseRatesInput(adjusted_mass_rate_kg_s=source.outputs.mass_rate_kg_s,
            flammable_mass_fraction=.8,flash_mass_fraction=1),context=context)
        ignition=events.single_phase_ignition(events.SinglePhaseIgnitionInput(phase="vapor",
            release_type="instantaneous" if hole == "rupture" else "continuous",case_type="rupture" if hole == "rupture" else "leakage",
            flammable_rate_kg_s=rates.outputs.flammable_vapor_rate_kg_s,flash_point_temperature_k=270,
            correlation_basis_source="Owner-qualified illustrative flash point270K; not a fluid database lookup",
            molecular_weight_kg_kmol=44,storage_temperature_k=300,autoignition_temperature_k=600,
            reference_basis="qualified_reference",qualified_reference_temperature_k=294.2611111111111,
            reference_source="Illustrative70F reference selected explicitly; not an authorized C16 erratum"),context=context)
        probabilities=ignition.outputs.terminal_probabilities
        vce=effects.vce_blast_consequence(effects.VceBlastConsequenceInput(flammable_cloud_mass_kg=cloud_mass,
            combustion_heat_j_kg=46e6,explosion_yield=1,tnt_heat_j_kg=4.648e6,
            tnt_heat_source="Illustrative explicit4.648MJ/kg assumption",
            mass_basis="between_flammability_limits",yield_engineering_basis="Source-recommended yield1 for supplied LFL/UFL cloud mass",
            fit_domain=fit),context=context)
        flash=effects.flash_fire(effects.FlashFireInput(area_within_lfl_m2=cloud_area),context=context)
        jet_equipment=jet_personnel=fireball_equipment=fireball_personnel=0
        physical_equipment=physical_personnel=0
        if hole != "rupture":
            power=effects.jet_fire_power(effects.JetFirePowerInput(mass_rate_kg_s=.8*source.outputs.mass_rate_kg_s,
                heat_of_combustion_j_kg=46e6),context=context)
            jet_equipment=effects.jet_fire_distance(effects.JetFireDistanceInput(radiated_power_w=power.outputs.radiated_power_w,
                threshold_w_m2=37800,transmissivity_model="constant",atmospheric_transmissivity=.8),context=context).outputs.consequence_area_m2
            jet_personnel=effects.jet_fire_distance(effects.JetFireDistanceInput(radiated_power_w=power.outputs.radiated_power_w,
                threshold_w_m2=12600,transmissivity_model="constant",atmospheric_transmissivity=.8),context=context).outputs.consequence_area_m2
        else:
            fireball=effects.fireball_consequence(effects.FireballConsequenceInput(available_mass_kg=2000,
                flammable_mass_fraction=.8,heat_of_combustion_j_kg=46e6,burst_pressure_pa_abs=1e6,
                atmosphere=effects.AtmosphereInput(transmissivity_model="constant",constant_transmissivity=.8),
                geometry_basis="elevated_sphere_maximum",maximum_distance_m=1000),context=context)
            fireball_equipment,fireball_personnel=fireball.outputs.equipment_area_m2,fireball.outputs.personnel_area_m2
            physical=effects.physical_explosion_consequence(effects.PhysicalExplosionConsequenceInput(hole=hole,
                fit_domain=fit,vapor_volume_m3=2,heat_capacity_ratio=1.15,burst_pressure_pa_abs=1e6),context=context)
            physical_equipment,physical_personnel=physical.outputs.equipment_area_m2,physical.outputs.personnel_area_m2
        rows=[("pool_fire",probabilities["pool_fire"],0,0),("jet_fire",probabilities["jet_fire"],jet_equipment,jet_personnel),
              ("fireball",probabilities["fireball"],fireball_equipment,fireball_personnel),
              ("vce",probabilities["vce"],vce.outputs.equipment_area_m2,vce.outputs.personnel_area_m2),
              ("flash_fire",probabilities["flash_fire"],flash.outputs.equipment_area_m2,flash.outputs.personnel_area_m2)]
        cases.append(level2.ScenarioCaseInput(hole=hole,release_type="instantaneous" if hole == "rupture" else "continuous",
            outcomes=[level2.FlammableOutcomeInput(event=event,probability=p,equipment_area_m2=e,personnel_area_m2=i) for event,p,e,i in rows],
            non_ignition_probability=ignition.outputs.non_ignition_probability,
            event_tree_source="Calculated source ignition/Table5.3 and Figure5.3/5.4 paths with qualified reference",
            fireball_applicability_basis=ignition.outputs.fireball_applicability_basis,
            consequence_source="Computed jet/fireball/VCE/flash + supplied flammable cloud inputs",
            toxic_applicability="evaluated",toxic_applicability_source="Illustrative toxic component in mixture",
            toxic_components=[level2.ToxicCloudAreaInput(component_id="hydrogen_sulfide",cloud_area_m2=toxic_area,
                selected_criterion_source="Owner-supplied illustrative probit50% footprint; not a dispersion result")],
            nfnt=level2.NfntAreasInput(physical_equipment_area_m2=physical_equipment,physical_personnel_area_m2=physical_personnel,
                consequence_source="Computed gas-vessel physical explosion; no liquid/steam/chemical event assumed")))
    result=level2.assessment(level2.AssessmentInput(component_type="DRUM",management_score=500,total_damage_factor=10,
        damage_factor_source="Explicit illustrative total DF; no automated damage assessment",cases=cases,
        financial=level2.FinancialBasisInput(repair=level2.RepairCostInput(component_type="DRUM",material_id="carbon_steel",
            price_factor_since_2001=2,usd_to_output_currency=1,cost_basis_year=2026,currency="USD"),
            outage=level2.ComponentOutageInput(component_type="DRUM",outage_multiplier=1,
                override_days={"small":2,"medium":5,"large":10,"rupture":30}),equipment_cost_per_m2=1000,
            production_cost_per_day=10000,population_density_per_m2=.001,cost_per_injury=1e6,
            weighted_cleanup_volume_m3=0,cleanup_cost_per_m3=0)),context=context)
    print("Level2 equipment/personnel area (m2):",result.outputs.equipment_area_m2,result.outputs.personnel_area_m2)
    print("Annual failure frequency (1/year):",result.outputs.annual_failure_frequency)
    print("Financial consequence / annual risk (2026 USD,USD/year):",result.outputs.financial_consequence,result.outputs.financial_risk_per_year)
    print("Integration boundary:",result.outputs.integration_scope)
    return result


if __name__ == "__main__":
    main()
