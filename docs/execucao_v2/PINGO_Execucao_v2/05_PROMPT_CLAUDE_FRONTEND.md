# Interface — Claude Code ou agente escolhido

Leia as instruções existentes, 00_COMECE_AQUI.md, 01_ESPECIFICACAO.md e contracts/. O nome é Pingo. Este v2 estende o v1 sem autorização para sobrescrever trabalho em andamento. Faça revisão curta de compatibilidade/contrato com Vinicius; após a aprovação de escopo e plano, implemente em sua branch/worktree. Não repetir descoberta ampla nem automatizar login novamente. Claude/Codex são ferramentas de desenvolvimento; o produto usa somente Gemini autorizado. Não exportar dados do evento, commitar segredos, alterar IAM, faturamento ou publicar sem autorização específica. Fixture deve ter modo visível; não dizer que integração real passou sem testar. Não fazer mudanças fora da faixa de arquivos sem coordenação.

## Faixa
Somente frontend/ e seus testes. O backend, shared contracts e deploy pertencem aos colegas.

## Missão
Tela Pingo inspirada em padrões de app bancário, com identidade própria (sem imitar login/identidade oficial Itaú). Dois modos: **Quero planejar** e **Pingo acompanha**. Desktop com conversa compacta à esquerda e painel de decisão à direita, responsivo. Não montar um banco inteiro.

## Fluxo
1. Escolha de persona autorizada e selo 'Demonstração com dados sintéticos'; período de referência visível.
2. Planejar: intenção, campos editáveis, confirmação pontual, 1–2 cenários, compromissos, evidências, ajustar, salvar e rever.
3. Não chamar resposta de aprovação. Valores vêm da API, nunca contas JS espalhadas pelo front; null não vira zero.
4. Acompanha: opt-in inicialmente desligado, finalidade explicada, revogação a um clique. Demo de acompanhamento vale para sessão atual. Não enviar evento ao backend se desligado.
5. Botão 'Simular compra realizada', marcado como simulação. Resultado em card não modal, sem tom de bronca. Um event_id gera no máximo um card por sessão. Sem push/WhatsApp, sem alegação de monitoramento real.
6. 'Mulher pode ser CEO?' e conversa benigna: renderizar a resposta de política do backend, sem hardcode político/institucional na UI.
7. Modo fixture separado de modo real. Queda da API aparece como erro/retry, não vira mock silencioso.

## Contratos
Usar decision-response.schema.json sem alteração unilateral e accompaniment-response.schema.json (envelope com DecisionResponse). Cliente API separado dos componentes: analyze, review e reviewAccompaniment. Endpoint/entrada aprovados com o integrador. Fixtures locais para avançar enquanto API não existe; não chamar Gemini/BigQuery no browser.

## Critérios de entrega
Primeiro incremento consumindo fixture pelo client de desenvolvimento; segundo integrado à API. Testar loading/needs_input/limited/ready/blocked/error, opt-out, event_id duplicado, respostas fora de ordem, legenda de simulação, teclado e mobile. Rodar build e informar resultado. Não construir mascote/animação complexa/checkout antes da integração.
