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
GRANDE_SP
```

### 3. fn_get_current_region_rate()

####  Descrição

A função retorna o valor da tarifa de água vigente para uma determinada região e categoria de imóvel, considerando uma data específica. A tarifa retornada deve estar dentro do período de validade cadastrado (initial_validity e final_validity)


#### Assinatura

```sql
fn_get_current_region_rate(
    p_region_id INTEGER,
    p_classification_id INTEGER,
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
* se existe tarifa válida para a região e categoria do imóvel.


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

## Functions organizacionais

As functions de 5 a 11 dão suporte ao perfil organizacional (usuário vinculado a uma empresa via
`tb_user_organization`, em vez de dono de imóvel residencial via `tb_user_property`). Elas existem porque
o `delta-artificial-intelligence` (Agente de Previsão) fazia essa resolução em várias consultas SQL
separadas, uma conexão por consulta; mover a lógica pra cá reduz isso a chamadas prontas, no mesmo papel
que `fn_user_can_estimate()`/`fn_get_current_region_rate()` cumprem para o caminho residencial. O
comportamento residencial não foi alterado por nenhuma delas.

---

### 5. fn_user_access_kind()

#### Descrição

Resolve o tipo de vínculo do usuário: se ele tem qualquer linha em `tb_user_property`, é residencial
(comportamento antigo, não alterado). Só verifica `tb_user_organization` quando não há nenhuma
propriedade residencial.

#### Assinatura

```sql
fn_user_access_kind(
    p_user_id INTEGER
)
```

#### Retorno

* `'residential'` → usuário dono de imóvel residencial;
* `'organizational'` → usuário vinculado a organização, sem imóvel residencial próprio;
* `'none'` → usuário sem nenhum dos dois vínculos.

---

### 6. fn_user_organization_properties()

#### Descrição

Lista as propriedades de todas as organizações às quais o usuário está vinculado. Como
`tb_user_organization` é M:N e sem papel/hierarquia, um usuário em mais de uma organização recebe as
propriedades de todas elas no mesmo conjunto.

#### Assinatura

```sql
fn_user_organization_properties(
    p_user_id INTEGER
)
```

#### Retorno

Tabela com `property_id`, `name`, `city`, `state` — uma linha por propriedade.

---

### 7. fn_organization_can_estimate()

#### Descrição

Verifica se existe telemetria real para pelo menos uma das propriedades informadas. Uma linha em
`gold.ft_consumption_daily` já implica que o ETL calculou uma tarifa válida com sucesso (via
`fn_get_current_region_rate()`), então a existência da linha já basta como critério.

#### Assinatura

```sql
fn_organization_can_estimate(
    p_property_ids INTEGER[]
)
```

#### Retorno

* `TRUE` → existe telemetria para pelo menos uma das propriedades;
* `FALSE` → nenhuma das propriedades tem telemetria na camada `gold`.

---

### 8. fn_organization_consumption_history()

#### Descrição

Soma o consumo diário (`total_liters`) das propriedades informadas, dia a dia, numa janela de dias
encerrada em `p_today`. Lê de `dw.vw_consumption_daily` e funciona igual para 1 ou N propriedades.

#### Assinatura

```sql
fn_organization_consumption_history(
    p_property_ids INTEGER[],
    p_days         INTEGER,
    p_today        DATE
)
```

#### Retorno

Tabela com `full_date`, `total_liters` — uma linha por dia com consumo agregado.

---

### 9. fn_organization_last_billed_period()

#### Descrição

Soma `total_liters`/`cost_value` do último mês calendário fechado antes de `p_today`. Como o dado real de
telemetria organizacional ainda é escasso, quando o mês fechado não tem nenhuma linha a function cai num
fallback: soma todo o histórico disponível das propriedades, rotulado com o mês da leitura mais recente.

#### Assinatura

```sql
fn_organization_last_billed_period(
    p_property_ids INTEGER[],
    p_today        DATE
)
```

#### Retorno

Tabela com `reference_month`, `total_liters`, `total_cost` — uma linha, ou nenhuma se as propriedades não
tiverem telemetria alguma.

---

### 10. fn_organization_effective_rate()

#### Descrição

Calcula `SUM(cost_value) / (SUM(total_liters)/1000)` numa janela de dias. É calculada, e não consultada
diretamente em `tb_region_rate`, porque propriedades de uma mesma organização podem estar em
regiões/categorias diferentes — não existe um único `region_id`/`classification_id` válido pro conjunto.

#### Assinatura

```sql
fn_organization_effective_rate(
    p_property_ids  INTEGER[],
    p_today         DATE,
    p_window_days   INTEGER DEFAULT 30
)
```

#### Retorno

Valor da tarifa efetiva em R$/m³, ou `NULL` quando não há consumo na janela informada.

---

### 11. fn_organization_forecast_context()

#### Descrição

Function de otimização principal: compõe as seis anteriores num único round-trip, pensada para o fluxo
`calculate_forecast` do Agente de Previsão, que antes encadeava todas as consultas em sequência. Quando
`p_property_name` é informado, filtra as propriedades por substring (case-insensitive) no nome:

* mais de uma bateu → `match_status = 'ambiguous'`, `candidate_properties` lista as que bateram;
* nenhuma bateu → `match_status = 'not_found'`, `candidate_properties` lista todas as unidades da organização;
* exatamente uma bateu, ou `p_property_name` não informado (agrega todas) → `match_status = 'resolved'`.

Se o usuário não for organizacional (`fn_user_access_kind() <> 'organizational'`), retorna
`match_status = 'not_applicable'` sem consultar mais nada.

#### Assinatura

```sql
fn_organization_forecast_context(
    p_user_id          INTEGER,
    p_property_name    TEXT    DEFAULT NULL,
    p_today            DATE    DEFAULT CURRENT_DATE,
    p_history_days     INTEGER DEFAULT 45,
    p_rate_window_days INTEGER DEFAULT 30
)
```

#### Retorno

Uma linha com: `access_kind`, `match_status`, `resolved_property_ids`, `candidate_properties` (JSON),
`can_estimate`, `history` (JSON, array de `{full_date, total_liters}`), `last_bill_month`,
`last_bill_total_value`, `last_bill_m3_value` (litros convertidos pra m³), `effective_rate`.

> **Validação:** as 7 functions foram testadas manualmente (padrão já usado neste repositório — container
> Postgres 18 descartável, pipeline oficial completo) com os dados reais de organização do dataload (3
> organizações, `tb_user_organization` com os usuários 2 e 15). Como não havia telemetria real disponível
> na sessão de teste, `gold.ft_consumption_daily` foi populada com dado sintético só dentro do container
> descartável (nunca commitado) para exercitar as 7 functions ponta a ponta, incluindo o fallback de
> `fn_organization_last_billed_period()` e os 4 `match_status` de `fn_organization_forecast_context()`.

---

## Procedures

---

### 1. sp_change_region_rate()

####  Descrição

A procedure realiza a alteração da tarifa de água de uma região e categoria de imóvel, mantendo o histórico de valores. Quando uma nova tarifa é cadastrada, a tarifa anterior daquela combinação região/categoria é encerrada automaticamente, pois uma região e categoria não podem possuir duas tarifas vigentes ao mesmo tempo.

#### Assinatura

```sql
sp_change_region_rate(
    p_region_id INTEGER,
    p_classification_id INTEGER,
    p_new_rate NUMERIC(10,2),
    p_initial_validity DATE
)
```
#### Funcionamento
A procedure executa:

* validação da existência da região;
* validação da existência da categoria;
* validação do valor informado;
* encerramento da tarifa atual daquela região/categoria;
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
| `fn_get_current_region_rate()` | Function | Consulta a tarifa de água vigente de uma região e categoria de imóvel considerando o período de validade cadastrado. |
| `fn_user_can_estimate()` | Function | Verifica se um usuário possui todos os requisitos necessários para geração de estimativas de consumo. |
| `fn_user_access_kind()` | Function | Resolve se o usuário é residencial, organizacional ou nenhum dos dois. |
| `fn_user_organization_properties()` | Function | Lista as propriedades de todas as organizações do usuário. |
| `fn_organization_can_estimate()` | Function | Verifica se existe telemetria real em pelo menos uma propriedade da organização. |
| `fn_organization_consumption_history()` | Function | Soma o consumo diário das propriedades informadas numa janela de dias. |
| `fn_organization_last_billed_period()` | Function | Soma consumo/custo do último mês fechado, com fallback pro histórico disponível. |
| `fn_organization_effective_rate()` | Function | Calcula a tarifa efetiva (R$/m³) numa janela de dias, a partir do consumo real. |
| `fn_organization_forecast_context()` | Function | Compõe as 6 functions organizacionais acima num único round-trip para o Agente de Previsão. |

---

#### Procedures Implementadas

| Nome | Tipo | Objetivo |
|---|---|---|
| `sp_change_region_rate()` | Procedure | Atualiza tarifas de uma região e categoria de imóvel mantendo o histórico de valores e controle de vigência. |
| `sp_register_property()` | Procedure | Realiza o cadastro de uma propriedade e cria automaticamente o vínculo com o usuário responsável. |
| `sp_disable_user()` | Procedure | Desativa usuários e seus dispositivos relacionados mantendo os dados históricos. |

---