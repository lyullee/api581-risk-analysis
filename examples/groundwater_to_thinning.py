"""Groundwater TKS + independent specialist rate -> qualified thinning DF."""
from api581 import Context
from api581.api import damage


def request(**changes):
    return damage.GroundwaterThinningAssessmentInput(**(dict(corrosion=dict(
        chemistry=dict(chloride_mg_l=100.,sulfate_mg_l=20.,dissolved_co2_mg_l=5.,bicarbonate_mg_l=80.,
            carbonate_mg_l=1.,sulfide_mg_l=.5,ammonia_mg_l=2.,
            concentration_basis='Illustrative independent species mg/L; no overlapping total carbon/nitrogen reports'),
        qualified_rate=dict(corrosion_rate_m_year=.0005,unit_basis='printed_si'),
        steel_applicability_basis='Qualified steel/component/groundwater representativeness fixture',
        specialist_rate_basis='Independent competent-specialist rate fixture, not inferred from TKS'),
        assessment_distribution='local',starting_thickness_m=.01,elapsed_years=5.,
        strength=dict(method='internal_pressure_eq2_18',differential_pressure_pa=2e6,diameter_m=.5,
            flow_stress_pa=250e6,starting_thickness_m=.01,shape='cylinder'),
        inspections=dict(confidence='high',inspections_a=1),
        conditions=dict(monitoring=dict(row=dict(mechanism='other'),methods=[],organized_monitoring_plan=False),
            injection=dict(component_scope='piping',injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
            deadleg=dict(component_scope='piping',deadleg_present=False,highly_effective_targeted_inspection=False)),
        qualification_basis='Illustrative common wall baseline, qualified local inspection; not site validation')|changes))


def main():
    output=damage.groundwater_thinning_assessment(request(),context=Context(
        asset_id='groundwater-qualified-rate-demo',source_revision='specialist-rate-fixture-v1')).outputs
    assert output.total_key_species_mg_l==208.5
    assert output.corrosivity_category=='high' and not output.tks_to_rate_model_available
    assert abs(output.wall_loss_fraction-.25)<1e-12
    print('TKS / externally qualified rate:',output.total_key_species_mg_l,output.corrosion_rate_m_year)
    print('Category / wall-loss fraction / DF:',output.corrosivity_category,output.wall_loss_fraction,output.thinning_damage_factor)
    return output


if __name__=='__main__':
    main()
