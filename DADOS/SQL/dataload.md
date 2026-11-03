# Dataload — Carga Inicial de Dados de Teste

Documentação do script `script-dataload.sql`, responsável por popular o banco com dados volumétricos e plausíveis para testes. A carga soma **2.331 registros em 22 tabelas**, acima do mínimo de 500 registros exigido (MOD-03).

## Registros por tabela

### Referências e perfil residencial

| # | Tabela | Registros | Observações |
|---|---|---:|---|
| 1 | `tb_region` | 9 | Grupos tarifários da Sabesp: GRANDE_SP, LINS, PRESIDENTE_PRUDENTE, ADAMANTINA_PIRAPOZINHO, BRAGANCA_PAULISTA, LITORAL, VALE_DO_RIBEIRA, INTERIOR e VALE_DO_PARAIBA |
| 2 | `tb_municipality` | 371 | Municípios do Anexo I do Contrato 01/2024 (URAE-1), com código IBGE e região tarifária, ver `mapeamento-cidade-regiao.md` |
| 3 | `tb_day_of_week` | 7 | Valores fixos: SEGUNDA a DOMINGO |
| 4 | `tb_habit` | 6 | Valores fixos com descrição e categoria (`HIGIENE E CUIDADOS`, `LIMPEZA`, `JARDINAGEM`) |
| 5 | `tb_property_classification` | 8 | Valores fixos, grupos RESIDENCIAL/COMERCIAL |
| 6 | `tb_address` | 156 | CEP plausível por região, inclui os endereços das 6 unidades comerciais/industriais |
| 7 | `tb_user` | 201 | 200 usuários de teste e 1 administrador fixo |
| 8 | `tb_property` | 155 | 150 residenciais e 5 unidades comerciais/industriais (`organization_id` preenchido) |
| 9 | `tb_user_property` | 148 | Associação usuário ↔ imóvel residencial. Os usuários 2 e 15 (gestores de organização) não têm vínculo residencial |
| 10 | `tb_device` | 155 | 150 residenciais e 5 industriais, 3 delas com telemetria real vinculada (ver `camada-bi.md`, seção 8) |
| 11 | `tb_region_rate` | 72 | 9 regiões × 8 categorias de imóvel, vigência a partir de 2026-01-01, fonte ARSESP |
| 12 | `tb_user_habit` | 400 | Hábitos associados a usuários (frequência 1–7), 2 hábitos por usuário em média. `start_time`, `end_time` e `estimated_liters` são preenchidos por `UPDATE` após o `INSERT` |
| 13 | `tb_user_habit_day` | 400 | 1 dia da semana por hábito de usuário |
| 14 | `tb_last_water_bill` | 200 | 1 conta por usuário residencial (ids 1–200), meses de JAN/2025 a JUN/2025. O administrador (id 201) não possui imóvel nem conta |

### Perfil comercial/industrial

| # | Tabela | Registros | Observações |
|---|---|---:|---|
| 15 | `tb_organization` | 3 | SWIFT (varejo), METALVALE (indústria) e JARDIM DAS FLORES (condomínio), CNPJ em formato válido |
| 16 | `tb_user_organization` | 2 | Usuário 2 → SWIFT, usuário 15 → METALVALE |
| 17 | `tb_property_operational_profile` | 2 | Unidades com cadastro industrial completo (154 e 155) |
| 18 | `tb_property_shift` | 5 | 2 turnos (unidade 154) e 3 turnos (unidade 155) |
| 19 | `tb_water_usage_type` | 4 | LIMPEZA, CONSUMO_HUMANO, PROCESSO_PRODUTIVO e IRRIGACAO |
| 20 | `tb_property_water_usage` | 8 | Vínculo unidade × tipo de uso da água |
| 21 | `tb_property_operation_day` | 16 | Dias de operação das unidades 151, 154 e 155 |
| 22 | `tb_investment_scenario` | 3 | Valores pesquisados, ver `pesquisa-cenarios-investimento.md` |
| | **Total** | **2.331** | |

A soma por conjunto é: 2.288 registros de referência e perfil residencial (linhas 1 a 14) e 43 registros do perfil comercial/industrial (linhas 15 a 22).

## Tabelas populadas em execução

Quatro tabelas técnicas não recebem carga inicial, porque seus registros nascem do uso do sistema:

| Tabela | Quem grava | Quando |
|---|---|---|
| `tb_data_catalog` | `script-catalogo-dados.sql` e `script-catalogo-datamart.sql` | Na criação do catálogo de metadados (261 colunas catalogadas, MOD-12) |
| `tb_user_access_log` | `sp_register_user_access` | A cada acesso de usuário (MOD-14) |
| `tb_backup_restore_log` | `backup_db.py restore-test` | A cada teste de restauração (MOD-13) |
| `tb_log_rpa` | `delta-rpa` | A cada execução da migração (MOD-04) |

Quando `script-audit.sql` é executado antes do dataload, cada `INSERT` dispara o trigger correspondente e popula os logs de auditoria. Executar apenas `script-schema.sql` e `script-dataload.sql` não instala esses triggers; a comprovação dos logs pertence ao MOD-10.

## Como validar a contagem

Ao final da execução do `script-dataload.sql`, a consulta de verificação exibe a contagem por tabela. Os valores esperados são os da coluna "Registros" acima:

```sql
SELECT 'tb_region' AS tabela, COUNT(*) AS registros FROM tb_region
UNION ALL SELECT 'tb_municipality',   COUNT(*) FROM tb_municipality
UNION ALL SELECT 'tb_day_of_week',    COUNT(*) FROM tb_day_of_week
UNION ALL SELECT 'tb_habit',          COUNT(*) FROM tb_habit
UNION ALL SELECT 'tb_water_usage_type', COUNT(*) FROM tb_water_usage_type
UNION ALL SELECT 'tb_address',        COUNT(*) FROM tb_address
UNION ALL SELECT 'tb_user',           COUNT(*) FROM tb_user
UNION ALL SELECT 'tb_property_classification', COUNT(*) FROM tb_property_classification
UNION ALL SELECT 'tb_organization',   COUNT(*) FROM tb_organization
UNION ALL SELECT 'tb_property',       COUNT(*) FROM tb_property
UNION ALL SELECT 'tb_property_operational_profile', COUNT(*) FROM tb_property_operational_profile
UNION ALL SELECT 'tb_property_shift', COUNT(*) FROM tb_property_shift
UNION ALL SELECT 'tb_property_water_usage', COUNT(*) FROM tb_property_water_usage
UNION ALL SELECT 'tb_property_operation_day', COUNT(*) FROM tb_property_operation_day
UNION ALL SELECT 'tb_investment_scenario', COUNT(*) FROM tb_investment_scenario
UNION ALL SELECT 'tb_user_organization', COUNT(*) FROM tb_user_organization
UNION ALL SELECT 'tb_user_property',  COUNT(*) FROM tb_user_property
UNION ALL SELECT 'tb_device',         COUNT(*) FROM tb_device
UNION ALL SELECT 'tb_region_rate',    COUNT(*) FROM tb_region_rate
UNION ALL SELECT 'tb_user_habit',     COUNT(*) FROM tb_user_habit
UNION ALL SELECT 'tb_user_habit_day', COUNT(*) FROM tb_user_habit_day
UNION ALL SELECT 'tb_last_water_bill', COUNT(*) FROM tb_last_water_bill
ORDER BY tabela;
```

Para o total, envolva a consulta em `SELECT SUM(registros) FROM (...) AS contagem;` e confira `2331`.

A carga da camada de BI (`stage`, `silver` e `gold`) não faz parte deste script. Ela é feita por `bi_etl.py` (extração real do MongoDB) e por `script-datamart-dataload.sql`, documentados em `camada-bi.md`.

## Origem dos dados

- **Tarifas e municípios:** fontes públicas (ARSESP e Anexo I do Contrato 01/2024 da URAE-1). O cabeçalho do script registra a fonte de cada bloco.
- **Usuários, endereços e hábitos:** valores de teste verossímeis, com CEP plausível por região e frequências entre 1 e 7 dias por semana.
- **Cenários de investimento:** valores pesquisados, documentados em `pesquisa-cenarios-investimento.md`.
