from fastapi.testclient import TestClient
from backend.api.main import app

client=TestClient(app)


def test_card_purchase_and_confirmed_bill_are_not_counted_twice(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','true')
    response=client.post('/api/decision',json={
        'persona_key':'persona-a','message':'Planejar',
        'decision':{'total_price_cents':100,'upfront_cents':0,'installment_count':1,'first_due_date':'2026-10-10'},
        'confirmed_context':{'as_of_date':'2026-09-26','available_balance_cents':10000,'protected_buffer_cents':0,
            'scheduled_cashflows':[
                {'ref':'purchase','date':'2026-10-01','amount_cents':1000,'direction':'outflow','accounting_kind':'card_purchase','settlement_ref':'bill'},
                {'ref':'bill','date':'2026-10-05','amount_cents':1000,'direction':'outflow','accounting_kind':'card_bill_payment'}]}})
    assert response.status_code == 200
    assert response.json()['scenarios'][0]['projection']['min_balance_cents'] == 8900


def test_unreconciled_card_purchase_is_rejected(monkeypatch):
    monkeypatch.setenv('DEMO_MODE','true')
    response=client.post('/api/decision',json={
        'persona_key':'persona-a','message':'Planejar',
        'confirmed_context':{'as_of_date':'2026-09-26','scheduled_cashflows':[
            {'ref':'purchase','date':'2026-10-01','amount_cents':1000,'direction':'outflow','accounting_kind':'card_purchase'}]}})
    assert response.status_code == 422
