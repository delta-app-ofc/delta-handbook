# 📘 Documentação da Auditoria de Tabelas

## Objetivo

O sistema de auditoria foi desenvolvido com o objetivo de registrar todas as alterações realizadas nas tabelas do banco de dados, permitindo rastrear quem realizou uma operação, quando ela ocorreu e quais dados foram afetados.

A auditoria contempla as operações de **INSERT**, **UPDATE** e **DELETE**.

---

# Funcionamento

Cada tabela principal do sistema possui uma tabela de auditoria correspondente.

Exemplos:

| Tabela Principal | Tabela de Auditoria |
|------------------|---------------------|
| tb_region | tb_log_region |
| tb_user | tb_log_user |
| tb_property | tb_log_property |
| ... | ... |

Sempre que um registro é inserido, alterado ou removido, uma Trigger é executada.
A Trigger chama uma Function responsável por copiar os dados da operação para sua respectiva tabela de auditoria.

---

# Informações Registradas

Cada registro de auditoria armazena as seguintes informações:

| Campo | Descrição |
|--------|-----------|
| id | Identificador do registro de auditoria |
| operation | Tipo da operação realizada (INSERT, UPDATE ou DELETE) |
| executed_by | Usuário do banco responsável pela operação (`CURRENT_USER`) |
| executed_at | Data e hora da operação (`CURRENT_TIMESTAMP`) |
| id da tabela | Identificador do registro alterado |
| Demais campos | Cópia completa dos dados do registro auditado |

---

# Estrutura Geral das Tabelas de Auditoria

Todas as tabelas de auditoria seguem o mesmo padrão estrutural.

Exemplo:

```sql
CREATE TABLE tb_log_region (

      id                      SERIAL       PRIMARY KEY

    , operation               VARCHAR(10)  NOT NULL

    , executed_by             VARCHAR(100) NOT NULL

    , executed_at             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP

    , region_id               INTEGER

    , name                    VARCHAR(20)

);
```

---

# Funcionamento da Function

Cada tabela possui uma Function específica.

Exemplo:

```
fn_log_region()
```

A Function é executada automaticamente pela Trigger sempre que ocorre uma modificação na tabela correspondente.

O comportamento depende do tipo de operação executada.

## INSERT

Quando um novo registro é inserido:

- `TG_OP` recebe o valor **INSERT**;
- `CURRENT_USER` identifica o usuário responsável pela operação;
- `CURRENT_TIMESTAMP` registra a data e hora da execução;
- `NEW` contém os valores do novo registro.

Essas informações são inseridas na tabela de auditoria.

---

## UPDATE

Quando um registro é atualizado:

- `TG_OP` recebe o valor **UPDATE**;
- `CURRENT_USER` identifica quem realizou a alteração;
- `CURRENT_TIMESTAMP` registra o momento da alteração;
- `NEW` contém os novos valores do registro atualizado.

Os dados atualizados são gravados na tabela de auditoria.

---

## DELETE

Quando um registro é removido:

- `TG_OP` recebe o valor **DELETE**;
- `CURRENT_USER` identifica quem realizou a exclusão;
- `CURRENT_TIMESTAMP` registra o momento da exclusão;
- `OLD` contém os valores do registro antes de sua remoção.

Esses dados são armazenados na tabela de auditoria antes que o registro seja definitivamente excluído.

---

# Funcionamento da Trigger

Cada tabela possui uma Trigger própria.

Exemplo:

```sql
CREATE TRIGGER trg_log_region

AFTER INSERT OR UPDATE OR DELETE

ON tb_region

FOR EACH ROW

EXECUTE FUNCTION fn_log_region();
```

A Trigger é executada **AFTER**, garantindo que somente operações concluídas com sucesso sejam registradas.
---

# Recursos Utilizados

A implementação da auditoria utiliza os seguintes recursos do PostgreSQL:

- Triggers
- Functions em PL/pgSQL
- TG_OP
- NEW
- OLD
- CURRENT_USER
- CURRENT_TIMESTAMP

---

# Operações Auditadas

| Operação | Auditada |
|-----------|:-------:|
| INSERT | ✔ |
| UPDATE | ✔ |
| DELETE | ✔ |
| TRUNCATE | ✘ |

O comando **TRUNCATE** não faz parte desta auditoria, pois não atua sobre registros individuais e, portanto, não disponibiliza os pseudo-registros **NEW** e **OLD**, utilizados pelas Triggers do tipo `FOR EACH ROW`.

---
