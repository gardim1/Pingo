-- 05 — Saídas antes da primeira entrada e vale da variação acumulada por usuário/mês.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 30.393.025 bytes.
-- Job bqjob_r10ff0b52d313ff67_000001a0def9c99d_1.
-- Processados: 30.393.025 bytes; faturados: 30.408.704 bytes.
-- A variação parte de zero em cada mês: NÃO é saldo, dívida nem cheque especial.
-- DATE(TIMESTAMP) usa UTC; o fuso operacional da base não foi documentado.
WITH diario AS (
  SELECT
    id_usuario,
    anomes,
    DATE(anomesdia) AS dia,
    SUM(IF(tipo = 'E', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS entradas,
    SUM(IF(tipo = 'S', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS saidas
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1, 2, 3
), sequencia AS (
  SELECT
    *,
    MIN(IF(entradas > 0, dia, NULL)) OVER (PARTITION BY id_usuario, anomes) AS primeira_entrada,
    SUM(entradas - saidas) OVER (
      PARTITION BY id_usuario, anomes ORDER BY dia ROWS UNBOUNDED PRECEDING
    ) AS variacao_acumulada
  FROM diario
), usuario_mes AS (
  SELECT
    id_usuario,
    anomes,
    SUM(entradas) AS entradas,
    SUM(saidas) AS saidas,
    SUM(IF(dia < primeira_entrada, saidas, 0)) AS saidas_antes_primeira_entrada,
    MIN(variacao_acumulada) AS menor_variacao_acumulada
  FROM sequencia
  GROUP BY 1, 2
)
SELECT
  IFNULL(CAST(anomes AS STRING), 'TOTAL') AS mes,
  COUNT(*) AS usuario_meses,
  COUNT(DISTINCT IF(saidas_antes_primeira_entrada > 0, id_usuario, NULL)) AS usuarios_com_saida_antes,
  COUNTIF(saidas_antes_primeira_entrada > 0) AS meses_com_saida_antes,
  COUNTIF(menor_variacao_acumulada < 0) AS meses_com_vale_negativo,
  COUNTIF(entradas >= saidas) AS meses_fluxo_final_nao_negativo,
  COUNTIF(entradas >= saidas AND menor_variacao_acumulada < 0) AS meses_final_nao_negativo_com_vale
FROM usuario_mes
GROUP BY ROLLUP(anomes)
ORDER BY anomes;
