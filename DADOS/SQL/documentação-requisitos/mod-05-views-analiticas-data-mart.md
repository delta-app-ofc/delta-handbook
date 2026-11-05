### MOD-05 — Criar views analíticas para Data Mart, com modelagem dimensional Star Schema ou Snowflake

**Evidência direta:**

- [Script de criação do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart.sql)
- [Pasta das camadas do Data Mart (`stage`, `silver`, `gold`, `dw`)](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart)
- [Views analíticas do schema `dw`](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views)
- [Script de carga do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart-dataload.sql)
- [Documentação da camada de BI](../camada-bi.md)
- [Diagrama da camada analítica](../anexos/modelagem-logica-camada-analitica.png)

- [Print das nove views do schema dw](../anexos/evidencias-requisitos/mod-05-views-dw.png)

**Localização e como comprovar:**

O Data Mart está no mesmo PostgreSQL do banco relacional e é criado pelo `script-datamart.sql`, que organiza os dados em quatro schemas (arquitetura medalhão):

| Schema | Papel | Materialização |
|---|---|---|
| `stage` | Dados brutos do MongoDB: `consumption_summary`, `user_preferences` e `alerts_history` | Tabela |
| `silver` | Dado tratado, tipado e deduplicado, no grão original | Tabela |
| `gold` | Modelo dimensional (Star Schema) com chaves substitutas | Tabela |
| `dw` | Camada de consumo do BI | Views |

#### 1. Modelo dimensional (Star Schema)

O núcleo do schema `gold` organiza consumo, faturas e alertas em Star Schema, compartilhando `gold.dm_date`. A extensão `gold.dm_user_preference` referencia `gold.dm_person`, formando uma relação adicional entre dimensões para as metas.

- **Dimensões:** `gold.dm_date` (1 linha por dia), `gold.dm_property` (1 linha por propriedade) e `gold.dm_person` (1 linha por pessoa), além de `gold.dm_user_preference` (preferências por pessoa).
- **Fatos:** `gold.ft_consumption_daily` (propriedade × dia), `gold.ft_water_bill_monthly` (pessoa × mês), `gold.ft_investment_scenario` (cenário de investimento, fato sem dimensão de tempo) e `gold.ft_alert` (ocorrência de alerta).

O nome da organização fica denormalizado em `gold.dm_property` (`organization_name`). Essa decisão preserva o núcleo em estrela sem criar uma dimensão separada de organização.

#### 2. Views analíticas (`dw`)

O schema `dw` contém **nove views**. As views analíticas leem `gold`; `vw_ft_user_goal` também consulta `tb_user_property` para associar consumo à pessoa. A view `vw_audit_history_chain` lê diretamente o log de auditoria:

| View | O que entrega |
|---|---|
| `dw.vw_ft_consumption_daily` | Consumo diário com total acumulado e média móvel de 7 dias |
| `dw.vw_ft_property_ranking` | Ranking de eficiência (L/m²) e custo por propriedade |
| `dw.vw_ft_monthly_variation` | Variação percentual mês a mês |
| `dw.vw_ft_consumption_distribution` | Quartis, quintis e percentis do consumo |
| `dw.vw_ft_capex_comparison` | Comparação dos cenários de investimento por payback |
| `dw.vw_ft_residential_efficiency_ranking` | Ranking de consumo residencial por mês |
| `dw.vw_audit_history_chain` | Cadeia histórica de reajustes de tarifa (CTE recursiva, MOD-15) |
| `dw.vw_ft_alert` | Alertas por propriedade e pessoa, com severidade e tempo de resolução em minutos |
| `dw.vw_ft_user_goal` | Consumo médio dos últimos 30 dias de cada pessoa comparado à meta diária de litros |

Na branch de indicadores `feat/indicadores-views-medalhao`, há views adicionais de metas e organização, como `vw_ft_property_monthly`, `vw_ft_organization_monthly_kpi`, `vw_ft_organization_esg`, `vw_ft_monitoring_hourly`, `vw_ft_leak`, `vw_ft_device_status`, `vw_ft_organization_device_summary` e `vw_ft_investment_impact`. A presença delas nessa branch não significa que façam parte da `main` ou do banco publicado. A lista acima descreve a versão do requisito documentada nesta branch do handbook; atualize-a após confirmar o merge e a migração correspondente.

#### 3. Fonte e persistência das cargas

O ETL Python do repositório SQL espelha quatro coleções do MongoDB: `consumption_summary` e `device_status` de `db_delta_telemetry`, além de `user_preferences` e `alerts_history` de `db_delta_app`. Os arquivos individuais das tabelas `stage`, procedures `silver`/`gold` e views `dw` devem acompanhar o script consolidado `script-datamart.sql`; `bi_etl.py` realiza as cargas de Mongo para Stage, e `silver.sp_load()`/`gold.sp_load()` transformam os dados.

Isso descreve o código-fonte. Uma prova de gravação real exige logs de uma execução bem-sucedida e comparação de contagens/IDs entre as coleções de origem e as tabelas `stage`, seguida de confirmação de execução das procedures. Testes offline não acessam os bancos reais. O cron e os secrets também devem ser conferidos na branch padrão do repositório, não inferidos de um branch de feature.

#### 4. Como comprovar

1. Executar os scripts na ordem de `setup_db.py`, incluindo `script-datamart.sql` e `script-datamart-dataload.sql`.
2. Listar as views com `\dv dw.*` e conferir as nove views.
3. Consultar `SELECT * FROM dw.vw_ft_property_ranking LIMIT 10;` para ver o resultado analítico sobre as tabelas `gold`.
4. Abrir o diagrama da camada analítica e conferir as relações entre fatos e dimensões.

A sequência de carga é `bi_etl.py → silver.sp_load() → gold.sp_load()`. O ETL Python grava as coleções diretamente nas tabelas de `stage`; não há chamada `stage.sp_load()` nesse fluxo. O `script-datamart-dataload.sql` executa as duas procedures SQL.
