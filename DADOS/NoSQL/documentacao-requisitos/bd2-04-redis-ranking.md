### BD2-04 — Usar Redis para fila de processamento e/ou ranking em tempo real

**Evidência direta:**

- [Cálculo do ranking com Sorted Sets](https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/ranking.py)
- [Rotas de leitura do ranking (`/get-ranking`, `/get-position`, `/get-best`)](https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/routes/ranking.py)
- [Rota de gravação do consumo (`/save-consumption`)](https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/routes/consumption.py)
- [Testes do ranking](https://github.com/delta-app-ofc/delta-redis-database/blob/main/tests/test_ranking.py)
- [Serviço do web-app que consome o ranking](https://github.com/delta-app-ofc/delta-web-app/blob/main/src/services/ranking.ts)
- [Tela de ranking do web-app](https://github.com/delta-app-ofc/delta-web-app/blob/main/src/pages/ranking/index.tsx)
- [Documentação da API de ranking](../api-ranking-redis.md)

**Localização e como comprovar:**

O requisito é atendido pelo **ranking em tempo real**. O projeto não usa o Redis como fila de processamento.

Cada `POST /save-consumption` grava os litros do dia no Hash `consumption:{propertyId}:{YYYY-MM}` e recalcula o ranking na mesma requisição. Não há job em lote nesse caminho.

#### 1. Como o ranking é calculado

O critério é o `perm2`, em litros por m² por dia:

```
consumo_medio_diario = soma(litros dos dias fechados) / dias_com_leitura
perm2                = consumo_medio_diario / area_m2
```

| Regra | Justificativa |
|---|---|
| Menor `perm2` fica em 1º | Quanto menos litros por m², mais eficiente é a unidade |
| Usa a média por dia | Fevereiro e março têm tamanhos diferentes e precisam ser comparáveis |
| O dia corrente não entra | Um dia parcial faria a unidade parecer mais eficiente do que é |
| Cobertura mínima de 50% do mês | Poucas leituras não representam o mês e tirariam a unidade do ranking |
| Membro do Sorted Set com 6 dígitos (`000151`) | Garante desempate previsível por ID |

O recálculo roda em uma transação (`MULTI/EXEC`): `ZADD` e `EXPIRE` nos dois Sorted Sets, ou `ZREM` quando a unidade não tem cobertura suficiente.

#### 2. Leitura

| Endpoint | Comando Redis | Uso |
|---|---|---|
| `GET /get-ranking` | `ZRANGE ... WITHSCORES` | Lista ordenada, com `limit` |
| `GET /get-position` | `ZRANK`, `ZSCORE`, `ZCARD` | Posição de uma unidade |
| `GET /get-best` | `ZRANGE 0 0` | A unidade mais eficiente |

O web-app chama `GET /get-ranking` com `organizationId`, `period`, `criterion` e `limit` (10) e mostra a unidade mais eficiente, o gráfico do top 5 e a classificação completa.

#### 3. Carga complementar

O `POST /sync` carrega do PostgreSQL o consumo do mês atual e do anterior. Ele é disparado ao fim do ETL (`etl-completed`) e por um cron diário às 04h. O ranking continua sendo atualizado na hora a cada gravação, e o `/sync` apenas completa os dados.

#### 4. Como comprovar

1. Cadastrar duas unidades de áreas diferentes e enviar o mesmo consumo diário para ambas.
2. Consultar `GET /get-ranking` e conferir que a unidade de maior área aparece em 1º.
3. Enviar um consumo novo e consultar de novo, sem rodar nenhum job, e conferir que a ordem mudou.
4. Rodar `pytest` e conferir os testes `test_justica_por_m2`, `test_cobertura_minima`, `test_idempotencia` e `test_empate_desempate_por_property_id`.

> **Pendente:** anexar o print da tela de ranking exibindo dados reais vindos da API.

#### 5. Limitações conhecidas

- O recálculo lê o consumo fora da transação. Duas requisições simultâneas para a mesma unidade podem deixar o ranking desatualizado até a próxima gravação.
- O tempo de expiração (`EXPIRE`) e a concorrência não têm teste automatizado.
