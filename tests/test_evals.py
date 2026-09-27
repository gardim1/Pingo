"""The report runner must execute cases and preserve failure evidence."""

from scripts.evaluate import EvaluationCase, Observation, render_report, run_cases


def test_report_does_not_mark_unexecuted_or_failed_cases_as_pass():
    calls = []

    def success():
        calls.append("executed")
        return Observation(True, {"status": 200})

    def failure():
        return Observation(False, {"status": 503})

    def crashed():
        raise RuntimeError("sensitive provider payload must not be printed")

    cases = [
        EvaluationCase("ok", "Works", "MOCK/DEMO", "HTTP 200", success),
        EvaluationCase("bad", "Fails", "FAULT INJECTION", "HTTP 200", failure),
        EvaluationCase("error", "Crashes", "FAULT INJECTION", "HTTP 200", crashed),
    ]
    results = run_cases(cases)
    assert calls == ["executed"]
    assert [result.status for result in results] == ["PASS", "FAIL", "FAIL"]
    assert results[2].observed == {"error_type": "RuntimeError"}
    rendered = render_report(results)
    assert "1 PASS / 2 FAIL" in rendered
    assert "sensitive provider payload" not in rendered


def test_empty_harness_does_not_claim_a_successful_evaluation():
    report = render_report(run_cases([]))
    assert "0 PASS / 0 FAIL" in report
    assert "Nenhum caso executado" in report
