# Diagnóstico da base

Estado: **metadados e 12 consultas agregadas verificados na aba autorizada do Chrome / Cloud Shell**. Limite de consultas desta rodada atingido.

## Fonte e metadados confirmados
- Tabela indicada: `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`.
- Localização do dataset e tabela: `us-central1`, verificada por `bq show` e pela aba Detalhes do BigQuery.
- Metadados da tabela: `numRows=467585`, `numBytes=58858724` (56,13 MB exibidos na interface). Nenhuma das contagens substitui a consulta executada.
- Sem particionamento por tempo ou faixa e sem clustering, conforme resposta de `bq show` (campos ausentes/nulos).
- Todas as 11 colunas são `NULLABLE`; `bq show` não retornou descrições de coluna:

| Coluna | Tipo |
|---|---|
| `id_usuario` | STRING |
| `anomesdia` | TIMESTAMP |
| `anomes` | INTEGER |
| `tipo` | STRING |
| `descr` | STRING |
| `vlr` | FLOAT |
| `nom_cate_macro` | STRING |
| `nom_cate_micro` | STRING |
| `saldo_apos` | FLOAT |
| `parcela_atual` | FLOAT |
| `parcela_total` | FLOAT |

`saldo_apos` e os campos de parcela existem; a cobertura observada está nos resultados abaixo, mas sua semântica de negócio não foi confirmada. `vlr`, `saldo_apos` e parcelas são FLOAT; para somas monetárias, explicitar arredondamento/conversão decimal e conferir anomalias.

## Consulta 02 — universo e período
Dry-run: 28.990.270 bytes. Job `bqjob_r4199df9a7d8b9498_000001a0deecee86_1`, concluído, 28.990.270 bytes processados e 29.360.128 bytes faturados. Resultado: **467.585 lançamentos**, **1.000 usuários distintos**, `anomes` de **202501 a 202512** com **12 valores distintos**; timestamps mínimo e máximo de 2025-01-01 00:00:00 a 2025-12-31 00:00:00 (campo TIMESTAMP; a exibição do CLI não declara fuso). Nulos em `id_usuario`, `anomesdia`, `anomes` e `vlr`: **0**. Isso não comprova que todos os usuários tenham 12 meses completos.

## Semântica e qualidade
Consulta 03: `tipo` tem somente `S` (432.508 lançamentos) e `E` (35.077). Todos os 467.585 valores de `vlr` são positivos; portanto o sinal não codifica entrada/saída, e a distinção observável está em `tipo`. Categorias macro e micro não têm nulos/vazios nessa consulta; são 21/92 categorias distintas em S e 4/6 em E. `saldo_apos` está preenchido em todos os lançamentos e é negativo em 54.336 linhas S e 1.805 linhas E; **não** concluir que isso represente cheque especial, dívida ou saldo atual. Os campos `parcela_atual` e `parcela_total` estão simultaneamente preenchidos e positivos em 29.847 saídas e nenhuma entrada; falta testar integridade e significado. Dry-run: 23.817.613 bytes; job `bqjob_r1ddccd4e12eff57e_000001a0def69d6c_1`, processados 23.817.613 e faturados 24.117.248 bytes.

Cobertura por mês/usuário, consistência de datas e repetição de linhas foram verificadas nas consultas 04 e 12. Repetição de linhas não provaria duplicação indevida sem identificador de transação.

Consulta 04: todos os **1.000 usuários** têm pelo menos um lançamento de entrada e saída em **cada um dos 12 meses de 2025**; há registros do primeiro ao último dia em janeiro e dezembro, em nível global. Isso torna os 12 meses elegíveis para comparações de histórico observado, mas não prova que todos os compromissos financeiros do usuário estejam na base nem que cada dia tenha atividade. Dry-run 26.652.345 bytes; job `bqjob_r54b79dde52490148_000001a0def82ef1_1`, 26.652.345 processados e 27.262.976 faturados.

Consulta 05: em 12.000 usuário-meses (1.000 usuários × 12 meses), houve saída antes da primeira entrada observada em **10.834** (90,3%). A variação acumulada do fluxo observado, iniciada artificialmente em zero a cada mês, atingiu valor negativo em **11.364** (94,7%). Mesmo entre **6.200** usuário-meses cujo fluxo mensal terminou não negativo, **5.564** (89,7% desse subconjunto) tiveram vale negativo antes. Isso sugere investigar a **ordem das entradas e saídas**. Não é saldo negativo, cheque especial, dívida nem prova de insuficiência de recursos: faltam saldo inicial, outras contas e obrigações externas; a primeira entrada pode não ser renda. Dry-run 30.393.025 bytes; job `bqjob_r10ff0b52d313ff67_000001a0def9c99d_1`, 30.393.025 processados e 30.408.704 faturados.

Consulta 06: uso de `descr` **somente dentro do BigQuery**, para agrupar por pessoa + descrição normalizada + microcategoria. Entre 34.655 grupos com pelo menos três meses de uma saída mensal única, 8.615 satisfizeram ainda dois pares consecutivos e variação máxima de valor de 20%; somam 101.053 lançamentos candidatos e aparecem nos 1.000 usuários. Mediana de meses por candidato: 12. Critério sensível a descrições genéricas e itens repetidos; **não** representa 8.615 contratos nem compromissos futuros confirmados. Dry-run 44.191.179 bytes; job `bqjob_r51bab02a3c1bb5b1_000001a0defe44e3_1`, 44.191.179 processados e 45.088.768 faturados.

Consulta 07: comparação dos seis primeiros e seis últimos meses de 2025, exigindo pelo menos três saídas por semestre na mesma pessoa/macrocategoria. Há **12.373 pares usuário-categoria** elegíveis em 21 macrocategorias; **3.312** tiveram valor semestral pelo menos 30% maior, **2.500** frequência pelo menos 30% maior e **2.905** valor médio por transação pelo menos 30% maior (grupos sobrepostos). Em `Mercado`, 323/1.000 pares tiveram valor +30%, 188 frequência +30% e 287 ticket médio +30%; a razão mediana de valor foi 1,017. Em `Assinaturas`, a razão mediana foi 0,998 e 56/1.000 pares tiveram valor +30% — contraponto a uma tese de aumento generalizado. Isso identifica mudanças individuais observadas, sem explicar causa ou dispensabilidade. Transferências e pagamentos podem gerar dupla contagem com outras categorias. Dry-run 33.360.978 bytes; job `bqjob_r174196c94ae5eb4f_000001a0df00c155_1`, 33.360.978 processados e 33.554.432 faturados.

Consulta 08: todos os 1.000 usuários tiveram E em cada mês. O dia da **primeira E** em cada mês ficou numa faixa de até 3 dias do calendário ao longo do ano em 788/1.000 usuários, mas o total mensal de E variou mais de 50% entre mínimo e máximo em 553/1.000. A razão mediana máximo/mínimo de E mensal foi 1,529. Datas relativamente previsíveis não implicam valores previsíveis; E pode incluir transferências, estornos e empréstimos, não apenas renda. Dry-run 30.393.025 bytes; job `bqjob_r74c026093759c784_000001a0df032591_1`, 30.393.025 processados e 30.408.704 faturados.

Consulta 09: **29.847/467.585 lançamentos** (6,4%) de **992/1.000 usuários** têm ambos os campos de parcela. Nenhum registro tem só um dos campos, valores não positivos, não inteiros ou `parcela_atual > parcela_total`. `parcela_atual` varia de 1 a 12, `parcela_total` de 3 a 12; há quatro macrocategorias com esses campos. O dado suporta reconhecer uma parcela histórica informada, mas não confirma valor futuro da parcela, vencimento, taxa, contrato ativo ou total de obrigações restantes. Dry-run 24.954.415 bytes; job `bqjob_r24a83a105859b82e_000001a0df05dc10_1`, 24.954.415 processados e 25.165.824 faturados. O primeiro dry-run falhou por assinatura `MOD(FLOAT64, INT64)` e não leu dados; corrigido para comparar com `ROUND`.

Consulta 10: consulta agregada por rótulos macro/micro, sem descrição livre. Entre os rótulos financeiros estão `Pagamento de fatura` (**12.000** lançamentos, 1.000 usuários), `Financiamento de imovel` (**8.400**, 700), `Juros pagos` (**4.755**, 695), `Outras tarifas financeiras` (**2.487**, 424), `Emprestimos` (**1.556**, 410) e `Outros emprestimos` (**971**, 376). A categoria rotulada `Juros pagos` identifica custo observado, mas não informa taxa, base de cálculo ou custo futuro. Pagamento de fatura pode refletir compras já lançadas: não somar mecanicamente as duas coisas. Os campos de parcela aparecem em categorias de Casa, Lojas e sites, Viagens e Lazer, inclusive IPTU; validar semântica do evento antes de chamar cada registro de compra parcelada. Dry-run 33.865.707 bytes; job `bqjob_r542044f63e149e9_000001a0df0b9803_1`, 33.865.707 processados e 34.603.008 faturados.

Consulta 11: em 1.000 usuários com 12 meses observados, **58** não tiveram mês de fluxo E−S negativo, **264** tiveram pelo menos 9 meses negativos e **54** tiveram os 12 meses negativos. Mediana de meses negativos por usuário: 6. Nos 12.000 usuário-meses, quantis aproximados da diferença observada E−S: p10 −4.011,13, p50 120,45, p90 3.852,79 (unidade monetária não confirmada). Isso mostra perfis contrastantes e contraria a ideia de que uma nova parcela possa ser recomendada amplamente com base em um histórico médio. Não comprova endividamento; transferência, fatura e outras contas podem afetar E e S. Dry-run 26.652.345 bytes; job `bqjob_r283dec7790b2cb67_000001a0df17144e_1`, 26.652.345 processados e 27.262.976 faturados.

Consulta 12: 0 linhas integralmente idênticas nas 11 colunas, 0 divergências entre `anomes` e o ano/mês de `anomesdia` em UTC, 0 tipos fora de E/S e 0 valores `vlr` não positivos. Ausência de linhas idênticas não prova inexistência de duplicação econômica sem ID de transação. Dry-run 58.858.724 bytes; job `bqjob_r7c0b0ecfda7cceae_000001a0df184ef9_1`, 58.858.724 processados e 59.768.832 faturados.

Consulta 13, checagem de sensibilidade: excluindo das **saídas** os rótulos `Pagamento de fatura` e toda macrocategoria `Transferencias diversas`, ainda há saída antes da primeira E em **10.721/12.000 usuário-meses** (89,3%, ante 10.834/12.000 sem exclusão). Dos **9.127** meses cujo fluxo ajustado terminou não negativo, **8.197** (89,8%) passaram por vale negativo relativo ao zero artificial do início do mês. O padrão de timing persiste sob essa exclusão, mas o ajuste não é conciliação contábil e pode remover obrigações reais; E continua podendo incluir transferências. Dry-run 44.848.971 bytes; job `bqjob_r8e00195ffee6052_000001a0df1fe640_1`, 44.848.971 processados e 45.088.768 faturados.

## Síntese de cobertura
Foram executadas 12 consultas de dados, todas após dry-run e com `maximum_bytes_billed=1073741824`. Soma das estimativas: **406.978.597 bytes (0,379 GiB)**; soma dos bytes faturados reportados: **412.090.368 bytes**. O teto de 12 consultas foi atingido. Detalhes de cada job em `sql/README.md`.

## Questões ainda abertas
- Qual é a definição operacional de `saldo_apos` e qual fonte autorizada informa o saldo disponível hoje?
- Existem, fora desta tabela, vencimentos, obrigações futuras, condições de crédito e metas confirmadas pelo cliente?
- Como conciliar lançamentos de compras, transferências e pagamento de fatura sem dupla contagem?
- Qual é a natureza das entradas `E` e quais podem ser tratadas como entradas futuras confirmadas?

Cada achado futuro deve seguir: **evidência → interpretação → limitação → consequência para o MVP**. Somente agregados; nenhum ID individual ou descrição livre nos documentos.
