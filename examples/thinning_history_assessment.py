"""Measured baseline reset with dated, qualified inspection eligibility."""
from pathlib import Path
import runpy
from api581 import Context
from api581.api import damage


def history():
    def record(identity,at,grade,qualified=True):
        return dict(inspection_id=identity,performed_at=at,effectiveness=grade,
            qualified_for_component_mechanism=qualified,inspection_basis='Qualified performed inspection/coverage fixture')
    return damage.ThinningInspectionHistoryInput(installed_at='2010-01-01T00:00:00Z',assessment_at='2025-01-01T00:00:00Z',
        baseline_type='measured',measured_baseline=dict(inspection_id='baseline',measured_at='2021-01-01T00:00:00Z',
            thickness_m=.01,high_quality_inspection=True,high_confidence_accuracy=True,
            reset_basis='Qualified reliable measured thickness after significant process change'),
        days_per_year=365.25,period_and_year_basis='Same current-process plan period, UTC elapsed time and365.25day year convention',
        baseline_boundary_policy='exclude_baseline_time',inspections=[
            record('old','2020-01-01T00:00:00Z','a'),record('baseline','2021-01-01T00:00:00Z','a'),
            record('b1','2022-01-01T00:00:00Z','b'),record('c1','2023-01-01T00:00:00Z','c'),
            record('unqualified','2024-01-01T00:00:00Z','a',False),record('later','2026-01-01T00:00:00Z','a'),
            record('e1','2021-06-01T00:00:00Z','e')])


def request():
    factory=runpy.run_path(str(Path(__file__).with_name('multiple_thinning_mechanisms.py')))['request']
    source=factory()
    return damage.ThinningHistoryAssessmentInput(history=history(),selection=source.selection,
        prior=dict(confidence='high'),strength=source.strength,conditions=source.conditions,
        qualification_basis='Qualified common measured wall baseline, local coverage and performed-record eligibility')


def main():
    output=damage.thinning_history_assessment(request(),context=Context(
        asset_id='period-consistent-thinning-demo',source_revision='measured-baseline-history-v1')).outputs
    assert output.elapsed_years==4. and abs(output.wall_loss_fraction-.12)<1e-12
    assert (output.inspections_a,output.inspections_b,output.inspections_c,output.inspections_d)==(0,1,1,0)
    print('Baseline / years:',output.baseline_at,output.elapsed_years)
    print('Eligible / excluded:',output.eligible_inspection_ids,output.excluded_inspection_reasons)
    print('Wall loss / DF:',output.wall_loss_fraction,output.thinning_damage_factor)
    return output


if __name__=='__main__':
    main()
