# Registro de consultas

Estado em 2026-09-26: `bq show` confirmou metadados; `02_contagens.sql` foi a primeira consulta de dados desta sessão. `01_schema.sql` não foi executada porque o schema foi obtido por `bq show`.

Antes de cada consulta de dados, registrar aqui: localização, dry-run/bytes estimados, limite `maximum_bytes_billed=1073741824`, job ID, bytes processados/faturados, resultado agregado e acumulado estimado. Não ultrapassar 12 consultas de dados ou 5 GiB de estimativas acumuladas nesta rodada.

| Nº | Arquivo | Estado | Dry-run (bytes) | Job ID | Processados (bytes) | Resultado |
|---|---|---|---:|---|---:|---|
| 01 | `01_schema.sql` | NÃO EXECUTADA | — | — | — | — |
| 02 | `02_contagens.sql` | EXECUTADA | 28.990.270 | `bqjob_r4199df9a7d8b9498_000001a0deecee86_1` | 28.990.270 (29.360.128 faturados) | 467.585 linhas, 1.000 usuários, 12 `anomes` de 202501 a 202512; nulos essenciais 0 |
| 03 | `03_semantica_cobertura.sql` | EXECUTADA | 23.817.613 | `bqjob_r1ddccd4e12eff57e_000001a0def69d6c_1` | 23.817.613 (24.117.248 faturados) | E/S, sinais e cobertura |
| 04 | `04_cobertura_mensal.sql` | EXECUTADA | 26.652.345 | `bqjob_r54b79dde52490148_000001a0def82ef1_1` | 26.652.345 (27.262.976 faturados) | 1.000 usuários com lançamentos, entradas e saídas em cada um dos 12 meses |
| 05 | `05_timing_fluxo.sql` | EXECUTADA | 30.393.025 | `bqjob_r10ff0b52d313ff67_000001a0def9c99d_1` | 30.393.025 (30.408.704 faturados) | 10.834/12.000 usuário-meses com saída anterior à primeira entrada observada |
| 06 | `06_recorrencia_estimada.sql` | EXECUTADA | 44.191.179 | `bqjob_r51bab02a3c1bb5b1_000001a0defe44e3_1` | 44.191.179 (45.088.768 faturados) | 8.615 grupos candidatos, 1.000 usuários |
| 07 | `07_mudanca_categoria.sql` | EXECUTADA | 33.360.978 | `bqjob_r174196c94ae5eb4f_000001a0df00c155_1` | 33.360.978 (33.554.432 faturados) | 12.373 pares usuário-categoria elegíveis, 3.312 com valor +30% |
| 08 | `08_regularidade_entradas.sql` | EXECUTADA | 30.393.025 | `bqjob_r74c026093759c784_000001a0df032591_1` | 30.393.025 (30.408.704 faturados) | 788/1.000 com primeiro dia E em faixa de 3 dias; 553/1.000 com total mensal E variando >50% |
| 09 | `09_integridade_parcelas.sql` | EXECUTADA | 24.954.415 | `bqjob_r24a83a105859b82e_000001a0df05dc10_1` | 24.954.415 (25.165.824 faturados) | 29.847 lançamentos com parcela, 992 usuários, sem inconsistências básicas |
| 10 | `10_categorias_financeiras_parcelas.sql` | EXECUTADA | 33.865.707 | `bqjob_r542044f63e149e9_000001a0df0b9803_1` | 33.865.707 (34.603.008 faturados) | Rótulos estruturados de parcelas, juros, tarifas, fatura e crédito |
| 11 | `11_distribuicao_fluxo_observado.sql` | EXECUTADA | 26.652.345 | `bqjob_r283dec7790b2cb67_000001a0df17144e_1` | 26.652.345 (27.262.976 faturados) | 58 usuários sem mês negativo observado, 264 com >=9 |
| 12 | `12_qualidade_repeticao.sql` | EXECUTADA | 58.858.724 | `bqjob_r7c0b0ecfda7cceae_000001a0df184ef9_1` | 58.858.724 (59.768.832 faturados) | 0 divergências de mês/data, 0 linhas integralmente idênticas |
| 13 | `13_sensibilidade_fatura_transferencias.sql` | EXECUTADA | 44.848.971 | `bqjob_r8e00195ffee6052_000001a0df1fe640_1` | 44.848.971 (45.088.768 faturados) | 10.721/12.000 meses ainda têm saída antes de E após exclusões de sensibilidade |

Consultas de dados desta sessão: **12/12**. Soma de estimativas e bytes processados: **406.978.597 bytes (0,379 GiB) / 5 GiB**. Soma de bytes faturados informados pelos jobs: **412.090.368**. Não executar nova consulta de dados nesta rodada.

Metadados de localização, particionamento, clustering e descrições também podem ser obtidos por `bq show --format=prettyjson` no Cloud Shell, sem ler linhas da tabela. A localização do dataset deve ser confirmada antes da execução de `INFORMATION_SCHEMA`.
