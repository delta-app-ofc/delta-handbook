# 8. Modelagem de Dados — Texto da Entrega

**Formato exigido de entrega:** links diretos do GitHub para cada demanda, acesso liberado aos professores e relatório de justificativa no próprio repositório.

- Link do GitHub onde estão os códigos do banco de dados relacional: https://github.com/delta-app-ofc/delta-sql-database
- Link do GitHub onde estão os códigos do RPA: https://github.com/delta-app-ofc/delta-rpa
- Link do repositório de documentação: https://github.com/delta-app-ofc/delta-handbook/tree/main/DADOS
- Link do README que reúne tudo: https://github.com/delta-app-ofc/delta-sql-database/blob/main/README.md

## 8.1 Requisitos

### MOD-01 — Criar novo banco relacional PostgreSQL normalizado até 3FN ou, se necessário, até 5FN

banco PostgreSQL com 22 tabelas de negócio normalizadas até a 3FN, com tabelas associativas para relacionamentos N:N e restrições de integridade no próprio banco.

**Evidências diretas:**

- Script de criação do banco e tabelas: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-schema.sql
- Documentação do modelo relacional: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-relacional.md
- Diagrama com a modelagem lógica das entidades principais: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica.png
- Modelagem conceitual da arquitetura: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-conceitual.png
- Inventário de tabelas — parte 1: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-01-tabelas-01.png
- Inventário de tabelas — parte 2: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-01-tabelas-02.png
- Inventário de tabelas — parte 3: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-01-tabelas-03.png
- Inventário de tabelas — parte 4: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-01-tabelas-04.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-01-banco-postgresql-normalizacao.md

### MOD-02 — Definir claramente PKs, FKs e cardinalidades 1:1, 1:N e N:N

todas as tabelas têm chave primária, os relacionamentos usam chaves estrangeiras nomeadas (`fk_<origem>_<destino>`) com política `ON DELETE`, e as cardinalidades 1:1, 1:N e N:N estão representadas no modelo.

**Evidências diretas:**

- Script de criação do banco e tabelas: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-schema.sql
- Documentação do modelo relacional: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-relacional.md
- Diagrama lógico: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-02-pk-fk-cardinalidades.md

### MOD-03 — Carregar pelo menos 500 registros verossímeis para testes de volume

carga de 2.331 registros em 22 tabelas, com 201 usuários, 155 imóveis, 400 hábitos, 371 municípios e tarifas reais da ARSESP, acompanhada de consulta de contagem por tabela.

**Evidências diretas:**

- Script da carga de dados: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-dataload.sql
- Documentação da carga e contagem por tabela: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/dataload.md
- Contagem executada — parte 1: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-03-contagem-01.png
- Contagem executada — parte 2: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-03-contagem-02.png
- Consulta SQL da contagem: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-03-consulta-contagem.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-03-carga-registros-verossimeis.md

### MOD-04 — Orquestrar RPA para mover dados do banco legado ao novo normalizado, garantindo integridade e tratamento de falhas de carga

RPA em Python que executa um pipeline de extração, validação, transformação e carga entre o banco legado e o novo banco, com transação única, rollback em caso de falha e registro de cada execução em `tb_log_rpa`.

**Evidências diretas:**

- Repositório do RPA: https://github.com/delta-app-ofc/delta-rpa
- README explicativo: https://github.com/delta-app-ofc/delta-rpa/blob/main/README.md
- Orquestração principal: https://github.com/delta-app-ofc/delta-rpa/blob/main/app/main.py
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-04-rpa-migracao-banco-legado.md

### MOD-05 — Criar views analíticas para Data Mart, com modelagem dimensional Star Schema ou Snowflake

Data Mart em Star Schema, com camadas `stage`, `silver`, `gold` e `dw`, três dimensões, três tabelas fato e nove views analíticas.

**Evidências diretas:**

- Script de criação do Data Mart: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-datamart.sql
- Views analíticas do schema `dw`: https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views
- Documentação da camada de BI: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md
- Diagrama da camada analítica: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica-camada-analitica.png
- Print das nove views do schema dw: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-05-views-dw.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-05-views-analiticas-data-mart.md

### MOD-06 — Usar CTEs na lógica de transformação ETL em SQL

a procedure de transformação `silver.sp_load_ft_consumption_daily` e as sete views do schema `dw` usam `WITH` para separar a transformação em etapas.

**Evidências diretas:**

- Procedure de transformação com CTE: https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/silver/procedures/sp_load_ft_consumption_daily.sql
- Views analíticas com CTEs: https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views
- Documentação da camada de BI: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-06-ctes-etl-sql.md

### MOD-07 — Usar Window Functions para cálculos analíticos, por exemplo Running Total ou Ranking, nas views de BI

as views de BI calculam consumo acumulado, média móvel de 7 dias, rankings (`RANK`, `DENSE_RANK`), quartis, quintis (`NTILE`), posição relativa (`PERCENT_RANK`) e variação mensal (`LAG`).

**Evidências diretas:**

- View com Running Total e média móvel: https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_consumption_daily.sql
- View com rankings e distribuição: https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_property_ranking.sql
- View com variação mês a mês: https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_monthly_variation.sql
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-07-window-functions.md

### MOD-08 — Criar no mínimo duas Functions para regras críticas de negócio

24 Functions PL/pgSQL, entre elas `fn_user_can_estimate`, `fn_get_current_region_rate`, `fn_calculate_water_cost` e `fn_user_is_active`, que concentram no banco as validações e os cálculos de negócio.

**Evidências diretas:**

- Pasta das Functions: https://github.com/delta-app-ofc/delta-sql-database/tree/main/functions
- Script que agrega as Functions e Procedures: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-optimization.sql
- Documentação das Functions e Procedures: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/otimizacao.md
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-08-functions-regras-negocio.md

### MOD-09 — Criar no mínimo duas Procedures para regras críticas de negócio

cinco Procedures (`sp_change_region_rate`, `sp_register_property`, `sp_disable_user`, `sp_update_property_classification` e `sp_register_user_access`) que executam operações de várias etapas com validação e transação.

**Evidências diretas:**

- Pasta das Procedures: https://github.com/delta-app-ofc/delta-sql-database/tree/main/procedures
- Script que agrega as Functions e Procedures: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-optimization.sql
- Documentação das Functions e Procedures: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/otimizacao.md
- Print das cinco Procedures do schema public: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-09-procedures-01.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-09-procedures-regras-negocio.md

### MOD-10 — Criar triggers de auditoria em ao menos duas tabelas com logs completos NEW, OLD, TG_OP e CURRENT_USER

triggers `AFTER INSERT OR UPDATE OR DELETE` em 21 tabelas, cada uma com tabela de log própria que registra `TG_OP`, `NEW`, `OLD`, `CURRENT_USER`, data e hora e o log anterior (`previous_log_id`).

**Evidências diretas:**

- Script de auditoria: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-audit.sql
- Triggers de auditoria: https://github.com/delta-app-ofc/delta-sql-database/tree/main/triggers
- Documentação da auditoria: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/auditoria.md
- Diagrama de tabelas de auditoria: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/modelagem-logica-log.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-10-triggers-auditoria.md

### MOD-11 — Analisar consultas lentas com EXPLAIN ANALYZE e aplicar índices SQL para otimização

três índices aplicados após comparar planos com `EXPLAIN (ANALYZE, BUFFERS)` em volume ampliado, com ganhos medidos de cerca de 360x, 280x e 61x.

**Evidências diretas:**

- Script de criação dos índices: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-indexes.sql
- Documentação dos testes e resultados: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-11-explain-analyze-indices.md

### MOD-12 — Criar tabela técnica de catálogo de metadados com tabelas, colunas, regras de negócio e níveis de acesso

tabela `tb_data_catalog` com 261 colunas catalogadas (descrição, regra de negócio e nível `PUBLICO`, `INTERNO`, `RESTRITO` ou `SENSIVEL`), usada também para gerar os comentários das colunas.

**Evidências diretas:**

- Definição da tabela: https://github.com/delta-app-ofc/delta-sql-database/blob/main/tables/tb_data_catalog.sql
- Carga do catálogo do banco relacional: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-catalogo-dados.sql
- Carga do catálogo do Data Mart: https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-catalogo-datamart.sql
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-12-catalogo-metadados.md

### MOD-13 — Documentar procedimentos para backup e recuperação de falhas

estratégia em duas camadas, com PITR do Neon e `pg_dump` automatizado a cada 6 horas, procedimento de recuperação por gravidade, RPO de até 6 horas e RTO medido de 11 segundos.

**Evidências diretas:**

- Documentação de backup e recuperação: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/backup-recuperacao.md
- Script de backup e teste de restauração: https://github.com/delta-app-ofc/delta-sql-database/blob/main/backup_db.py
- Workflow automatizado: https://github.com/delta-app-ofc/delta-sql-database/blob/main/.github/workflows/backup-postgres.yml
- Evidência da janela de PITR no Neon: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencia-neon.png
- Teste de restauração com 47 tabelas e contagens corretas: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/backup-recuperacao/resultado-backup.png
- Log da restauração local: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/backup-recuperacao/resultado-restauracao.txt
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-13-backup-recuperacao.md

### MOD-14 — Automatizar diretamente no Postgres o registro DAU (Daily Active User)

a procedure `sp_register_user_access` valida o usuário e grava o acesso em `tb_user_access_log`, e a function `fn_get_dau` conta os usuários distintos do dia.

**Evidências diretas:**

- Tabela de acessos: https://github.com/delta-app-ofc/delta-sql-database/blob/main/tables/tb_user_access_log.sql
- Procedure de registro: https://github.com/delta-app-ofc/delta-sql-database/blob/main/procedures/sp_register_user_access.sql
- Function de cálculo: https://github.com/delta-app-ofc/delta-sql-database/blob/main/functions/fn_get_dau.sql
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-14-dau-daily-active-user.md

### MOD-15 — Implementar, onde fizer sentido, CTE recursiva ou herança de tabelas

CTE recursiva na view `dw.vw_audit_history_chain`, que reconstrói a cadeia de reajustes de tarifa por `previous_log_id`. A herança de tabelas foi testada e descartada, com justificativa.

**Evidências diretas:**

- View com `WITH RECURSIVE`: https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_audit_history_chain.sql
- Documentação da camada de BI: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md
- Print da cadeia recursiva com três níveis: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencias-requisitos/mod-15-cadeia-recursiva.png
- Justificativa do requisito: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-15-cte-recursiva-heranca.md

### MOD-16 — Incluir no repositório relatório de justificativa das decisões

um documento de justificativa por requisito, mais os documentos técnicos de cada decisão, reunidos pelo README do repositório.

**Evidências diretas:**

- README que reúne tudo: https://github.com/delta-app-ofc/delta-sql-database/blob/main/README.md
- Índice do relatório de justificativas: https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-16-relatorio-justificativas.md
- Pasta com a justificativa de cada requisito: https://github.com/delta-app-ofc/delta-handbook/tree/main/DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos

## 8.3 Checklist de fechamento

- Todos os critérios possuem evidências verificáveis: cada requisito acima lista scripts, documentos e imagens com link direto.
- Os links apontam diretamente ao trecho, documento ou imagem: arquivos na branch `main` dos repositórios `delta-sql-database`, `delta-rpa` e `delta-handbook`.
- Repositórios: os três pertencem à organização `delta-app-ofc` no GitHub.
- Evidências visuais: diagramas lógico, de auditoria, da camada analítica e conceitual em `DADOS/SQL/anexos/`, e captura do PITR do Neon (`evidencia-neon.png`).
- Conformidade com o PDF da disciplina: a numeração MOD-01 a MOD-16 segue o documento de requisitos.
