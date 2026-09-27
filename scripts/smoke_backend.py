"""HTTP smoke using own synthetic inputs; prints only result/status metadata.

For private Cloud Run use `gcloud run services proxy` and target its localhost URL.
The script never accepts a token on the command line or reads credentials.
"""

import argparse
import copy
from datetime import date, timedelta
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--persona", default="persona-a", help="Backend-approved public alias, never a dataset ID")
    parser.add_argument("--chat", action="store_true", help="Also verify the configured agent via /api/chat")
    parser.add_argument("--expect-agent", choices=("demo", "gemini"))
    parser.add_argument("--expect-data", choices=("own_synthetic_demo", "event_dataset_demo"))
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urlsplit(base)
    if (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path):
        parser.error("Use only an HTTP(S) origin without credentials, path or query.")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        parser.error("HTTP is permitted only on localhost; use HTTPS for remote services.")
    if args.expect_agent and not args.chat:
        parser.error("--expect-agent requires --chat")

    def request(path: str, body=None, *, raw=False):
        started = time.monotonic()
        req = Request(base + path, data=None if body is None else json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=120) as response:
                content = response.read()
                status = response.status
        except HTTPError as exc:
            print(json.dumps({"endpoint": path, "status": exc.code, "result": "FAIL"}))
            raise RuntimeError("HTTP failure; inspect sanitized backend logs.") from None
        except (URLError, TimeoutError):
            raise RuntimeError("Endpoint unavailable or timed out.") from None
        print(json.dumps({"endpoint": path, "status": status,
                          "duration_ms": round((time.monotonic() - started) * 1000)}))
        return content if raw else json.loads(content)

    try:
        assert request("/health") == {"status": "ok"}, "Health contract mismatch"
        assert b"swagger" in request("/docs", raw=True).lower(), "OpenAPI documentation unavailable"
        today = date.today()
        payload = {
            "message": "Quero comparar esta compra fictícia de celular nas condições informadas.",
            "persona_key": args.persona,
            "decision": {"label": "Celular fictício smoke", "total_price_cents": 1000000,
                         "upfront_cents": 0, "installment_count": 10,
                         "first_due_date": (today + timedelta(days=5)).isoformat()},
            "confirmed_context": {"as_of_date": today.isoformat(), "available_balance_cents": 2000000,
                                  "protected_buffer_cents": 100000, "scheduled_cashflows": []},
        }
        result = request("/api/decision", payload)
        assert result["contract_version"] == "1.0", "Contract version mismatch"
        assert result["state"] in {"ready", "limited"}, "Decision did not produce a scenario"
        if args.expect_data:
            assert result["data_mode"] == args.expect_data, "Unexpected data provider"
        assert sum(row["amount_cents"] for row in result["scenarios"][0]["schedule"]) == 1000000
        revised = copy.deepcopy(payload)
        revised["decision"]["total_price_cents"] = 900000
        reviewed = request("/api/decision/review", revised)
        assert sum(row["amount_cents"] for row in reviewed["scenarios"][0]["schedule"]) == 900000
        assert reviewed["scenarios"][0]["total_price_cents"] == 900000
        if args.chat:
            chat = request("/api/chat", payload)
            assert chat.get("message"), "Chat returned no safe message"
            runtime = chat["runtime"]
            if args.expect_agent:
                assert runtime["agent"] == args.expect_agent, "Unexpected agent provider"
            if args.expect_agent == "gemini":
                assert runtime["model"], "Gemini model absent from runtime evidence"
            print(json.dumps({"agent": runtime["agent"], "model": runtime.get("model"),
                              "data": runtime["data"], "safety": runtime["safety"]}))
        print(json.dumps({"result": "PASS", "inputs": "own_synthetic_confirmed_scenario"}))
        return 0
    except (AssertionError, RuntimeError, ValueError, KeyError, IndexError) as exc:
        print(json.dumps({"result": "FAIL", "reason": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
