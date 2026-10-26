"""Caustic SCC material screen and qualified Figure6.2 susceptibility routing."""
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure
from .scc_mechanisms import Assessment, InspectionCounts, assess


class CausticScreen(Model):
    material: Literal['carbon_steel','low_alloy_steel','other_material']
    caustic_present: bool
    screening_basis: str = Field(min_length=1)


@calculation('damage/caustic-screening','Caustic cracking material and any-concentration exposure screen',CausticScreen,
    ['Part2 §6.3; PDF p172'],limitations=[
        'Carbon/low-alloy steel with caustic at any concentration requires evaluation. Presence includes qualified local/upset/residual exposure; no5wtpct or normal-process-temperature cutoff is used for screening. Screen-out means outside this procedure, not material immunity, zero overall DF or exclusion of other mechanisms.'])
def caustic_screening(x):
    ensure(bool(x.screening_basis.strip()),'Material and caustic exposure qualification required')
    material=x.material!='other_material'
    return {'evaluate_caustic_cracking':material and x.caustic_present,
        'screening_reason':'evaluate' if material and x.caustic_present else 'outside_material_scope' if not material else 'caustic_absent'}


class CausticPlotEvidence(Model):
    maximum_metal_temperature_k: Positive
    naoh_mass_fraction: Fraction
    chart_area: Literal['A','B','C']
    chart_unit_basis: Literal['printed_si','printed_us']
    heat_traced: bool
    steamed_out_before_water_flush: bool
    plot_basis: str = Field(min_length=1)


class CausticFigureSusceptibility(Model):
    stress_relieved: bool
    cracking_history: Literal['never_detected','detected_repaired','unrepaired','specialist_reassigned_after_clear_inspection']
    adequate_subsequent_clear_inspection: bool = False
    specialist_reassignment_basis: str | None = None
    fabrication_history_basis: str = Field(min_length=1)
    plot: CausticPlotEvidence | None = None


@calculation('damage/caustic-figure-susceptibility','Qualified caustic graph area through Figure6.2 and crack-history gate',CausticFigureSusceptibility,
    ['Part2 §6.5,Figure6.2; Figures6.1/6.1M; PDF pp172-173,176-178'],limitations=[
        'Figure6.1/6.1M area is independently qualified from actual maximum metal temperature and effective local NaOH concentration. This API routes the area; it does not digitize/interpolate the graph or certify PWHT. Plot concentration0..50wtpct; exactly5wtpct follows the not-less-than5 branch. Heat tracing and steam-out before water flushing follow Figure6.2.',
        'Detected/repaired historical cracking stays High until an adequately effective subsequent clear inspection AND specialist reassignment basis. Stress relief cannot erase that history. Unrepaired cracks require separate FFS and fail explicitly. No automatic stress-relief temperature/hold-time qualification, alloy immunity or local boiling concentration model.'])
def caustic_figure_susceptibility(x):
    # FFS referral must not be obscured by conflicting reassignment metadata.
    ensure(x.cracking_history!='unrepaired','Unrepaired caustic cracks require separate FFS evaluation','ffs_required')
    ensure(bool(x.fabrication_history_basis.strip()),'Qualified fabrication and crack-history basis required')
    reassigned=x.cracking_history=='specialist_reassigned_after_clear_inspection'
    ensure((x.specialist_reassignment_basis is not None)==reassigned,
        'Specialist reassignment requires a matching basis, unused basis must be omitted')
    if reassigned:
        ensure(x.adequate_subsequent_clear_inspection and bool(x.specialist_reassignment_basis.strip()),
            'Specialist reassignment requires adequate subsequent clear inspection and nonblank basis')
    retained=x.cracking_history=='detected_repaired'
    if retained:
        level,branch,used='high','historical_cracking_high',False
    elif x.stress_relieved:
        level,branch,used='none','qualified_stress_relief',False
    else:
        plot=x.plot
        ensure(plot is not None,'Non-stress-relieved uncracked branch requires qualified caustic graph area')
        ensure(bool(plot.plot_basis.strip()),'Actual metal temperature/local concentration graph-area basis required')
        ensure(plot.naoh_mass_fraction<=.5,'Caustic graph concentration exceeds50wtpct support')
        low=plot.naoh_mass_fraction<.05
        if plot.chart_area!='A':
            level='medium' if low else 'high'
            branch='outside_area_a_low_concentration' if low else 'outside_area_a_high_concentration'
        elif plot.heat_traced:
            level='medium' if low else 'high'
            branch='area_a_heat_traced'
        elif plot.steamed_out_before_water_flush:
            level='low' if low else 'medium'
            branch='area_a_steamout_before_flush'
        else:
            level,branch='none','area_a_no_heating_or_steamout'
        used=True
    return {'susceptibility':level,'decision_branch':branch,'plot_evidence_used':used,'historical_high_retained':retained}


class QualifiedCausticAssessment(Model):
    screening: CausticScreen
    susceptibility: CausticFigureSusceptibility
    years_since_qualifying_inspection: NonNegative
    inspections: InspectionCounts
    assessment_basis: str = Field(min_length=1)


@calculation('damage/caustic-screened-assessment','Caustic screen and Figure6.2 through SCC severity/inspection/age DF',QualifiedCausticAssessment,
    ['Part2 §§6.3,6.5-6.6; Tables6.2-6.3; Figure6.2; eq(2.25); PDF pp172-178'],
    origin='qualified_caustic_screen_figure_to_existing_scc_df',limitations=[
        'Material/exposure screen must pass; outside-scope input fails instead of manufacturing DF0. Figure area/PWHT and crack-history/reassignment declarations require qualification. Uses existing caustic SVI, equivalent highest inspection and age escalation unchanged; source ambiguous E/500 cell and counts beyond6 remain unsupported. Inspection coverage and qualifying age are externally established per §6.6.3, not inferred from generic thinning history. No FFS, graph interpolation or all-mechanism risk.'])
def caustic_screened_assessment(x):
    ensure(bool(x.assessment_basis.strip()),'Caustic inspection period/effectiveness and applicability basis required')
    screen=caustic_screening(x.screening)
    ensure(screen['evaluate_caustic_cracking'],'Caustic material/exposure screen not met','caustic_outside_screen')
    susceptibility=caustic_figure_susceptibility(x.susceptibility)
    result=assess('caustic',Assessment(susceptibility=susceptibility['susceptibility'],
        confirmed_cracking=susceptibility['historical_high_retained'],unrepaired_cracks=False,
        years_since_qualifying_inspection=x.years_since_qualifying_inspection,inspections=x.inspections))
    return {**screen,**susceptibility,**result}
