# Pingo: backend demonstrável e integração Google

Execução autorizada pelo pedido atual: sem novo brainstorming, sem frontend, sem IAM/faturamento ou segredos. Trabalhar na pasta atual preservando arquivos staged anteriores. As restrições antigas de primeira entrega local foram ampliadas explicitamente pelo usuário. Contratos compartilhados permanecem inalterados.

## Arquitetura e decisões

FastAPI existente; engine de centavos preservado; um agente Gemini configurável (ADK se instalação simples), tools fechadas e validadas. Histórico BigQuery é somente contexto observado e jamais saldo/agenda atual. Modo fixture explicitamente separado. Segurança local obrigatória mais Model Armor opcional/configurável. Sem persistência longa, jobs, notificações ou serviços proibidos do evento.

O contrato DecisionResponse v1 já suporta `event_dataset_demo`: esse é o rótulo da base sintética do evento, mesmo ao usar BigQuery real. Chat terá envelope próprio contendo DecisionResponse e metadados de runtime. A autorização da demo privada usa persona vinculada no servidor; não oferecer autenticação multicliente fictícia.

## Tarefas e verificações

- [x] Fase 0: ler estado/core/contratos; executar suíte antiga e HTTP real localhost. Evidência: 19 passed; health/docs/decision/review 200; totais 1000000 -> 900000 e mínimo -20000 -> -10000 centavos.
- [x] Fase 1: ler integralmente ambas transcrições e site, salvar WORKSHOP_REQUIREMENTS com timestamps e classificação. Responsável workshop.
- [x] Fase 2: preservar invariantes, acrescentar conciliação explícita compra/fatura e limites/datas com testes antes do código.
- [x] Fase 3 (offline; cloud pendente): backend/agent models, provider ADK, parser conservador demo, tools allowlist; testes de interação, erro de modelo, identidade e dados não confirmados.
- [x] Fase 4 (offline; SQL real pendente): backend/data adapter parametrizado/preagregado, dry-run, timeout, erros explícitos; tests/test_data.py com cliente fake. Responsável data_adapter.
- [x] Fases 5–6 (local + provider/handoff; Armor remoto pendente): SafetyProvider local/Model Armor, input/output, documentação oficial e handoff; tests/test_safety.py. Responsável safety. Tool guard integrado no orquestrador.
- [x] Fase 7: plano snapshot consentido, acompanha desligado, evento demo rotulado, opt-out antes de providers. Testes de zero chamadas e recálculo sem dupla contagem.
- [x] Fase 8: logs estruturados sem conteúdo, evals executáveis com 15 casos e relatório gerado.
- [ ] Fase 9 — CLOUD RUN DEPLOYED obrigatório: build/smoke da imagem, deploy real, URL, GET /health e fluxo Pingo real nessa URL. Localmente bloqueado por ferramentas/ADC; handoff não satisfaz o aceite atualizado pelo usuário.
- [x] Fase 10 — handoff de continuação preparado, começando pelo setup de participante dos organizadores; não equivale à entrega do evento.
- [x] Revisão independente, suíte final, pip check, HTTP smoke, atualizar STATUS e DEPLOY_HANDOFF com evidências e limitações.

## Foco da revisão

Identidade nunca controlada pelo modelo; valores extraídos precisam de confirmação verificável; histórico sem saldo não pode resultar em certeza; falha Google nunca vira fixture; saída livre do modelo não altera cálculos ou alega viabilidade; consentimento falso evita qualquer consulta; planos não prometem persistência Cloud Run.

## Evidências e execução

2026-09-26: Python 3.13.15; branch feat/core sem commit/remote; gcloud/agy/docker ausentes do PATH e gcloud ausente nos caminhos comuns; ADC ausente no caminho padrão; variáveis de credenciais/modelo ausentes. Nenhum segredo lido. Health local foi executado em processo temporário e encerrado.

## Fechamento verificado

103 testes PASS, 18/18 evals PASS, pip check saudável, smoke HTTP atual 5 rotas 200. Revisão independente encontrou cinco defeitos corrigidos com regressões red-green (parser/carryover e encerramento async SDK). Demo mantida em 127.0.0.1:8766. Studio confirmou gemini-3.8-flash/global com OK; backend ADC, SQL/Armor remotos e Docker/deploy não testados. Fonte consolidada: docs/STATUS-CORE.md. Não foram criados commit/remote, alterados contracts/frontend, concedidos papéis IAM ou publicado serviço.
