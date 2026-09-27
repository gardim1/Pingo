-- 01 — Schema da tabela, via metadados. NÃO EXECUTADA nesta preparação.
-- Finalidade: confirmar todas as colunas, tipos, nulabilidade e ordem antes de consultas de dados.
-- Executar na localização correta do dataset, a ser confirmada por `bq show`/console.
SELECT
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM `batalha-time-08-g7ha.hackathon_dados.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'extrato_sintetico'
ORDER BY ordinal_position;
