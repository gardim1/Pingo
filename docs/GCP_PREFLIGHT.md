# Preflight Google Cloud — Pingo

Atualizado em 2026-09-26, 21:07 America/Sao_Paulo. Escopo desta frente: observação do console autenticado, uma geração mínima no playground Gemini e preparação de verificações de leitura. **Nenhum deploy, mudança de IAM, faturamento, API, recurso ou segredo foi realizado nesta frente.**

## Resultado observado

| Verificação | Estado | Evidência e limite |
|---|---|---|
| Console autenticado | VERIFICADO | Navegador Chrome já aberto em Google Cloud; seletor exibiu **Batalha Agentes Time 08** e URL com `project=batalha-time-08-g7ha`. Identidade pessoal omitida deste documento. |
| Projeto da sessão Cloud Shell | VERIFICADO | Terminal exibiu `Your Cloud Platform project in this session is set to batalha-time-08-g7ha` e prompt com o mesmo projeto. Isso não comprova permissões de API. |
| Autorização Cloud Shell | BLOQUEADO | Ao abrir, apareceu **Autorizar o Cloud Shell**, pedindo uso das credenciais para chamadas Google Cloud. O agente não clicou. O usuário posteriormente informou que autorizaria no navegador. Houve uma interrupção de controle; depois ele foi recuperado e a aba ainda exibia o diálogo de autorização e **A conexão com seu Google Cloud Shell foi perdida**, com opção Reconectar. Nenhum comando foi enviado. A intenção de autorizar não é registrada como autorização concluída. |
| Cloud Run — serviços existentes | VERIFICADO na UI | A lista Serviços, sem filtro aplicado, carregou vazia, com a orientação para criar um serviço. Não houve mensagem de permissão negada nessa lista. Isso não comprova autorização para criar/deploy nem inventaria recursos fora da visão consultada. |
| URL Pingo Cloud Run | BLOQUEADO | Nenhuma URL de backend publicada foi encontrada/verificada nesta frente. |
| Agent Platform | VERIFICADO na UI | Uma aplicação de interface existente estava aberta no Studio. Havia aviso **Ask your admin to enable required APIs**. O aviso não nomeava a API; não prova que a API Gemini esteja desabilitada. O texto de modelo na prévia gerada não é evidência de modelo acessível. |
| APIs habilitadas | VERIFICADO na UI | A página **APIs e serviços ativados**, sem filtro e com 36 itens, inclui `aiplatform.googleapis.com`, `bigquery.googleapis.com`, `modelarmor.googleapis.com`, `run.googleapis.com`, `artifactregistry.googleapis.com`, `cloudbuild.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`, `secretmanager.googleapis.com` e `generativelanguage.googleapis.com`. Nenhum `gcloud services list` executado. API habilitada não comprova todas as permissões da identidade runtime. |
| Gemini/modelo/região | VERIFICADO no Studio; backend pendente | Selecionado **Gemini 3.8 Flash**; URL e seletor mostram `gemini-3.8-flash`, URL com `region=global`. Enviado somente **Responda somente OK.**; resposta real **OK**, contador UI **7 tokens**. Nenhum dado financeiro, tool ou arquivo enviado. Não foi teste do backend/ADK nem da ADC local. A UI não forneceu HTTP status, `modelVersion` completo ou latência final; não inventá-los. |
| BigQuery atual | BLOQUEADO nesta frente | Aba BigQuery do projeto existe, mas nenhum job novo ou leitura de tabela foi executado. Resultados históricos de diagnóstico permanecem evidências anteriores, descritas em `WORKSHOP_REQUIREMENTS.md`. |
| Model Armor/templates | VERIFICADO na UI; integração bloqueada | Página Modelos carregou tabela sem linhas e **Nenhum modelo de proteção de modelo foi criado**. Botão superior Criar modelo desabilitado; havia também link de criação, não utilizado. API habilitada. Permissão de criar, região/configuração de template e custo continuam não verificados. |
| Cloud Build, Artifact Registry, Logging/Monitoring, Secret Manager | APIs VERIFICADAS na UI | Constam na lista de APIs ativadas; recursos, permissões operacionais e integrações não testados. Nenhum segredo aberto ou copiado. |

Páginas utilizadas: [Agent Platform no projeto](https://console.cloud.google.com/agent-platform?project=batalha-time-08-g7ha), [serviços Cloud Run](https://console.cloud.google.com/run/services?project=batalha-time-08-g7ha), [BigQuery](https://console.cloud.google.com/bigquery?project=batalha-time-08-g7ha), [APIs ativadas](https://console.cloud.google.com/apis/dashboard?project=batalha-time-08-g7ha), [templates Model Armor](https://console.cloud.google.com/security/modelarmor/templates?project=batalha-time-08-g7ha), [playground Gemini utilizado](https://console.cloud.google.com/agent-platform/studio/multimodal;mode=prompt?model=gemini-3.8-flash&project=batalha-time-08-g7ha&supportedpurview=project,folder&region=global). A sessão autenticada do navegador não foi exportada para a máquina local nem convertida em chave de conta de serviço.

O teste foi executado às aproximadamente 21:03 America/Sao_Paulo. A resposta **OK** foi lida na árvore de acessibilidade e vista em captura do console, com projeto e modelo simultaneamente visíveis. Não houve salvamento na galeria nem implantação. O painel Código sugeria `google-genai` com `vertexai=True` e `GOOGLE_CLOUD_API_KEY` como variável/placeholder; nenhuma chave real foi exibida, aberta ou criada. A integração backend deve preferir ADC e precisa de teste independente.

A lista de APIs também mostrava Model Armor com 210 solicitações e 99% de erros no intervalo de um dia apresentado. São métricas agregadas do projeto, não deste backend; a causa não foi investigada e não pode ser atribuída a IAM por inferência. Cloud Pub/Sub apareceu na lista habilitada, mas **continua proibido** pela restrição explícita do evento nesta rodada.

## Próxima verificação: Cloud Shell já autorizado pelo usuário

Os comandos abaixo são **PLANEJADOS / NÃO EXECUTADOS nesta frente**. Usar Bash no Cloud Shell do projeto. Não executar `gcloud auth login` se a sessão já estiver autorizada; não imprimir access/refresh tokens, não usar `--log-http`, não ativar tracing shell (`set -x`). Se aparecer login, MFA ou nova permissão, devolver essa etapa ao usuário.

```bash
gcloud config get-value project
gcloud auth list --filter=status:ACTIVE --format='value(status)'
gcloud services list --enabled --project=batalha-time-08-g7ha --format='value(config.name)'
gcloud run services list --project=batalha-time-08-g7ha --region=us-central1 --format='table(metadata.name,status.url,status.conditions[0].status)'
gcloud model-armor templates list --project=batalha-time-08-g7ha --location=us-central1 --limit=20 --format='value(name)'
bq --project_id=batalha-time-08-g7ha show --format=prettyjson batalha-time-08-g7ha:hackathon_dados.extrato_sintetico
```

Esperado: projeto correto, presença de conta ativa e estado real dos serviços. A leitura `bq show` consulta metadados, não linhas de extrato. Ao registrar evidências, guardar somente localização, schema e contagens úteis; evitar copiar descrição livre, labels pessoais ou metadados desnecessários. Um erro de autorização deve ser registrado com operação, código e mensagem sanitizada; não converter erro em lista vazia.

APIs a verificar: `aiplatform.googleapis.com`, `bigquery.googleapis.com`, `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`; `modelarmor.googleapis.com` para Armor e `secretmanager.googleapis.com` apenas se a configuração realmente precisar de segredo. Listar serviços não autoriza ativá-los. A ausência/permissão insuficiente deve virar bloqueio concreto no handoff, sem mudança autônoma de IAM/faturamento.

Referências oficiais consultadas: [listagem de serviços habilitados](https://docs.cloud.google.com/sdk/gcloud/reference/services/list), [listagem Cloud Run](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/list), [listagem de templates Armor](https://docs.cloud.google.com/sdk/gcloud/reference/model-armor/templates/list). A página de Armor consultada possui um exemplo textual com `list list`; usar o **SYNOPSIS**, que especifica apenas um `list`.

## Chamada Gemini mínima, após confirmar acesso

Preferir o verificador de integração existente no repositório se já houver. Para teste isolado em Cloud Shell, usar ADC/identidade da sessão e a API oficial com conteúdo único **“Responda somente OK.”**; não enviar dados financeiros. O modelo `gemini-3.8-flash` agora foi confirmado por geração no Studio, com região de interface `global`; o próximo teste deve verificar o mesmo ID pela identidade e biblioteca do backend.

1. Usar `GEMINI_MODEL=gemini-3.8-flash` e verificar endpoint/região `global` pela API; guardar `GEMINI_MODEL` e `GOOGLE_CLOUD_LOCATION` como configuração explícita. Isso não muda a região de deploy Cloud Run, que permanece `us-central1`.
2. Executar uma única chamada `generateContent` com timeout de 30 segundos e `maxOutputTokens` pequeno.
3. Registrar HTTP/status, `modelVersion`, texto mínimo e latência. Não registrar headers, token, conta pessoal ou credenciais.
4. `403` é bloqueio de acesso; `404` pode ser ID/região/acesso; `429` pode ser quota/capacidade. Nenhum deles justifica afirmar que outro modelo funcionou ou trocar provider silenciosamente.
5. Se houver necessidade de selecionar outro Gemini, confirmar no catálogo/projeto e repetir explicitamente. Somente uma resposta real permite marcar **VERIFICADO**.

Contrato/SDK deve seguir a [documentação oficial de início com Gemini/Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start). Exemplos públicos de modelos não comprovam acesso deste projeto.

## Model Armor e limite de atuação

Se a listagem funcionar, registrar apenas nomes/localizações dos templates e inspecionar configuração sem alterá-la. Validar filtros de prompt injection/jailbreak e Responsible AI, idioma português/multilíngue, endpoints de input/output e tratamento de falhas. [Documentação oficial dos templates](https://docs.cloud.google.com/model-armor/manage-templates).

Não criar template, habilitar API, conceder papel ou modificar logging de prompts sem verificar autorização e configuração apropriadas. O preço e a compatibilidade do projeto continuam **não verificados**. A integração local/fallback deve continuar rotulada e testada independentemente disso.

## Proibições e continuidade

- Não instalar dependências de Cloud Pub/Sub, BigQuery Graph, Cloud Spanner ou Security Command Center. O evento os excluiu explicitamente; links históricos de documentação não são permissão para usá-los.
- Não criar JSON service-account key, exportar cookies, imprimir tokens, ler valores do Secret Manager, mudar IAM/faturamento ou publicar acesso anônimo.
- Não alterar o frontend já existente no Agent Platform Studio: a frente atual é backend.
- Não marcar autenticação local, build cloud, Gemini, BigQuery ou Model Armor reais como funcionando a partir de uma tela do console.
- Continuar backend/testes/evals locais e handoff enquanto a conexão/autorização cloud não produzir evidência verificável.

Próxima ação única desta frente: **retomar o Cloud Shell autorizado e executar a sequência de leitura acima, substituindo estes bloqueios por saídas reais sanitizadas.**
