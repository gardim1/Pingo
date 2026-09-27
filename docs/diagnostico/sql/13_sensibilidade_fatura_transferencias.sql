-- 13 — Sensibilidade do sinal de timing ao excluir fatura e transferências das saídas.
-- EXECUTADA em 2026-09-26 como 12ª e última consulta de dados da rodada.
-- Dry-run: 44.848.971 bytes; job bqjob_r8e00195ffee6052_000001a0df1fe640_1.
-- Processados: 44.848.971 bytes; faturados: 45.088.768 bytes.
-- Teto de 1 GiB aplicado. Excluir não equivale a conciliação contábil:
-- pode remover compromissos reais e ainda restar dupla contagem.
WITH diario AS (
  SELECT
    id_usuario,
    anomes,
    DATE(anomesdia) AS dia,
    SUM(IF(tipo = 'E', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS entradas,
    SUM(IF(tipo = 'S', SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0)) AS saidas_todas,
    SUM(IF(
      tipo = 'S'
      AND nom_cate_macro != 'Transferencias diversas'
      AND NOT (nom_cate_macro = 'Produtos financeiros' AND nom_cate_micro = 'Pagamento de fatura'),
      SAFE_CAST(ROUND(vlr, 2) AS NUMERIC), 0
    )) AS saidas_ajustadas
  FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
  GROUP BY 1, 2, 3
), sequencia AS (
  SELECT
    *,
    MIN(IF(entradas > 0, dia, NULL)) OVER (PARTITION BY id_usuario, anomes) AS primeira_entrada,
    SUM(entradas - saidas_ajustadas) OVER (
      PARTITION BY id_usuario, anomes ORDER BY dia ROWS UNBOUNDED PRECEDING
    ) AS variacao_ajustada_acumulada
  FROM diario
), usuario_mes AS (
  SELECT
    id_usuario,
    anomes,
    SUM(entradas) AS entradas,
    SUM(saidas_todas) AS saidas_todas,
    SUM(saidas_ajustadas) AS saidas_ajustadas,
    SUM(IF(dia < primeira_entrada, saidas_todas, 0)) AS saidas_antes_todas,
    SUM(IF(dia < primeira_entrada, saidas_ajustadas, 0)) AS saidas_antes_ajustadas,
    MIN(variacao_ajustada_acumulada) AS menor_variacao_ajustada
  FROM sequencia
  GROUP BY 1, 2
)
SELECT
  COUNT(*) AS usuario_meses,
  COUNTIF(saidas_antes_todas > 0) AS meses_saida_antes_todas,
  COUNTIF(saidas_antes_ajustadas > 0) AS meses_saida_antes_ajustadas,
  COUNTIF(entradas >= saidas_ajustadas) AS meses_final_ajustado_nao_negativo,
  COUNTIF(entradas >= saidas_ajustadas AND menor_variacao_ajustada < 0) AS meses_final_ajustado_com_vale,
  COUNT(DISTINCT IF(saidas_antes_ajustadas > 0, id_usuario, NULL)) AS usuarios_ao_menos_um_mes_ajustado
FROM usuario_mes;
