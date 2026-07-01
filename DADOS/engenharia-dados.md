# 🏗️ Engenharia de Dados — Projeto Delta

Este documento descreve a engenharia de dados do Projeto Delta, explicando o papel de cada banco de dados utilizado na solução e como eles se integram dentro do sistema de monitoramento inteligente de consumo de água.

O sistema adota uma arquitetura multi-banco para atender diferentes necessidades: transacional, analítica, tempo real, dados massivos e relações complexas.

---

# PostgreSQL — Banco Relacional

## Papel no sistema

O PostgreSQL é o **banco de dados principal do sistema**, responsável por armazenar todos os **dados cadastrais, estruturais e transacionais essenciais** para o funcionamento da aplicação.

---

## Responsabilidades

O PostgreSQL armazena principalmente **dados cadastrais do sistema**, incluindo:

- tb_user 
- tb_property 
- tb_address 
- tb_device 
- tb_region 
- tb_habit 
- tb_user_property 
- tb_user_habit 
- tb_user_habit_day 
- tb_region_rate 

Além disso, também armazena:

- Views analíticas (camada de BI)
- Functions, triggers e procedures (regras de negócio no banco)
- Tabelas auxiliares de suporte e histórico, quando aplicável

---

## Uso obrigatório

O banco é responsável por:

- **Dados cadastrais (core do sistema)**  
  Ex: usuários, imóveis, dispositivos, regiões

- **Dados relacionais**  
  Ex: vínculos entre usuário e imóvel, usuário e hábito

- **Dados analíticos (BI)**  
  Ex: views para relatórios e dashboards

---

##  Finalidade

O PostgreSQL garante:

- Integridade dos dados
- Consistência transacional (ACID)
- Relacionamentos via PK/FK
- Padronização dos dados cadastrais

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