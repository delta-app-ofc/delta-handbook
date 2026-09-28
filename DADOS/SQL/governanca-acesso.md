# Governança de Acesso — Projeto Delta

Este documento define as roles e permissões do banco de dados relacional PostgreSQL do Projeto Delta.

## Estruturas consideradas

Tabelas do schema `public` (cadastral/transacional, perfil residencial e comercial/industrial):

- `tb_region`, `tb_day_of_week`, `tb_habit`, `tb_water_usage_type`, `tb_address`, `tb_user`,
  `tb_organization`, `tb_property`, `tb_property_classification`, `tb_property_operational_profile`,
  `tb_property_shift`, `tb_property_water_usage`, `tb_property_operation_day`, `tb_user_property`,
  `tb_user_organization`, `tb_device`, `tb_region_rate`, `tb_user_habit`, `tb_user_habit_day`,
  `tb_last_water_bill`, `tb_investment_scenario`
- Trio de auditoria (`tb_log_*`/`fn_log_*`/`trg_log_*`) para cada uma das tabelas acima - ver
  `auditoria.md`.

Camada de BI, em schemas próprios (não em `public`) - ver `camada-bi.md`:

- `stage` - espelho bruto da telemetria do MongoDB.
- `silver` - dado tratado (dimensões e fatos no grão original).
- `gold` - modelo dimensional (star schema, chave substituta).
- `dw` - views analíticas (`vw_ft_*`, `vw_audit_history_chain`), a camada que o BI consome de fato.

`sys_bi_analyst` tem `USAGE`/`SELECT` nos schemas `gold` e `dw` (além do `public`) - é o papel pensado
pra consumir o resultado da camada de BI. `sys_data_engineer` tem controle total sobre `stage`/`silver`/
`gold` e leitura em `dw`, porque é quem mantém o pipeline.

---

## sys_data_engineer *(anteriormente referido como "sys_engenheiro_dados")*

Permissões:
- Criação e manutenção de tabelas normalizadas
- Definição de PKs, FKs e constraints
- `CREATE` no schema `public` (permite criar functions, procedures, triggers e views)
- `ALL PRIVILEGES` em todas as tabelas e sequences do schema `public`
- `ALL PRIVILEGES` nos schemas `stage`/`silver`/`gold` da camada de BI e `SELECT` em `dw` - é quem
  mantém o pipeline `stage → silver → gold → dw` (`camada-bi.md`)
- Controle estrutural do banco

---

## sys_backend_developer *(anteriormente referido como "sys_desenvolvedor_backend")*

Permissões:
- CRUD completo (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) nas tabelas cadastrais/transacionais do sistema
  listadas individualmente em "Estruturas consideradas" (schema `public`)
- Privilégio padrão (`ALTER DEFAULT PRIVILEGES`) garante o mesmo CRUD em tabelas futuras criadas no schema `public`

---

## sys_bi_analyst *(anteriormente referido como "sys_analista_bi")*

Permissões:
- `SELECT` em todas as tabelas do schema `public`
- `USAGE` + `SELECT` nos schemas `gold` e `dw` da camada de BI (`camada-bi.md`) - é o acesso real que este
  papel usa no dia a dia, já que o BI consome as views de `dw` e, quando precisa, o modelo dimensional de
  `gold` diretamente
- Sem permissão de escrita em nenhum schema

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
| Samuel | BI, DevOps, BD2, IA, MDD, EQS | `sys_devops`, `sys_data_engineer`, `sys_bi_analyst` |
| Primeiro Ano | Apoio / Leitura | `sys_first_year` |

---