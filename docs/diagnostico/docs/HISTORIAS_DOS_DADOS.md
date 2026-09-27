# Histórias sustentadas pela exploração

Base sintética `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`, `us-central1`, 1.000 usuários, 467.585 lançamentos entre janeiro e dezembro de 2025. As três histórias abaixo são **agregadas**; não representam pessoas reais nem estatísticas brasileiras. SQL, dry-runs, jobs e bytes em `sql/README.md`; detalhes em `docs/DADOS.md`.

## 1. A ordem das saídas e entradas merece uma jornada própria

> Observamos saídas antes da primeira entrada observada em **10.834 de 12.000 usuário-meses** (1.000 usuários, 2025). Após excluir pagamentos de fatura e transferências das saídas, ainda são **10.721 de 12.000**. Isso sugere investigar o calendário dos compromissos, mas não comprova falta de saldo, uso de cheque especial ou atraso; o agente poderia mostrar uma linha do tempo do fluxo observado, perguntar saldo inicial e datas/valores esperados, e recalcular quando o cliente corrigir os dados.

- **Pergunta e SQL:** quanto do problema pode ser *quando* saem os valores? `sql/05_timing_fluxo.sql` e sensibilidade `sql/13_sensibilidade_fatura_transferencias.sql`.
- **Evidência adicional:** 5.564 de 6.200 usuário-meses com fluxo E−S final não negativo tiveram vale negativo da variação acumulada iniciada em zero; após as exclusões, 8.197 de 9.127. São denominadores diferentes, descritos explicitamente.
- **Alternativas/limites:** saldo anterior ao mês e outras contas podem cobrir o vale; E pode ser transferência, estorno ou empréstimo. Exclusão de fatura/transferências não substitui conciliação e pode remover compromissos reais. As datas usam UTC.
- **Consequência para MVP:** visualização de **variação do fluxo observado** até a próxima entrada confirmada, com premissas editáveis e sem afirmar saldo negativo.

## 2. Há sinais estruturados de parcelas e custos, mas falta o calendário futuro

> Observamos campos de parcela em **29.847 lançamentos de 992 usuários** em 2025, além de **8.615 grupos candidatos** a repetição regular em 1.000 usuários; isso sugere investigar compromissos existentes e custos observados, mas não comprova que estejam ativos ou quais parcelas vencerão; o agente poderia apresentar candidatos para confirmação do cliente antes de qualquer cenário de nova compra.

- **Pergunta e SQL:** quanto do movimento parece recorrente e quais custos são rotulados? `sql/06_recorrencia_estimada.sql`, `sql/09_integridade_parcelas.sql`, `sql/10_categorias_financeiras_parcelas.sql`.
- **Critério e evidência:** candidato de recorrência = mesma pessoa + descrição normalizada + microcategoria, uma saída mensal em ≥3 meses, ≥2 pares de meses consecutivos e variação de valor ≤20%. Foram 8.615 grupos em 34.655 com ≥3 meses e 101.053 lançamentos candidatos. Os dois campos de parcela estão presentes juntos, positivos e inteiros; `parcela_atual` ≤ `parcela_total` em todos os 29.847. `Juros pagos`: 4.755 lançamentos/695 usuários; `Outras tarifas financeiras`: 2.487/424; `Pagamento de fatura`: 12.000/1.000.
- **Alternativas/limites:** descrições genéricas geram falso positivo; marcadores de parcela podem se referir a eventos históricos, inclusive IPTU. Não há ID de transação, vencimentos futuros, valor de parcela futura ou taxa. Pagamento de fatura pode duplicar compras já lançadas.
- **Consequência para MVP:** lista de compromissos **candidatos**, com confirmação de vigência, valor e vencimento pelo cliente; não inferir dívida, taxa ou número de parcelas futuras.

## 3. A mudança não é igual para todos

> Observamos **3.312 de 12.373 pares usuário-macrocategoria** elegíveis com valor de saídas ao menos 30% maior no segundo semestre de 2025; em `Mercado`, foram **323/1.000**, mas a razão mediana foi 1,017. Isso sugere investigar mudanças individuais, mas não comprova inflação pessoal, descontrole ou causa; o agente poderia mostrar se a diferença veio de frequência ou valor médio e perguntar o que o cliente quer preservar.

- **Pergunta e SQL:** o que mudou em relação ao próprio histórico? `sql/07_mudanca_categoria.sql`, com apoio de `sql/08_regularidade_entradas.sql` e `sql/11_distribuicao_fluxo_observado.sql`.
- **Elegibilidade e métrica:** janeiro–junho versus julho–dezembro, seis meses em cada lado; ≥3 saídas por semestre na mesma pessoa/macrocategoria. Dos 12.373 pares, 2.500 tiveram frequência +30% e 2.905 valor médio por lançamento +30%; os grupos se sobrepõem. `Assinaturas` teve razão mediana de valor 0,998 e só 56/1.000 pares +30%, contrariando a ideia de alta generalizada. No fluxo observado, 58/1.000 usuários não tiveram mês E−S negativo, enquanto 264/1.000 tiveram ≥9 meses assim. A primeira data E variou até três dias em 788/1.000 usuários, mas o total mensal E variou >50% em 553/1.000.
- **Alternativas/limites:** mudança pode vir de necessidade, preferência, sazonalidade, classificação ou movimentação entre contas. E não equivale a renda e S pode incluir fatura/transferência. A base sintética não permite inferir profissão, hábitos sensíveis ou comportamento da população real.
- **Consequência para MVP:** comparação explicável com o próprio histórico e pergunta explícita sobre prioridades; sem classificar gastos como dispensáveis.

## Escolha de jornada para discussão

| Jornada | Viável com a base atual | O que perguntar ao cliente | O que não sustentar |
|---|---|---|---|
| **Organizar compromissos até a próxima entrada** | Linha do tempo de E/S observados, concentração temporal, candidatos recorrentes. É a melhor primeira jornada de diagnóstico. | Saldo disponível na data de referência, próxima entrada esperada e sua natureza, vencimentos/valores de obrigações, outras contas, eventos que quer preservar. | Saldo negativo real, atraso, crédito usado ou garantia de sobra. |
| **Ajustar planejamento após mudança no fluxo** | Comparar seis meses equivalentes por categoria, frequência e valor médio; mostrar divergência individual. | Se a mudança é temporária, prioridades, necessidades e correções de classificação. | Causa, julgamento do gasto ou previsão causal. |
| **Assumir nova parcela** | Exibir histórico e marcadores de parcelas, custos rotulados e cenários condicionais. | Preço e condições **reais** da compra, vencimento, saldo atual, compromissos ativos, renda/entradas confirmadas, outros cartões/contas e metas. | Aprovação de viabilidade, juros/oferta inventados, parcelas restantes deduzidas automaticamente. |

**Viável só com a base:** descrição retrospectiva dos padrões observados e perguntas contextualizadas. **Viável com informações complementares:** simulação limitada de calendário, mudança ou nova parcela. **Não sustentado:** fluxo de caixa completo, saldo atual, inadimplência, condições de crédito ou recomendação de assumir dívida.

**Pergunta principal ao mentor:** há fonte autorizada de saldo atual e calendário de compromissos futuros, com regra para conciliar compra no cartão e pagamento da fatura? Sem isso, o MVP deve prometer apenas uma análise histórica e simulações explicitamente condicionais.
