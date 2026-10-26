"""Optional native methane LFL plane through API581 flash-fire area mapping."""
import runpy
from api581 import Context
from api581.api import dispersion


def main():
    from pathlib import Path
    factory = runpy.run_path(str(Path(__file__).with_name('native_dispersion_pool.py')))['request']
    inputs = factory('slabx').model_dump()|dict(crosswind_half_span_m=250.,crosswind_points_per_side=65,receptor_height_m=0.,
        threshold_source='Qualified illustrative methane LFL=.05 volume fraction;80s average assumption')
    result = dispersion.native_pool_flash_fire(dispersion.NativePoolFlashFireInput(**inputs,criterion_role='qualified_lfl'),
        context=Context(asset_id='native-pool-flash-fixture',source_revision='qualified-sampling-example-v1'))
    r = result.outputs
    print('Footprint:',r.footprint_status,r.threshold_area_m2,'m2 on supplied grid')
    print('Personnel/equipment:',r.personnel_area_m2,r.equipment_area_m2,'m2')
    print('Native grid:',r.downwind_node_count,r.crosswind_node_count)
    print('No ignition/GFF weighting; numeric grid and model applicability still require qualification.')


if __name__ == '__main__':
    main()
