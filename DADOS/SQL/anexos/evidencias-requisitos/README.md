# Evidências visuais dos requisitos de Modelagem de Dados

Objetivo: reunir as 13 capturas enviadas para comprovar consultas e resultados do PostgreSQL. As capturas originais foram preservadas, incluindo as três versões da consulta de Procedures.

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

## Backup e recuperação — MOD-13

A [evidência do teste local concluído](../backup-recuperacao/resultado-backup.png) confirma `SUCCESS`, 47 tabelas e contagens corretas. O [log da restauração](../backup-recuperacao/resultado-restauracao.txt) apresenta as comparações individuais. A captura do workflow #121 registra apenas o job pulado; o resultado de sucesso é comprovado pelo teste local.

## Contagens — MOD-03

Os dois prints de resultado mostram 1.960 registros nas 21 tabelas selecionadas pela consulta enviada, acima do mínimo de 500. Essa consulta não inclui `tb_municipality`. A carga inicial completa documentada em [dataload.md](../../dataload.md) tem 2.331 registros em 22 tabelas, incluindo os 371 municípios.

## Alcance das evidências

O inventário de tabelas apoia a comprovação da existência das estruturas. A análise de normalização, PKs, FKs e cardinalidades está nos scripts, diagramas e justificativas dos requisitos. O MOD-14 mantém suas evidências de código, sem print, conforme definido para a entrega.
