# Handoff da próxima revisão — backend Pingo

Atualizado em 2026-09-27. **Revisão anterior Cloud Run VERIFICADA por Antigravity:** pingo-backend-00001-l22 no [serviço privado](https://pingo-backend-575520783518.us-central1.run.app), health autenticado 200/anônimo 403 e chat/recálculo com Gemini e BigQuery reais. Evidências em STATUS-CORE e work/cloud-run-smoke.json. **Golden agora validada localmente com SQL BigQuery e Gemini reais; nova revisão não publicada por bloqueio na verificação de IAM ancestral.** Ver EXECUCAO_GOLDEN_REAL_2026-09-27.md.

**Verificação local consolidada:** 147 testes PASS (103 anteriores + 44 novos), 18 evals anteriores + 23 golden PASS, smoke golden offline PASS. Isso verifica fixture explícita, engine, API e controles locais; não comprova a nova consulta Google nem uma imagem nova.

ADC agora renovada com TLS válido via confiança nativa do Windows no processo local. Bloqueio atual: leitura `folders/900300571186:getIamPolicy` retornou 403; responsável com acesso deve comprovar ausência de grants herdados antes de publicar. Serviço/IAM/tráfego preservados. A correção de uma linha no limite Gemini (512 → 2048) passou na jornada real e na suíte local.

## Continuação única

O roteiro completo de build, validação real, nova revisão, smoke HTTPS e rollback está em [ANTIGRAVITY_HANDOFF.md](ANTIGRAVITY_HANDOFF.md). Seguir esse documento e preservar a revisão saudável; não reescrever app, alterar frontend ou iniciar melhorias.

Sequência: ADC com TLS válido → adapter golden real e comparação do snapshot → jornada Gemini/BigQuery real → testes/build/smoke da imagem → candidata privada → health/chat/recálculo/Supervisor na URL HTTPS autenticada → migração autorizada e registro de evidências. Somente marcar a nova revisão verificada após execução correspondente.

## Configuração golden publicada

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
HOST=0.0.0.0
~~~

Cloud Run continua em us-central1 e fornece PORT. DEMO_MODE=true habilita a experiência sintética/eventos simulados; DATA_PROVIDER=bigquery continua consultando dados reais. A golden recusa fixture e agente demo quando K_SERVICE está presente. ID/data são fixos no servidor; o alias compatível é persona-a, omitível no request. Não usar PINGO_AUTHORIZED_USERS para selecionar outra golden.

Runtime usa identidade Google/ADC já aprovada, sem chave JSON. Sem secrets em build/frontend. Não copiar a configuração offline do README para publicação. Model Armor permanece escolha explícita; falha remota não é mascarada. Não alterar IAM/faturamento, conceder acesso público ou criar dependência dos serviços proibidos do evento.

## Artefatos e aceite

- Dockerfile/entrypoint: python -m backend, bind 0.0.0.0 e PORT da plataforma; health em /health.
- Allowlists .dockerignore/.gcloudignore incluem ambos os SQL fixos e código backend. Excluem testes/fixture golden, docs/diagnóstico, .env, credenciais, frontend e work.
- scripts/smoke_golden.py verifica jornada golden, providers, valores de referência, recálculo, preservação de centavos e Supervisor opt-in.
- contracts mantêm respostas v1; event_dataset_demo é origem sintética, não seleção de fonte. Golden real deve reportar runtime.data=bigquery e golden_analysis.data_source=dataset_observed.

Na nova publicação, registrar build/digest, revisão, URL, health autenticado, acesso anônimo negado e jornada com Gemini + BigQuery reais. Proxy pode auxiliar diagnóstico; não substitui aceite HTTPS direto. Preservar rollback para revisão verificada. Comandos detalhados e prompt de continuação: [ANTIGRAVITY_HANDOFF](ANTIGRAVITY_HANDOFF.md). Detalhes de API/dados: [API_BACKEND](API_BACKEND.md), [BIGQUERY_HANDOFF](BIGQUERY_HANDOFF.md) e [GOLDEN_PERSONA](GOLDEN_PERSONA.md).
