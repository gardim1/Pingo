"""Deterministic defense in depth, not a claim of complete attack detection.

Free-form financial prose is not validated through numeric allowlists: a value
could belong to the engine while being attached to the wrong concept. The HTTP
boundary should render approved templates and supply their expected text.
"""

import re
import unicodedata

from backend.safety.types import OutputContext, SafetyAction, SafetyResult


POLICY_VERSION = "pingo-local-v2"
MAX_TEXT_CHARS = 24000


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c)
                   and unicodedata.category(c) != "Cf").casefold()


INPUT_RULES = (
    ("prompt_injection", r"\b(ignore|ignora|ignore|desconsidere|esqueca|forget|disregard)\b.{0,90}\b(instrucoes|instructions|regras|rules|system|sistema)\b"),
    ("jailbreak", r"\b(modo desenvolvedor|developer mode|jailbreak|sem restricoes|unrestricted assistant|sem filtros)\b"),
    ("secret_request", r"\b(revel\w*|mostr\w*|exib\w*|imprim\w*|leia|ler|reveal|print|show|exfiltrat\w*)\b.{0,100}\b(segred\w*|secret\w*|credencia\w*|credentials|api[ _-]?key|chave\w*|token\w*|system prompt|prompt do sistema|\.env)\b"),
    ("cross_user_access", r"\b(outro[as]?|outra[as]?|todos[oa]s|other|another|all)\s+(cliente\w*|usuario\w*|pessoa\w*|customer\w*|user\w*)\b"),
    ("identity_override", r"\b(user_id|customer_id|session_id|client_id)\b\s*(?:[:=]|e\b)"),
    ("arbitrary_sql", r"\b(select\s+.{0,300}\s+from|drop\s+table|delete\s+from|insert\s+into|update\s+\w+\s+set|union\s+select|execute\s+immediate)\b"),
    ("arbitrary_sql", r"\b(execut\w*|rod\w*|alter\w*)\b.{0,60}\b(sql|query|consulta arbitraria)\b"),
    ("unauthorized_tool", r"\b(execut\w*|rod\w*|run|call|use)\b.{0,60}\b(shell|bash|powershell|terminal|os\.system|subprocess|ferramenta nao autorizada)\b"),
)

SECRET_PATTERNS = (
    r"-----begin [a-z ]*private key-----",
    r"\bbearer\s+[a-z0-9._~+/-]{12,}",
    r"\baiza[a-z0-9_-]{20,}",
    r"\b(api[ _-]?key|access_token|refresh_token|client_secret|private_key)\s*[:=]\s*\S+",
    r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
)

UNSAFE_OUTPUT_PATTERNS = (
    r"\b(mulher\w*|homen\w*|negro\w*|idoso\w*)\b.{0,40}\b(incapaz|inferior\w*|nao (podem|pode|consegue\w*) (ser |liderar|trabalhar))",
    r"\b(irresponsavel|burro|idiota|se envergonh\w*)\b",
    r"\b(compra aprovada|renda garantida|sem risco|viabilidade garantida)\b",
    r"\bitau\b.{0,70}\b(afirma|garante|recomenda|oferece|aprova|defende|acredita|assegura|declara)\b",
    r"\b(segundo|politica\w* d[oa]|posicao d[oa])\s+itau\b",
)


class LocalSafetyProvider:
    name = "local"

    def _result(self, action, reason, message=None):
        return SafetyResult(action, reason, self.name, message)

    def inspect_input(self, text: str) -> SafetyResult:
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
            return self._result(SafetyAction.BLOCK, "invalid_input", "Envie uma mensagem curta sobre seu planejamento.")
        normalized = _normalize(text)
        for reason, pattern in INPUT_RULES:
            if re.search(pattern, normalized, flags=re.DOTALL):
                return self._result(SafetyAction.BLOCK, reason,
                                    "Posso ajudar no planejamento com os dados autorizados desta sessão.")
        if any(re.search(pattern, normalized) for pattern in SECRET_PATTERNS):
            return self._result(SafetyAction.BLOCK, "sensitive_input", "Não envie senhas, chaves ou documentos pessoais no chat.")
        if re.search(r"\bmulher\w*\b.{0,50}\b(ceo|lider\w*|diretora|presidente)\b", normalized):
            return self._result(SafetyAction.REDIRECT, "respectful_general_answer",
                                "Sim. Gênero não determina capacidade de liderança. Posso ajudar você a planejar seu objetivo financeiro.")
        if re.search(r"\b(escrev\w*|cri\w*|program\w*|write)\b.{0,50}\b(python|codigo|code|javascript)\b", normalized):
            return self._result(SafetyAction.REDIRECT, "outside_scope",
                                "Meu foco aqui é planejamento financeiro. Posso ajudar a comparar condições de uma compra.")
        return self._result(SafetyAction.ALLOW, "local_checks_passed")

    def inspect_output(self, text: str, context: OutputContext | None = None) -> SafetyResult:
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
            return self._result(SafetyAction.BLOCK, "invalid_output")
        normalized = _normalize(text)
        if any(re.search(pattern, normalized) for pattern in SECRET_PATTERNS):
            return self._result(SafetyAction.BLOCK, "sensitive_output")
        if any(re.search(pattern, normalized) for pattern in UNSAFE_OUTPUT_PATTERNS):
            return self._result(SafetyAction.BLOCK, "unsafe_or_unsupported_claim")
        if context is not None and context.trusted_text is not None:
            if text != context.trusted_text:
                return self._result(SafetyAction.BLOCK, "engine_template_mismatch")
            return self._result(SafetyAction.ALLOW, "verified_backend_template")
        # Numeric words evade a digit-only check. Free financial claims require
        # backend provenance even when they do not contain an Arabic numeral.
        if re.search(r"\d|r\$|\b(reais|real|centavos|parcelas?|saldo|juros|desconto|viavel|viabilidade)\b", normalized):
            return self._result(SafetyAction.BLOCK, "unsupported_financial_output")
        # Regex cannot establish semantic truth, absence of bias or whether a
        # claim agrees with an engine. Free model prose never reaches the UI.
        return self._result(SafetyAction.BLOCK, "unverified_output")
