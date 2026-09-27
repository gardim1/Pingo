from typing import Literal
from pydantic import Field
from datetime import date
from backend.models.decision import DecisionRequest, DecisionResponse, DecisionTerms, Preferences, StrictModel, PlanSnapshot, ConfirmedContext


class RuntimeInfo(StrictModel):
    agent: str
    model: str | None = None
    data: str
    safety: str
    tools: list[str] = Field(default_factory=list)


class HistoricalComparison(StrictModel):
    month: date
    conditional_release_cents: int
    benchmark_margin_cents: int
    margin_after_installment_min_cents: int | None
    margin_after_installment_max_cents: int | None


class GoldenAnalysis(StrictModel):
    reference_date: date
    data_source: str
    salary_observed_cents: int | None
    recent_average_margin_cents: int | None
    six_month_average_margin_cents: int | None
    last_month_margin_cents: int | None
    observed_installments_total_cents: int
    observed_installment_count: int
    estimated_last_installment_month: date | None
    installments_cents: list[int]
    selected_month: date
    selected_conditional_release_cents: int
    comparisons: list[HistoricalComparison]
    assumptions: list[str]
    simulated_purchase_cents: int = 0
    event_month_before_cents: int | None = None
    event_month_after_cents: int | None = None


class ChatResponse(StrictModel):
    session_id: str
    message: str
    draft: DecisionTerms | None
    decision: DecisionResponse | None
    runtime: RuntimeInfo
    accompaniment_enabled: Literal[False] = False
    golden_analysis: GoldenAnalysis | None = None


class PlanRequest(DecisionRequest):
    consent_enabled: bool = Field(default=False, strict=True)


class SavedPlan(StrictModel):
    plan_id: str
    decision: DecisionTerms | None
    preferences: Preferences | None
    storage: Literal['client_session_only'] = 'client_session_only'
    accompaniment_enabled: Literal[False] = False


class SimulatedEvent(StrictModel):
    event_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    kind: Literal['demo_purchase_posted']
    offer_ref: Literal['demo-iphone', 'golden-extra-1000']


class AccompanimentRequest(StrictModel):
    persona_key: str | None = Field(default=None, min_length=1, max_length=100)
    consent_enabled: bool = Field(default=False, strict=True)
    event: SimulatedEvent | None = None
    plan_snapshot: PlanSnapshot | None = None
    confirmed_context: ConfirmedContext | None = None


class AccompanimentResponse(StrictModel):
    reviewed: bool
    reason: Literal['opted_out','reviewed','needs_confirmation']
    decision: DecisionResponse | None
