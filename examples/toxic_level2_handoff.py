"""Explicit cell-history fixtures -> toxic dose -> footprints -> GFF average.

These are invented concentration histories for demonstrating a Python handoff;
no slabx engine is invoked and spatial cell classification is only illustrative.
"""
from api581 import Context
from api581.api import effects, properties, consequence, frequency


def main():
    context=Context(asset_id="illustrative-toxic-cloud",source_revision="explicit-cell-history-fixture-1")
    threshold=effects.toxic_species_threshold(effects.ToxicSpeciesThresholdInput(
        fluid="hydrogen_sulfide",exposure_duration_s=600),context=context)
    mixture=consequence.toxic_mixture_limit(consequence.ToxicMixtureLimitInput(
        pure_component_limit_ppm=threshold.outputs.concentration_ppm,toxic_mole_fraction=.05),context=context)
    generic=frequency.generic(frequency.GenericInput(component_type="DRUM"),context=context)
    cases=[]
    for hole,scale in [("small",.2),("medium",.5),("large",1),("rupture",2)]:
        area=0
        for peak_ppm in [30,120,300]:
            result=effects.toxic_dose_profile(effects.ToxicDoseProfileInput(fluid="hydrogen_sulfide",interpolation="linear",
                profile=[effects.ConcentrationPointInput(time_s=t,concentration_ppm=c) for t,c in [(0,0),(300,peak_ppm*scale),(600,0)]],
                profile_source="Invented species-resolved cell-center history;100m2 disjoint cells"),context=context)
            if result.outputs.fatality_probability >= .5:
                area+=100
        cases.append(consequence.ToxicFrequencyCaseInput(hole=hole,generic_frequency_per_year=generic.outputs.by_hole_per_year[hole],
            non_ignition_probability=.8,components=[consequence.ToxicCloudAreaInput(component_id="hydrogen_sulfide",cloud_area_m2=area,
                selected_criterion_source="Table4.14 + transient dose extension,50% probit; illustrative cell-center approximation")]))
    summary=consequence.level2_toxic_summary(consequence.Level2ToxicSummaryInput(cases=cases),context=context)
    row=properties.toxic_impact_table(properties.ToxicImpactTableInput(fluid="hydrogen_sulfide"),context=context)
    print("Printed H2S A/B/N:",row.outputs.probit_intercept,row.outputs.probit_slope,row.outputs.concentration_exponent)
    print("Constant600s species /5mol% mixture criterion (ppm):",threshold.outputs.concentration_ppm,mixture.outputs.modified_mixture_limit_ppm)
    print("By-hole nonignition-weighted personnel area (m2):",summary.outputs.by_hole_personnel_area_m2)
    print("GFF-weighted personnel area (m2):",summary.outputs.personnel_area_m2)
    print("Fixture demonstration; not an actual dispersion result or current toxic-exposure guidance.")
    return summary


if __name__ == "__main__":
    main()
