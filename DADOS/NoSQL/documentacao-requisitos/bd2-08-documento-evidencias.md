### BD2-08 — Anexar documento de evidências ou inserir link para ele

**Evidência direta:**

- [Repositório de documentação (`delta-handbook`)](https://github.com/delta-app-ofc/delta-handbook)
- [Entrega da seção de Banco de Dados II](entrega-banco-dados-2.md)
- [Repositório do Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database)
- [Repositório do Redis](https://github.com/delta-app-ofc/delta-redis-database)
- [Repositório do MongoDB](https://github.com/delta-app-ofc/delta-mongo-database)

**Localização e como comprovar:**

O relatório de justificativa é formado por um documento por requisito, em `DADOS/NoSQL/documentacao-requisitos/`, e pelos documentos técnicos que registram as decisões de cada banco.

#### 1. Justificativa por requisito

| Requisito | Documento |
|---|---|
| BD2-01 | [MongoDB](bd2-01-mongodb.md) |
| BD2-02 | [Redis](bd2-02-redis.md) |
| BD2-03 | [MongoDB em interação conversacional](bd2-03-mongodb-conversa.md) |
| BD2-04 | [Redis para ranking em tempo real](bd2-04-redis-ranking.md) |
| BD2-05 | [Modelagem conceitual](bd2-05-modelagem-conceitual.md) |
| BD2-06 | [Neo4j como grafo](bd2-06-neo4j-grafo.md) |
| BD2-07 | [Pergunta de negócio com traversal](bd2-07-neo4j-traversal.md) |
| BD2-08 | Este documento |

#### 2. Decisões de projeto registradas

| Tema | Documento | Decisões justificadas |
|---|---|---|
| MongoDB | [modelagem-mongodb.md](../modelagem-mongodb.md) | Divisão em dois bancos, padrão de *bucket*, índices e expiração |
| Redis | [api-ranking-redis.md](../api-ranking-redis.md) | Critério `perm2`, cobertura mínima, retenção |
| Neo4j | [modelagem-neo4j.md](../modelagem-neo4j.md) | Multi-labels, nó de interseção, constraints e queries |
| Regras de negócio | [regras-negocio.md](../regras-negocio.md) | Padrões de nomes e dados |
| Governança de acesso | [governanca-acesso.md](../governanca-acesso.md) | Níveis de acesso no MongoDB |

#### 3. Como comprovar

1. Abrir a [entrega de Banco de Dados II](entrega-banco-dados-2.md) e conferir a tabela BD2-01 a BD2-08 com os links.
2. Abrir cada documento `bd2-XX` e conferir as seções "Evidência direta" e "Localização e como comprovar".
3. Abrir os repositórios do MongoDB, do Redis e do Neo4j e conferir os arquivos citados.
