# Núcleo e integração — Codex OU Claude Code

Leia as instruções existentes, 00_COMECE_AQUI.md, 01_ESPECIFICACAO.md e contracts/. O nome é Pingo. Este v2 estende o v1 sem autorização para sobrescrever trabalho em andamento. Faça revisão curta de compatibilidade/contrato com Vinicius; após a aprovação de escopo e plano, implemente em sua branch/worktree. Não repetir descoberta ampla nem automatizar login novamente. Claude/Codex são ferramentas de desenvolvimento; o produto usa somente Gemini autorizado. Não exportar dados do evento, commitar segredos, alterar IAM, faturamento ou publicar sem autorização específica. Fixture deve ter modo visível; não dizer que integração real passou sem testar. Não fazer mudanças fora da faixa de arquivos sem coordenação.

## Faixa
backend/core/, backend/agent/, backend/api/, backend/models/, contracts/ e testes correspondentes. Você é integrador; não reescreva o frontend ou o adaptador de dados dos colegas.

## Começo
Inspecione git status/remotes/stack e preserve a .venv validada. Liste em no máximo 8 linhas o plano de execução e contratos para confirmação de Vinicius. Se já estiverem aprovados, implemente em incrementos; não trate uma integração Google bloqueada como motivo para não escrever o motor.
A primeira integração deve funcionar localmente com fixtures próprias e sinalização explícita. Em paralelo, outro responsável valida BigQuery/Gemini no GCP.

## Entregas em ordem
1. Base /health, models e OpenAPI; resposta conforme schema v1 já fornecido. Entrada validada com confirmed_context do adendo v2. Publique esse contrato antes de os colegas implementarem adaptadores; evite nova versão a cada pedido.
2. Testes unitários antes do engine: distribuição de centavos, data de fim de mês, agenda completa, janela parcial, saldo ausente, referências duplicadas e nenhuma dupla contagem da compra. Implemente engine puro. Sem taxas/preços inventados; juros/ofertas especiais ausentes ficam fora.
3. Defina interface de dados única em backend/core/context_contract.py. O adaptador real é de backend/data/ (pessoa 3). Contexto contém histórico, origem, período, lacunas e candidatos a confirmação — não fabrica saldo atual.
4. /api/decision e /api/decision/review; mudar parâmetros recalcula. O resultado não vem do texto Gemini. Mensagem explicativa só depois de validação de saída. Use fixture existente para a primeira resposta integrada com a UI.
5. Gemini pelo SDK/ADK já escolhido e autorizado no projeto. Validar modelo/endpoint em uma chamada mínima; não usar fornecedor pessoal silenciosamente. LLM chama tools de consulta/cálculo com argumentos validados, no máximo 4 iterações; não pode escolher user_id ou SQL arbitrário. Cliente/escopo vêm do servidor/sessão/allowlist demo.
6. /api/accompaniment/review conforme spec e schema adicional. No início do handler verifique consentimento e DEMO_MODE antes de qualquer acesso/modelo. Reuse o mesmo engine/guardrails. Não construir segundo agente completo ou job em background.
7. Integre os callbacks de segurança da pessoa 4. Fallbacks honestos, erros sem segredos e trace_id. Não retornar sucesso com mock em modo real.
8. Integre main cedo; chamar testes e build da UI antes do merge. Auxilie o dono do deploy sem assumir permissões que não testamos.

## Evidência e testes mínimos da nova parte
- consent_enabled=false => reviewed=false/reason=opted_out/decision=null, zero consultas/model calls.
- evento inexistente ou DEMO_MODE=false => erro explícito e nenhum processamento financeiro.
- compra postada acrescenta apenas os vencimentos, nunca preço cheio mais parcelas.
- saldo não informado => projection.mode=unavailable, min_balance_cents=null.
- dados de 2025 não viram contexto atual em 2026 sem confirmação.
- pedido de outro cliente nunca altera a identidade usada pela ferramenta.
- pedido de CEO mulher não é tratado como ataque; redirecionamento seguro e sem alegação institucional inventada.

Termine cada incremento com comandos/testes executados e próximo bloqueio. Se não conseguir integrar algum serviço em uma tentativa curta, peça ajuda concreta e avance no que é independente. Não gastar outra hora em browser. Não instalar UCP/AP2/Jev ou um banco novo nesta etapa.
