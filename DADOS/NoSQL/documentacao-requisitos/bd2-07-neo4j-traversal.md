### BD2-07 — Responder pelo menos uma pergunta de negócio que exija traversal, não uma simples busca por nó

**Evidência direta:**

- [Query transversal da pergunta de negócio](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/querys/transversal.cypher)
- [Resultado da query transversal (`transversal.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/transversal.png)
- [Demais queries de negócio](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/querys/querys.cypher)
- [Hábitos por usuário e dia (`query4.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query4.png)
- [Faturas e tarifa por região (`query3.png`)](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/query3.png)
- [Documentação das queries](../modelagem-neo4j.md)

**Localização e como comprovar:**

#### 1. A pergunta de negócio

> Quais usuários praticam hábitos aos sábados e moram em regiões com tarifa de água superior a R$ 8,00 por m³?

A resposta ajuda a identificar quem tem hábitos de consumo no fim de semana e paga a tarifa mais cara, que é o público em que uma dica de economia rende mais.

#### 2. A consulta

```cypher
MATCH (u:User)-[:HAS_HABIT]->(uh:UserHabit)-[:ON_DAY]->(d:Day {name: "SÁBADO"})
MATCH (uh)-[:IS_HABIT]->(h:Habit)
MATCH (u)-[:OWNS]->(:Property)-[:LOCATED_AT]->(:Address)-[:IN_REGION]->(r:Region)-[:HAS_RATE]->(rr:RegionRate)
WHERE rr.m3Value > 8.00
RETURN DISTINCT
    u.name AS usuario,
    h.name AS habito,
    r.name AS regiao,
    rr.m3Value AS tarifa;
```

#### 3. Por que exige traversal

Não existe um nó que contenha a resposta. A consulta percorre dois caminhos que se encontram no usuário:

```
User -[HAS_HABIT]-> UserHabit -[ON_DAY]-> Day {SÁBADO}
                    UserHabit -[IS_HABIT]-> Habit
User -[OWNS]-> Property -[LOCATED_AT]-> Address -[IN_REGION]-> Region -[HAS_RATE]-> RegionRate
```

Ela cruza hábito, dia, imóvel, endereço, região e tarifa. Em SQL, isso seria uma sequência de `JOIN`s entre cerca de oito tabelas.

#### 4. Resultado obtido

![Resultado da query transversal no Neo4j](https://github.com/delta-app-ofc/delta-neo4j-database/blob/main/diagrams/transversal.png?raw=true)

| usuario | habito | regiao | tarifa |
|---|---|---|---|
| Carlos | LAVAR CARRO | OESTE | 8.8 |
| Beatriz | BANHO LONGO | NORTE | 9.1 |
| Lucas | LAVAR QUINTAL | SUL | 8.5 |
| Julia | LAVAR LOUÇA | CENTRO | 8.2 |
| Ana | LAVAR CARRO | CENTRO | 8.2 |

Os resultados estão de acordo com os dados carregados:

- **João** tem um hábito no sábado, mas mora na região LESTE, de tarifa 7,90. O filtro de tarifa o exclui.
- **Mariana** não tem hábito registrado no sábado. O filtro de dia a exclui.

As imagens `query3.png` e `query4.png` mostram as partes do grafo que a consulta cruza: as tarifas por região e os hábitos por dia.

#### 5. Outra consulta de traversal

A Q8 de `querys.cypher` soma a frequência dos hábitos por região, percorrendo usuário, imóvel, endereço e região e, em paralelo, usuário, hábito do usuário e hábito:

```cypher
MATCH (u:User)-[:OWNS]->(p:Property)-[:LOCATED_AT]->(a:Address)-[:IN_REGION]->(r:Region)
MATCH (u)-[:HAS_HABIT]->(uh:UserHabit)-[:IS_HABIT]->(h:Habit)
RETURN r.name AS regiao, h.name AS habito, SUM(uh.frequency) AS frequenciaTotal
ORDER BY regiao, frequenciaTotal DESC;
```

#### 6. Como comprovar

1. Carregar o grafo com `setup.cypher` e `seed.cypher`.
2. Executar a consulta acima no Neo4j Browser.
3. Conferir as cinco linhas da tabela e a ausência de João e Mariana.

#### 7. Divergências conhecidas

- A versão da consulta no `README` do repositório do Neo4j não tem `DISTINCT`, e a de `transversal.cypher` tem. Com os dados atuais, o resultado é o mesmo.
- A Q7 de `querys.cypher` usa `ORDER BY totalConsumo`, mas o alias projetado é `totalConsumoM3`. Essa consulta deve falhar e não é usada como evidência.
