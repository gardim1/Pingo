# Pingo — racional de experiência, elementos usados e critérios de prototipação

Atualizado em 2026-09-27. Este documento cobre o entregável "racional de experiência" do edital da Batalha de Agentes (peso 20% do critério de avaliação, conforme `WORKSHOP_REQUIREMENTS.md`). Descreve por que a interface do Pingo foi desenhada como foi, quais elementos foram usados, quais decisões de experiência foram tomadas e quais critérios guiaram cada escolha. Todas as afirmações abaixo foram verificadas contra o código em `frontend/src/` nesta data; não descrevem intenção não implementada.

## 1. Problema de experiência que o Pingo resolve

O banco tradicionalmente mostra o passado financeiro (extrato, fatura, saldo). A pergunta que o usuário faz antes de uma compra parcelada — "o que acontece com o meu mês se eu fizer isso agora?" — normalmente não tem resposta no app do banco (`README.md`). O Pingo existe para responder essa pergunta especificamente, sem virar um segundo aplicativo bancário: ele se apresenta como uma camada conversacional sobre uma tela de banco já familiar, não como um produto novo a ser aprendido.

Essa escolha de escopo (responder uma pergunta, não recriar um banco) é o critério-mestre que disciplina todas as decisões de tela: cada elemento de UI existe para reduzir a distância entre "o usuário perguntou" e "o usuário entendeu o impacto no saldo futuro", e nada além disso.

## 2. Método de prototipação: duas rotas na mesma base de código

O frontend (`frontend/src/App.tsx`) expõe duas rotas que renderizam os mesmos componentes React, mas com propósitos diferentes:

- **Rota `/` — produto bancário puro.** Um `<main>` centralizado com um `device-frame` (moldura de smartphone) contendo apenas a experiência final: Home → Loading → Consentimento → Chat → Supervisor. Nenhum elemento de apresentação, mapa de fluxo ou nota de design aparece aqui (`App.tsx:200-256`). Esta é a rota que representa o "protótipo" propriamente dito.
- **Rota `/demo-map` ou `/dev/flow` — quadro de apresentação para avaliadores.** A mesma moldura de smartphone é reaproveitada, mas ao lado aparece um `FlowMap` navegável (`frontend/src/components/FlowMap.tsx`) com 12 etapas nomeadas e clicáveis, mais um painel lateral fixo com a nota de design da tela atual e uma legenda "Observado ou Simulação" (`App.tsx:258-531`).

Decisão e critério: **não construir dois códigos-fonte** (um "de mentira" para pitch e outro real). A rota de apresentação reutiliza exatamente os mesmos componentes de produção (`HomeScreen`, `LoadingScreen`, `ConsentScreen`, `ChatScreen`, `SupervisorSheet`), diferenciando-se apenas pela casca de navegação em volta. Isso evita a divergência clássica de protótipo-mockup-vs-produto-real: o que o comitê avaliador navega em `/demo-map` é bit-a-bit o que roda em produção em `/`.

A rota de apresentação também embute uma barra de acessibilidade (seletor de escala de texto 100/115/130% e toggle de "movimento reduzido", `App.tsx:294-322`) para permitir que o avaliador teste a interface sob diferentes condições sem precisar alterar configurações do sistema operacional.

## 3. Elementos usados

### 3.1 Linguagem visual
- Paleta: petróleo `#0b3c49`, azul Pingo `#0e5a5f`, fundo neutro `#f0f1f3`/`#eceae6`, vermelho de alerta `#c8322f`, verde de confirmação `#15855c` (consistente entre `FolgaChart.tsx`, `SupervisorSheet.tsx`, `ConsentScreen.tsx` e documentado em `docs/FRONTEND_FINAL.md`).
- Tipografia: Inter para corpo de texto, Montserrat para títulos/wordmark (`App.tsx:286`, `docs/FRONTEND_FINAL.md`).
- Ícones: conjunto `lucide-static` carregado via CDN (unpkg), usados de forma consistente em todas as telas (`x.svg`, `calendar-check.svg`, `triangle-alert.svg`, `hand.svg`, `wallet.svg`, `shield-check.svg`, `circle-check.svg`) — decisão de usar um único sistema de ícones open-source em vez de desenhar ícones customizados, para acelerar a prototipação sem comprometer a coerência visual.
- Barra de status iOS simulada (relógio, notch, indicador de bateria) desenhada manualmente em `LoadingScreen.tsx:24-61` e `ConsentScreen.tsx:24-62`, para que a moldura de smartphone pareça um dispositivo real durante a demonstração, sem depender de biblioteca externa de mockup.
- Mascote/wordmark: um ícone de "sparkle" (duas estrelas de 4 pontas) desenhado em SVG inline, reused como avatar do Pingo no chat e como logotipo — deliberadamente minimalista, sem personagem antropomórfico (ver seção 6).

### 3.2 Padrões de interação reaproveitados de apps bancários
- Estrutura de Home (cabeçalho, atalhos em carrossel, cartões de conta/fatura) segue convenções de app bancário de referência, com a marca do banco substituída por elementos neutros — o Pingo não personifica nem imita a identidade visual oficial do Itaú (`App.tsx` nota de design "home"; também explícito em `docs/execucao_v2/PINGO_Execucao_v2/05_PROMPT_CLAUDE_FRONTEND.md`: "identidade própria, sem imitar login/identidade oficial Itaú").
- Layout de chat: mensagens do assistente sem balão (texto corrido, mais parecido com um extrato/relatório do que com um chatbot genérico), balão cinza para o usuário com iniciais de avatar e horário (nota de design "greet"; `ChatScreen.tsx`).
- Bottom sheet modal para o Supervisor (`role="dialog"`, `aria-modal="true"`, alça de arraste visual no topo) — padrão nativo de app mobile para ações opcionais que não devem ocupar a tela inteira (`SupervisorSheet.tsx:31-78`).

## 4. A jornada de 12 telas e a decisão por trás de cada uma

O `FlowMap` (`frontend/src/components/FlowMap.tsx:10-23`) define formalmente as 12 etapas da jornada de demonstração, cada uma com um rótulo e uma descrição de uma linha. `App.tsx` associa a cada etapa uma nota de design (`DESIGN_NOTES`, `App.tsx:10-96`) que documenta o critério de UX adotado. Reproduzido e explicado abaixo:

| # | Etapa | Critério de experiência adotado |
|---|---|---|
| 1 | **Home do banco** | Estrutura, espaçamento e navegação seguem a home de referência; o Pingo aparece como atalho flutuante discreto acima da barra inferior, sem cobrir conteúdo — o agente é um complemento, não uma substituição da navegação bancária existente. |
| 2 | **Carregamento** | Composição minimalista (botão fechar no topo, muito branco, indicador de progresso baixo e centralizado); com "movimento reduzido" ativado, o anel de carregamento fica parado e a mensagem de texto assume sozinha a função de comunicar progresso — o critério de acessibilidade não é um extra visual, é um caminho funcional alternativo. |
| 3 | **Consentimento** | Aparece só na primeira vez. O escopo de dados necessário (conta, cartão, parcelas) é fixo e não pode ser desligado; o escopo opcional (renda/salário) tem um switch explícito. A frase "o que o Pingo nunca faz" (não paga, não transfere, não contrata crédito) aparece **antes** do botão de aceitar, não depois — o critério é que a limitação de poder do agente precisa ser lida antes do consentimento, não como rodapé legal ignorável. |
| 4 | **Pergunta (greet)** | Segue o layout de chat de referência descrito acima. |
| 5 | **Forma de pagamento (terms)** | O Pingo explicitamente recusa-se a responder sem saber a forma de pagamento, porque a resposta financeira muda substancialmente entre uma compra à vista e uma parcelada — esse é o motivo de negócio por trás da pergunta obrigatória (`ChatScreen.tsx`, gate em `msg.decision?.question?.field === 'installment_count'`, backend `REQUIRED_TERMS` em `backend/core/decision.py`). |
| 6 | **O que observei (facts)** | Mostra apenas dados reais da persona (renda CLT, margem média, margem do último mês, as 3 parcelas ativas), em formato de lista estilo extrato — não um card/widget de dashboard — para reforçar que aquilo é um fato observado, não uma estimativa de UI. |
| 7 | **Projeção da folga (compare)** | Regra de camadas de informação: primeiro uma conclusão + uma mudança-chave + uma linha do tempo simples; "Ver detalhes" expande a comparação completa "agora × novembro". Linha contínua = observado; linha pontilhada/tracejada = simulação, sempre com rótulo escrito (nunca só cor). O fim das parcelas deliberadamente **não** é apresentado como "cabe no orçamento" — é apresentado como um fato neutro (fim de uma obrigação), evitando que a UI pareça estar recomendando a compra. |
| 8 | **E se… (whatif)** | Três perguntas "e se" (momento da compra, prazo de parcelamento, um mês parecido com o pior mês observado). Valores negativos aparecem abaixo da linha de zero, com textura listrada e sinal de menos explícito — não apenas cor vermelha, para não depender de percepção de cor. O gráfico tem descrição textual completa para leitor de tela. |
| 9 | **Plano** | Observado em traço sólido, simulação em tracejado (mesmo código de cores da etapa 7, reaplicado). O Supervisor só é oferecido **depois** que algum valor já foi entregue ao usuário (o plano gerado) — nunca como a primeira coisa que a interface propõe. |
| 10 | **Supervisor (sheet)** | Opt-in explícito: a folha mostra o que o Supervisor faz e o que ele nunca faz antes de qualquer botão de ativação. Recusar ("Agora não") é visualmente tão fácil quanto aceitar — mesmo tamanho de área de toque, mesma proeminência tipográfica. |
| 11 | **Plano salvo (saved)** | O resumo deixa explícito que nada foi comprado. O status do Supervisor (ativo/desligado) permanece visível no topo da conversa a partir daqui. |
| 12 | **Aviso proativo (nudge)** | O aviso proativo (quando as parcelas terminam) nasce do mesmo atalho flutuante da Home, no momento certo — e é sempre dispensável com uma ação. |

Critério transversal presente em praticamente toda etapa: **o valor numérico nunca é o primeiro elemento a aparecer sem contexto** — sempre vem acompanhado de um rótulo de proveniência (observado/simulação) e, a partir da etapa 7, de uma trilha visual (linha do tempo) que situa o número no tempo.

## 5. O princípio "Observado vs. Simulação"

Esta é a decisão de experiência mais repetida no código e a mais importante do ponto de vista de confiança do usuário em um produto financeiro. Ela aparece em pelo menos quatro lugares independentes:

1. **Legenda fixa na rota de apresentação** (`App.tsx:472-527`): dois selos visuais — "Observado" (borda sólida, ícone de círculo com check) e "Simulação" (borda tracejada, ícone de círculo tracejado) — com a explicação textual "Borda sólida, ícone de check. Dado real da conta." vs. "Borda tracejada e rótulo escrito. Projeção, pode mudar."
2. **`FolgaChart.tsx`**: o trecho do gráfico até "hoje" é desenhado com traço sólido preto (`stroke="#1c1b1b"` `strokeWidth="4"`), e o trecho projetado (hoje → novembro) é desenhado com gradiente e `strokeDasharray="2 9"` (linha pontilhada), dentro de um `clipPath` animado que revela a transição em vez de simplesmente trocar a cor (`FolgaChart.tsx:135-157`).
3. **Cards de fatos vs. cards de simulação no chat** (achado do agente de exploração sobre `ChatScreen.tsx`): o card "Observado" (linha 652) usa borda sólida; os cards de comparação, what-if e plano usam borda tracejada e o rótulo explícito "Simulação" com um ícone de círculo tracejado (linhas 803-804, 881, 1089, 1111).
4. **Contrato de dados**: no nível de API, o campo `evidence[].origin` do `DecisionResponse` distingue formalmente `user_confirmed`, `dataset_observed`, `derived` e `own_synthetic_fixture` (`contracts/decision-response.schema.json:228-235`) — ou seja, a distinção visual front-end não é uma convenção estética isolada, ela espelha uma distinção que já existe no contrato de dados do backend.

Critério adotado: a distinção observado/simulação nunca depende só de cor (acessibilidade a daltonismo) e nunca é implícita — todo elemento simulado carrega a palavra "Simulação" por escrito. Essa regra está documentada explicitamente no comentário da nota de design da etapa "compare": *"Linha contínua é observado; pontilhado e tracejado são simulação, com rótulo escrito."*

## 6. Decisões de tom, copy e agência do usuário

- **Nenhuma recomendação de compra.** O agente nunca diz "compre" ou "não compre"; ele mostra o impacto e devolve a decisão ao usuário. Isso está refletido tanto na copy (`backend/core/golden.py`, textos de "mesmo assim"/autonomia) quanto na UI: o texto do card de comparação explicitamente evita around framing de aprovação ("Esperar evita somar parcelas em outubro, mas não torna a compra segura por si só.", achado em `ChatScreen.tsx:1038-1041`).
- **Sem tom de repreensão.** O card de simulação de evento do Supervisor foi projetado deliberadamente para não modal e sem tom de "bronca" (`docs/execucao_v2/PINGO_Execucao_v2/05_PROMPT_CLAUDE_FRONTEND.md`, item 5 do fluxo), critério herdado do brief original de UX e confirmado na implementação (`ChatScreen.tsx`, disclaimers como "Nenhuma compra foi feita. Simulações não são recomendação financeira.").
- **Nenhuma atribuição de marca/opinião institucional.** Perguntas fora de escopo (ex.: "uma mulher pode ser CEO?") recebem resposta respeitosa sem atribuir posição ao Itaú — comportamento testado explicitamente no caso de avaliação "08 — Gênero e off-topic" (`docs/EVAL_REPORT.md`) e citado como requisito de UI no brief original ("renderizar a resposta de política do backend, sem hardcode político/institucional na UI").
- **Sem mascote antropomórfico complexo.** O brief original pedia para não construir "mascote/animação complexa/checkout antes da integração" — a implementação final manteve essa disciplina: o "Pingo" é representado por um ícone de sparkle simples, não por um personagem animado.
- **Nada é comprado de verdade.** Todo o fluxo de "Simular compra realizada" do Supervisor é rotulado como simulação, gera no máximo um card por `event_id` por sessão, e a UI trata explicitamente a ausência de transação real como parte do design (`docs/execucao_v2/PINGO_Execucao_v2/05_PROMPT_CLAUDE_FRONTEND.md`, item 5; confirmado em `backend/models/conversation.py` — `SimulatedEvent`).

## 7. Critérios de acessibilidade adotados (WCAG AA)

Todos os itens abaixo foram verificados diretamente no código-fonte dos componentes:

| Critério | Onde está implementado |
|---|---|
| Rótulos ARIA em toda ação sem texto visível | `aria-label="Fechar"` / `"Fechar Pingo"` em botões de ícone (`SupervisorSheet.tsx:99`, `LoadingScreen.tsx:67`, `ConsentScreen.tsx:68`) |
| Live region para novas mensagens de chat | `role="log" aria-live="polite" aria-label="Conversa com o Pingo"` no container de rolagem do chat (achado em `ChatScreen.tsx:368-370`) |
| Indicador de carregamento anunciado | `role="status" aria-live="polite"` em `LoadingScreen.tsx:12-13` e no indicador "pensando" do chat (`ChatScreen.tsx:1652`) |
| Controles de opção/alternância semânticos | `role="switch" aria-checked` nos toggles de consentimento e do Supervisor (`ConsentScreen.tsx:165-166`, `SupervisorSheet.tsx:191-192, 247-248`); `role="radiogroup"`/`role="radio"`/`aria-checked` no simulador "E se" (`ChatScreen.tsx:1130,1170,1210`) |
| Gráficos com descrição textual completa | `role="img" aria-label` com frase completa descrevendo os valores da linha do tempo em `FolgaChart.tsx:92-93` (função `ariaDesc`, linha 85) e no gráfico de 12 meses do simulador (`ChatScreen.tsx:1273`) |
| Suporte a `prefers-reduced-motion` | Checado via `window.matchMedia('(prefers-reduced-motion: reduce)')` e via prop `reduceMotion` propagada de `App.tsx` a todos os componentes animados; desliga a animação do `FolgaChart` (linhas 22-44), do spinner de carregamento (`LoadingScreen.tsx:118`), do scroll do chat (`ChatScreen.tsx:79`) e dos pontos de "pensando" (`ChatScreen.tsx:1672`) |
| Alvo de toque mínimo | `minHeight: 44` (Apple HIG) aplicado consistentemente a botões interativos no chat (achado do agente de exploração) e `minHeight: 44-52` nos botões de ação das demais telas |
| Ajuste de escala de texto sem quebra de layout | Prop `zoom` propagada a todos os componentes de tela na rota de apresentação, testável via seletor 100/115/130% (`App.tsx:112-115, 294-313`) |

Esses critérios não foram "adicionados depois" — eles aparecem já como parte da assinatura de props dos componentes (`reduceMotion?: boolean`, `zoom?: number`) desde a primeira versão lida do código, o que indica que acessibilidade foi tratada como requisito de design, não como tarefa de polimento final.

## 8. Validação da experiência

A experiência foi validada por dois mecanismos complementares, ambos com evidência registrada:

1. **Matriz de 8 cenários end-to-end** (`docs/FRONTEND_FINAL.md`): jornadas completas cobrindo compra de iPhone (golden), AirPods, notebook parcelado, reforma de casa, viagem, consulta de saldo, consulta de salário e uma tentativa de injeção via "outro cliente" — todas com resultado PASS.
2. **Smoke E2E de produção** (`docs/STATUS-CORE.md`, seção "Publicação do Frontend Final"): verificação HTTP real pós-deploy cobrindo `/health`, proxy S2S (`/api/pingo/health`), dois turnos de chat com dados reais do BigQuery e cálculo real de novembro, e opt-out do Supervisor — evidência gravada em `work/frontend-smoke-evidence.json`.

Nenhuma validação de usabilidade com usuários humanos reais foi realizada ou está documentada nesta base — a validação existente é funcional/técnica (a interface se comporta como especificado), não um teste de compreensão por usuários finais. Isso é uma limitação explícita, não uma alegação de teste de usuário.

## 9. Aderência aos critérios do edital

O regulamento da Batalha de Agentes (`docs/WORKSHOP_REQUIREMENTS.md`) pontua "racional de experiência" dentro do bloco de 20% de peso "experiência". As decisões documentadas aqui atendem diretamente a esse critério ao explicitar, para cada tela, qual problema de confiança/compreensão ela resolve — não apenas descrever a aparência visual. O restante do peso do edital (30% negócio, 50% arquitetura/engenharia/dados) é coberto pelos documentos irmãos [`DESENHO_SOLUCAO.md`](DESENHO_SOLUCAO.md) e [`ARQUITETURA.md`](ARQUITETURA.md).

## 10. Limitações conhecidas desta camada de experiência

- A rota de apresentação (`/demo-map`) e a barra de acessibilidade nela embutida são uma ferramenta de avaliação/demonstração, não fazem parte da rota de produto (`/`) usada pelo usuário final.
- O layout responsivo foi verificado no formato de moldura de smartphone (390×844) usado na apresentação; não há evidência registrada de teste em breakpoints de desktop/tablet além do que o brief original pedia ("desktop com conversa compacta à esquerda e painel à direita") — a implementação final adotou a moldura mobile como formato único.
- Não há telemetria de uso real (cliques, tempo em tela, abandono) instrumentada nesta base — a validação de experiência é qualitativa/funcional, conforme descrito na seção 8.
