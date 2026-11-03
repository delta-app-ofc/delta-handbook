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
| `Property` (`Casa` ou `Predio`, mais `Residencial`) | Imóvel | `LOCATED_AT`, `HAS_DEVICE` |
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

#### 5. Propriedades de cada nó e relacionamento

| Nó | Propriedades gravadas pelo `setup.cypher` e `seed.cypher` |
|---|---|
| `User:Pessoa` | `id`, `name`, `email`, `phone`, `birthDate`, `registrationDate`, `isActive`, `isAdmin`, `isManager` |
| `Property` | `id`, `name`, `registrationDate` |
| `Address` | `id`, `cep`, `city`, `state` |
| `Region` | `id`, `name` |
| `RegionRate` | `id`, `m3Value` (preço por m³), `initialValidity`, `finalValidity` |
| `Device` | `id`, `deviceId`, `isActive`, `installationDate` |
| `WaterBill` | `id`, `month`, `totalValue` (valor em reais), `m3Value` (consumo em m³) |
| `Habit` | `id`, `name`, `description` |
| `UserHabit` | `id`, `frequency` |
| `Day` | `id`, `name` |

O único relacionamento com propriedade é `OWNS`, que guarda `associationDate`, a data em que o usuário passou a possuir o imóvel.

> **Atenção ao nome `m3Value`:** em `RegionRate` ele é o **preço** do m³ (por exemplo, 8,50), e em `WaterBill` ele é o **consumo** em m³ (por exemplo, 15,20). O nome é igual, mas o significado é diferente.

#### 6. Dados carregados

Os dois scripts juntos criam o grafo abaixo. A coluna "origem" mostra quanto vem de cada arquivo.

| Nó | Total | `setup.cypher` | `seed.cypher` |
|---|---|---|---|
| `User:Pessoa` | 7 | 3 (Mariana, João, Ana) | 4 (Carlos, Beatriz, Lucas, Julia) |
| `Property` | 7 | 3 | 4 |
| `Address` | 7 | 3 | 4 |
| `Region` | 5 | 5 (LESTE, OESTE, SUL, NORTE, CENTRO) | 0 |
| `RegionRate` | 5 | 3 | 2 |
| `Day` | 7 | 7 (SEGUNDA a DOMINGO) | 0 |
| `Habit` | 6 | 6 | 0 |
| `UserHabit` | 10 | 6 | 4 |
| `Device` | 3 | 3 (ESP001 a ESP003) | 0 |
| `WaterBill` | 4 | 4 | 0 |

Regiões e tarifas, como carregadas:

| Região | Tarifa por m³ |
|---|---|
| LESTE | 7,90 |
| OESTE | 8,80 |
| SUL | 8,50 |
| NORTE | 9,10 |
| CENTRO | 8,20 |

Os imóveis são `Casa` (1, 2, 4, 5 e 7) ou `Predio` (3 e 6), e todos são `Residencial`.

#### 7. Limitações conhecidas

- **Nenhum imóvel comercial no grafo.** O README prevê o rótulo `:Comercial`, mas a carga só cria `:Residencial`. O ranking do Redis, ao contrário, só trata unidades comerciais.
- **Os usuários novos do `seed.cypher` não têm dispositivo nem fatura.** Só Mariana, João e Ana têm esses dados.
- **O grafo é uma carga estática.** O repositório só tem scripts `.cypher` e o `load_graph.py`, que executa esses arquivos. Não há sincronização com o PostgreSQL, e os identificadores do grafo são independentes dos do banco relacional.
- **O `setup.cypher` apaga tudo antes de criar** (`MATCH (n) DETACH DELETE n`). O README o descreve como re-executável sem duplicar, mas ele também apaga o que o `seed.cypher` carregou. Depois de rodá-lo, é preciso rodar o `seed.cypher` de novo.
- **`UserHabit` é criado com `CREATE` no `setup.cypher`** e com `MERGE` no `seed.cypher`.

#### 8. Execução

O script `load_graph.py` conecta pelo driver oficial do Neo4j, usando `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` e `NEO4J_DATABASE`. A carga de desenvolvimento usa o Neo4j Aura, e o CI usa a imagem `neo4j:5-community`.

O loader só executa quatro arquivos: `setup.cypher`, `seed.cypher`, `querys/querys.cypher` e `querys/transversal.cypher`. Ele recusa caminho absoluto, `..`, arquivo fora do repositório, extensão diferente de `.cypher` e diretório, e fecha o driver mesmo quando uma consulta falha. O pytest cobre esses casos e usa um driver simulado, sem conectar ao Neo4j.

#### 9. Como comprovar

1. Executar `python load_graph.py setup.cypher` e depois `python load_graph.py seed.cypher`, com as variáveis de `.env.example`.
2. No Neo4j Browser, executar `MATCH (n)-[r]->(m) RETURN n, r, m` e conferir o grafo.
3. Executar `SHOW CONSTRAINTS` e conferir as 10 constraints de unicidade.

> `setup.cypher` começa com `MATCH (n) DETACH DELETE n`, que apaga todo o grafo. Use apenas em um banco de desenvolvimento.

![Grafo carregado no Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query1.png?raw=true)
