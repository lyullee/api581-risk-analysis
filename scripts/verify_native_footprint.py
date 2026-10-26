"""Actual optional-engine field/area and flash-bridge verification."""
import json
from pathlib import Path
import runpy
import numpy as np
from api581 import DomainError
from api581.api import dispersion


def main():
    factory = runpy.run_path('examples/native_dispersion_pool.py')['request']
    baseline = factory('slabx').model_dump()|dict(crosswind_half_span_m=250.,crosswind_points_per_side=65)
    field = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**baseline)).outputs
    assert field.footprint_status == 'closed_on_supplied_grid' and field.threshold_area_m2 > 0
    from slabx.core.source import EvaporatingPool
    from slabx.core.plume import run_dispersion
    from slabx.post.concentration import concentration_field
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    substance = Substance(name='methane',mw=.016043,cp_vapour=2238.,cp_liquid=3348.5,
        dh_vap=509900.,T_boil=111.7,rho_liquid=424.1)
    atmosphere = Atmosphere(u_ref=1.94,z_ref=3.,T=290.,rh=50.,z0=.0002,stability='E',p=101325.)
    source = EvaporatingPool(substance=substance,rate=116.93,area=116.93/.167,duration=107.)
    trajectory,_ = run_dispersion(source,atmosphere,LegacyThermo(substance),water_backend(),x_max=2000.,n_puff_steps=40)
    direct = concentration_field(trajectory,atmosphere,z=1.,t_avg=80.,t_release=107.,meander_closure='ermak')
    actual = np.asarray(field.volume_fraction_by_crosswind_then_downwind)
    np.testing.assert_array_equal(actual,direct.at_y(field.crosswind_distance_m))
    np.testing.assert_allclose(actual,actual[::-1,:],rtol=1e-12,atol=1e-15)
    fine = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**(baseline|dict(crosswind_points_per_side=129)))).outputs
    delta = abs(fine.threshold_area_m2-field.threshold_area_m2)/fine.threshold_area_m2
    assert delta < .005
    narrow = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**(baseline|dict(crosswind_half_span_m=1.)))).outputs
    assert narrow.footprint_status == 'boundary_censored' and narrow.threshold_area_m2 is None
    assert set(narrow.boundary_sides)&{'negative_crosswind','positive_crosswind'}
    try:
        dispersion.native_pool_flash_fire(dispersion.NativePoolFlashFireInput(**(baseline|dict(crosswind_half_span_m=1.,receptor_height_m=0.)),criterion_role='qualified_lfl'))
    except DomainError as exc:
        assert exc.code == 'dispersion_footprint_unusable'
    else:
        raise AssertionError('Censored area became valid flash consequence')
    grade_input = baseline|dict(receptor_height_m=0.)
    grade = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**grade_input)).outputs
    flash = dispersion.native_pool_flash_fire(dispersion.NativePoolFlashFireInput(**grade_input,criterion_role='qualified_lfl')).outputs
    assert flash.personnel_area_m2 == grade.threshold_area_m2 and flash.equipment_area_m2 == .25*grade.threshold_area_m2
    assert flash.receptor_height_m == 0.
    hydrogen = factory('slabx-lh2').model_dump()|dict(crosswind_half_span_m=50.,crosswind_points_per_side=65)
    h2 = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**hydrogen)).outputs
    assert h2.premise_status == 'within_premise' and h2.threshold_area_m2 > 0
    hydrogen['atmosphere']['wind_speed_m_s'] = .3
    invalid = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(**hydrogen)).outputs
    assert invalid.footprint_status == 'premise_violated' and invalid.threshold_area_m2 is None
    report = dict(checks=['native_at_y_exact_field_equivalence','crosswind_symmetry',
        'crosswind_grid_refinement','lateral_censoring','censored_flash_bridge_rejection',
        'native_flash_quarter_area_mapping','lh2_planar_execution','lh2_premise_blocks_area'],
        baseline_area_m2=field.threshold_area_m2,refined_area_m2=fine.threshold_area_m2,
        baseline_receptor_height_m=field.receptor_height_m,grade_level_flash_area_m2=flash.personnel_area_m2,
        crosswind_refinement_relative_difference=delta,hydrogen_area_m2=h2.threshold_area_m2,
        engine_versions=field.engine_versions,engine_source_fingerprints=h2.engine_source_fingerprints)
    Path('tmp/native-footprint-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
