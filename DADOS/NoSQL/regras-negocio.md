# 📘 Regras de Negócio — Projeto Delta (MongoDB)

Este documento descreve todas as regras de negócio do banco de dados não relacional MongoDB do Projeto Delta.

---

## 1. 🔤 Padrão de letras nos registros

Todos os **dados inseridos no banco devem ser armazenados em MAIÚSCULAS**, quando aplicável.

✔ Exemplos:
- status → "ONLINE"
- severidade → "ALTA"

---

## 2. 🌐 Padrão de idioma

- Todos os **objetos do banco de dados devem estar em INGLÊS**
- Isso inclui:
  - collections
  - campos
  - indexes

---

## 3. 🔡 Padrão de acentuação

- Os **registros podem conter acentuação normalmente**
- Já os **objetos do banco NÃO devem conter acentos**

---

## 4. 🏷️ Padrões de Nomenclatura NoSQL

---

### 4.1 📂 Databases
Padrão: **lower_snake_case** com o prefixo `db_delta_` para identificar claramente o ambiente dentro do cluster.

✔ Exemplos:
db_delta_telemetry
db_delta_app

---

### 4.2 📦 Coleções (Collections)
No MongoDB, o padrão mais adotado pelo mercado e pela própria equipe do Mongo é o **lower_snake_case** no plural (ou indicando o tipo de histórico), 
dispensando o uso de prefixos como tb_, já que o contexto de documento é implícito.

✔ Exemplos:

pulses_raw
consumption_summary
client_preferences
chat_sessions

---

### 4.3 🆔 Nomenclatura de PKs
- Todas as **Primary Keys (PKs)** das collections seguem o padrão de ObjectId do MongoDB
- As PKs em todas as collections são o _id para padronização

---

### 4.4 🔑 Campos (Fields/Properties) dentro do JSON
Padrão: **lower_snake_case** para todas as chaves do documento JSON.

✔ Exemplos:
device_id
window_started_at
anomaly_detected

---

## 5. 🏷️ Prefixos utilizados no projeto

---

### 5.1 🔑 Prefixo de Indexes Simples e Compostos

- Prefixo: `idx_`
- Formato:
    idx_<collection>_<campo1>_<campo2>_..._<campoN>

✔ Exemplos:
idx_client_preferences_user_id

---

### 5.2 🔒 Sufixo de Indexes Únicos
- Prefixo: `idx_`
- Sufixo: `_uq`
- Formato:
    idx_<collection>_<campo>_uq

✔ Exemplos:
idx_client_preferences_user_id_uq

---

### 5.3 ⏳ Prefixo de Indexes de Expiração Automática
- Sufixo: `ttl_`
- Formato:
    ttl_<collection>_<campo_data>

✔ Exemplos:
ttl_pulses_raw_sent_at

---

### 🔒 5.4 Prefixo de Roles

Todas as roles seguem o prefixo: role_
✔ Exemplos:
role_devops  
role_analyst  

---