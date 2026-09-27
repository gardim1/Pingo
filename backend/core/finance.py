"""Pure, integer-cent scenario calculations. No historical ledger inference."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Installment:
    due_date: date
    amount_cents: int


@dataclass(frozen=True)
class Cashflow:
    date: date
    amount_cents: int  # Negative is an outflow.


@dataclass(frozen=True)
class ProjectionResult:
    mode: str
    through_date: date | None
    min_balance_cents: int | None
    end_balance_cents: int | None
    assessment: str
    remaining_after_window_cents: int


def split_installments(amount_cents: int, count: int) -> list[int]:
    if amount_cents < 0 or count < 1:
        raise ValueError("amount_cents must be nonnegative and count positive")
    base, extra = divmod(amount_cents, count)
    return [base + (index < extra) for index in range(count)]


def shift_months_clamped(first_due_date: date, offset: int) -> date:
    month_index = first_due_date.year * 12 + first_due_date.month - 1 + offset
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(first_due_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def build_schedule(
    total_price_cents: int, upfront_cents: int, installment_count: int, first_due_date: date
) -> list[Installment]:
    if total_price_cents < 0 or upfront_cents < 0 or upfront_cents > total_price_cents:
        raise ValueError("upfront_cents must be between zero and total_price_cents")
    if not 1 <= installment_count <= 60:
        raise ValueError("installment_count must be between 1 and 60")
    amounts = split_installments(total_price_cents - upfront_cents, installment_count)
    return [Installment(shift_months_clamped(first_due_date, i), amount) for i, amount in enumerate(amounts)]


def project(
    schedule: list[Installment],
    upfront_cents: int,
    as_of_date: date,
    through_date: date,
    opening_balance_cents: int | None,
    cashflows: list[Cashflow],
    protected_buffer_cents: int = 0,
) -> ProjectionResult:
    if through_date < as_of_date:
        raise ValueError("through_date precedes as_of_date")
    if schedule and schedule[0].due_date < as_of_date:
        raise ValueError("first_due_date precedes as_of_date")
    if protected_buffer_cents < 0 or upfront_cents < 0:
        raise ValueError("buffer and upfront must be nonnegative")

    remaining = sum(item.amount_cents for item in schedule if item.due_date > through_date)
    if opening_balance_cents is None:
        return ProjectionResult("unavailable", None, None, None, "insufficient_data", remaining)

    events = [Cashflow(as_of_date, -upfront_cents)] if upfront_cents else []
    events.extend(Cashflow(item.due_date, -item.amount_cents) for item in schedule)
    events.extend(cashflows)
    events = [event for event in events if as_of_date <= event.date <= through_date]
    events.sort(key=lambda event: (event.date, event.amount_cents >= 0))

    balance = opening_balance_cents
    minimum = balance
    for event in events:
        balance += event.amount_cents
        minimum = min(minimum, balance)
    assessment = (
        "meets_declared_constraints_in_window"
        if minimum >= protected_buffer_cents
        else "violates_declared_constraints_in_window"
    )
    return ProjectionResult(
        "scenario_with_assumptions", through_date, minimum, balance, assessment, remaining
    )
