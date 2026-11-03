# 1. Banco de Dados II — Texto da Entrega

**Responsáveis pela disciplina:** Mariana Marrão Ferreira Felis e Samuel Pimenta Hironimus

- Repositório do MongoDB: https://github.com/delta-app-ofc/delta-mongo-database
- Repositório do Redis: https://github.com/delta-app-ofc/delta-redis-database
- Repositório do Neo4j: https://github.com/delta-app-ofc/delta-neo4j-database
- Repositório de documentação: https://github.com/delta-app-ofc/delta-handbook/tree/main/DADOS/NoSQL

## Requisitos

### BD2-01 — Usar obrigatoriamente MongoDB

MongoDB com dois bancos, `db_delta_telemetry` e `db_delta_app`, e oito coleções com validação `$jsonSchema` e índices, testadas em CI com um MongoDB temporário.

**Evidências diretas:**

- Versionamento: https://github.com/delta-app-ofc/delta-mongo-database
- API sobre o MongoDB: https://github.com/delta-app-ofc/delta-api-mongo
- Business Intelligence, que lê o MongoDB: https://github.com/delta-app-ofc/delta-business-intelligence
- Inteligência Artificial, que grava no MongoDB: https://github.com/delta-app-ofc/delta-artificial-intelligence
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-01-mongodb.md

### BD2-02 — Usar obrigatoriamente Redis

API FastAPI que guarda no Redis o ranking de eficiência hídrica das unidades comerciais, por organização e mês, em Hash, Set e Sorted Set, com retenção de 13 meses e 20 testes contra um Redis real.

**Evidências diretas:**

- Versionamento: https://github.com/delta-app-ofc/delta-redis-database
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-02-redis.md

### BD2-03 — Usar MongoDB em alguma interação conversacional

O chatbot persiste cada conversa na coleção `chat_sessions`, com um documento por sessão e um array `messages`. A coleção `chat_feedback` guarda a avaliação de cada sessão.

**Evidências diretas:**

- Persistência das sessões: https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/memory/session.py
- Schema e índices das coleções de chat: https://github.com/delta-app-ofc/delta-mongo-database/blob/main/scripts/delta-app/script-collections.js
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-03-mongodb-conversa.md

### BD2-04 — Usar Redis para fila de processamento e/ou ranking em tempo real

Ranking de eficiência por `perm2` (litros por m² por dia) em Sorted Sets, recalculado a cada `POST /save-consumption` dentro de uma transação, sem job em lote, e exibido na tela de ranking do web-app.

**Evidências diretas:**

- Cálculo do ranking: https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/ranking.py
- Rotas de leitura: https://github.com/delta-app-ofc/delta-redis-database/blob/main/app/routes/ranking.py
- Testes: https://github.com/delta-app-ofc/delta-redis-database/blob/main/tests/test_ranking.py
- Tela de ranking do web-app: https://github.com/delta-app-ofc/delta-web-app/blob/main/src/pages/ranking/index.tsx
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-04-redis-ranking.md

### BD2-05 — Colar imagem de modelo conceitual com coleções, documentos, chaves, relações, nós, relacionamentos e propriedades, conforme aplicável

Modelo de cada banco: coleções e relações do MongoDB, chaves e tipos do Redis, e nós, relacionamentos e propriedades do Neo4j.

**Evidências diretas:**

- Modelagem MongoDB: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/modelagem-mongodb.md
- Modelagem Redis: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/api-ranking-redis.md
- Modelagem Neo4j: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/modelagem-neo4j.md
- Grafo completo: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query1.png
- Usuário, imóvel, região e dispositivo: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query2.png
- Faturas e tarifa por região: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query3.png
- Hábitos por usuário e dia: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query4.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-05-modelagem-conceitual.md

### BD2-06 — Usar Neo4j para modelar as entidades principais do projeto como grafo

Grafo com 10 tipos de nó (usuário, imóvel, endereço, região, tarifa, dispositivo, fatura, hábito, hábito do usuário e dia) e 9 relacionamentos, com constraint de unicidade por tipo e carga testada em CI.

**Evidências diretas:**

- Versionamento: https://github.com/delta-app-ofc/delta-neo4j-database
- Constraints e dados base: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/setup.cypher
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-06-neo4j-grafo.md

### BD2-07 — Responder pelo menos uma pergunta de negócio que exija traversal, não uma simples busca por nó

Pergunta: quais usuários praticam hábitos aos sábados e moram em regiões com tarifa superior a R$ 8,00 por m³. A consulta percorre hábito, dia, imóvel, endereço, região e tarifa e devolve cinco usuários.

**Evidências diretas:**

- Query transversal: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/querys/transversal.cypher
- Resultado da query: https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/transversal.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-07-neo4j-traversal.md

### BD2-08 — Anexar documento de evidências ou inserir link para ele

Um documento de justificativa por requisito, mais os documentos técnicos de cada banco, reunidos neste texto de entrega.

**Evidências diretas:**

- Repositório de documentação: https://github.com/delta-app-ofc/delta-handbook
- Pasta com a justificativa de cada requisito: https://github.com/delta-app-ofc/delta-handbook/tree/main/DADOS/NoSQL/documentacao-requisitos
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/NoSQL/documentacao-requisitos/bd2-08-documento-evidencias.md
