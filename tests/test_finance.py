from datetime import date

import pytest

from backend.core.finance import Cashflow, build_schedule, project, split_installments


def test_installments_preserve_every_cent():
    assert split_installments(10000, 3) == [3334, 3333, 3333]


def test_month_end_dates_follow_original_day_including_leap_year():
    schedule = build_schedule(300, 0, 3, date(2024, 1, 31))
    assert [item.due_date.isoformat() for item in schedule] == [
        "2024-01-31", "2024-02-29", "2024-03-31"
    ]


def test_full_schedule_survives_short_visible_window():
    schedule = build_schedule(1200, 0, 12, date(2026, 10, 1))
    result = project(schedule, 0, date(2026, 9, 26), date(2026, 12, 31), None, [])
    assert len(schedule) == 12
    assert result.remaining_after_window_cents == 900
    assert result.min_balance_cents is None
    assert result.mode == "unavailable"


def test_illustrative_fixture_now_matches_hand_checked_minimum():
    schedule = build_schedule(1000000, 0, 10, date(2026, 10, 1))
    cashflows = [
        Cashflow(date(2026, 10, 1), -120000),
        Cashflow(date(2026, 10, 5), 600000),
        Cashflow(date(2026, 10, 10), -280000),
        Cashflow(date(2026, 10, 15), -100000),
        Cashflow(date(2026, 11, 1), -120000),
        Cashflow(date(2026, 11, 5), 600000),
        Cashflow(date(2026, 11, 10), -280000),
        Cashflow(date(2026, 11, 15), -100000),
        Cashflow(date(2026, 12, 1), -120000),
        Cashflow(date(2026, 12, 5), 600000),
        Cashflow(date(2026, 12, 10), -280000),
        Cashflow(date(2026, 12, 15), -100000),
    ]
    result = project(schedule, 0, date(2026, 9, 26), date(2026, 12, 31), 200000, cashflows)
    assert result.min_balance_cents == -20000
    assert result.remaining_after_window_cents == 700000


def test_upfront_and_installments_are_deducted_once_each():
    schedule = build_schedule(10000, 2000, 2, date(2026, 10, 1))
    result = project(schedule, 2000, date(2026, 9, 26), date(2026, 10, 31), 10000, [])
    assert [item.amount_cents for item in schedule] == [4000, 4000]
    assert result.end_balance_cents == 4000
    assert result.remaining_after_window_cents == 4000


def test_outflows_precede_inflows_when_only_date_is_known():
    schedule = build_schedule(100, 0, 1, date(2026, 10, 1))
    result = project(schedule, 0, date(2026, 9, 26), date(2026, 10, 1), 0,
                     [Cashflow(date(2026, 10, 1), 200)])
    assert result.min_balance_cents == -100
    assert result.end_balance_cents == 100


def test_first_due_date_cannot_precede_as_of_date():
    schedule = build_schedule(100, 0, 1, date(2026, 9, 25))
    with pytest.raises(ValueError, match="first_due_date"):
        project(schedule, 0, date(2026, 9, 26), date(2026, 12, 31), None, [])
