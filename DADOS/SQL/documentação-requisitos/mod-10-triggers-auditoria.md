### MOD-10 — Criar triggers de auditoria em ao menos duas tabelas com logs completos NEW, OLD, TG_OP e CURRENT_USER

**Evidência direta:**

- [Script de auditoria](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-audit.sql)
- [Tabelas de auditoria](https://github.com/delta-app-ofc/delta-sql-database/tree/main/audit-tables)
- [Functions de auditoria](https://github.com/delta-app-ofc/delta-sql-database/tree/main/audit-functions)
- [Triggers de auditoria](https://github.com/delta-app-ofc/delta-sql-database/tree/main/triggers)
- [Documentação da auditoria](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/auditoria.md)
- [Diagrama das tabelas de auditoria](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica-log.png)

**Localização e como comprovar:**

A auditoria cobre **21 tabelas**. Cada tabela auditada tem três peças: uma tabela de log (`tb_log_*`), uma Function de auditoria (`fn_log_*`) e um trigger (`trg_log_*`) `AFTER INSERT OR UPDATE OR DELETE ... FOR EACH ROW`.

Exemplo da tarifa regional:

| Peça | Arquivo |
|---|---|
| Tabela de log | `audit-tables/tb_log_region_rate.sql` |
| Function | `audit-functions/fn_log_region_rate.sql` |
| Trigger | `triggers/trg_log_region_rate.sql` |

#### 1. O que cada log registra

| Elemento | Onde aparece | Uso |
|---|---|---|
| `TG_OP` | coluna `operation` | Informa se a operação foi `INSERT`, `UPDATE` ou `DELETE` |
| `NEW` | valores gravados nas colunas do log em `INSERT` e `UPDATE` | Estado do registro depois da operação |
| `OLD` | valores gravados em `DELETE` e comparados em `UPDATE` | Estado do registro antes da operação |
| `CURRENT_USER` | coluna `executed_by` | Usuário do banco que executou a operação |
| `CURRENT_TIMESTAMP` | coluna `executed_at` | Momento da operação |
| `previous_log_id` | coluna autorreferenciada | Liga cada log ao log anterior do mesmo registro |

Em `UPDATE`, a Function compara `OLD` e `NEW` campo a campo e descreve o que mudou em `log_description`.

#### 2. Tabelas auditadas

`tb_user`, `tb_address`, `tb_property`, `tb_device`, `tb_habit`, `tb_user_habit`, `tb_user_habit_day`, `tb_user_property`, `tb_last_water_bill`, `tb_region`, `tb_region_rate`, `tb_day_of_week`, `tb_property_classification`, `tb_organization`, `tb_user_organization`, `tb_property_operational_profile`, `tb_property_shift`, `tb_water_usage_type`, `tb_property_water_usage`, `tb_property_operation_day` e `tb_investment_scenario`.

#### 3. Como comprovar

1. Executar `script-schema.sql`, `script-optimization.sql` e `script-audit.sql`.
2. Executar `INSERT`, `UPDATE` e `DELETE` em uma tabela auditada, por exemplo `tb_region_rate`.
3. Consultar `SELECT operation, executed_by, executed_at, log_description FROM tb_log_region_rate ORDER BY id;`.
4. Conferir uma linha por operação, com `executed_by` preenchido por `CURRENT_USER`.

O `TRUNCATE` não é auditado porque remove registros em massa e não expõe `OLD` e `NEW` linha a linha.
