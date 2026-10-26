import pytest
from api581 import DomainError
from api581.api import damage


def service(**changes):
    return damage.HicH2sQualifiedSusceptibilityInput(**(dict(environment=dict(water_ph=8.5,h2s_in_water_ppm=2000.,cyanides_present=True),
        steel_sulfur_weight_percent=.01,product_form='plate_or_welded',pwht=True,confirmed_cracking=False,
        service_basis='Qualified carbon-steel sulfur/product/PWHT fixture')|changes))


def request(**changes):
    return damage.HicH2sQualifiedAssessmentInput(**(dict(screening=dict(material='carbon_steel',water_present=True,h2s_present=True,
        exposure_basis='Qualified exposure'),service=service(),known_blisters_or_cracks=False,ffs_disposition='not_required',
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),monitoring='none',
        inspection_monitoring_basis='Qualified HIC/SOHIC inspection age/coverage and organized monitoring')|changes))


def test_sulfur_boundary_and_cyanide_step():
    low=damage.hic_h2s_qualified_susceptibility(service()).outputs
    high=damage.hic_h2s_qualified_susceptibility(service(steel_sulfur_weight_percent=.010001)).outputs
    assert low.environmental_severity=='moderate' and low.unadjusted_susceptibility=='low' and low.susceptibility=='medium'
    assert high.unadjusted_susceptibility=='medium' and high.susceptibility=='high'


def test_confirmed_cracking_environment_and_final_high_override():
    r=damage.hic_h2s_qualified_susceptibility(service(confirmed_cracking=True,product_form='seamless_or_extruded_pipe')).outputs
    assert r.environmental_severity=='moderate' and r.effective_environmental_severity=='high'
    assert r.unadjusted_susceptibility=='low' and r.susceptibility=='high'


@pytest.mark.parametrize('monitor,factor',[('none',1.),('process_variables',2.),('hydrogen_probes',2.),('both',4.)])
def test_monitoring_applied_once(monitor,factor):
    result=damage.hic_h2s_qualified_assessment(request(monitoring=monitor)).outputs
    assert result.monitoring_factor==factor and result.base_damage_factor==1.
    assert result.damage_factor==pytest.approx(2**1.1/factor)


def test_known_damage_requires_ffs_and_accepts_external_disposition():
    with pytest.raises(DomainError) as caught:
        damage.hic_h2s_qualified_assessment(request(known_blisters_or_cracks=True))
    assert caught.value.code=='ffs_required'
    r=damage.hic_h2s_qualified_assessment(request(known_blisters_or_cracks=True,
        ffs_disposition='qualified_ffs_basis',ffs_basis='External FFS disposition and inspection recommendations')).outputs
    assert r.ffs_disposition=='qualified_ffs_basis'


def test_low_alloy_screen_does_not_authorize_carbon_steel_table():
    screening=request().screening.model_dump()|dict(material='low_alloy_steel')
    with pytest.raises(DomainError) as caught:
        damage.hic_h2s_qualified_assessment(request(screening=screening))
    assert caught.value.code=='unsupported_hic_material'


def test_source_gap_stays_unresolved():
    values=service().model_dump()
    values['environment']['water_ph']=8.35
    with pytest.raises(DomainError) as caught:
        damage.hic_h2s_qualified_susceptibility(damage.HicH2sQualifiedSusceptibilityInput(**values))
    assert caught.value.code=='ambiguous_source'


@pytest.mark.parametrize('factor',[.5,1.,3.,10.])
def test_experience_factor_replaces_not_multiplies_table(factor):
    r=damage.hic_h2s_qualified_assessment(request(monitoring='both',experience_factor=factor,
        experience_basis='Qualified monitoring experience replacement')).outputs
    assert r.table_monitoring_factor==4. and r.monitoring_factor==factor
    assert r.monitoring_factor_source=='qualified_experience_replacement'
    assert r.damage_factor==pytest.approx(2**1.1/factor)


@pytest.mark.parametrize('values',[dict(monitoring='both',experience_factor=3.),
    dict(monitoring='both',experience_basis='unused'),
    dict(monitoring='both',experience_factor=3.,experience_basis=' '),
    dict(monitoring='none',experience_factor=3.,experience_basis='unsupported')])
def test_unqualified_monitoring_replacement_rejected(values):
    with pytest.raises(DomainError):
        damage.hic_h2s_monitoring_selection(damage.HicH2sMonitoringSelectionInput(**values))
