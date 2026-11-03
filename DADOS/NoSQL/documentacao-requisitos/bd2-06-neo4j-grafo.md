### BD2-06 — Usar Neo4j para modelar as entidades principais do projeto como grafo

**Evidência direta:**

- [Repositório de versionamento do Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database)
- [README com o modelo em grafo](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/README.md)
- [`setup.cypher`: constraints e dados base](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/setup.cypher)
- [`seed.cypher`: usuários e dados adicionais](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/seed.cypher)
- [`load_graph.py`: carregador dos scripts](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/load_graph.py)
- [Teste do carregador](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/tests/test_load_graph.py)
- [Workflow de teste com Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/.github/workflows/test.yml)
- [Documentação da modelagem Neo4j](../modelagem-neo4j.md)

**Localização e como comprovar:**

O grafo representa as entidades principais do Delta e as ligações entre elas: quem possui qual imóvel, onde ele fica, qual tarifa vale na região, quais faturas e dispositivos existem e quais hábitos o usuário pratica em cada dia da semana.

#### 1. Nós e relacionamentos

| Nó | Representa | Relacionamentos que saem dele |
|---|---|---|
| `User:Pessoa` | Usuário do sistema | `OWNS`, `HAS_BILL`, `HAS_HABIT` |
| `Property` (`Casa` ou `Predio`, `Residencial` ou `Comercial`) | Imóvel | `LOCATED_AT`, `HAS_DEVICE` |
| `Address` | Endereço | `IN_REGION` |
| `Region` | Região tarifária | `HAS_RATE` |
| `RegionRate` | Tarifa da região | nenhum |
| `Device` | Dispositivo instalado | nenhum |
| `WaterBill` | Fatura | nenhum |
| `UserHabit` | Hábito de um usuário, com a frequência | `IS_HABIT`, `ON_DAY` |
| `Habit`, `Day` | Catálogo de hábitos e dias da semana | nenhum |

#### 2. Por que um grafo

O caminho usuário, imóvel, endereço, região e tarifa tem cinco saltos. Em SQL ele vira uma cadeia de `JOIN`s. No grafo, cada salto é um relacionamento já gravado, e a consulta lê o caminho diretamente. Perguntas como "quem paga a tarifa mais cara e pratica tal hábito no sábado" são o tipo de pergunta em que o grafo é natural.

#### 3. Decisões de modelagem

- **Multi-labels:** todo `User` carrega também `:Pessoa`, e o imóvel carrega tipo e classificação. Isso permite `MATCH (p:Casa:Residencial)` sem filtrar por propriedade de texto.
- **`UserHabit` como nó de interseção:** frequência e dia variam por usuário, e não pelo hábito do catálogo.
- **Constraints de unicidade:** há uma constraint de unicidade em `id` para cada um dos 10 tipos de nó.
- **`MERGE` nos dados de referência:** regiões, dias e hábitos usam `MERGE` e não duplicam.

#### 4. Qualidade

O workflow `test.yml` sobe um Neo4j 5, executa `setup.cypher` e `seed.cypher` e confere 7 usuários, 7 dias e 7 relações `OWNS`. O pytest testa o carregador, inclusive a recusa de caminhos de arquivo não permitidos.

#### 5. Como comprovar

1. Executar `python load_graph.py setup.cypher` e depois `python load_graph.py seed.cypher`, com as variáveis de `.env.example`.
2. No Neo4j Browser, executar `MATCH (n)-[r]->(m) RETURN n, r, m` e conferir o grafo.
3. Executar `SHOW CONSTRAINTS` e conferir as 10 constraints de unicidade.

> `setup.cypher` começa com `MATCH (n) DETACH DELETE n`, que apaga todo o grafo. Use apenas em um banco de desenvolvimento.

![Grafo carregado no Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query1.png?raw=true)
