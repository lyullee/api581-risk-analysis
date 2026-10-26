"""Qualified chart-area routing and crack history -> caustic SCC DF."""
from api581 import Context
from api581.api import damage


def request(**changes):
    return damage.CausticScreenedAssessmentInput(**(dict(
        screening=dict(material='carbon_steel',caustic_present=True,screening_basis='Qualified steel and residual/local caustic exposure'),
        susceptibility=dict(stress_relieved=False,cracking_history='never_detected',
            fabrication_history_basis='Qualified as-fabricated and caustic-crack history fixture',
            plot=dict(maximum_metal_temperature_k=320.,naoh_mass_fraction=.02,chart_area='A',chart_unit_basis='printed_si',
                heat_traced=True,steamed_out_before_water_flush=False,
                plot_basis='Independently qualified Figure6.1M area-A fixture; local/upset temperature/concentration reviewed')),
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        assessment_basis='Owner-qualified caustic-specific inspection grade, coverage and period per6.6.3')|changes))


def main():
    output=damage.caustic_screened_assessment(request(),context=Context(
        asset_id='caustic-screened-fixture',source_revision='qualified-figure-area-v1')).outputs
    assert output.effective_susceptibility=='medium' and output.severity_index==500
    assert output.base_damage_factor==25.
    print('Susceptibility / branch:',output.effective_susceptibility,output.decision_branch)
    print('SVI / base / DF:',output.severity_index,output.base_damage_factor,output.damage_factor)
    return output


if __name__=='__main__':
    main()
