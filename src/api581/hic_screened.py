"""Qualified carbon-steel HIC/SOHIC wet-H2S composition."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .ssc_screening import SscScreen, hic_h2s_screening
from .scc_mechanisms import (WetH2sEnvironment, wet_h2s_environment, HicH2sMaterial,
    hic_h2s_susceptibility, HicAssessment, InspectionCounts, assess)


class HicQualifiedService(Model):
    environment: WetH2sEnvironment
    steel_sulfur_weight_percent: NonNegative = Field(le=100)
    product_form: Literal['plate_or_welded','seamless_or_extruded_pipe']
    pwht: bool
    confirmed_cracking: bool
    service_basis: str = Field(min_length=1)


@calculation('damage/hic-h2s-qualified-susceptibility','HIC/SOHIC-H2S environment/material/cyanide susceptibility',HicQualifiedService,
    ['Part2 §9.6.4 STEP1-2,Tables9.2-9.3; PDF pp190,193'],limitations=[
        'Carbon-steel Table9.3 applicability qualified externally. Sulfur input is weight percent, not mass fraction. Confirmed cracking forces environmental severity high under STEP1 and final susceptibility high under section9.5; measured environment remains diagnostic. Cyanide note upgrades subsequent susceptibility one category capped high, not environment. Existing pH gaps/1000ppm overlap fail. No sulfur inference from steel grade/year or automatic low-alloy table applicability.'])
def hic_qualified_susceptibility(x):
    ensure(bool(x.service_basis.strip()),'Carbon-steel chemistry/product/PWHT applicability basis required')
    environment=wet_h2s_environment(x.environment)
    effective='high' if x.confirmed_cracking else environment['environmental_severity']
    base=hic_h2s_susceptibility(HicH2sMaterial(steel_sulfur_weight_percent=x.steel_sulfur_weight_percent,
        product_form=x.product_form,pwht=x.pwht,environmental_severity=effective))['susceptibility']
    levels=('none','low','medium','high')
    adjusted=levels[min(3,levels.index(base)+int(environment['susceptibility_upgrade_required']))]
    return {**environment,'effective_environmental_severity':effective,'unadjusted_susceptibility':base,
        'cyanide_adjusted_susceptibility':adjusted,'susceptibility':'high' if x.confirmed_cracking else adjusted}


class HicMonitoringSelection(Model):
    monitoring: Literal['none','process_variables','hydrogen_probes','both']
    experience_factor: Positive | None = None
    experience_basis: str | None = None


@calculation('damage/hic-h2s-monitoring-selection','Table9.5 or qualified experience replacement monitoring factor',HicMonitoringSelection,
    ['Part2 Table9.5 note; PDF p193'],limitations=[
        'Table factors1/2/2/4 or one positive finite experience-based replacement with nonblank basis. Replacement is not multiplied by the table factor. Source gives no numeric range for experience substitutes; no automatic clamp or empirical calibration. Replacement requires an active monitoring method; no credit inferred for absent monitoring. Physical program effectiveness remains owner-qualified.'])
def hic_monitoring_selection(x):
    table={'none':1.,'process_variables':2.,'hydrogen_probes':2.,'both':4.}[x.monitoring]
    custom=x.experience_factor is not None
    ensure((x.experience_basis is not None)==custom,'Experience factor and basis must be supplied together')
    if custom:
        ensure(x.monitoring!='none' and bool(x.experience_basis.strip()),'Experience replacement requires active monitoring and qualified basis')
    return {'table_monitoring_factor':table,'monitoring_factor':x.experience_factor if custom else table,
        'monitoring_factor_source':'qualified_experience_replacement' if custom else 'table9_5'}


class HicQualifiedAssessment(Model):
    screening: SscScreen
    service: HicQualifiedService
    known_blisters_or_cracks: bool
    ffs_disposition: Literal['not_required','repaired','qualified_ffs_basis']
    ffs_basis: str | None = None
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    monitoring: Literal['none','process_variables','hydrogen_probes','both']
    experience_factor: Positive | None = None
    experience_basis: str | None = None
    inspection_monitoring_basis: str = Field(min_length=1)


@calculation('damage/hic-h2s-qualified-assessment','Screened HIC/SOHIC-H2S service through monitoring-adjusted DF',HicQualifiedAssessment,
    ['Part2 §§9.3,9.5-9.6,Tables9.2-9.5,eq(2.28); PDF pp189-193'],
    origin='qualified_hic_h2s_service_material_monitoring_to_df',limitations=[
        'Carbon-steel integration only, despite broader carbon/low-alloy screening. Known blisters/cracks require explicit repaired or externally qualified FFS disposition and basis; this API performs no FFS. Confirmed cracking must also be declared known. Inspection and age follow section9.6.4, not generic thinning periods. Monitoring is applied once using existing factors1/2/2/4; qualification is mandatory. Existing six-equivalent-inspection and source table guards retained. No whole-asset risk or automatic damage detection.'])
def hic_qualified_assessment(x):
    ensure(not x.service.confirmed_cracking or x.known_blisters_or_cracks,'Confirmed cracking requires known damage declaration')
    if x.known_blisters_or_cracks:
        ensure(x.ffs_disposition!='not_required' and x.ffs_basis is not None and bool(x.ffs_basis.strip()),
            'Known blisters/cracks require repaired or externally qualified FFS disposition','ffs_required')
    else:
        ensure(x.ffs_disposition=='not_required' and x.ffs_basis is None,'FFS disposition is unused without known damage')
    ensure(bool(x.inspection_monitoring_basis.strip()),'HIC/SOHIC-specific inspection age and monitoring qualification required')
    screen=hic_h2s_screening(x.screening)
    ensure(screen['evaluate_hic_sohic_h2s'],'HIC/SOHIC wet-H2S screen not met','hic_outside_screen')
    ensure(x.screening.material=='carbon_steel','Table9.3 integration requires qualified carbon steel','unsupported_hic_material')
    service=hic_qualified_susceptibility(x.service)
    monitoring=hic_monitoring_selection(HicMonitoringSelection(monitoring=x.monitoring,
        experience_factor=x.experience_factor,experience_basis=x.experience_basis))
    result=assess('hic-sohic-h2s',HicAssessment(susceptibility=service['susceptibility'],confirmed_cracking=x.service.confirmed_cracking,
        unrepaired_cracks=False,years_since_qualifying_inspection=x.years_since_qualifying_inspection,
        inspections=x.inspections,monitoring='none'))
    result['damage_factor']=result['base_damage_factor']*result['age_factor']/monitoring['monitoring_factor']
    return {**screen,**service,**result,**monitoring,'ffs_disposition':x.ffs_disposition}
