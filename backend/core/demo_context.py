"""Explicit own synthetic fixture; never used when DEMO_MODE is false."""

import json
from datetime import date
from pathlib import Path

from backend.core.context_contract import FinancialContext
from backend.core.finance import Cashflow
from backend.models.decision import EvidenceOut


FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "calculo-ilustrativo.json"
DEMO_PERSONAS = {"persona-a": "Exemplo A — dados fictícios"}


class OwnSyntheticDemoProvider:
    def get_context(self, persona_key: str) -> FinancialContext:
        if persona_key not in DEMO_PERSONAS:
            raise KeyError("persona not in demo allowlist")
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cashflows = [
            Cashflow(date.fromisoformat(item["date"]), item["amount_cents"])
            for item in fixture["events"]
        ]
        return FinancialContext(
            as_of_date=date.fromisoformat(fixture["as_of_date"]),
            available_balance_cents=fixture["opening_balance_cents"],
            scheduled_cashflows=cashflows,
            visible_until=date.fromisoformat(fixture["projection_until"]),
            protected_buffer_cents=0,
            evidence=[EvidenceOut(
                id="fixture-context", label="Contexto inteiramente fictício",
                origin="own_synthetic_fixture",
                detail="Saldo e movimentos do fixture próprio de teste; não representam dados bancários atuais.",
            )],
            assumptions=[
                "Dados próprios de demonstração; nenhuma consulta BigQuery ou chamada Gemini foi feita.",
                "Os movimentos do fixture são hipotéticos e não representam orçamento completo.",
            ],
        )
