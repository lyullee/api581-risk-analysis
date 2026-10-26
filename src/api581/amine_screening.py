"""Amine SCC screening; susceptibility remains separately qualified."""
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, calculation, ensure
from .scc_mechanisms import Assessment, InspectionCounts, assess


class AmineCrackingScreen(Model):
    material: Literal['carbon_steel','low_alloy_steel','other_material']
    acid_gas_treating_amine_present: bool
    screening_basis: str = Field(min_length=1)


@calculation('damage/amine-cracking-screening','Any-concentration acid-gas-treating amine SCC material screen',AmineCrackingScreen,
    ['Part2 §7.3; PDF p179'],limitations=[
        'Carbon/low-alloy steel with acid-gas-treating amines in any concentration requires susceptibility evaluation. No concentration, normal-temperature, amine-type, rich-service or PWHT exclusion is inferred. Lean/rich/fresh composition, actual metal temperature, heat tracing, steam-out and other cracking mechanisms require separate evaluation. Screen-out is outside this procedure, not overall immunity or DF0.'])
def amine_cracking_screening(x):
    ensure(bool(x.screening_basis.strip()),'Qualified material and acid-gas-treating amine exposure basis required')
    material=x.material!='other_material'
    return {'evaluate_amine_cracking':material and x.acid_gas_treating_amine_present,
        'screening_reason':'evaluate' if material and x.acid_gas_treating_amine_present else
            'outside_material_scope' if not material else 'treating_amine_absent'}


class ScreenedAmineCracking(Model):
    screening: AmineCrackingScreen
    cracking: Assessment
    susceptibility_and_inspection_basis: str = Field(min_length=1)


@calculation('damage/amine-cracking-screened-assessment','Screened amine exposure through qualified SCC susceptibility and DF',ScreenedAmineCracking,
    ['Part2 §§7.3,7.5-7.6; Table7.2,Table6.3; eq(2.26); PDF pp179-181'],
    origin='amine_material_exposure_screen_to_supplied_susceptibility_df',limitations=[
        'Supplied susceptibility must be independently qualified using Figure7.1 or expert assessment; this API does not implement the figure or predict from amine chemistry. Screening must pass; no synthetic zero DF on screen-out. Confirmed cracking forces High; unrepaired cracks require FFS. Inspection grade/count and time since qualifying A/B/C clear/repaired inspection follow section7.6.3 and remain externally qualified. Existing six-equivalent-inspection support is retained; no all-mechanism assessment.'])
def amine_cracking_screened_assessment(x):
    ensure(not x.cracking.unrepaired_cracks,'Unrepaired amine cracks require separate FFS evaluation','ffs_required')
    ensure(bool(x.susceptibility_and_inspection_basis.strip()),'Amine susceptibility and mechanism-specific inspection basis required')
    screen=amine_cracking_screening(x.screening)
    ensure(screen['evaluate_amine_cracking'],'Amine material/exposure screen not met','amine_outside_screen')
    return {**screen,**assess('amine',x.cracking)}


class AmineFigure(Model):
    confirmed_cracking: bool
    unrepaired_cracks: bool
    stress_relieved: bool
    solution: Literal['fresh','rich','lean','lean_and_rich']
    amine_group: Literal['mea_or_dipa','dea','other_treating_amine']
    maximum_metal_temperature_k: Positive
    heat_traced: bool
    steamed_out_before_water_flush: bool
    applicability_basis: str = Field(min_length=1)


@calculation('damage/amine-figure-susceptibility','Figure7.1 amine cracking susceptibility',AmineFigure,
    ['Part2 Figure7.1,Table7.1; PDF pp182-183'],limitations=[
        'Literal Fahrenheit flowchart thresholds100/140/180F converted exactly to kelvin.100..180 and140..180 include endpoints after the prior >180 test. Both lean/rich exposure routes lean per Table7.1. Other treating amines follow the printed not-MEA/DIPA/not-DEA branch; mixtures spanning groups require independent qualification, not automatic worst-group selection. Actual maximum metal temperature, heat tracing, steam-out before flushing and effective stress relief require qualification. Confirmed cracks forceHigh before stress relief/composition; unrepaired cracks require FFS. Not an amine corrosion-rate model or automatic chemical speciation/PWHT validation.'])
def amine_figure_susceptibility(x):
    ensure(not x.unrepaired_cracks,'Unrepaired amine cracks require separate FFS evaluation','ffs_required')
    ensure(bool(x.applicability_basis.strip()),'Qualified amine composition, actual metal temperature and fabrication basis required')
    if x.confirmed_cracking:
        level,branch='high','confirmed_cracking'
    elif x.stress_relieved:
        level,branch='none','stress_relieved'
    elif x.solution in ('fresh','rich'):
        level,branch='none','not_exposed_to_lean_amine'
    else:
        # Compare in kelvin to avoid back-conversion roundoff at printed endpoints.
        t=x.maximum_metal_temperature_k
        f100,f140,f180=((f-32)*5/9+273.15 for f in (100.,140.,180.))
        heated=x.heat_traced or x.steamed_out_before_water_flush
        if x.amine_group=='mea_or_dipa':
            level='high' if t>f180 else 'medium' if t>=f100 or heated else 'low'
        elif x.amine_group=='dea':
            level='medium' if t>f180 else 'low' if t>=f140 or heated else 'none'
        else:
            level='low' if t>f180 or heated else 'none'
        branch=x.amine_group+'_lean'
    return {'susceptibility':level,'decision_branch':branch,
        'lean_exposure_selected':x.solution in ('lean','lean_and_rich')}


class FigureAmineAssessment(Model):
    screening: AmineCrackingScreen
    service: AmineFigure
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    inspection_basis: str = Field(min_length=1)


@calculation('damage/amine-figure-assessment','Figure7.1 susceptibility through amine SCC DF',FigureAmineAssessment,
    ['Part2 §7.6.3,Figure7.1,Tables7.2/6.3,eq(2.26); PDF pp180,182-183'],
    origin='amine_flowchart_to_existing_scc_df',limitations=[
        'Material/exposure screen, Figure7.1 service declarations and mechanism-specific qualifying inspection age/count require qualification. Reuses existing SVI, equivalent inspection and age escalation, with maximum supported equivalent count6. Rich/fresh none applies only to this amine SCC mechanism, not SSC/HIC/SOHIC or other damage. No whole-component risk, FFS or automatic inspection grading.'])
def amine_figure_assessment(x):
    selected=amine_figure_susceptibility(x.service)
    ensure(bool(x.inspection_basis.strip()),'Amine-specific qualifying inspection period and effectiveness basis required')
    screen=amine_cracking_screening(x.screening)
    ensure(screen['evaluate_amine_cracking'],'Amine material/exposure screen not met','amine_outside_screen')
    result=assess('amine',Assessment(susceptibility=selected['susceptibility'],confirmed_cracking=x.service.confirmed_cracking,
        unrepaired_cracks=x.service.unrepaired_cracks,years_since_qualifying_inspection=x.years_since_qualifying_inspection,
        inspections=x.inspections))
    return {**screen,**selected,**result}
