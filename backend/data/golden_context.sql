-- Golden mode only. Fixed readonly aggregates for the backend-bound identity.
-- Free descriptions never leave BigQuery; they only identify explicit CLT/labels.
WITH base AS (
  SELECT DATE(anomesdia) AS observed_date, tipo,
         SAFE_CAST(ROUND(vlr, 2) AS NUMERIC) AS amount,
         nom_cate_macro AS category, nom_cate_micro AS subcategory,
         REGEXP_REPLACE(NORMALIZE(LOWER(TRIM(nom_cate_micro)), NFD), r'\pM', '')
           AS normalized_subcategory,
         REGEXP_REPLACE(NORMALIZE(LOWER(TRIM(descr)), NFD), r'\pM', '')
           AS internal_description,
         parcela_atual, parcela_total
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  WHERE id_usuario = @user_id
    AND DATE(anomesdia) <= @reference_date
    AND DATE(anomesdia) BETWEEN @coverage_start AND @coverage_end
    AND DATE(anomesdia) >= DATE_SUB(DATE_TRUNC(@reference_date, MONTH), INTERVAL 5 MONTH)
), classified AS (
  SELECT *,
    tipo = 'E' AND (normalized_subcategory = 'salario clt'
                   OR internal_description = 'salario clt') AS explicit_clt_salary,
    tipo = 'S' AND subcategory != 'Pagamento de fatura' AS expense_without_invoice
  FROM base
), monthly AS (
  SELECT DATE_TRUNC(observed_date, MONTH) AS month,
         IF(COUNTIF(explicit_clt_salary) = 0, NULL,
            CAST(SUM(IF(explicit_clt_salary, amount, 0)) AS STRING)) AS salary_units,
         CAST(SUM(IF(expense_without_invoice, amount, 0)) AS STRING)
           AS expenses_excluding_invoice_units,
         CAST(SUM(IF(tipo = 'S' AND subcategory = 'Juros pagos', amount, 0)) AS STRING)
           AS interest_units
  FROM classified GROUP BY 1
), current_month AS (
  SELECT * FROM classified
  WHERE DATE_TRUNC(observed_date, MONTH) = DATE_TRUNC(@reference_date, MONTH)
), categories AS (
  SELECT category, CAST(SUM(amount) AS STRING) AS amount_units
  FROM current_month WHERE expense_without_invoice GROUP BY 1
), installments AS (
  SELECT CASE
           WHEN REGEXP_CONTAINS(internal_description, r'(^|[^a-z])iptu([^a-z]|$)') THEN 'IPTU'
           WHEN REGEXP_CONTAINS(internal_description, r'cia aerea') THEN 'Passagem aérea'
           WHEN REGEXP_CONTAINS(internal_description, r'art infant') THEN 'Artigos infantis'
           ELSE 'Parcela observada'
         END AS label,
         CAST(amount AS STRING) AS amount_units,
         SAFE_CAST(parcela_atual AS INT64) AS `current`,
         SAFE_CAST(parcela_total AS INT64) AS total,
         observed_date AS last_observed_date
  FROM current_month
  WHERE expense_without_invoice AND parcela_atual < parcela_total
)
SELECT TO_JSON_STRING(STRUCT(
  (SELECT MIN(observed_date) FROM base) AS coverage_start,
  (SELECT MAX(observed_date) FROM base) AS coverage_end,
  (SELECT COUNT(*) FROM base) AS row_count,
  (SELECT COUNTIF(
      amount IS NULL OR amount < 0 OR tipo IS NULL OR tipo NOT IN ('E', 'S')
      OR category IS NULL OR TRIM(category) = '' OR subcategory IS NULL OR TRIM(subcategory) = ''
      OR ((parcela_atual IS NULL) != (parcela_total IS NULL))
      OR parcela_atual <= 0 OR parcela_total <= 0 OR parcela_atual > parcela_total
      OR parcela_atual != ROUND(parcela_atual) OR parcela_total != ROUND(parcela_total)
    ) FROM base) AS invalid_rows,
  ARRAY(SELECT AS STRUCT * FROM monthly ORDER BY month LIMIT 6) AS monthly,
  ARRAY(SELECT AS STRUCT * FROM categories
        ORDER BY CAST(amount_units AS NUMERIC) DESC, category LIMIT 12) AS categories,
  ARRAY(SELECT AS STRUCT * FROM installments
        ORDER BY last_observed_date, label, amount_units, `current`, total LIMIT 12) AS installments,
  (SELECT COUNT(*) FROM categories) AS category_count,
  (SELECT COUNT(*) FROM installments) AS installment_count
)) AS summary_json
LIMIT 1
