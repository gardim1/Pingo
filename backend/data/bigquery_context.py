"""BigQuery history adapter; it cannot supply today's balance or future obligations.

The caller must construct the allowlist from trusted backend configuration. This
module is not an authentication service and must not be exposed as a raw LLM tool.
"""

from collections.abc import Mapping
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
from types import MappingProxyType

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.core.context_contract import FinancialContext
from backend.models.decision import EvidenceOut


PROJECT_ID = "batalha-time-08-g7ha"
TABLE_ID = f"{PROJECT_ID}.hackathon_dados.extrato_sintetico"
LOCATION = "us-central1"
COVERAGE_START = date(2025, 1, 1)
COVERAGE_END = date(2025, 12, 31)
MAXIMUM_BYTES = 1073741824
QUERY = Path(__file__).with_name("historical_context.sql").read_text(encoding="utf-8")
LIMITATIONS = [
    "Histórico observado de 2025; não confirma saldo atual, crédito disponível ou obrigações futuras.",
    "Entradas observadas podem ser transferências, estornos ou empréstimos; não equivalem a salário.",
    "Compra e pagamento de fatura não têm conciliação confiável; totais observados não entram na projeção.",
    "Recorrências são candidatas, e marcadores de parcela não comprovam contrato ativo nem parcelas restantes.",
    "Datas históricas usam UTC, conforme o diagnóstico; o fuso operacional da base não foi confirmado.",
    "A unidade monetária da base não foi confirmada; valores históricos não são convertidos em centavos BRL.",
    "Resumo limitado a 12 meses, 12 categorias, 10 recorrências e 12 grupos de parcelas; listas não são exaustivas.",
]


class DataAccessDenied(PermissionError):
    """An identity outside the backend allowlist attempted a query."""


class DataProviderError(RuntimeError):
    """Safe exception: never contains the SDK error, query arguments or identity."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Contexto BigQuery indisponível ({code}).")


class _StrictAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class _Monthly(_StrictAggregate):
    month: date
    entry_count: int = Field(ge=0, strict=True)
    exit_count: int = Field(ge=0, strict=True)
    entry_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)
    exit_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)
    invoice_payment_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)
    transfer_exit_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)


class _Category(_StrictAggregate):
    category: str = Field(min_length=1, max_length=160)
    direction: str = Field(pattern="^[ES]$")
    count: int = Field(ge=1, strict=True)
    amount_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)


class _Recurrence(_StrictAggregate):
    category: str = Field(min_length=1, max_length=160)
    months_observed: int = Field(ge=3, le=12, strict=True)
    consecutive_pairs: int = Field(ge=2, le=11, strict=True)
    min_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)
    max_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)
    last_observed_date: date


class _Installment(_StrictAggregate):
    category: str = Field(min_length=1, max_length=160)
    count: int = Field(ge=1, strict=True)
    first_observed_date: date
    last_observed_date: date
    min_installment_index: int = Field(ge=1, strict=True)
    max_installment_index: int = Field(ge=1, strict=True)
    max_installment_total: int = Field(ge=1, strict=True)
    observed_units: Decimal = Field(ge=0, max_digits=38, decimal_places=2)


class _Aggregates(_StrictAggregate):
    coverage_start: date | None
    coverage_end: date | None
    row_count: int = Field(ge=0, strict=True)
    invalid_rows: int = Field(ge=0, strict=True)
    monthly: list[_Monthly] = Field(max_length=12)
    categories: list[_Category] = Field(max_length=12)
    recurrence_candidates: list[_Recurrence] = Field(max_length=10)
    observed_installments: list[_Installment] = Field(max_length=12)


def _validate_summary(payload: dict, reference_date: date) -> _Aggregates:
    result = _Aggregates.model_validate(payload)
    if result.invalid_rows:
        raise ValueError("invalid history")
    if not result.row_count:
        if (result.coverage_start is not None or result.coverage_end is not None
                or result.monthly or result.categories or result.recurrence_candidates
                or result.observed_installments):
            raise ValueError("inconsistent empty history")
        return result
    cutoff = min(reference_date, COVERAGE_END)
    if not (result.coverage_start and result.coverage_end
            and COVERAGE_START <= result.coverage_start <= result.coverage_end <= cutoff):
        raise ValueError("invalid coverage")
    if not result.monthly:
        raise ValueError("missing monthly coverage")
    for item in result.monthly:
        if not (item.month.day == 1 and COVERAGE_START <= item.month <= cutoff):
            raise ValueError("invalid month")
        if item.invoice_payment_units + item.transfer_exit_units > item.exit_units:
            raise ValueError("inconsistent outgoing components")
    for item in result.recurrence_candidates:
        if not (result.coverage_start <= item.last_observed_date <= result.coverage_end
                and item.min_units <= item.max_units <= item.min_units * Decimal("1.2")
                and item.consecutive_pairs < item.months_observed):
            raise ValueError("invalid recurrence")
    for item in result.observed_installments:
        if not (result.coverage_start <= item.first_observed_date
                <= item.last_observed_date <= result.coverage_end
                and item.min_installment_index <= item.max_installment_index
                <= item.max_installment_total):
            raise ValueError("invalid installment observations")
    return result


class BigQueryContextProvider:
    def __init__(
        self, *, authorized_users: Mapping[str, str], reference_date: date | None = None,
        client=None, project_id: str = PROJECT_ID, location: str = LOCATION,
        maximum_bytes_billed: int = MAXIMUM_BYTES, timeout_seconds: float = 20.0,
        golden_persona: bool = False,
    ):
        if not authorized_users or any(
            not isinstance(key, str) or not key.strip() or len(key) > 100
            or not isinstance(value, str) or not value.strip() or len(value) > 256
            or any(ord(c) < 32 for c in key + value)
            for key, value in authorized_users.items()
        ):
            raise ValueError("A backend identity allowlist is required")
        if project_id != PROJECT_ID or location != LOCATION:
            raise ValueError("Only the authorized project and dataset location are permitted")
        if (type(maximum_bytes_billed) is not int or not 0 < maximum_bytes_billed <= MAXIMUM_BYTES
                or not 0 < timeout_seconds <= 60):
            raise ValueError("Invalid query limits")
        if reference_date is not None and type(reference_date) is not date:
            raise ValueError("reference_date must be a date")
        if type(golden_persona) is not bool:
            raise ValueError("golden_persona must be an explicit bool")
        if golden_persona and reference_date != date(2025, 9, 30):
            raise ValueError("Golden reference_date must be explicitly 2025-09-30")
        self._authorized_users = MappingProxyType(dict(authorized_users))
        self._reference_date = reference_date or date.today()
        self._client = client
        self._project_id = project_id
        self._location = location
        self._maximum_bytes_billed = maximum_bytes_billed
        self._timeout_seconds = float(timeout_seconds)
        self._golden_persona = golden_persona

    def get_context(self, persona_key: str) -> FinancialContext:
        user_id = self._authorized_users.get(persona_key)
        if user_id is None:
            raise DataAccessDenied("Persona não autorizada pelo backend.")
        return self.get_financial_context(user_id, self._reference_date)

    def get_financial_context(self, user_id: str, reference_date: date) -> FinancialContext:
        if user_id not in self._authorized_users.values():
            raise DataAccessDenied("Identidade não autorizada pelo backend.")
        if type(reference_date) is not date:
            raise ValueError("reference_date must be a date")
        if self._golden_persona and reference_date != date(2025, 9, 30):
            raise ValueError("Golden reference_date must be 2025-09-30")
        query = (Path(__file__).with_name("golden_context.sql").read_text(encoding="utf-8")
                 if self._golden_persona else QUERY)
        try:
            from google.cloud import bigquery
        except ImportError:
            raise DataProviderError("bigquery_sdk_missing") from None
        job = None
        try:
            client = self._client or bigquery.Client(project=self._project_id, location=self._location)
            parameters = [
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("reference_date", "DATE", reference_date),
                bigquery.ScalarQueryParameter("coverage_start", "DATE", COVERAGE_START),
                bigquery.ScalarQueryParameter("coverage_end", "DATE", COVERAGE_END),
            ]

            def config(dry_run: bool):
                return bigquery.QueryJobConfig(
                    use_legacy_sql=False, dry_run=dry_run, use_query_cache=not dry_run,
                    maximum_bytes_billed=self._maximum_bytes_billed,
                    job_timeout_ms=int(self._timeout_seconds * 1000),
                    query_parameters=parameters, labels={"application": "pingo", "purpose": "context"},
                )

            options = dict(location=self._location, timeout=self._timeout_seconds,
                           retry=None, job_retry=None)
            estimate = client.query(query, job_config=config(True), **options)
            if estimate.total_bytes_processed is None:
                raise DataProviderError("bigquery_estimate_unavailable")
            if estimate.total_bytes_processed > self._maximum_bytes_billed:
                raise DataProviderError("bigquery_budget_exceeded")
            job = client.query(query, job_config=config(False), **options)
            rows = list(job.result(timeout=self._timeout_seconds, max_results=1,
                                   retry=None, job_retry=None))
        except DataProviderError:
            raise
        except Exception:
            if job is not None:
                try:
                    job.cancel(retry=None, timeout=5)
                except Exception:
                    pass
            raise DataProviderError("bigquery_unavailable") from None
        try:
            if len(rows) != 1 or len(rows[0]["summary_json"]) > 50000:
                raise ValueError("unexpected aggregate size")
            if self._golden_persona:
                from backend.data.golden_context import query_result_to_context
                return query_result_to_context(json.loads(rows[0]["summary_json"]), reference_date)
            aggregates = _validate_summary(json.loads(rows[0]["summary_json"]), reference_date)
        except (ValueError, TypeError, KeyError, ValidationError):
            raise DataProviderError("bigquery_invalid_result") from None
        return _to_context(aggregates, reference_date)


def _to_context(aggregates: _Aggregates, reference_date: date) -> FinancialContext:
    raw = aggregates.model_dump(mode="json")
    limitations = list(LIMITATIONS)
    if aggregates.row_count == 0:
        limitations.append("Nenhum lançamento observado para o perfil autorizado no período consultado.")
    history = {
        "source": TABLE_ID, "origin": "dataset_observed", "currency": None,
        "reference_date": reference_date.isoformat(),
        "coverage": {"start": raw["coverage_start"], "end": raw["coverage_end"]},
        "observed_facts": {"row_count": raw["row_count"], "monthly": raw["monthly"],
                           "categories": raw["categories"]},
        "recurrence_candidates": [
            {**item, "origin": "derived", "requires_confirmation": True}
            for item in raw["recurrence_candidates"]
        ],
        "observed_installments": [
            {**item, "origin": "dataset_observed", "future_schedule_known": False}
            for item in raw["observed_installments"]
        ],
        "limitations": limitations,
    }
    coverage_detail = (
        f"Origem: {TABLE_ID}. Cobertura observada: {raw['coverage_start']} a {raw['coverage_end']}. "
        "Histórico sintético; não representa posição financeira atual."
        if aggregates.row_count else "Sem registros para o perfil autorizado no período consultado."
    )
    return FinancialContext(
        as_of_date=reference_date, available_balance_cents=None, scheduled_cashflows=[],
        visible_until=reference_date + timedelta(days=90), protected_buffer_cents=None,
        evidence=[
            EvidenceOut(id="bq-coverage", label="Origem e cobertura histórica",
                        origin="dataset_observed", detail=coverage_detail),
            EvidenceOut(id="bq-recurrence-candidates", label="Recorrências candidatas",
                        origin="derived", detail="Repetições históricas exigem confirmação de vigência, valor e vencimento."),
            EvidenceOut(id="bq-installments-observed", label="Marcadores de parcela históricos",
                        origin="dataset_observed", detail="Parcelas observadas não foram convertidas em compromissos futuros."),
        ],
        assumptions=limitations, historical_summary=history,
    )
