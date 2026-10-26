"""Explicit optional-engine verification, separate from dependency-free unit tests."""
from concurrent.futures import ThreadPoolExecutor
import importlib.metadata
import json
from pathlib import Path
import runpy
import sys
import numpy as np
from api581.api import dispersion


def main():
    factory = runpy.run_path('examples/native_dispersion_pool.py')['request']
    def run(request):
        return dispersion.native_pool_centreline(request).outputs
    baseline = factory('slabx')
    # Native direct call independently spells out all mapping units/defaults.
    from slabx.core.plume import run_dispersion
    from slabx.core.source import EvaporatingPool
    from slabx.post.concentration import concentration_field
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    substance = Substance(name='methane',mw=.016043,cp_vapour=2238.,cp_liquid=3348.5,
        dh_vap=509900.,T_boil=111.7,rho_liquid=424.1)
    atmosphere = Atmosphere(u_ref=1.94,z_ref=3.,T=290.,rh=50.,z0=.0002,stability='E',p=101325.)
    source = EvaporatingPool(substance=substance,rate=116.93,area=116.93/.167,duration=107.)
    trajectory,_ = run_dispersion(source,atmosphere,LegacyThermo(substance),water_backend(),x_max=2000.,n_puff_steps=40)
    field = concentration_field(trajectory,atmosphere,z=1.,t_avg=80.,t_release=107.,meander_closure='ermak')
    adapted = run(baseline)
    np.testing.assert_array_equal(adapted.downwind_distance_m,field.x)
    np.testing.assert_array_equal(adapted.centreline_volume_fraction,field.peak)
    assert adapted.native_threshold_distance_m == field.distance_to(.05)
    assert adapted.threshold_status == 'interpolated'
    boundary = run(baseline.model_copy(update={'plume_distance_limit_m':100.,'threshold_volume_fraction':.001}))
    assert boundary.threshold_status == 'boundary_censored' and boundary.threshold_distance_m is None
    assert boundary.native_grid_maximum_downwind_distance_m > 100.
    absent = run(baseline.model_copy(update={'threshold_volume_fraction':1.}))
    assert absent.threshold_status == 'not_reached' and absent.native_threshold_distance_m is None
    # Both corrections live only in the child; host module namespace is unaffected.
    import slabx.core.plume as plume
    before = {k:id(v) for k,v in vars(plume).items() if callable(v)}
    hydrogen = factory('slabx-lh2')
    h2 = run(hydrogen)
    assert h2.engine_versions == {'slabx':'1.0.8','slabx-lh2':'0.2.0'}
    assert h2.premise_status == 'within_premise'
    low_wind = hydrogen.model_dump()
    low_wind['atmosphere']['wind_speed_m_s'] = .3
    violated = run(dispersion.NativePoolCentrelineInput(**low_wind))
    assert violated.premise_status == 'violated' and violated.threshold_status == 'premise_violated'
    assert violated.threshold_distance_m is None
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run,[hydrogen,hydrogen.model_copy(update={'lh2_plume_width_coupling':False})]))
    assert results[0].centreline_volume_fraction == h2.centreline_volume_fraction
    assert before == {k:id(v) for k,v in vars(plume).items() if callable(v)}
    assert 'slabx_lh2' not in sys.modules
    report = {'checks':['native_direct_exact_array_equivalence','kg_kmol_and_humidity_unit_mapping',
        'boundary_censoring','no_exceedance_nan_to_null','lh2_native_execution','lh2_premise_violation_blocks_distance',
        'concurrent_process_isolation_and_repeatability','host_module_globals_unchanged'],
        'versions':{name:importlib.metadata.version(name) for name in ('slabx','slabx-lh2','numpy','scipy','CoolProp')},
        'engine_fingerprints':h2.engine_source_fingerprints,
        'baseline_distance_m':adapted.threshold_distance_m,'hydrogen_distance_m':h2.threshold_distance_m,
        'low_wind_premise_ratio':violated.maximum_vertical_to_horizontal_velocity_ratio}
    Path('tmp/native-dispersion-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
