"""Smoke HTTP da golden persona; sem credenciais ou dados financeiros em logs.

Cloud Run privado: use `gcloud run services proxy` e informe a URL localhost.
O script nunca recebe token na CLI, lê ADC ou muda a configuração do servidor.
"""

import argparse
import json
import sys
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


GOLDEN_USER_ID = "6491f4a4-67dc-49de-a38a-cf655ff77c33"
REFERENCE_DATE = "2025-09-30"
INITIAL_MESSAGE = "Quero comprar um iPhone de R$ 10.000. Faz sentido agora?"


class SmokeFailure(RuntimeError):
    """A fixed diagnostic label, never an upstream response body."""


def require(condition, label):
    if not condition:
        raise SmokeFailure(label)


def check_chat(body, expect_agent, expect_data):
    runtime = body["runtime"]
    analysis = body["golden_analysis"]
    decision = body["decision"]
    require(runtime["agent"] == expect_agent, "agent_provider_mismatch")
    require(runtime["data"] == expect_data, "data_provider_mismatch")
    require(bool(runtime.get("model")) if expect_agent == "gemini" else True, "gemini_model_missing")
    expected_origin = "dataset_observed" if expect_data == "bigquery" else "user_supplied_hackathon_snapshot"
    require(analysis["data_source"] == expected_origin, "source_origin_mismatch")
    require(analysis["reference_date"] == decision["as_of_date"] == REFERENCE_DATE, "reference_date_mismatch")
    require(decision["data_mode"] == "event_dataset_demo", "legacy_data_mode_mismatch")
    require(GOLDEN_USER_ID not in json.dumps(body), "identity_exposed")
    require(body["accompaniment_enabled"] is False, "automatic_accompaniment")
    require(bool(body["message"]), "empty_message")
    return analysis


def check_quote(analysis, amounts):
    require(analysis["installments_cents"] == amounts, "installment_quote_mismatch")
    require(analysis["salary_observed_cents"] == 675499, "salary_mismatch")
    require(analysis["recent_average_margin_cents"] == 20377, "recent_mean_mismatch")
    require(analysis["six_month_average_margin_cents"] == -34516, "six_month_mean_mismatch")
    require(analysis["last_month_margin_cents"] == -57685, "september_margin_mismatch")
    require(analysis["observed_installments_total_cents"] == 69078, "observed_installments_mismatch")
    november = next(row for row in analysis["comparisons"] if row["month"] == "2025-11-01")
    require(november["benchmark_margin_cents"] == 11393, "september_anchored_comparison_mismatch")
    require(november["margin_after_installment_min_cents"] == 11393 - max(amounts), "comparison_quote_mismatch")


def run_journey(request, *, expect_agent, expect_data, observe=lambda row: None):
    """Exercise HTTP or TestClient through an injected request callable."""
    require(request("/health") == {"status": "ok"}, "health_contract_mismatch")
    require(b"swagger" in request("/docs", raw=True).lower(), "docs_missing")
    observations = []

    def turn(step, message, previous=None):
        body = request("/api/chat", {"message": message, "decision": previous})
        analysis = check_chat(body, expect_agent, expect_data)
        observations.append({"step": step, "agent": body["runtime"]["agent"],
                             "model": body["runtime"].get("model"), "data": body["runtime"]["data"],
                             "source": analysis["data_source"], "state": body["decision"]["state"]})
        return body

    first = turn("initial", INITIAL_MESSAGE)
    require(first["draft"]["total_price_cents"] == 1000000, "price_extraction_mismatch")
    require(first["decision"]["state"] == "needs_input", "payment_clarification_missing")
    require(not first["golden_analysis"]["installments_cents"], "invented_payment_terms")
    require("à vista" in first["message"] and "parcelar" in first["message"], "payment_question_missing")

    ten = turn("ten_installments", "10 vezes sem juros", first["draft"])
    check_quote(ten["golden_analysis"], [100000] * 10)
    require(ten["draft"]["first_due_date"] is None and not ten["decision"]["scenarios"], "invented_due_date")
    require("volátil" in ten["message"] and "garantia" in ten["message"], "uncertainty_missing")

    work = turn("work_need", "Mas eu preciso dele agora porque trabalho com marketing.", ten["draft"])
    require("trabalho" in work["message"] and "entrada" in work["message"], "work_need_not_acknowledged")
    upfront = turn("upfront", "Consigo dar R$2.000 de entrada.", work["draft"])
    require(upfront["draft"]["upfront_cents"] == 200000, "upfront_mismatch")
    check_quote(upfront["golden_analysis"], [80000] * 10)

    twelve = turn("twelve_installments", "Em 12 vezes sem juros.", upfront["draft"])
    check_quote(twelve["golden_analysis"], [66667] * 8 + [66666] * 4)
    require(sum(twelve["golden_analysis"]["installments_cents"]) + 200000 == 1000000, "cent_conservation_failed")
    later = turn("wait_november", "E se eu esperar até novembro?", twelve["draft"])
    require(later["draft"]["purchase_month"] == "2025-11-01", "purchase_month_mismatch")
    require(later["golden_analysis"]["selected_conditional_release_cents"] == 69078, "waiting_not_recalculated")
    require(ten["golden_analysis"]["selected_conditional_release_cents"] == 0, "initial_release_invented")
    agency = turn("human_agency", "Quero comprar mesmo assim.", later["draft"])
    require(agency["decision"]["state"] != "blocked" and "decisão é sua" in agency["message"], "agency_not_preserved")
    require(not any(word in agency["message"].casefold() for word in
                    ("irresponsável", "gastou errado", "não deveria comprar", "aprender a controlar")), "moralizing_language")

    dated = turn("dated_schedule", "Primeira em 2025-11-10.", agency["draft"])
    scenario = dated["decision"]["scenarios"][0]
    require(scenario["schedule"][0]["due_date"] == "2025-11-10", "first_charge_mismatch")
    require(sum(row["amount_cents"] for row in scenario["schedule"]) + scenario["upfront_cents"] == 1000000, "schedule_conservation_failed")
    require(scenario["projection"]["min_balance_cents"] is None, "unknown_balance_became_number")

    off = request("/api/accompaniment/review", {})
    require(off == {"reviewed": False, "reason": "opted_out", "decision": None}, "opt_out_failed")
    event = {"consent_enabled": True, "plan_snapshot": {"decision": dated["draft"]},
             "event": {"event_id": "golden-smoke-1", "kind": "demo_purchase_posted", "offer_ref": "golden-extra-1000"}}
    reviewed = request("/api/accompaniment/review", event)
    require(reviewed["reviewed"] is True and reviewed["reason"] == "reviewed", "supervisor_not_reviewed")
    require("SIMULADO" in reviewed["decision"]["message"] and "1.000,00" in reviewed["decision"]["message"], "event_label_missing")
    require("uma vez" in reviewed["decision"]["message"], "event_single_charge_missing")
    require(reviewed["decision"]["scenarios"][0]["total_price_cents"] == 1000000, "event_changed_plan_price")
    replayed = request("/api/accompaniment/review", event)
    require(reviewed["decision"]["scenarios"] == replayed["decision"]["scenarios"], "event_replay_accumulated")
    observations.append({"step": "supervisor", "opt_out": off["reason"], "reviewed": True, "simulated": True, "replay_stable": True})
    for observation in observations:
        observe({**observation, "result": "PASS"})
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--expect-agent", required=True, choices=("demo", "gemini"))
    parser.add_argument("--expect-data", required=True, choices=("golden_fixture", "bigquery"))
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlsplit(base)
    if (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment):
        parser.error("Use apenas uma origem HTTP(S), sem credencial, caminho, query ou fragmento.")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("HTTP somente em localhost; serviço remoto exige HTTPS.")

    def request(path, body=None, *, raw=False):
        started = perf_counter()
        req = Request(base + path, data=None if body is None else json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=120) as response:
                content, status = response.read(), response.status
        except HTTPError as exc:
            print(json.dumps({"endpoint": path, "status": exc.code, "result": "FAIL"}))
            raise SmokeFailure("http_failure") from None
        except (URLError, TimeoutError):
            raise SmokeFailure("endpoint_unavailable") from None
        print(json.dumps({"endpoint": path, "status": status, "duration_ms": round((perf_counter() - started) * 1000, 2)}))
        return content if raw else json.loads(content)

    try:
        steps = run_journey(request, expect_agent=args.expect_agent, expect_data=args.expect_data,
                            observe=lambda row: print(json.dumps(row, ensure_ascii=False)))
        print(json.dumps({"result": "PASS", "verified_steps": len(steps), "agent": args.expect_agent,
                          "data": args.expect_data, "live_data": args.expect_data == "bigquery"}))
        return 0
    except (SmokeFailure, ValueError, KeyError, IndexError, TypeError, StopIteration) as exc:
        print(json.dumps({"result": "FAIL", "reason": str(exc) if isinstance(exc, SmokeFailure) else type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
