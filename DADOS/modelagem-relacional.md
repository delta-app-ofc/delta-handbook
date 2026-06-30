# 📊 Modelagem de Dados - PostgreSQL (Projeto Delta)

Este documento descreve a modelagem relacional do banco de dados PostgreSQL do Projeto Delta, responsável por armazenar informações de usuários, imóveis, dispositivos IoT, hábitos de consumo e regras regionais de tarifação de água.

🔗 Repositório: https://github.com/delta-app-ofc/delta-database

---

## 🌎 1. Tabela: `tb_region`

Armazena as regiões utilizadas para cálculo de tarifas.

### 📌 Atributos
- **id (PK)**: Identificador da região.
- **name**: Nome da região.
  - Valores permitidos: `LESTE`, `OESTE`, `SUL`, `NORTE`, `CENTRO`

---

## 📅 2. Tabela: `tb_day_of_week`

Define os dias da semana utilizados na associação de hábitos.

### 📌 Atributos
- **id (PK)**: Identificador do dia da semana.
- **name**: Nome do dia.
  - Valores permitidos: `SEGUNDA`, `TERÇA`, `QUARTA`, `QUINTA`, `SEXTA`, `SÁBADO`, `DOMINGO`

---

## 🧠 3. Tabela: `tb_habit`

Armazena os tipos de hábitos de consumo de água.

### 📌 Atributos
- **id (PK)**: Identificador do hábito.
- **name**: Nome do hábito.
  - Valores permitidos: `BANHO LONGO`, `LAVAR QUINTAL`, `LAVAR ROUPA`, `REGAR PLANTAS`, `LAVAR CARRO`, `LAVAR LOUÇA`
- **description**: Descrição opcional do hábito.

---

## 📍 4. Tabela: `tb_address`

Armazena os endereços dos imóveis cadastrados.

### 📌 Atributos
- **id (PK)**: Identificador do endereço.
- **region_id (FK)**: Referência para `tb_region`.
- **cep**: CEP (8 dígitos numéricos).
- **city**: Cidade.
- **state**: Estado.

---

## 👤 5. Tabela: `tb_user`

Armazena os usuários do sistema.

### 📌 Atributos
- **id (PK)**: Identificador do usuário.
- **name**: Nome completo.
- **email**: E-mail (único).
- **password**: Senha criptografada.
- **phone**: Telefone.
- **birth_date**: Data de nascimento.
- **registration_date**: Data de cadastro (padrão: CURRENT_DATE).
- **is_active**: Indica se o usuário está ativo.
- **is_admin**: Indica se o usuário é administrador.

---

## 🏠 6. Tabela: `tb_property`

Representa os imóveis cadastrados no sistema.

### 📌 Atributos
- **id (PK)**: Identificador do imóvel.
- **name**: Nome do imóvel.
- **type**: Tipo do imóvel (`CASA`, `PRÉDIO`).
- **classification**: Classificação (`RESIDENCIAL`, `COMERCIAL`).
- **address_id (FK)**: Referência para `tb_address`.
- **registration_date**: Data de cadastro.

---

## 🔗 7. Tabela: `tb_user_property`

Tabela de relacionamento N:N entre usuários e imóveis.

### 📌 Atributos
- **id (PK)**: Identificador do relacionamento.
- **user_id (FK)**: Referência para `tb_user`.
- **property_id (FK)**: Referência para `tb_property`.
- **association_date**: Data de vinculação.


---

## 📟 8. Tabela: `tb_device`

Armazena os dispositivos IoT instalados nos imóveis.

### 📌 Atributos
- **id (PK)**: Identificador interno.
- **device_id**: Identificador físico do dispositivo (único).
- **property_id (FK)**: Referência para `tb_property`.
- **is_active**: Status do dispositivo (ativo/inativo).
- **installation_date**: Data de instalação.

---

## 💧 9. Tabela: `tb_region_rate`

Define tarifas de água por região e faixa de consumo.

### 📌 Atributos
- **id (PK)**: Identificador da tarifa.
- **region_id (FK)**: Referência para `tb_region`.
- **initial_range**: Início da faixa de consumo (>= 0).
- **final_range**: Fim da faixa de consumo (> inicial).
- **m3_value**: Valor por m³ (> 0).
- **initial_validity**: Início da vigência.
- **final_validity**: Fim da vigência (pode ser NULL).

---

## 👥 10. Tabela: `tb_user_habit`

Relaciona usuários aos seus hábitos de consumo.

### 📌 Atributos
- **id (PK)**: Identificador.
- **user_id (FK)**: Referência para `tb_user`.
- **habit_id (FK)**: Referência para `tb_habit`.
- **frequency**: Frequência do hábito (> 0).


---

## 📆 11. Tabela: `tb_user_habit_day`

Define em quais dias da semana cada hábito ocorre.

### 📌 Atributos
- **id (PK)**: Identificador.
- **user_habit_id (FK)**: Referência para `tb_user_habit`.
- **day_of_week_id (FK)**: Referência para `tb_day_of_week`.