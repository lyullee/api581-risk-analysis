"""Two-phase correlations + explicit raw footprints -> correlated-event risk.

Footprints, flash properties, reference and phase-weighting basis are fixtures,
not a dispersion/EOS run or independently validated installation inputs.
"""
import _bootstrap  # noqa: F401
from api581 import Context
from api581.api import events, level2


def main():
    context=Context(asset_id="illustrative-two-phase-component",source_revision="two-phase-event-inputs-1")
    cases=[]
    for i,(hole,rate) in enumerate([("small",.5),("medium",2),("large",5),("rupture",25)],start=1):
        continuous=hole != "rupture"
        tree=events.two_phase_ignition(events.TwoPhaseIgnitionInput(release_type="continuous" if continuous else "instantaneous",
            case_type="leakage" if continuous else "rupture",adjusted_mass_rate_kg_s=rate,flammable_mass_fraction=.8,flash_mass_fraction=.25,
            liquid_flash_point_temperature_k=290,vapor_flash_point_temperature_k=270,vapor_molecular_weight_kg_kmol=44,
            storage_temperature_k=330,autoignition_temperature_k=600,correlation_basis_source="Illustrative owner-qualified phase properties",
            reference_basis="qualified_reference",qualified_reference_temperature_k=294.2611111111111,
            reference_source="Explicit illustrative70F reference; not official C16 erratum",
            mixing_basis="qualified_vapor_weight",weighting_source="Explicit illustrative vapor weighting; not an authorized equation correction"),context=context)
        p=tree.outputs.terminal_probabilities
        footprints={"pool_fire":(0,0) if continuous else (600*i,900*i),"jet_fire":(0,0),
            "fireball":(0,0) if continuous else (1500*i,3000*i),"vce":(1000*i,2000*i),"flash_fire":(100*i,400*i)}
        correlated=level2.CorrelatedJetPoolInput(probability=p["jet_pool_max"],jet_equipment_area_m2=400*i,
            jet_personnel_area_m2=100*i,pool_equipment_area_m2=100*i,pool_personnel_area_m2=500*i,
            consequence_source="Supplied illustrative jet/pool footprints; one shared immediate event") if continuous else None
        cases.append(level2.ScenarioCaseInput(hole=hole,release_type="continuous" if continuous else "instantaneous",
            outcomes=[level2.FlammableOutcomeInput(event=e,probability=p[e],equipment_area_m2=a,personnel_area_m2=b)
                for e,(a,b) in footprints.items()],correlated_jet_pool=correlated,
            non_ignition_probability=tree.outputs.non_ignition_probability,
            fireball_applicability_basis=tree.outputs.fireball_applicability_basis,
            event_tree_source="Computed two-phase probabilities with explicit reference/weighting basis",
            consequence_source="Owner-supplied footprint fixtures; no dispersion executed",toxic_components=[],toxic_applicability="not_applicable",
            toxic_applicability_source="Illustrative non-toxic mixture assumption",
            nfnt=level2.NfntAreasInput(consequence_source="Supplied illustrative non-ignition footprints",
                physical_equipment_area_m2=1000 if not continuous else 0,physical_personnel_area_m2=1800 if not continuous else 0)))
    result=level2.assessment(level2.AssessmentInput(component_type="DRUM",management_score=500,total_damage_factor=10,
        damage_factor_source="Explicit illustrative DF",cases=cases,
        financial=level2.FinancialBasisInput(repair=level2.RepairCostInput(component_type="DRUM",material_id="carbon_steel",
            price_factor_since_2001=2,usd_to_output_currency=1,cost_basis_year=2026,currency="USD"),
            outage=level2.ComponentOutageInput(component_type="DRUM",outage_multiplier=1,
                override_days={"small":2,"medium":5,"large":10,"rupture":30}),equipment_cost_per_m2=1000,
            production_cost_per_day=10000,population_density_per_m2=.001,cost_per_injury=1e6,
            weighted_cleanup_volume_m3=0,cleanup_cost_per_m3=0)),context=context)
    print("Equipment/personnel consequence areas (m2):",result.outputs.equipment_area_m2,result.outputs.personnel_area_m2)
    print("Financial consequence/annual risk (illustrative2026 USD):",result.outputs.financial_consequence,result.outputs.financial_risk_per_year)
    print("Jet/pool immediate maxima were weighted once; supplied footprints are illustrative.")
    return result


if __name__ == "__main__":
    main()
