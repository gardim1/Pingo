-- 08 — Regularidade de datas e totais mensais de E; E não equivale a renda.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 30.393.025 bytes.
-- Job bqjob_r74c026093759c784_000001a0df032591_1.
-- Processados: 30.393.025 bytes; faturados: 30.408.704 bytes.
-- Elegibilidade: 12 meses observados com ao menos uma entrada em cada mês.
WITH usuario_mes AS (
  SELECT
    id_usuario,
    anomes,
    MIN(IF(tipo = 'E', EXTRACT(DAY FROM DATE(anomesdia)), NULL)) AS primeiro_dia_entrada,
    SUM(IF(tipo = 'E', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS total_entradas,
    COUNTIF(tipo = 'E') AS quantidade_entradas
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1, 2
), usuario AS (
  SELECT
    id_usuario,
    COUNT(*) AS meses,
    MIN(primeiro_dia_entrada) AS primeiro_dia_min,
    MAX(primeiro_dia_entrada) AS primeiro_dia_max,
    MIN(total_entradas) AS total_min,
    MAX(total_entradas) AS total_max,
    MIN(quantidade_entradas) AS quantidade_min,
    MAX(quantidade_entradas) AS quantidade_max
  FROM usuario_mes
  GROUP BY 1
  HAVING meses = 12 AND COUNTIF(quantidade_entradas > 0) = 12
)
SELECT
  COUNT(*) AS usuarios_elegiveis,
  COUNTIF(primeiro_dia_max - primeiro_dia_min <= 3) AS primeiro_dia_faixa_ate_3,
  COUNTIF(primeiro_dia_max - primeiro_dia_min <= 7) AS primeiro_dia_faixa_ate_7,
  COUNTIF(total_max > total_min * 1.5) AS total_entrada_variou_mais_50pct,
  COUNTIF(quantidade_max > quantidade_min) AS quantidade_entrada_variou,
  APPROX_QUANTILES(SAFE_DIVIDE(total_max, NULLIF(total_min, 0)), 100)[OFFSET(50)] AS mediana_razao_max_min_entradas
FROM usuario;
