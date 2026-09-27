-- 02 — Contagens e período. EXECUTADA em 2026-09-26, us-central1.
-- Antes de executar: dry-run/estimativa, maximum_bytes_billed=1073741824,
-- registrar bytes estimados no acumulado máximo de 5 GiB.
-- Dry-run: 28.990.270 bytes; job bqjob_r4199df9a7d8b9498_000001a0deecee86_1.
-- Processados: 28.990.270 bytes; faturados: 29.360.128 bytes.
-- Finalidade: verificar número de lançamentos/pessoas, período e nulos essenciais, sem retornar IDs.
SELECT
  COUNT(*) AS total_lancamentos,
  COUNT(DISTINCT id_usuario) AS total_usuarios,
  MIN(anomesdia) AS primeiro_timestamp,
  MAX(anomesdia) AS ultimo_timestamp,
  MIN(anomes) AS primeiro_anomes,
  MAX(anomes) AS ultimo_anomes,
  COUNT(DISTINCT anomes) AS total_anomes,
  COUNTIF(id_usuario IS NULL) AS usuarios_nulos,
  COUNTIF(anomesdia IS NULL) AS timestamps_nulos,
  COUNTIF(anomes IS NULL) AS anomes_nulos,
  COUNTIF(vlr IS NULL) AS valores_nulos
FROM `batalha-time-08-g7ha.hackathon_dados.extrato_sintetico`;
