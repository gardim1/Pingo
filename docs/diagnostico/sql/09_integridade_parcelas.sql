-- 09 — Cobertura e integridade superficial dos campos estruturados de parcela.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 24.954.415 bytes.
-- Job bqjob_r24a83a105859b82e_000001a0df05dc10_1.
-- Processados: 24.954.415 bytes; faturados: 25.165.824 bytes.
-- Não infere valor da parcela futura, juros, vencimento ou contrato ativo.
SELECT
  COUNT(*) AS lancamentos,
  COUNTIF(parcela_atual IS NOT NULL OR parcela_total IS NOT NULL) AS lancamentos_com_parcela,
  COUNT(DISTINCT IF(parcela_atual IS NOT NULL OR parcela_total IS NOT NULL, id_usuario, NULL)) AS usuarios_com_parcela,
  COUNTIF((parcela_atual IS NULL) != (parcela_total IS NULL)) AS somente_um_campo,
  COUNTIF(parcela_atual <= 0 OR parcela_total <= 0) AS parcela_nao_positiva,
  COUNTIF(parcela_atual > parcela_total) AS atual_maior_que_total,
  COUNTIF(parcela_atual != ROUND(parcela_atual) OR parcela_total != ROUND(parcela_total)) AS parcela_nao_inteira,
  MIN(parcela_atual) AS menor_atual,
  MAX(parcela_atual) AS maior_atual,
  MIN(parcela_total) AS menor_total,
  MAX(parcela_total) AS maior_total,
  COUNT(DISTINCT IF(parcela_atual IS NOT NULL, nom_cate_macro, NULL)) AS macros_com_parcela
FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`;
