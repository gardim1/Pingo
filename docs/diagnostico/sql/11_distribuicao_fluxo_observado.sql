-- 11 — Distribuição do fluxo mensal observado e perfis agregados contrastantes.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 26.652.345 bytes.
-- Job bqjob_r283dec7790b2cb67_000001a0df17144e_1.
-- Processados: 26.652.345 bytes; faturados: 27.262.976 bytes.
-- Entrada E não é necessariamente renda; o fluxo pode duplicar compras/fatura
-- e não inclui saldo inicial nem compromissos fora da tabela.
WITH usuario_mes AS (
  SELECT
    id_usuario,
    anomes,
    SUM(IF(tipo = 'E', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS entradas,
    SUM(IF(tipo = 'S', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS saidas
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1, 2
), usuario AS (
  SELECT
    id_usuario,
    COUNT(*) AS meses,
    COUNTIF(entradas < saidas) AS meses_fluxo_negativo
  FROM usuario_mes
  GROUP BY 1
)
SELECT
  COUNT(*) AS usuarios_elegiveis,
  COUNTIF(meses_fluxo_negativo = 0) AS usuarios_sem_mes_negativo,
  COUNTIF(meses_fluxo_negativo >= 9) AS usuarios_nove_ou_mais_meses_negativos,
  COUNTIF(meses_fluxo_negativo = 12) AS usuarios_todos_meses_negativos,
  APPROX_QUANTILES(meses_fluxo_negativo, 100)[OFFSET(50)] AS mediana_meses_negativos,
  (SELECT APPROX_QUANTILES(entradas - saidas, 100)[OFFSET(10)] FROM usuario_mes) AS p10_fluxo_mensal,
  (SELECT APPROX_QUANTILES(entradas - saidas, 100)[OFFSET(50)] FROM usuario_mes) AS p50_fluxo_mensal,
  (SELECT APPROX_QUANTILES(entradas - saidas, 100)[OFFSET(90)] FROM usuario_mes) AS p90_fluxo_mensal
FROM usuario
WHERE meses = 12;
