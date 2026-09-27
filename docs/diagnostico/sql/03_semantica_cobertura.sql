-- 03 — Tipo, sinal de valor e cobertura de campos estruturados.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 23.817.613 bytes.
-- Job: bqjob_r1ddccd4e12eff57e_000001a0def69d6c_1.
-- Processados: 23.817.613 bytes; faturados: 24.117.248 bytes.
-- Não presume que tipo=E seja renda nem que saldo_apos seja saldo atual.
SELECT
  tipo,
  COUNT(*) AS lancamentos,
  COUNTIF(vlr > 0) AS vlr_positivo,
  COUNTIF(vlr < 0) AS vlr_negativo,
  COUNTIF(vlr = 0) AS vlr_zero,
  COUNTIF(nom_cate_macro IS NULL OR LENGTH(TRIM(nom_cate_macro)) = 0) AS macro_ausente,
  COUNTIF(nom_cate_micro IS NULL OR LENGTH(TRIM(nom_cate_micro)) = 0) AS micro_ausente,
  COUNTIF(saldo_apos IS NOT NULL) AS saldo_apos_presente,
  COUNTIF(saldo_apos < 0) AS saldo_apos_negativo,
  COUNTIF(parcela_atual IS NOT NULL) AS parcela_atual_presente,
  COUNTIF(parcela_total IS NOT NULL) AS parcela_total_presente,
  COUNTIF(parcela_atual > 0 AND parcela_total > 0) AS parcelas_positivas,
  COUNT(DISTINCT nom_cate_macro) AS categorias_macro_distintas,
  COUNT(DISTINCT nom_cate_micro) AS categorias_micro_distintas
FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
GROUP BY 1
ORDER BY lancamentos DESC;
