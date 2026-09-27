-- 04 — Cobertura mensal e elegibilidade para comparações entre meses.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 26.652.345 bytes.
-- Job bqjob_r54b79dde52490148_000001a0def82ef1_1.
-- Processados: 26.652.345 bytes; faturados: 27.262.976 bytes.
-- Um mês com algum lançamento não significa orçamento mensal completo.
WITH usuario_mes AS (
  SELECT
    id_usuario,
    anomes,
    COUNT(*) AS lancamentos,
    COUNTIF(tipo = 'E') AS entradas,
    COUNTIF(tipo = 'S') AS saidas,
    MIN(DATE(anomesdia)) AS primeira_data,
    MAX(DATE(anomesdia)) AS ultima_data
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1, 2
), cobertura AS (
  SELECT id_usuario, COUNT(*) AS meses_com_lancamento
  FROM usuario_mes
  GROUP BY 1
)
SELECT
  m.anomes,
  COUNT(*) AS usuarios_com_lancamento,
  SUM(m.lancamentos) AS lancamentos,
  COUNTIF(m.entradas > 0) AS usuarios_com_entrada,
  COUNTIF(m.saidas > 0) AS usuarios_com_saida,
  APPROX_QUANTILES(m.lancamentos, 100)[OFFSET(50)] AS mediana_lancamentos_por_usuario,
  MIN(m.primeira_data) AS primeira_data_observada,
  MAX(m.ultima_data) AS ultima_data_observada,
  (SELECT COUNTIF(meses_com_lancamento = 12) FROM cobertura) AS usuarios_12_meses,
  (SELECT COUNTIF(meses_com_lancamento >= 9) FROM cobertura) AS usuarios_9_meses
FROM usuario_mes AS m
GROUP BY m.anomes
ORDER BY m.anomes;
