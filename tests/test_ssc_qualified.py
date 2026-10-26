import math
import runpy
import pytest
from api581 import DomainError
from api581.api import damage


def service(**changes):
    return damage.SscQualifiedSusceptibilityInput(**(dict(environment=dict(water_ph=8.5,h2s_in_water_ppm=2000.,cyanides_present=True),
        measured_brinnell_hardness=220.,pwht=True,service_basis='Qualified water, measured weldment Brinnell and PWHT fixture')|changes))


@pytest.mark.parametrize('hardness,pwht,base,adjusted',[(190.,True,'none','low'),(220.,True,'none','low'),
    (240.,True,'low','medium'),(190.,False,'low','medium'),(220.,False,'medium','high'),(240.,False,'high','high')])
def test_cyanide_upgrades_susceptibility_not_environment(hardness,pwht,base,adjusted):
    r=damage.ssc_qualified_susceptibility(service(measured_brinnell_hardness=hardness,pwht=pwht)).outputs
    assert r.environmental_severity=='moderate'
    assert r.unadjusted_susceptibility==base and r.susceptibility==adjusted
    assert r.cyanide_upgrade_applied


@pytest.mark.parametrize('ph,ppm,cyanide',[(8.3,2000.,True),(8.5,999.,True),(8.5,2000.,False)])
def test_upgrade_thresholds(ph,ppm,cyanide):
    r=damage.ssc_qualified_susceptibility(service(environment=dict(water_ph=ph,h2s_in_water_ppm=ppm,cyanides_present=cyanide))).outputs
    assert not r.cyanide_upgrade_applied and r.susceptibility==r.unadjusted_susceptibility


@pytest.mark.parametrize('ph,ppm',[(7.55,2000.),(8.35,2000.),(8.95,2000.),(9.,2000.),(8.5,1000.)])
def test_source_gaps_and_overlap_stay_explicit(ph,ppm):
    with pytest.raises(DomainError) as caught:
        damage.ssc_qualified_susceptibility(service(environment=dict(water_ph=ph,h2s_in_water_ppm=ppm,cyanides_present=True)))
    assert caught.value.code=='ambiguous_source'


def request(**changes):
    return damage.SscQualifiedAssessmentInput(**(dict(screening=dict(material='carbon_steel',water_present=True,h2s_present=True,
        exposure_basis='Qualified wet-H2S exposure'),service=service(),confirmed_cracking=False,unrepaired_cracks=False,
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0),
        inspection_basis='Qualified SSC inspection period and1A coverage')|changes))


def test_service_to_df_and_cracking_override():
    r=damage.ssc_qualified_assessment(request()).outputs
    assert r.susceptibility=='low' and r.severity_index==1 and r.base_damage_factor==1.
    assert r.damage_factor==pytest.approx(2**1.1)
    high=damage.ssc_qualified_assessment(request(confirmed_cracking=True)).outputs
    assert high.effective_susceptibility=='high' and high.severity_index==100 and high.base_damage_factor==5.


def test_ffs_priority_and_screenout():
    with pytest.raises(DomainError) as caught:
        damage.ssc_qualified_assessment(request(unrepaired_cracks=True,inspection_basis=' '))
    assert caught.value.code=='ffs_required'
    screen=request().screening.model_dump()|dict(water_present=False)
    with pytest.raises(DomainError) as caught:
        damage.ssc_qualified_assessment(request(screening=screen))
    assert caught.value.code=='ssc_outside_screen'


@pytest.mark.parametrize('pwht,expected',[(False,['low','medium','medium','high']),
    (True,['none','none','none','low'])])
def test_exact_hardness_boundaries_through_cyanide_bridge(pwht,expected):
    for hardness,base in zip([math.nextafter(200.,-math.inf),200.,237.,math.nextafter(237.,math.inf)],expected):
        result=damage.ssc_qualified_susceptibility(service(measured_brinnell_hardness=hardness,pwht=pwht)).outputs
        assert result.unadjusted_susceptibility==base
        levels=['none','low','medium','high']
        assert result.susceptibility==levels[min(3,levels.index(base)+1)]


def test_integrated_df_matches_explicit_independent_calls():
    inputs=request(service=service(measured_brinnell_hardness=237.,pwht=False))
    integrated=damage.ssc_qualified_assessment(inputs).outputs
    environment=damage.wet_h2s_environment(damage.WetH2sEnvironmentInput(**inputs.service.environment.model_dump())).outputs
    base=damage.ssc_susceptibility(damage.SscSusceptibilityInput(measured_brinnell_hardness=237.,pwht=False,
        environmental_severity=environment.environmental_severity)).outputs
    assert base.susceptibility=='medium' and environment.susceptibility_upgrade_required
    direct=damage.ssc(damage.SscInput(susceptibility='high',confirmed_cracking=False,unrepaired_cracks=False,
        years_since_qualifying_inspection=2.,inspections=dict(a=1,b=0,c=0,d=0))).outputs
    assert integrated.damage_factor==direct.damage_factor
    assert integrated.equivalent_inspection_grade==direct.equivalent_inspection_grade


def test_public_ssc_example():
    result=runpy.run_path('examples/ssc_qualified_assessment.py')['main']()
    assert result.cyanide_upgrade_applied and result.effective_susceptibility=='high'
