-- Fixed, read-only query. Identifiers never come from the model or request.
-- descr is used exclusively inside BigQuery to identify recurrence candidates.
WITH base AS (
  SELECT DATE(anomesdia) AS observed_date, tipo,
         SAFE_CAST(ROUND(vlr, 2) AS NUMERIC) AS amount,
         nom_cate_macro AS category, nom_cate_micro AS subcategory,
         LOWER(TRIM(descr)) AS internal_description,
         parcela_atual, parcela_total
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  WHERE id_usuario = @user_id
    AND DATE(anomesdia) <= @reference_date
    AND DATE(anomesdia) BETWEEN @coverage_start AND @coverage_end
), monthly AS (
  SELECT DATE_TRUNC(observed_date, MONTH) AS month,
         COUNTIF(tipo = 'E') AS entry_count,
         COUNTIF(tipo = 'S') AS exit_count,
         CAST(SUM(IF(tipo = 'E', amount, 0)) AS STRING) AS entry_units,
         CAST(SUM(IF(tipo = 'S', amount, 0)) AS STRING) AS exit_units,
         CAST(SUM(IF(tipo = 'S' AND category = 'Produtos financeiros'
                     AND subcategory = 'Pagamento de fatura', amount, 0)) AS STRING)
           AS invoice_payment_units,
         CAST(SUM(IF(tipo = 'S' AND category = 'Transferencias diversas', amount, 0)) AS STRING)
           AS transfer_exit_units
  FROM base GROUP BY 1
), categories AS (
  SELECT category, tipo AS direction, COUNT(*) AS count,
         CAST(SUM(amount) AS STRING) AS amount_units
  FROM base GROUP BY 1, 2
), recurring_monthly AS (
  SELECT internal_description, category, subcategory,
         DATE_TRUNC(observed_date, MONTH) AS month,
         MAX(observed_date) AS last_observed_date,
         COUNT(*) AS observations, SUM(amount) AS amount
  FROM base
  WHERE tipo = 'S' AND internal_description IS NOT NULL AND internal_description != ''
  GROUP BY 1, 2, 3, 4
), recurring_sequence AS (
  SELECT *, LAG(month) OVER (
    PARTITION BY internal_description, category, subcategory ORDER BY month
  ) AS previous_month
  FROM recurring_monthly WHERE observations = 1
), recurrence_groups AS (
  SELECT category, subcategory, internal_description,
         COUNT(*) AS months_observed,
         COUNTIF(DATE_DIFF(month, previous_month, MONTH) = 1) AS consecutive_pairs,
         MIN(amount) AS min_amount, MAX(amount) AS max_amount,
         MAX(last_observed_date) AS last_observed_date
  FROM recurring_sequence GROUP BY 1, 2, 3
), recurrence_candidates AS (
  SELECT subcategory AS category, months_observed, consecutive_pairs,
         CAST(min_amount AS STRING) AS min_units,
         CAST(max_amount AS STRING) AS max_units, last_observed_date
  FROM recurrence_groups
  WHERE months_observed >= 3 AND consecutive_pairs >= 2
    AND max_amount <= min_amount * NUMERIC '1.2'
), observed_installments AS (
  SELECT category, COUNT(*) AS count,
         MIN(observed_date) AS first_observed_date,
         MAX(observed_date) AS last_observed_date,
         SAFE_CAST(MIN(parcela_atual) AS INT64) AS min_installment_index,
         SAFE_CAST(MAX(parcela_atual) AS INT64) AS max_installment_index,
         SAFE_CAST(MAX(parcela_total) AS INT64) AS max_installment_total,
         CAST(SUM(amount) AS STRING) AS observed_units
  FROM base WHERE parcela_atual IS NOT NULL OR parcela_total IS NOT NULL
  GROUP BY 1
)
SELECT TO_JSON_STRING(STRUCT(
  (SELECT MIN(observed_date) FROM base) AS coverage_start,
  (SELECT MAX(observed_date) FROM base) AS coverage_end,
  (SELECT COUNT(*) FROM base) AS row_count,
  (SELECT COUNTIF(
      amount IS NULL OR amount < 0 OR tipo IS NULL OR tipo NOT IN ('E', 'S')
      OR category IS NULL OR TRIM(category) = ''
      OR ((parcela_atual IS NULL) != (parcela_total IS NULL))
      OR parcela_atual <= 0 OR parcela_total <= 0 OR parcela_atual > parcela_total
      OR parcela_atual != ROUND(parcela_atual) OR parcela_total != ROUND(parcela_total)
    ) FROM base) AS invalid_rows,
  ARRAY(SELECT AS STRUCT * FROM monthly ORDER BY month LIMIT 12) AS monthly,
  ARRAY(SELECT AS STRUCT * FROM categories ORDER BY count DESC, category, direction LIMIT 12)
    AS categories,
  ARRAY(SELECT AS STRUCT * FROM recurrence_candidates
        ORDER BY months_observed DESC, category, last_observed_date DESC LIMIT 10)
    AS recurrence_candidates,
  ARRAY(SELECT AS STRUCT * FROM observed_installments
        ORDER BY count DESC, category LIMIT 12) AS observed_installments
)) AS summary_json
LIMIT 1
