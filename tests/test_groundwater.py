import runpy
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def chemistry(**changes):
    return damage.GroundwaterTksInput(**(dict(chloride_mg_l=1.,sulfate_mg_l=2.,dissolved_co2_mg_l=3.,
        bicarbonate_mg_l=4.,carbonate_mg_l=5.,sulfide_mg_l=6.,ammonia_mg_l=7.,
        concentration_basis='Qualified nonoverlapping species mg/L fixture')|changes))


def classify(rate,basis='printed_si',**changes):
    return damage.groundwater_rate_classification(damage.GroundwaterRateClassificationInput(
        corrosion_rate_m_year=rate,unit_basis=basis,**changes)).outputs


def test_all_seven_species_sum_and_missing_is_not_zero():
    assert damage.groundwater_tks(chemistry()).outputs.total_key_species_mg_l==28.
    values=chemistry().model_dump()
    del values['ammonia_mg_l']
    with pytest.raises(ValidationError):
        damage.GroundwaterTksInput(**values)


@pytest.mark.parametrize('value',[-1.,float('inf'),float('nan')])
def test_invalid_concentrations(value):
    with pytest.raises(ValidationError):
        chemistry(sulfide_mg_l=value)


def test_concentration_basis_required_and_sum_overflow_explicit():
    with pytest.raises(DomainError):
        damage.groundwater_tks(chemistry(concentration_basis=' '))
    values={k:1e308 for k in chemistry().model_dump() if k!='concentration_basis'}
    with pytest.raises(DomainError) as caught:
        damage.groundwater_tks(chemistry(**values))
    assert caught.value.code=='numerical_failure'


@pytest.mark.parametrize('basis,first,middle,last',[('printed_si',.00003,.00025,.00127),
    ('printed_us_converted',.0000254,.000254,.00127)])
def test_source_limits_and_shared_boundary(basis,first,middle,last):
    assert classify(0.,basis).corrosivity_category=='low'
    assert classify(first*.99,basis).corrosivity_category=='low'
    assert classify(first,basis).corrosivity_category=='medium'
    with pytest.raises(DomainError) as caught:
        classify(middle,basis)
    assert caught.value.code=='ambiguous_groundwater_boundary'
    for policy,category in [('lower_severity','medium'),('higher_severity','high')]:
        output=classify(middle,basis,shared_boundary_policy=policy)
        assert output.corrosivity_category==category and output.shared_boundary_encountered
    assert classify(last,basis).corrosivity_category=='high'
    result=classify(last*1.01,basis)
    assert result.corrosivity_category=='very_high' and result.category_upper_bound_m_year is None
    assert result.lower_bound_relation=='exclusive'


def test_printed_unit_rounding_is_not_silently_normalized():
    assert classify(.000028,'printed_si').corrosivity_category=='low'
    assert classify(.000028,'printed_us_converted').corrosivity_category=='medium'
    assert classify(.000252,'printed_si').corrosivity_category=='high'
    assert classify(.000252,'printed_us_converted').corrosivity_category=='medium'


def test_unused_boundary_policy_rejected():
    with pytest.raises(DomainError):
        classify(.0001,shared_boundary_policy='higher_severity')


def test_tks_cannot_change_independently_qualified_rate():
    factory=runpy.run_path('examples/groundwater_to_thinning.py')['request']
    first=factory().corrosion
    second=first.model_copy(update={'chemistry':first.chemistry.model_copy(update={'chloride_mg_l':1e6})})
    outputs=[damage.groundwater_assessment(damage.GroundwaterAssessmentInput(**x.model_dump())).outputs for x in [first,second]]
    assert outputs[0].total_key_species_mg_l!=outputs[1].total_key_species_mg_l
    assert outputs[0].corrosion_rate_m_year==outputs[1].corrosion_rate_m_year
    assert outputs[0].corrosivity_category==outputs[1].corrosivity_category
    assert not outputs[0].tks_to_rate_model_available


@pytest.mark.parametrize('field',['steel_applicability_basis','specialist_rate_basis'])
def test_specialist_qualification_required(field):
    factory=runpy.run_path('examples/groundwater_to_thinning.py')['request']
    values=factory().corrosion.model_dump()|{field:' '}
    with pytest.raises(DomainError):
        damage.groundwater_assessment(damage.GroundwaterAssessmentInput(**values))


def test_end_to_end_thinning_and_no_borrowed_monitoring():
    example=runpy.run_path('examples/groundwater_to_thinning.py')
    output=example['main']()
    assert output.online_monitoring_factor==1. and output.thinning_damage_factor>0.
    values=example['request']().model_dump()
    values['conditions']['monitoring']['row']={'mechanism':'hydrochloric_acid'}
    with pytest.raises(DomainError,match='other-mechanism'):
        damage.groundwater_thinning_assessment(damage.GroundwaterThinningAssessmentInput(**values))
