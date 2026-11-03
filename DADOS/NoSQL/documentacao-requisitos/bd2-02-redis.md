### BD2-02 — Usar obrigatoriamente Redis

**Evidência direta:**

- [Repositório de versionamento do Redis](https://github.com/delta-app-ofc/delta-redis-database)
- [README com o modelo de chaves e os endpoints](https://github.com/delta-app-ofc/delta-redis-database/blob/main/README.md)
- [Cálculo e gravação do ranking](https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/ranking.py)
- [Conexão com o Redis](https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/redis_client.py)
- [Testes contra um Redis real](https://github.com/delta-app-ofc/delta-redis-database/blob/main/tests/test_ranking.py)
- [Documentação da API de ranking](../api-ranking-redis.md)

**Localização e como comprovar:**

O Redis guarda o ranking de eficiência hídrica das unidades comerciais, por organização e por mês. Uma API FastAPI recebe os consumos e mantém as estruturas atualizadas.

| Chave | Tipo | Conteúdo |
|---|---|---|
| `property:{propertyId}` | Hash | `name`, `organizationId`, `areaM2` |
| `org:{organizationId}:properties` | Set | IDs das unidades da organização |
| `consumption:{propertyId}:{YYYY-MM}` | Hash | Campo = dia (`01` a `31`), valor = litros |
| `ranking:org:{organizationId}:{YYYY-MM}:perm2` | Sorted Set | Score = litros por m² por dia |
| `ranking:org:{organizationId}:{YYYY-MM}:consumo` | Sorted Set | Score = média diária em litros |

#### 1. Por que Redis

O ranking precisa ser lido com frequência pelo painel web e refletir cada consumo novo sem rodar uma view SQL nem um ETL. O Sorted Set mantém os membros ordenados pelo score, e a posição de uma unidade sai de uma única consulta (`ZRANK`).

#### 2. Retenção

Os Hashes de consumo e os Sorted Sets de ranking expiram em `RETENTION_MONTHS` meses (padrão 13), por meio de `EXPIRE`. Os dados cadastrais (`property` e `org:properties`) permanecem até a remoção da unidade.

#### 3. Como comprovar

1. Subir a API com um Redis local (`docker-compose.dev.yml`).
2. Cadastrar uma unidade com `POST /save-property` e enviar consumos com `POST /save-consumption`.
3. Consultar `GET /get-ranking` e conferir o resultado ordenado.
4. Rodar `pytest` e conferir os 20 testes, que usam um Redis isolado e limpam o banco a cada teste.

> **Pendente:** anexar o print das chaves no Redis Insight ou no `redis-cli`.
