-- MOD-13: resultado do teste de restauração mais recente.
SELECT started_at, finished_at, status, table_name,
       expected_row_count, restored_row_count
FROM tb_backup_restore_log
WHERE started_at = (SELECT MAX(started_at) FROM tb_backup_restore_log)
ORDER BY table_name;

-- MOD-13: resumo para um print compacto.
SELECT started_at, MAX(finished_at) AS finished_at,
       COUNT(*) AS checked_tables,
       COUNT(*) FILTER (WHERE status = 'SUCCESS'
                         AND expected_row_count = restored_row_count) AS matching_tables,
       COUNT(*) FILTER (WHERE status <> 'SUCCESS'
                         OR expected_row_count IS DISTINCT FROM restored_row_count) AS failures
FROM tb_backup_restore_log
WHERE started_at = (SELECT MAX(started_at) FROM tb_backup_restore_log)
GROUP BY started_at;

-- Dados de referência e catálogo atualizados.
SELECT 'tb_region' AS table_name, COUNT(*) AS rows FROM tb_region
UNION ALL SELECT 'tb_municipality', COUNT(*) FROM tb_municipality
UNION ALL SELECT 'tb_region_rate', COUNT(*) FROM tb_region_rate
UNION ALL SELECT 'tb_data_catalog', COUNT(*) FROM tb_data_catalog;
