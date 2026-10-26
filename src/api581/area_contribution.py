"""Selected event/weather area-risk contributions, distinct from full assessment."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Fraction, calculation, ensure, REGISTRY
from .pof import Component, generic, Management, management, Frequency, adjusted
from .flash_pool import FlashedBoilingPoolFlashFire, flashed_boiling_pool_flash_fire


class AreaEventContribution(Model):
    annual_release_frequency_per_year: NonNegative
    weather_probability_given_release: Fraction
    event_probability_given_release_weather: Fraction
    equipment_area_m2: NonNegative
    personnel_area_m2: NonNegative
    probability_source: str = Field(min_length=1,max_length=1000)


@calculation('risk/area-event-contribution','Selected conditional event/weather area-risk contribution',AreaEventContribution,
    ['Part1 §4.3.1 eqs(1.6)-(1.8); Part3 §5.8.7'],
    origin='explicit_selected_event_weather_risk_contribution',limitations=[
        'Partial contribution only; does not require or imply complete terminal outcomes/weather/holes. Event probability is conditional on the supplied release AND weather, so multiplying by weather probability is the chain rule, not an independence assertion. Raw event areas must not already be event/weather weighted. Release frequency must not already contain these probabilities. Each probability and annual release frequency is applied once. No financial, individual or societal risk; no zero-consequence assertion for omitted events.'])
def area_event_contribution(x):
    ensure(bool(x.probability_source.strip()),'Conditional event/weather probability source required')
    joint=x.weather_probability_given_release*x.event_probability_given_release_weather
    equipment=joint*x.equipment_area_m2
    personnel=joint*x.personnel_area_m2
    equipment_risk=x.annual_release_frequency_per_year*equipment
    personnel_risk=x.annual_release_frequency_per_year*personnel
    return dict(annual_release_frequency_per_year=x.annual_release_frequency_per_year,
        conditional_joint_probability=joint,annual_selected_event_frequency_per_year=x.annual_release_frequency_per_year*joint,
        event_weighted_equipment_area_m2=equipment,event_weighted_personnel_area_m2=personnel,
        equipment_area_risk_contribution_m2_per_year=equipment_risk,
        personnel_area_risk_contribution_m2_per_year=personnel_risk,
        area_risk_contribution_m2_per_year=max(equipment_risk,personnel_risk),
        contribution_scope='selected_event_weather_case')


class FlashedPoolRiskContribution(Model):
    fire: FlashedBoilingPoolFlashFire
    component_type: str = Field(min_length=1)
    hole: Literal['small','medium','large','rupture']
    management_score: NonNegative = Field(le=1000)
    total_damage_factor: NonNegative
    damage_factor_source: str = Field(min_length=1,max_length=1000)
    hole_release_basis: str = Field(min_length=1,max_length=1000)
    weather_probability_given_release: Fraction
    event_probability_given_release_weather: Fraction
    probability_source: str = Field(min_length=1,max_length=1000)


@calculation('risk/flashed-pool-flash-fire-contribution','Selected hole/weather EOS-to-flash-fire annual area-risk contribution',FlashedPoolRiskContribution,
    ['Part1 §4.3.1; Part2 Table3.1,eqs(2.1),(2.9)-(2.10); Part3 §§5.7.4,5.8.6-5.8.7'],
    origin='selected_hole_eos_native_fire_risk_composition',limitations=[
        *REGISTRY['risk/area-event-contribution'].limitations,
        'Uses only the selected non-tank GFF hole, supplied governing DF and management score. Hole-specific adjusted rate/mass and applicability must be qualified externally; this API does not derive hydraulic hole size, isolation/inventory or damage applicability. Probability is for this selected steady pool flash-fire scenario, not total ignition probability.',
        'EOS/native source scope, constant-property qualification, ground LFL, sampled-grid censoring and LH2 premise restrictions are inherited. No startup/jet/post-release pool or other outcome contribution. Omitted scenarios remain unassessed; this result is not a whole-component or four-hole risk assessment.'])
def flashed_pool_risk_contribution(x):
    ensure(all(s.strip() for s in (x.damage_factor_source,x.hole_release_basis,x.probability_source)),
        'Damage, selected-hole release and probability bases must be nonblank')
    frequencies=generic(Component(component_type=x.component_type))
    gff=frequencies['by_hole_per_year'][x.hole]
    fms=management(Management(score=x.management_score))['management_factor']
    frequency=adjusted(Frequency(generic_frequency_per_year=gff,total_damage_factor=x.total_damage_factor,
        management_factor=fms))['annual_failure_frequency']
    fire=flashed_boiling_pool_flash_fire(x.fire)
    contribution=area_event_contribution(AreaEventContribution(annual_release_frequency_per_year=frequency,
        weather_probability_given_release=x.weather_probability_given_release,event_probability_given_release_weather=x.event_probability_given_release_weather,
        equipment_area_m2=fire['equipment_area_m2'],personnel_area_m2=fire['personnel_area_m2'],probability_source=x.probability_source))
    return {**fire,**contribution,'generic_hole_frequency_per_year':gff,'management_factor':fms,
        'total_damage_factor':x.total_damage_factor,'selected_hole':x.hole,
        'contribution_scope':'selected_hole_weather_steady_pool_flash_fire',
        'integration_scope':'selected_hole_weather_steady_pool_flash_fire_risk_contribution'}
