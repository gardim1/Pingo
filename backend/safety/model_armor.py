"""Regional Model Armor REST integration, using ADC and no hidden fallback."""

import re

from backend.safety.local import LocalSafetyProvider
from backend.safety.types import OutputContext, SafetyAction, SafetyResult


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


class ModelArmorSafetyProvider:
    name = "model_armor"

    def __init__(self, template_name: str, *, enforcement: str = "INSPECT_ONLY",
                 timeout_seconds: float = 5, session=None):
        match = re.fullmatch(
            r"projects/([a-z][a-z0-9-]{0,62}|[0-9]+)/locations/([a-z]+(?:-[a-z]+)*[0-9]?)/templates/([a-zA-Z0-9_-]{1,128})",
            template_name,
        )
        if match is None:
            raise ValueError("Invalid Model Armor template resource name")
        if enforcement not in {"INSPECT_ONLY", "INSPECT_AND_BLOCK"}:
            raise ValueError("Invalid Model Armor enforcement mode")
        if isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 30:
            raise ValueError("Model Armor timeout must be between zero and thirty seconds")
        self.endpoint = f"https://modelarmor.{match.group(2)}.rep.googleapis.com/v1/{template_name}"
        self.enforcement = enforcement
        self.timeout_seconds = timeout_seconds
        self._session = session
        self._local = LocalSafetyProvider()

    def inspect_input(self, text: str) -> SafetyResult:
        local = self._local.inspect_input(text)
        if local.action != SafetyAction.ALLOW:
            return local
        return self._inspect(text, "sanitizeUserPrompt", "userPromptData")

    def inspect_output(self, text: str, context: OutputContext | None = None) -> SafetyResult:
        local = self._local.inspect_output(text, context)
        if local.action != SafetyAction.ALLOW:
            return local
        return self._inspect(text, "sanitizeModelResponse", "modelResponseData")

    def _error(self, reason):
        return SafetyResult(SafetyAction.ERROR, reason, self.name,
                            "A verificação de segurança está indisponível. Tente novamente.")

    def _inspect(self, text, operation, data_field):
        try:
            if self._session is None:
                import google.auth
                from google.auth.transport.requests import AuthorizedSession
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                self._session = AuthorizedSession(credentials)
            response = self._session.post(
                f"{self.endpoint}:{operation}",
                json={data_field: {"text": text}, "multiLanguageDetectionMetadata": {
                    "enableMultiLanguageDetection": True, "sourceLanguage": "pt",
                }}, timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                return self._error("model_armor_http_error")
            body = response.json()
            result = body.get("sanitizationResult", {})
            if result.get("invocationResult") != "SUCCESS":
                return self._error("model_armor_incomplete_inspection")
            match = result.get("filterMatchState")
            if match not in {"MATCH_FOUND", "NO_MATCH_FOUND"}:
                return self._error("model_armor_invalid_response")
            filters = result.get("filterResults")
            if not isinstance(filters, dict) or not filters:
                return self._error("model_armor_missing_filter_results")
            for name, result_type in (("rai", "raiFilterResult"),
                                      ("pi_and_jailbreak", "piAndJailbreakFilterResult")):
                detail = filters.get(name, {}).get(result_type, {})
                if detail.get("executionState") != "EXECUTION_SUCCESS":
                    return self._error("model_armor_missing_required_filter")
            findings = []
            for filter_name, filter_result in filters.items():
                if not isinstance(filter_result, dict):
                    return self._error("model_armor_invalid_response")
                for detail in _objects(filter_result):
                    if detail.get("executionState") not in {None, "EXECUTION_SUCCESS"}:
                        return self._error("model_armor_incomplete_inspection")
                    if detail.get("matchState") == "MATCH_FOUND":
                        # Codes only, never findings containing inspected data.
                        known = {"rai", "pi_and_jailbreak", "sdp", "malicious_uris", "csam"}
                        name = filter_name if filter_name in known else "configured_filter"
                        if name not in findings:
                            findings.append(name)
            if match == "MATCH_FOUND":
                if self.enforcement == "INSPECT_AND_BLOCK":
                    return SafetyResult(SafetyAction.BLOCK, "model_armor_match", self.name,
                                        "Não posso processar esse conteúdo. Reformule o pedido de planejamento.",
                                        tuple(findings) or ("configured_filter",))
                return SafetyResult(SafetyAction.ALLOW, "model_armor_inspect_only_match", self.name,
                                    findings=tuple(findings) or ("configured_filter",))
            return SafetyResult(SafetyAction.ALLOW, "model_armor_checks_passed", self.name)
        except Exception:
            # Never return error strings: transport/Google errors may include
            # headers, payload fragments or credential paths.
            return self._error("model_armor_unavailable")
