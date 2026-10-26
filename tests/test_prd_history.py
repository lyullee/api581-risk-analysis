import pytest
from api581 import DomainError
from api581.api import prd


def age(events=(),**changes):
    return prd.service_age(prd.ServiceAgeInput(**{**dict(installation_date="2020-01-01",
        evaluation_date="2021-01-01",events=list(events),days_per_year=365.25),**changes})).outputs


def event(date,kind):
    return prd.ServiceEventInput(event_date=date,event_type=kind)


def test_leap_year_age_is_an_explicit_day_count_not_rounded_calendar_year():
    result=age()
    assert result.effective_age_years == pytest.approx(366/365.25)
    assert result.last_test_date is None
    assert result.last_age_reset_type == "installation"
    assert age(days_per_year=366).effective_age_years == 1


def test_test_alone_does_not_make_prd_as_new():
    original=age()
    tested=age([event("2020-12-31","test")])
    assert tested.effective_age_years == original.effective_age_years
    assert tested.last_age_reset_date == "2020-01-01"
    assert tested.last_test_date == "2020-12-31"


def test_same_day_test_and_overhaul_start_new_age_but_not_new_design_history():
    result=age([event("2020-12-31","test"),event("2020-12-31","overhaul")])
    assert result.effective_age_years == pytest.approx(1/365.25)
    assert result.last_age_reset_type == "overhaul"
    assert result.parameter_history_valid_from_date == "2020-01-01"
    assert result.inspection_update_start_date == "2020-12-31"


def test_replacement_starts_both_new_age_and_device_history():
    result=age([event("2020-07-01","replacement")])
    assert result.effective_age_years == pytest.approx(184/365.25)
    assert result.parameter_history_valid_from_date == result.last_age_reset_date == "2020-07-01"


def test_design_change_invalidates_curve_history_without_assuming_as_new():
    result=age([event("2020-07-01","design_change")])
    assert result.effective_age_years == pytest.approx(366/365.25)
    assert result.parameter_history_valid_from_date == "2020-07-01"
    assert result.inspection_update_start_date == "2020-07-01"


@pytest.mark.parametrize("events", [
    [event("2019-12-31","test")], [event("2021-01-02","test")],
    [event("2020-08-01","test"),event("2020-07-01","overhaul")]])
def test_invalid_event_chronology_is_rejected(events):
    with pytest.raises(DomainError):
        age(events)


def test_evaluation_cannot_precede_installation():
    with pytest.raises(DomainError):
        age(evaluation_date="2019-12-31")
