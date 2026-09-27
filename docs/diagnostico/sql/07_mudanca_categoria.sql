-- 07 — Mudança no próprio histórico por macrocategoria, sem usar descrições.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 33.360.978 bytes.
-- Job bqjob_r174196c94ae5eb4f_000001a0df00c155_1.
-- Processados: 33.360.978 bytes; faturados: 33.554.432 bytes.
-- Compara jan-jun e jul-dez de 2025 (seis meses equivalentes). Exige >=3
-- lançamentos em cada metade por usuário/categoria. Resultados são pares
-- usuário-categoria, não usuários únicos entre categorias.
WITH base AS (
  SELECT
    id_usuario,
    nom_cate_macro,
    IF(MOD(anomes, 100) <= 6, 1, 2) AS semestre,
    SAFE_CAST(ROUND(vlr, 2) AS NUMERIC) AS valor
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  WHERE tipo = 'S' AND anomes BETWEEN 202501 AND 202512
), comparacao AS (
  SELECT
    id_usuario,
    nom_cate_macro,
    COUNTIF(semestre = 1) AS n1,
    COUNTIF(semestre = 2) AS n2,
    SUM(IF(semestre = 1, valor, 0)) AS v1,
    SUM(IF(semestre = 2, valor, 0)) AS v2
  FROM base
  GROUP BY 1, 2
)
SELECT
  nom_cate_macro,
  COUNT(*) AS pares_elegiveis,
  COUNTIF(v2 >= v1 * 1.3) AS pares_valor_30pct_maior,
  COUNTIF(n2 >= n1 * 1.3) AS pares_frequencia_30pct_maior,
  COUNTIF(v2 * n1 >= v1 * n2 * 1.3) AS pares_ticket_medio_30pct_maior,
  APPROX_QUANTILES(SAFE_DIVIDE(v2, v1), 100)[OFFSET(50)] AS mediana_razao_valor,
  APPROX_QUANTILES(SAFE_DIVIDE(n2, n1), 100)[OFFSET(50)] AS mediana_razao_frequencia
FROM comparacao
WHERE n1 >= 3 AND n2 >= 3
GROUP BY 1
ORDER BY pares_elegiveis DESC;
