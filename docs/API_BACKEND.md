# Integração do backend Pingo

Atualizado em 2026-09-27. Os endpoints anteriores e DecisionResponse 1.0 continuam compatíveis; os 103 testes anteriores integram a suíte de regressão preservada. /docs descreve os requests atuais. Nenhum frontend ou schema compartilhado de resposta foi alterado.

## Providers e identidade da golden persona

Configuração golden real, definida somente no servidor:

~~~dotenv
DEMO_MODE=true
DEMO_USER_ID=6491f4a4-67dc-49de-a38a-cf655ff77c33
DEMO_REFERENCE_DATE=2025-09-30
DATA_PROVIDER=bigquery
AGENT_PROVIDER=gemini
GOOGLE_CLOUD_PROJECT=batalha-time-08-g7ha
GOOGLE_CLOUD_LOCATION=global
BIGQUERY_LOCATION=us-central1
GEMINI_MODEL=gemini-3.8-flash
SAFETY_PROVIDER=local
~~~

DEMO_MODE=true permite a demonstração sintética e seus eventos simulados; **não troca BigQuery por fixture**. ID/data devem coincidir exatamente com os valores autorizados. Configuração parcial ou divergente retorna HTTP 503 golden_demo_not_configured. Na golden, o servidor monta a identidade fixa; PINGO_AUTHORIZED_USERS/PINGO_BOUND_PERSONA não selecionam outra persona.

Para desenvolvimento offline, conservar identidade/data acima e selecionar explicitamente DATA_PROVIDER=golden_fixture e AGENT_PROVIDER=demo. Isso lê somente tests/fixtures/golden_persona.json, com origem user_supplied_hackathon_snapshot; não é consulta BigQuery. A fixture não integra a imagem. Com K_SERVICE, a golden exige **BigQuery + Gemini**, recusando fixture e agente demo. Falhas não ativam fallback.

O request golden pode omitir persona_key; o único alias compatível é persona-a. Outro alias retorna 403. user_id não é campo do request nem argumento de tool; texto declarando outra identidade não altera o vínculo.

| Modo | Dados | Identidade | runtime.data do chat |
|---|---|---|---|
| Golden real | Configuração acima | Fixa no servidor | bigquery |
| Golden offline explícita | DATA_PROVIDER=golden_fixture | Mesma identidade/data | golden_fixture |
| Demo própria anterior | DEMO_MODE=true, sem variáveis golden, dados demo | Allowlist anterior | own_synthetic_demo |
| BigQuery anterior | DATA_PROVIDER=bigquery, sem variáveis golden | PINGO_BOUND_PERSONA + PINGO_AUTHORIZED_USERS | event_dataset_demo (compatibilidade anterior) |

decision.data_mode=event_dataset_demo continua sendo o enum de **origem sintética do evento** no contrato v1, não o nome do adapter. Na golden, conferir runtime.data e golden_analysis.data_source: bigquery/dataset_observed ou golden_fixture/user_supplied_hackathon_snapshot. runtime.agent identifica gemini/demo e runtime.model informa o modelo quando chamado. HTTP 200 com input bloqueado pode ter agent=not_called; não comprova integração.

## Conversa e recálculo

POST /api/chat inicia sem persona selecionável:

~~~json
{"message":"Quero comprar um iPhone de R$ 10.000. Faz sentido agora?"}
~~~

O backend pergunta a forma de pagamento. O retorno contém message, draft, decision v1, runtime, session_id, accompaniment_enabled=false e golden_analysis opcional. O ID de sessão é gerado **por requisição**; não autentica usuário nem mantém memória. O cliente conserva o draft e o envia como decision:

~~~json
{"message":"10 vezes sem juros","decision":{"label":"iPhone — condições informadas","total_price_cents":1000000}}
~~~

Reenviar sempre o draft mais recente nos próximos turnos: “Consigo dar R$ 2.000 de entrada”, “Em 12 vezes sem juros”, “E se eu esperar até novembro?” e “Primeira em 2025-11-10”. O engine recalcula. “Sem juros” é condição/hipótese informada pelo usuário; não existe oferta comercial presumida.

Novos campos **opcionais**, default null, em DecisionTerms:

| Campo | Significado |
|---|---|
| interest_free | Booleano estrito. Cotação golden exige true; juros/custos desconhecidos exigem esclarecimento. |
| purchase_month | Data ISO no primeiro dia do mês, por exemplo 2025-11-01. Seleciona comparação mensal, não vencimento. |

Campos anteriores preservados: total_price_cents, upfront_cents, installment_count, first_due_date e label. Na golden, “esperar até novembro” resolve o mês a partir de 2025-09-30 e deixa first_due_date=null. Sem dia de primeira cobrança, a cotação pode aparecer em golden_analysis.installments_cents, mas não há agenda completa em decision.scenarios. Entrada ausente pode ser comparada como hipótese explícita de zero, com pedido de confirmação. Texto ambíguo precisa de campos estruturados.

golden_analysis reúne cálculo determinístico: referência/origem, salário observado, médias de margem de três/seis meses, margem de setembro, quantidade/total das parcelas observadas, último mês estimado, cotação em centavos, mês selecionado, liberação condicional, comparações e hipóteses. comparisons contém benchmark_margin_cents, conditional_release_cents e margens após a menor/maior parcela. **Não são saldos nem renda disponível garantida.** A comparação condicional usa setembro; não soma liberação à média trimestral. Ver [GOLDEN_PERSONA.md](GOLDEN_PERSONA.md).

O engine executa antes de Gemini na golden; o agente recebe o resumo calculado mínimo. Dinheiro, datas e identidade não são argumentos livres do modelo. A resposta é renderizada pelo backend e passa pelo output guardrail. /api/decision e /api/decision/review continuam atalhos determinísticos **sem Gemini**: enviar condições estruturadas, pois extração conversacional ocorre em /api/chat.

confirmed_context pode complementar saldo, margem protegida e lançamentos confirmados. Na golden, as_of_date precisa ser 2025-09-30; outra data retorna 422 golden_reference_date_is_fixed. Histórico não preenche saldo/agenda desconhecidos. Valores calculados recebidos do cliente não são prova financeira.

## Compra de cartão e fatura

Lançamentos confirmados aceitam accounting_kind ordinary (default), card_purchase ou card_bill_payment. Uma compra exige settlement_ref da fatura confirmada, posterior/igual e suficiente para as compras vinculadas; somente a liquidação afeta caixa. Sem vínculo, rejeitar e pedir confirmação. A compra simulada não deve já estar incluída no contexto anterior. Excluir Pagamento de fatura dos agregados golden define uma visão de despesas, não conciliação bancária automática.

## Plano, consentimento e Supervisor simulado

POST /api/plan recebe DecisionRequest mais consent_enabled=true; sem consentimento retorna 409. Exemplo com condições fornecidas:

~~~json
{"message":"Guardar estas condições na sessão","consent_enabled":true,"decision":{"label":"iPhone","total_price_cents":1000000,"upfront_cents":200000,"installment_count":12,"interest_free":true,"purchase_month":"2025-11-01","first_due_date":"2025-11-10"}}
~~~

Retorna plan_id, decision, preferences, storage=client_session_only e accompaniment_enabled=false. Salvar não ativa acompanhamento nem grava memória longa. Para revisar, enviar as condições em plan_snapshot; o snapshot é entrada não confiável, não prova de saldo.

POST /api/accompaniment/review com {} ou consent_enabled=false retorna reviewed=false, reason=opted_out, decision=null antes de qualquer provider. Na golden ativada, exige plano e evento autorizado:

~~~json
{"consent_enabled":true,"plan_snapshot":{"decision":{"label":"iPhone","total_price_cents":1000000,"upfront_cents":200000,"installment_count":12,"interest_free":true,"purchase_month":"2025-11-01","first_due_date":"2025-11-10"}},"event":{"event_id":"golden-1","kind":"demo_purchase_posted","offer_ref":"golden-extra-1000"}}
~~~

golden-extra-1000 acrescenta compra **SIMULADA de R$ 1.000**, definida no servidor e contabilizada uma vez no mês do evento (referência setembro). Não altera preço/condições do plano nem vira despesa recorrente. O contexto é recarregado e recalculado. O retorno preserva reviewed, reason e decision; a análise derivada fica nas evidências da decisão, sem envelope adicional de chat. Se faltarem condições de cotação, reason=needs_confirmation; sem plano: 422 golden_plan_snapshot_required; outro evento: 403 golden_event_not_authorized. confirmed_context opcional segue a referência fixa.

Fora da golden, o evento anterior demo-iphone permanece em demo própria; não é intercambiável com golden-extra-1000. Repetir requisição recalcula da base original, sem acumular o gasto entre chamadas. Não há registro durável de eventos; o cliente evita cards repetidos por event_id. Desligar = consent_enabled=false e nenhum disparo posterior. Sem jobs, notificações, movimentação real ou memória entre dispositivos.

## Segurança, operação e evidências

Cloud Run deve permanecer privado, com invocadores autorizados; identidade fixa não é autenticação bancária multicliente. Input/output guardrails, allowlist de tools, schemas e SQL parametrizado permanecem. Model Armor selecionado falhando retorna erro; provider local não promete cobertura universal de jailbreak.

Logs JSON: IDs opacos request/sessão, modelo, tools, duração, uso quando disponível, safety/status e erros classificados. Sem extrato, mensagem completa, ID sintético ou credenciais. Headers: X-Request-ID e Cache-Control: no-store. Não ativar captura de conteúdo ADK/SDK. python -m backend ouve 0.0.0.0:$PORT (8080 padrão); para local, HOST=127.0.0.1. CORS/frontend continuam fora desta rodada.

**VERIFICADO anteriormente por Antigravity:** revisão pingo-backend-00001-l22 no [Cloud Run privado](https://pingo-backend-575520783518.us-central1.run.app), health/chat com Gemini e BigQuery reais; evidência em work/cloud-run-smoke.json e STATUS-CORE. **A golden nova foi validada nesta continuação em HTTP local com BigQuery/Gemini reais**, oito turnos e Supervisor/replay PASS; não está publicada. ADC/TLS resolvidos. Nova revisão bloqueada na leitura IAM ancestral 403, sem alterações de permissões. Detalhes: EXECUCAO_GOLDEN_REAL_2026-09-27.md; contrato para frontend: FRONTEND_INTEGRATION.md.

Smoke de servidor offline já configurado:

~~~powershell
./.venv/Scripts/python.exe scripts/smoke_golden.py --base-url http://127.0.0.1:8080 --expect-agent demo --expect-data golden_fixture
~~~

Para providers reais, usar --expect-agent gemini --expect-data bigquery. O script não recebe token: proxy autorizado pode ajudar no diagnóstico de Cloud Run privado, mas aceite de nova revisão também exige smoke autenticado direto na URL HTTPS. Resultados consolidados: STATUS-CORE, EVAL_REPORT e GOLDEN_EVAL_REPORT.
