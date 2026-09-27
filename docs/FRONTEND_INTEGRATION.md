# Integração frontend — golden persona iPhone

Revisão documental em 2026-09-27. Atualização operacional: jornada local com BigQuery/Gemini reais PASS; nova revisão Cloud Run pendente por verificação de IAM ancestral bloqueada. Ver EXECUCAO_GOLDEN_REAL_2026-09-27.md. URL atual observada: https://pingo-backend-uahbqqbh3a-uc.a.run.app, ainda revisão anterior pingo-backend-00001-l22. Escopo: contratos e roteiro de integração; nenhuma chamada cloud, mudança de API/frontend/IAM ou validação de publicação feita nesta revisão. A persona é sintética, com referência fixa em **2025-09-30**. Não apresentar os dados como saldo atual de um cliente real.

## Conexão privada e estado do cliente

Usar o caminho **navegador → proxy de servidor já autorizado → Cloud Run privado**. A identidade Google e o token de invocação ficam somente no servidor. O proxy deve preservar status HTTP, JSON e `X-Request-ID`, respeitar `Cache-Control: no-store` e não registrar conteúdo financeiro ou credenciais. Não embutir token, ADC, chave JSON ou ID da persona no navegador. Reutilizar a identidade com invocação já autorizada, sem alterar IAM.

**Dependência não confirmada nesta cópia:** não há diretório `frontend/` nem implementação de proxy identificada. O responsável precisa fornecer a rota do proxy existente, sua origem e a URL Cloud Run comprovada após a publicação golden. CORS está fora desta rodada; não assumir uma chamada direta do navegador ao Cloud Run. O proxy local de diagnóstico citado em `smoke_golden.py` não comprova que o proxy do produto existe.

Não fixar a revisão anterior como golden. A URL/revisão de destino deve vir da evidência atual do deploy e do smoke HTTPS direto. Uma requisição bem-sucedida a `/health` só demonstra saúde básica.

Estado mínimo por sessão do cliente: último `draft`, mensagens exibidas, plano/condições aceitas, consentimento explícito e IDs dos eventos já exibidos. Enviar turnos sequencialmente. `session_id` muda por requisição e não oferece memória ou autenticação; `plan_id` não permite recuperar um plano no servidor. `previous_request_id` é aceito no request, mas não substitui o `draft`.

## Endpoints e payloads

Todos os POST recebem `Content-Type: application/json`. O request não inclui `user_id`; omitir `persona_key` na golden. Campos adicionais no request são rejeitados.

| Método e caminho | Entrada / saída usada |
|---|---|
| `GET /health` | `{"status":"ok"}`. Cloud Run privado continua exigindo invocação autorizada. |
| `GET /docs` | OpenAPI interativo da revisão efetiva; conferir tipos atuais. |
| `POST /api/chat` | `DecisionRequest` → `ChatResponse`; conversa e recálculo com Gemini. |
| `POST /api/decision` | `DecisionRequest` → `DecisionResponse` v1; condições estruturadas, sem Gemini. |
| `POST /api/decision/review` | `DecisionRequest` + `plan_snapshot` opcional → `DecisionResponse` v1; sem Gemini. `decision`/`preferences` explícitos prevalecem sobre o snapshot. |
| `POST /api/plan` | `DecisionRequest` + `consent_enabled:true` → snapshot para a sessão do cliente. |
| `POST /api/accompaniment/review` | Consentimento, snapshot e evento simulado → `AccompanimentResponse`. |

Primeiro turno (`POST /api/chat`):

```json
{"message":"Quero comprar um iPhone de R$ 10.000. Faz sentido agora?","decision":null}
```

Em cada turno seguinte, usar `{"message": textoDoTurno, "decision": ultimoRetorno.draft}`. O objeto enviado em `decision` é **o rascunho de condições**, não `ultimoRetorno.decision`, que contém o resultado calculado. Conservar o último rascunho válido se uma resposta bloqueada vier com `draft:null`.

`DecisionTerms` aceita somente `label` (até 160 caracteres), `total_price_cents`, `upfront_cents`, `installment_count` (1–60), `first_due_date`, `interest_free` e `purchase_month`. Valores monetários são inteiros em centavos; `interest_free` é booleano estrito; campos ausentes podem ser `null`. `purchase_month` deve ser o primeiro dia do mês e não substitui a primeira cobrança. `message` tem 1–2.000 caracteres.

Salvar as condições finais exige ação/consentimento explícito (`POST /api/plan`):

```json
{"message":"Guardar estas condições na sessão","consent_enabled":true,"decision":{"label":"iPhone","total_price_cents":1000000,"upfront_cents":200000,"installment_count":12,"first_due_date":"2025-11-10","interest_free":true,"purchase_month":"2025-11-01"}}
```

O exemplo contém as condições finais do roteiro; na integração usar o `draft` realmente retornado. A resposta traz `plan_id`, `decision`, `preferences`, `storage:"client_session_only"` e `accompaniment_enabled:false`. Salvar não ativa o Supervisor nem persistência remota. Não existe endpoint de recuperação de plano nesta API.

## Campos a renderizar

| Origem | Uso na interface |
|---|---|
| `message` do chat | Texto principal já renderizado e validado pelo backend; não inventar nova recomendação. |
| `draft` | Estado das condições para o próximo turno e o plano. Não contém prova de saldo. |
| `decision.state`, `question.field/text`, `actions` | Mostrar esclarecimento/limitações e apenas ações compatíveis. Estados: `needs_input`, `ready`, `limited`, `blocked`, `error`. |
| `decision.scenarios[]` | `title`, `total_price_cents`, `upfront_cents`, `schedule[].due_date/amount_cents`, `visible_until`, `remaining_after_window_cents` e `projection`. Lista pode estar vazia. |
| `decision.evidence[]`, `assumptions` | Exibir origem/ressalvas; `reason_evidence_ids` liga cenário às evidências. |
| `golden_analysis` | Resumo determinístico opcional; não existe no envelope do Supervisor. |
| `runtime.agent/data/model/safety` | Diagnóstico sanitizado da execução; não dados financeiros nem autenticação. |
| `session_id`, `decision.request_id/trace_id`, header `X-Request-ID` | Correlação para suporte, sem utilizá-los como sessão persistente. |

Em `golden_analysis`, consumir quando presentes: `reference_date`, `data_source`, `salary_observed_cents`, `recent_average_margin_cents`, `six_month_average_margin_cents`, `last_month_margin_cents`, `observed_installments_total_cents`, `observed_installment_count`, `estimated_last_installment_month`, `installments_cents`, `selected_month`, `selected_conditional_release_cents`, `comparisons` e `assumptions`. Campos adicionais do modelo: `simulated_purchase_cents`, `event_month_before_cents`, `event_month_after_cents`.

Cada comparação contém `month`, `conditional_release_cents`, `benchmark_margin_cents`, `margin_after_installment_min_cents` e `margin_after_installment_max_cents`. Formatar centavos em BRL apenas na apresentação; preservar negativos e `null`. Datas ISO representam datas civis: evitar conversão de fuso que altere o dia. Cotação sem vencimento usa `installments_cents`; só desenhar agenda quando o servidor devolver `scenarios[].schedule`.

`projection.min_balance_cents:null` significa **saldo desconhecido**, nunca zero. Salário/margens/comparações históricos não são saldo, crédito, renda futura garantida ou autorização de compra. O comparativo após as parcelas usa setembro como base; não somar a liberação à média trimestral.

`ChatResponse.decision`, `draft` e `golden_analysis` podem ser `null` em respostas de safety. HTTP 200 com `runtime.agent:"not_called"` não comprova Gemini. Na golden real validada, esperar `runtime.agent:"gemini"`, modelo informado, `runtime.data:"bigquery"`, `golden_analysis.data_source:"dataset_observed"` e referência `2025-09-30`. `decision.data_mode:"event_dataset_demo"` é enum legado e permanece correto; não indica uso de fixture.

## Jornada de oito turnos

Cada linha é um POST em `/api/chat`; a partir do turno 2, enviar o `draft` da resposta anterior. Valores abaixo são expectativas do smoke, **não constantes a preencher no frontend**.

| Turno | Mensagem exata | Verificação da resposta |
|---|---|---|
| 1 | Quero comprar um iPhone de R$ 10.000. Faz sentido agora? | `draft.total_price_cents=1000000`; `state=needs_input`; pergunta pagamento; cotação vazia. |
| 2 | 10 vezes sem juros | 10 × `100000`; primeira cobrança desconhecida; cenários vazios; ressalva sobre volatilidade e ausência de garantia. |
| 3 | Mas eu preciso dele agora porque trabalho com marketing. | Acolhe a necessidade profissional e pergunta sobre entrada; preservar rascunho. |
| 4 | Consigo dar R$2.000 de entrada. | `upfront_cents=200000`; 10 × `80000`. |
| 5 | Em 12 vezes sem juros. | 8 × `66667` + 4 × `66666`; parcelas + entrada = `1000000`. |
| 6 | E se eu esperar até novembro? | `purchase_month=2025-11-01`; liberação **condicional** `69078`; não inventar dia de cobrança. |
| 7 | Quero comprar mesmo assim. | Preserva autonomia; sem bloqueio motivado apenas pela escolha nem julgamento moral. |
| 8 | Primeira em 2025-11-10. | Agenda inicia em `2025-11-10`; conserva centavos; `projection.min_balance_cents=null`. |

O smoke também exige salário observado `675499`, médias de três/seis meses `20377`/`-34516`, setembro `-57685`, parcelas observadas `69078` e comparativo de novembro antes do novo aparelho `11393`. Esses números precisam vir da consulta golden real para o aceite de produção; fixture offline não basta. “Sem juros” é condição fornecida pela pessoa, não oferta confirmada de banco/loja.

## Supervisor, evento e replay

Sem opt-in, enviar `{}` ou `{"consent_enabled":false}` em `/api/accompaniment/review`: resposta exata `{"reviewed":false,"reason":"opted_out","decision":null}`. Esse retorno ocorre antes dos providers no código, mas a barreira privada do Cloud Run continua válida.

Com opt-in explícito e o rascunho final, enviar:

```json
{"consent_enabled":true,"plan_snapshot":{"decision":{"label":"iPhone","total_price_cents":1000000,"upfront_cents":200000,"installment_count":12,"first_due_date":"2025-11-10","interest_free":true,"purchase_month":"2025-11-01"}},"event":{"event_id":"golden-smoke-1","kind":"demo_purchase_posted","offer_ref":"golden-extra-1000"}}
```

O `event_id` admite 1–100 caracteres em `[A-Za-z0-9_-]`. O servidor define a compra **SIMULADA de R$ 1.000**, uma vez no mês de referência (setembro); o request não escolhe valor/data do evento. As condições/preço do iPhone continuam iguais. Resultado esperado: `reviewed:true`, `reason:"reviewed"`, `decision` v1 com mensagem marcada como simulada. Cotação incompleta pode retornar `reason:"needs_confirmation"`.

Reenviar o mesmo payload deve preservar `decision.scenarios`; não comparar a resposta inteira, pois IDs de requisição mudam. O backend recalcula da base original: não há registro durável de eventos ou deduplicação persistente por ID. O cliente evita cards duplicados por `event_id`. Ao desligar, usar `consent_enabled:false` e suspender novos disparos. Não há transação, push, job ou sincronização entre dispositivos.

## Erros e pontos pendentes de integração

- Suportar `detail` como objeto `{code,message}`, lista de validação `{loc,type,msg}` ou texto. Rejeições da plataforma/proxy podem não ser JSON. Mostrar falha explícita e preservar rascunho; não substituir por resposta mock.
- Tratar 403 de invocação/autorização, 409 `plan_consent_required`, 422 de campos ou `golden_plan_snapshot_required`/`simulated_event_required` e 503 de provider/configuração. `golden_event_not_authorized` é 403 para o evento legado permitido pelo schema; um `offer_ref` fora do enum falha na validação com 422.
- Confirmar a rota do proxy existente, autenticação da sessão de quem abre o frontend e identidade de invocação já autorizada. A persona fixa do backend não implementa autenticação bancária multicliente. Se faltar permissão, registrar bloqueio sem concedê-la.
- Confirmar a URL/revisão após o smoke real e preservar a evidência: nova revisão privada, acesso anônimo negado, health autenticado 200 e os oito turnos/evento/replay com Gemini + BigQuery. O proxy serve à integração/diagnóstico; não substitui o smoke de aceite diretamente em HTTPS.
- O envelope do chat é definido nos modelos Python e no OpenAPI; os arquivos em `contracts/` cobrem `DecisionResponse` e `AccompanimentResponse`. Confirmar se o frontend tem tipos gerados do OpenAPI atual. Não ampliar o schema v1 para encaixar o envelope do chat.
- Não há eventos individuais, categorias ou tabela mensal completa em `golden_analysis`; esses dados internos não devem ser presumidos como campos disponíveis. Usar o resumo, as evidências e as ressalvas existentes, sem pedir novos endpoints nesta rodada.
- `confirmed_context` é opcional e não participa deste smoke. Se já houver esse fluxo no frontend, usar apenas dados confirmados pela pessoa e `as_of_date:"2025-09-30"`; não converter histórico em saldo/agenda. Outra referência retorna 422. Compra de cartão exige a fatura vinculada já confirmada.

## Fontes locais conferidas

- `backend/api/main.py:34`: headers e correlação; `:126`: chat e retornos nullable; `:202`: plano; `:214`: Supervisor/replay.
- `backend/api/runtime.py:23`: erro classificado; `:33`: vínculo da identidade; `:140`: referência fixa e provider de dados.
- `backend/models/decision.py:13`: condições; `:77`: request; `:86`: snapshot não confiável; `:137`: resposta v1.
- `backend/models/conversation.py:15`: comparação; `:23`: análise golden; `:43`: envelope do chat; `:53`: plano/evento/acompanhamento.
- `contracts/decision-response.schema.json:1` e `contracts/accompaniment-response.schema.json:1`: contratos compartilhados.
- `scripts/smoke_golden.py:30`: origem/providers; `:47`: números de aceite; `:65`: oito turnos; `:108`: opt-out/evento/replay.
- `docs/API_BACKEND.md:37`: integração; `:72`: plano/Supervisor; `:92`: operação/segurança.
- `docs/GOLDEN_PERSONA.md:41`: parcelas e base condicional; `:95`: limites de classificação; `:116`: comportamento esperado.
- `docs/ANTIGRAVITY_HANDOFF.md:7`: aceite da nova revisão; `:229`: smoke HTTPS privado; `:283`: promoção/evidência. Leitura não verifica o estado cloud atual.
