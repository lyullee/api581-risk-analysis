"""Common component/period rate and inspection-type selection, not mechanism screening."""
from pathlib import Path
import runpy
from api581 import Context
from api581.api import damage


def selection():
    return damage.ThinningRateSelectionInput(mechanisms=[
        dict(mechanism_id='uniform_mechanism',thinning_type='general',
            measured=dict(corrosion_rate_m_year=.0003,representative_for_current_period=True,
                measurement_basis='Illustrative qualified long-term current-process CML rate'),
            fallback=dict(corrosion_rate_m_year=.0005,method='calculated',rate_basis='Illustrative Annex2.B model rate')),
        dict(mechanism_id='localized_mechanism',thinning_type='local',
            fallback=dict(corrosion_rate_m_year=.0002,method='estimated',rate_basis='Qualified specialist rate fixture'))],
        applicability_and_period_basis='Same component, assessed surface and current-process plan period; all applicable mechanisms qualified')


def request():
    factory=runpy.run_path(str(Path(__file__).with_name('groundwater_to_thinning.py')))['request']
    values=factory().model_dump(exclude={'corrosion','assessment_distribution'})
    return damage.ThinningSelectedMechanismsInput(**values,selection=selection())


def main():
    output=damage.thinning_selected_mechanisms(request(),context=Context(
        asset_id='multi-mechanism-thinning-demo',source_revision='qualified-common-period-v1')).outputs
    assert output.corrosion_rate_m_year==.0003
    assert output.assessment_distribution=='local'
    assert output.governing_rate_mechanism_ids==['uniform_mechanism']
    assert output.governing_type_mechanism_ids==['localized_mechanism']
    assert abs(output.wall_loss_fraction-.15)<1e-12
    print('Selected rates:',output.rate_by_mechanism_m_year)
    print('Rate/type governors:',output.governing_rate_mechanism_ids,output.governing_type_mechanism_ids)
    print('Rate / loss / DF:',output.corrosion_rate_m_year,output.wall_loss_fraction,output.thinning_damage_factor)
    return output


if __name__=='__main__':
    main()
