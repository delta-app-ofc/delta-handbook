### MOD-11 — Analisar consultas lentas com EXPLAIN ANALYZE e aplicar índices SQL para otimização

**Evidência direta:**

- [Script de criação dos índices](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-indexes.sql)
- [Índice da camada `stage`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/stage/indexes/idx_stage_consumption_summary_device_window.sql)
- [Índice da camada `gold`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/gold/indexes/idx_gold_dm_property_organization.sql)
- [Índice da tabela de auditoria](https://github.com/delta-app-ofc/delta-sql-database/tree/main/audit-tables/indexes)
- [Documentação da camada de BI, seção 7](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md)

**Localização e como comprovar:**

A análise usou `EXPLAIN (ANALYZE, BUFFERS)` para comparar o plano de execução antes e depois de cada índice. O volume real do banco é pequeno (de 14 a 400 linhas nas tabelas envolvidas), e nessa escala o PostgreSQL escolhe corretamente o `Seq Scan`. Por isso a medição foi feita também em um volume ampliado, em um PostgreSQL descartável criado só para o teste.

#### 1. Metodologia

1. Subir um PostgreSQL descartável e carregar o schema real, na ordem oficial de `setup_db.py`.
2. Inserir volume de teste identificado como tal (por exemplo `ORG_TESTE_UNICA`), compatível com anos de operação contínua. Esse volume nunca entra no `script-dataload.sql`.
3. Executar `ANALYZE` para atualizar as estatísticas do planner.
4. Executar a consulta real, a mesma da view ou procedure, com `EXPLAIN (ANALYZE, BUFFERS)` sem índice.
5. Criar o índice, executar `ANALYZE` novamente e repetir o `EXPLAIN (ANALYZE, BUFFERS)`.
6. Comparar os dois planos, sem usar `SET enable_seqscan = off` para forçar o resultado.

#### 2. Índices aplicados e ganho medido

| Índice | Consulta analisada | Sem índice | Com índice | Ganho |
|---|---|---|---|---|
| `idx_stage_consumption_summary_device_window` | Histórico de um dispositivo, `WHERE device_id = X ORDER BY window_started_at DESC LIMIT 20` | Parallel Seq Scan, 4.690 buffers, 52,000 ms | Index Scan, 23 buffers, 0,144 ms | ~360x |
| `idx_gold_dm_property_organization` | Filtro por organização, `WHERE organization_name = X` | Parallel Seq Scan, 4.684 buffers, 19,588 ms | Index Scan, 4 buffers, 0,070 ms | ~280x |
| `idx_log_region_rate_previous_log_id` | CTE recursiva `dw.vw_audit_history_chain` sobre 500.342 linhas | Merge Join com sort em disco a cada nível, 69.417 ms | Index Scan, 1.134 ms | ~61x |

O terceiro índice cobre a chave estrangeira autorreferenciada `previous_log_id`. O PostgreSQL cria índice automático só no lado referenciado (a `PRIMARY KEY`), e a CTE recursiva percorre justamente o lado que referencia.

#### 3. Views em que o índice não se aplica

As sete views do schema `dw` foram analisadas uma a uma em volume de até 730.000 linhas em `gold.ft_consumption_daily`. Seis delas agregam ou ranqueiam 100% das linhas de entrada, e nesses casos `Seq Scan` é o plano correto, sem filtro que um índice possa explorar. A sétima, `vw_audit_history_chain`, foi a que gerou o terceiro índice.

#### 4. Como comprovar

1. Executar os scripts na ordem de `setup_db.py` até `script-indexes.sql`.
2. Executar `\di` e conferir os três índices.
3. Executar `EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM gold.dm_property WHERE organization_name = 'SWIFT DISTRIBUIDORA';` e conferir o plano.
4. Para reproduzir o ganho, repetir a metodologia da seção 1 com volume ampliado.
