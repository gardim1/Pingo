"""Conservative local extraction; model-selected actions cannot supply money or IDs."""
import re
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field
from backend.models.decision import DecisionTerms, StrictModel


class AgentInstruction(StrictModel):
    tool: Literal['simulate_options', 'get_financial_context', 'ask_purchase_terms']
    intent: Literal['purchase', 'adjustment', 'financial_difficulty', 'out_of_scope']
    explanation_style: Literal['neutral', 'explore_options'] = 'neutral'


class EmptyToolArgs(StrictModel):
    """Tools use only request-scoped, backend-authorized inputs."""


def extract_terms(message: str, previous: DecisionTerms | None) -> DecisionTerms:
    """Only unambiguous Brazilian currency, explicit installments and ISO dates.

    Unrecognized/ambiguous prose leaves fields absent so the engine asks. Structured
    fields remain the route for richer conditions. No inferred interest or discounts.
    """
    terms = (previous or DecisionTerms()).model_dump()
    # A mentioned field supersedes the previous draft even when the new value
    # cannot be parsed. In that case ask instead of silently keeping old terms.
    for field, pattern in (
        ('upfront_cents', r'\bentrada\b'),
        ('installment_count', r'\b(parcelas?|vezes)\b'),
        ('first_due_date', r'\b(primeira|vencimento)\b'),
        ('total_price_cents', r'\b(preço|preco|total|custa|custará|custara)\b'),
    ):
        if re.search(pattern,message,re.I):
            terms[field] = None
    amounts = list(re.finditer(r'R\$\s*(\d[\d.,]*)', message, re.I))
    extracted = {'upfront_cents': [], 'total_price_cents': []}
    for match in amounts:
        before = message[max(0, match.start()-24):match.start()].lower()
        after = message[match.end():].lower()
        field = 'upfront_cents' if (re.search(r'entrada\s*(?:(?:de|para|:)\s*)?$', before)
            or re.match(r'\s*(?:de\s+)?entrada\b', after)) else 'total_price_cents'
        raw = match.group(1).removesuffix('.')
        if not re.fullmatch(r'(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?',raw):
            terms[field] = None
            continue
        if field == 'total_price_cents':
            after = message[match.end():].lower()
            if (re.search(r'(?:parcelas?|vezes|x)\s*(?:de|a)?\s*$',before)
                    or re.match(r'\s*(?:(?:por|ao|a|/)\s*)?(?:m[eê]s|mensais|mensal|parcelas?)\b',after)):
                terms[field] = None
                continue
            explicit_price = re.search(r'(?:por|preço|preco|total|custa|custará|custara)\s*(?:de\s*)?$', before)
            bare_amount = message[:match.start()].strip() == ''
            purchase_context = re.search(r'\b(comprar|iphone|celular|produto)\b', before, re.I)
            if not (explicit_price or bare_amount or purchase_context):
                continue
        extracted[field].append(int(Decimal(raw.replace('.', '').replace(',', '.')) * 100))
    for field, values in extracted.items():
        if len(values) == 1:
            terms[field] = values[0]
        elif values:
            terms[field] = None
    if len(amounts) - len(extracted['upfront_cents']) > 1:
        terms['total_price_cents'] = None
    if re.search(r'\bsem entrada\b', message, re.I):
        terms['upfront_cents'] = 0
    counts = re.findall(r'\b(\d{1,2})\s*(?:parcelas?|vezes|x\b)', message, re.I)
    if counts:
        terms['installment_count'] = int(counts[0]) if len(counts) == 1 else None
    dates = re.findall(r'(?:primeira(?:\s+(?:parcela|cobrança))?|vencimento)\s*(?:em|dia|:)\s*(\d{4}-\d{2}-\d{2})(?!\d)', message, re.I)
    if dates:
        terms['first_due_date'] = date.fromisoformat(dates[0]) if len(dates) == 1 else None
    if re.search(r'\biphone\b', message, re.I):
        terms['label'] = 'iPhone — condições informadas'
    return DecisionTerms.model_validate(terms)


def extract_golden_terms(message: str, previous: DecisionTerms | None, reference: date) -> DecisionTerms:
    """Resolve only explicit demo conditions; month is not an invented due day."""
    terms = extract_terms(message, previous).model_dump()
    negated_interest = re.search(r'\bn[aã]o\s+(?:(?:é|e|era|ser[aá]|tem|vai\s+ser|est[aá])\s+)?sem\s+juros\b', message, re.I)
    if negated_interest or re.search(r'\bcom juros\b', message, re.I):
        terms['interest_free'] = None
    elif re.search(r'\bsem juros\b', message, re.I):
        terms['interest_free'] = True
    elif re.search(r'\b(juros|taxa)\b', message, re.I):
        terms['interest_free'] = None
    negated_cash = re.search(r'\bn[aã]o\b.{0,24}\b[aà] vista\b', message, re.I)
    if negated_cash and previous and previous.upfront_cents == previous.total_price_cents:
        terms['upfront_cents'] = None
    if re.search(r'\b[aà] vista\b', message, re.I) and not negated_cash and terms['total_price_cents'] is not None:
        terms.update(upfront_cents=terms['total_price_cents'], installment_count=1,
                     interest_free=True, first_due_date=reference)
    months = ('janeiro','fevereiro','março','abril','maio','junho','julho','agosto',
              'setembro','outubro','novembro','dezembro')
    mentioned_months = re.findall(r'\b(' + '|'.join(months) + r')\b', message, re.I)
    waiting = re.search(r'\b(?:esperar|comprar|compra)\b.{0,24}\b(?:até|em|para)\s+(' + '|'.join(months) + r')\b(?:\s+(?:de\s+)?(\d{4}))?', message, re.I)
    if waiting and len(mentioned_months) != 1:
        terms.update(purchase_month=None, first_due_date=None)
    elif waiting:
        month = months.index(waiting.group(1).lower()) + 1
        year = int(waiting.group(2)) if waiting.group(2) else reference.year + (month < reference.month)
        terms['purchase_month'] = date(year, month, 1)
        terms['first_due_date'] = None  # Month alone never claims a billing date.
    elif re.search(r'\b(?:agora|hoje)\b', message, re.I):
        terms['purchase_month'] = reference.replace(day=1)
        if terms['first_due_date'] and terms['first_due_date'].month != reference.month:
            terms['first_due_date'] = None
    return DecisionTerms.model_validate(terms)
