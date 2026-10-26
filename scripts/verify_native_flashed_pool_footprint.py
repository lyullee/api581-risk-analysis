"""Actual EOS + native planar field + selected flash-fire consequence verification."""
import math
import runpy
from api581 import DomainError
from api581.api import dispersion


example=runpy.run_path('examples/flashed_pool_flash_fire.py')
request=example['request']
fire=example['main']()
assert fire.footprint_status=='closed_on_supplied_grid' and fire.threshold_area_m2>0.
assert fire.personnel_area_m2==fire.threshold_area_m2
assert math.isclose(fire.equipment_area_m2,.25*fire.threshold_area_m2)
assert math.isclose(fire.steady_evaporated_mass_kg+fire.startup_unmodeled_pool_mass_kg+fire.jet_total_mass_kg,120.)
values=request().model_dump(exclude={'criterion_role'})
footprint=dispersion.flashed_boiling_pool_footprint(dispersion.FlashedBoilingPoolFootprintInput(**values)).outputs
assert footprint.threshold_area_m2==fire.threshold_area_m2
assert footprint.spatial_output_scope=='planar_sampled_threshold_field'
fine=dispersion.flashed_boiling_pool_footprint(dispersion.FlashedBoilingPoolFootprintInput(**(values|dict(crosswind_points_per_side=257)))).outputs
assert fine.footprint_status=='closed_on_supplied_grid' and fine.threshold_area_m2>0.
print('Crosswind grid refinement areas:',footprint.threshold_area_m2,fine.threshold_area_m2)
clipped_values=values|dict(crosswind_half_span_m=.01)
clipped=dispersion.flashed_boiling_pool_footprint(dispersion.FlashedBoilingPoolFootprintInput(**clipped_values)).outputs
assert clipped.footprint_status=='boundary_censored' and clipped.threshold_area_m2 is None
assert clipped.sampled_exceedance_area_m2>0. and clipped.boundary_sides
try:
    dispersion.flashed_boiling_pool_flash_fire(request(crosswind_half_span_m=.01))
except DomainError as error:
    assert error.code=='dispersion_footprint_unusable'
else:
    raise AssertionError('Censored footprint accepted as a fire consequence')
print('VERIFIED: EOS-to-footprint/fire, same area mapping, refined grid, censored diagnostics and consequence rejection')
hydrogen=dispersion.flashed_boiling_pool_flash_fire(request(fluid='Hydrogen',storage_temperature_k=25.,
    engine='slabx-lh2',lh2_plume_width_coupling=True,adjusted_mass_rate_kg_s=.1,released_mass_kg=6.,
    threshold_volume_fraction=.04,qualification_basis='Normal-hydrogen EOS demonstration, not model validation',
    native_property_basis='Normal-hydrogen saturation constant-property demonstration',
    threshold_source='Owner-qualified illustrative hydrogen LFL fixture; no site/model validation')).outputs
assert hydrogen.engine_versions['slabx-lh2']=='0.2.0' and hydrogen.premise_status=='within_premise'
assert hydrogen.footprint_status=='closed_on_supplied_grid' and hydrogen.threshold_area_m2>0.
assert hydrogen.personnel_area_m2==hydrogen.threshold_area_m2
assert math.isclose(hydrogen.equipment_area_m2,.25*hydrogen.threshold_area_m2)
print('VERIFIED: normal-hydrogen EOS/LH2 planar field/flash-fire mapping; software integration only')
