# Dataload — Carga Inicial de Dados de Teste

Documentação resumida do script `script-dataload.sql`, responsável por popular o banco com dados volumétricos e plausíveis para testes.

## Registros por tabela

### Perfil residencial (já existia antes da extensão comercial/industrial)

| # | Tabela | Registros | Observações |
|---|---|---:|---|
| 1 | `tb_region` | 5 | Valores fixos: GRANDE_SP, LINS, PRESIDENTE_PRUDENTE, ADAMANTINA_PIRAPOZINHO, BRAGANCA_PAULISTA |
| 2 | `tb_day_of_week` | 7 | Valores fixos: SEGUNDA a DOMINGO |
| 3 | `tb_habit` | 6 | Valores fixos com descrição |
| 4 | `tb_property_classification` | 8 | Valores fixos, grupos RESIDENCIAL/COMERCIAL |
| 5 | `tb_address` | 156 | CEP plausível por região (zonas de São Paulo) · inclui os endereços das 6 unidades comerciais/industriais novas |
| 6 | `tb_user` | 201 | 200 usuários aleatórios + 1 admin fixo |
| 7 | `tb_property` | 155 | 150 residenciais + 5 unidades comerciais/industriais (organization_id preenchido) |
| 8 | `tb_user_property` | 148 | Associação usuário ↔ imóvel residencial - **não** 150: usuários 2 e 15 (gestores de organização) tiveram o vínculo residencial removido, ver `camada-bi.md` seção 9 |
| 9 | `tb_device` | 155 | 150 residenciais + 5 industriais (3 com telemetria real vinculada - ver `camada-bi.md` seção 8) |
| 10 | `tb_region_rate` | 40 | 5 regiões × 8 categorias de imóvel, vigência única a partir de 2026-01-01 |
| 11 | `tb_user_habit` | 400 | Hábitos associados a usuários (frequência 1–7), 2 hábitos por usuário em média |
| 12 | `tb_user_habit_day` | 400 | 1 dia da semana por hábito de usuário |
| 13 | `tb_last_water_bill` | 200 | 1 conta por usuário "normal" (ids 1–200), meses de JAN/2025 a JUN/2025. Admin (id 201) não possui conta, pois não tem imóvel associado |

### Perfil comercial/industrial (extensão desta revisão)

| # | Tabela | Registros | Observações |
|---|---|---:|---|
| 14 | `tb_organization` | 3 | SWIFT (varejo), METALVALE (indústria), JARDIM DAS FLORES (condomínio) - CNPJ real (formato), sem unidade vinculada pro condomínio |
| 15 | `tb_user_organization` | 2 | Usuário 2 → SWIFT, usuário 15 → METALVALE (gestores, sem hierarquia) |
| 16 | `tb_property_operational_profile` | 2 | Só as 2 unidades com cadastro industrial completo (154, 155) |
| 17 | `tb_property_shift` | 5 | 2 turnos (unidade 154) + 3 turnos (unidade 155) |
| 18 | `tb_water_usage_type` | 4 | LIMPEZA, CONSUMO_HUMANO, PROCESSO_PRODUTIVO, IRRIGACAO |
| 19 | `tb_property_water_usage` | 8 | Vínculo unidade × tipo de uso da água |
| 20 | `tb_property_operation_day` | 16 | Dias de operação das unidades 151, 154, 155 |
| 21 | `tb_investment_scenario` | 3 | Valores pesquisados, ver `pesquisa-cenarios-investimento.md` |
| | **Total** | **1.914** | |

## Como validar a contagem

Ao final da execução do `script-dataload.sql`, a própria query de verificação já exibe esses números
(lista completa, residencial + comercial/industrial):

```sql
SELECT 'tb_region' AS tabela, COUNT(*) AS registros FROM tb_region
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

A carga da camada de BI (`stage`/`silver`/`gold`) não faz parte deste script - é feita por `bi_etl.py`
(extração real do MongoDB) e `script-datamart-dataload.sql`, documentado em `camada-bi.md`.