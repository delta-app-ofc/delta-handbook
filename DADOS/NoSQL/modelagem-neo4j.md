# Modelagem Neo4j — DELTA

Este documento descreve a modelagem em grafo do projeto DELTA no Neo4j Aura, os scripts Cypher disponíveis e as queries de negócio implementadas.

## 1. Modelo de Grafo

```
(User:Pessoa)-[:OWNS]->(Property:Casa|Predio:Residencial|Comercial)
(Property)-[:LOCATED_AT]->(Address)-[:IN_REGION]->(Region)-[:HAS_RATE]->(RegionRate)
(Property)-[:HAS_DEVICE]->(Device)
(User)-[:HAS_BILL]->(WaterBill)
(User)-[:HAS_HABIT]->(UserHabit)-[:IS_HABIT]->(Habit)
(UserHabit)-[:ON_DAY]->(Day)
```

### 1.1 Nós e labels

| Nó | Labels | Descrição |
|---|---|---|
| `User` | `:User:Pessoa` | Usuário do sistema. Recebe também o label `:Pessoa` para representar a entidade humana de forma genérica |
| `Property` | `:Property:Casa:Residencial` ou `:Property:Predio:Residencial` | Imóvel associado ao usuário. O tipo (`Casa`/`Predio`) e a classificação (`Residencial`/`Comercial`) são modelados como labels, não como propriedades de texto |
| `Address` | `:Address` | Endereço do imóvel |
| `Region` | `:Region` | Região geográfica (LESTE, OESTE, SUL, NORTE, CENTRO) |
| `RegionRate` | `:RegionRate` | Tarifa de água vigente por região |
| `Device` | `:Device` | Dispositivo IoT instalado no imóvel |
| `WaterBill` | `:WaterBill` | Fatura de água do usuário |
| `Habit` | `:Habit` | Catálogo de hábitos relacionados ao consumo de água |
| `UserHabit` | `:UserHabit` | Nó de interseção entre usuário e hábito — armazena frequência e dias da semana por usuário |
| `Day` | `:Day` | Dia da semana |

> **Por que `UserHabit` existe?** Frequência e dias variam por usuário, não pelo hábito em si. Sem esse nó intermediário, haveria duplicação de dados ou perda de granularidade.

### 1.2 Relacionamentos

| Relacionamento | Direção | Propriedades | Significado |
|---|---|---|---|
| `OWNS` | `User → Property` | `associationDate` | Usuário é proprietário do imóvel |
| `LOCATED_AT` | `Property → Address` | — | Imóvel fica no endereço |
| `IN_REGION` | `Address → Region` | — | Endereço pertence à região |
| `HAS_RATE` | `Region → RegionRate` | — | Tarifa vigente da região |
| `HAS_DEVICE` | `Property → Device` | — | Dispositivo instalado no imóvel |
| `HAS_BILL` | `User → WaterBill` | — | Fatura pertence ao usuário |
| `HAS_HABIT` | `User → UserHabit` | — | Usuário registra o hábito |
| `IS_HABIT` | `UserHabit → Habit` | — | De qual hábito do catálogo se trata |
| `ON_DAY` | `UserHabit → Day` | — | Dia em que o hábito ocorre |

---

## 2. Decisões de Modelagem

### Multi-labels como categorias
As aulas de Neo4j ensinaram que labels devem ser usadas para categorizar nós, não apenas identificá-los. Por isso:

- Todo `User` também recebe o label `:Pessoa` — permite buscar entidades humanas independentemente do papel no sistema.
- `Property` usa labels para tipo e classificação (`Casa`, `Predio`, `Residencial`, `Comercial`) em vez de propriedades de texto, permitindo filtros eficientes com `MATCH (p:Casa)` sem varredura por valor de string.

### MERGE em vez de CREATE
O `setup.cypher` usa `MERGE` para todos os nós de referência (Region, Day, Habit, User, Property, Device, etc.), tornando o script idempotente — pode ser re-executado sem duplicar dados.

### Constraints
Todas as entidades possuem constraint de unicidade no campo `id`:

```cypher
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;
```

---

## 3. Scripts disponíveis

| Arquivo | Função |
|---|---|
| `setup.cypher` | Limpa o banco, cria constraints, popula nós e relacionamentos base |
| `seed.cypher` | Adiciona mais usuários, imóveis e hábitos para enriquecer o grafo |
| `querys/querys.cypher` | Queries de visualização e análise de negócio |
| `querys/transversal.cypher` | Query transversal da pergunta de negócio principal |
| `load_graph.py` | Executa qualquer `.cypher` no Aura via Python |

---

## 4. Como executar

```bash
pip install neo4j python-dotenv

# Carregar o modelo base
python load_graph.py setup.cypher

# Adicionar dados adicionais
python load_graph.py seed.cypher
```

As variáveis de ambiente ficam em `.env` (não versionado — ver `.env.example`):

```
NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io
NEO4J_USER=<instance-id>
NEO4J_PASSWORD=<senha-gerada-pelo-aura>
NEO4J_DATABASE=<instance-id>
```

---

## 5. Queries de negócio

### Q1 — Visualizar todo o grafo
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
```

### Q2 — Usuário, imóvel, região e dispositivo
```cypher
MATCH (u:User)-[o:OWNS]->(p:Property)
OPTIONAL MATCH (p)-[l:LOCATED_AT]->(a:Address)-[ir:IN_REGION]->(r:Region)
OPTIONAL MATCH (p)-[d:HAS_DEVICE]->(device:Device)
RETURN u, o, p, l, a, ir, r, d, device;
```

### Q3 — Faturas e tarifa por região
```cypher
MATCH (u:User)-[hb:HAS_BILL]->(b:WaterBill)
MATCH (u)-[:OWNS]->(:Property)-[:LOCATED_AT]->(:Address)-[ir:IN_REGION]->(r:Region)-[hr:HAS_RATE]->(rr:RegionRate)
RETURN u, hb, b, ir, r, hr, rr;
```

### Q4 — Hábitos por usuário e dia
```cypher
MATCH (u:User)-[hh:HAS_HABIT]->(uh:UserHabit)-[ih:IS_HABIT]->(h:Habit)
OPTIONAL MATCH (uh)-[od:ON_DAY]->(d:Day)
RETURN u, hh, uh, ih, h, od, d;
```

### Q5 — Todos os usuários via label `:Pessoa` (multi-label)
```cypher
MATCH (p:Pessoa)
RETURN p.name AS nome, p.email AS email, p.registrationDate AS cadastro;
```

### Q6 — Imóveis por tipo (multi-label)
```cypher
MATCH (p:Casa) RETURN p.name AS imovel, "Casa" AS tipo
UNION
MATCH (p:Predio) RETURN p.name AS imovel, "Prédio" AS tipo;
```

### Q7 — Consumo consolidado por região com UNWIND
```cypher
MATCH (r:Region)-[:HAS_RATE]->(rr:RegionRate)
MATCH (a:Address)-[:IN_REGION]->(r)
MATCH (prop:Property)-[:LOCATED_AT]->(a)
MATCH (u:User)-[:OWNS]->(prop)
MATCH (u)-[:HAS_BILL]->(b:WaterBill)
WITH r.name AS regiao, rr.m3Value AS tarifaM3, COLLECT(b.totalValue) AS faturas
UNWIND faturas AS valorFatura
RETURN regiao, tarifaM3, SUM(valorFatura) AS totalConsumo, COUNT(valorFatura) AS qtdFaturas
ORDER BY totalConsumo DESC;
```

### Q8 — Traversal: hábitos mais frequentes por região
```cypher
MATCH (u:User)-[:OWNS]->(p:Property)-[:LOCATED_AT]->(a:Address)-[:IN_REGION]->(r:Region)
MATCH (u)-[:HAS_HABIT]->(uh:UserHabit)-[:IS_HABIT]->(h:Habit)
RETURN r.name AS regiao, h.name AS habito, SUM(uh.frequency) AS frequenciaTotal
ORDER BY regiao, frequenciaTotal DESC;
```

### Q9 — Pergunta de negócio transversal
> Quais usuários praticam hábitos aos sábados e moram em regiões com tarifa superior a R$ 8,00/m³?

```cypher
MATCH (u:User)-[:HAS_HABIT]->(uh:UserHabit)-[:ON_DAY]->(d:Day {name: "SÁBADO"})
MATCH (uh)-[:IS_HABIT]->(h:Habit)
MATCH (u)-[:OWNS]->(:Property)-[:LOCATED_AT]->(:Address)-[:IN_REGION]->(r:Region)-[:HAS_RATE]->(rr:RegionRate)
WHERE rr.m3Value > 8.00
RETURN u.name AS usuario, h.name AS habito, r.name AS regiao, rr.m3Value AS tarifa;
```

---

## 6. Repositório

`repo-neo4j/delta-neo4j/` — branch principal: `main`
