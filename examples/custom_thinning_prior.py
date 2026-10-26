"""Qualified empirical prior -> Bayes inspection update -> same-wall thinning DF."""
from pathlib import Path
import runpy
from api581.api import damage


def main():
    choice=damage.ThinningPriorSelectionInput(custom_prior_probabilities=[.3,.3,.4],
        custom_prior_basis='Illustrative owner-qualified actual experience and thickness-confidence prior; not calibrated here')
    selected=damage.thinning_prior_selection(choice).outputs
    posterior=damage.thinning_posterior(damage.ThinningPosteriorInput(**choice.model_dump(),inspections_a=1)).outputs
    factory=runpy.run_path(str(Path(__file__).with_name('groundwater_to_thinning.py')))['request']
    baseline=damage.groundwater_thinning_assessment(factory()).outputs
    customized=damage.groundwater_thinning_assessment(factory(inspections=dict(**choice.model_dump(),inspections_a=1))).outputs
    assert customized.wall_loss_fraction==baseline.wall_loss_fraction
    assert customized.corrosion_rate_m_year==baseline.corrosion_rate_m_year
    assert customized.thinning_damage_factor>baseline.thinning_damage_factor
    print('Selected prior / source:',selected.prior_probabilities,selected.prior_source)
    print('OneA inspection posterior:',posterior.posterior_probabilities)
    print('Default / custom thinning DF:',baseline.thinning_damage_factor,customized.thinning_damage_factor)
    return selected,posterior,baseline,customized


if __name__=='__main__':
    main()
