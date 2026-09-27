"""Request-scoped identity, authorized tools and safe rendering shared by routes."""
import json
import os
from dataclasses import replace
from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from backend.agent.intent import EmptyToolArgs
from backend.core.context_contract import FinancialContext
from backend.core.decision import decide, from_confirmed_context
from backend.core.demo_context import DEMO_PERSONAS, OwnSyntheticDemoProvider
from backend.models.decision import DecisionRequest, DecisionResponse
from backend.safety import LocalSafetyProvider, ModelArmorSafetyProvider, OutputContext, SafetyAction
from backend.api.golden_config import (golden_enabled, validate_golden_config,
    GOLDEN_ALIAS, GOLDEN_USER_ID, GOLDEN_REFERENCE_DATE)


def demo_mode() -> bool:
    return os.getenv('DEMO_MODE', '').lower() == 'true'


def error(code: str, status: int = 503):
    raise HTTPException(status_code=status, detail={'code': code, 'message': 'Não foi possível concluir esta etapa; nenhuma integração foi substituída por demo.'})


def data_provider_name() -> str:
    if golden_enabled():
        return os.getenv('DATA_PROVIDER', 'unconfigured')
    return 'event_dataset_demo' if os.getenv('DATA_PROVIDER') == 'bigquery' else 'own_synthetic_demo'


def authorize(persona_key: str | None) -> str:
    if golden_enabled():
        validate_golden_config()
        if persona_key not in (None, GOLDEN_ALIAS):
            error('identity_not_authorized', 403)
        return GOLDEN_ALIAS
    if os.getenv('DATA_PROVIDER') not in (None, '', 'demo', 'bigquery'):
        error('data_provider_not_allowed')
    if demo_mode() and os.getenv('DATA_PROVIDER') != 'bigquery':
        if persona_key not in DEMO_PERSONAS:
            raise HTTPException(403, 'Persona not authorized for demo')
        return persona_key
    if os.getenv('DATA_PROVIDER') != 'bigquery':
        raise HTTPException(503, 'Real data/model integration is not configured')
    # Private event demo: one profile bound by server configuration. Client/model
    # cannot switch this identity. Cloud Run invoker is the authentication boundary.
    bound = os.getenv('PINGO_BOUND_PERSONA', '')
    if not bound:
        error('server_identity_not_configured')
    if persona_key != bound:
        error('identity_not_authorized', 403)
    return bound


def get_safety_provider():
    provider = os.getenv('SAFETY_PROVIDER', 'local')
    if provider == 'local':
        return LocalSafetyProvider()
    if provider == 'model_armor':
        try:
            return ModelArmorSafetyProvider(os.getenv('MODEL_ARMOR_TEMPLATE',''),
                enforcement=os.getenv('MODEL_ARMOR_ENFORCEMENT','INSPECT_ONLY'))
        except (ValueError, RuntimeError):
            error('model_armor_not_configured')
    error('safety_provider_not_allowed')


def input_text(request: DecisionRequest) -> str:
    # All user-controlled text is inspected before any provider/tool, not just chat.
    parts = [request.message]
    if request.decision and request.decision.label:
        parts.append(request.decision.label)
    if request.preferences:
        parts.extend([request.preferences.purpose or '', *request.preferences.protected_items])
    if request.confirmed_context:
        parts.extend(i.ref for i in request.confirmed_context.scheduled_cashflows)
    return '\n'.join(parts)


def inspect_input(safety, request):
    result = safety.inspect_input(input_text(request))
    if result.action == SafetyAction.ERROR:
        error('safety_provider_error')
    return result


def blocked_response(message: str) -> DecisionResponse:
    return DecisionResponse(request_id=str(uuid4()),trace_id=str(uuid4()),
        data_mode='event_dataset_demo' if golden_enabled() or os.getenv('DATA_PROVIDER') == 'bigquery' else 'own_synthetic_demo',
        as_of_date=GOLDEN_REFERENCE_DATE if golden_enabled() else date.today(),state='blocked',message=message,question=None,
        scenarios=[],evidence=[],assumptions=[],actions=['update_inputs'])


def validate_output(safety, text: str):
    # Only call this with backend-rendered text; raw model prose is never rendered.
    result = safety.inspect_output(text, OutputContext(trusted_text=text))
    if result.action != SafetyAction.ALLOW:
        error('output_guard_rejected' if result.action != SafetyAction.ERROR else 'safety_provider_error')
    return result


class ToolExecutor:
    """Closed catalog. Identity and financial parameters never come from the model."""
    def __init__(self, request: DecisionRequest, identity: str):
        if identity != authorize(request.persona_key):
            error('identity_not_authorized', 403)
        self.request = request
        self.identity = identity
        self.context = None
        self.golden_analysis = None
        self.calls: list[str] = []

    def call(self, name: str, args: dict):
        if name not in {'get_financial_context', 'simulate_options', 'ask_purchase_terms'}:
            error('tool_not_allowed', 400)
        try:
            EmptyToolArgs.model_validate(args)
        except ValueError:
            error('tool_arguments_rejected', 400)
        if len(self.calls) >= 4:
            error('tool_budget_exceeded')
        self.calls.append(name)
        if name == 'get_financial_context':
            if self.context is None:
                self.context = self._load_context()
            return self.context
        if self.context is None:
            self.call('get_financial_context', {})
        if golden_enabled():
            from backend.core.golden import golden_decision
            result, self.golden_analysis = golden_decision(self.request, self.context)
        else:
            result = decide(self.request, self.context)
        if not demo_mode() or os.getenv('DATA_PROVIDER') == 'bigquery' or golden_enabled():
            result.data_mode = 'event_dataset_demo'
        return result

    def _load_context(self) -> FinancialContext:
        golden = golden_enabled()
        if golden:
            validate_golden_config()
            if self.request.confirmed_context and self.request.confirmed_context.as_of_date != GOLDEN_REFERENCE_DATE:
                error('golden_reference_date_is_fixed', 422)
        if golden and os.getenv('DATA_PROVIDER') == 'golden_fixture':
            try:
                from backend.data.golden_fixture import load_golden_fixture
                observed = load_golden_fixture()
            except Exception:
                error('golden_fixture_unavailable')
        elif demo_mode() and os.getenv('DATA_PROVIDER') != 'bigquery':
            observed = OwnSyntheticDemoProvider().get_context(self.identity)
        else:
            try:
                from backend.data import BigQueryContextProvider
                mapping = {GOLDEN_ALIAS: GOLDEN_USER_ID} if golden else json.loads(os.getenv('PINGO_AUTHORIZED_USERS', '{}'))
                if not isinstance(mapping, dict) or self.identity not in mapping:
                    error('server_identity_not_configured')
                observed = BigQueryContextProvider(authorized_users=mapping,
                    project_id=os.getenv('GOOGLE_CLOUD_PROJECT', 'batalha-time-08-g7ha'),
                    location=os.getenv('BIGQUERY_LOCATION','us-central1'),
                    **({'reference_date':GOLDEN_REFERENCE_DATE, 'golden_persona':True} if golden else {})).get_context(self.identity)
            except HTTPException:
                raise
            except Exception as exc:
                error('bigquery_unavailable')
        if self.request.confirmed_context is not None:
            confirmed = from_confirmed_context(self.request.confirmed_context)
            # In fixture mode confirmed context replaces fixture; real historical
            # context remains evidence only and cannot alter confirmed cashflows.
            if not demo_mode() or golden or os.getenv('DATA_PROVIDER') == 'bigquery':
                return replace(confirmed, evidence=observed.evidence + confirmed.evidence,
                    assumptions=observed.assumptions + confirmed.assumptions,
                    historical_summary=observed.historical_summary)
            return confirmed
        return observed


def explain(result: DecisionResponse) -> str:
    if golden_enabled():
        return result.message
    if result.question:
        return result.question.text
    base = result.message
    if not result.scenarios:
        return base
    assessment = result.scenarios[0].projection.assessment
    if assessment == 'violates_declared_constraints_in_window':
        return base + ' Nas condições informadas, a margem protegida não é preservada. Podemos ajustar entrada, quantidade de parcelas ou testar outra data informada, sem presumir uma oferta.'
    if assessment == 'meets_declared_constraints_in_window':
        return base + ' A margem informada é preservada nesta janela. Confira também os compromissos posteriores e o que ainda falta confirmar.'
    return base + ' Confirme saldo disponível, margem que deseja preservar e próximos compromissos para avaliar o impacto no objetivo.'
