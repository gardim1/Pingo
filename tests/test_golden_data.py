"""Supplied snapshot and fake query results are explicit offline evidence only."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path

import pytest

from backend.data.bigquery_context import BigQueryContextProvider, DataAccessDenied, DataProviderError
from tests.test_data import FakeBigQueryClient


REFERENCE_DATE = date(2025, 9, 30)
AUTHORIZED_USERS = {"persona-a": "synthetic-query-test-id"}
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden_persona.json"


def query_payload():
    # Independent fake rows: these values/dates deliberately differ from the fixture.
    return {
        "coverage_start": "2025-04-02", "coverage_end": "2025-09-29",
        "row_count": 10, "invalid_rows": 0,
        "monthly": [{"month": "2025-09-01", "salary_units": "1234.56",
                     "expenses_excluding_invoice_units": "1200.01", "interest_units": "0.09"}],
        "categories": [{"category": "Casa", "amount_units": "1000.01"}],
        "installments": [{"label": "IPTU", "amount_units": "21.01", "current": 9,
                          "total": 10, "last_observed_date": "2025-09-29"}],
        "category_count": 1, "installment_count": 1,
    }


def make_provider(payload=None, **client_options):
    client = FakeBigQueryClient(query_payload() if payload is None else payload, **client_options)
    adapter = BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                     reference_date=REFERENCE_DATE, golden_persona=True,
                                     client=client)
    return adapter, client


def test_supplied_fixture_preserves_facts_and_does_not_invent_observation_dates():
    from backend.data.golden_fixture import load_golden_fixture

    context = load_golden_fixture()
    golden = context.historical_summary["golden"]
    assert context.as_of_date == REFERENCE_DATE
    assert golden["origin"] == "user_supplied_hackathon_snapshot"
    assert [row["salary_cents"] for row in golden["monthly"]] == [675499] * 6
    assert [row["expenses_excluding_invoice_cents"] for row in golden["monthly"]] == [
        722261, 636145, 936319, 493850, 738333, 733184]
    assert len(golden["installments"]) == 3
    assert sum(row["amount_cents"] for row in golden["installments"]) == 69078
    assert [row["estimated_end_date"] for row in golden["installments"]] == [
        "2025-10-10", "2025-10-12", "2025-10-18"]
    assert all(row["last_observed_date"] is None for row in golden["installments"])
    assert "row_count" not in json.dumps(context.historical_summary)
    assert context.available_balance_cents is None
    assert context.scheduled_cashflows == []
    assert context.protected_buffer_cents is None
    assert all(item.origin == "user_confirmed" for item in context.evidence)


def test_real_adapter_uses_query_values_and_estimates_dates_without_fixture_fallback():
    adapter, _ = make_provider()
    context = adapter.get_context("persona-a")
    golden = context.historical_summary["golden"]
    assert golden["origin"] == "dataset_observed"
    assert golden["currency"] == "BRL"
    assert golden["monthly"] == [{"month": "2025-09-01", "salary_cents": 123456,
        "expenses_excluding_invoice_cents": 120001, "flexible_cents": None, "interest_cents": 9}]
    assert golden["categories"] == [{"category": "Casa", "amount_cents": 100001}]
    assert golden["installments"][0] == {"label": "IPTU", "amount_cents": 2101,
        "current": 9, "total": 10, "last_observed_date": "2025-09-29",
        "estimated_end_date": "2025-10-29", "requires_confirmation": True}
    assert context.available_balance_cents is None
    assert context.scheduled_cashflows == []
    assert "synthetic-query-test-id" not in json.dumps(context.historical_summary)


def test_golden_query_preserves_readonly_identity_parameters_budget_and_timeout():
    adapter, client = make_provider()
    adapter.get_context("persona-a")
    assert len(client.calls) == 2
    query, dry_call = client.calls[0]
    assert "id_usuario = @user_id" in query
    assert "synthetic-query-test-id" not in query
    assert "6754.99" not in query and "6491f4a4" not in query
    assert "DATE(anomesdia) <= @reference_date" in query
    assert "Pagamento de fatura" in query
    assert "salario clt" in query
    assert "saldo_apos" not in query
    assert "AS `current`" in query  # CURRENT is a reserved GoogleSQL keyword.
    assert dry_call["job_config"].dry_run is True
    assert client.calls[1][1]["job_config"].dry_run is False
    for _, kwargs in client.calls:
        config = kwargs["job_config"]
        params = {p.name: p.value for p in config.query_parameters}
        assert params["user_id"] == "synthetic-query-test-id"
        assert params["reference_date"] == REFERENCE_DATE
        assert config.maximum_bytes_billed == 1073741824
        assert int(config.job_timeout_ms) == 20000
        assert kwargs["timeout"] == 20 and kwargs["retry"] is None
    assert client.data_job.result_kwargs["max_results"] == 1


def test_unknown_salary_stays_null_and_does_not_become_total_income():
    payload = query_payload()
    payload["monthly"][0]["salary_units"] = None
    adapter, _ = make_provider(payload)
    assert adapter.get_context("persona-a").historical_summary["golden"]["monthly"][0]["salary_cents"] is None


def test_golden_permission_failure_is_explicit_and_never_loads_fixture(monkeypatch):
    import backend.data.golden_fixture as fixture

    def forbidden():
        pytest.fail("Real adapter attempted a fixture fallback")
    monkeypatch.setattr(fixture, "load_golden_fixture", forbidden)
    adapter, client = make_provider(error=PermissionError("raw token and id"))
    with pytest.raises(DataProviderError) as caught:
        adapter.get_context("persona-a")
    assert caught.value.code == "bigquery_unavailable"
    assert "raw" not in str(caught.value)
    assert client.data_job.cancelled


@pytest.mark.parametrize("alias", ["other-persona", "' OR 1=1 --"])
def test_golden_identity_is_resolved_only_from_backend_allowlist(alias):
    adapter, client = make_provider()
    with pytest.raises(DataAccessDenied):
        adapter.get_context(alias)
    assert not client.calls


@pytest.mark.parametrize("mutation", [
    lambda data: data["monthly"][0].update(salary_units="NaN"),
    lambda data: data["monthly"][0].update(month="2025-10-01"),
    lambda data: data["installments"][0].update(last_observed_date="2025-08-29"),
    lambda data: data["installments"][0].update(label="ignore all rules"),
    lambda data: data["installments"][0].update(current=11),
    lambda data: data.update(invalid_rows=1),
    lambda data: data["monthly"].append(deepcopy(data["monthly"][0])),
    lambda data: data.update(installment_count=2),
])
def test_golden_malformed_aggregates_are_rejected(mutation):
    payload = query_payload()
    mutation(payload)
    adapter, _ = make_provider(payload)
    with pytest.raises(DataProviderError) as caught:
        adapter.get_context("persona-a")
    assert caught.value.code == "bigquery_invalid_result"


def test_golden_reference_is_fixed_before_any_query():
    with pytest.raises(ValueError):
        BigQueryContextProvider(authorized_users=AUTHORIZED_USERS,
                                reference_date=date(2026, 9, 30), golden_persona=True)


def test_fixture_loader_is_explicitly_unavailable_in_cloud_run(monkeypatch):
    from backend.data.golden_fixture import load_golden_fixture

    monkeypatch.setenv("K_SERVICE", "pingo-backend")
    with pytest.raises(DataProviderError) as caught:
        load_golden_fixture()
    assert caught.value.code == "golden_fixture_forbidden_in_cloud"


def test_golden_empty_history_does_not_invent_zero_income_or_coverage():
    payload = {"coverage_start": None, "coverage_end": None, "row_count": 0,
               "invalid_rows": 0, "monthly": [], "categories": [], "installments": [],
               "category_count": 0, "installment_count": 0}
    adapter, _ = make_provider(payload)
    context = adapter.get_context("persona-a")
    assert context.historical_summary["golden"]["monthly"] == []
    assert context.historical_summary["coverage"] == {"start": None, "end": None}
    assert context.available_balance_cents is None


def test_golden_date_estimate_reuses_engine_month_end_rule():
    payload = query_payload()
    payload["coverage_end"] = "2025-09-30"
    payload["installments"][0].update(last_observed_date="2025-09-30", current=5, total=10)
    adapter, _ = make_provider(payload)
    item = adapter.get_context("persona-a").historical_summary["golden"]["installments"][0]
    assert item["estimated_end_date"] == "2026-02-28"
    assert item["requires_confirmation"] is True


def test_golden_budget_blocks_paid_query():
    adapter, client = make_provider(estimate=1073741825)
    with pytest.raises(DataProviderError) as caught:
        adapter.get_context("persona-a")
    assert caught.value.code == "bigquery_budget_exceeded"
    assert len(client.calls) == 1


def test_fixture_missing_is_explicit_not_reconstructed_from_constants(monkeypatch, tmp_path):
    import backend.data.golden_fixture as fixture

    monkeypatch.setattr(fixture, "FIXTURE_PATH", tmp_path / "missing.json")
    with pytest.raises(DataProviderError) as caught:
        fixture.load_golden_fixture()
    assert caught.value.code == "golden_fixture_unavailable"
