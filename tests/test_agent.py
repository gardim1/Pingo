import asyncio
import json
from datetime import date

import pytest
from fastapi import HTTPException
from backend.agent.intent import extract_terms
from backend.agent.provider import GeminiADKProvider, AgentError
from backend.api.runtime import ToolExecutor
from backend.models.decision import DecisionRequest, DecisionTerms


@pytest.mark.parametrize('name,args',[('execute_sql',{}),('simulate_options',{'user_id':'other'}),('get_financial_context',{'sql':'SELECT 1'}),('simulate_options',{'total_price_cents':1})])
def test_model_cannot_select_identity_sql_or_money(monkeypatch,name,args):
    monkeypatch.setenv('DEMO_MODE','true')
    tool=ToolExecutor(DecisionRequest(persona_key='persona-a',message='Planejar'),'persona-a')
    with pytest.raises(HTTPException):
        tool.call(name,args)
    assert tool.calls == []


def test_parser_never_calculates_interest_or_assumes_dates():
    terms=extract_terms('iPhone R$ 10.000,99 em 3 parcelas; primeira amanhã, com desconto',None)
    assert terms.total_price_cents == 1000099
    assert terms.installment_count == 3
    assert terms.first_due_date is None
    assert terms.upfront_cents is None


def test_balance_is_not_a_purchase_price_and_alternatives_need_confirmation():
    assert extract_terms('Meu saldo é R$ 5.000',None).total_price_cents is None
    assert extract_terms('iPhone por R$ 10.000 ou R$ 9.000',None).total_price_cents is None
    assert extract_terms('Não quero 10 parcelas, quero 20 parcelas',None).installment_count is None


@pytest.mark.parametrize('message',[
    'iPhone em 10x de R$ 100,00 sem entrada, primeira em 2026-10-01',
    'iPhone por R$ 10.0000 sem entrada em 10 parcelas, primeira em 2026-10-01',
    'iPhone por R$ 100,00 por mês em 10 parcelas, sem entrada, primeira em 2026-10-01',
    'iPhone por R$ 100,00/parcela em 10 parcelas',
])
def test_installment_amount_and_malformed_price_never_become_total(message):
    assert extract_terms(message,None).total_price_cents is None


def test_multiple_due_dates_require_confirmation():
    assert extract_terms('primeira em 2026-10-01 ou primeira em 2026-12-01',None).first_due_date is None


def test_followup_updates_do_not_silently_keep_superseded_terms():
    previous=DecisionTerms(total_price_cents=100000,upfront_cents=0,installment_count=10,first_due_date=date(2026,10,1))
    assert extract_terms('Agora custa R$ 2.000',previous).total_price_cents == 200000
    assert extract_terms('Mudar entrada para R$ 200',previous).upfront_cents == 20000
    assert extract_terms('Mude a primeira para novembro',previous).first_due_date is None
    assert extract_terms('Mude para vinte parcelas',previous).installment_count is None


def test_adk_runtime_with_fake_transport_exercises_schema_and_runner(monkeypatch):
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types
    from google.auth.credentials import AnonymousCredentials
    from google import genai
    import google.auth
    import google.adk.models.google_llm as llm
    from google.genai.client import AsyncClient
    closed=[]
    original_close=AsyncClient.aclose
    async def track_close(self):
        closed.append(True)
        await original_close(self)
    monkeypatch.setattr(AsyncClient,'aclose',track_close)
    clients=[]
    class TrackedClient(genai.Client):
        def __init__(self,**kwargs):
            super().__init__(**kwargs)
            clients.append(self)  # Keep alive: destructor cleanup must not satisfy assertion.
    monkeypatch.setattr(genai,'Client',TrackedClient)

    class FakeGemini(llm.Gemini):
        async def generate_content_async(self,llm_request,stream=False):
            assert llm_request.config.response_schema is not None
            yield LlmResponse(content=types.Content(role='model',parts=[types.Part.from_text(text=json.dumps({
                'tool':'simulate_options','intent':'purchase','explanation_style':'explore_options'}))]))

    monkeypatch.setenv('GEMINI_MODEL','gemini-transport-test')
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT','batalha-time-08-g7ha')
    monkeypatch.setattr(google.auth,'default',lambda **kwargs:(AnonymousCredentials(),'batalha-time-08-g7ha'))
    monkeypatch.setattr(llm,'Gemini',FakeGemini)
    result=asyncio.run(GeminiADKProvider().interpret('Quero comprar um iPhone',{'terms':{}}))
    assert result.instruction.tool == 'simulate_options'
    assert result.model == 'gemini-transport-test'
    assert closed == [True]


def test_gemini_transport_error_is_not_replaced_with_demo(monkeypatch):
    import google.auth
    monkeypatch.setenv('GEMINI_MODEL','gemini-transport-test')
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT','batalha-time-08-g7ha')
    def unavailable(**kwargs):
        raise RuntimeError('sensitive credential error')
    monkeypatch.setattr(google.auth,'default',unavailable)
    with pytest.raises(AgentError) as caught:
        asyncio.run(GeminiADKProvider().interpret('Quero planejar',{}))
    assert caught.value.code == 'gemini_unavailable'
    assert 'sensitive' not in str(caught.value)
