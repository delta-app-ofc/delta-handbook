# Modelagem de Dados - PostgreSQL
Este documento descreve todas as tabelas do banco de dados relacional PostgreSQL do Projeto Delta, responsável por armazenar os dados transacionais principais do sistema de monitoramento inteligente de consumo de água.

Para visualizar os códigos, acesse: https://github.com/delta-app-ofc/delta-database



## 👤 1. Tabela: tbl_usuario
Armazena os dados dos usuários do sistema.

### 📌 Atributos
- **id (PK)**: Identificador único do usuário.
- **nome**: Nome completo do usuário.
- **email**: E-mail utilizado para login e comunicação.
- **senha**: Senha criptografada do usuário.
- **telefone**: Número de contato.
- **data_nascimento**: Data de nascimento do usuário.
- **data_cadastro**: Data de criação da conta no sistema.
- **ativo**: Campo boleano que índica que o usuário está ou não ativo.

---

## 🏠 2. Tabela: tbl_instalacao

Representa os imóveis onde foram instalados os dispositivos que são monitorados pelo sistema.

### 📌 Atributos

- **id (PK)**: Identificador único da instalação.
- **nome_identificador**: Nome personalizado da instalação (ex: "Casa Centro", "Swift da Leopoldina").
- **tipo_classificacao**: Tipo de uso (residencial ou comercial).
- **tipo_imovel**: Tipo do imóvel (casa, apartamento, etc.).
- **percentual_consumo**: Percentual estimado de consumo associado à instalação.
- **cep**: Código postal do imóvel.
- **cidade**: Cidade onde a instalação está localizada.
- **estado**: Estado da instalação.
- **data_cadastro**: Data de registro da instalação no sistema.

---

## 🔗 3. Tabela: tbl_usuario_instalacao

Tabela de relacionamento N:N entre usuários e instalações.

### 📌 Atributos
- **id**: Identificados da tabela de relacionamento N:N entre usuários e instalações.
- **id_usuario (FK)**: Referência ao usuário.
- **id_instalacao (FK)**: Referência à instalação.
- **data_vinculo**: Data em que o usuário foi vinculado à instalação.

---

## 📟 4. Tabela: tbl_dispositivo

Armazena os dispositivos IoT (ESP32) instalados nas residências.

### 📌 Atributos

- **id (PK)**: Identificador interno do dispositivo.
- **device_id**: Identificador físico do dispositivo (ex: ESP32_001).
- **id_instalacao (FK)**: Instalação onde o dispositivo está instalado.
- **ativo**: Campo boleano que índica que o dispositivo está ou não ativo.
- **data_instalacao**: Data de instalação do dispositivo.
- **ultima_comunicacao**: Última vez que o dispositivo enviou dados.

---

##  🎯 5. Tabela: tbl_meta_consumo

Define metas de consumo de água para cada instalação.

### 📌 Atributos

- **id (PK)**: Identificador da meta.
- **id_instalacao (FK)**: Instalação associada.
- **limite_diario_litros**: Limite diário de consumo permitido.
- **limite_mensal_litros**: Limite mensal de consumo permitido.
- **data_inicio**: Início da vigência da meta.
- **data_fim**: Fim da vigência da meta.

---

## 🚨 6. Tabela: tbl_alerta

Armazena os alertas ativos gerados pelo sistema.

### 📌 Atributos

- **id (PK)**: Identificador do alerta.
- **id_instalacao (FK)**: Instalação onde o alerta foi gerado.
- **tipo**: Tipo do alerta (ex: vazamento, consumo alto).
- **mensagem**: Descrição do alerta.
- **status**: Situação do alerta (ativo, resolvido).
- **data_criacao**: Data de criação do alerta.
- **data_resolucao**: Data em que o alerta foi resolvido.

---

## 💰 7. Tabela: tbl_tarifa_agua

Tabela responsável pela definição de tarifas de água por cidade.

### 📌 Atributos

- **id (PK)**: Identificador da tarifa.
- **cidade**: Cidade de aplicação da tarifa.
- **faixa_inicial**: Início da faixa de consumo (m³).
- **faixa_final**: Fim da faixa de consumo (m³).
- **valor_m3**: Valor cobrado por metro cúbico.
- **vigencia_inicio**: Início da validade da tarifa.
- **vigencia_fim**: Fim da validade da tarifa.

---

## 🧠 8. Tabela: tbl_habito

Tabela responsável por armazenar os tipos de hábitos de consumo de água do sistema.  

### 📌 Atributos

- **id (PK)**: Identificador do hábito.
- **codigo**: Código técnico do hábito (ex: JARDIM, PISCINA, LAVAGEM_ALTA).
- **descricao**: Descrição textual do hábito (ex: "Possui jardim", "Uso frequente de máquina de lavar").

---

## 🔗 9. Tabela: tbl_usuario_habito

Tabela de relacionamento **N:N entre usuários e hábitos**, permitindo que um usuário possua vários hábitos e um hábito pertença a vários usuários


### 📌 Atributos

- **id (PK)**: Identificador do relacionamento.
- **id_usuario (FK)**: Referência ao usuário.
- **id_habito (FK)**: Referência ao hábito.
- **data_vinculo**: Data em que o hábito foi associado ao usuário.

---