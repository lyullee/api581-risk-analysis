"""PASCC sulfur-exposure/material screen; shutdown mitigation is not screening."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, calculation, ensure
from .scc_mechanisms import PasccSusceptibility, pascc_susceptibility, Assessment, InspectionCounts, assess


class PasccScreen(Model):
    material: Literal['austenitic_stainless_steel','nickel_based_alloy','other_material']
    sulfur_bearing_compounds_exposure: bool
    exposure_basis: str = Field(min_length=1)


@calculation('damage/pascc-screening','PASCC austenitic stainless/nickel alloy sulfur exposure screen',PasccScreen,
    ['Part2 §11.3; PDF p201'],limitations=[
        'Austenitic stainless steel or nickel-based alloy exposed to sulfur-bearing compounds requires PASCC susceptibility evaluation. No automatic exclusion for normal-operation dryness, low-carbon/stabilized grade, low operating temperature, alkaline wash or nitrogen purge; shutdown air/moisture and mitigation remain separate evaluation. Material category does not authorize every Table11.2 cell. Screen-out is outside this procedure, not global immunity or zero DF.'])
def pascc_screening(x):
    ensure(bool(x.exposure_basis.strip()),'Qualified alloy identity and sulfur exposure history basis required')
    material=x.material!='other_material'
    return {'evaluate_pascc':material and x.sulfur_bearing_compounds_exposure,
        'screening_reason':'outside_material_scope' if not material else 'sulfur_exposure_absent' if not x.sulfur_bearing_compounds_exposure else 'evaluate'}


class PasccFigure(Model):
    alloy: PasccSusceptibility
    sulfur_oxygen_water_during_operation: bool
    sulfur_oxygen_water_during_shutdown: bool
    qualified_rp0170_downtime_protection: bool
    protection_basis: str | None = None
    confirmed_cracking: bool
    unrepaired_cracks: bool
    service_alloy_basis: str = Field(min_length=1)


@calculation('damage/pascc-figure-susceptibility','PASCC Figure11.1 exposure and qualified downtime protection',PasccFigure,
    ['Part2 Figure11.1,Table11.2; PDF pp205-206'],limitations=[
        'Caller qualifies simultaneous sulfur/oxygen/water exposure in operation/shutdown and Table11.2 alloy/thermal history. No exposure in either phase returns none without table lookup. RP0170 downtime protection, when qualified, reduces table susceptibility one level high->medium->low->none exactly as Figure11.1. Confirmed cracks forcehigh before exposure/protection; unrepaired cracks requireFFS. No RP0170 compliance verification or automatic shutdown exposure inference. Existing SI427C table threshold/unsupported cells retained.'])
def pascc_figure_susceptibility(x):
    ensure(not x.unrepaired_cracks,'Unrepaired PASCC requires separate FFS evaluation','ffs_required')
    ensure(bool(x.service_alloy_basis.strip()),'Qualified alloy/thermal history and operation/shutdown exposure basis required')
    ensure((x.protection_basis is not None)==x.qualified_rp0170_downtime_protection,'Downtime protection and basis must agree')
    if x.protection_basis is not None:
        ensure(bool(x.protection_basis.strip()),'Downtime protection basis must be nonblank')
    if x.confirmed_cracking:
        base,selected,used='high','high',False
    elif not (x.sulfur_oxygen_water_during_operation or x.sulfur_oxygen_water_during_shutdown):
        base,selected,used='none','none',False
    else:
        base=pascc_susceptibility(x.alloy)['susceptibility']
        levels=('none','low','medium','high')
        used=x.qualified_rp0170_downtime_protection
        selected=levels[max(0,levels.index(base)-int(used))]
    return {'table_or_override_susceptibility':base,'susceptibility':selected,'downtime_reduction_applied':used}


class PasccQualifiedAssessment(Model):
    screening: PasccScreen
    service: PasccFigure
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    inspection_basis: str = Field(min_length=1)


@calculation('damage/pascc-qualified-assessment','PASCC screen/Figure11.1 through inspection and age DF',PasccQualifiedAssessment,
    ['Part2 §§11.3,11.6.3,Figure11.1,Tables11.2-11.3; eq(2.30); PDF pp201-206'],
    origin='qualified_pascc_exposure_protection_to_df',limitations=[
        'Requires positive material/sulfur screen and independent alloy-group identity/thermal-history qualification. Nickel-family screening cannot use H/L-grade300SS or321SS table groups. Mixed-named table groups require owner matching, not automatic grade inference. Figure11.1 exposures/protection and mechanism-specific inspection period remain explicit. Confirmed cracks override mitigation; unrepairedFFS. Existing equivalent-count/age rules retained. No whole-asset risk or FFS.'])
def pascc_qualified_assessment(x):
    selected=pascc_figure_susceptibility(x.service)
    ensure(bool(x.inspection_basis.strip()),'PASCC-specific inspection period and coverage basis required')
    screen=pascc_screening(x.screening)
    ensure(screen['evaluate_pascc'],'PASCC material/sulfur screen not met','pascc_outside_screen')
    if x.screening.material=='nickel_based_alloy':
        ensure(x.service.alloy.material_group not in ('h_grade_300ss','l_grade_300ss','321ss'),
            'Nickel family contradicts stainless-only table group','pascc_material_mismatch')
    result=assess('pascc',Assessment(susceptibility=selected['susceptibility'],confirmed_cracking=x.service.confirmed_cracking,
        unrepaired_cracks=False,years_since_qualifying_inspection=x.years_since_qualifying_inspection,inspections=x.inspections))
    return {**screen,**selected,**result}
