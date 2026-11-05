### MOD-06 — Usar CTEs na lógica de transformação ETL em SQL

**Evidência direta:**

- [Procedure de transformação com CTE (`silver.sp_load_ft_consumption_daily`)](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/silver/procedures/sp_load_ft_consumption_daily.sql)
- [Views analíticas com CTEs](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views)
- [Script do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart.sql)
- [Documentação da camada de BI, seção 5](../camada-bi.md)
- [Resultado da view com CTE `vw_ft_consumption_daily`](../anexos/evidencias-requisitos/mod-06-view-consumo-diario.png)
- [ETL MongoDB → Stage (`bi_etl.py`)](https://github.com/delta-app-ofc/delta-sql-database/blob/main/bi_etl.py)

**Localização e como comprovar:**

As CTEs (`WITH`) organizam a transformação em etapas legíveis, uma por responsabilidade. Elas aparecem na procedure de transformação do ETL e em várias views do schema `dw`.

#### 1. CTE na transformação ETL

`silver.sp_load_ft_consumption_daily` usa uma CTE para agregar as leituras por propriedade e dia antes do `INSERT`. A CTE soma os litros de todos os dispositivos da propriedade, e o `INSERT` apenas grava o resultado já calculado.

#### 2. CTEs nas views analíticas

| View | Uso da CTE |
|---|---|
| `vw_ft_consumption_daily` | Monta os `JOIN`s de propriedade e data antes das window functions |
| `vw_ft_property_ranking` | Duas CTEs em cadeia: agrega consumo e custo, depois calcula litros por m² |
| `vw_ft_consumption_distribution` | Agrega os totais diários e calcula os percentis em uma CTE separada |
| `vw_ft_monthly_variation` | Agrega por mês antes de aplicar `LAG()` |
| `vw_ft_capex_comparison` | CTE simples, por padronização |
| `vw_ft_residential_efficiency_ranking` | Monta os `JOIN`s antes dos rankings |
| `vw_audit_history_chain` | `WITH RECURSIVE` (MOD-15) |
| `vw_ft_user_goal` | Agrega a média dos últimos 30 dias por pessoa antes de compará-la à meta |

`vw_ft_alert` usa um `SELECT` direto, sem CTE.

O pipeline Python e as procedures SQL têm papéis separados: `bi_etl.py` extrai documentos MongoDB e insere/atualiza tabelas `stage`; as procedures `silver.sp_load_*` e `gold.sp_load_*` transformam e carregam as camadas analíticas. A existência de CTE nas procedures comprova a técnica de transformação SQL, mas não prova que o job Python rodou contra bancos reais. Essa confirmação depende do log do workflow e de contagens/IDs nas tabelas de destino, como detalhado em [camada de BI](../camada-bi.md#escopo-do-etl-e-evidencia-de-gravacao).

#### 3. Por que CTEs

O PostgreSQL permite `JOIN` no `FROM` e window functions no `SELECT` da mesma consulta. As CTEs foram escolhidas para organizar agregações e cálculos em etapas legíveis e, quando necessário, criar outro nível de consulta. Ela também evita repetir expressões, como a divisão litros por m², em cada `OVER`.

#### 4. Como comprovar

1. Abrir `datamart/silver/procedures/sp_load_ft_consumption_daily.sql` e localizar o `WITH`.
2. Abrir `datamart/dw/views/vw_ft_consumption_daily.sql` e localizar o `WITH`.
3. Executar `CALL silver.sp_load();`, depois `CALL gold.sp_load();` e consultar `SELECT * FROM dw.vw_ft_monthly_variation;` para ver o resultado das etapas.
