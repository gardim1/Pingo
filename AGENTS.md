# Pingo — orientação de implementação

O pedido atual autoriza o primeiro incremento local do core. Leia `docs/execucao_v2/PINGO_Execucao_v2/01_ESPECIFICACAO.md`, `04_PROMPT_CODEX_CORE.md`, `contracts/decision-response.schema.json`, `docs/STATUS-CORE.md` e `docs/DEPLOY_HANDOFF.md` antes de mudar a API.

Propriedade do core: `backend/core/`, `backend/api/`, `backend/models/` e testes correspondentes. `backend/data/`, `backend/safety/`, `frontend/`, `deploy/` e arquivos de build/deploy pertencem a outros responsáveis. Alterações no contrato compartilhado exigem alinhamento com o integrador.

O histórico em `docs/diagnostico/` cobre 2025 e não é saldo atual nem agenda futura confirmada. `DEMO_MODE=true` ativa apenas fixture própria. Sem esse modo, uma chamada a `/api/decision` deve falhar explicitamente enquanto a integração real estiver pendente. Não incluir segredos, extratos completos, chaves de serviço ou dados de cliente no Git. Sem deploy, IAM, faturamento ou acesso público nesta fase.
