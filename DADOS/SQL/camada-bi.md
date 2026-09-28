# 📊 Camada de BI (Data Mart) - PostgreSQL (Projeto Delta)

Este documento descreve a camada de BI/Data Mart do banco PostgreSQL do Projeto Delta: arquitetura em
camadas, modelagem dimensional (star schema), CTEs, Window Functions, índices e a extração real de dados a
partir do MongoDB. Cobre o perfil comercial/industrial (unidades operadas por organização) e o resumo
analítico do perfil residencial já existente.

🔗 Repositório: https://github.com/delta-app-ofc/delta-database (pasta `datamart/`)

---

## 1. Objetivo e motivação

O requisito de disciplina pedia uma camada de BI com Views Analíticas em Modelagem Dimensional (Star
Schema), ETL via CTEs, Window Functions (Running Total, Ranking) e otimização com `EXPLAIN ANALYZE` +
Índices, além de uma estrutura avançada (CTE Recursiva ou Herança de Tabelas). Esta camada foi construída
para atender isso usando dado real sempre que possível: telemetria real do MongoDB local (gerada pelo
`delta-hardware-data-simulator`), dado cadastral real já existente no Postgres, e cenários de investimento
com valores pesquisados (não fictícios).

Onde o volume real de dados era pequeno demais para o `EXPLAIN ANALYZE` mostrar diferença de plano (a
telemetria real hoje cobre só 3 propriedades), isso é registrado explicitamente na seção 7 - a decisão foi
não fingir dado de produção, e sim rodar um teste de capacidade separado, isolado, nunca commitado.

---

## 2. Arquitetura em 4 camadas (medalhão)

| Camada | Papel | Materialização |
|---|---|---|
| `stage` | Cópia bruta, sem tratamento, do que vem de fora do Postgres (hoje só telemetria do MongoDB) | Tabela, com `loaded_at` |
| `silver` | Dado tratado: tipado, deduplicado, no grão original (ainda sem chave substituta) | Tabela |
| `gold` | Modelo dimensional final - star schema, chave substituta, pronto pra consumo analítico | Tabela |
| `dw` | Só views (`dw.vw_*`) - a camada de consumo do BI, CTEs + Window Functions, lendo só do `gold` | View |

Dado cadastral do Postgres que já chega limpo (propriedade, pessoa, fatura, cenário de investimento) **pula
a `stage`** e entra direto na `silver` - só o que vem de fora (hoje, telemetria do MongoDB) precisa do
espelho bruto. Isso é uma decisão de desenho, não uma inconsistência: `stage` existe para isolar o formato
de uma fonte externa, e dado que já nasce no Postgres não tem esse problema.

---

## 3. Modelo dimensional (star schema)

Star schema puro (sem snowflake - nenhuma dimensão referencia outra dimensão), com `gold.dm_date` como
dimensão conformada compartilhada por duas tabelas fato:

```
                    gold.dm_date (dimensão conformada)
                   /                              \
gold.dm_property--+--gold.ft_consumption_daily      gold.ft_water_bill_monthly--+--gold.dm_person
```

### Dimensões

| Tabela | Grão | PK | Chave natural |
|---|---|---|---|
| `gold.dm_date` | 1 linha por dia | `date_key` (INTEGER, YYYYMMDD) | - (dimensão raiz, gerada por `generate_series`) |
| `gold.dm_property` | 1 linha por propriedade | `property_key` (substituta) | `property_id` (único, aponta pra `tb_property.id`) |
| `gold.dm_person` | 1 linha por pessoa | `person_key` (substituta) | `user_id` (único, aponta pra `tb_user.id`) |

`gold.dm_property` traz o nome da organização já denormalizado na própria linha (`organization_name`) - é
isso que mantém o desenho como star, não snowflake: dado de organização não vira uma dimensão à parte.

### Fatos

| Tabela | Grão | PK | FK | Medidas |
|---|---|---|---|---|
| `gold.ft_consumption_daily` | 1 linha por propriedade x dia | `fact_key` | `property_key`, `date_key` | `total_liters`, `avg_flow_lmin`, `cost_value` |
| `gold.ft_water_bill_monthly` | 1 linha por pessoa x mês | `fact_key` | `person_key`, `date_key` | `total_value`, `m3_value` |
| `gold.ft_investment_scenario` | 1 linha por cenário (fato degenerado, sem FK de dimensão - não cruza com tempo/propriedade/pessoa) | `scenario_key` | - | `investment_value`, `reduction_pct`, `annual_savings_value`, `payback_months` |

`gold.ft_investment_scenario` é fato (tem medida numérica analisável - ranking por payback) mas não é
transacional: é referência estática, por isso não tem dimensão de tempo associada.

---

## 4. Fluxo de dados por conjunto

- **Consumo (telemetria industrial)** - o único fluxo que passa pelas 4 camadas de verdade, porque é o
  único dado que chega de fora do Postgres:

  `MongoDB db_delta_telemetry.consumption_summary` (real) → `bi_etl.py` → `stage.consumption_summary`
  (cópia 1:1, `mongo_id` único e idempotente) → `silver.sp_load_ft_consumption_reading` (`JOIN tb_device`
  resolve `device_id` → `property_id`) → `silver.ft_consumption_reading` (grão device x instante -
  `UNIQUE (device_id, read_at)`, porque uma propriedade pode ter mais de 1 dispositivo instalado) →
  `silver.sp_load_ft_consumption_daily` (CTE de agregação por dia, soma todos os devices de uma
  propriedade) → `silver.ft_consumption_daily` →
  `gold.sp_load_ft_consumption_daily` (chave substituta + `fn_get_current_region_rate` pro custo) →
  `gold.ft_consumption_daily` → `dw.vw_ft_consumption_daily` / `vw_ft_property_ranking` / `vw_ft_monthly_variation`
  / `vw_ft_consumption_distribution`.

- **Propriedade + organização + perfil operacional** - dado cadastral já limpo, pula a `stage`:
  `tb_property` + `tb_organization` + `tb_property_operational_profile` → `silver.sp_load_dm_property`
  (achata organização/perfil operacional numa linha só) → `silver.dm_property` →
  `gold.sp_load_dm_property` (chave substituta + remove órfão) → `gold.dm_property`.

- **Pessoa** - pula a `stage`: `tb_user` → `silver.sp_load_dm_person` (hoje um `SELECT` direto, sem
  transformação) → `silver.dm_person` → `gold.sp_load_dm_person` → `gold.dm_person`.

- **Fatura residencial** - pula a `stage`: `tb_last_water_bill` + `tb_user` →
  `silver.sp_load_ft_water_bill` → `silver.ft_water_bill` → `gold.sp_load_ft_water_bill_monthly` (chave
  substituta via `dm_person`/`dm_date`) → `gold.ft_water_bill_monthly` →
  `dw.vw_ft_residential_efficiency_ranking`.

- **Cenário de investimento (CAPEX)** - o mais curto, dado de referência estático, não passa por
  `stage`/`silver`: `tb_investment_scenario` → `gold.sp_load_ft_investment_scenario` (só chave substituta)
  → `gold.ft_investment_scenario` → `dw.vw_ft_capex_comparison`.

- **Auditoria (cadeia de reajuste de tarifa)** - fora do star schema, é a estrutura avançada da seção 6:
  `tb_region_rate` (operações reais) → `trg_log_region_rate`/`fn_log_region_rate` (auditoria já existente)
  → `tb_log_region_rate` → `dw.vw_audit_history_chain` (CTE recursiva direto sobre o log de auditoria).

---

## 5. CTEs e Window Functions

### CTEs (`WITH`)

Todas as 7 views de `dw` usam pelo menos uma CTE, além de 1 procedure de carga:

- `silver.sp_load_ft_consumption_daily` - agrega leituras por propriedade/dia antes do `INSERT`.
- `dw.vw_ft_consumption_daily` - CTE monta os `JOIN`s (propriedade, data) antes das window functions -
  necessário, porque o Postgres não permite `JOIN` depois de `OVER` no mesmo nível.
- `dw.vw_ft_property_ranking` - 2 CTEs em cadeia: agrega consumo/custo, depois calcula litros/m² - evita
  repetir a divisão em cada `OVER` do `SELECT` final.
- `dw.vw_ft_consumption_distribution` - agrega os totais diários, depois calcula os percentis
  (`PERCENTILE_CONT`) numa CTE separada que entra via `CROSS JOIN`.
- `dw.vw_ft_monthly_variation` - agrega por mês antes de aplicar `LAG()`.
- `dw.vw_ft_capex_comparison` - CTE simples, por padronização com as outras views.
- `dw.vw_ft_residential_efficiency_ranking` - monta os `JOIN`s antes das window functions.
- `dw.vw_audit_history_chain` - `WITH RECURSIVE` (seção 6).

### Window Functions

| Tipo | Onde | Uso |
|---|---|---|
| Running total | `SUM() OVER (PARTITION BY property_id ORDER BY full_date ROWS UNBOUNDED PRECEDING)` em `vw_ft_consumption_daily` | Soma acumulada de consumo por propriedade ao longo do tempo |
| Média móvel | `AVG() OVER (... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`, mesma view | Média móvel de 7 dias, suaviza variação diária |
| Ranking | `RANK()`/`DENSE_RANK()` em `vw_ft_property_ranking`, `vw_ft_capex_comparison`, `vw_ft_residential_efficiency_ranking` | Eficiência (L/m²), custo, payback, consumo residencial (`PARTITION BY` mês) |
| Distribuição | `NTILE(4)`/`NTILE(5)` + `PERCENT_RANK()` em `vw_ft_property_ranking`/`vw_ft_consumption_distribution` | Quartil/quintil de consumo, posição relativa 0-1 |
| Comparação com período anterior | `LAG()` em `vw_ft_monthly_variation` | Variação percentual mês a mês |

Todas testadas com dado real (seção 7).

---

## 6. Estrutura avançada: CTE Recursiva

A rubrica pedia CTE Recursiva **ou** Herança de Tabelas. As duas foram avaliadas:

- **Herança de tabelas** (`INHERITS`) foi tentada em `tb_property_operational_profile` e descartada depois
  de testar contra um Postgres descartável: FK de outras tabelas apontando pra `tb_property(id)` não
  enxerga linhas da tabela filha quando ela usa `INHERITS` - o Postgres trata tabela pai/filha como relações
  fisicamente separadas pra fins de integridade referencial. Foi substituída por uma extensão 1:1
  (`property_id` como PK e FK ao mesmo tempo), que resolve "propriedade com dado extra opcional" sem
  quebrar FK.
- **CTE Recursiva** foi a escolha final, sobre um cenário que já existia de verdade: a cadeia de auditoria
  de reajuste de tarifa (`tb_log_region_rate.previous_log_id`).

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

Testado com dado real: o dataload faz 1 `INSERT` + 2 `UPDATE` reais na mesma tarifa, cada um disparando o
trigger de auditoria de verdade. `dw.vw_audit_history_chain WHERE region_rate_id = 5` devolve os 3 níveis
esperados (`level` 1, 2 e 3), confirmando que a cadeia sobe certo por `previous_log_id`.

O cenário de auditoria (lista encadeada) é o caso de uso correto pra CTE recursiva; hierarquia de tipos de
entidade (o caso de uso correto pra `INHERITS`) não existe no domínio do projeto - por isso a CTE recursiva
sozinha satisfaz o requisito sem forçar herança onde ela não se encaixa.

---

## 7. Índices e `EXPLAIN ANALYZE`

### Metodologia

No volume real de produção hoje (14 a 400 linhas nas tabelas envolvidas), nenhum índice muda o plano de
nenhuma consulta que existe no projeto - o Postgres corretamente prefere Seq Scan porque a tabela cabe em
poucas páginas. Isso foi confirmado com `EXPLAIN (ANALYZE, BUFFERS)` real contra o dado real, não é uma
suposição.

Como o dado real ainda é pequeno (telemetria cobre só 3 propriedades hoje), o `EXPLAIN ANALYZE` sozinho
contra o dado real não prova nem desmente a necessidade de um índice - ele só mostra que hoje não é
necessário. Pra responder "esse índice vai ajudar quando o volume crescer de verdade?", foi feito um
**teste de capacidade em duas rodadas**, sempre no mesmo formato:

1. Container Postgres descartável, nunca commitado, criado só para o teste.
2. Carrega o schema real (`script-schema.sql` até `script-indexes.sql`, ordem oficial do `setup_db.py`).
3. Insere volume sintético claramente identificado como teste (nomes tipo `ORG_TESTE_UNICA`,
   `PROPRIEDADE SINTETICA N`), em quantidade compatível com anos de operação contínua - nunca no
   `script-dataload.sql` real, nunca commitado.
4. Roda `ANALYZE` pra atualizar as estatísticas do planner.
5. Roda a consulta real (a mesma que a view/procedure executa) com `EXPLAIN (ANALYZE, BUFFERS)`, sem
   índice.
6. Cria o índice candidato, roda `ANALYZE` de novo, repete o `EXPLAIN (ANALYZE, BUFFERS)`.
7. Compara os dois planos reais - nunca usando `SET enable_seqscan=off` pra forçar um resultado.
8. Container descartado ao final.

**Rodada 1** testou os 2 índices que já existiam (ver tabela abaixo). **Rodada 2**, depois de a autora
pedir um teste mais rigoroso, testou sistematicamente **as 7 views de `dw`, uma por uma**, em volume grande
(até 730.000 linhas em `gold.ft_consumption_daily`), pra confirmar se sobrava algum índice faltando -
processo descrito na íntegra a seguir.

### O que foi testado view por view (rodada 2)

| View | Padrão de acesso | Resultado no volume grande |
|---|---|---|
| `vw_ft_consumption_daily` | `JOIN` propriedade+data, window functions | Já usa Index Scan nos índices de `UNIQUE` existentes (não precisa de índice novo) |
| `vw_ft_property_ranking` | `SUM` de TODAS as linhas por propriedade | `Seq Scan` correto - agregação total não tem filtro pra um índice explorar |
| `vw_ft_monthly_variation` | `SUM` de TODAS as linhas por mês | Mesmo caso - agregação total |
| `vw_ft_consumption_distribution` | Percentis (`PERCENTILE_CONT`) sobre 100% dos dados | Por definição lê tudo - índice não ajudaria |
| `vw_ft_capex_comparison` | Tabela de referência, não cresce em volume | Sem necessidade de índice |
| `vw_ft_residential_efficiency_ranking` | Ranking global por mês | `Seq Scan` correto - lê tudo por definição |
| `vw_audit_history_chain` | CTE recursiva sobre `previous_log_id` | **Achado real, ver abaixo** |

Conclusão: das 7 views, 6 fazem agregação/ranking sobre 100% dos dados de entrada - nelas, `Seq Scan`/
`Parallel Seq Scan` já é o plano correto, não uma lacuna de índice. A única com um padrão de acesso que um
índice poderia mesmo mudar era a CTE recursiva.

### Três índices, com evidência real de ganho em volume de produção continuado

```sql
CREATE INDEX idx_stage_consumption_summary_device_window
    ON stage.consumption_summary (device_id, window_started_at DESC);

CREATE INDEX idx_gold_dm_property_organization
    ON gold.dm_property (organization_name);

CREATE INDEX idx_log_region_rate_previous_log_id
    ON tb_log_region_rate (previous_log_id);
```

| Índice | Consulta | Sem índice | Com índice | Ganho |
|---|---|---|---|---|
| `idx_stage_consumption_summary_device_window` | Histórico de 1 device (`WHERE device_id = X ORDER BY window_started_at DESC LIMIT 20`) | Parallel Seq Scan, 4690 buffers, 52,000 ms | Index Scan, 23 buffers, 0,144 ms | ~360x |
| `idx_gold_dm_property_organization` | Filtro por organização específica (`WHERE organization_name = X`) | Parallel Seq Scan, 4684 buffers, 19,588 ms | Index Scan, 4 buffers, 0,070 ms | ~280x |
| `idx_log_region_rate_previous_log_id` | CTE recursiva (`dw.vw_audit_history_chain`), tabela de log com 500.342 linhas reais+teste | Merge Join com sort em disco a cada nível da recursão, 69.417 ms | Index Scan, 1.134 ms | ~61x |

O terceiro índice foi achado na rodada 2: a chave estrangeira auto-referenciada `previous_log_id` (que a
CTE recursiva percorre a cada nível) não tinha índice de apoio - problema clássico de performance em
Postgres, onde uma FK nunca ganha índice automático no lado que referencia (só o lado referenciado, via
`PRIMARY KEY`). Em volume pequeno isso não aparece (o Postgres consegue fazer hash da tabela inteira de
uma vez), mas em volume real de anos de histórico de reajuste de tarifa, o plano degenera pra um sort em
disco repetido a cada nível da cadeia - e o índice resolve isso de verdade.

Os três índices ficam no schema mesmo sem uso na consulta cotidiana de hoje (volume real ainda pequeno) -
o ganho é real, medido, e vai aparecer conforme o volume real de telemetria e de histórico de auditoria
cresce.

---

## 8. Extração real de dados (MongoDB → Postgres)

`bi_etl.py` (raiz do `delta-database`) extrai `db_delta_telemetry.consumption_summary` do MongoDB real e
carrega a cadeia `stage → silver → gold`:

1. Lê o watermark atual (`MAX(window_started_at)` em `stage.consumption_summary`); se vazio, busca todo o
   histórico.
2. Busca no MongoDB os documentos com `window_started_at >= watermark` (inclusive, não estrito) - garante
   que nenhum documento com o mesmo instante do watermark fique de fora, mesmo que uma execução anterior
   tenha sido interrompida no meio.
3. Processa o cursor em lotes de 1000 documentos (não carrega tudo em memória de uma vez), inserindo em
   `stage.consumption_summary` com `ON CONFLICT (mongo_id) DO NOTHING` a cada lote - o `>=` do passo 2
   pode reencontrar um documento já carregado, mas essa trava garante que ele nunca duplica.
4. Executa `CALL silver.sp_load(); CALL gold.sp_load();`.

Agendado via GitHub Actions (`.github/workflows/bi-etl.yml`), diariamente, mesmo padrão de cron já usado
pelo backup do banco.

**Estado real hoje**: telemetria do MongoDB Atlas (produção) ainda não foi testada por bloqueio de rede;
testado de ponta a ponta contra o MongoDB local (`docker-compose.dev.yml` do
`delta-artificial-intelligence`, populado pelo `delta-hardware-data-simulator`) - 80 documentos reais
extraídos, 44 resolvidos pra propriedade (via `tb_device.device_id`), números conferidos em toda a cadeia
silver/gold/dw. O parque de dispositivos (`tb_device`) tem 155 linhas, mas só 3 propriedades (1, 151, 152)
têm telemetria real vinculada hoje - as demais têm `device_id` no formato certo, mas sem documento
correspondente no Mongo ainda.

---

## 9. Pendências conhecidas

- **Simulador não usa o `device_id` real do Postgres**: o `delta-hardware-data-simulator` ainda se
  autonumera, em vez de puxar os `device_id` cadastrados em `tb_device`. Fora do escopo do
  `delta-database` corrigir (é código de outro repositório).
- **Agentes de IA não leem o perfil comercial/industrial**: o Agente de Previsão
  (`delta-artificial-intelligence`) depende inteiramente de `tb_user_property` (posse residencial direta) -
  um usuário vinculado só por `tb_user_organization` nunca passa em `fn_user_can_estimate`, mesmo com
  telemetria real na camada `gold`. `TASK.md` completo criado naquele repositório para fechar essa lacuna.
- **`tb_user.is_manager` x `tb_user_organization`**: duas fontes de verdade pro mesmo fato (bater 1:1 nos
  dados de teste atuais). Mantidas as duas por decisão de escopo; unificação registrada como pendência
  futura.
- **Redis/Neo4j**: documentados como planejados em toda a arquitetura do projeto (ver
  `DADOS/infra-bancos.md`, seção 4.2), sem código em nenhum repositório - nada a fazer aqui. Se o ranking
  Web em Redis (`ZSET`) for implementado no futuro, ele seria um cache de leitura alimentado por
  `dw.vw_ft_property_ranking`, não um substituto dela.
- **Coleções MongoDB do perfil industrial** (alerta, escalonamento, relatório agendado) - fora do escopo
  deste repositório (só Postgres); pendência de modelagem pra quem cuidar do MongoDB do perfil industrial.
