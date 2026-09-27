"""Deterministic historical comparison, deliberately separate from a cash balance.

The September expense composition is the benchmark for conditional release; a
three-month mean may not contain all the same installments and is context only.
"""
from collections import Counter
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import re

from backend.core.context_contract import FinancialContext
from backend.core.decision import decide
from backend.core.finance import split_installments, shift_months_clamped
from backend.models.decision import DecisionRequest, EvidenceOut, Question
from backend.models.conversation import GoldenAnalysis, HistoricalComparison


def money(cents: int) -> str:
    sign = '-' if cents < 0 else ''
    whole, fraction = divmod(abs(cents), 100)
    return f"{sign}R$ {whole:,}".replace(',', '.') + f',{fraction:02d}'


def mean(values: list[int]) -> int | None:
    return int((Decimal(sum(values)) / len(values)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) if values else None


def analyze_golden(request: DecisionRequest, context: FinancialContext, simulated_purchase_cents: int = 0) -> GoldenAnalysis:
    history = (context.historical_summary or {}).get('golden')
    if not history:
        raise ValueError('golden history missing')
    reference = context.as_of_date
    months = sorted(history['monthly'], key=lambda row: row['month'])
    recent_start = shift_months_clamped(reference.replace(day=1), -2)
    six_start = shift_months_clamped(reference.replace(day=1), -5)
    eligible = [row for row in months if six_start <= date.fromisoformat(row['month']) <= reference]
    recent = [row for row in eligible if date.fromisoformat(row['month']) >= recent_start]
    latest = next((row for row in eligible if row['month'] == reference.replace(day=1).isoformat()), None)
    def margin(row):
        return None if row['salary_cents'] is None else row['salary_cents'] - row['expenses_excluding_invoice_cents']
    recent_mean = mean([margin(row) for row in recent]) if len(recent) == 3 and all(margin(row) is not None for row in recent) else None
    six_mean = mean([margin(row) for row in eligible]) if len(eligible) == 6 and all(margin(row) is not None for row in eligible) else None
    baseline = margin(latest) if latest else None
    terms = request.decision
    quote = []
    assumptions = [
        'Persona derivada da base sintética do hackathon. Não representa cliente real do Itaú.',
        'Margens históricas não são saldo nem renda disponível garantida; histórico volátil.',
        'Comparação condicional usa a composição de setembro, não soma liberação à média trimestral.',
        'Hipótese: repetir receitas/despesas de setembro e retirar somente parcelas cujo término estimado seja anterior ao mês comparado, sem novas obrigações.',
        'Marcadores de parcela não confirmam quitação, contrato ativo nem calendário futuro. Confirme o término.',
        'Excluir pagamento de fatura evita somá-lo às compras nesta comparação; não é conciliação bancária completa.',
        'O mês escolhido não confirma dia da primeira cobrança; saldo, despesas futuras e margem protegida continuam a confirmar.',
        *history.get('limitations', []),
    ]
    if terms and terms.total_price_cents is not None and terms.installment_count and terms.interest_free is True:
        upfront = terms.upfront_cents or 0
        quote = split_installments(terms.total_price_cents - upfront, terms.installment_count)
        assumptions.append('Parcelamento sem juros é condição/hipótese informada pelo usuário, não oferta de loja ou banco.')
        if terms.upfront_cents is None:
            assumptions.append('Para cotar a parcela, hipótese explícita de entrada zero; pode ser alterada, não é condição confirmada.')
    active = [row for row in history['installments'] if row['total'] > row['current']]
    selected = (terms.purchase_month or (terms.first_due_date.replace(day=1) if terms.first_due_date else None)) if terms else None
    selected = selected or reference.replace(day=1)
    if selected < reference.replace(day=1):
        raise ValueError('purchase month precedes analysis reference')
    end_dates = [date.fromisoformat(row['estimated_end_date']) for row in active if row.get('estimated_end_date')]
    released_month = shift_months_clamped(max(end_dates).replace(day=1), 1) if end_dates else None
    def release(month):
        return sum(row['amount_cents'] for row in active if row.get('estimated_end_date')
                   and date.fromisoformat(row['estimated_end_date']) < month)
    comparisons = []
    if baseline is not None:
        for month in dict.fromkeys([reference.replace(day=1), *([released_month] if released_month else []), selected]):
            benchmark = baseline + release(month)
            comparisons.append(HistoricalComparison(month=month, conditional_release_cents=release(month),
                benchmark_margin_cents=benchmark,
                margin_after_installment_min_cents=benchmark-max(quote) if quote else None,
                margin_after_installment_max_cents=benchmark-min(quote) if quote else None))
    return GoldenAnalysis(reference_date=reference, data_source=history['origin'],
        salary_observed_cents=latest['salary_cents'] if latest else None,
        recent_average_margin_cents=recent_mean, six_month_average_margin_cents=six_mean,
        last_month_margin_cents=baseline,
        observed_installments_total_cents=sum(row['amount_cents'] for row in active),
        observed_installment_count=len(active),
        estimated_last_installment_month=max(end_dates).replace(day=1) if end_dates else None,
        installments_cents=quote, selected_month=selected, selected_conditional_release_cents=release(selected),
        comparisons=comparisons, assumptions=assumptions, simulated_purchase_cents=simulated_purchase_cents,
        event_month_before_cents=baseline if simulated_purchase_cents else None,
        event_month_after_cents=baseline-simulated_purchase_cents if simulated_purchase_cents and baseline is not None else None)


def golden_decision(request: DecisionRequest, context: FinancialContext, simulated_purchase_cents: int = 0):
    result = decide(request, context)
    analysis = analyze_golden(request, context, simulated_purchase_cents)
    result.data_mode = 'event_dataset_demo'  # Legacy v1 provenance enum; runtime names actual provider.
    result.assumptions = list(dict.fromkeys([*result.assumptions, *analysis.assumptions]))
    terms = request.decision
    if not terms or terms.total_price_cents is None:
        result.question = Question(field='total_price_cents', text='Qual é o preço total do aparelho que você está considerando?')
    elif terms.installment_count is None:
        result.question = Question(field='installment_count', text='Você pensa em pagar à vista, dar uma entrada ou parcelar?')
    elif terms.interest_free is not True:
        result.question = Question(field='interest_free', text='Esse parcelamento é sem juros? Se houver custos, preciso das condições reais para comparar.')
        result.scenarios = []
        result.state = 'needs_input'
    elif result.question:
        if terms.upfront_cents is None:
            result.question = Question(field='upfront_cents', text='Estou comparando com entrada zero como hipótese. Você pretende dar uma entrada?')
        elif terms.first_due_date is None:
            result.question = Question(field='first_due_date', text='Em que dia seria a primeira cobrança? O mês sozinho ainda não define o cronograma.')
    result.evidence.append(EvidenceOut(id='golden-historical-comparison', label='Comparação histórica condicional em centavos',
        origin='derived', detail=analysis.model_dump_json(exclude={'assumptions'})))
    result.message = render_golden(request, result, analysis)
    return result, analysis


def render_golden(request, result, analysis):
    message = request.message.lower()
    if re.search(r'\bita[uú]\b|iphone pra sempre', message):
        return 'Modalidades do banco podem ser comparadas caso você forneça as condições reais. Não tenho condições verificadas desse produto configuradas.'
    if not request.decision or request.decision.total_price_cents is None or request.decision.installment_count is None:
        return ('EVENTO SIMULADO recebido; faltam condições do plano para comparar. ' if analysis.simulated_purchase_cents else '') + result.question.text
    if not analysis.installments_cents:
        return ('EVENTO SIMULADO recebido; faltam condições do plano para comparar. ' if analysis.simulated_purchase_cents else '') + result.question.text
    prefix = ''
    if re.search(r'\b(trabalho|marketing|preciso)\b', message):
        prefix = 'Entendo que o aparelho é importante para o seu trabalho. Se esperar não funcionar, podemos comparar entrada maior, prazo informado ou aparelho de menor valor. '
    elif re.search(r'\bmesmo assim\b', message):
        prefix = 'A decisão é sua. Posso ajudar a deixar as consequências claras e ajustar o plano com você. '
    elif request.decision.purchase_month and request.decision.purchase_month > analysis.reference_date.replace(day=1):
        prefix = 'Recalculei a comparação para o mês que você escolheu. '
    installments = Counter(analysis.installments_cents)
    quote = ' e '.join(f'{count} parcelas de {money(amount)}' for amount, count in installments.items())
    if request.decision.upfront_cents == request.decision.total_price_cents:
        quote = f'pagamento à vista de {money(request.decision.total_price_cents)}'
    parts = [prefix + f'Com as condições sem juros que você informou, o cálculo dá {quote}.']
    if request.decision.upfront_cents:
        parts.append(f'A entrada de {money(request.decision.upfront_cents)} também precisa caber no saldo que você confirmar.')
    if prefix and re.search(r'\b(trabalho|marketing|preciso|mesmo assim)\b', message) and not analysis.simulated_purchase_cents:
        selected = next((item for item in analysis.comparisons if item.month == analysis.selected_month), None)
        if selected:
            parts.append(f'No comparativo histórico condicional para {selected.month:%m/%Y}, o indicador após a maior parcela seria {money(selected.margin_after_installment_min_cents)}. Isso não é saldo disponível; o histórico é volátil.')
        parts.append('Para decidir com esse impacto em vista, faltam confirmar saldo e próximos compromissos. Uma mudança de entrada ou prazo recalcula as parcelas, sem presumir renda adicional pelo trabalho.')
        return ' '.join(parts)
    if analysis.recent_average_margin_cents is not None:
        parts.append(f'A margem média observada nos três meses recentes foi {money(analysis.recent_average_margin_cents)}, mas a série é volátil: isso não é renda disponível garantida.')
    if analysis.last_month_margin_cents is not None:
        parts.append(f'Em setembro a margem observada foi {money(analysis.last_month_margin_cents)}; a média dos seis meses foi {money(analysis.six_month_average_margin_cents)}.' if analysis.six_month_average_margin_cents is not None else f'A última margem observada foi {money(analysis.last_month_margin_cents)}.')
    if analysis.observed_installments_total_cents:
        end = f' com término estimado até {analysis.estimated_last_installment_month:%m/%Y}' if analysis.estimated_last_installment_month else ''
        parts.append(f'Há {analysis.observed_installment_count} parcelas observadas{end}, somando {money(analysis.observed_installments_total_cents)} por mês. Se terminarem nas datas estimadas, sem novas obrigações, esperar reduz essa pressão; não é garantia de capacidade futura.')
    future_chosen = (request.decision.purchase_month
                     if request.decision.purchase_month and request.decision.purchase_month > analysis.reference_date.replace(day=1)
                     else None)
    if len(analysis.comparisons) > 1:
        after = (next((item for item in analysis.comparisons if item.month == future_chosen), None)
                 if future_chosen else analysis.comparisons[1])
        parts.append(f'Na hipótese de repetir setembro e encerrar essas parcelas, o indicador mensal em {after.month:%m/%Y} seria {money(after.benchmark_margin_cents)} antes do novo aparelho e {money(after.margin_after_installment_min_cents)} com sua maior parcela. É uma comparação histórica condicional, não uma previsão de saldo.')
        if after.margin_after_installment_min_cents < 0:
            parts.append('Mesmo esperando, esse cenário ainda ficaria apertado. Podemos testar outras condições que você informar.')
    if analysis.simulated_purchase_cents:
        parts.append(f'EVENTO SIMULADO — compra de {money(analysis.simulated_purchase_cents)}, contabilizada uma vez no mês do evento, sem virar despesa recorrente. O preço e as condições do seu plano continuam iguais. Essa compra reduz os recursos para o objetivo; podemos recalcular o caminho sem presumir saldo disponível.')
        if analysis.event_month_before_cents is not None:
            parts.append(f'Na comparação ancorada em setembro, esse efeito pontual muda o indicador de {money(analysis.event_month_before_cents)} para {money(analysis.event_month_after_cents)}; esses valores não são saldo bancário.')
    parts.append(result.question.text if result.question else 'Faltam confirmar saldo, próximos compromissos e término das obrigações para avaliar a segurança da compra.')
    return ' '.join(parts)
