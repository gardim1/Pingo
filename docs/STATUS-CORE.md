# Status do core Pingo

Atualizado em **2026-09-27**. **Nova revisão Golden PUBLICADA e PROMOVIDA no Cloud Run (`pingo-backend-00003-cup`, 100% de tráfego) com BigQuery e Gemini 3.8 Flash reais. FRONTEND FINAL CONSTRUÍDO E PUBLICADO NO CLOUD RUN (`pingo-frontend-00002-7fv`, 100% de tráfego) COM S2S PRIVADO AUTENTICADO POR GOOGLE ID TOKEN, ROTA `/` DIRETA NO PRODUTO E CHAT DINÂMICO.**

## Continuação executada — 27/09/2026 (QA Fix, Nova Imagem, Candidata e Promoção)

1. **Correção Mínima Obrigatória de QA (WARN resolvido — PASS):**
   - Eliminado prefixo `"Recalculei a comparação para o mês que você escolheu"` quando o usuário ainda não escolheu outro mês (ex.: turno "10 vezes sem juros").
   - Esclarecido que as 3 parcelas observadas terminam em outubro de 2025 (`10/2025`); setembro observado é de -R$ 576,85 e as parcelas ativas somam R$ 690,78/mês.
   - Cenário de esperar até novembro (`11/2025`) utiliza exclusivamente valores calculados pelo engine determinístico: +R$ 113,93 antes da compra e -R$ 886,07 após a maior parcela do iPhone (10x de R$ 1.000,00). Nenhum número hardcoded.
   - Removida duplicação textual da hipótese de "entrada zero" na resposta.
   - 147 testes unitários PASS (`pytest -q`).
   - 41 avaliações PASS (18 legados em `scripts.evaluate` + 23 golden em `scripts.evaluate_golden`).

2. **Validação Local de Integração Real:**
   - BigQuery real com ADC validado via dry-run e query real (job `1b99463a-66e6-4566-913b-ebe99fa4ccf0`): 6 meses, salário CLT R$ 6.754,99, 3 parcelas totalizando R$ 690,78/mês.
   - Gemini real `gemini-3.8-flash` via ADK testado na jornada completa com 13 requisições HTTP 200, finish_reason `STOP` em todos os turnos.
   - Confirmado que nenhum valor financeiro é gerado pelo LLM (cálculos 100% realizados pelo engine determinístico em Python e validados por guardrail local de output).

3. **Cloud Build da Nova Imagem:**
   - Build ID: `81f6b821-c096-4d3b-aa09-4ae216014fcc` (STATUS: SUCCESS).
   - Imagem gerada: `us-central1-docker.pkg.dev/batalha-time-08-g7ha/agentes/pingo-backend:golden-20260927081802`.
   - Digest: `sha256:1258edb92301cf065dc93b7452c69d5629ae439100652042cf627acd996746b0`.

4. **Publicação da Revisão Candidata com Zero Tráfego:**
   - Revisão criada: `pingo-backend-00003-cup` com tag `golden`.
   - Tráfego inicial: 0% para a nova revisão (100% mantido na revisão preexistente `pingo-backend-00001-l22`).
   - Service Account preservada: `squad-agent-sa@batalha-time-08-g7ha.iam.gserviceaccount.com`.
   - Ingress preservado: `all` com invoker IAM habilitado.
   - URL da candidata com tag: `https://golden---pingo-backend-uahbqqbh3a-uc.a.run.app`.

5. **Smoke HTTPS Autenticado da Candidata (Zero Tráfego):**
   - `/health` anônimo: HTTP 403 (acesso privado comprovado).
   - `/health` e `/docs` autenticados: HTTP 200.
   - Jornada Golden completa de 8 turnos de chat com BigQuery e Gemini 3.8 Flash reais: HTTP 200.
   - Acompanhamento / Supervisor com opt-out, compra simulada de R$ 1.000 e replay idempotente: HTTP 200.
   - Evidência gravada: `work/golden-cloud-smoke-20260927T112324172869.json` (RESULT: PASS).

6. **Promoção de Tráfego para 100%:**
   - Tráfego migrado: 100% para `pingo-backend-00003-cup`.
   - URL canônica em produção: `https://pingo-backend-uahbqqbh3a-uc.a.run.app`.

7. **Smoke HTTPS Repetido na URL Canônica Pós-Promoção:**
   - `/health` anônimo: HTTP 403.
   - `/health`, `/docs`, 8 turnos de chat e 3 turnos de acompanhamento/review: todos HTTP 200.
   - Evidência gravada: `work/golden-cloud-smoke-20260927T112439391185.json` (RESULT: PASS).

8. **Limitação Registrada (sem bloqueio de deploy):**
   - Leitura de política IAM ancestral em `folders/900300571186:getIamPolicy` retornou 403 `PERMISSION_DENIED` (`IAM_PERMISSION_DENIED`). Acesso privado ao serviço verificado via IAM no serviço e no projeto (chamadas anônimas rejeitadas com 403; chamadas autenticadas aceitas com 200). Nenhum grant público no serviço ou projeto.

## Resultado da Publicação Golden

| Item | Estado e evidência |
|---|---|
| QA Fix | **VERIFICADO: OK** (sem prefixo indevido, termos de novembro calculados pelo engine, término das parcelas em outubro, sem duplicação de texto). |
| Testes Unitários | **VERIFICADO: 147 passed** (`pytest -q`). |
| Evals | **VERIFICADO: 41 passed** (18 legados + 23 golden). |
| Cloud Build | **VERIFICADO: `81f6b821-c096-4d3b-aa09-4ae216014fcc` SUCCESS**. Imagem `golden-20260927081802`. |
| Revisão Cloud Run | **VERIFICADO: `pingo-backend-00003-cup`**. 100% de tráfego. |
| URL Canônica | **`https://pingo-backend-uahbqqbh3a-uc.a.run.app`** |
| URL Tag Golden | **`https://golden---pingo-backend-uahbqqbh3a-uc.a.run.app`** |
| Golden BigQuery | **VERIFICADO REAL**: 6 meses, salário CLT R$ 6.754,99, 3 parcelas totalizando R$ 690,78/mês, saldo null. |
| Gemini Real | **VERIFICADO REAL**: `gemini-3.8-flash` com ADK, turnos concluídos com STOP, sem invenção de dados financeiros. |
| Smoke Cloud Run | **VERIFICADO: PASS** (tanto na candidata zero-tráfego quanto na canônica com 100% de tráfego). |
| Bloqueio Restante | **NENHUM**. Apenas a limitação de leitura IAM da pasta ancestral `folders/900300571186` registrada. |

**Persona derivada da base sintética do hackathon. Não representa cliente real do Itaú.** Fonte, cálculos e limitações: [GOLDEN_PERSONA.md](GOLDEN_PERSONA.md). Interface: [API_BACKEND.md](API_BACKEND.md).

## Publicação anterior — evidência preservada

**CLOUD RUN DEPLOYED, versão anterior: VERIFICADO na evidência existente**, não reexecutado nesta rodada. O usuário informou a publicação concluída. `work/cloud-run-smoke.json`, lido nesta rodada, registra PASS em **2026-09-27T02:24:38Z**: health autenticado 200, anônimo 403 e dois chats 200 com Gemini `gemini-3.8-flash`, safety local e engine ready. O status recebido registra adapter BigQuery real com 836 transações agregadas do perfil anteriormente autorizado. O rótulo legado `event_dataset_demo` pertence ao contrato; a golden passa a identificar explicitamente o provider real em `runtime.data=bigquery`.

- URL registrada: **https://pingo-backend-575520783518.us-central1.run.app**.
- Projeto/região: `batalha-time-08-g7ha` / `us-central1`.
- Serviço/revisão: `pingo-backend` / `pingo-backend-00001-l22`; tráfego registrado de 100%.
- Runtime SA: `squad-agent-sa@batalha-time-08-g7ha.iam.gserviceaccount.com`.
- Cloud Build: `ae8047cc-ac61-4b9f-b00f-11549aa69441`.
- Imagem: `us-central1-docker.pkg.dev/batalha-time-08-g7ha/agentes/pingo-backend:latest`.
- Digest: `sha256:8c3a17599a992ad3c7785d55541fe67873b469458acbd5b5f87dd909287b7988`.

Revalidar o estado remoto antes de publicar; esses dados não são inspeção atual do tráfego. Não sobrescrever o smoke anterior. **Cloud Run continua obrigatório: a atualização golden só estará entregue após nova revisão implantada, URL real, GET /health e jornada golden com providers reais nessa URL. Handoff não substitui execução.**

## Verificação executada após as correções

```powershell
.\.venv\Scripts\python.exe -m pytest -q
# 147 passed, 1 warning (Starlette/httpx já existente)
.\.venv\Scripts\python.exe -m pip check
# No broken requirements found.
.\.venv\Scripts\python.exe -m scripts.evaluate
# 18 PASS / 0 FAIL
.\.venv\Scripts\python.exe -m scripts.evaluate_golden
# 23 PASS / 0 FAIL
.\.venv\Scripts\python.exe work/deploy_entrypoint_smoke.py
# HOST=0.0.0.0 / PORT=18768; health/docs/decision/review/chat 200; PASS
```

Smoke golden em servidor temporário `127.0.0.1:8871`, usando `scripts/smoke_golden.py --expect-agent demo --expect-data golden_fixture`: **PASS, nove etapas**, incluindo oito turnos, agenda datada, opt-out, Supervisor e replay. Processo temporário encerrado; servidores preexistentes preservados. São testes de HTTP/processo Python, **não smoke de imagem Docker nova nem providers Google**. Logs finais em `work/golden-final-legacy-evals.txt` e `work/golden-final-evals.txt` (ignorados).

A revisão independente reexecutou 23 testes de conversa/compatibilidade, sem achados abertos nos casos verificados. Casos corrigidos/cobertos: negação de juros/à vista, ano explícito, alternativas de mês, texto de outubro, data passada, título inseguro e `DATA_PROVIDER=demo` legado.

## Comportamento e limites

- Runtime golden real: `DEMO_MODE=true`, `DATA_PROVIDER=bigquery`, `AGENT_PROVIDER=gemini`, `DEMO_USER_ID=6491f4a4-67dc-49de-a38a-cf655ff77c33`, `DEMO_REFERENCE_DATE=2025-09-30`. DEMO_MODE identifica a demonstração sintética; não decide sozinho a fonte. BigQuery selecionado permanece BigQuery em caso de erro.
- Offline exige `golden_fixture`/`demo` explicitamente. Fixture em `tests/fixtures/` excluída da imagem/upload; `K_SERVICE` impede fixture/agente demo no modo golden publicado.
- Contexto mínimo agregado; ID, extrato e descrições livres não vão ao Gemini/resposta. SQL novo classifica CLT conservadoramente, **ainda sem validação na tabela**. Flexíveis no runtime real são null porque a regra não foi fornecida.
- Engine calcula dinheiro e datas. R$ 8.000 / 12 resulta em **8 parcelas de R$ 666,67 e 4 de R$ 666,66**. São condições informadas pelo usuário, não ofertas de loja/banco.
- Comparação condicional usa a composição de setembro: -R$ 576,85 + R$ 690,78 = **R$ 113,93** antes da compra, se as três parcelas terminarem e os demais componentes se repetirem. Não soma a liberação à média trimestral. R$ 203,77 recente e -R$ 345,16 semestral são médias históricas, não capacidade garantida.
- Sem primeira data há cotação, não cronograma inventado. Saldo desconhecido permanece null. Histórico não confirma renda futura, crédito, quitação ou agenda completa.
- Reenviar `draft` como `decision` no próximo turno. Plano/sessão usam snapshots existentes; sem banco novo, memória longa, autenticação bancária ou notificação real.
- Supervisor reutiliza `/api/accompaniment/review`, evento `demo_purchase_posted` / `golden-extra-1000`, consentimento e plano explícitos. Impacto pontual, não recorrente; deduplicação da apresentação do card cabe ao cliente.
- Um agente Gemini/ADK e texto financeiro renderizado pelo backend. Guardrail local não garante cobertura universal. Model Armor remoto não foi usado nesta rodada; o estado recebido registrava criação negada com 403 e safety local explícito.

## Arquivos criados/alterados nesta rodada

- API/agente/modelos: `backend/api/golden_config.py`, `backend/api/runtime.py`, `backend/api/main.py`, `backend/agent/intent.py`, `backend/models/decision.py`, `backend/models/conversation.py`.
- Cálculo/dados/safety: `backend/core/golden.py`, `backend/data/bigquery_context.py`, `backend/data/golden_context.py`, `backend/data/golden_context.sql`, `backend/data/golden_fixture.py`, `backend/safety/local.py`.
- Testes/harness: `tests/fixtures/golden_persona.json`, `tests/test_golden_data.py`, `tests/test_golden_chat.py`, `scripts/evaluate.py`, `scripts/evaluate_golden.py`, `scripts/smoke_golden.py`.
- Configuração: `.dockerignore`, `.gcloudignore`, `.env.example`. Dockerfile/entrypoint já atendiam HOST/PORT/health e foram preservados. Allowlists incluem `golden_context.sql`.
- Docs: `README.md`, `docs/GOLDEN_PERSONA.md`, `docs/GOLDEN_EVAL_REPORT.md`, `docs/EVAL_REPORT.md`, `docs/API_BACKEND.md`, `docs/BIGQUERY_HANDOFF.md`, `docs/STATUS-CORE.md`, `docs/DEPLOY_HANDOFF.md`, `docs/ANTIGRAVITY_HANDOFF.md`, `docs/superpowers/plans/2026-09-27-golden-persona.md`.

## Publicação do Frontend Final — 27/09/2026 (100% Tráfego no Cloud Run)

1. **Desenvolvimento e Fidelidade Visual:**
   - Construído em `frontend/` com React 18, TypeScript 5, Vite 6 e servidor Express 4.
   - Fidelidade total ao design de referência em `frontend-reference/` (`Pingo v3.dc.html` e `uploads/pingo-grafico-folga.html`).
   - Tipografia Montserrat e Inter, paleta oficial, SVG animado `FolgaChart`, sem marcas do Itaú.
   - Mobile-first, acessível (WCAG AA), suporte a `prefers-reduced-motion` e ampliação de texto.

2. **Regra Fundamental — Nenhum Cálculo Financeiro no Browser:**
   - Frontend não calcula dinheiro: salários, margens, parcelas ativas, cotações e comparações históricas são obtidos dinamicamente da API do backend.

3. **Arquitetura S2S com Backend Privado:**
   - Browser comunica-se apenas com a camada Node.js (`/api/pingo/*`).
   - Servidor Node.js obtém Google ID token com audience `https://pingo-backend-uahbqqbh3a-uc.a.run.app` via Cloud Run Metadata Server e invoca o backend privado.
   - Nenhum token, segredo ou chave exposta ao cliente.

4. **Publicação no Cloud Run:**
   - Serviço: `pingo-frontend`
   - Revisão: `pingo-frontend-00001-wr8` (100% de tráfego)
   - URL Pública: **`https://pingo-frontend-575520783518.us-central1.run.app`**
   - Imagem: `us-central1-docker.pkg.dev/batalha-time-08-g7ha/agentes/pingo-frontend:v1-202609270847`
   - Service Account: `squad-agent-sa@batalha-time-08-g7ha.iam.gserviceaccount.com`
   - Build ID: `e4bec935-9ee9-4fb9-85da-b9a7610b7301` (SUCCESS)

5. **Smoke E2E de Produção:**
   - `/health` -> 200
   - `/api/pingo/health` (S2S ao backend privado) -> 200
   - Chat Turno 1 (pergunta iPhone 10k) -> 200
   - Chat Turno 2 (10x sem juros) -> 200 com fatos BigQuery reais e cálculos de novembro do engine
   - Supervisor opt-out -> 200
   - Entrega estática HTML -> 200
   - Evidência gravada: `work/frontend-smoke-evidence.json` (RESULT: PASS).
   - Documentação completa: `docs/FRONTEND_FINAL.md`.
