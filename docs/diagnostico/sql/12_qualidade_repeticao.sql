-- 12 — Qualidade adicional: coerência de anomes/data e linhas idênticas.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 58.858.724 bytes.
-- Job bqjob_r7c0b0ecfda7cceae_000001a0df184ef9_1.
-- Processados: 58.858.724 bytes; faturados: 59.768.832 bytes.
-- Linhas idênticas NÃO são necessariamente duplicações indevidas sem ID de transação.
-- Comparação de anomes com DATE(TIMESTAMP) usa UTC.
WITH grupos AS (
  SELECT
    id_usuario, anomesdia, anomes, tipo, descr, vlr,
    nom_cate_macro, nom_cate_micro, saldo_apos, parcela_atual, parcela_total,
    COUNT(*) AS repeticoes
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1,2,3,4,5,6,7,8,9,10,11
)
SELECT
  SUM(repeticoes) AS lancamentos,
  COUNTIF(repeticoes > 1) AS grupos_identicos_repetidos,
  SUM(IF(repeticoes > 1, repeticoes - 1, 0)) AS linhas_excedentes_em_grupos_identicos,
  SUM(IF(anomes != EXTRACT(YEAR FROM DATE(anomesdia)) * 100 + EXTRACT(MONTH FROM DATE(anomesdia)), repeticoes, 0)) AS anomes_diferente_timestamp_utc,
  SUM(IF(tipo NOT IN ('E', 'S'), repeticoes, 0)) AS tipo_fora_E_S,
  SUM(IF(vlr <= 0, repeticoes, 0)) AS vlr_nao_positivo
FROM grupos;
