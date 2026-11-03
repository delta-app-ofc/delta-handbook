### BD2-05 — Colar imagem de modelo conceitual com coleções, documentos, chaves, relações, nós, relacionamentos e propriedades, conforme aplicável

**Evidência direta:**

- [Modelagem MongoDB (coleções, documentos e índices)](../modelagem-mongodb.md)
- [Modelagem do ranking Redis (chaves e tipos)](../api-ranking-redis.md)
- [Modelagem Neo4j (nós e relacionamentos)](../modelagem-neo4j.md)
- [Modelo em grafo no repositório do Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/README.md)
- [Visão geral do grafo (`query1.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query1.png)
- [Usuário, imóvel, região e dispositivo (`query2.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query2.png)
- [Faturas e tarifa por região (`query3.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query3.png)
- [Hábitos por usuário e dia (`query4.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query4.png)

**Localização e como comprovar:**

Cada banco tem um modelo próprio, e cada um é representado do jeito que cabe ao seu paradigma.

#### 1. MongoDB: coleções, documentos e relações

| Banco | Coleção | Chave de busca principal | Relação |
|---|---|---|---|
| `db_delta_telemetry` | `consumption_summary` | `{ user_id, window_started_at }` | `user_id` e `device_id` apontam para o PostgreSQL |
| `db_delta_telemetry` | `device_status` | `device_id` (único) | `device_id` aponta para `tb_device` |
| `db_delta_app` | `user_preferences` | `user_id` (único) | `user_id` aponta para `tb_user` |
| `db_delta_app` | `alerts_history` | `{ user_id, triggered_at }` | `device_id` e `user_id` apontam para o PostgreSQL |
| `db_delta_app` | `chat_sessions` | `{ user_id, last_activity_at }` | Contém o array embutido `messages` |
| `db_delta_app` | `chat_feedback` | `session_id` | `session_id` referencia `chat_sessions._id` |
| `db_delta_app` | `weather_daily` | `{ country, state, city, weather_date }` (único) | Contém o array embutido `hours` (até 24 itens) |
| `db_delta_app` | `observability_requests` | `request_id` (único) | `user_hash` é um HMAC do `user_id`, sem o `user_id` |

As relações com o PostgreSQL são lógicas, sem chave estrangeira. O único vínculo entre coleções é `chat_feedback.session_id`.

> **Pendente:** anexar a imagem do modelo MongoDB.

#### 2. Redis: chaves, tipos e relações

```
property:{propertyId}                              Hash   name, organizationId, areaM2
org:{organizationId}:properties                    Set    propertyId, ...
consumption:{propertyId}:{YYYY-MM}                 Hash   dia -> litros
ranking:org:{organizationId}:{YYYY-MM}:perm2       ZSET   propertyId -> L/m2/dia
ranking:org:{organizationId}:{YYYY-MM}:consumo     ZSET   propertyId -> média diária em litros
```

A unidade em `property` entra em `org:properties`, recebe os dias de `consumption` e dá origem aos dois Sorted Sets de ranking.

> **Pendente:** anexar a imagem do modelo Redis.

#### 3. Neo4j: nós, relacionamentos e propriedades

```
(User:Pessoa)-[:OWNS]->(Property:Casa|Predio:Residencial|Comercial)
(Property)-[:LOCATED_AT]->(Address)-[:IN_REGION]->(Region)-[:HAS_RATE]->(RegionRate)
(Property)-[:HAS_DEVICE]->(Device)
(User)-[:HAS_BILL]->(WaterBill)
(User)-[:HAS_HABIT]->(UserHabit)-[:IS_HABIT]->(Habit)
(UserHabit)-[:ON_DAY]->(Day)
```

| Nó | Propriedades usadas |
|---|---|
| `User:Pessoa` | `id`, `name`, `email`, `phone`, `birthDate`, `registrationDate`, `isActive`, `isAdmin`, `isManager` |
| `Property` | `id`, `name`, `registrationDate` |
| `Address` | `id`, `cep`, `city`, `state` |
| `Region` | `id`, `name` |
| `RegionRate` | `id`, `m3Value`, `initialValidity`, `finalValidity` |
| `UserHabit` | `id`, `frequency` |
| `Habit`, `Day` | `id`, `name` |

O nó `UserHabit` é uma interseção: a frequência e o dia de um hábito variam por usuário, e não pelo hábito do catálogo. Esse é o equivalente a uma tabela associativa no modelo relacional.

Imagens do grafo carregado no Neo4j:

| Visão | Imagem |
|---|---|
| Grafo completo de um usuário | ![Visão geral do grafo](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query1.png?raw=true) |
| Usuário, imóvel, endereço, região e dispositivo | ![Imóveis e regiões](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query2.png?raw=true) |
| Faturas e tarifa por região | ![Faturas e tarifas](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query3.png?raw=true) |
| Hábitos por usuário e dia | ![Hábitos por dia](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query4.png?raw=true) |

#### 4. Como comprovar

1. Abrir [`modelagem-mongodb.md`](../modelagem-mongodb.md) e conferir os campos e índices de cada coleção.
2. Abrir [`api-ranking-redis.md`](../api-ranking-redis.md) e conferir a tabela de chaves.
3. Abrir o Neo4j Browser, executar `MATCH (n)-[r]->(m) RETURN n, r, m` e comparar com `query1.png`.
