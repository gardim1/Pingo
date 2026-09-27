# Pingo — explicação arquitetural (componentes, integrações e decisões técnicas)

Atualizado em 2026-09-27. Este documento cobre o entregável "explicação arquitetural" do edital da Batalha de Agentes (bloco de 50% de peso "arquitetura/engenharia/dados", `docs/WORKSHOP_REQUIREMENTS.md`). É o companheiro técnico de [`DESENHO_SOLUCAO.md`](DESENHO_SOLUCAO.md): onde aquele documento explica a solução em nível de camadas, este detalha componente por componente — arquivo por arquivo — quais integrações cada um faz e por que foi construído daquela forma. Toda referência de arquivo/linha foi conferida no código nesta data.

## 1. Inventário de componentes

```
frontend/src/                     React 18 + TypeScript 5 (SPA servida pelo Vite/Express)
  App.tsx                         Roteamento de tela, DESIGN_NOTES, estado de Supervisor/consentimento
  components/HomeScreen.tsx       Home bancária simulada + atalho flutuante do Pingo
  components/LoadingScreen.tsx    Tela de transição com spinner acessível
  components/ConsentScreen.tsx    Consentimento progressivo (fixo + opcional)
  components/ChatScreen.tsx       Conversa, cards de fatos/comparação/simulação/plano
  components/FolgaChart.tsx       SVG animado observado-vs-simulação
  components/SupervisorSheet.tsx  Bottom sheet de opt-in do Supervisor
  components/FlowMap.tsx          Navegação das 12 etapas (rota de apresentação)
  api/client.ts                   Cliente HTTP para o proxy Node (nunca para o backend direto)
  types/pingo.ts                  Espelho TypeScript do contrato Pydantic/JSON Schema

frontend/server/                  Node/Express (camada S2S)
  index.ts                        Rotas /api/pingo/*, remove user_id/persona_key do cliente
  auth.ts                         Google ID token via Metadata Server (fallback gcloud local)

backend/api/                      FastAPI (orquestração)
  main.py                         Rotas HTTP, middleware de observabilidade, exception handlers
  runtime.py                      Autorização, ToolExecutor, safety, seleção de provider de dados
  golden_config.py                Configuração/validação da identidade sintética golden

backend/agent/                    Integração com o LLM
  intent.py                       AgentInstruction (schema estrito), extração determinística de termos
  provider.py                     DemoAgentProvider (offline) / GeminiADKProvider (produção)

backend/core/                     Motor determinístico (sem I/O)
  finance.py                      Aritmética de centavos, parcelamento, projeção de saldo
  decision.py                     Montagem de cenários e perguntas obrigatórias
  golden.py                       Análise estatística e template de resposta da golden persona
  context_contract.py             Protocolo ContextProvider e FinancialContext
  demo_context.py                 Provider de fixture própria (offline)

backend/data/                     Acesso a dados (único ponto de I/O externo além do LLM)
  bigquery_context.py             Adaptador BigQuery real (dry-run, parametrizado, com teto de bytes)
  golden_context.py               Modelos/validação do snapshot golden
  golden_fixture.py               Leitura de fixture de teste (proibida sob K_SERVICE)
  historical_context.sql          SQL fixo do modo legado
  golden_context.sql              SQL fixo do modo golden

backend/safety/                   Guardrails de entrada/saída
  types.py                        Protocolo SafetyProvider, SafetyAction, SafetyResult
  local.py                        LocalSafetyProvider (regex determinístico, sempre disponível)
  model_armor.py                  ModelArmorSafetyProvider (Google Model Armor via REST)

backend/models/                   Contratos Pydantic (StrictModel, extra="forbid")
  decision.py                     DecisionRequest/Response, ConfirmedContext, ScenarioOut
  conversation.py                 ChatResponse, GoldenAnalysis, PlanRequest, AccompanimentResponse

contracts/                        JSON Schema (fonte de verdade do contrato, versionado "1.0")
  decision-response.schema.json
  accompaniment-response.schema.json
```

## 2. Fluxo de uma requisição de chat, ponta a ponta

1. **Browser → Node/Express** (`frontend/src/api/client.ts` → `frontend/server/index.ts`): o navegador chama `/api/pingo/chat` no próprio host do frontend. Nenhuma credencial Google trafega até aqui.
2. **Node/Express → FastAPI privado**: `frontend/server/auth.ts` monta o cabeçalho `Authorization: Bearer <Google ID token>` obtido via Metadata Server (produção) ou `gcloud auth print-identity-token` (desenvolvimento), com audience fixada na URL do backend (`TARGET_AUDIENCE`, default `https://pingo-backend-uahbqqbh3a-uc.a.run.app`). O proxy sobrescreve/remove qualquer `user_id`/`persona_key` vindo do corpo do cliente antes de repassar.
3. **Middleware `observe`** (`backend/api/main.py:34-50`): gera/propaga `request_id`, mede duração, e registra em log estruturado apenas metadados (session_id, modelo, ferramentas chamadas, safety provider) — nunca o conteúdo da mensagem.
4. **Rota `/api/chat`** (`backend/api/main.py:126-200`): valida o payload contra `DecisionRequest` (Pydantic `StrictModel`), chama `authorize()` para resolver a identidade real a partir de `persona_key` (nunca aceita um `user_id` literal do cliente), instancia `ToolExecutor` e invoca o provider de agente.
5. **Guardrail de entrada** (`backend/api/runtime.py`, `inspect_input`): a mensagem do usuário é inspecionada pelo `SafetyProvider` ativo antes de qualquer chamada ao modelo ou à ferramenta. Uma detecção `BLOCK` interrompe o fluxo com zero chamadas de ferramenta e zero consulta a dado (comprovado pelos casos "05 — Prompt injection" e "15 — SQL injection" em `docs/EVAL_REPORT.md`).
6. **Agente** (`backend/agent/provider.py`): `GeminiADKProvider` monta um `LlmAgent` com o texto do usuário e o histórico de sessão, chama o Gemini e recebe de volta um `AgentInstruction` estruturado (`tool`, `intent`, `explanation_style`) — nunca texto livre financeiro.
7. **`ToolExecutor.call()`** (`backend/api/runtime.py:115-138`): valida que a ferramenta pedida está no catálogo fechado de três nomes, valida que os argumentos batem com `EmptyToolArgs` (ou seja, vazios — o modelo não pode enviar parâmetros de negócio), verifica o orçamento de 4 chamadas, e executa `get_financial_context` (carrega `FinancialContext` do provider de dados apropriado) ou `simulate_options`/`ask_purchase_terms` (chama `golden_decision()` ou `decide()` do motor determinístico).
8. **Motor determinístico** (`backend/core/decision.py`, `backend/core/finance.py`, `backend/core/golden.py`): calcula parcelas, projeção de saldo e, no modo golden, a análise estatística de margem — sempre em centavos inteiros, sempre a partir de `FinancialContext` já carregado, nunca a partir de um número que o modelo tenha proposto.
9. **Montagem da resposta** (`explain()`, `render_golden()`): o backend monta o texto final a partir de templates parametrizados pelos números do motor — este é o único texto que existe como candidato a ser mostrado ao usuário.
10. **Guardrail de saída** (`validate_output`, `backend/api/runtime.py:96-101`): o texto montado no passo 9 é reenviado ao `SafetyProvider` com `OutputContext(trusted_text=<o mesmo texto>)`. Uma divergência entre o que seria mostrado e o que o guardrail espera vira `BLOCK` (`output_guard_rejected`).
11. **Resposta desce**: FastAPI retorna `ChatResponse` (validado contra o modelo Pydantic) → Node/Express repassa ao browser → `ChatScreen.tsx` decide quais cards renderizar de acordo com as flags do objeto de decisão (`decision.question`, `golden_analysis`, etc.), sem calcular nada.

## 3. Integrações externas e como cada uma é isolada

### 3.1 Google ADK / Gemini
**Onde**: `backend/agent/provider.py`, classe `GeminiADKProvider`.
**Como**: `LlmAgent` + `Runner` + `InMemorySessionService` do pacote `google.adk`; modelo fixado por variável de ambiente `GEMINI_MODEL` (produção usa `gemini-3.8-flash`), `GOOGLE_CLOUD_LOCATION=global` para a API, `temperature=0`, `max_output_tokens=2048` (elevado de 512 depois que a jornada real revelou truncamento por `FinishReason.MAX_TOKENS` — `docs/EXECUCAO_GOLDEN_REAL_2026-09-27.md`), timeout de 30 segundos, telemetria `ContentCapturingMode.NO_CONTENT` (conteúdo de prompt/resposta não é capturado em telemetria).
**Validações de segurança no construtor**: o provider recusa-se a instanciar se o projeto configurado não for `batalha-time-08-g7ha` ou se o nome do modelo não começar com `gemini-` — bloqueando por construção qualquer tentativa de apontar o runtime para OpenAI/Anthropic ou para outro projeto GCP.
**Camada de fallback offline**: `DemoAgentProvider` implementa o mesmo protocolo de provider sem chamar rede nenhuma, usado em testes e no modo `AGENT_PROVIDER=demo` — permite que toda a suíte de 147 testes e 41 avaliações rode sem custo/latência de rede e sem dependência de credencial.

### 3.2 BigQuery
**Onde**: `backend/data/bigquery_context.py`, classe `BigQueryContextProvider`.
**Como**: projeto e localização fixados por configuração (`batalha-time-08-g7ha` / `us-central1`), tabela única e imutável no código (`hackathon_dados.extrato_sintetico`), duas queries fixas (`historical_context.sql` / `golden_context.sql`) com parâmetros nomeados. Todo `SELECT` é precedido por um `dry-run` que estima o custo antes de rodar; `maximum_bytes_billed=1073741824` (1 GiB) é aplicado tanto no dry-run quanto na execução real; timeout de job de 20 segundos, sem retries automáticos.
**Validação de resultado**: a resposta é convertida em modelos Pydantic estritos (`_Monthly`, `_Category`, `_Recurrence`, `_Installment`, `_Aggregates`) que validam finitude, precisão decimal, sinal e tamanho de lista antes de virar `FinancialContext` — um resultado malformado do BigQuery vira erro explícito (`bigquery_invalid_result`), nunca é silenciosamente aceito.
**Allowlist de identidade**: `authorized_users` é um mapeamento alias→ID copiado na construção do provider (para impedir mutação posterior); o identificador real do usuário nunca é aceito como parâmetro livre vindo do request.

### 3.3 Model Armor (opcional, não ativado em produção nesta data)
**Onde**: `backend/safety/model_armor.py`, classe `ModelArmorSafetyProvider`.
**Como**: chamadas REST diretas (`google-auth` + `requests`, sem o SDK `google-cloud-modelarmor`) para `:sanitizeUserPrompt` e `:sanitizeModelResponse` na região `us-central1`, com `enableMultiLanguageDetection=true` e `sourceLanguage=pt`. Suporta dois modos de enforcement (`INSPECT_ONLY`, `INSPECT_AND_BLOCK`) e trata qualquer falha de transporte/timeout/schema como `ERROR` explícito — nunca reclassifica uma falha do serviço gerenciado como aprovação.
**Estado real**: a tentativa de criar o template `pingo-safety` no projeto do evento foi negada (a UI do console mostrava o botão "Criar modelo" desabilitado — `docs/GCP_PREFLIGHT.md`), portanto a produção roda com `SAFETY_PROVIDER=local`. O adaptador está implementado e testado como unidade (40 testes em `tests/test_safety.py`, substituindo apenas o transporte HTTP), mas rotulado explicitamente como **IMPLEMENTADO NÃO TESTADO na nuvem** — distinção que o próprio handoff insiste em manter (`docs/MODEL_ARMOR_HANDOFF.md`).

### 3.4 Cloud Run Metadata Server (autenticação S2S)
**Onde**: `frontend/server/auth.ts`.
**Como**: em produção, o servidor Node consulta o Metadata Server interno do Cloud Run para obter um Google ID token cuja audience é a URL exata do backend privado; em desenvolvimento local, cai para `gcloud auth print-identity-token`. O backend, por sua vez, valida esse token na borda do Cloud Run (IAM invoker check habilitado, sem `allUsers`/`allAuthenticatedUsers`) — `/health` anônimo responde 403, autenticado responde 200 (verificado em produção, `docs/STATUS-CORE.md`).

## 4. Decisões técnicas e suas justificativas

| # | Decisão | Onde no código | Justificativa |
|---|---|---|---|
| D1 | Identidade sempre resolvida no servidor via `authorize(persona_key)`, nunca aceita como `user_id` literal do cliente | `backend/api/runtime.py`, `ToolExecutor.__init__` | Impede que qualquer cliente (ou o próprio modelo) selecione os dados de outro usuário; testado no caso "06 — Acesso a outro usuário" (HTTP 403) |
| D2 | Ferramentas do agente recebem `EmptyToolArgs` — zero parâmetros de negócio vindos do modelo | `backend/agent/intent.py:17`, `backend/api/runtime.py:118-121` | O modelo escolhe *qual* ferramenta chamar, nunca *com quê*; elimina uma classe inteira de prompt-to-parameter injection |
| D3 | Orçamento fixo de 4 chamadas de ferramenta por decisão | `backend/api/runtime.py:122-123` | Limite determinístico de custo/latência, independente de quão "verboso" o modelo tente ser |
| D4 | `REQUIRED_TERMS` como tupla fixa de 4 campos obrigatórios antes de calcular qualquer cenário | `backend/core/decision.py:14-19` | Formaliza que perguntar antes de responder não é uma escolha de tom de conversa, é uma pré-condição de cálculo — sem preço/entrada/parcelas/data não há projeção possível |
| D5 | `available_balance_cents` e `scheduled_cashflows` sempre vazios/`None` quando vindos do histórico agregado | `backend/data/bigquery_context.py`, confirmado em `docs/BIGQUERY_HANDOFF.md` | A coluna de saldo não é lida pela consulta; em vez de inferir um saldo a partir de médias, o sistema propaga a ausência de dado como `null` até a UI, que trata isso como estado `insufficient_data` |
| D6 | SQL fixo e parametrizado, nunca concatenado, com dry-run + teto de 1 GiB obrigatórios | `backend/data/*.sql`, `backend/data/bigquery_context.py` | Elimina SQL injection por construção e torna o custo de qualquer consulta limitado antes da execução, não depois |
| D7 | Saída do agente restrita a um schema Pydantic estrito (`AgentInstruction`) em vez de texto livre | `backend/agent/intent.py:11-14` | Torna estruturalmente impossível o modelo produzir, como saída direta, uma frase com número financeiro que seria repassada ao usuário |
| D8 | Guardrail de saída só aceita como `trusted_text` um texto já montado pelo backend a partir do resultado do engine | `backend/api/runtime.py:96-101`, reforçado em `docs/MODEL_ARMOR_HANDOFF.md` | Uma comparação do texto do modelo contra ele mesmo não prova nada; comparar contra um texto de origem controlada é o que torna o guardrail uma fronteira real, não decorativa |
| D9 | `K_SERVICE` (variável presente apenas dentro do Cloud Run) desativa fixtures e o agente demo | `backend/data/golden_fixture.py`, `docs/BIGQUERY_HANDOFF.md` | Impede estruturalmente que uma falha de BigQuery/Gemini em produção seja mascarada por dado sintético — o processo publicado literalmente não tem esse caminho de código disponível |
| D10 | Duas camadas de safety atrás do mesmo protocolo (`SafetyProvider`), trocáveis por variável de ambiente | `backend/safety/types.py`, `local.py`, `model_armor.py` | Defesa em profundidade: a camada local determinística nunca é removida, mesmo quando/se Model Armor for habilitado; uma indisponibilidade do serviço gerenciado não elimina toda proteção |
| D11 | Contratos JSON Schema com `additionalProperties: false` e enums fechados, espelhados manualmente em Pydantic (`StrictModel`, `extra="forbid"`) e TypeScript | `contracts/*.json`, `backend/models/*.py`, `frontend/src/types/pingo.ts` | Barata defesa contra campos extras contrabandeados; força qualquer mudança de contrato a ser uma mudança de arquivo versionado, revisável em diff |
| D12 | Token de identidade Google obtido só no servidor Node (Metadata Server), nunca no navegador | `frontend/server/auth.ts` | Um ID token exposto no bundle JS anularia a garantia de backend privado; a fronteira de confiança fica no processo Node, que roda em ambiente controlado |
| D13 | Cálculo monetário 100% em Python, em centavos inteiros, com o frontend proibido de fazer contas de dinheiro | `backend/core/finance.py`; regra reforçada em `docs/FRONTEND_FINAL.md` | Fonte única de verdade monetária; elimina divergência de arredondamento entre camadas e concentra toda a lógica financeira em código testável isoladamente |
| D14 | `data_mode`/`runtime.data`/`golden_analysis.data_source` como três sinais independentes de proveniência, em vez de um único campo | `backend/models/decision.py`, `backend/models/conversation.py` | Permite distinguir "o contrato diz que é dado de evento" de "o provider realmente usado foi BigQuery" de "a evidência específica veio de consulta real vs. snapshot fornecido" — os relatórios de avaliação usam essa granularidade para nunca afirmar mais integração real do que foi de fato exercitada |

## 5. Observabilidade e o que deliberadamente não é logado

O middleware `observe` (`backend/api/main.py:34-50`) registra por requisição: `request_id`, `session_id`, duração, modelo do agente, lista de ferramentas chamadas e o provider de safety ativo. O guardrail de segurança, por sua vez, registra fase, provider, ação e motivo — nunca o prompt, a resposta financeira, extrato ou token (regra explícita em `docs/MODEL_ARMOR_HANDOFF.md`, seção "Logs, limites e rollback"). O exception handler de validação (`validation_error`, `backend/api/main.py:52-57`) explicitamente descarta o corpo do input do usuário antes de compor a resposta de erro, para que um payload malformado não vaze de volta dados sensíveis via mensagem de erro.

## 6. Limites arquiteturais conhecidos e assumidos

- **Sem persistência durável.** Planos salvos e o estado do Supervisor vivem em snapshots de sessão (`backend/models/conversation.py`, `SavedPlan`); não há banco de dados de aplicação, fila de mensagens ou notificação real — decisão de escopo do hackathon, documentada em `docs/execucao_v2/PINGO_Execucao_v2/01_ESPECIFICACAO.md` ("Fora do corte principal: notificações reais, monitoramento bancário em produção").
- **Um único modelo, uma única chamada por decisão de ferramenta.** Não há orquestração multiagente nem chamadas paralelas ao Gemini; o orçamento de 4 chamadas é por sessão de decisão, não um mecanismo de retry sofisticado.
- **Model Armor gerenciado não está validado em produção** (seção 3.3) — a superfície de guardrail real e testada em produção é exclusivamente `LocalSafetyProvider`.
- **Leitura de política IAM da pasta ancestral do projeto ficou bloqueada** durante a validação de publicação (403 em `folders/900300571186:getIamPolicy`); a ausência de grants públicos foi confirmada nos níveis de serviço e projeto, mas não no nível de pasta — limite registrado e não escondido (`docs/STATUS-CORE.md`).
- **Sincronização manual de contrato entre Pydantic e TypeScript.** Não há geração automática de tipos a partir de `contracts/*.json`; qualquer mudança de contrato exige atualizar três lugares (`contracts/`, `backend/models/`, `frontend/src/types/pingo.ts`) manualmente.

## 7. Referências cruzadas

Camadas e disciplinas (arquitetura/engenharia/ciência de dados) em nível de solução: [`DESENHO_SOLUCAO.md`](DESENHO_SOLUCAO.md). Racional de experiência e critérios de UX: [`RACIONAL_EXPERIENCIA.md`](RACIONAL_EXPERIENCIA.md). Especificação completa da golden persona e regras de classificação de dados: [`GOLDEN_PERSONA.md`](GOLDEN_PERSONA.md). Contrato de API detalhado turno a turno: [`FRONTEND_INTEGRATION.md`](FRONTEND_INTEGRATION.md) e [`API_BACKEND.md`](API_BACKEND.md). Estado de implantação vivo e evidências de execução real: [`STATUS-CORE.md`](STATUS-CORE.md), [`BIGQUERY_HANDOFF.md`](BIGQUERY_HANDOFF.md), [`MODEL_ARMOR_HANDOFF.md`](MODEL_ARMOR_HANDOFF.md).
