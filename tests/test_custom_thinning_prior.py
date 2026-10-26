import math
import runpy
import pytest
from pydantic import ValidationError
from api581.api import damage


@pytest.mark.parametrize('confidence,expected',[('low',[.5,.3,.2]),('medium',[.7,.2,.1]),('high',[.8,.15,.05])])
def test_table_priors_and_legacy_posterior_unchanged(confidence,expected):
    selected=damage.thinning_prior_selection(damage.ThinningPriorSelectionInput(confidence=confidence)).outputs
    assert selected.prior_probabilities==expected
    assert selected.prior_source=='table4_5' and selected.confidence==confidence
    posterior=damage.thinning_posterior(damage.ThinningPosteriorInput(confidence=confidence)).outputs
    assert posterior.posterior_probabilities==pytest.approx(expected)


def test_custom_prior_known_bayes_update():
    result=damage.thinning_posterior(damage.ThinningPosteriorInput(custom_prior_probabilities=[.3,.3,.4],
        custom_prior_basis='Qualified empirical fixture',inspections_a=1)).outputs
    assert result.posterior_probabilities==pytest.approx([270/301,27/301,4/301])


@pytest.mark.parametrize('prior,zero_states',[([0.,0.,1.],[1,2]),([0.,1.,0.],[1,3]),([1.,0.,0.],[2,3]),([.5,0.,.5],[2])])
def test_zero_prior_stays_zero_without_invented_floor(prior,zero_states):
    selected=damage.thinning_prior_selection(damage.ThinningPriorSelectionInput(custom_prior_probabilities=prior,
        custom_prior_basis='Explicit zero-state certainty fixture')).outputs
    assert selected.zero_prior_state_indices==zero_states
    result=damage.thinning_posterior(damage.ThinningPosteriorInput(custom_prior_probabilities=prior,
        custom_prior_basis='Explicit zero-state certainty fixture',inspections_a=100000,inspections_b=100000,
        inspections_c=100000,inspections_d=100000)).outputs.posterior_probabilities
    assert all(result[i-1]==0. for i in zero_states)
    assert math.isclose(math.fsum(result),1.)


@pytest.mark.parametrize('changes',[{},dict(confidence='high',custom_prior_probabilities=[.3,.3,.4],custom_prior_basis='qualified'),
    dict(confidence='low',custom_prior_basis='unused'),dict(custom_prior_probabilities=[.3,.3,.4]),
    dict(custom_prior_probabilities=[.3,.3,.4],custom_prior_basis=' '),
    dict(custom_prior_probabilities=[0.,0.,0.],custom_prior_basis='qualified'),
    dict(custom_prior_probabilities=[.3,.3,.3],custom_prior_basis='qualified'),
    dict(custom_prior_probabilities=[.3,.3,.4,.0],custom_prior_basis='qualified'),
    dict(custom_prior_probabilities=[-.1,.5,.6],custom_prior_basis='qualified'),
    dict(custom_prior_probabilities=[float('nan'),.5,.5],custom_prior_basis='qualified')])
def test_ambiguous_unqualified_or_invalid_prior_rejected(changes):
    with pytest.raises(ValidationError):
        damage.ThinningPosteriorInput(**changes)


def test_only_sum_rounding_is_normalized():
    result=damage.thinning_prior_selection(damage.ThinningPriorSelectionInput(custom_prior_probabilities=[.3,.3,.4000000001],
        custom_prior_basis='Rounded empirical fixture')).outputs
    assert math.isclose(math.fsum(result.prior_probabilities),1.,rel_tol=0.,abs_tol=1e-15)
    assert result.prior_source=='qualified_custom' and result.confidence is None


def test_custom_prior_propagates_through_corrosion_thinning_composition():
    selected,posterior,baseline,custom=runpy.run_path('examples/custom_thinning_prior.py')['main']()
    assert custom.posterior_probabilities==posterior.posterior_probabilities
    assert custom.thinning_damage_factor>baseline.thinning_damage_factor
    assert selected.prior_source=='qualified_custom'
