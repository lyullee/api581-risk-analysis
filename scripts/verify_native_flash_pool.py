"""Requires [flash,slabx-lh2]: actual EOS and isolated native engines."""
import math
import runpy
from api581 import DomainError
from api581.api import dispersion


example=runpy.run_path('examples/flashed_boiling_pool.py')
request=example['request']
output=example['main']()
assert output.support_status=='supported'
assert output.engine_versions['slabx']=='1.0.8'
assert math.isclose(output.steady_window_start_s+output.steady_window_duration_s,60.)
assert math.isclose(output.steady_evaporated_mass_kg+output.startup_unmodeled_pool_mass_kg,output.pool_liquid_mass_kg)
assert math.isclose(output.pool_liquid_mass_kg+output.jet_total_mass_kg,120.)
assert math.isclose(output.used_source_area_m2,output.pool_area_m2)
assert len(output.downwind_distance_m)==len(output.centreline_volume_fraction)>5
assert output.threshold_status=='interpolated' and output.threshold_distance_m>0
for changes,code in [(dict(maximum_pool_area_m2=1e-8),'pool_source_unsupported'),
        (dict(released_mass_kg=1e-8),'pool_source_unsupported'),
        (dict(averaging_time_s=60.),'unsupported_averaging_window'),
        (dict(storage_pressure_pa_abs=3e6,storage_temperature_k=350.,method='isenthalpic'),'no_pool_feed')]:
    try:
        dispersion.flashed_boiling_pool_centreline(request(**changes))
    except DomainError as error:
        assert error.code==code,(changes,error.code)
    else:
        raise AssertionError('Unsupported source accepted: '+str(changes))
print('VERIFIED: EOS/partition/steady-pool/native chain, window mass accounting, source-support gates')
hydrogen=dispersion.flashed_boiling_pool_centreline(request(fluid='Hydrogen',storage_temperature_k=25.,
    engine='slabx-lh2',lh2_plume_width_coupling=True,adjusted_mass_rate_kg_s=.1,released_mass_kg=6.,
    threshold_volume_fraction=.04,threshold_source='Illustrative4volpct hydrogen criterion, not a validated endpoint',
    qualification_basis='Qualified normal-hydrogen EOS demonstration, not cryogenic model validation',
    native_property_basis='Demonstration of normal-hydrogen saturated constants; no experimental validation')).outputs
assert hydrogen.engine_versions['slabx-lh2']=='0.2.0'
assert hydrogen.premise_status=='within_premise'
assert hydrogen.threshold_status=='interpolated' and hydrogen.threshold_distance_m>0
assert math.isclose(hydrogen.steady_evaporated_mass_kg+hydrogen.startup_unmodeled_pool_mass_kg+hydrogen.jet_total_mass_kg,6.)
print('VERIFIED: normal-hydrogen EOS to isolated LH2 engine, premise reporting and mass accounting; not physical validation')
