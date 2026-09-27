"""Own synthetic aggregates only; these tests never query customer data."""

import json
from datetime import date

import pytest

from backend.data.bigquery_context import (
    BigQueryContextProvider, DataAccessDenied, DataProviderError,
)


REFERENCE_DATE = date(2026, 9, 26)
AUTHORIZED_USERS = {"event-persona": "synthetic-test-id"}


def summary_payload():
    return {
        "coverage_start": "2025-01-01", "coverage_end": "2025-12-31",
        "row_count": 12, "invalid_rows": 0,
        "monthly": [{
            "month": "2025-01-01", "entry_count": 2, "exit_count": 10,
            "entry_units": "5000.10", "exit_units": "4000.20",
            "invoice_payment_units": "1000.20", "transfer_exit_units": "200.00",
        }],
        "categories": [{"category": "Casa", "direction": "S",
                        "count": 6, "amount_units": "1500.10"}],
        "recurrence_candidates": [{
            "category": "Casa", "months_observed": 6, "consecutive_pairs": 5,
            "min_units": "250.00", "max_units": "260.00",
            "last_observed_date": "2025-12-10",
        }],
        "observed_installments": [{
            "category": "Lojas e sites", "count": 3,
            "first_observed_date": "2025-01-10", "last_observed_date": "2025-03-10",
            "min_installment_index": 1, "max_installment_index": 3,
            "max_installment_total": 12, "observed_units": "300.01",
        }],
    }


class FakeJob:
    def __init__(self, payload=None, *, estimate=1000, error=None):
        self.payload = payload
        self.total_bytes_processed = estimate
        self.error = error
        self.cancelled = False
        self.result_kwargs = None

    def result(self, **kwargs):
        self.result_kwargs = kwargs
        if self.error:
            raise self.error
        return [{"summary_json": json.dumps(self.payload)}]

    def cancel(self, **kwargs):
        self.cancelled = True
        return True


class FakeBigQueryClient:
    def __init__(self, payload=None, *, estimate=1000, error=None):
        self.calls = []
        self.dry_job = FakeJob(estimate=estimate)
        self.data_job = FakeJob(payload if payload is not None else summary_payload(), error=error)

    def query(self, query, **kwargs):
        self.calls.append((query, kwargs))
        return self.dry_job if kwargs["job_config"].dry_run else self.data_job


@pytest.fixture
def provider():
    client = FakeBigQueryClient()
    return BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                  reference_date=REFERENCE_DATE, client=client), client


def test_historical_data_never_becomes_current_balance_or_future_schedule(provider):
    adapter, _ = provider
    context = adapter.get_context("event-persona")
    assert context.available_balance_cents is None
    assert context.protected_buffer_cents is None
    assert context.scheduled_cashflows == []
    assert context.as_of_date == REFERENCE_DATE
    history = context.historical_summary
    assert history["source"] == "batalha-time-08-g7ha.hackathon_dados.extrato_sintetico"
    assert history["coverage"] == {"start": "2025-01-01", "end": "2025-12-31"}
    assert history["currency"] is None
    assert history["observed_facts"]["monthly"][0]["entry_units"] == "5000.10"
    assert history["recurrence_candidates"][0]["requires_confirmation"] is True
    assert history["observed_installments"][0]["future_schedule_known"] is False
    assert "synthetic-test-id" not in json.dumps(history)
    assert all(e.origin in {"dataset_observed", "derived"} for e in context.evidence)


def test_fixed_query_is_parametrized_dry_run_first_and_bounded(provider):
    adapter, client = provider
    adapter.get_context("event-persona")
    assert len(client.calls) == 2
    query, first = client.calls[0]
    _, second = client.calls[1]
    assert "id_usuario = @user_id" in query
    assert "synthetic-test-id" not in query
    assert "DATE(anomesdia) <= @reference_date" in query
    assert first["job_config"].dry_run is True
    assert second["job_config"].dry_run is False
    for call in (first, second):
        assert call["job_config"].use_legacy_sql is False
        assert call["job_config"].maximum_bytes_billed == 1073741824
        assert int(call["job_config"].job_timeout_ms) == 20000
        assert call["location"] == "us-central1"
        assert call["timeout"] == 20.0
        params = {p.name: p.value for p in call["job_config"].query_parameters}
        assert params["user_id"] == "synthetic-test-id"
        assert params["reference_date"] == REFERENCE_DATE
    assert client.data_job.result_kwargs["max_results"] == 1
    assert client.data_job.result_kwargs["timeout"] == 20.0


@pytest.mark.parametrize("identity", ["other-client", "' OR 1=1 --", "event-persona; DROP TABLE x"])
def test_unauthorized_and_sql_injection_identities_never_reach_query(provider, identity):
    adapter, client = provider
    with pytest.raises(DataAccessDenied):
        adapter.get_context(identity)
    with pytest.raises(DataAccessDenied):
        adapter.get_financial_context(identity, REFERENCE_DATE)
    assert client.calls == []


def test_over_budget_dry_run_prevents_data_query():
    client = FakeBigQueryClient(estimate=1073741825)
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS, client=client)
    with pytest.raises(DataProviderError) as raised:
        adapter.get_context("event-persona")
    assert raised.value.code == "bigquery_budget_exceeded"
    assert len(client.calls) == 1


def test_bigquery_timeout_is_explicit_sanitized_and_cancelled():
    client = FakeBigQueryClient(error=TimeoutError("sensitive raw id/token"))
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS, client=client)
    with pytest.raises(DataProviderError) as raised:
        adapter.get_context("event-persona")
    assert raised.value.code == "bigquery_unavailable"
    assert "sensitive" not in str(raised.value)
    assert client.data_job.cancelled is True


def test_bigquery_permission_failure_is_not_replaced_by_fixture():
    client = FakeBigQueryClient(error=PermissionError("raw provider message"))
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS, client=client)
    with pytest.raises(DataProviderError, match="indisponível"):
        adapter.get_context("event-persona")


def test_empty_history_does_not_fabricate_coverage():
    payload = {"coverage_start": None, "coverage_end": None, "row_count": 0,
               "invalid_rows": 0, "monthly": [], "categories": [],
               "recurrence_candidates": [], "observed_installments": []}
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                     client=FakeBigQueryClient(payload))
    context = adapter.get_context("event-persona")
    assert context.historical_summary["coverage"] == {"start": None, "end": None}
    assert context.available_balance_cents is None
    assert context.scheduled_cashflows == []
    assert any("Nenhum" in note for note in context.assumptions)


@pytest.mark.parametrize("change", [
    {"invalid_rows": 1}, {"coverage_end": "2026-01-01"},
    {"row_count": -1}, {"unexpected_secret": "never emit"},
])
def test_malformed_aggregates_are_rejected(change):
    payload = {**summary_payload(), **change}
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                     client=FakeBigQueryClient(payload))
    with pytest.raises(DataProviderError) as raised:
        adapter.get_context("event-persona")
    assert raised.value.code == "bigquery_invalid_result"


def test_invoice_and_transfer_totals_are_separate_observations_not_net_cash(provider):
    adapter, _ = provider
    context = adapter.get_context("event-persona")
    month = context.historical_summary["observed_facts"]["monthly"][0]
    assert month["invoice_payment_units"] == "1000.20"
    assert month["transfer_exit_units"] == "200.00"
    assert "net_balance" not in month
    assert context.scheduled_cashflows == []
    assert any("fatura" in text.lower() and "concilia" in text.lower()
               for text in context.historical_summary["limitations"])


def test_returned_arrays_cannot_exceed_sql_limits():
    payload = summary_payload()
    payload["monthly"] *= 13
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                     client=FakeBigQueryClient(payload))
    with pytest.raises(DataProviderError):
        adapter.get_context("event-persona")


def test_reference_date_is_backend_controlled_and_never_exposes_later_history():
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                     reference_date=date(2025, 6, 30),
                                     client=FakeBigQueryClient())
    with pytest.raises(DataProviderError) as raised:
        adapter.get_context("event-persona")
    assert raised.value.code == "bigquery_invalid_result"


def test_invalid_configuration_fails_before_external_access():
    with pytest.raises(ValueError):
        BigQueryContextProvider(authorized_users={})
    with pytest.raises(ValueError):
        BigQueryContextProvider(authorized_users=AUTHORIZED_USERS, project_id="other-project")
    with pytest.raises(ValueError):
        BigQueryContextProvider(authorized_users=AUTHORIZED_USERS, maximum_bytes_billed=1073741825)
