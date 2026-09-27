# Pingo — execução v2: uma aplicação, dois modos

Este pacote atualiza o handoff anterior, sem substituir código que já exista. É especificação, contratos, fixtures e instruções para os implementadores: **não contém o aplicativo implementado**.

## Decisão para revisão rápida do time
Claude/Codex escrevem o código. O runtime usa apenas Gemini autorizado. React/TypeScript + FastAPI em um serviço Cloud Run, mantendo outra stack se já houver implementação. O Pingo oferece **Quero planejar** e **Pingo acompanha**; são dois pontos de entrada para o mesmo agente/ferramentas, não dois sistemas independentes.

A revisão rápida é: conferir este escopo, os contratos e donos. Após aprovação, cada executor apresenta uma sequência curta e implementa sua faixa; não repetir a pesquisa de 1h30 nem todo o brainstorming. Mudanças incompatíveis com código já iniciado devem ser resolvidas pelo integrador, não aplicadas automaticamente.

## Primeira ação
Um repositório privado autorizado, quatro clones/branches, um integrador. Leia `09_COLABORACAO.md`. Se já existe repositório, reutilize-o. Não criar quatro repositórios; não compartilhar a mesma pasta aberta entre dois agentes.

## Faixas de trabalho
| Responsável | Branch | Propriedade |
|---|---|---|
| Vinicius + agente de código principal | feat/core | backend/core/, backend/api/, backend/agent/, backend/models/, contracts/, integração |
| Pessoa 2 + seu agente | feat/ui | frontend/ e testes de UI |
| Pessoa 3 | feat/data | backend/data/, sql/, docs/DADOS.md |
| Pessoa 4 | feat/safety-release | backend/safety/, testes de segurança, deploy/, Dockerfile, .dockerignore, .gcloudignore |

O integrador gera a base comum e os contratos primeiro. Mudanças em contratos e dependências Python compartilhadas passam por ele; cada frente registra dependências necessárias, não edita o lockfile da outra. O proprietário do frontend controla package.json e seu lockfile.

## Ordem, não uma promessa de duração
1. Agora: confirmar repo, aprovar contrato e distribuir donos. Encerrar exploração ampla.
2. Primeiro incremento: `/health`, UI consumindo contrato e motor determinístico testado com fixture própria.
3. Em paralelo: uma consulta BigQuery autorizada e uma chamada mínima Gemini. Testar permissões de build/deploy cedo sem alterar IAM.
4. Integração: uma persona da base, com saldo/compromissos complementares explicitamente confirmados para a demonstração.
5. Segundo fluxo: consentimento, evento de compra **simulado**, revisão e próximo passo sem julgamento.
6. Segurança e ensaio: sem vazamento entre personas, sem números inventados, falha explícita e URL verificada pelo time.

Se uma integração bloquear por 10 minutos, registrar o erro e acionar o responsável; não passar mais uma hora automatizando login. Fixtures deixam o desenvolvimento avançar, mas uma demo só com fixtures não comprova uso da base/Google.

## Fora do corte principal
Jev, UCP/AP2, notificações reais, monitoramento bancário em produção, compra/pagamento real, scraping de lojas, RAG amplo de posicionamentos e três agentes de finanças diferentes.

Leia `01_ESPECIFICACAO.md` (atualizada), seu prompt de frente e os contratos. Os exemplos financeiros já existentes continuam sendo fictícios e não são achados do BigQuery.
