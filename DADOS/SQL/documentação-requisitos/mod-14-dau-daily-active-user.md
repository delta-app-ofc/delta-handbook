### MOD-14 — Automatizar diretamente no Postgres o registro DAU (Daily Active User)

**Evidência direta:**

- [Tabela de registro de acessos `tb_user_access_log`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/tables/tb_user_access_log.sql)
- [Procedure `sp_register_user_access`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/procedures/sp_register_user_access.sql)
- [Function `fn_get_dau`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/functions/fn_get_dau.sql)
- [Script que agrega as Functions e Procedures](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-optimization.sql)
- [Documentação das Functions e Procedures](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/otimizacao.md)

**Localização e como comprovar:**

O DAU (Daily Active User) é a quantidade de usuários distintos que acessaram o sistema em um dia. O registro e o cálculo acontecem dentro do PostgreSQL, em três peças.

| Peça | Papel |
|---|---|
| `tb_user_access_log` | Guarda um registro por acesso: `user_id`, `access_channel` (`WEB`, `MOBILE` ou `CHATBOT`) e `accessed_at`, preenchido por `CURRENT_TIMESTAMP` |
| `sp_register_user_access(p_user_id, p_access_channel)` | Valida com `fn_user_is_active` que o usuário existe e está ativo, e então insere o acesso |
| `fn_get_dau(p_date)` | Retorna `COUNT(DISTINCT user_id)` dos acessos da data informada |

#### 1. Por que no banco

A chamada `CALL sp_register_user_access(...)` é a única operação que a API, o app e o chatbot precisam executar. O PostgreSQL aplica a regra de usuário ativo, grava o horário e restringe o canal, sem lógica duplicada em cada aplicação. `COUNT(DISTINCT user_id)` garante que vários acessos do mesmo usuário no dia contem uma vez só.

A tabela `tb_user_access_log` tem `ON DELETE CASCADE` para o usuário e uma restrição `CHECK` para o canal. Os acessos são populados em execução, a cada chamada da procedure, e não pelo dataload.

#### 2. Como comprovar

1. Executar `script-schema.sql`, `script-optimization.sql` e `script-dataload.sql`.
2. Registrar dois acessos do mesmo usuário e um de outro:

```sql
CALL sp_register_user_access(1, 'WEB');
CALL sp_register_user_access(1, 'MOBILE');
CALL sp_register_user_access(2, 'CHATBOT');
```

3. Executar `SELECT fn_get_dau(CURRENT_DATE);` e conferir `2`, pois são dois usuários distintos.
4. Executar `CALL sp_register_user_access(<id de usuário inativo>, 'WEB');` e conferir a exceção de usuário inativo.
