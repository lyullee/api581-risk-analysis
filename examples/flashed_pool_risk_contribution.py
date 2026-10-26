"""One selected hole/weather/steady-pool flash-fire contribution, not asset total."""
from pathlib import Path
import runpy
from api581 import Context
from api581.api import risk


def request(**changes):
    fire=runpy.run_path(str(Path(__file__).with_name('flashed_pool_flash_fire.py')))['request']()
    return risk.FlashedPoolFlashFireContributionInput(**(dict(fire=fire,
        component_type='DRUM',hole='small',management_score=500.,total_damage_factor=2.,
        damage_factor_source='Illustrative independently qualified governing DF, not assessed by this example',
        hole_release_basis='Owner-qualified small-hole adjusted2kg/s and120kg fixture; not a hydraulic derivation',
        weather_probability_given_release=.25,event_probability_given_release_weather=.2,
        probability_source='Illustrative selected weather and conditional steady-pool flash-fire terminal event')|changes))


def main():
    output=risk.flashed_pool_flash_fire_contribution(request(),context=Context(
        asset_id='propane-selected-pool-event',source_revision='qualified-frequency-source-event-fixture-v1')).outputs
    print('Release/event frequency per year:',output.annual_release_frequency_per_year,output.annual_selected_event_frequency_per_year)
    print('Raw/weighted personnel area:',output.personnel_area_m2,output.event_weighted_personnel_area_m2)
    print('Area-risk contribution m2/year:',output.area_risk_contribution_m2_per_year)
    print('Scope:',output.contribution_scope)
    return output


if __name__=='__main__':
    main()
