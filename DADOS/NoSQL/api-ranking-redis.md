# API de Ranking Redis — Projeto Delta

Este documento descreve a modelagem de dados e o funcionamento da API de ranking de eficiência hídrica do Projeto Delta, implementada no repositório `delta-redis-database`.

Complementa o [`modelagem-mongodb.md`](./modelagem-mongodb.md), que descreve o papel do MongoDB, e o [`engenharia-dados.md`](../engenharia-dados.md), que trata do pipeline ETL.

---

## 1. Papel do Redis na Arquitetura

O Projeto Delta usa quatro motores de persistência, cada um com responsabilidade fechada:

| Motor | Responsabilidade |
|---|---|
| **PostgreSQL** | Dados cadastrais, relacionais e transacionais; camadas gold e data mart para BI |
| **MongoDB** | Telemetria IoT (consumo em janelas de 5 min), dados de aplicação e chat |
| **Redis** | Ranking de eficiência hídrica em tempo real (Sorted Sets); cache de resultados da IA |
| **Neo4j** | Grafo de relações entre entidades |

O Redis entra onde a velocidade de leitura e a ordenação em tempo real são essenciais. O ranking de eficiência precisa ser consultado com frequência pelo painel web industrial, e qualquer registro novo de consumo deve ser refletido imediatamente — sem precisar recalcular uma view SQL nem rodar um ETL.

---

## 2. Por que L/m²·dia é o critério justo

Comparar consumo bruto entre unidades de tamanhos diferentes é injusto. Uma loja de 3.200 m² sempre vai consumir mais litros do que uma de 650 m², mesmo sendo mais eficiente.

O critério `perm2` corrige isso:

```
consumo_medio_diario = soma(litros dos dias fechados com leitura) / dias_com_leitura
perm2                = consumo_medio_diario / built_area_m2        (L/m²·dia)
```

- **Menor `perm2` = 1º lugar.**
- Usa **média por dia** (não o total do mês) para tratar fevereiro e março com justiça — meses têm tamanhos diferentes.
- O **dia corrente não entra no cálculo** até fechar: um dia parcial faria a unidade parecer mais eficiente do que é.
- O consumo total (`consumo`) fica como critério secundário, só informativo.

### Desempate

Quando duas unidades têm o mesmo score, o Redis desempata pelo `member` em ordem lexicográfica crescente. Os `propertyId` são gravados com zeros à esquerda (ex.: `000042`) para garantir que a ordem lexicográfica coincida com a ordem numérica.

---

## 3. Modelo de chaves no Redis

Os IDs usados são os mesmos do PostgreSQL: `propertyId` = `tb_property.id`, `organizationId` = `tb_organization.id`.

| Chave | Tipo Redis | Conteúdo |
|---|---|---|
| `property:{propertyId}` | Hash | `name`, `organizationId`, `areaM2` (vazio se NULL) |
| `org:{organizationId}:properties` | Set | IDs de todas as unidades da organização |
| `consumption:{propertyId}:{YYYY-MM}` | Hash | campo = dia (`01`..`31`), valor = litros do dia |
| `ranking:org:{organizationId}:{YYYY-MM}:perm2` | Sorted Set | member = propertyId com zeros à esquerda, score = L/m²·dia |
| `ranking:org:{organizationId}:{YYYY-MM}:consumo` | Sorted Set | member = propertyId com zeros à esquerda, score = média diária de litros |

### Regras de escrita

- O dia é um campo do Hash de consumo → reenviar o mesmo dia **sobrescreve** (idempotente).
- A cada escrita, médias e totais são recalculados a partir do Hash (no máximo 31 campos) e os dois Sorted Sets são atualizados em `pipeline(transaction=True)`.
- Se a área da unidade mudar, os scores do mês corrente são recalculados automaticamente.
- **Retenção:** 13 meses — TTL aplicado ao criar ou atualizar chaves de consumo e ranking.

---

## 4. Como o TTL de retenção é calculado

Toda chave de consumo e de ranking recebe um **TTL** (*Time To Live*): um contador que o próprio Redis decrementa automaticamente. Quando chega a zero, a chave some da memória sem precisar de nenhum job de limpeza.

A função `period_ttl_seconds(period)` calcula esse valor em segundos:

```
período:         "2026-10"   (outubro de 2026)
expiração:       mês + 13    = outubro + 13 = novembro de 2027
hoje:            23/10/2026
dias restantes:  374 dias
TTL:             374 × 86400 = 32.313.600 segundos
```

O cálculo garante que dados de outubro de 2026 expirem no dia 1º de novembro de 2027 — exatamente 13 meses depois. Se, por algum motivo, o período calculado já tiver passado, aplica-se um mínimo de 86.400 segundos (1 dia) para evitar TTL zero ou negativo.

Esse TTL é recalculado e reaplicado em toda atualização de consumo ou ranking, não só na criação — assim a chave não expira enquanto ainda está sendo usada.

---

## 5. Como o ranking é recalculado (`recalculate_ranking`)

Essa função é chamada sempre que um consumo é gravado ou a área de uma unidade é atualizada. Ela relê todos os dados do Redis e recalcula os scores do zero. O processo tem seis etapas:

### Etapa 1 — lê a unidade
```
property:42  →  { name: "Loja Centro", organizationId: "1", areaM2: "650.0" }
```
Se a unidade não existir mais (foi removida), a função retorna sem fazer nada.

### Etapa 2 — lê os dias de consumo do mês
```
consumption:42:2026-10  →  { "01": "130.5", "02": "125.0", "15": "98.3", ... }
```
Um Hash com até 31 campos — um por dia do mês.

### Etapa 3 — descobre quantos dias já fecharam
"Dias fechados" são os dias com `date < hoje`. Se hoje é 23/10/2026, os dias fechados são 1 a 22 (22 dias). O dia 23 ainda está em andamento: gravar o consumo parcial de hoje faria a unidade parecer mais eficiente do que ela é.

| Situação | Dias fechados |
|---|---|
| Mês já passou inteiro | todos os dias do mês |
| Mês corrente | do dia 1 até ontem |
| Período futuro | 0 |

### Etapa 4 — filtra só os dias com leitura
Dos dias fechados, pega apenas os que têm valor no Hash de consumo. Um dia fechado sem leitura não entra na média — ele conta para a cobertura mínima, mas não para o cálculo do consumo.

### Etapa 5 — verifica cobertura mínima
```
cobertura = dias_com_leitura / dias_fechados
```

Se cobertura < 50%: a unidade é **removida** dos dois ZSETs de ranking. Não é justo comparar uma unidade com leituras de 3 dias com outra que tem leituras de 28.

Exemplo: janeiro tem 31 dias → mínimo de 16 dias com leitura para entrar no ranking.

### Etapa 6 — calcula e grava os scores
```
media_diaria  = soma(litros dos dias com leitura) / quantidade de dias com leitura
perm2_score   = media_diaria / area_m2
```

Exemplo concreto:
```
leituras em 20 dias de outubro → total: 2.600 L
media_diaria  = 2.600 / 20 = 130 L/dia
perm2_score   = 130 / 650  = 0,2 L/m²·dia   ← score no ZSET perm2
```

Os dois `ZADD` (um para `perm2`, um para `consumo`) são enviados dentro de um `pipeline(transaction=True)`: ou os dois são gravados, ou nenhum. Isso evita que o Redis fique com os ZSETs em estados diferentes entre si.

Unidades sem área são removidas do ZSET `perm2` e mantidas apenas no ZSET `consumo`.

---

## 6. Períodos armazenados

O endpoint `POST /sync` sempre busca o **mês corrente e o mês anterior** para cobrir viradas de mês (unidades cujo consumo de ontem pertence ao mês passado). Dados de meses ainda mais antigos, carregados em syncs anteriores, permanecem no Redis até atingir 13 meses de TTL.

Exemplo em 23/10/2026: o sync popula `2026-10` e `2026-09`.

---

## 7. Regras de entrada no ranking

| Condição | Comportamento |
|---|---|
| `classificationGroup` não começa com `COMERCIAL` | Rejeitada com HTTP 422 |
| `areaM2` ausente (NULL) | Entra no ranking `consumo`; fora do `perm2`; listada em `withoutArea` |
| `areaM2 <= 0` | Rejeitada com HTTP 422 |
| Menos de 50% dos dias fechados com leitura | Fora dos dois rankings |
| Dia corrente enviado | Gravado, mas ignorado no cálculo até fechar |

---

## 8. Endpoints da API

A API roda no repositório `delta-redis-database` (FastAPI + redis-py). Todos os parâmetros de query usam camelCase.

| Método | Rota | Parâmetros principais | Descrição |
|---|---|---|---|
| `GET` | `/health` | — | Verifica conexão com o Redis |
| `POST` | `/save-property` | body: `organizationId`, `propertyId`, `name`, `classificationGroup`, `areaM2?` | Cadastra ou atualiza unidade |
| `DELETE` | `/remove-property` | query: `organizationId`, `propertyId` | Remove unidade e todos os seus dados |
| `POST` | `/save-consumption` | body: `propertyId`, `days: [{date, liters}]` | Grava consumo e atualiza ranking em tempo real |
| `GET` | `/get-ranking` | `organizationId`, `period` (YYYY-MM), `criterion` (perm2\|consumo), `limit?` | Ranking completo com `withoutArea` |
| `GET` | `/get-position` | `organizationId`, `propertyId`, `period`, `criterion` | Posição, total e score de uma unidade |
| `GET` | `/get-best` | `organizationId`, `period`, `criterion` | Primeira colocada (card "Unidade mais eficiente") |
| `POST` | `/sync` | — | Faz login na delta-api-postgres, busca unidades e consumo e popula o Redis |

---

## 9. Fluxo de dados

```
[ETL bi_etl.py]
      │ roda às 03:00, atualiza gold.ft_consumption_daily
      ▼
[POST /sync — delta-redis-database]
      │ POST /delta/auth/login → obtém JWT
      │ GET /delta/property (Authorization: Bearer) → filtra COMERCIAL_*
      │ GET /delta/analytics/consumption-daily/{id} (Authorization: Bearer)
      │ grava Hash de propriedade + consumo
      │ recalcula scores → ZADD nos Sorted Sets (pipeline atômico)
      ▼
[Redis Cloud — Sorted Sets]
      │ ZRANGE / ZRANK / ZSCORE
      ▼
[Painel web industrial — tela "Ranking"]
```

O Redis é apenas camada de consulta: todos os dados podem ser reconstruídos reenviando os dados da camada gold do PostgreSQL.

---

## 10. Decisões de projeto

| Assunto | Decisão |
|---|---|
| Critério padrão | `perm2` (L/m²·dia), menor = melhor |
| Critério secundário | `consumo` (média diária de litros) |
| Segmentação | Por organização e mês; apenas unidades COMERCIAL_* |
| Cobertura mínima | 50% dos dias fechados do mês com leitura |
| Retenção | 13 meses |
| Fonte dos dados | `delta-api-postgres` via `POST /sync`; autenticação JWT com `POSTGRES_API_EMAIL` e `POSTGRES_API_PASSWORD` |
| Dia corrente | Gravado, ignorado no cálculo até fechar |
| Desempate | Lexicográfico pelo member (zero-padded) — equivale a crescente por `propertyId` |
