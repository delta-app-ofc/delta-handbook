# 🏗️ Arquitetura de Dados — Projeto Delta

Este documento descreve a arquitetura de dados do Projeto Delta, explicando o papel de cada banco de dados utilizado na solução e como eles se integram dentro do sistema de monitoramento inteligente de consumo de água.

O sistema adota uma arquitetura multi-banco para atender diferentes necessidades: transacional, analítica, tempo real, dados massivos e relações complexas.

---

# PostgreSQL — Banco Relacional

## Papel no sistema

O PostgreSQL é o **banco principal do sistema**, responsável por armazenar todos os dados estruturados, normalizados e essenciais para o funcionamento da aplicação.

---

## 📌 Responsabilidades

O PostgreSQL armazena:

- tbl_usuario;
- tbl_instalacao;
- tbl_usuario_instalacao;
- tbl_dispositivo
- tbl_meta_consumo;
- tbl_alerta;
- tbl_tarifa_agua;
- tbl_habito;
- tbl_usuario_habito;
- views analíticas;
- triggers, functions, procedures e tabelas de auditoria das respectivas tabelas.

Ou seja, dados dos usuários, estrutura física e regras de negócio, representando o CORE do Sistema, além das VIEWS analíticas, usadas para camada de BI.

---

## Finalidade

O PostgreSQL garante:
- Integridade dos dados
- Relacionamentos (PK/FK)
- Consistência transacional
- Base oficial do sistema

---

# MongoDB — Dados Não Estruturados 

## Papel no sistema

O MongoDB é responsável pelo armazenamento de **dados massivos e não estruturados gerados pelos dispositivos IoT**.

---

## 📌 Responsabilidades

O MongoDB armazena:

### 📟 Dados de sensores (ESP32)
- device_id
- timestamp
- pulsos do hidrômetro
- vazão instantânea
- consumo em tempo real

### 📊 Eventos do sistema
- detecção de vazamentos
- picos de consumo
- logs de comunicação
- dados de integração com APIs externas (ex: clima)

---

## Uso obrigatório no sistema

- Base de consultas do chatbot
- Agregações de consumo em tempo real
- Histórico bruto de leituras

---

##  Finalidade

O MongoDB garante:
- Alta escalabilidade
- Armazenamento de dados em grande volume
- Flexibilidade de schema
- Histórico detalhado de eventos IoT

---

#  Redis — Cache, Ranking e Tempo Real

## Papel no sistema

O Redis é responsável por **processamento em memória**, garantindo respostas rápidas e operações em tempo real.

---

## 📌 Responsabilidades

###  Ranking em tempo real
- Usuários com menor consumo
- Ranking diário, semanal e mensal
- Comparação entre instalações

### Cache de dashboard
- Consumo atual
- Últimos 5/10/15 minutos
- Métricas temporárias

###  Filas de processamento
- Atualização de alertas
- Processamento de métricas
- Atualização de rankings

---

## Finalidade

O Redis garante:
- Alta performance
- Baixa latência
- Processamento em tempo real
- Otimização de consultas frequentes

---

#  Neo4j — Banco de Grafos 

## Papel no sistema

O Neo4j é utilizado para modelar o sistema como uma **rede de relações entre usuários, hábitos, dispositivos e consumo**.

---

## 📌 Modelagem em grafo

### Entidades principais:
- Usuários
- Instalações
- Dispositivos
- Consumo
- Alertas
- Hábitos

---

## 🔗 Exemplo de relacionamentos

- (Usuário)-[:POSSUI]->(Instalação)
- (Instalação)-[:TEM]->(Dispositivo)
- (Dispositivo)-[:GERA]->(Consumo)
- (Consumo)-[:DISPARA]->(Alerta)
- (Usuário)-[:POSSUI_HABITO]->(Hábito)

---

## 🔍 Exemplo de pergunta de negócio (Traversal)

> Quais usuários que possuem piscina tiveram alertas de consumo alto associados a dispositivos com comportamento anômalo?

Esse tipo de consulta exige navegação profunda no grafo, o que não é eficiente em bancos relacionais.

---

## Finalidade

O Neo4j garante:
- Análise de relacionamentos complexos
- Detecção de padrões de comportamento
- Consultas multi-nível (traversal)
- Inteligência baseada em conexões

---

# 🧠 Visão Geral da Arquitetura

| Banco | Função Principal |
|------|----------------|
|  PostgreSQL | Dados estruturados, regras de negócio e integridade |
|  MongoDB | Dados IoT e eventos em grande volume |
|  Redis | Tempo real, cache e ranking |
|  Neo4j | Relações complexas e análise de comportamento |

---

# 🚀 Conclusão

O Projeto Delta utiliza uma arquitetura multi-banco para garantir escalabilidade, desempenho e inteligência analítica.

Cada banco de dados possui uma responsabilidade bem definida.Essa arquitetura possibilita monitoramento avançado, previsão de consumo e detecção inteligente de desperdícios.