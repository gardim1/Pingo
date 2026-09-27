# Pingo — validação real e bloqueio de publicação

Execução em **27/09/2026, 05:59–06:08 (America/Sao_Paulo)**, projeto `batalha-time-08-g7ha`, região Cloud Run `us-central1`.

**Golden validada localmente com BigQuery e Gemini reais. Nova revisão Cloud Run não publicada: verificação de IAM ancestral bloqueada.** Nenhuma mudança de IAM, faturamento, tráfego, conta de serviço ou acesso público foi feita.

## Resultado comprovado

| Item | Resultado |
|---|---|
| Testes e avaliações após a correção | 147 testes, 18 evals anteriores e 23 golden aprovados; dependências íntegras. Um aviso já existente de Starlette/httpx. |
| Autenticação local | ADC renovada com sucesso; validação TLS ativa usando a confiança nativa do Windows no processo temporário. Sem alteração de certificados ou dependências do produto. |
| BigQuery golden | Dry-run e consulta real aprovados. 51.377.364 bytes processados, abaixo do teto de 1 GiB. Job `9f752879-64f2-4e0c-80f8-56a0233dfc0c`. |
| Valores consultados | Seis meses com salário classificado de R$ 6.754,99; três parcelas somando R$ 690,78; saldo desconhecido preservado. SQL existente preservado. |
| Gemini na jornada | Oito turnos reais com `gemini-3.8-flash`, região `global`, `runtime.data=bigquery`, origem `dataset_observed`; todos HTTP 200. |
| Roteiro iPhone | Preço de R$ 10 mil, 10 parcelas, necessidade profissional, entrada de R$ 2 mil, 12 parcelas, espera até novembro, decisão humana e primeira cobrança em 10/11/2025. Valores, datas, conservação de centavos e saldo desconhecido conferidos pelo harness existente. |
| Supervisor | Opt-out, evento SIMULADO de R$ 1.000 e replay estável aprovados. Oito turnos mais Supervisor: nove etapas; 13 requisições HTTP 200 incluindo health/docs. |
| Cloud Run existente | `pingo-backend-00001-l22`, 100% do tráfego no snapshot consultado; health autenticado 200 e anônimo 403 revalidados. Essa revisão é anterior à golden. |
| Nova imagem / revisão / promoção | Não executadas por bloqueio no preflight de IAM. Nenhum smoke golden HTTPS da nova revisão foi realizado. |
| Frontend | Contrato, payloads, oito turnos, plano, consentimento e replay documentados. Não há frontend nem proxy implementado nesta cópia. |

O smoke real usou um servidor temporário em `127.0.0.1:18081`, encerrado ao final. Ele usou a ADC local; ainda falta repetir a jornada na nova revisão com a identidade runtime do Cloud Run. Não houve fixture ou agente demo substituindo os serviços reais.

## Correção mínima encontrada na integração

A jornada original falhava no primeiro turno com HTTP 503 (`gemini_unavailable`). O diagnóstico registrou `FinishReason.MAX_TOKENS`: 488 tokens de raciocínio e 9 de resposta, produzindo JSON incompleto.

Foi alterada **uma linha** em `backend/agent/provider.py`: `max_output_tokens=512` para `2048`. O engine financeiro, SQL, contrato, API, guardrails e arquitetura foram preservados. O limite inclui raciocínio e saída, conforme a [documentação do Gemini](https://ai.google.dev/gemini-api/docs/thinking).

Depois da correção, as oito chamadas encerraram com `FinishReason.STOP`; o maior consumo observado de raciocínio + resposta foi 697 tokens. O teto maior pode aumentar consumo/latência em outras entradas e não garante ausência de truncamento para qualquer mensagem. Os limites existentes de tempo, uma chamada de modelo e validação estrita continuam ativos. Falhas permanecem explícitas.

## Bloqueio exato e ação para retomar

A leitura de IAM do serviço e do projeto funcionou, sem bindings públicos; a checagem de invocador está habilitada. APIs necessárias, repositório `agentes`, bucket de staging e build anterior também foram verificados.

A chamada **POST `https://cloudresourcemanager.googleapis.com/v3/folders/900300571186:getIamPolicy`** recebeu **403 `PERMISSION_DENIED` / `IAM_PERMISSION_DENIED`**. A permissão requerida é `resourcemanager.folders.getIamPolicy`. Assim, não foi possível comprovar ausência de grants públicos herdados, exigência do `ANTIGRAVITY_HANDOFF.md` antes de publicar. [Referência oficial da operação](https://docs.cloud.google.com/resource-manager/reference/rest/v3/folders/getIamPolicy).

**Isso é uma negação de leitura da política ancestral, não uma tentativa de deploy negada.** O health anônimo 403 não exclui, por si só, grants herdados para `allAuthenticatedUsers`.

Um responsável que já possua acesso deve verificar a política dessa pasta e dos ancestrais aplicáveis, confirmando ausência de invocação pública herdada, ou continuar no ambiente já autorizado a fazer essa verificação. Não é necessário conceder acesso público nem alterar o IAM do serviço para resolver esta etapa.

Com essa evidência, retomar o handoff: revalidar snapshot/tráfego, build com conta e staging existentes, smoke da imagem, candidata privada sem tráfego, smoke golden HTTPS autenticado, promoção da revisão testada e repetição do smoke. A build anterior usa a conta `575520783518-compute@developer.gserviceaccount.com`; a runtime permanece `squad-agent-sa@batalha-time-08-g7ha.iam.gserviceaccount.com`. Nenhuma delas foi alterada.

## URL e integração

URL canônica retornada pela API nesta execução: **https://pingo-backend-uahbqqbh3a-uc.a.run.app**. Revisão observada: `pingo-backend-00001-l22`; não apresentar como golden publicada. O alias anteriormente registrado permanece uma referência histórica: `https://pingo-backend-575520783518.us-central1.run.app`.

O frontend deve consumir a golden por um proxy de servidor já autorizado, reenviar `draft` como `decision` e manter tokens Google fora do navegador. A rota/origem desse proxy ainda precisam ser confirmadas no ambiente do frontend; não foram criadas nesta rodada. Safety atual: `local`; Model Armor remoto não foi validado nem ativado.

## Evidências e arquivos

No projeto: `docs/STATUS-CORE.md`, `docs/ANTIGRAVITY_HANDOFF.md`, `docs/FRONTEND_INTEGRATION.md` e `work/golden-continuation-evidence-20260927.json`. As evidências incluem timestamps, HTTP status/request IDs, job BigQuery, providers, modelo e motivo do bloqueio, sem tokens, mensagens, extratos ou identidade da persona.

Repositório e alterações anteriores preservados; nenhum commit, push ou refactor realizado.
