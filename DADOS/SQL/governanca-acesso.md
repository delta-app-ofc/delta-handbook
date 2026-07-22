# Governança de Acesso — Projeto Delta

Este documento define as roles e permissões do banco de dados relacional PostgreSQL do Projeto Delta.

## Estruturas consideradas

Tabelas atualmente implementadas no schema (`script-dataload.sql` / DDL):

- `tb_region`
- `tb_day_of_week`
- `tb_habit`
- `tb_address`
- `tb_user`
- `tb_property`
- `tb_user_property`
- `tb_device`
- `tb_region_rate`
- `tb_user_habit`
- `tb_user_habit_day`
- `tb_last_water_bill`

Estruturas **planejadas, ainda não criadas** no banco (sem `CREATE TABLE`/`CREATE VIEW` correspondente até o momento):

- views analíticas
- functions, procedures, triggers e auditoria

> Enquanto essas estruturas não existirem, as permissões abaixo (ex.: `sys_bi_analyst`) recaem sobre as tabelas normais do schema `public`, não sobre views. Assim que as views/functions forem criadas, os grants precisam ser revisados.

---

## sys_data_engineer *(anteriormente referido como "sys_engenheiro_dados")*

Permissões:
- Criação e manutenção de tabelas normalizadas
- Definição de PKs, FKs e constraints
- `CREATE` no schema `public` (permite criar functions, procedures, triggers e views quando forem implementadas)
- `ALL PRIVILEGES` em todas as tabelas e sequences do schema `public`
- Controle estrutural do banco

---

## sys_backend_developer *(anteriormente referido como "sys_desenvolvedor_backend")*

Permissões:
- CRUD completo (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) nas 12 tabelas do sistema listadas em "Estruturas consideradas"
- Privilégio padrão (`ALTER DEFAULT PRIVILEGES`) garante o mesmo CRUD em tabelas futuras criadas no schema `public`

---

## sys_bi_analyst *(anteriormente referido como "sys_analista_bi")*

Permissões:
- `SELECT` em todas as tabelas do schema `public` (hoje não existem views analíticas separadas; quando forem criadas, o acesso deve ser restrito a elas)
- `USAGE` no schema `public`
- Sem permissão de escrita

---

## sys_devops

Permissões:
- `ALL PRIVILEGES ON DATABASE` (conectar, criar objetos, uso de espaço temporário)
- Responsável por backup, restore e administração geral do PostgreSQL (operações executadas fora do SQL de grants, via acesso de sistema/infra)

> ⚠️ **Pendência:** o script atual **não** concede `CREATEROLE` nem privilégios de gerenciamento de usuários/roles. Se o `sys_devops` precisa criar/alterar/remover roles e usuários pelo próprio banco, é necessário um `ALTER ROLE sys_devops CREATEROLE;` explícito (ou acesso de superusuário via infraestrutura).

---

## sys_first_year *(anteriormente referido como "sys_primeiro_ano")*

Permissões:
- Apenas leitura (`SELECT`)
- Acesso restrito às tabelas do sistema
- Sem permissões de escrita ou execução (`INSERT`, `UPDATE`, `DELETE` e `EXECUTE` em functions revogados explicitamente)

---

# 2. Atribuição de Usuários

| Integrante | Disciplinas | Roles |
|------------|------------|------|
| Ana | UX, DAD, BI, EQS | `sys_bi_analyst` |
| Davi | Mobile, DAD, DS2, EQS | `sys_backend_developer` |
| João | Mobile, DS2, IA, EQS | `sys_backend_developer` |
| Mariana | MDD, BD2, DS2, IA, EQS | `sys_data_engineer`, `sys_backend_developer` |
| Rahquel | Mobile, DAD, UX, EQS | `sys_backend_developer` |
| Samuel | BI, DevOps, BD2, IA, MDD, EQS | `sys_devops`, `sys_data_engineer`, `sys_bi_analyst` |
| Primeiro Ano | Apoio / Leitura | `sys_first_year` |

---