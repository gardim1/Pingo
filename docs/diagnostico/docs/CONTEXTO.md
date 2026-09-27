# Contexto do projeto Abacate

Atualizado em 2026-09-26. Nome anterior: PRISMA; nome, jornada e arquitetura ainda são provisórios.

## Desafio e hipótese
Produto baseado em agentes que transforme histórico financeiro e contexto individual em decisões melhores. Hipótese principal: ajudar a avaliar uma compra parcelada considerando compromissos, necessidades essenciais e objetivos. A equipe também considera orçamento apertado e uso de crédito; a exploração dos dados deve poder mudar a hipótese.

Jornada proposta: entender intenção; consultar contexto; perguntar dados essenciais faltantes; comparar somente condições informadas; mostrar impactos e premissas; permitir que o cliente indique o que preservar; recalcular após correção; resumir a decisão. Nunca executar operação real.

Não presumir sobra de dinheiro, nem julgar delivery, lazer ou outros gastos como dispensáveis. Não inventar ofertas, descontos, juros, metas ou renda; não afirmar viabilidade sem dados suficientes. A ia.i já existe no Itaú; o valor pretendido é aprofundar uma jornada específica com ferramentas e cálculos, não criar um chatbot genérico.

## Ambiente informado
- Projeto visto no console: `batalha-time-08-g7ha` (Batalha Agentes Time 08).
- Tabela: `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`.
- Console: https://console.cloud.google.com/bigquery?project=batalha-time-08-g7ha
- O screenshot inicial mostrava 467.585 linhas e parte das colunas; a apresentação mencionou 1.000 pessoas. Depois, `bq show` e consultas agregadas confirmaram as contagens, o período de 2025 e o schema de 11 colunas em `docs/DADOS.md`.
- Guia da organização, ainda não verificado: orçamento informado US$ 1.000/equipe; modelo `gemini-3.8-flash`; segredo `gemini-api-key`; chaves JSON de conta de serviço bloqueadas; pipeline Cloud Build → Artifact Registry (`agentes`) → Cloud Run (`us-central1`). Não ler o segredo nem presumir região do dataset ou limite automático de gastos.
- Notebook relatado: Windows, Python 3.13, Node.js 24, npm, Git e `.venv` verificados antes. Inspeção desta pasta em 2026-09-26: pasta inicialmente vazia além de `work/` e `outputs/`; `gcloud`/`bq` ausentes do PATH; `agent-browser` disponível; `.venv` ausente daqui.

## Arquitetura para discussão, sem implementar
React/TypeScript para conversa e cards; Python/FastAPI para API, ferramentas e cálculos; Gemini no ambiente Google autorizado; BigQuery via backend; frontend compilado e backend em um Cloud Run; Cloud Build/Artifact Registry; identidade de serviço/ADC e Secret Manager conforme regras. Logs sem credenciais ou extratos. Jev opcional e desligado até autorização e benefício demonstrado. Preservar stack já existente se a equipe trouxer código.

## Decisões e pendências
- Diagnóstico de schema, localização, contagens, período, semântica e qualidade concluído nesta rodada; evidências e limites em `docs/DADOS.md`.
- Distinguir o que a base sustenta, o que exige informação do usuário e o que não é sustentado.
- Não tratar entrada como renda, saída líquida negativa como endividamento, recorrência estimada como obrigação, histórico como saldo atual, nem mês incompleto como queda de renda.
- Validar se agregados podem sair do ambiente Google conforme restrições da organização.
- Aguardar decisão da equipe antes de desenvolver o produto.

## Direção após a exploração (provisória)
- A base confirmou 1.000 usuários, 467.585 lançamentos e 12 meses de 2025, com categorias, saldo após lançamento e marcadores de parcela. O histórico não inclui vencimentos futuros, ofertas, juros contratados ou confirmação de compromissos ativos.
- O sinal agregado mais robusto é a ordem temporal de saídas e entradas; a jornada de organizar compromissos até a próxima entrada observada merece discussão prioritária, sempre com saldo e previsões confirmados pelo cliente.
- A hipótese de orientar uma nova compra parcelada pode ser tratada como cenário condicional com informações complementares, nunca aprovação de viabilidade baseada apenas no histórico.
- Ver `docs/HISTORIAS_DOS_DADOS.md` para evidência, ressalvas e comparação das três jornadas. Não implementar nesta etapa.
