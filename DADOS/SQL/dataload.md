# Dataload — Carga Inicial de Dados de Teste

Documentação resumida do script `script-dataload.sql`, responsável por popular o banco com dados volumétricos e plausíveis para testes.

## Registros por tabela

| # | Tabela | Registros | Observações |
|---|---|---:|---|
| 1 | `tb_region` | 5 | Valores fixos: LESTE, OESTE, SUL, NORTE, CENTRO |
| 2 | `tb_day_of_week` | 7 | Valores fixos: SEGUNDA a DOMINGO |
| 3 | `tb_habit` | 6 | Valores fixos com descrição |
| 4 | `tb_address` | 150 | CEP plausível por região (zonas de São Paulo) · 30 endereços por região |
| 5 | `tb_user` | 201 | 200 usuários aleatórios + 1 admin fixo |
| 6 | `tb_property` | 150 | Alterna CASA/PRÉDIO · RESIDENCIAL/COMERCIAL conforme padrão do script |
| 7 | `tb_user_property` | 150 | 1 imóvel por usuário (associação direta usuário ↔ propriedade) |
| 8 | `tb_device` | 150 | 1 dispositivo por imóvel |
| 9 | `tb_region_rate` | 30 | 5 regiões × 2 vigências × 3 faixas de consumo |
| 10 | `tb_user_habit` | 400 | Hábitos associados a usuários (frequência 1–7), 2 hábitos por usuário em média |
| 11 | `tb_user_habit_day` | 400 | 1 dia da semana por hábito de usuário |
| 12 | `tb_last_water_bill` | 200 | 1 conta por usuário "normal" (ids 1–200), meses de JAN/2025 a JUN/2025. Admin (id 201) não possui conta, pois não tem imóvel associado |
| | **Total** | **1.849** | |

## Como validar a contagem

Ao final da execução do `script-dataload.sql`, a própria query de verificação já exibe esses números:

```sql
SELECT 'tb_region' AS tabela, COUNT(*) AS registros FROM tb_region
UNION ALL SELECT 'tb_day_of_week',    COUNT(*) FROM tb_day_of_week
UNION ALL SELECT 'tb_habit',          COUNT(*) FROM tb_habit
UNION ALL SELECT 'tb_address',        COUNT(*) FROM tb_address
UNION ALL SELECT 'tb_user',           COUNT(*) FROM tb_user
UNION ALL SELECT 'tb_property',       COUNT(*) FROM tb_property
UNION ALL SELECT 'tb_user_property',  COUNT(*) FROM tb_user_property
UNION ALL SELECT 'tb_device',         COUNT(*) FROM tb_device
UNION ALL SELECT 'tb_region_rate',    COUNT(*) FROM tb_region_rate
UNION ALL SELECT 'tb_user_habit',     COUNT(*) FROM tb_user_habit
UNION ALL SELECT 'tb_user_habit_day', COUNT(*) FROM tb_user_habit_day
UNION ALL SELECT 'tb_last_water_bill', COUNT(*) FROM tb_last_water_bill
ORDER BY tabela;
```