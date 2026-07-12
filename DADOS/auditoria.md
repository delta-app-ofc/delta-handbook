# 📘 Documentação da Auditoria de Tabelas PostgreSQL

## Objetivo

O sistema de auditoria foi desenvolvido com o objetivo de garantir a rastreabilidade das operações realizadas no banco de dados, permitindo identificar:

- qual registro foi afetado;
- qual operação foi executada;
- qual usuário realizou a alteração;
- quando a alteração ocorreu;
- quais dados foram modificados.

A auditoria permite manter um histórico completo das alterações realizadas nas tabelas principais do sistema, auxiliando no controle das informações, análise de alterações e acompanhamento das ações realizadas no banco de dados.

São registradas as seguintes operações:

- **INSERT**: inclusão de novos registros;
- **UPDATE**: alteração de registros existentes;
- **DELETE**: remoção de registros.

---

# Funcionamento Geral

Cada tabela principal do sistema possui uma tabela de auditoria correspondente.

Exemplo:

| Tabela Principal | Tabela de Auditoria |
|------------------|---------------------|
| tb_region | tb_log_region |
| tb_day_of_week | tb_log_day_of_week |
| tb_habit | tb_log_habit |
| tb_address | tb_log_address |
| tb_user | tb_log_user |
| tb_property | tb_log_property |
| tb_user_property | tb_log_user_property |
| tb_device | tb_log_device |
| tb_region_rate | tb_log_region_rate |
| tb_user_habit | tb_log_user_habit |
| tb_user_habit_day | tb_log_user_habit_day |
| tb_last_water_bill | tb_log_last_water_bill |

O processo de auditoria funciona através da integração entre tabelas, triggers e functions.

---

# Estrutura das Tabelas de Auditoria

Todas as tabelas de auditoria seguem um padrão de organização.

Cada tabela possui:

- identificador próprio do log;
- informações da operação realizada;
- usuário responsável;
- data e hora da execução;
- dados do registro original;
- referência ao log anterior;
- descrição da alteração.

Exemplo:

```sql
CREATE TABLE tb_log_region (

      id                      SERIAL PRIMARY KEY

    , operation               VARCHAR(10) NOT NULL

    , executed_by             VARCHAR(100) NOT NULL

    , executed_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP

    , region_id               INTEGER

    , name                    VARCHAR(20)

    , previous_log_id         INTEGER

    , log_description         TEXT

);
```

---

# Informações Registradas

Cada registro de auditoria armazena as seguintes informações:

| Campo | Descrição |
|-------|-----------|
| id | Identificador único do registro de auditoria |
| operation | Tipo da operação realizada: INSERT, UPDATE ou DELETE |
| executed_by | Usuário responsável pela execução utilizando `CURRENT_USER` |
| executed_at | Data e hora da operação utilizando `CURRENT_TIMESTAMP` |
| identificador do registro | ID do registro original alterado |
| demais campos | Cópia dos valores existentes no registro auditado |
| previous_log_id | Referência ao registro de auditoria anterior |
| log_description | Descrição detalhada das alterações realizadas |

---

# Controle Histórico com previous_log_id

O campo `previous_log_id` é utilizado para manter a sequência histórica das alterações de um mesmo registro.

Exemplo:

```
Registro original
      |
      |
INSERT
      |
      v
tb_log_region
id = 1


UPDATE
      |
      v
tb_log_region
id = 2
previous_log_id = 1


DELETE
      |
      v
tb_log_region
id = 3
previous_log_id = 2
```

Esse relacionamento permite acompanhar toda a evolução de um registro desde sua criação até sua remoção.

---

# Funcionamento das Functions

Cada tabela auditada possui uma Function específica responsável pelo registro das alterações.

Exemplos:

```
fn_log_region()

fn_log_user()

```

---

# Auditoria de INSERT

Quando um novo registro é inserido:

- `TG_OP` recebe o valor **INSERT**;
- `CURRENT_USER` identifica o usuário conectado ao banco;
- `CURRENT_TIMESTAMP` registra a data e hora da operação;
- `NEW` contém os valores do novo registro.

A Function utiliza os valores presentes em `NEW` para inserir uma cópia dos dados na tabela de auditoria.

Exemplo:

```
Registro inserido na tabela tb_region.
```

---

# Auditoria de UPDATE

Quando um registro existente é atualizado:

- `TG_OP` recebe o valor **UPDATE**;
- `CURRENT_USER` identifica o usuário responsável;
- `CURRENT_TIMESTAMP` registra o momento da alteração;
- `OLD` contém os valores antes da alteração;
- `NEW` contém os valores após a alteração.

Para identificar quais campos foram modificados, é utilizada uma comparação dinâmica entre os valores antigos e novos.

A comparação utiliza:

```sql
json_each_text(row_to_json(OLD))
```

Esse recurso permite percorrer automaticamente todos os campos do registro anterior, evitando a necessidade de criar comparações individuais para cada coluna.

A lógica realizada é:

1. Percorrer todos os campos existentes no `OLD`;
2. Buscar o valor correspondente no `NEW`;
3. Comparar os valores antigos e novos;
4. Registrar somente os campos que sofreram alteração.

Exemplo:

```
Registro atualizado na tabela tb_habit. Campos alterados:

- Campo: description
  Valor antigo: "Consumo elevado de água durante o banho"
  Valor novo: "Banho com duração acima do recomendado"
```

---

# Auditoria de DELETE

Quando um registro é removido:

- `TG_OP` recebe o valor **DELETE**;
- `CURRENT_USER` identifica o usuário responsável;
- `CURRENT_TIMESTAMP` registra o momento da exclusão;
- `OLD` contém os valores existentes antes da remoção.

Como após a exclusão o registro deixa de existir na tabela principal, os dados são obtidos através do `OLD`.

A Function utiliza esses valores para armazenar o histórico do registro removido.

Exemplo:

```
Registro removido da tabela tb_property.
```

---

# Funcionamento das Triggers

Cada tabela possui uma Trigger responsável por executar automaticamente a Function de auditoria.

Exemplo:

```sql
CREATE TRIGGER trg_log_region

AFTER INSERT OR UPDATE OR DELETE

ON tb_region

FOR EACH ROW

EXECUTE FUNCTION fn_log_region();
```

A utilização de `AFTER` garante que a auditoria seja realizada somente após a operação principal ser executada.

---

# Recursos Utilizados

A implementação utiliza os seguintes recursos do PostgreSQL:

- Triggers;
- Functions em PL/pgSQL;
- `TG_OP`;
- `NEW`;
- `OLD`;
- `CURRENT_USER`;
- `CURRENT_TIMESTAMP`;
- `json_each_text`;
- `row_to_json`.

---

# Operações Auditadas

| Operação | Auditoria |
|----------|:---------:|
| INSERT | ✔ |
| UPDATE | ✔ |
| DELETE | ✔ |
| TRUNCATE | ✘ |

O comando **TRUNCATE** não faz parte desta auditoria porque remove registros em massa e não disponibiliza os valores individuais `OLD` e `NEW`.

---