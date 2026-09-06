# 📘 Documentação — Functions e Procedures de Regras de Negócio (PostgreSQL)

## 1. Objetivo

Este documento apresenta as Functions e Procedures implementadas no banco PostgreSQL.

Esses objetos foram desenvolvidos para centralizar regras de negócio críticas e otimizar operações frequentes.

---

## Functions

---

### 1. fn_user_is_active()

####  Descrição

A função verifica se um usuário está ativo no sistema, pois usuários inativos não devem realizar operações.

#### Assinatura

```sql
fn_user_is_active(
    p_user_id INTEGER
)
````

#### Retorno

* `TRUE` → usuário ativo;
* `FALSE` → usuário inativo.

---

### 2. fn_get_property_region()

####  Descrição

A função retorna a região associada a uma propriedade, para não precisar realizar tantos joins em consultas.

#### Assinatura

```sql
fn_get_property_region(
    p_property_id INTEGER
)
```

#### Retorno

Retorna o nome da região.

Exemplo:
```
CENTRO
```

### 3. fn_get_current_region_rate()

####  Descrição

A função retorna o valor da tarifa de água vigente para uma determinada região considerando uma data específica. A tarifa retornada deve estar dentro do período de validade cadastrado (initial_validity e final_validity)


#### Assinatura

```sql
fn_get_current_region_rate(
    p_region_id INTEGER,
    p_date DATE
)
```

#### Retorno
Retorna o valor do metro cúbico da água.

---

### 4. fn_user_can_estimate()

####  Descrição

A função verifica se um usuário possui todos os requisitos necessários para que o sistema possa gerar uma estimativa de consumo.

*Validações realizadas*

* se o usuário existe;
* se o usuário está ativo;
* se existe uma propriedade vinculada;
* se a propriedade possui dispositivo ativo;
* se existe tarifa válida para a região.


#### Assinatura

```sql
fn_user_can_estimate(
    p_user_id INTEGER
)
```

#### Retorno
* TRUE → usuário pode gerar estimativas;
* FALSE → usuário não possui requisitos suficientes.

---

## Procedures

---

### 1. sp_change_region_rate()

####  Descrição

A procedure realiza a alteração da tarifa de água de uma região mantendo o histórico de valores. Quando uma nova tarifa é cadastrada, a tarifa anterior é encerrada automaticamente, pois uma região não pode possuir duas tarifas vigentes ao mesmo tempo.

#### Assinatura

```sql
sp_change_region_rate(
    p_region_id INTEGER,
    p_new_rate NUMERIC(10,2),
    p_initial_validity DATE
)
```
#### Funcionamento
A procedure executa:

* validação da existência da região;
* validação do valor informado;
* encerramento da tarifa atual;
* inserção da nova tarifa.

---

### 2. sp_register_property()

####  Descrição


A procedure realiza o cadastro completo de uma propriedade no sistema.

Além de criar o imóvel, ela também realiza automaticamente o vínculo entre usuário e propriedade.


#### Assinatura

```sql
sp_register_property(
    p_user_id INTEGER,
    p_name VARCHAR(100),
    p_type VARCHAR(20),
    p_classification VARCHAR(20),
    p_address_id INTEGER
)
```
#### Funcionamento
A procedure executa:

* verificação se o usuário existe;
* verificação se o usuário está ativo;
* Validação se o endereço informado existe;
* inserção da nova propriedade;
* obtenção do id gerado;
* criação do relacionamento entre usuário e propriedade;

---

### 2. sp_disable_user()

####  Descrição


A procedure realiza a desativação de um usuário mantendo os dados históricos no banco.

Ao invés de excluir registros, o usuário é marcado como inativo e os dispositivos relacionados também são desativados.


#### Assinatura

```sql
sp_disable_user(
    p_user_id INTEGER
)
```
#### Funcionamento
A procedure executa:

* verificação se o usuário existe;
* alteração do campo is_active;
* busca das propriedades vinculadas;
* desativação dos dispositivos vinculados;

---

### Resumo
#### Functions Implementadas

| Nome | Tipo | Objetivo |
|---|---|---|
| `fn_user_is_active()` | Function | Verifica se um usuário está ativo antes da execução de operações do sistema. |
| `fn_get_property_region()` | Function | Retorna a região associada a uma propriedade através do relacionamento entre imóvel, endereço e região. |
| `fn_get_current_region_rate()` | Function | Consulta a tarifa de água vigente de uma região considerando o período de validade cadastrado. |
| `fn_user_can_estimate()` | Function | Verifica se um usuário possui todos os requisitos necessários para geração de estimativas de consumo. |

---

#### Procedures Implementadas

| Nome | Tipo | Objetivo |
|---|---|---|
| `sp_change_region_rate()` | Procedure | Atualiza tarifas de uma região mantendo o histórico de valores e controle de vigência. |
| `sp_register_property()` | Procedure | Realiza o cadastro de uma propriedade e cria automaticamente o vínculo com o usuário responsável. |
| `sp_disable_user()` | Procedure | Desativa usuários e seus dispositivos relacionados mantendo os dados históricos. |

---