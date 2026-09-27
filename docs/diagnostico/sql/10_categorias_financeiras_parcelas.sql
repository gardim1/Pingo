-- 10 — Categorias estruturadas ligadas a parcelas ou possíveis custos financeiros.
-- EXECUTADA em 2026-09-26, us-central1. Dry-run: 33.865.707 bytes.
-- Job bqjob_r542044f63e149e9_000001a0df0b9803_1.
-- Processados: 33.865.707 bytes; faturados: 34.603.008 bytes.
-- Nomes de categoria são rótulos sintéticos, não prova de cobrança, taxa ou dívida.
-- Nenhuma descrição livre nem ID individual é retornado.
SELECT
  nom_cate_macro,
  nom_cate_micro,
  tipo,
  COUNT(*) AS lancamentos,
  COUNT(DISTINCT id_usuario) AS usuarios,
  COUNTIF(parcela_atual IS NOT NULL) AS lancamentos_com_parcela
FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`
WHERE parcela_atual IS NOT NULL
  OR REGEXP_CONTAINS(
    LOWER(CONCAT(COALESCE(nom_cate_macro, ''), ' ', COALESCE(nom_cate_micro, ''))),
    r'juro|encargo|tarifa|cr[eé]dito|empr[eé]st|financi|fatura|cart[aã]o'
  )
GROUP BY 1, 2, 3
ORDER BY lancamentos_com_parcela DESC, lancamentos DESC
LIMIT 40;
