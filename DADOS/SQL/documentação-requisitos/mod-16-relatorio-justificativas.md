### MOD-16 — Incluir no repositório relatório de justificativa das decisões

**Evidência direta:**

- [README que reúne tudo](https://github.com/delta-app-ofc/delta-sql-database/blob/docs/readme-modelagem/README.md)
- [Entrega da seção de Modelagem de Dados](entrega-modelagem-dados.md)
- [Pasta com a justificativa de cada requisito](.)
- [Modelagem conceitual da arquitetura](../anexos/modelagem-conceitual.png)

**Localização e como comprovar:**

O relatório de justificativa é formado por um documento por requisito, em `DADOS/SQL/documentação-requisitos/`, e pelos documentos técnicos que registram cada decisão de projeto. O README do `delta-sql-database` reúne os links de todos eles.

#### 1. Justificativa por requisito

| Requisito | Documento |
|---|---|
| MOD-01 | [Banco relacional normalizado até 3FN](mod-01-banco-postgresql-normalizacao.md) |
| MOD-02 | [PKs, FKs e cardinalidades](mod-02-pk-fk-cardinalidades.md) |
| MOD-03 | [Carga de registros verossímeis](mod-03-carga-registros-verossimeis.md) |
| MOD-04 | [RPA de migração do banco legado](mod-04-rpa-migracao-banco-legado.md) |
| MOD-05 | [Views analíticas e Data Mart](mod-05-views-analiticas-data-mart.md) |
| MOD-06 | [CTEs no ETL](mod-06-ctes-etl-sql.md) |
| MOD-07 | [Window Functions](mod-07-window-functions.md) |
| MOD-08 | [Functions de regras de negócio](mod-08-functions-regras-negocio.md) |
| MOD-09 | [Procedures de regras de negócio](mod-09-procedures-regras-negocio.md) |
| MOD-10 | [Triggers de auditoria](mod-10-triggers-auditoria.md) |
| MOD-11 | [EXPLAIN ANALYZE e índices](mod-11-explain-analyze-indices.md) |
| MOD-12 | [Catálogo de metadados](mod-12-catalogo-metadados.md) |
| MOD-13 | [Backup e recuperação](mod-13-backup-recuperacao.md) |
| MOD-14 | [DAU](mod-14-dau-daily-active-user.md) |
| MOD-15 | [CTE recursiva](mod-15-cte-recursiva-heranca.md) |

#### 2. Decisões de projeto registradas

| Tema | Documento | Decisões justificadas |
|---|---|---|
| Modelo relacional | [modelagem-relacional.md](../modelagem-relacional.md) | Entidades, tabelas associativas, extensão comercial e industrial |
| Regras de negócio | [regras-negocio.md](../regras-negocio.md) | Padrão de maiúsculas, idioma, prefixos de objetos |
| Mapeamento de municípios | [mapeamento-cidade-regiao.md](../mapeamento-cidade-regiao.md) | 371 municípios em nove regiões tarifárias |
| Tarifas e cenários | [pesquisa-cenarios-investimento.md](../pesquisa-cenarios-investimento.md) | Fontes dos valores de tarifa e investimento |
| Camada de BI | [camada-bi.md](../camada-bi.md) | Arquitetura medalhão, Star Schema, CTE recursiva no lugar de herança |
| Functions e Procedures | [otimizacao.md](../otimizacao.md) | Regras de negócio concentradas no banco |
| Auditoria | [auditoria.md](../auditoria.md) | Uma tabela de log por tabela auditada, `previous_log_id` |
| Governança de acesso | [governanca-acesso.md](../governanca-acesso.md) | Roles `sys_*` e níveis de acesso |
| Backup | [backup-recuperacao.md](../backup-recuperacao.md) | PITR mais `pg_dump`, RPO e RTO |
| Carga de dados | [dataload.md](../dataload.md) | Contagem por tabela e consulta de verificação |

#### 3. Como comprovar

1. Abrir o README do `delta-sql-database` e conferir a tabela MOD-01 a MOD-16 com os links.
2. Abrir cada documento `mod-XX` e conferir as seções "Evidência direta" e "Localização e como comprovar".
3. Abrir a pasta `documentação-requisitos` e conferir os 16 documentos e a entrega consolidada.
