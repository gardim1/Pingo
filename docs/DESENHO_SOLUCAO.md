# Pingo — desenho da solução (arquitetura, engenharia e ciência de dados)

Atualizado em 2026-09-27. Este documento cobre o entregável "desenho de solução" do edital da Batalha de Agentes, dentro do bloco de 50% de peso "arquitetura/engenharia/dados" (`docs/WORKSHOP_REQUIREMENTS.md`). Descreve como o sistema é construído de ponta a ponta, por que cada camada existe, e como as três disciplinas — arquitetura, engenharia de software e ciência de dados — se encaixam no mesmo produto. Todas as afirmações foram verificadas contra o código-fonte e contra os relatórios de execução em `docs/` nesta data; estados de infraestrutura citam a evidência específica que os comprova.

## 1. Visão geral

O Pingo é um agente conversacional que responde "o que acontece com o meu mês se eu fizer esta compra agora?" combinando três ingredientes que nunca se misturam livremente: **contexto financeiro real do usuário** (BigQuery ou contexto confirmado na conversa), **cálculo determinístico em Python** (nunca em JavaScript no navegador, nunca gerado pelo modelo de linguagem) e **um agente Gemini via Google ADK** que apenas interpreta a intenção do usuário e escolhe qual ferramenta chamar — nunca gera números financeiros que cheguem ao usuário sem passar pelo motor determinístico.

```
Browser (React/Vite)
  → Node/Express (frontend/server) — proxy S2S, obtém Google ID token
    → FastAPI privado (backend/api) — autoriza identidade, orquestra o agente
      → Google ADK + Gemini (backend/agent) — classifica intenção, escolhe ferramenta
      → Engine determinístico (backend/core) — calcula dinheiro e datas em centavos
      → BigQuery (backend/data) — contexto histórico agregado, read-only
      → Guardrails (backend/safety) — inspeciona entrada e saída
```

Esta cadeia é a mesma para toda solicitação: não existe um caminho alternativo em que o frontend calcule algo sozinho, nem um caminho em que a resposta do modelo alcance o usuário sem ser validada contra um texto controlado pelo servidor.

## 2. Arquitetura — as camadas e por que existem

### 2.1 Frontend como cliente sem lógica financeira
`frontend/src/` é React 18 + TypeScript 5 + Vite 6. Ele não faz nenhuma conta de dinheiro: todos os valores exibidos (salário, margem, parcelas, comparações) vêm de respostas de API já calculadas (regra explícita em `docs/FRONTEND_FINAL.md`, seção "Regra Fundamental"). A única lógica local é a apresentação (animação do `FolgaChart`, gating de qual card mostrar conforme flags da mensagem) e um simulador "E se" client-side que recalcula um gráfico de 12 meses usando apenas os números que a API já retornou — não é uma fonte nova de verdade, é uma reapresentação interativa de dados já obtidos (achado do agente de exploração sobre `ChatScreen.tsx`, seção "wfValues").

**Justificativa arquitetural**: manter toda aritmética monetária em um único processo Python elimina uma classe inteira de bugs de arredondamento/duplicação de regra de negócio entre front e back, e é o requisito mais repetido em toda a documentação do projeto (README, STATUS-CORE, ANTIGRAVITY_HANDOFF, GCP_PREFLIGHT).

### 2.2 Node/Express como fronteira de autenticação S2S
`frontend/server/index.ts` e `frontend/server/auth.ts` implementam um servidor Express que fica entre o navegador e o backend privado. O navegador nunca vê um token do Google: o servidor Node obtém um Google ID token com audience igual à URL do Cloud Run do backend, via **Cloud Run Metadata Server** em produção, com fallback para `gcloud auth print-identity-token` em desenvolvimento local (`frontend/server/auth.ts`, função `getBackendHeaders()`). Além disso, o proxy remove explicitamente qualquer `user_id`/`persona_key` que o cliente tente enviar antes de repassar a chamada ao backend (achado documentado no resumo de `frontend/server/index.ts`).

**Justificativa arquitetural**: o backend precisa ficar privado (sem `allUsers`/`allAuthenticatedUsers` no IAM do Cloud Run) para que a identidade do usuário nunca seja um parâmetro que o cliente controla. Colocar a obtenção do token no servidor, não no navegador, é o que torna essa privacidade seguível na prática — um token de ID do Google exposto no bundle JS anularia a garantia.

### 2.3 FastAPI privado como orquestrador único
`backend/api/main.py` expõe `/health`, `/api/demo/personas`, `/api/decision`, `/api/decision/review`, `/api/chat` e `/api/accompaniment/review`. Um middleware `observe` registra `request_id`, `session_id`, modelo, ferramentas chamadas e provider de safety para cada requisição, sem registrar corpo de mensagem, prompt ou extrato (`backend/api/main.py`). Toda montagem de contexto e execução de ferramenta passa por `backend/api/runtime.py`, nunca diretamente pelas rotas.

### 2.4 Camada de agente: Google ADK + Gemini, com saída estruturada obrigatória
`backend/agent/provider.py` implementa `GeminiADKProvider`, que usa `LlmAgent`, `Runner` e `InMemorySessionService` do Google ADK para orquestrar uma chamada ao Gemini (`gemini-3.8-flash`, `temperature=0`, `max_output_tokens=2048`, timeout de 30s). A saída do modelo é forçada a validar contra o schema Pydantic `AgentInstruction` (`backend/agent/intent.py`) — um objeto estrito com `tool` (uma das três ferramentas permitidas), `intent` e `explanation_style`, sem espaço para texto livre financeiro. O provider valida explicitamente que o projeto é `batalha-time-08-g7ha` e que o modelo começa com o prefixo `gemini-`, rejeitando qualquer configuração de fallback para OpenAI/Anthropic (`backend/agent/provider.py`).

**Justificativa arquitetural**: o LLM é tratado como um classificador de intenção com saída tipada, não como um gerador de conteúdo final. Isso é o que torna possível a garantia "o modelo nunca inventa um valor financeiro que chega ao usuário" — porque estruturalmente o modelo não tem um canal de saída livre para números.

### 2.5 Catálogo fechado de ferramentas e orçamento de chamadas
`ToolExecutor` (`backend/api/runtime.py:104-138`) expõe exatamente três ferramentas — `get_financial_context`, `simulate_options`, `ask_purchase_terms` — e rejeita qualquer outra com `tool_not_allowed` (HTTP 400). Cada chamada de ferramenta tem seus argumentos validados contra `EmptyToolArgs`, ou seja, **o modelo não pode passar parâmetros de negócio para a ferramenta** (nem identidade, nem SQL, nem valores) — os parâmetros reais vêm exclusivamente do `DecisionRequest` já validado e da identidade já autorizada no servidor. Um orçamento fixo de 4 chamadas por sessão de decisão bloqueia loops (`tool_budget_exceeded`).

**Justificativa arquitetural**: isso elimina duas classes de risco simultaneamente — model-controlled parameter injection (o modelo não pode pedir dados de outro usuário porque não pode nem passar um `user_id`) e custo/latência descontrolados (o orçamento de chamadas limita o "raciocínio" do agente).

### 2.6 Motor financeiro determinístico
`backend/core/finance.py` faz toda aritmética em **centavos inteiros**, nunca em ponto flutuante: `split_installments()` distribui um valor total em N parcelas sem perda de centavos (o resto é distribuído nas primeiras parcelas — por isso R$ 8.000 em 12x vira 8 parcelas de R$ 666,67 e 4 de R$ 666,66, conforme documentado em `docs/STATUS-CORE.md`), `shift_months_clamped()` desloca datas por mês preservando o dia quando possível, `build_schedule()` monta o cronograma de cobranças e `project()` simula o saldo mínimo dentro de uma janela e classifica o resultado em três estados: `insufficient_data`, `meets_declared_constraints_in_window`, `violates_declared_constraints_in_window`. `backend/core/decision.py` consome esse motor para montar até 2 cenários (a opção informada + uma hipótese de "esperar") e decide se falta alguma informação obrigatória, consultando a tupla fixa `REQUIRED_TERMS` (preço total, entrada, quantidade de parcelas, data da primeira cobrança).

**Justificativa arquitetural**: nenhuma dessas contas é delegada ao modelo nem ao navegador. O motor é uma função pura, testável isoladamente (ver seção 4), e o estado `insufficient_data` é uma classificação de primeira classe — o sistema é desenhado para admitir explicitamente "não sei" em vez de inferir um saldo que não foi informado.

### 2.7 Camada de dados: dois adaptadores atrás de uma interface única
`backend/core/context_contract.py` define o protocolo `ContextProvider` com um único método (`get_context`) e a estrutura imutável `FinancialContext`. Três implementações concretas satisfazem esse protocolo: `OwnSyntheticDemoProvider` (fixture local para desenvolvimento offline), `BigQueryContextProvider` (produção, ver seção 5) e a leitura de fixture golden isolada para testes (`backend/data/golden_fixture.py`, que recusa operar quando a variável de ambiente `K_SERVICE` está presente — ou seja, é estruturalmente impossível essa fixture rodar dentro de um serviço publicado no Cloud Run). O motor de decisão (`decision.py`/`golden.py`) nunca importa um adaptador de dados diretamente — apenas consome `FinancialContext`.

**Justificativa arquitetural**: trocar a fonte de dados (fixture → BigQuery real) não exige mudar uma linha do motor de cálculo ou dos testes que exercitam o motor. Essa é a razão pela qual a mesma suíte de 147 testes unitários continua válida entre modo offline e modo de produção.

### 2.8 Guardrails de segurança em duas camadas independentes
`backend/safety/local.py` (`LocalSafetyProvider`) aplica regras determinísticas via regex — políticas versionadas (`POLICY_VERSION = "pingo-local-v2"`) para injeção de prompt, jailbreak, pedido de segredo, acesso cross-user, sobreposição de identidade, SQL arbitrário e chamada de ferramenta não autorizada na entrada; e um conjunto de padrões de saída insegura na resposta. `backend/safety/model_armor.py` (`ModelArmorSafetyProvider`) é uma camada adicional opcional que chama a API REST do Google Model Armor (`sanitizeUserPrompt`/`sanitizeModelResponse`) — as duas camadas implementam o mesmo protocolo `SafetyProvider` (`backend/safety/types.py`) e podem ser trocadas por configuração (`SAFETY_PROVIDER=local|model_armor`) sem alterar o restante do sistema.

O guardrail de saída (`validate_output`, `backend/api/runtime.py:96-101`) só é chamado sobre **texto renderizado pelo backend a partir de um template**, nunca sobre prosa livre do modelo — o parâmetro `OutputContext.trusted_text` deve ser exatamente o texto que será mostrado, nunca vindo do modelo, do snapshot do cliente ou de descrição bruta do dataset (regra explícita em `docs/MODEL_ARMOR_HANDOFF.md`). Isso é verificado pelo caso de avaliação "11 — Output inconsistente"/"22 — Saída financeira divergente", que confirmam `BLOCK` quando um número alterado ou uma frase sem proveniência tenta passar pela fronteira.

**Justificativa arquitetural**: defesa em profundidade — mesmo que o LLM fosse convencido a produzir uma frase com um número financeiro inventado, essa frase nunca é o texto que chega ao guardrail de saída, porque o texto que chega ao guardrail já foi montado pelo backend a partir do resultado do motor determinístico.

## 3. Engenharia de software

### 3.1 Contratos versionados e validação estrita
O contrato de resposta (`contracts/decision-response.schema.json`, JSON Schema draft 2020-12) fixa `contract_version: "1.0"` como constante, restringe `state` a um enum fechado (`needs_input`, `ready`, `limited`, `blocked`, `error`), limita `scenarios` a no máximo 3 itens e usa `additionalProperties: false` em todos os objetos aninhados — qualquer campo extra quebra a validação. `backend/models/decision.py` e `backend/models/conversation.py` espelham esse contrato em Pydantic usando uma classe base `StrictModel` com `extra="forbid"` em todos os modelos de entrada, incluindo os que recebem dados potencialmente influenciáveis pelo modelo ou pelo cliente. `frontend/src/types/pingo.ts` replica as mesmas formas em TypeScript, mantendo os dois lados do contrato sincronizados manualmente (não há geração automática de tipos a partir do schema nesta base).

**Justificativa de engenharia**: `extra="forbid"` é uma defesa barata contra tentativas de contrabandear campos não previstos (por exemplo, um `user_id` alternativo) através do corpo de uma requisição ou de uma resposta do modelo.

### 3.2 Pirâmide de testes
| Camada | Ferramenta | Resultado mais recente | Evidência |
|---|---|---|---|
| Testes unitários | `pytest` (`tests/test_finance.py`, `test_data.py`, `test_golden_data.py`, `test_agent.py`, `test_api.py`, `test_chat.py`, `test_context_safety.py`, `test_safety.py`, `test_evals.py`, `test_golden_chat.py`) | 147 passed | `docs/STATUS-CORE.md` |
| Avaliações comportamentais (legado) | `python -m scripts.evaluate` | 18 PASS / 0 FAIL | `docs/EVAL_REPORT.md` |
| Avaliações comportamentais (golden) | `python -m scripts.evaluate_golden` | 23 PASS / 0 FAIL | `docs/GOLDEN_EVAL_REPORT.md` |
| Smoke HTTP local | `scripts/smoke_golden.py` | 9 etapas PASS | `docs/GOLDEN_EVAL_REPORT.md` |
| Smoke HTTPS autenticado em produção | script ad-hoc com token de identidade real | PASS (candidata e canônica) | `docs/STATUS-CORE.md`, `work/golden-cloud-smoke-*.json` |
| Smoke E2E de frontend em produção | verificação HTTP real pós-deploy | PASS | `docs/FRONTEND_FINAL.md`, `work/frontend-smoke-evidence.json` |

Os relatórios de avaliação (`EVAL_REPORT.md`, `GOLDEN_EVAL_REPORT.md`) são gerados por execução real do harness, não escritos à mão — o cabeçalho de cada um documenta explicitamente o comando que os produziu e a limitação de cada modo (MOCK/DEMO, FAULT INJECTION, VERIFICADO LOCAL), incluindo uma frase padronizada deixando claro que nenhum caso ali prova acesso real a Gemini/BigQuery/Model Armor — essa prova vem separadamente dos relatórios de execução real (`BIGQUERY_HANDOFF.md`, `EXECUCAO_GOLDEN_REAL_2026-09-27.md`).

### 3.3 Casos de falha tratados como cidadãos de primeira classe
Casos de avaliação explícitos cobrem: erro do modelo (Gemini indisponível → HTTP 503 `gemini_unavailable`, sem decisão-fallback), erro do BigQuery (→ HTTP 503 `bigquery_unavailable`, sem fixture-fallback), tentativa de acesso a outro usuário (→ HTTP 403, zero dados retornados), injeção de prompt e SQL injection (→ `blocked`, zero ferramentas executadas), tool guard (ferramenta fora do catálogo ou com argumentos → rejeitada com `tool_not_allowed`/`tool_arguments_rejected`, zero execução), e falha do Model Armor (→ `ERROR` explícito, nunca convertido silenciosamente em sucesso local) — todos com PASS registrado em `docs/EVAL_REPORT.md` e `docs/GOLDEN_EVAL_REPORT.md`.

**Justificativa de engenharia**: em um produto financeiro, uma falha silenciosa (fallback para dado fictício sem aviso) é pior do que uma falha visível. O padrão consistente do código é: indisponibilidade de uma dependência externa vira um erro HTTP explícito e sanitizado, nunca um valor inventado.

### 3.4 Correção mínima e cirúrgica como prática registrada
O histórico de execução documenta pelo menos duas correções desse tipo: (a) `backend/agent/provider.py`, `max_output_tokens=512 → 2048`, depois que a jornada golden real revelou `FinishReason.MAX_TOKENS` truncando o JSON de saída do Gemini (`docs/EXECUCAO_GOLDEN_REAL_2026-09-27.md`); (b) cinco achados de revisão independente corrigidos e cobertos por 23 testes de regressão adicionais — confusão parcela/preço total, parsing malformado de `R$10.0000`, múltiplas datas ambíguas, limpeza assíncrona do cliente ADK, e atualização não reconhecida preservando termos obsoletos (`docs/REVIEW_BACKEND.md`). Em ambos os casos a mudança de código foi mínima e a suíte completa foi reexecutada antes de aceitar a correção.

## 4. Ciência de dados

### 4.1 Fonte e escopo dos dados
Uma única tabela é usada em produção: `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`, região `us-central1` (`backend/data/bigquery_context.py`). O diagnóstico documentado registra 467.585 lançamentos, 1.000 usuários, cobertura janeiro–dezembro de 2025, com 29.847 lançamentos com marcador de parcela distribuídos em 992 usuários (`docs/BIGQUERY_HANDOFF.md`). O schema esperado é `id_usuario`, `anomesdia`, `tipo`, `descr`, `vlr`, `nom_cate_macro`, `nom_cate_micro`, `parcela_atual`, `parcela_total` — **não existe uma coluna de saldo pós-transação usada pela consulta** (`saldo_apos não é consultado`), o que é a razão estrutural pela qual `available_balance_cents` é sempre `None` no contexto histórico: o dado simplesmente não é lido, não é uma limitação de cálculo.

### 4.2 Duas consultas SQL fixas, nunca livres
`backend/data/historical_context.sql` (modo legado, agregação geral do histórico de 2025) e `backend/data/golden_context.sql` (modo golden, recorte abril–setembro de 2025 com até 12 categorias e 12 parcelas individuais de setembro) são os dois únicos SQLs que o sistema executa. Ambos usam parâmetros nomeados (`user_id`, `reference_date`, `coverage_start`, `coverage_end`) — nunca concatenação de string — e passam por **dry-run obrigatório antes do `SELECT` real**, com teto de `maximum_bytes_billed=1073741824` (1 GiB), timeout de job de 20 segundos e sem retries (`backend/data/bigquery_context.py`). Não existe caminho de código que aceite SQL vindo do request, do modelo ou de variável de ambiente por usuário — o SQL é um arquivo versionado no repositório.

**Justificativa de ciência de dados/segurança**: fixar o SQL e parametrizar valores elimina SQL injection por construção, e o teto de bytes faturáveis limita o custo de qualquer consulta individual de forma determinística, antes mesmo dela rodar (o dry-run existe exatamente para isso).

### 4.3 Regras de classificação e por que são conservadoras
| Métrica | Regra aplicada | Consequência quando a regra não bate |
|---|---|---|
| Salário CLT | Apenas lançamentos de entrada cuja microcategoria ou descrição normalizada seja exatamente `"salario clt"` | `salary_cents = null` — nunca "toda entrada" vira salário |
| Despesas/categorias | Saídas excluindo a microcategoria `"Pagamento de fatura"` | É uma visão de despesas, não uma conciliação completa; transferências não são removidas por inferência |
| Juros | Microcategoria `"Juros pagos"` | Zero representa ausência observada nessa classificação, não "sem juros confirmado" |
| Gastos flexíveis | Regra de cálculo não fornecida pelo evento | Permanece `null` no runtime real; a fixture local preserva valores de exemplo, mas isso é documentado como não-regra |
| Parcelas ativas | Saídas de setembro com índice de parcela atual menor que o total | Datas/valores futuros de parcelas são estimativas a confirmar, nunca uma agenda garantida |

Essas regras estão documentadas e replicadas em `docs/GOLDEN_PERSONA.md` e `docs/BIGQUERY_HANDOFF.md`, e o próprio handoff de dados recomenda validar o rótulo `"salario clt"` contra a tabela real antes de generalizar a regra — ou seja, a equipe de dados tratou a regra de classificação como uma hipótese testável, não como verdade assumida.

### 4.4 Da consulta agregada à análise estatística da golden persona
`backend/core/golden.py` (`analyze_golden`) processa os agregados mensais retornados pelo adaptador BigQuery e calcula: margem de cada mês observado (`margin()`), média simples dos últimos meses (`mean()`), a liberação condicional de caixa esperada quando as parcelas ativas terminam (`release()`), e uma tabela de comparação histórica mês a mês entre a liberação condicional e uma margem de referência (benchmark). O resultado alimenta o objeto `GoldenAnalysis`, que carrega explicitamente `assumptions: string[]` — premissas textuais que acompanham todo número apresentado (por exemplo, que a comparação de novembro assume que os demais componentes do mês se repetem).

Os números centrais desta persona, verificados por consulta real ao BigQuery (job `9f752879-64f2-4e0c-80f8-56a0233dfc0c`, 51.377.364 bytes processados — `docs/BIGQUERY_HANDOFF.md`): salário CLT de R$ 6.754,99/mês em 6 meses observados (abril–setembro/2025), 3 parcelas ativas somando R$ 690,78/mês (Passagem aérea R$ 244,01, IPTU R$ 411,09, Artigos infantis R$ 35,68), margem de setembro de −R$ 576,85, liberação condicional projetada de R$ 113,93 quando as parcelas terminam em outubro (`docs/GOLDEN_PERSONA.md`, `docs/STATUS-CORE.md`).

**Justificativa de ciência de dados**: a "análise" aqui é deliberadamente simples (médias, diferenças, comparação condicional) e não um modelo preditivo/estatístico complexo — a escolha reflete o critério de que qualquer número mostrado ao usuário precisa ser auditável por uma pessoa lendo o SQL e a fórmula, não uma saída de caixa-preta. Toda média é explicitamente rotulada como "não é saldo, é histórico" tanto no código de premissas quanto na cópia de UI (documentado em `RACIONAL_EXPERIENCIA.md`, seção 4).

### 4.5 Limites de dados declarados explicitamente
`backend/data/bigquery_context.py` mantém uma lista `LIMITATIONS` retornada junto ao contexto, e a suíte de avaliação golden verifica que o saldo permanece `null` mesmo com histórico completo (`G08 — Saldo desconhecido`, `docs/GOLDEN_EVAL_REPORT.md`). O histórico de 2025 nunca é tratado como renda futura garantida, crédito aprovado ou agenda de cobrança completa — essas são afirmações textuais repetidas em pelo menos quatro documentos (`BIGQUERY_HANDOFF.md`, `STATUS-CORE.md`, `GOLDEN_EVAL_REPORT.md`, `ANTIGRAVITY_HANDOFF.md`), o que indica que é uma decisão de produto deliberada, não um esquecimento de uma única frente.

## 5. Estado de implantação (infraestrutura) nesta data

| Componente | Estado verificado | Evidência |
|---|---|---|
| Backend Cloud Run | Revisão `pingo-backend-00003-cup`, 100% de tráfego, `https://pingo-backend-uahbqqbh3a-uc.a.run.app`, privado (`/health` anônimo → 403, autenticado → 200) | `docs/STATUS-CORE.md` |
| Frontend Cloud Run | Revisão `pingo-frontend-00002-7fv`/`00001-wr8`, 100% de tráfego, S2S autenticado por Google ID token via Metadata Server | `docs/STATUS-CORE.md`, `docs/FRONTEND_FINAL.md` |
| BigQuery real | Dry-run + consulta real, job `9f752879-...` e `1b99463a-...`, dentro do teto de 1 GiB | `docs/BIGQUERY_HANDOFF.md`, `docs/STATUS-CORE.md` |
| Gemini real | `gemini-3.8-flash`, jornada de 8 turnos, todos `FinishReason.STOP`, sem invenção de dado financeiro | `docs/STATUS-CORE.md` |
| Model Armor remoto | **Não ativado.** Criação de template negada (403) no preflight; `SAFETY_PROVIDER=local` permanece a configuração de produção | `docs/MODEL_ARMOR_HANDOFF.md`, `docs/GCP_PREFLIGHT.md` |
| Leitura de IAM ancestral (`folders/900300571186`) | Bloqueada (403 `IAM_PERMISSION_DENIED`) durante a validação; ausência de grants públicos confirmada nos níveis de serviço e projeto antes da promoção | `docs/STATUS-CORE.md`, `docs/EXECUCAO_GOLDEN_REAL_2026-09-27.md` |

Serviços explicitamente fora do escopo por restrição do evento e não utilizados nesta base: Cloud Pub/Sub, BigQuery Graph, Cloud Spanner, Security Command Center (`docs/WORKSHOP_REQUIREMENTS.md`, reafirmado em todos os handoffs de infraestrutura).

## 6. Decisões de trade-off explícitas

| Decisão | Alternativa descartada | Por quê |
|---|---|---|
| Cálculo em centavos inteiros no backend | Ponto flutuante ou cálculo no frontend | Elimina erro de arredondamento e garante fonte única de verdade monetária |
| LLM como classificador de intenção com saída tipada | LLM gerando a resposta final em texto livre | Torna estruturalmente impossível o modelo "inventar" um valor financeiro que chega ao usuário sem passar pelo motor |
| Catálogo fechado de 3 ferramentas sem argumentos do modelo | Ferramentas genéricas parametrizáveis pelo modelo | Remove a superfície de ataque de injeção de parâmetro/identidade pela conversa |
| Dois SQLs fixos e versionados | Query builder dinâmico | Elimina SQL injection por construção e torna toda consulta auditável no diff do repositório |
| Saldo/renda futura sempre `null` quando não confirmados | Inferir saldo a partir da média histórica | Evita apresentar uma estimativa como fato financeiro num domínio sensível |
| Duas camadas de safety independentes (`local` sempre ativo, `model_armor` opcional) | Depender só do guardrail gerenciado do Google | Garante que uma falha/indisponibilidade do serviço gerenciado não remove toda a proteção |
| Fixture golden proibida quando `K_SERVICE` está presente | Permitir fixture em produção como fallback de emergência | Impede que uma falha de BigQuery em produção seja mascarada silenciosamente por dado sintético |

## 7. Referências cruzadas

Detalhamento componente-a-componente, integrações e justificativas técnicas linha a linha: [`ARQUITETURA.md`](ARQUITETURA.md). Racional de experiência e critérios de UX: [`RACIONAL_EXPERIENCIA.md`](RACIONAL_EXPERIENCIA.md). Especificação de dados da golden persona: [`GOLDEN_PERSONA.md`](GOLDEN_PERSONA.md). Contrato de API para consumo do frontend: [`FRONTEND_INTEGRATION.md`](FRONTEND_INTEGRATION.md). Estado de implantação vivo: [`STATUS-CORE.md`](STATUS-CORE.md).
