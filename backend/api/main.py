"""Pingo HTTP boundary: deterministic decisions and a guarded Gemini conversation."""
import logging
import json
import asyncio
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.agent.intent import extract_terms, extract_golden_terms, AgentInstruction
from backend.agent.provider import AgentError, get_agent_provider
from backend.api.runtime import (
    ToolExecutor, authorize, blocked_response, demo_mode, error, explain,
    get_safety_provider, inspect_input, validate_output,
    data_provider_name,
)
from backend.api.golden_config import golden_enabled, validate_golden_config, GOLDEN_REFERENCE_DATE, GOLDEN_ALIAS
from backend.core.demo_context import DEMO_PERSONAS
from backend.models.decision import DecisionRequest, DecisionResponse, DecisionReviewRequest, DecisionTerms
from backend.models.conversation import (
    AccompanimentRequest, AccompanimentResponse, ChatResponse, PlanRequest, RuntimeInfo, SavedPlan,
)
from backend.safety import SafetyAction

app = FastAPI(title='Pingo Core', version='0.2.0')
logger = logging.getLogger('pingo.requests')
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


@app.middleware('http')
async def observe(request: Request, call_next):
    start = perf_counter()
    request.state.audit = {'request_id':str(uuid4()), 'session_id':str(uuid4()),
                           'model':None, 'tools':[], 'safety':'not_run', 'engine':'not_run'}
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers['X-Request-ID'] = request.state.audit['request_id']
        response.headers['Cache-Control'] = 'no-store'
        return response
    finally:
        route = request.scope.get('route')
        logger.info(json.dumps({**request.state.audit, 'route':getattr(route, 'path', 'unmatched'),
            'status':status, 'duration_ms':round((perf_counter()-start)*1000, 2)}, ensure_ascii=False))


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Pydantic's default includes user input; omit it and any raw exception.
    return JSONResponse(status_code=422, content={'detail':[
        {'loc':list(e['loc']), 'type':e['type'], 'msg':'Invalid request field'} for e in exc.errors()]})


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    if hasattr(request.state, 'audit'):
        request.state.audit['error'] = exc.detail.get('code', 'http_error') if isinstance(exc.detail,dict) else 'http_error'
    return JSONResponse(status_code=exc.status_code, content={'detail':exc.detail})


@app.get('/health')
def health() -> dict[str,str]:
    return {'status':'ok'}


@app.get('/api/demo/personas')
def demo_personas() -> list[dict[str,str]]:
    if golden_enabled():
        validate_golden_config()
        return [{'key':GOLDEN_ALIAS, 'label':'Golden persona — identidade fixa no servidor'}]
    if not demo_mode():
        raise HTTPException(503, 'Demo mode is disabled')
    return [{'key':key,'label':label} for key,label in DEMO_PERSONAS.items()]


def run_decision(payload: DecisionRequest, http: Request | None = None) -> DecisionResponse:
    identity = authorize(payload.persona_key)
    safety = get_safety_provider()
    checked = inspect_input(safety, payload)
    if http:
        http.state.audit['safety'] = checked.action.value
    if checked.action in {SafetyAction.BLOCK, SafetyAction.REDIRECT}:
        result = blocked_response(checked.safe_message)
        if checked.action == SafetyAction.REDIRECT:
            result.state = 'limited'
        validate_output(safety, result.message)
        return result
    executor = ToolExecutor(payload, identity)
    if http:
        http.state.audit['tools'] = executor.calls
    start = perf_counter()
    try:
        result = executor.call('simulate_options', {})
    except (ValueError, OverflowError):
        error('invalid_financial_inputs',422)
    result.message = explain(result)
    validate_output(safety, '\n'.join([result.message, *[s.title for s in result.scenarios]]))
    if http:
        http.state.audit.update(tools=executor.calls,engine=result.state,
            tools_duration_ms=round((perf_counter()-start)*1000,2),output_safety='ALLOW')
        result.request_id = http.state.audit['request_id']
        result.trace_id = http.state.audit['request_id']
    return result


@app.post('/api/decision', response_model=DecisionResponse)
def decision(payload: DecisionRequest, request: Request) -> DecisionResponse:
    return run_decision(payload,request)


@app.post('/api/decision/review', response_model=DecisionResponse)
def review(payload: DecisionReviewRequest, request: Request) -> DecisionResponse:
    snapshot = payload.plan_snapshot
    current = payload.model_copy(update={
        'decision':payload.decision or (snapshot.decision if snapshot else None),
        'preferences':payload.preferences or (snapshot.preferences if snapshot else None),
    })
    return run_decision(DecisionRequest.model_validate(current.model_dump(exclude={'plan_snapshot'})),request)


@app.post('/api/chat', response_model=ChatResponse)
def chat(payload: DecisionRequest, request: Request) -> ChatResponse:
    identity = authorize(payload.persona_key)
    safety = get_safety_provider()
    checked = inspect_input(safety,payload)
    request.state.audit['safety'] = checked.action.value
    runtime = RuntimeInfo(agent='not_called',data=data_provider_name(),
                          safety=checked.provider)
    if checked.action in {SafetyAction.BLOCK, SafetyAction.REDIRECT}:
        validate_output(safety, checked.safe_message)
        return ChatResponse(session_id=request.state.audit['session_id'],message=checked.safe_message,
            draft=None,decision=blocked_response(checked.safe_message) if checked.action == SafetyAction.BLOCK else None,
            runtime=runtime)
    try:
        draft = (extract_golden_terms(payload.message, payload.decision, GOLDEN_REFERENCE_DATE)
                 if golden_enabled() else extract_terms(payload.message,payload.decision))
        current = payload.model_copy(update={'decision':draft})
        # Missing Gemini configuration must not trigger a paid data query.
        provider = get_agent_provider()
        executor = ToolExecutor(current,identity)
        request.state.audit.update(tools=executor.calls, model=getattr(provider,'model',None))
        start = perf_counter()
        context = executor.call('get_financial_context',{})
        request.state.audit['data_duration_ms'] = round((perf_counter()-start)*1000,2)
        golden_result = None
        if golden_enabled():
            engine_start = perf_counter()
            golden_result = executor.call('simulate_options', {})
            request.state.audit['engine_duration_ms'] = round((perf_counter()-engine_start)*1000,2)
        start = perf_counter()
        agent = asyncio.run(provider.interpret(payload.message, {
            'terms':draft.model_dump(mode='json'),
            'has_confirmed_balance':context.available_balance_cents is not None,
            'limitations':context.assumptions,
            'history': (executor.golden_analysis.model_dump(mode='json', exclude={'assumptions'})
                        if executor.golden_analysis else context.historical_summary),
        }))
        request.state.audit.update(model=agent.model,model_duration_ms=round((perf_counter()-start)*1000,2),usage=agent.usage)
        instruction = AgentInstruction.model_validate(agent.instruction.model_dump())
        if golden_result is not None:
            # Gemini chooses intent/tool but cannot replace the calculated response.
            result = golden_result
            message = result.message
        elif instruction.intent == 'out_of_scope':
            message = 'Meu foco é ajudar a planejar objetivos financeiros. Podemos comparar condições de uma compra.'
            result = None
        elif instruction.tool == 'get_financial_context':
            result = blocked_response('O histórico oferece contexto, mas não confirma saldo atual, renda futura ou compromissos restantes. Informe as condições da compra para montar um cenário.')
            result.state = 'limited'
            result.as_of_date = context.as_of_date
            result.evidence = context.evidence
            result.assumptions = context.assumptions
            message = result.message
        else:
            start = perf_counter()
            result = executor.call(instruction.tool,{})
            request.state.audit['engine_duration_ms'] = round((perf_counter()-start)*1000,2)
            message = explain(result)
            result.message = message
        validate_output(safety,'\n'.join([message,*([s.title for s in result.scenarios] if result else [])]))
        runtime.agent, runtime.model, runtime.tools = agent.provider, agent.model, executor.calls
        request.state.audit.update(tools=executor.calls,engine=result.state if result else 'not_run',output_safety='ALLOW')
        if result:
            result.request_id = request.state.audit['request_id']
            result.trace_id = request.state.audit['request_id']
            if agent.provider == 'gemini':
                result.assumptions = [s.replace('nenhuma consulta BigQuery ou chamada Gemini foi feita.',
                    'nenhuma consulta BigQuery foi feita; interpretação realizada pelo Gemini.') for s in result.assumptions]
        return ChatResponse(session_id=request.state.audit['session_id'],message=message,draft=draft,decision=result,runtime=runtime,
                            golden_analysis=executor.golden_analysis)
    except AgentError as exc:
        error(exc.code)
    except (ValueError, OverflowError):
        error('invalid_agent_or_financial_inputs',422)


@app.post('/api/plan', response_model=SavedPlan)
def save_plan(payload: PlanRequest) -> SavedPlan:
    if not payload.consent_enabled:
        error('plan_consent_required',409)
    authorize(payload.persona_key)
    checked = inspect_input(get_safety_provider(),payload)
    if checked.action != SafetyAction.ALLOW:
        error('plan_input_rejected',400)
    validate_output(get_safety_provider(),payload.decision.label if payload.decision and payload.decision.label else 'Plano com condições informadas.')
    return SavedPlan(plan_id=str(uuid4()),decision=payload.decision,preferences=payload.preferences)


@app.post('/api/accompaniment/review', response_model=AccompanimentResponse)
def accompaniment(payload: AccompanimentRequest, request: Request) -> AccompanimentResponse:
    # Opt-out precedes auth, context, model and safety providers. No proactive job.
    if not payload.consent_enabled:
        return AccompanimentResponse(reviewed=False,reason='opted_out',decision=None)
    if not demo_mode():
        error('simulated_event_requires_demo',403)
    authorize(payload.persona_key)
    if payload.event is None:
        error('simulated_event_required',422)
    if golden_enabled():
        if payload.event.offer_ref != 'golden-extra-1000':
            error('golden_event_not_authorized', 403)
        if payload.plan_snapshot is None or payload.plan_snapshot.decision is None:
            error('golden_plan_snapshot_required', 422)
        from dataclasses import replace
        from backend.core.finance import Cashflow
        from backend.core.golden import golden_decision
        current = DecisionRequest(persona_key=payload.persona_key, message='Rever plano após compra simulada',
            decision=payload.plan_snapshot.decision, preferences=payload.plan_snapshot.preferences,
            confirmed_context=payload.confirmed_context)
        safety = get_safety_provider()
        checked = inspect_input(safety, current)
        if checked.action != SafetyAction.ALLOW:
            error('plan_input_rejected', 400)
        executor = ToolExecutor(current, authorize(payload.persona_key))
        context = executor.call('get_financial_context', {})
        context = replace(context, scheduled_cashflows=[*context.scheduled_cashflows,
                          Cashflow(context.as_of_date, -100000)])
        engine_start = perf_counter()
        try:
            result, analysis = golden_decision(current, context, simulated_purchase_cents=100000)
        except (ValueError, OverflowError):
            error('invalid_financial_inputs', 422)
        validate_output(safety, '\n'.join([result.message, *[s.title for s in result.scenarios]]))
        request.state.audit.update(tools=executor.calls, engine=result.state, safety=checked.action.value,
                                   engine_duration_ms=round((perf_counter()-engine_start)*1000,2), output_safety='ALLOW')
        result.request_id = result.trace_id = request.state.audit['request_id']
        return AccompanimentResponse(reviewed=True,
            reason='needs_confirmation' if not analysis.installments_cents else 'reviewed', decision=result)
    if payload.event.offer_ref != 'demo-iphone':
        error('simulated_event_not_authorized', 403)
    # Fixed own fixture. Replays recalculate from original context without accumulation.
    current = DecisionRequest(persona_key=payload.persona_key,message='Rever compra simulada',
        decision=DecisionTerms(label='iPhone fictício — EVENTO SIMULADO',total_price_cents=1000000,
            upfront_cents=0,installment_count=10,first_due_date='2026-10-01'))
    result = run_decision(current,request)
    result.message = 'EVENTO SIMULADO — não é uma transação bancária. A compra acrescentou os vencimentos do cenário; saldo inicial e demais compromissos do fixture continuam iguais. ' + result.message
    validate_output(get_safety_provider(),result.message)
    return AccompanimentResponse(reviewed=True,reason='reviewed',decision=result)
