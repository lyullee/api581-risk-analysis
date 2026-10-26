"""Explicit PRD service-age and inspection-history boundary calculations."""
from datetime import date
from typing import Literal
from pydantic import Field
from .core import Model, Positive, calculation, ensure


class ServiceEvent(Model):
    event_date: date
    event_type: Literal["test", "overhaul", "replacement", "design_change"]


class ServiceAge(Model):
    installation_date: date
    evaluation_date: date
    events: list[ServiceEvent] = Field(default_factory=list,max_length=10000)
    days_per_year: Positive = 365.25


@calculation("prd/service-age", "PRD as-new service age and valid-history start boundary", ServiceAge,
             ["Part 1 §7.1.6, §7.2.4(i)(5), §7.7.2-7.7.3; PDF pp48,57,70"],
             origin="api581_lifecycle_rules_with_explicit_calendar_convention",
             limitations=["Overhaul/replacement reset effective age; test alone does not. Replacement/design change invalidate earlier parameter-updating history. Inspection update window starts at later of last as-new reset and parameter-history validity boundary per §7.2.6 STEP6.4. Design change alone does not assert an as-new condition. Dates/age only, not automatic test/eta updating or new-curve qualification. Default365.25-day year is an explicit engineering calendar convention, not a claimed source mandate. Same-day ordered events are allowed."])
def service_age(x):
    ensure(x.evaluation_date >= x.installation_date,"Evaluation precedes original installation")
    reset,history = x.installation_date,x.installation_date
    last_test = None
    kind = "installation"
    previous = x.installation_date
    for event in x.events:
        ensure(previous <= event.event_date <= x.evaluation_date,"Service events must be chronological and within installation/evaluation dates")
        previous = event.event_date
        if event.event_type == "test":
            last_test = event.event_date
        elif event.event_type in ("overhaul","replacement"):
            reset,kind = event.event_date,event.event_type
        if event.event_type in ("replacement","design_change"):
            history = event.event_date
    return {"effective_age_years":(x.evaluation_date-reset).days/x.days_per_year,
            "elapsed_since_original_installation_years":(x.evaluation_date-x.installation_date).days/x.days_per_year,
            "last_age_reset_date":reset.isoformat(),"last_age_reset_type":kind,
            "parameter_history_valid_from_date":history.isoformat(),
            "inspection_update_start_date":max(reset,history).isoformat(),
            "last_test_date":None if last_test is None else last_test.isoformat(),"days_per_year":x.days_per_year}
