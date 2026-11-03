# Evidências visuais dos requisitos de Modelagem de Dados

Objetivo: reunir as capturas enviadas para comprovar consultas e resultados do PostgreSQL. As capturas originais foram preservadas, incluindo as três versões da consulta de Procedures.

| Requisito | Imagem | O que a captura apresenta |
|---|---|---|
| MOD-13 — histórico | [historico-workflow-restauracao-pulada.png](historico-workflow-restauracao-pulada.png) | Execução #121: o job de restauração foi pulado. Não comprova restauração; o teste local bem-sucedido está na pasta de backup. |
| MOD-05 | [mod-05-views-dw.png](mod-05-views-dw.png) | Consulta lista as nove views do schema dw. |
| MOD-15 | [mod-15-cadeia-recursiva.png](mod-15-cadeia-recursiva.png) | View de auditoria da tarifa 5: INSERT, UPDATE e UPDATE nos níveis 1, 2 e 3. |
| MOD-09 | [mod-09-procedures-01.png](mod-09-procedures-01.png) | Consulta lista as cinco Procedures do schema public. |
| MOD-09 | [mod-09-procedures-02.png](mod-09-procedures-02.png) | Segunda captura enviada da mesma consulta de Procedures. |
| MOD-09 | [mod-09-procedures-03.png](mod-09-procedures-03.png) | Terceira captura enviada da mesma consulta de Procedures. |
| MOD-01 | [mod-01-tabelas-01.png](mod-01-tabelas-01.png) | Inventário das tabelas públicas, primeira parte. |
| MOD-01 | [mod-01-tabelas-02.png](mod-01-tabelas-02.png) | Inventário das tabelas públicas, segunda parte. |
| MOD-01 | [mod-01-tabelas-03.png](mod-01-tabelas-03.png) | Inventário das tabelas públicas, terceira parte. |
| MOD-01 | [mod-01-tabelas-04.png](mod-01-tabelas-04.png) | Parte final do inventário, encerrando em 47 tabelas; tb_device_credential não aparece. |
| MOD-03 | [mod-03-contagem-01.png](mod-03-contagem-01.png) | Primeira parte da contagem, incluindo 9 regiões, 72 tarifas e 201 usuários. |
| MOD-03 | [mod-03-contagem-02.png](mod-03-contagem-02.png) | Parte final da contagem das 21 tabelas selecionadas. |
| MOD-03 | [mod-03-consulta-contagem.png](mod-03-consulta-contagem.png) | SQL da consulta de contagem; tb_municipality não faz parte dessa seleção. |
| MOD-02 | [mod-02-pks-fks-01.png](mod-02-pks-fks-01.png) a [mod-02-pks-fks-06.png](mod-02-pks-fks-06.png) | Constraints do schema public (PK, FK e UNIQUE), em seis capturas sequenciais com 116 linhas. |
| MOD-04 | [mod-04-rpa-execucao-github-actions.png](mod-04-rpa-execucao-github-actions.png) | Execução #44 do RPA no GitHub Actions, concluída com sucesso. |
| MOD-04 | [mod-04-rpa-log-execucao.png](mod-04-rpa-log-execucao.png) | Log da execução: extração, validação, transformação, carga e transação confirmada com COMMIT. |
| MOD-06 | [mod-06-view-consumo-diario.png](mod-06-view-consumo-diario.png) | Resultado da view `vw_ft_consumption_daily`, construída com CTE. |
| MOD-07 | [mod-07-view-ranking-propriedades.png](mod-07-view-ranking-propriedades.png) | Rankings de eficiência e custo em `vw_ft_property_ranking`. |
| MOD-07 | [mod-07-view-variacao-mensal.png](mod-07-view-variacao-mensal.png) | Variação mensal com `LAG()` em `vw_ft_monthly_variation`. |
| MOD-08 | [mod-08-functions-01.png](mod-08-functions-01.png) e [mod-08-functions-02.png](mod-08-functions-02.png) | Lista de Functions do schema public, incluindo as Functions de auditoria `fn_log_*`. |
| MOD-09 | [mod-09-chamada-sp-change-region-rate.png](mod-09-chamada-sp-change-region-rate.png) | Chamada de `sp_change_region_rate`. |
| MOD-09 | [mod-09-tarifa-encerrada-e-nova.png](mod-09-tarifa-encerrada-e-nova.png) | Tarifa anterior encerrada e nova tarifa registrada, resultado da chamada. |
| MOD-10 | [mod-10-triggers-01.png](mod-10-triggers-01.png) e [mod-10-triggers-02.png](mod-10-triggers-02.png) | Os 21 triggers `trg_log_*` e as tabelas a que pertencem. |
| MOD-10 | [mod-10-log-auditoria-tarifa.png](mod-10-log-auditoria-tarifa.png) | Log da tarifa 5: INSERT e dois UPDATE, com `executed_by` e `log_description`. |
| MOD-11 | [mod-11-explain-analyze.png](mod-11-explain-analyze.png) | `EXPLAIN (ANALYZE, BUFFERS)` sobre `gold.dm_property`; em volume pequeno o plano é Seq Scan. |
| MOD-12 | [mod-12-catalogo-tb-user.png](mod-12-catalogo-tb-user.png) | Catálogo de `tb_user` com tipo, regra de negócio e nível de acesso. |

## Backup e recuperação — MOD-13

A [evidência do teste local concluído](../backup-recuperacao/resultado-backup.png) confirma `SUCCESS`, 47 tabelas e contagens corretas. O [log da restauração](../backup-recuperacao/resultado-restauracao.txt) apresenta as comparações individuais. A captura do workflow #121 registra apenas o job pulado; o resultado de sucesso é comprovado pelo teste local.

## Contagens — MOD-03

Os dois prints de resultado mostram 1.960 registros nas 21 tabelas selecionadas pela consulta enviada, acima do mínimo de 500. Essa consulta não inclui `tb_municipality`. A carga inicial completa documentada em [dataload.md](../../dataload.md) tem 2.331 registros em 22 tabelas, incluindo os 371 municípios.

## Alcance das evidências

O inventário de tabelas apoia a comprovação da existência das estruturas. A análise de normalização, PKs, FKs e cardinalidades está nos scripts, diagramas e justificativas dos requisitos. O MOD-14 mantém suas evidências de código, sem print, conforme definido para a entrega.
