"""Actual jet engine mapping, unsupported-domain and partition integration checks."""
import json
from pathlib import Path
import runpy
import numpy as np
from api581 import DomainError
from api581.api import dispersion


def main():
    factory = runpy.run_path('examples/native_jet_dispersion.py')['request']
    from slabx.core.source import HorizontalJet
    from slabx.core.vertical_jet import VerticalJet
    from slabx.core.plume import run_dispersion
    from slabx.post.concentration import concentration_field
    from slabx.submodels.atmosphere import Atmosphere
    from slabx.thermo.base import Substance, LegacyThermo, water_backend
    substance = Substance(name='propane',mw=.044096,cp_vapour=1670.,cp_liquid=2500.,
        dh_vap=425000.,T_boil=231.,rho_liquid=580.)
    atmosphere = Atmosphere(u_ref=3.,z_ref=10.,T=293.,p=101325.,rh=50.,z0=.01,stability='D')
    direct_fields = {}
    for orientation,source_type in [('horizontal_downwind',HorizontalJet),('vertical_up',VerticalJet)]:
        source = source_type(substance=substance,rate=1.,area=.01,duration=60.,liquid_fraction=0.,T_source=240.,height=3.)
        trajectory,_ = run_dispersion(source,atmosphere,LegacyThermo(substance),water_backend(),x_max=1000.,n_puff_steps=40)
        direct = concentration_field(trajectory,atmosphere,z=1.,t_avg=10.,t_release=60.,meander_closure='ermak')
        actual = dispersion.native_jet_centreline(factory(orientation=orientation)).outputs
        np.testing.assert_array_equal(actual.downwind_distance_m,direct.x)
        np.testing.assert_array_equal(actual.centreline_volume_fraction,direct.peak)
        assert actual.native_exit_velocity_m_s == source.exit_velocity(atmosphere)
        direct_fields[orientation] = (direct,actual)
    baseline = factory().model_dump()|dict(crosswind_half_span_m=30.,crosswind_points_per_side=129)
    footprint = dispersion.native_jet_footprint(dispersion.NativeJetFootprintInput(**baseline)).outputs
    assert footprint.footprint_status == 'closed_on_supplied_grid'
    np.testing.assert_array_equal(footprint.volume_fraction_by_crosswind_then_downwind,
        direct_fields['horizontal_downwind'][0].at_y(footprint.crosswind_distance_m))
    censored = dispersion.native_jet_footprint(dispersion.NativeJetFootprintInput(**(baseline|dict(release_height_m=1.)))).outputs
    assert 'upwind' in censored.boundary_sides and censored.threshold_area_m2 is None
    clamped = dispersion.native_jet_centreline(factory(source_temperature_k=250.,jet_liquid_mass_fraction=.2,
        temperature_basis='allow_native_clamp')).outputs
    assert clamped.source_temperature_clamped and clamped.used_source_temperature_k == 231.
    buoyant = dispersion.native_jet_centreline(factory(
        orientation='vertical_up', source_temperature_k=1000., temperature_basis='allow_native_clamp')).outputs
    assert buoyant.orientation == 'vertical_up'
    assert len(buoyant.downwind_distance_m) > 1
    buoyant_source = VerticalJet(substance=substance,rate=1.,area=.01,duration=60.,liquid_fraction=0.,T_source=1000.,height=3.)
    rho_s = buoyant_source.rho_source(atmosphere)
    ws = buoyant_source.w_source(atmosphere)
    ua = atmosphere.wind_speed(3.0)
    fb = (4.0/np.pi)*9.80665*(atmosphere.rho-rho_s)*ws*buoyant_source.half_width_geometric**2/atmosphere.rho
    h_rise = 0.0
    for _ in range(30):
        h_rise = 1.2*(fb/(ua*atmosphere.u_star**2))**(3.0/5.0)*(3.0+h_rise)**(2.0/5.0)
    neutral_temperature = (substance.mw/atmosphere.mw_moist)*atmosphere.T
    neutral_cp = (atmosphere.mw_moist/substance.mw)*atmosphere.cp_moist
    neutral = Substance(name='propane-neutralized',mw=substance.mw,cp_vapour=neutral_cp,cp_liquid=neutral_cp,
        dh_vap=substance.dh_vap,T_boil=substance.T_boil,rho_liquid=substance.rho_liquid)
    effective_source = HorizontalJet(substance=neutral,rate=1.,area=.01,duration=60.,liquid_fraction=0.,
        T_source=neutral_temperature,height=3.0+h_rise)
    buoyant_trajectory,_ = run_dispersion(effective_source,atmosphere,LegacyThermo(neutral),water_backend(),x_max=1000.,n_puff_steps=40)
    buoyant_direct = concentration_field(buoyant_trajectory,atmosphere,z=1.,t_avg=10.,t_release=60.,meander_closure='ermak')
    # The worker and the independent fixture use the same equations but may
    # differ in harmless IEEE-754 operation ordering at the last bit.
    np.testing.assert_allclose(buoyant.downwind_distance_m, buoyant_direct.x, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(buoyant.centreline_volume_fraction, buoyant_direct.peak, rtol=1e-12, atol=1e-12)
    hydrogen = dispersion.native_jet_centreline(factory(engine='slabx-lh2')).outputs
    assert hydrogen.engine_versions == {'slabx':'1.0.8','slabx-lh2':'0.2.0'}
    assert hydrogen.premise_status == 'within_premise'
    geometry = {k:v for k,v in factory(source_temperature_k=231.).model_dump().items()
        if k not in {'mass_source_rate_kg_s','release_duration_s','jet_liquid_mass_fraction'}}
    partition = dict(adjusted_mass_rate_kg_s=2.,released_mass_kg=120.,rainout_mass_fraction=.25,
        equation_basis='post_flash_mass_balance',post_flash_vapor_mass_fraction=.5,
        rainout_basis_source='Qualified fixture',flash_property_source='Qualified fixture')
    integrated = dispersion.partitioned_jet_centreline(dispersion.PartitionedJetCentrelineInput(partition=partition,jet=geometry)).outputs
    explicit = dispersion.native_jet_centreline(dispersion.NativeJetCentrelineInput(**geometry,mass_source_rate_kg_s=1.5,
        release_duration_s=60.,jet_liquid_mass_fraction=1-(.5/.75))).outputs
    assert integrated.centreline_volume_fraction == explicit.centreline_volume_fraction
    assert integrated.jet_total_rate_kg_s == 1.5 and integrated.release_duration_s == 60.
    assert integrated.pool_liquid_rate_kg_s == .5
    plane = dispersion.partitioned_jet_footprint(dispersion.PartitionedJetFootprintInput(partition=partition,
        jet=geometry|dict(crosswind_half_span_m=30.,crosswind_points_per_side=129))).outputs
    assert plane.jet_total_rate_kg_s == integrated.jet_total_rate_kg_s
    assert plane.used_source_temperature_k == 231.
    report = dict(checks=['horizontal_native_exact_arrays','vertical_native_exact_arrays','native_exit_velocity',
        'jet_at_y_exact_field','source_handoff_boundary_censoring','explicit_temperature_clamp',
        'buoyant_vertical_native_exact_arrays','lh2_horizontal_native_run',
        'partition_to_native_exact_chain','partitioned_planar_run'],
        horizontal_distance_m=direct_fields['horizontal_downwind'][1].threshold_distance_m,
        jet_sampled_area_m2=footprint.threshold_area_m2,partitioned_area_status=plane.footprint_status,
        partitioned_area_m2=plane.threshold_area_m2,engine_versions=hydrogen.engine_versions,
        engine_source_fingerprints=hydrogen.engine_source_fingerprints)
    Path('tmp/native-jet-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
