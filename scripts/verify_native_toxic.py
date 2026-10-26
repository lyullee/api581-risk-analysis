"""Real chlorine native field through historical criterion and conditional area."""
import math
import json
from pathlib import Path
import runpy
import numpy as np
from api581 import DomainError
from api581.api import dispersion


def main():
    factory = runpy.run_path('examples/native_toxic_pool.py')['request']
    request = factory()
    result = dispersion.native_pool_toxic_consequence(request).outputs
    expected_ppm = math.exp(((5+8.29)/.92-math.log(600.))/2)
    assert result.pure_component_limit_ppm == expected_ppm
    from slabx.core.source import EvaporatingPool
    from slabx.core.plume import run_dispersion
    from slabx.post.concentration import concentration_field
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    substance = Substance(name='chlorine',mw=.070906,cp_vapour=479.,cp_liquid=950.,dh_vap=287000.,T_boil=239.11,rho_liquid=1467.)
    atmosphere = Atmosphere(u_ref=3.,z_ref=10.,T=293.,p=101325.,rh=50.,z0=.01,stability='D')
    source = EvaporatingPool(substance=substance,rate=1.,area=10.,duration=600.)
    trajectory,_ = run_dispersion(source,atmosphere,LegacyThermo(substance),water_backend(),x_max=5000.,n_puff_steps=40)
    field = concentration_field(trajectory,atmosphere,z=0.,t_avg=600.,t_release=600.,meander_closure='ermak')
    np.testing.assert_array_equal(result.downwind_distance_m,field.x)
    np.testing.assert_array_equal(result.centreline_volume_fraction,field.peak)
    np.testing.assert_array_equal(result.volume_fraction_by_crosswind_then_downwind,field.at_y(result.crosswind_distance_m))
    assert result.averaging_time_s == result.exposure_duration_s == result.release_duration_s == 600.
    assert result.equipment_area_m2 == 0.
    assert result.personnel_area_m2 == .8*result.threshold_area_m2
    assert result.unweighted_cloud_area_m2 == result.threshold_area_m2
    source_values = request.source.model_dump()
    native = dispersion.native_pool_footprint(dispersion.NativePoolFootprintInput(
        **{k:v for k,v in source_values.items() if k not in {'available_mass_kg','detection_maximum_duration_s'}},
        engine='slabx',lh2_plume_width_coupling=False,release_duration_s=600.,averaging_time_s=600.,
        threshold_volume_fraction=expected_ppm/1e6,threshold_source='Independent historical criterion anchor')).outputs
    assert result.threshold_area_m2 == native.threshold_area_m2
    for override,code in [(dict(crosswind_half_span_m=1.),'dispersion_footprint_unusable'),
                          (dict(available_mass_kg=60.),'toxic_exposure_duration_unsupported')]:
        values = request.model_dump()
        values['source'].update(override)
        try:
            dispersion.native_pool_toxic_consequence(dispersion.NativePoolToxicConsequenceInput(**values))
        except DomainError as exc:
            assert exc.code == code
        else:
            raise AssertionError('Unusable toxic source/field returned consequence')
    report = dict(checks=['historical_probit50_ppm_anchor','direct_native_centreline_exact',
        'direct_native_planar_exact','exposure_average_and_release_window_mapping','independent_native_area_chain',
        'nonignition_probability_once','toxic_equipment_zero','censored_area_rejected','short_source_window_rejected'],
        criterion_ppm=result.pure_component_limit_ppm,raw_area_m2=result.threshold_area_m2,
        conditional_personnel_area_m2=result.personnel_area_m2,engine_versions=result.engine_versions,
        exposure_model_basis=result.exposure_model_basis)
    Path('tmp/native-toxic-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
