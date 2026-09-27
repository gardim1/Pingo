import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.api.main import app


CLIENT = TestClient(app)
SCHEMA = json.loads((Path(__file__).parents[1] / "contracts" / "decision-response.schema.json").read_text(encoding="utf-8"))


def decision_payload(**overrides):
    payload = {
        "message": "Quero planejar esta compra.",
        "persona_key": "persona-a",
        "decision": {
            "label": "Celular fictício",
            "total_price_cents": 1000000,
            "upfront_cents": 0,
            "installment_count": 10,
            "first_due_date": "2026-10-01",
        },
    }
    payload.update(overrides)
    return payload


def test_health_and_docs_are_available_without_demo(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    assert CLIENT.get("/health").json() == {"status": "ok"}
    assert CLIENT.get("/docs").status_code == 200


def test_real_mode_never_silently_uses_fixture(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    response = CLIENT.post("/api/decision", json=decision_payload())
    assert response.status_code == 503
    assert "integration" in response.json()["detail"]


def test_demo_decision_matches_shared_schema_and_fixture_math(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    response = CLIENT.post("/api/decision", json=decision_payload())
    assert response.status_code == 200
    body = response.json()
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(body)
    assert body["data_mode"] == "own_synthetic_demo"
    assert body["state"] == "ready"
    assert body["scenarios"][0]["projection"]["min_balance_cents"] == -20000
    assert body["scenarios"][0]["remaining_after_window_cents"] == 700000
    assert sum(item["amount_cents"] for item in body["scenarios"][0]["schedule"]) == 1000000


def test_incomplete_terms_ask_instead_of_approving(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    payload = decision_payload()
    del payload["decision"]["first_due_date"]
    response = CLIENT.post("/api/decision", json=payload)
    assert response.status_code == 200
    body = response.json()
    Draft202012Validator(SCHEMA, format_checker=FormatChecker()).validate(body)
    assert body["state"] == "needs_input"
    assert body["question"]["field"] == "first_due_date"
    assert body["scenarios"] == []


def test_changed_price_recalculates_instead_of_reusing_old_schedule(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    changed = decision_payload()
    changed["decision"]["total_price_cents"] = 900000
    body = CLIENT.post("/api/decision", json=changed).json()
    assert sum(item["amount_cents"] for item in body["scenarios"][0]["schedule"]) == 900000
    assert body["scenarios"][0]["projection"]["min_balance_cents"] == -10000


def test_missing_confirmed_balance_stays_unknown_even_with_fixture(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    payload = decision_payload(confirmed_context={"as_of_date": "2026-09-26", "scheduled_cashflows": []})
    body = CLIENT.post("/api/decision", json=payload).json()
    assert body["state"] == "limited"
    assert body["scenarios"][0]["projection"] == {
        "mode": "unavailable", "through_date": None,
        "min_balance_cents": None, "assessment": "insufficient_data",
    }


def test_duplicate_confirmed_cashflow_refs_are_rejected(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    payload = decision_payload(confirmed_context={
        "as_of_date": "2026-09-26",
        "scheduled_cashflows": [
            {"ref": "rent-1", "date": "2026-10-01", "amount_cents": 100, "direction": "outflow"},
            {"ref": "rent-1", "date": "2026-11-01", "amount_cents": 100, "direction": "outflow"},
        ],
    })
    assert CLIENT.post("/api/decision", json=payload).status_code == 422


def test_unknown_persona_is_rejected_before_calculation(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    assert CLIENT.post("/api/decision", json=decision_payload(persona_key="other-client")).status_code == 403


def test_explicit_can_wait_compares_later_first_charge_as_hypothesis(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    body = CLIENT.post("/api/decision", json=decision_payload(
        preferences={"can_wait": True, "purpose": "trabalho", "protected_items": ["aluguel"]}
    )).json()
    assert len(body["scenarios"]) == 2
    assert body["scenarios"][1]["schedule"][0]["due_date"] == "2026-11-01"
    assert body["scenarios"][1]["projection"]["min_balance_cents"] == 80000
    assert body["scenarios"][1]["remaining_after_window_cents"] == 800000
    assert any("hipótese" in item.lower() for item in body["assumptions"])


def test_review_uses_new_terms_and_ignores_client_calculation(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    changed = decision_payload()
    changed["decision"]["total_price_cents"] = 900000
    changed["plan_snapshot"] = {
        "decision": {**decision_payload()["decision"], "total_price_cents": 1000000},
        "preferences": {"can_wait": False},
        "saved_as_of_date": "2025-01-01",
        "calculated_balance_cents": 99999999,
    }
    body = CLIENT.post("/api/decision/review", json=changed).json()
    assert body["scenarios"][0]["total_price_cents"] == 900000
    assert body["as_of_date"] == "2026-09-26"


def test_money_requires_integer_cents_not_boolean_or_decimal(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    for invalid in (True, 100.0):
        payload = decision_payload()
        payload["decision"]["total_price_cents"] = invalid
        assert CLIENT.post("/api/decision", json=payload).status_code == 422


def test_confirmed_negative_balance_is_known_and_not_replaced_with_zero(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    payload = decision_payload(confirmed_context={
        "as_of_date": "2026-09-26", "available_balance_cents": -1000,
        "protected_buffer_cents": 0, "scheduled_cashflows": [],
    })
    body = CLIENT.post("/api/decision", json=payload).json()
    assert body["scenarios"][0]["projection"]["mode"] == "scenario_with_assumptions"
    assert body["scenarios"][0]["projection"]["min_balance_cents"] == -301000
