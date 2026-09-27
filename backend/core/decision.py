"""Deterministic response assembly; no LLM-generated financial figures."""

from datetime import timedelta
from uuid import uuid4

from backend.core.context_contract import FinancialContext
from backend.core.finance import Cashflow, build_schedule, project, shift_months_clamped
from backend.models.decision import (
    ConfirmedContext, DecisionRequest, DecisionResponse, EvidenceOut,
    InstallmentOut, ProjectionOut, Question, ScenarioOut,
)


REQUIRED_TERMS = (
    ("total_price_cents", "Qual é o preço total em centavos?"),
    ("upfront_cents", "Qual é a entrada em centavos? Informe zero se não houver."),
    ("installment_count", "Em quantas parcelas será o pagamento?"),
    ("first_due_date", "Qual é a data da primeira cobrança?"),
)


def from_confirmed_context(confirmed: ConfirmedContext) -> FinancialContext:
    cashflows = [
        Cashflow(item.date, item.amount_cents * (1 if item.direction == "inflow" else -1))
        for item in confirmed.scheduled_cashflows
        if item.accounting_kind != 'card_purchase'
    ]
    return FinancialContext(
        as_of_date=confirmed.as_of_date,
        available_balance_cents=confirmed.available_balance_cents,
        scheduled_cashflows=cashflows,
        visible_until=confirmed.as_of_date + timedelta(days=90),
        protected_buffer_cents=confirmed.protected_buffer_cents,
        evidence=[EvidenceOut(
            id="confirmed-context", label="Contexto informado nesta requisição",
            origin="user_confirmed",
            detail="Saldo, vencimentos e margem informados pelo usuário; cobertura futura pode ser incompleta.",
        )],
        assumptions=[
            "Contexto declarado pelo usuário; eventos não informados ficam fora do cálculo.",
            "Histórico de 2025 não foi tratado como saldo atual ou obrigação futura.",
            "Compras de cartão explicitamente vinculadas a fatura confirmada são contabilizadas somente na liquidação da fatura; itens sem classificação não são conciliados automaticamente.",
        ],
    )


def decide(request: DecisionRequest, context: FinancialContext) -> DecisionResponse:
    common = dict(
        request_id=str(uuid4()), trace_id=str(uuid4()), data_mode="own_synthetic_demo",
        as_of_date=context.as_of_date, evidence=list(context.evidence),
        assumptions=list(context.assumptions),
    )
    terms = request.decision
    for field, question_text in REQUIRED_TERMS:
        if terms is None or getattr(terms, field) is None:
            return DecisionResponse(
                **common, state="needs_input",
                message="Falta uma condição da compra para montar o cronograma.",
                question=Question(field=field, text=question_text),
                scenarios=[], actions=["update_inputs"],
            )

    if terms.first_due_date < context.as_of_date:
        raise ValueError("first_due_date precedes as_of_date")

    def make_scenario(scenario_id: str, title: str, first_due_date):
        schedule = build_schedule(
            terms.total_price_cents, terms.upfront_cents,
            terms.installment_count, first_due_date,
        )
        projection = project(
            schedule, terms.upfront_cents, context.as_of_date, context.visible_until,
            context.available_balance_cents, context.scheduled_cashflows,
            context.protected_buffer_cents or 0,
        )
        assessment = (
            "insufficient_data" if context.protected_buffer_cents is None
            else projection.assessment
        )
        return ScenarioOut(
            id=scenario_id, title=title,
            total_price_cents=terms.total_price_cents,
            upfront_cents=terms.upfront_cents,
            schedule=[InstallmentOut(due_date=item.due_date, amount_cents=item.amount_cents)
                      for item in schedule],
            visible_until=context.visible_until,
            remaining_after_window_cents=projection.remaining_after_window_cents,
            projection=ProjectionOut(
                mode=projection.mode, through_date=projection.through_date,
                min_balance_cents=projection.min_balance_cents,
                assessment=assessment,
            ),
            reason_evidence_ids=[item.id for item in context.evidence] + ["user-terms"],
        )

    scenarios = [make_scenario("informada", terms.label or "Condições informadas", terms.first_due_date)]
    if request.preferences and request.preferences.can_wait is True:
        scenarios.append(make_scenario(
            "esperar", "Hipótese: primeira cobrança um mês depois",
            shift_months_clamped(terms.first_due_date, 1),
        ))
    evidence = list(context.evidence) + [EvidenceOut(
        id="user-terms", label="Condições da compra informadas",
        origin="user_confirmed",
        detail="Preço, entrada, número de parcelas e primeira cobrança enviados nesta requisição.",
    )]
    assumptions = list(context.assumptions) + [
        "Projeção limitada à janela exibida; a agenda completa inclui compromissos posteriores.",
        "Saídas são aplicadas antes de entradas no mesmo dia quando a ordem é desconhecida.",
        "A compra é deduzida somente pela entrada e pelas parcelas, sem descontar o preço cheio novamente.",
    ]
    if len(scenarios) > 1:
        assumptions.append(
            "A alternativa de esperar é hipótese: mesmo preço e mesmas condições com a primeira cobrança um mês depois; não é oferta confirmada."
        )
    if request.preferences and request.preferences.protected_items:
        assumptions.append(
            "Itens protegidos são prioridades declaradas; só valores e vencimentos confirmados entram no cálculo."
        )
    limited = scenarios[0].projection.mode == "unavailable" or context.protected_buffer_cents is None
    if limited:
        message = (
            "Posso mostrar todas as parcelas, mas falta saldo atual confirmado ou margem protegida "
            "para avaliar o dinheiro disponível. Não há conclusão de viabilidade."
        )
    else:
        message = (
            "Cenário calculado com as premissas exibidas. O resultado cobre apenas a janela "
            "indicada e não aprova a compra nem prevê todo o orçamento."
        )
    return DecisionResponse(
        **{**common, "evidence": evidence, "assumptions": assumptions},
        state="limited" if limited else "ready", message=message, question=None,
        scenarios=scenarios, actions=["update_inputs", "save_plan", "review_plan"],
    )
