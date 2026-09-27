"""HTTP models matching the shared DecisionResponse 1.0 schema."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DecisionTerms(StrictModel):
    label: str | None = Field(default=None, max_length=160)
    total_price_cents: int | None = Field(default=None, ge=0, strict=True)
    upfront_cents: int | None = Field(default=None, ge=0, strict=True)
    installment_count: int | None = Field(default=None, ge=1, le=60, strict=True)
    first_due_date: date | None = None
    interest_free: bool | None = Field(default=None, strict=True)
    purchase_month: date | None = None

    @model_validator(mode="after")
    def check_upfront(self):
        if self.purchase_month is not None and self.purchase_month.day != 1:
            raise ValueError('purchase_month must identify the first day of a month, not a due date')
        if (self.total_price_cents is not None and self.upfront_cents is not None
                and self.upfront_cents > self.total_price_cents):
            raise ValueError("upfront_cents exceeds total_price_cents")
        return self


class Preferences(StrictModel):
    purpose: str | None = Field(default=None, max_length=500)
    can_wait: bool | None = None
    protected_items: list[str] = Field(default_factory=list, max_length=20)


class ScheduledCashflow(StrictModel):
    ref: str = Field(min_length=1, max_length=100)
    date: date
    amount_cents: int = Field(ge=0, strict=True)
    direction: Literal["inflow", "outflow"]
    accounting_kind: Literal['ordinary', 'card_purchase', 'card_bill_payment'] = 'ordinary'
    settlement_ref: str | None = Field(default=None, max_length=100)


class ConfirmedContext(StrictModel):
    as_of_date: date
    available_balance_cents: int | None = Field(default=None, strict=True)
    scheduled_cashflows: list[ScheduledCashflow] = Field(default_factory=list, max_length=500)
    protected_buffer_cents: int | None = Field(default=None, ge=0, strict=True)

    @model_validator(mode="after")
    def check_refs(self):
        refs = [item.ref for item in self.scheduled_cashflows]
        if len(refs) != len(set(refs)):
            raise ValueError("duplicate scheduled_cashflows ref")
        if any(item.date < self.as_of_date for item in self.scheduled_cashflows):
            raise ValueError("scheduled_cashflows cannot precede as_of_date")
        bills = {item.ref: item for item in self.scheduled_cashflows
                 if item.accounting_kind == 'card_bill_payment' and item.direction == 'outflow'}
        for item in self.scheduled_cashflows:
            if item.accounting_kind == 'card_purchase':
                bill = bills.get(item.settlement_ref)
                if bill is None or item.direction != 'outflow' or bill.date < item.date:
                    raise ValueError('card purchase requires a confirmed linked bill payment')
            elif item.settlement_ref is not None:
                raise ValueError('settlement_ref is only valid for card purchases')
            if item.accounting_kind == 'card_bill_payment' and item.direction != 'outflow':
                raise ValueError('card bill payment must be an outflow')
        for ref, bill in bills.items():
            if sum(item.amount_cents for item in self.scheduled_cashflows if item.settlement_ref == ref) > bill.amount_cents:
                raise ValueError('linked purchases exceed confirmed bill amount')
        return self


class DecisionRequest(StrictModel):
    message: str = Field(min_length=1, max_length=2000)
    persona_key: str | None = Field(default=None, min_length=1, max_length=100)
    decision: DecisionTerms | None = None
    preferences: Preferences | None = None
    previous_request_id: str | None = Field(default=None, max_length=100)
    confirmed_context: ConfirmedContext | None = None


class PlanSnapshot(BaseModel):
    # Browser snapshots are untrusted; calculated fields are ignored.
    model_config = ConfigDict(extra="ignore")
    decision: DecisionTerms | None = None
    preferences: Preferences | None = None
    saved_as_of_date: date | None = None


class DecisionReviewRequest(DecisionRequest):
    plan_snapshot: PlanSnapshot | None = None


class Question(StrictModel):
    field: str
    text: str


class InstallmentOut(StrictModel):
    due_date: date
    amount_cents: int = Field(ge=0)


class ProjectionOut(StrictModel):
    mode: Literal["unavailable", "scenario_with_assumptions"]
    through_date: date | None
    min_balance_cents: int | None
    assessment: Literal[
        "insufficient_data", "meets_declared_constraints_in_window",
        "violates_declared_constraints_in_window",
    ]


class ScenarioOut(StrictModel):
    id: str
    title: str
    total_price_cents: int = Field(ge=0)
    upfront_cents: int = Field(ge=0)
    schedule: list[InstallmentOut]
    visible_until: date
    remaining_after_window_cents: int = Field(ge=0)
    projection: ProjectionOut
    reason_evidence_ids: list[str]


class EvidenceOut(StrictModel):
    id: str
    label: str
    origin: Literal["user_confirmed", "dataset_observed", "derived", "own_synthetic_fixture"]
    detail: str


class DecisionResponse(StrictModel):
    contract_version: Literal["1.0"] = "1.0"
    request_id: str
    data_mode: Literal["own_synthetic_demo", "event_dataset_demo"]
    as_of_date: date
    state: Literal["needs_input", "ready", "limited", "blocked", "error"]
    message: str
    question: Question | None
    scenarios: list[ScenarioOut] = Field(max_length=3)
    evidence: list[EvidenceOut]
    assumptions: list[str]
    actions: list[Literal[
        "update_inputs", "compare_options", "save_plan", "review_plan",
        "request_support", "open_demo_checkout",
    ]]
    trace_id: str
