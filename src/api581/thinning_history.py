"""Date-consistent thickness baseline and period-qualified inspection counts."""
from datetime import timezone
from typing import Literal
from pydantic import AwareDatetime, Field
from .core import Model, Positive, calculation, ensure
from .thinning import PriorSelection, Posterior
from .thinning_selection import ThinningRateSelection, SelectedMechanismThinning, selected_mechanism_thinning
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions


class MeasuredBaseline(Model):
    inspection_id: str = Field(min_length=1,max_length=100)
    measured_at: AwareDatetime
    thickness_m: Positive
    high_quality_inspection: bool
    high_confidence_accuracy: bool
    reset_basis: str = Field(min_length=1)


class ThinningPeriod(Model):
    installed_at: AwareDatetime
    assessment_at: AwareDatetime
    baseline_type: Literal['furnished','measured']
    furnished_thickness_m: Positive | None = None
    measured_baseline: MeasuredBaseline | None = None
    days_per_year: Positive
    period_and_year_basis: str = Field(min_length=1)


def _utc(value):
    return value.astimezone(timezone.utc)


@calculation('damage/thinning-assessment-period','Consistent furnished/measured thickness baseline and elapsed period',ThinningPeriod,
    ['Part2 §4.5.5; PDF p151'],limitations=[
        'Timezone-aware timestamps normalized to UTC. Furnished thickness starts at installation; selected measured thickness starts at its qualified inspection time, requiring high-quality inspection, high-confidence accuracy and reset basis. Year conversion is explicit caller convention, not an API581-mandated constant. No process-change detection, measurement uncertainty correction, automatic reset selection or thickness reconciliation.'])
def thinning_period(x):
    ensure(bool(x.period_and_year_basis.strip()),'Common plan period and year conversion basis required')
    installed,assessment=_utc(x.installed_at),_utc(x.assessment_at)
    ensure(installed<=assessment,'Assessment cannot precede installation')
    if x.baseline_type=='furnished':
        ensure(x.furnished_thickness_m is not None and x.measured_baseline is None,'Furnished baseline requires only furnished thickness')
        baseline,thickness,inspection_id=installed,x.furnished_thickness_m,None
    else:
        ensure(x.measured_baseline is not None and x.furnished_thickness_m is None,'Measured baseline requires only measured baseline record')
        measured=x.measured_baseline
        ensure(measured.high_quality_inspection and measured.high_confidence_accuracy and bool(measured.reset_basis.strip()),
            'Measured thickness reset requires qualified inspection quality, accuracy and basis')
        ensure(bool(measured.inspection_id.strip()),'Baseline inspection ID must be nonblank')
        baseline,thickness,inspection_id=_utc(measured.measured_at),measured.thickness_m,measured.inspection_id
        ensure(installed<=baseline<=assessment,'Measured baseline must lie between installation and assessment')
    days=(assessment-baseline).total_seconds()/86400.
    return dict(baseline_type=x.baseline_type,baseline_at=baseline.isoformat(),assessment_at=assessment.isoformat(),
        baseline_thickness_m=thickness,baseline_inspection_id=inspection_id,elapsed_days=days,
        elapsed_years=days/x.days_per_year,days_per_year=x.days_per_year)


class ThinningInspectionRecord(Model):
    inspection_id: str = Field(min_length=1,max_length=100)
    performed_at: AwareDatetime
    effectiveness: Literal['a','b','c','d','e']
    qualified_for_component_mechanism: bool
    inspection_basis: str = Field(min_length=1)


class ThinningInspectionHistory(ThinningPeriod):
    inspections: list[ThinningInspectionRecord] = Field(max_length=10000)
    baseline_boundary_policy: Literal['include_baseline_time','exclude_baseline_time']


@calculation('damage/thinning-inspection-history','Assessment-period inspection eligibility and direct A-D counts',ThinningInspectionHistory,
    ['Part2 §§4.5.5-4.5.6; Tables4.6,2.C inspection guidance; PDF pp151-152'],limitations=[
        'Only performed, qualified inspections in the selected period receive A-D counts; E receives no credit. Before-baseline and after-assessment records remain excluded diagnostics. Exact baseline-time inclusion is explicit owner policy; source does not resolve duplicate use of a baseline-setting inspection. End time is included. Duplicate IDs or a baseline inspection ID with conflicting timestamp fail. No automatic NDE effectiveness grading, equivalent-count conversion, geometry/coverage qualification or credit for planned inspections.'])
def thinning_inspection_history(x):
    period=thinning_period(ThinningPeriod(**x.model_dump(include=set(ThinningPeriod.model_fields))))
    baseline,assessment=_utc(x.installed_at if x.baseline_type=='furnished' else x.measured_baseline.measured_at),_utc(x.assessment_at)
    ids=[i.inspection_id for i in x.inspections]
    ensure(len(set(ids))==len(ids) and all(s.strip() for s in ids),'Inspection IDs must be nonblank and unique')
    counts={grade:0 for grade in 'abcd'}
    eligible,excluded=[],{}
    for item in x.inspections:
        ensure(bool(item.inspection_basis.strip()),'Inspection effectiveness/eligibility basis required')
        at=_utc(item.performed_at)
        if item.inspection_id==period['baseline_inspection_id']:
            ensure(at==baseline,'Baseline inspection ID has conflicting performed time')
        reason=('before_baseline' if at<baseline else 'after_assessment' if at>assessment else
            'baseline_boundary' if at==baseline and x.baseline_boundary_policy=='exclude_baseline_time' else
            'unqualified' if not item.qualified_for_component_mechanism else 'ineffective_e' if item.effectiveness=='e' else None)
        if reason:
            excluded[item.inspection_id]=reason
        else:
            counts[item.effectiveness]+=1
            eligible.append(item.inspection_id)
    return {**period,**{'inspections_'+grade:value for grade,value in counts.items()},
        'eligible_inspection_ids':sorted(eligible),'excluded_inspection_reasons':excluded,
        'baseline_boundary_policy':x.baseline_boundary_policy}


class HistoryThinningAssessment(Model):
    history: ThinningInspectionHistory
    selection: ThinningRateSelection
    prior: PriorSelection
    strength: PressureStrength | CodeStrength = Field(discriminator='method')
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation('damage/thinning-history-assessment','Thickness/history/rate selection through period-consistent thinning DF',HistoryThinningAssessment,
    ['Part2 §§4.5.2-4.5.7; PDF pp150-156'],origin='qualified_thinning_baseline_history_composition',limitations=[
        'Selected baseline derives both wall thickness and elapsed period; eligible dated inspection records derive counts, with independently selected table/custom prior. No competing manually supplied age/counts. Strength baseline must agree with derived wall baseline. Rate-selection common-period and inspection coverage/type qualifications remain external. Generic other monitoring row only, no borrowed mechanism credits. Non-AST unclad scope; no automatic process-change reset, inspection scheduling, cladding or all-mechanism/asset risk.'])
def thinning_history_assessment(x):
    history=thinning_inspection_history(x.history)
    inspections=Posterior(**x.prior.model_dump(),**{key:history[key] for key in ('inspections_a','inspections_b','inspections_c','inspections_d')})
    result=selected_mechanism_thinning(SelectedMechanismThinning(selection=x.selection,
        starting_thickness_m=history['baseline_thickness_m'],elapsed_years=history['elapsed_years'],strength=x.strength,
        inspections=inspections,conditions=x.conditions,qualification_basis=x.qualification_basis))
    return {**history,**result}
