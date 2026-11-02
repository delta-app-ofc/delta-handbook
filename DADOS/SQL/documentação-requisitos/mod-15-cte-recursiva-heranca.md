### MOD-15 — Implementar, onde fizer sentido, CTE recursiva ou herança de tabelas

**Evidência direta:**

- [View com CTE recursiva `dw.vw_audit_history_chain`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_audit_history_chain.sql)
- [Tabela de auditoria `tb_log_region_rate`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/audit-tables/tb_log_region_rate.sql)
- [Function de auditoria que preenche `previous_log_id`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/audit-functions/fn_log_region_rate.sql)
- [Índice de apoio à recursão](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-indexes.sql)
- [Documentação da camada de BI, seção 6](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md)

**Localização e como comprovar:**

A estrutura avançada escolhida foi a **CTE recursiva**, aplicada ao histórico de reajustes de tarifa.

#### 1. Onde faz sentido

Cada alteração em `tb_region_rate` gera uma linha em `tb_log_region_rate`, e a Function `fn_log_region_rate` preenche `previous_log_id` com o log anterior do mesmo registro. O resultado é uma lista encadeada: o primeiro log tem `previous_log_id` nulo, e cada log seguinte aponta para o anterior.

Percorrer essa cadeia exige um número de passos que não é conhecido de antemão. A CTE recursiva resolve isso em uma única consulta.

```sql
WITH RECURSIVE chain AS (
    SELECT id, region_rate_id, m3_value, operation, executed_by, executed_at, previous_log_id, 1 AS level
    FROM tb_log_region_rate
    WHERE previous_log_id IS NULL

    UNION ALL

    SELECT l.id, l.region_rate_id, l.m3_value, l.operation, l.executed_by, l.executed_at,
           l.previous_log_id, c.level + 1
    FROM tb_log_region_rate l
    JOIN chain c ON l.previous_log_id = c.id
)
SELECT id AS log_id, region_rate_id, m3_value, operation, executed_by, executed_at, level
FROM chain;
```

O membro âncora seleciona os logs iniciais, o membro recursivo acrescenta os logs seguintes, e `level` informa a profundidade na cadeia.

#### 2. Por que não herança de tabelas

A herança (`INHERITS`) foi testada em `tb_property_operational_profile` e descartada. As chaves estrangeiras de outras tabelas para `tb_property(id)` não enxergam as linhas da tabela filha, porque o PostgreSQL trata pai e filha como relações separadas para integridade referencial. O perfil operacional passou a ser uma extensão 1:1, com `property_id` como chave primária e estrangeira ao mesmo tempo. O domínio também não possui uma hierarquia de tipos que justifique herança.

#### 3. Desempenho

O índice `idx_log_region_rate_previous_log_id` apoia a recursão. Em 500.342 linhas de log, o tempo da view caiu de 69.417 ms para 1.134 ms (MOD-11).

#### 4. Como comprovar

1. Executar os scripts na ordem de `setup_db.py`. O dataload faz 1 `INSERT` e 2 `UPDATE` na mesma tarifa, e cada operação dispara o trigger de auditoria.
2. Executar a CTE recursiva da seção 1 sobre a tabela de log, filtrando a tarifa:

```sql
WITH RECURSIVE chain AS (
    SELECT id, region_rate_id, operation, previous_log_id, 1 AS level
    FROM tb_log_region_rate
    WHERE previous_log_id IS NULL AND region_rate_id = 5
    UNION ALL
    SELECT l.id, l.region_rate_id, l.operation, l.previous_log_id, c.level + 1
    FROM tb_log_region_rate l
    JOIN chain c ON l.previous_log_id = c.id
)
SELECT id, operation, level FROM chain ORDER BY level;
```

3. Conferir três linhas, com `level` 1, 2 e 3, e `INSERT` seguido de dois `UPDATE`.

O MOD-10 e o MOD-15 usam a mesma Function de auditoria, `fn_log_region_rate`: o MOD-10 comprova o registro de `TG_OP`, `OLD`, `NEW` e `CURRENT_USER`, e o MOD-15 percorre a cadeia de `previous_log_id` que essa Function preenche. A view `dw.vw_audit_history_chain` encapsula essa mesma consulta.
