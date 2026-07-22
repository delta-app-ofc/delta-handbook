Aqui está a documentação completa da **Governança de Acesso do MongoDB**, estruturada exatamente no mesmo padrão e formatação do seu arquivo do PostgreSQL (`governanca-acesso.md`), considerando os scripts de roles dos dois clusters.

---

# Governança de Acesso (MongoDB NoSQL) — Projeto Delta

Este documento define as *Custom Roles* e permissões dos bancos NoSQL (MongoDB Atlas) do Projeto Delta, divididos entre o **Cluster de Telemetria** e o **Cluster do Aplicativo**.

---

## Estruturas Consideradas

Coleções atualmente planejadas e implementadas nos schemas dos clusters NoSQL:

### Cluster 1: Telemetria (`db_delta_telemetry`)

* `pulses_raw`
* `consumption_summary`
* `device_status`

### Cluster 2: Aplicativo (`db_delta_app`)

* `client_preferences`
* `chat_history`
* `user_notifications`
* `chat_feedback`

> **Nota de Arquitetura:** No MongoDB, todas as Custom Roles são registradas centralmente no banco `admin`, porém seus privilégios (escopo de atuação) aplicam-se especificamente às coleções de cada banco de dados (`db_delta_telemetry` ou `db_delta_app`).

---

# 1. Definição das Roles por Cluster

## Cluster 1: Telemetria (`db_delta_telemetry`)

### `role_api_service`

Permissões:

* Gravação de dados brutos de sensores (ESP32) e cálculo/atualização de resumos
* `find`, `insert`, `update` em todas as coleções do banco `db_delta_telemetry`
* Sem permissão de exclusão (`delete`) nem alteração estrutural de índices

---

### `role_bi_analyst`

Permissões:

* Acesso exclusivo e restrito à coleção `consumption_summary`
* `find` e `createIndex` na coleção `consumption_summary`
* Sem acesso às coleções de dados brutos (`pulses_raw`, `device_status`, etc.) ou escrita de dados

---

### `role_dev_backend`

Permissões:

* Leitura para diagnóstico, depuração e auditoria de telemetria
* `find` em todas as coleções do banco `db_delta_telemetry`
* Sem permissões de escrita (`insert`, `update`, `delete`) ou gestão de índices

---

### `role_devops_engineer`

Permissões:

* Gestão de infraestrutura, performance e monitoramento do cluster
* `find`, `createIndex`, `dropIndex`, `collMod`, `dbStats`, `collStats` em todas as coleções do banco `db_delta_telemetry`
* Sem permissão de alteração/exclusão direta de dados de negócio

---

### `role_data_engineer`

Permissões:

* Administração total da estrutura de dados do cluster de telemetria
* `find`, `insert`, `update`, `delete`, `createIndex`, `dropIndex`, `dropCollection`, `collMod`, `dbStats`, `collStats` em todas as coleções do banco `db_delta_telemetry`
* Controle estrutural e operacional completo sobre a base NoSQL de telemetria

---

## Cluster 2: Aplicativo (`db_delta_app`)

### `role_api_service`

Permissões:

* CRUD completo do Back-end do aplicativo e assistente virtual
* `find`, `insert`, `update`, `delete` em todas as coleções do banco `db_delta_app`
* Sem permissão de alteração de índices ou remoção de coleções (`dropCollection`)

---

### `role_bi_analyst`

Permissões:

* Acesso exclusivo e restrito à coleção `alerts_history`
* `find` e `createIndex` na coleção `alerts_history`
* Sem acesso às outras coleções do database (`client_preferences`, `chat_history`, `chat_feedback`.) ou escrita de dados

---

### `role_dev_backend`

Permissões:

* Leitura para depuração de chats, preferências e notificações
* `find` em todas as coleções do banco `db_delta_app`
* Sem permissões de escrita (`insert`, `update`, `delete`) ou alteração de índices

---

### `role_devops_engineer`

Permissões:

* Gestão de infraestrutura, índices e políticas de TTL (Time-To-Live) dos chats
* `find`, `createIndex`, `dropIndex`, `collMod`, `dbStats`, `collStats` em todas as coleções do banco `db_delta_app`
* Sem permissão de alteração/exclusão de dados de aplicação

---

### `role_data_engineer`

Permissões:

* Administração total da estrutura de dados do cluster do aplicativo
* `find`, `insert`, `update`, `delete`, `createIndex`, `dropIndex`, `dropCollection`, `collMod`, `dbStats`, `collStats` em todas as coleções do banco `db_delta_app`
* Controle estrutural e operacional completo sobre a base NoSQL do app

---

# 2. Atribuição de Usuários às Roles do MongoDB

OBSERVAÇÃO: Integrantes com a role `role_data_engineer` possuem acesso completo a todas as coleções de ambos os clusters, por isso só tem essa role atribuída

| Integrante                  | Disciplinas                   | Roles Atribuídas (Telemetria)                                   | Roles Atribuídas (App)                                           |
|-----------------------------|-------------------------------|-----------------------------------------------------------------|------------------------------------------------------------------|
| **Ana**                     | UX, DAD, BI, EQS              | `role_bi_analyst`                                               | `role_bi_analyst`                                                |
| **Davi**                    | Mobile, DAD, DS2, EQS         | `role_dev_backend`                                              | `role_dev_backend`                                               |
| **João**                    | Mobile, DS2, IA, EQS          | `role_dev_backend`                                              | `role_dev_backend`                                               |
| **Mariana**                 | MDD, BD2, DS2, IA, EQS        | `role_data_engineer`, `role_dev_backend`                        | `role_data_engineer`, `role_dev_backend`                         |
| **Rahquel**                 | Mobile, DAD, UX, EQS          | `role_dev_backend`                                              | `role_dev_backend`                                               |
| **Samuel**                  | BI, DevOps, BD2, IA, MDD, EQS | `role_data_engineer`, `role_devops_engineer`, `role_bi_analyst` | `role_data_engineer`, `role_devops_engineer`, `role_bi_analyst`  |
| **Service Accounts (APIs)** | Aplicação / Ingestão          | `role_api_service`                                              | `role_api_service`                                               |