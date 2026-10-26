"""Optional EOS/native engines: one steady pool LFL scenario, no event weighting."""
from pathlib import Path
import runpy
from api581 import Context
from api581.api import dispersion


def request(**changes):
    factory=runpy.run_path(str(Path(__file__).with_name('flashed_boiling_pool.py')))['request']
    values=factory().model_dump()|dict(receptor_height_m=0.,threshold_volume_fraction=.021,
        threshold_source='Owner-qualified illustrative propane LFL fixture and1s averaging; no site/model validation',
        crosswind_half_span_m=100.,crosswind_points_per_side=129,criterion_role='qualified_lfl')|changes
    return dispersion.FlashedBoilingPoolFlashFireInput(**values)


def main():
    result=dispersion.flashed_boiling_pool_flash_fire(request(),context=Context(
        asset_id='propane-steady-pool-lfl-scenario',source_revision='qualified-grid-fixture-v1'))
    output=result.outputs
    print('Footprint:',output.footprint_status,output.threshold_area_m2)
    print('Personnel/equipment areas:',output.personnel_area_m2,output.equipment_area_m2)
    print('Grid:',output.downwind_node_count,output.crosswind_node_count)
    print('Selected steady pool only; startup and jet consequences remain unmodeled.')
    return output


if __name__=='__main__':
    main()
