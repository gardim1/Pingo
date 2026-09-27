> Atualização v2: 01_ESPECIFICACAO.md e 00_COMECE_AQUI.md prevalecem. UCP/AP2/Jev fora do primeiro corte; modos de acompanhamento e colaboração estão especificados nos documentos v2.

# Fontes e status das afirmações
Consulta pública: 26/09/2026. Revalidar versões na implementação.

## Materiais da equipe
- Foto do desenho manuscrito: compra de iPhone -> dados/painel -> alternativas/personalização; guardrails entrada/saída, testes, monitoramento e deploy.
- Texto colado.txt: transcrição automática recebida nesta conversa, sem timestamps; contém discussão de acompanhamento do plano, UCP/AP2, ADK/A2A e fala sobre modelos Gemini disponibilizados. Não é transcrição revisada; números, nomes e termos podem conter erros.
- Guia SVG da organização, recebido anteriormente: projeto por equipe, Gemini/BigQuery/Cloud Run. Não prova recursos/credenciais funcionais.
- Screenshot anterior: projeto batalha-time-08-g7ha e tabela hackathon_dados.extrato_sintetico. Não valida semântica ou permissões de query.

## Documentação pública primária
UCP — visão geral e especificação: https://ucp.dev/
UCP — implementação Google e requisitos de comerciante: https://developers.google.com/universal-commerce-protocol
UCP — explicação e sample de integração: https://developers.googleblog.com/under-the-hood-universal-commerce-protocol-ucp/
UCP — repositório de samples: https://github.com/Universal-Commerce-Protocol/samples
AP2 — especificação: https://ap2-protocol.org/ap2/specification/
AP2 — exemplos: https://github.com/google-agentic-commerce/AP2
UCP/AP2 — mandatos, negociação e requisitos criptográficos: https://ucp.dev/specification/payment/extensions/ap2-mandates/
A2A — escopo e governança: https://a2a-protocol.org/dev/
ADK — segurança: https://adk.dev/safety/
ADK — callbacks: https://adk.dev/callbacks/types-of-callbacks/
Model Armor — escopo do serviço: https://docs.cloud.google.com/model-armor/overview
Gemini 3.8 Flash — modelo documentado: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash/
Cloud Run — contrato de container e filesystem: https://docs.cloud.google.com/run/docs/container-contract
Codex — instruções persistentes: https://developers.openai.com/codex/guides/agents-md/
Claude Code — contexto do projeto: https://code.claude.com/docs/en/memory

## O que NÃO foi confirmado
Permissão de ferramentas de programação externas; autorização para enviar dados a tais ferramentas; schema completo/semântica da base; acesso funcional a BigQuery/Gemini/Model Armor no projeto; API Itaú Shop; compatibilidade UCP do lojista; credenciais de pagamento; políticas completas do Itaú; execução de teste/deploy do produto; pontuação ou chance de vitória.

## Distinção principal
Fontes sustentam a existência e requisitos dos protocolos. A escolha de NÃO adicioná-los ao caminho crítico, a divisão do time, a arquitetura mínima e as metas de tempo são recomendações de engenharia, não exigências da organização.
