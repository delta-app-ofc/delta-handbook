### MOD-05 — Criar views analíticas para Data Mart, com modelagem dimensional Star Schema ou Snowflake

**Evidência direta:**

- [Script de criação do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart.sql)
- [Pasta das camadas do Data Mart (`stage`, `silver`, `gold`, `dw`)](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart)
- [Views analíticas do schema `dw`](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views)
- [Script de carga do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart-dataload.sql)
- [Documentação da camada de BI](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md)
- [Diagrama da camada analítica](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica-camada-analitica.png)

**Localização e como comprovar:**

O Data Mart está no mesmo PostgreSQL do banco relacional e é criado pelo `script-datamart.sql`, que organiza os dados em quatro schemas (arquitetura medalhão):

| Schema | Papel | Materialização |
|---|---|---|
| `stage` | Cópia bruta da telemetria extraída do MongoDB | Tabela |
| `silver` | Dado tratado, tipado e deduplicado, no grão original | Tabela |
| `gold` | Modelo dimensional (Star Schema) com chaves substitutas | Tabela |
| `dw` | Camada de consumo do BI | Views |

#### 1. Modelo dimensional (Star Schema)

O schema `gold` implementa um Star Schema: nenhuma dimensão referencia outra dimensão, e `gold.dm_date` é a dimensão conformada compartilhada pelas tabelas fato.

- **Dimensões:** `gold.dm_date` (1 linha por dia), `gold.dm_property` (1 linha por propriedade) e `gold.dm_person` (1 linha por pessoa).
- **Fatos:** `gold.ft_consumption_daily` (propriedade × dia), `gold.ft_water_bill_monthly` (pessoa × mês) e `gold.ft_investment_scenario` (cenário de investimento, fato sem dimensão de tempo).

O nome da organização fica denormalizado em `gold.dm_property` (`organization_name`). Essa decisão mantém o desenho como Star Schema, e não Snowflake, porque a organização não vira uma dimensão separada.

#### 2. Views analíticas (`dw`)

O schema `dw` contém **nove views**, todas lendo da camada `gold`, exceto `vw_audit_history_chain`, que lê o log de auditoria:

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

#### 3. Como comprovar

1. Executar os scripts na ordem de `setup_db.py`, incluindo `script-datamart.sql` e `script-datamart-dataload.sql`.
2. Listar as views com `\dv dw.*` e conferir as nove views.
3. Consultar `SELECT * FROM dw.vw_ft_property_ranking LIMIT 10;` para ver o resultado analítico sobre as tabelas `gold`.
4. Abrir o diagrama da camada analítica e conferir as relações entre fatos e dimensões.

A carga da camada de BI é feita por `bi_etl.py` (extração do MongoDB para `stage`) e pelas procedures `sp_load` de cada schema, executadas em sequência: `stage → silver → gold`.
