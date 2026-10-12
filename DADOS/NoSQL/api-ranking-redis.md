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
| `ranking:org:{organizationId}:{YYYY-MM}:consumo` | Sorted Set | member = propertyId com zeros à esquerda, score = litros totais |

### Regras de escrita

- O dia é um campo do Hash de consumo → reenviar o mesmo dia **sobrescreve** (idempotente).
- A cada escrita, médias e totais são recalculados a partir do Hash (no máximo 31 campos) e os dois Sorted Sets são atualizados em `pipeline(transaction=True)`.
- Se a área da unidade mudar, os scores do mês corrente são recalculados automaticamente.
- **Retenção:** 13 meses — TTL aplicado ao criar ou atualizar chaves de consumo e ranking.

---

## 4. Regras de entrada no ranking

| Condição | Comportamento |
|---|---|
| `classificationGroup` não começa com `COMERCIAL` | Rejeitada com HTTP 422 |
| `areaM2` ausente (NULL) | Entra no ranking `consumo`; fora do `perm2`; listada em `withoutArea` |
| `areaM2 <= 0` | Rejeitada com HTTP 422 |
| Menos de 50% dos dias fechados com leitura | Fora dos dois rankings |
| Dia corrente enviado | Gravado, mas ignorado no cálculo até fechar |

---

## 5. Endpoints da API

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

---

## 6. Fluxo de dados

```
[ETL bi_etl.py]
      │ roda às 03:00, atualiza gold.ft_consumption_daily
      ▼
[sync_from_postgres.py]
      │ GET /delta/property → filtra COMERCIAL_*
      │ GET /delta/analytics/consumption-daily/{id}
      │ POST /save-property + POST /save-consumption
      ▼
[API Redis — delta-redis-database]
      │ grava Hash de consumo
      │ recalcula scores → ZADD nos Sorted Sets (pipeline atômico)
      ▼
[Redis Cloud — Sorted Sets]
      │ ZRANGE / ZRANK / ZSCORE
      ▼
[Painel web industrial — tela "Ranking"]
```

O Redis é apenas camada de consulta: todos os dados podem ser reconstruídos reenviando os dados da camada gold do PostgreSQL.

---

## 7. Decisões de projeto

| Assunto | Decisão |
|---|---|
| Critério padrão | `perm2` (L/m²·dia), menor = melhor |
| Critério secundário | `consumo` (litros totais do mês) |
| Segmentação | Por organização e mês; apenas unidades COMERCIAL_* |
| Cobertura mínima | 50% dos dias fechados do mês com leitura |
| Retenção | 13 meses |
| Fonte dos dados | `delta-api-postgres` (endpoints `/delta/property` e `/delta/analytics/consumption-daily/{id}`) |
| Dia corrente | Gravado, ignorado no cálculo até fechar |
| Desempate | Lexicográfico pelo member (zero-padded) — equivale a crescente por `propertyId` |
