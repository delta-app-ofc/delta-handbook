### MOD-08 — Criar no mínimo duas Functions para regras críticas de negócio

**Evidência direta:**

- [Pasta das Functions](https://github.com/delta-app-ofc/delta-sql-database/tree/main/functions)
- [Script que agrega as Functions e Procedures](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-optimization.sql)
- [Function de elegibilidade para estimativas](https://github.com/delta-app-ofc/delta-sql-database/blob/main/functions/fn_user_can_estimate.sql)
- [Function de tarifa vigente](https://github.com/delta-app-ofc/delta-sql-database/blob/main/functions/fn_get_current_region_rate.sql)
- [Documentação das Functions e Procedures](../otimizacao.md)
- [Lista de Functions do schema public, parte 1](../anexos/evidencias-requisitos/mod-08-functions-01.png)
- [Lista de Functions do schema public, parte 2](../anexos/evidencias-requisitos/mod-08-functions-02.png)

**Localização e como comprovar:**

O banco possui **24 arquivos de Functions** em `functions/`, reunidas em `script-optimization.sql`. Elas concentram regras de negócio no PostgreSQL, para que API, IA e BI apliquem a mesma regra sem reimplementá-la.

#### 1. Functions críticas

| Function | Regra de negócio |
|---|---|
| `fn_user_is_active` | Verifica se o usuário existe e está ativo antes de qualquer operação |
| `fn_get_current_region_rate` | Devolve a tarifa por m³ vigente para uma região, uma classificação e uma data, respeitando `initial_validity` e `final_validity` |
| `fn_user_can_estimate` | Valida usuário ativo, imóvel vinculado, dispositivo ativo e tarifa válida antes de gerar uma estimativa |
| `fn_calculate_water_cost` | Calcula o custo estimado de um consumo em m³ usando a tarifa da região do imóvel |
| `fn_get_dau` | Conta os usuários únicos com acesso registrado em um dia (MOD-14) |

#### 2. Functions de apoio

- **Cadastro do imóvel:** `fn_get_property_region`, `fn_get_property_classification` e `fn_get_property_classification_group`.
- **Perfil organizacional:** `fn_user_access_kind`, `fn_user_organization_properties`, `fn_user_authorized_property_ids`, `fn_organization_can_estimate`, `fn_organization_consumption_history`, `fn_organization_last_billed_period`, `fn_organization_effective_rate` e `fn_organization_forecast_context`.
- **Contexto de previsão:** `fn_get_user_property_context` e `fn_user_forecast_context`.
- **Hábitos:** `fn_user_habits`, `fn_user_habits_by_day`, `fn_user_location`, `fn_create_user_habit` e as Functions de trigger `fn_check_user_habit_conflict` e `fn_check_user_habit_day_conflict`.

#### 3. Por que Functions

As Functions retornam valores e podem ser usadas dentro de consultas. A `fn_get_current_region_rate` expõe a consulta de tarifa para os consumidores do banco. A carga `gold.sp_load_ft_consumption_daily` calcula `cost_value` por uma consulta `LATERAL` em `tb_region_rate`, sem chamar essa Function. A `fn_user_can_estimate` valida a elegibilidade da previsão usando o primeiro vínculo do usuário (`ORDER BY tb_user_property.id`) e a data de referência. A assinatura de um argumento mantém `CURRENT_DATE`; `fn_user_forecast_context` usa a assinatura de dois argumentos para informar `p_today`. As validações ficam no banco, o que evita regras duplicadas em cada aplicação.

#### 4. Como comprovar

1. Executar `script-schema.sql`, `script-optimization.sql` e `script-dataload.sql`.
2. Executar `SELECT fn_user_can_estimate(1);` e conferir `TRUE` para um usuário com imóvel, dispositivo ativo e tarifa.
3. Executar `SELECT fn_get_current_region_rate(1, 1, CURRENT_DATE);` e conferir o valor do m³.
4. Executar `SELECT * FROM fn_calculate_water_cost(1, 10);` e conferir tarifa e custo estimado.
