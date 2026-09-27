"""Validated, bounded historical facts for the explicitly enabled golden demo.

Query amounts are converted using Decimal; snapshot numbers are never imported
here. Dates of remaining installments are estimates, not scheduled cashflows.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.core.context_contract import FinancialContext
from backend.core.finance import shift_months_clamped
from backend.models.decision import EvidenceOut


REFERENCE_DATE = date(2025, 9, 30)
WINDOW_START = date(2025, 4, 1)
MONTH_START = date(2025, 9, 1)
TABLE_ID = "batalha-time-08-g7ha.hackathon_dados.extrato_sintetico"
Units = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
Cents = Annotated[int, Field(ge=0, le=10**18, strict=True)]
SafeLabel = Literal["Passagem aérea", "IPTU", "Artigos infantis", "Parcela observada"]
LIMITATIONS = [
    "Persona derivada da base sintética do hackathon. Não representa cliente real do Itaú.",
    "Referência da análise: 2025-09-30; histórico de abril a setembro, não posição financeira atual.",
    "Salário só inclui entrada identificada explicitamente como CLT; ausência de identificação permanece desconhecida.",
    "Gastos sem fatura são uma visão de despesas observadas, não conciliação completa nem fluxo de caixa.",
    "Histórico não confirma saldo disponível, renda futura, crédito ou todas as obrigações ativas.",
    "Término de parcela é estimado por repetição mensal do último registro; exige confirmação de vigência, valor e data.",
    "O alívio após término estimado é condicional e não garante capacidade para nova compra.",
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class _MonthlyUnits(_Strict):
    month: date
    salary_units: Units | None
    expenses_excluding_invoice_units: Units
    interest_units: Units


class _CategoryUnits(_Strict):
    category: str = Field(min_length=1, max_length=160)
    amount_units: Units


class _InstallmentUnits(_Strict):
    label: SafeLabel
    amount_units: Units
    current: int = Field(ge=1, le=360, strict=True)
    total: int = Field(ge=1, le=360, strict=True)
    last_observed_date: date


class _QueryResult(_Strict):
    coverage_start: date | None
    coverage_end: date | None
    row_count: int = Field(ge=0, strict=True)
    invalid_rows: int = Field(ge=0, strict=True)
    monthly: list[_MonthlyUnits] = Field(max_length=6)
    categories: list[_CategoryUnits] = Field(max_length=12)
    installments: list[_InstallmentUnits] = Field(max_length=12)
    category_count: int = Field(ge=0, strict=True)
    installment_count: int = Field(ge=0, strict=True)


class _Monthly(_Strict):
    month: date
    salary_cents: Cents | None
    expenses_excluding_invoice_cents: Cents
    flexible_cents: Cents | None
    interest_cents: Cents


class _Category(_Strict):
    category: str = Field(min_length=1, max_length=160)
    amount_cents: Cents


class _Installment(_Strict):
    label: SafeLabel
    amount_cents: Cents
    current: int = Field(ge=1, le=360, strict=True)
    total: int = Field(ge=1, le=360, strict=True)
    last_observed_date: date | None
    estimated_end_date: date
    requires_confirmation: Literal[True]


class GoldenSnapshot(_Strict):
    reference_date: date
    currency: Literal["BRL"]
    origin: Literal["dataset_observed", "user_supplied_hackathon_snapshot"]
    monthly: list[_Monthly] = Field(max_length=6)
    installments: list[_Installment] = Field(max_length=12)
    categories: list[_Category] = Field(max_length=12)
    limitations: list[str] = Field(max_length=30)


def validate_snapshot(payload: dict) -> GoldenSnapshot:
    result = GoldenSnapshot.model_validate(payload)
    if result.reference_date != REFERENCE_DATE:
        raise ValueError("Golden reference date is fixed")
    months = [item.month for item in result.monthly]
    if months != sorted(set(months)) or any(
            value.day != 1 or not WINDOW_START <= value <= MONTH_START for value in months):
        raise ValueError("Invalid golden month coverage")
    for item in result.monthly:
        if item.interest_cents > item.expenses_excluding_invoice_cents:
            raise ValueError("Interest cannot exceed observed expenses")
        if item.flexible_cents is not None and item.flexible_cents > item.expenses_excluding_invoice_cents:
            raise ValueError("Flexible expenses exceed observed expenses")
    if len({item.category for item in result.categories}) != len(result.categories):
        raise ValueError("Repeated category aggregate")
    for item in result.installments:
        if item.current >= item.total or item.estimated_end_date <= REFERENCE_DATE:
            raise ValueError("Invalid ongoing installment")
        if item.last_observed_date is not None:
            if not MONTH_START <= item.last_observed_date <= REFERENCE_DATE:
                raise ValueError("Installment was not observed in the reference month")
            if item.estimated_end_date != shift_months_clamped(item.last_observed_date, item.total - item.current):
                raise ValueError("Inconsistent installment estimate")
        elif result.origin == "dataset_observed":
            raise ValueError("Real observations require their source date")
    return result


def context_from_snapshot(snapshot: GoldenSnapshot, *, coverage: dict | None = None,
                          row_count: int | None = None) -> FinancialContext:
    fixture = snapshot.origin == "user_supplied_hackathon_snapshot"
    limitations = [*LIMITATIONS, *snapshot.limitations]
    history = {
        "source": TABLE_ID, "origin": snapshot.origin, "currency": "BRL",
        "reference_date": REFERENCE_DATE.isoformat(),
        "coverage": coverage or {"start": None, "end": None},
        "observed_facts": {}, "recurrence_candidates": [], "observed_installments": [],
        "golden": snapshot.model_dump(mode="json"), "limitations": limitations,
    }
    if row_count is not None:
        history["observed_facts"]["row_count"] = row_count
    return FinancialContext(
        as_of_date=REFERENCE_DATE, available_balance_cents=None, scheduled_cashflows=[],
        visible_until=REFERENCE_DATE + timedelta(days=90), protected_buffer_cents=None,
        evidence=[EvidenceOut(id="golden-source", label="Persona sintética de referência",
            origin="user_confirmed" if fixture else "dataset_observed",
            detail=("Snapshot fornecido pelo usuário; leitura offline explícita, sem consulta BigQuery."
                    if fixture else "Agregados BigQuery do perfil autorizado, limitados à referência 2025-09-30."))],
        assumptions=limitations, historical_summary=history,
    )


def query_result_to_context(payload: dict, reference_date: date) -> FinancialContext:
    if reference_date != REFERENCE_DATE:
        raise ValueError("Golden reference date is fixed")
    rows = _QueryResult.model_validate(payload)
    if rows.invalid_rows:
        raise ValueError("Invalid source rows")
    if rows.row_count:
        if not (rows.coverage_start and rows.coverage_end and rows.monthly
                and WINDOW_START <= rows.coverage_start <= rows.coverage_end <= REFERENCE_DATE):
            raise ValueError("Invalid source coverage")
        if any(not rows.coverage_start.replace(day=1) <= item.month <= rows.coverage_end
               for item in rows.monthly):
            raise ValueError("Month outside observed coverage")
    elif rows.coverage_start or rows.coverage_end or rows.monthly or rows.categories or rows.installments:
        raise ValueError("Inconsistent empty history")
    if (len(rows.categories) != min(rows.category_count, 12)
            or len(rows.installments) != min(rows.installment_count, 12)):
        raise ValueError("Inconsistent aggregate counts")
    for item in rows.installments:
        if not (rows.coverage_start and rows.coverage_end
                and rows.coverage_start <= item.last_observed_date <= rows.coverage_end):
            raise ValueError("Installment outside observed coverage")
    limitations = [
        "BRL confirmado para esta persona pelo snapshot fornecido; valores consultados convertidos com Decimal.",
        "Gastos flexíveis permanecem desconhecidos: classificação do snapshot ainda não foi verificada.",
        "Descrição livre e identificadores não integram o contexto retornado.",
    ]
    if len(rows.monthly) < 6:
        limitations.append("Menos de seis meses observados; não preencher meses ausentes com zero.")
    if rows.category_count > 12 or rows.installment_count > 12:
        limitations.append("Categorias/parcelas limitadas a 12 registros; resumo não exaustivo.")
    cents = lambda amount: None if amount is None else int(amount * 100)
    snapshot = validate_snapshot({
        "reference_date": reference_date, "currency": "BRL", "origin": "dataset_observed",
        "monthly": [{"month": item.month, "salary_cents": cents(item.salary_units),
            "expenses_excluding_invoice_cents": cents(item.expenses_excluding_invoice_units),
            "flexible_cents": None, "interest_cents": cents(item.interest_units)} for item in rows.monthly],
        "categories": [{"category": item.category, "amount_cents": cents(item.amount_units)}
                       for item in rows.categories],
        "installments": [{"label": item.label, "amount_cents": cents(item.amount_units),
            "current": item.current, "total": item.total, "last_observed_date": item.last_observed_date,
            "estimated_end_date": shift_months_clamped(item.last_observed_date, item.total - item.current),
            "requires_confirmation": True} for item in rows.installments],
        "limitations": limitations,
    })
    return context_from_snapshot(snapshot, coverage={
        "start": rows.coverage_start.isoformat() if rows.coverage_start else None,
        "end": rows.coverage_end.isoformat() if rows.coverage_end else None,
    }, row_count=rows.row_count)
