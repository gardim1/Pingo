# BigQuery — adaptador histórico e golden persona

Atualizado em 2026-09-27. **VERIFICADO na revisão anterior:** integração BigQuery e Gemini pelo backend publicado, conforme execução Antigravity registrada em STATUS-CORE e work/cloud-run-smoke.json. **VERIFICADO agora no Google:** dry-run e consulta golden reais, job `9f752879-64f2-4e0c-80f8-56a0233dfc0c`, 51.377.364 bytes; seis salários de 675499 centavos e três parcelas totalizando 69078 centavos. Jornada local Gemini/BigQuery completa PASS. Nova publicação ainda bloqueada; ver EXECUCAO_GOLDEN_REAL_2026-09-27.md.

**VERIFICADO localmente nesta frente:** 17 testes anteriores do adapter + 21 testes golden = **38 PASS**, com SDK real e cliente falso. ADC/TLS agora verificados com confiança nativa do Windows. O bloqueio de publicação é separado: leitura da política IAM da pasta ancestral negada com 403. Não alterar IAM nem desabilitar TLS. Os testes com cliente falso continuam sendo testes locais; a evidência real é o job e o smoke citados acima.

## Interface preservada e ativação

O modo anterior permanece default:

~~~python
from datetime import date
from backend.data.bigquery_context import BigQueryContextProvider

legacy = BigQueryContextProvider(
    authorized_users=trusted_backend_alias_to_id,
    reference_date=date.today(),
)
context = legacy.get_context(backend_bound_persona)
~~~

Golden acrescenta opt-in explícito e referência obrigatória:

~~~python
golden = BigQueryContextProvider(
    authorized_users=trusted_backend_alias_to_id,
    reference_date=date(2025, 9, 30),
    golden_persona=True,
)
context = golden.get_context(backend_bound_persona)
snapshot = context.historical_summary['golden']
~~~

get_context(persona_key) -> FinancialContext e get_financial_context(user_id, reference_date) permanecem. Ambas verificam a allowlist; o mapa é copiado para impedir mutação posterior. Tools não recebem identidade, SQL, tabela ou opções de consulta. Allowlist não substitui autenticação por cliente.

Configuração golden real da API, somente no servidor:

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

Golden vincula persona-a ao único ID sintético autorizado. O request pode omitir persona_key, mas não usar outro alias. ID/data diferentes ou configuração incompleta são recusados. Nesse modo, PINGO_AUTHORIZED_USERS não seleciona outra pessoa; o fluxo anterior continua usando PINGO_BOUND_PERSONA/PINGO_AUTHORIZED_USERS. Não imprimir mapas ou IDs em logs.

DEMO_MODE=true não implica fixture: DATA_PROVIDER=bigquery consulta BigQuery. Offline exige DATA_PROVIDER=golden_fixture explicitamente. load_golden_fixture() lê somente tests/fixtures/golden_persona.json, com origin=user_supplied_hackathon_snapshot; não é fallback. Com K_SERVICE, golden exige BigQuery + Gemini e o loader recusa fixture. A fixture não integra a imagem.

DecisionResponse.data_mode=event_dataset_demo preserva o enum v1 de origem sintética. No chat golden, runtime.data=bigquery ou golden_fixture identifica o provider; golden_analysis.data_source=dataset_observed ou user_supplied_hackathon_snapshot identifica a evidência. O enum v1 sozinho não comprova query.

## Contexto entregue ao engine

FinancialContext.historical_summary continua opcional. Schemas compartilhados de resposta não foram alterados; os 103 testes anteriores integram a regressão preservada. Ambos os modos retornam available_balance_cents=None, protected_buffer_cents=None e scheduled_cashflows=[]. A API pode complementar dados confirmados sem promover histórico a posição atual; na golden, confirmações usam referência 2025-09-30.

**Modo anterior:** fonte/origem/referência/cobertura, contagem, até 12 agregados mensais e 12 categorias/direções, 10 recorrências candidatas e 12 grupos de parcelas. currency=null e montantes *_units continuam strings decimais; a unidade não foi confirmada para todo o dataset. Recorrências exigem confirmação e parcelas não geram agenda futura.

**Golden:** context.historical_summary['golden'] contém:

~~~text
reference_date: "2025-09-30"
currency: "BRL"
origin: "dataset_observed" | "user_supplied_hackathon_snapshot"
monthly: [{month, salary_cents: int|null, expenses_excluding_invoice_cents,
           flexible_cents: int|null, interest_cents}]
installments: [{label, amount_cents, current, total, last_observed_date,
                estimated_end_date, requires_confirmation: true}]
categories: [{category, amount_cents}]
limitations: [string]
~~~

BRL foi confirmado pelo usuário para esta persona. A query fornece valores/datas; código converte Decimal em centavos e estima término mensal com shift_months_clamped. Não existem constantes monetárias do snapshot no caminho real. A fixture não inventa contagem de registros ou datas originais: last_observed_date=null, términos estimados apenas conforme o anexo. Query real exige data observada. Descrições livres/IDs não saem do BigQuery; rótulos de parcela são predefinidos. Categorias externas são dados não confiáveis, nunca instruções.

O engine calcula comparação histórica condicional ancorada em setembro, com volatilidade e hipóteses explícitas. Médias não são saldo. Ver [GOLDEN_PERSONA.md](GOLDEN_PERSONA.md) e [API_BACKEND.md](API_BACKEND.md) para proveniência, campos opcionais interest_free/purchase_month, golden_analysis e plano/Supervisor.

## Fonte, consultas e limites

Tabela fixa: batalha-time-08-g7ha.hackathon_dados.extrato_sintetico, us-central1. O provider rejeita outro projeto/localização; não aceita tabela por ambiente/request. O diagnóstico anterior documenta 467.585 lançamentos, 1.000 usuários, janeiro–dezembro de 2025 e 29.847 lançamentos com marcadores de parcela em 992 usuários. Não foram repetidas consultas exploratórias nesta rodada.

Schema necessário: id_usuario STRING, anomesdia TIMESTAMP, tipo STRING, descr STRING, vlr FLOAT, nom_cate_macro STRING, nom_cate_micro STRING, parcela_atual FLOAT e parcela_total FLOAT. **saldo_apos não é consultado.**

| Modo | SQL fixo | Recorte |
|---|---|---|
| Anterior | backend/data/historical_context.sql | Histórico de 2025 até referência, agregação geral/candidatos |
| Golden | backend/data/golden_context.sql | Abril–setembro; seis meses, até 12 categorias e 12 parcelas individuais de setembro |

Ambos usam parâmetros user_id/reference_date/coverage_start/coverage_end, dry-run antes do SELECT, estimativa obrigatória e maximum_bytes_billed=1073741824 (1 GiB). Timeout RPC/resultado de 20 segundos, job_timeout_ms=20000, sem retries, cancelamento best-effort e um resultado agregado limitado a 50 mil caracteres. Timeout/cancelamento não garante cessação instantânea; LIMIT não limita bytes lidos. [Parâmetros](https://docs.cloud.google.com/bigquery/docs/parameterized-queries), [custos](https://docs.cloud.google.com/bigquery/docs/best-practices-costs), [QueryJobConfig](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.QueryJobConfig).

Cada vlr é arredondado em duas casas e convertido para NUMERIC antes de somar. Python valida finitude, precisão, sinal, campos, datas e tamanho das listas. Na golden, meses ausentes não viram zero; truncamento acima de 12 categorias/parcelas é declarado.

Regras golden a validar contra a fonte:

- Salário: apenas E com microcategoria ou descrição normalizada exatamente salario clt. Sem correspondência, salary_cents=null; nunca toda entrada.
- Despesas/categorias: saídas excluindo microcategoria Pagamento de fatura. Visão de despesas, não conciliação completa; transferências não são removidas por inferência.
- Juros: microcategoria Juros pagos, documentada no diagnóstico; zero representa ausência observada nessa classificação.
- Flexíveis: null no runtime até definição verificada. O anexo fornece totais, mas não a regra; fixture conserva esses valores.
- Parcelas: saídas de setembro com índice atual menor que total; datas/valores futuros são estimativas a confirmar.

## Validação real no ambiente autorizado

Não publicar nem alterar permissões para contornar falha. Verificar identidade/projeto/ADC sem imprimir tokens ou ler credenciais para a conversa:

~~~bash
gcloud auth list --filter=status:ACTIVE --format='value(status)'
gcloud config get-value project
python - <<'PY'
import google.auth
from google.auth.transport.requests import Request
try:
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    credentials.refresh(Request())
except Exception as exc:
    print({'status': 'BLOQUEADO', 'error_type': type(exc).__name__})
    raise SystemExit(1) from None
print({'adc_valid': credentials.valid, 'project': project})
PY
~~~

Projeto esperado: batalha-time-08-g7ha. Projeto ADC não informado não autoriza usar outro projeto: o adapter fixa o projeto do evento. Usuário conclui login/MFA; Cloud Run usa identidade aprovada e ADC, sem chave JSON. TLS inválido exige correção de confiança. Um 403 real posterior exige diagnóstico próprio, sem alteração IAM automática. [ADC](https://docs.cloud.google.com/docs/authentication/application-default-credentials).

Se necessário, conferir somente metadados já conhecidos:

~~~bash
bq --project_id=batalha-time-08-g7ha show --format=prettyjson batalha-time-08-g7ha:hackathon_dados | python -c 'import json,sys; d=json.load(sys.stdin); print({"location":d.get("location")})'
bq --project_id=batalha-time-08-g7ha show --schema --format=prettyjson batalha-time-08-g7ha:hackathon_dados.extrato_sintetico
~~~

Na raiz do projeto com dependências e variáveis golden configuradas, executar o próprio adapter (um dry-run e um SELECT):

~~~bash
python - <<'PY'
import os
from backend.api.golden_config import (
    validate_golden_config, GOLDEN_ALIAS, GOLDEN_USER_ID, GOLDEN_REFERENCE_DATE,
)
from backend.data.bigquery_context import BigQueryContextProvider, DataProviderError

validate_golden_config()
assert os.environ['DATA_PROVIDER'] == 'bigquery'
provider = BigQueryContextProvider(
    authorized_users={GOLDEN_ALIAS: GOLDEN_USER_ID},
    reference_date=GOLDEN_REFERENCE_DATE, golden_persona=True,
)
try:
    context = provider.get_context(GOLDEN_ALIAS)
except DataProviderError as exc:
    print({'status': 'BLOQUEADO', 'code': exc.code})
    raise SystemExit(1)
history = context.historical_summary
golden = history['golden']
assert golden['origin'] == 'dataset_observed'
assert context.available_balance_cents is None and context.scheduled_cashflows == []
print({'status': 'VERIFICADO_ADAPTER', 'reference_date': golden['reference_date'],
       'coverage': history['coverage'], 'months': len(golden['monthly']),
       'installments': len(golden['installments']),
       'salary_identified_all_observed_months': bool(golden['monthly']) and all(
           item['salary_cents'] is not None for item in golden['monthly']),
       'balance_stays_unknown': True})
PY
~~~

Esse resultado comprova somente execução do adapter. Comparar seis meses, três parcelas, datas estimadas e totais com o snapshot; registrar divergências sem extrato/ID/descrições. Se CLT não corresponder, inspecionar só os agregados/rótulos necessários para ajustar o critério fixo com evidência. Não trocar por toda entrada, codificar resultados esperados no SQL ou inventar definição de flexíveis. SQL corrigido exige novo dry-run.

Depois executar o backend com providers reais e, em outro terminal:

~~~bash
python scripts/smoke_golden.py --base-url http://127.0.0.1:8080 --expect-agent gemini --expect-data bigquery
~~~

O smoke exige jornada, valores do snapshot, recálculo e Supervisor; HTTP 200 sozinho não basta. Não recebe tokens. Proxy autorizado ajuda no diagnóstico de Cloud Run privado, mas o aceite da nova revisão também exige URL HTTPS autenticada direta, conforme ANTIGRAVITY_HANDOFF. A revisão anterior é evidência anterior, não golden validada.

## Evidências locais e falhas explícitas

Executado nesta frente em 2026-09-27:

~~~powershell
./.venv/Scripts/python.exe -m pytest tests/test_data.py tests/test_golden_data.py -q
# 38 passed: 17 anteriores + 21 golden.
~~~

Cobertura: identidade/SQL injection, dry-run/limites, permissão/timeout, ausência de fallback, centavos, histórico vazio, referência fixa, salário desconhecido, estimativas de data, resultados diferentes da fixture e fixture proibida no Cloud Run. SDK real, cliente falso; não valida SQL remoto. Contagens globais/evals: STATUS-CORE, EVAL_REPORT e GOLDEN_EVAL_REPORT; reexecutar antes da publicação.

Erros internos: bigquery_sdk_missing, bigquery_estimate_unavailable, bigquery_budget_exceeded, bigquery_unavailable e bigquery_invalid_result; identidade fora da allowlist gera DataAccessDenied. A fronteira HTTP sanitiza falhas do provider como bigquery_unavailable, sem mensagens/argumentos SDK. Fixture tem falhas explícitas próprias e nunca é recuperação automática.

Registrar somente estado/código, duração, cobertura e job/bytes quando disponíveis no ambiente autorizado. Sem credenciais, descrições, IDs ou extrato. Permissões esperadas: criar jobs no projeto e ler a tabela permitida; sem criar tabela/view/export. Sem Pub/Sub, BigQuery Graph, Spanner ou Security Command Center.

Próxima ação: concluir refresh ADC com TLS válido, executar o adapter golden e comparar o snapshot; testar a jornada real antes da nova revisão privada. Não alterar IAM nem declarar a extensão validada sem essa evidência.
