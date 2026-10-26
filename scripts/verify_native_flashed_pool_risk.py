"""Actual selected source/event contribution through EOS and native field."""
import math
import runpy
from api581 import DomainError
from api581.api import risk


example=runpy.run_path('examples/flashed_pool_risk_contribution.py')
factory=example['request']
result=example['main']()
assert result.generic_hole_frequency_per_year==8e-6 and result.management_factor==1.
assert result.annual_release_frequency_per_year==1.6e-5
assert result.conditional_joint_probability==.05
assert math.isclose(result.annual_selected_event_frequency_per_year,8e-7)
assert math.isclose(result.area_risk_contribution_m2_per_year,result.personnel_area_m2*8e-7)
assert math.isclose(result.equipment_area_risk_contribution_m2_per_year,result.equipment_area_m2*8e-7)
assert result.integration_scope=='selected_hole_weather_steady_pool_flash_fire_risk_contribution'
zero=risk.flashed_pool_flash_fire_contribution(factory(event_probability_given_release_weather=0.)).outputs
assert zero.area_risk_contribution_m2_per_year==0.
assert zero.personnel_area_m2==result.personnel_area_m2>0.
assert zero.annual_release_frequency_per_year==result.annual_release_frequency_per_year
clipped=factory().model_copy(update={'fire':factory().fire.model_copy(update={'crosswind_half_span_m':.01})})
try:
    risk.flashed_pool_flash_fire_contribution(clipped)
except DomainError as error:
    assert error.code=='dispersion_footprint_unusable'
else:
    raise AssertionError('Censored fire footprint issued a risk contribution')
print('VERIFIED: known GFF/Fms/DF, weather/event weighting once, zero branch keeps raw area, censoring propagates')
