"""Single context interface for the future backend/data adapter."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from backend.core.finance import Cashflow
from backend.models.decision import EvidenceOut


@dataclass(frozen=True)
class FinancialContext:
    as_of_date: date
    available_balance_cents: int | None
    scheduled_cashflows: list[Cashflow]
    visible_until: date
    protected_buffer_cents: int | None
    evidence: list[EvidenceOut]
    assumptions: list[str]
    historical_summary: dict | None = None


class ContextProvider(Protocol):
    def get_context(self, persona_key: str) -> FinancialContext: ...
