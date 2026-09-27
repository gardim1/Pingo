-- 06 — Candidatos a repetição regular de despesas; não são obrigações futuras confirmadas.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 44.191.179 bytes.
-- Job bqjob_r51bab02a3c1bb5b1_000001a0defe44e3_1.
-- Processados: 44.191.179 bytes; faturados: 45.088.768 bytes.
-- Critério: mesma pessoa, descrição normalizada e microcategoria; exatamente uma
-- saída por mês em pelo menos três meses; ao menos dois pares de meses consecutivos;
-- maior valor até 20% acima do menor valor. Descrição usada somente dentro do Google.
WITH mensal AS (
  SELECT
    id_usuario,
    LOWER(TRIM(descr)) AS chave_descricao,
    nom_cate_micro,
    DATE(DIV(anomes, 100), MOD(anomes, 100), 1) AS mes,
    COUNT(*) AS lancamentos,
    SUM(SAFE_CAST(ROUND(vlr, 2) AS NUMERIC)) AS valor_mes
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  WHERE tipo = 'S' AND descr IS NOT NULL AND LENGTH(TRIM(descr)) > 0
  GROUP BY 1, 2, 3, 4
), unicos_mes AS (
  SELECT * FROM mensal WHERE lancamentos = 1
), sequencia AS (
  SELECT
    *,
    LAG(mes) OVER (
      PARTITION BY id_usuario, chave_descricao, nom_cate_micro ORDER BY mes
    ) AS mes_anterior
  FROM unicos_mes
), grupos AS (
  SELECT
    id_usuario,
    chave_descricao,
    nom_cate_micro,
    COUNT(*) AS meses,
    COUNTIF(DATE_DIFF(mes, mes_anterior, MONTH) = 1) AS pares_consecutivos,
    MIN(valor_mes) AS menor_valor,
    MAX(valor_mes) AS maior_valor
  FROM sequencia
  GROUP BY 1, 2, 3
)
SELECT
  COUNTIF(meses >= 3) AS grupos_tres_meses,
  COUNTIF(meses >= 3 AND pares_consecutivos >= 2 AND maior_valor <= menor_valor * 1.2) AS candidatos_estritos,
  COUNT(DISTINCT IF(meses >= 3 AND pares_consecutivos >= 2 AND maior_valor <= menor_valor * 1.2, id_usuario, NULL)) AS usuarios_com_candidato,
  SUM(IF(meses >= 3 AND pares_consecutivos >= 2 AND maior_valor <= menor_valor * 1.2, meses, 0)) AS lancamentos_candidatos,
  APPROX_QUANTILES(
    IF(meses >= 3 AND pares_consecutivos >= 2 AND maior_valor <= menor_valor * 1.2, meses, NULL), 100
  )[OFFSET(50)] AS mediana_meses_candidato
FROM grupos;
