# Operação do Glue e Databricks

O pipeline de BI extrai dados do MongoDB e do PostgreSQL, organiza as camadas Bronze e Silver no S3 e envia um lote para processamento no Databricks. A versão v3 reúne esse fluxo em quatro jobs Glue sequenciais. No Databricks, o importador carrega a Silver e a tarefa Gold prepara as tabelas analíticas.

Os scripts e os parâmetros de referência estão em [`delta-business-intelligence/v3`](https://github.com/delta-app-ofc/delta-business-intelligence/tree/main/v3).

## Ordem de execução

```text
Glue: Bronze → SQL → Silver e exportação → envio
Databricks: import_silver → gold_bi
```

| Etapa | Script da v3 | Resultado |
| --- | --- | --- |
| Bronze | `bronze/bronze.py` | Ingestão das coleções de aplicação e telemetria em Delta no S3. |
| SQL | `sql/read_sql_database.py` | Quatro snapshots PostgreSQL e registro do lote SQL pronto. |
| Silver | `silver/silver.py` | Transformação, deduplicação e exportação de dez tabelas Mongo e quatro SQL em Parquet. |
| Envio | `transfer/send_files.py` | Upload para o volume Databricks e disparo do job pela API. |
| Importação | `transfer/import_silver_databricks.py` | Importação das tabelas do lote no Databricks. |
| Gold | `gold/gold_bi.py` | Processamento das tabelas analíticas usadas nos indicadores. |

## Preparar os jobs Glue

Publique os scripts em um local S3 acessível à role dos jobs e configure os jobs com os caminhos correspondentes. A configuração inicial descrita pela v3 é:

| Job sugerido | Runtime | Capacidade | Timeout | Retries | Execuções simultâneas |
| --- | --- | --- | --- | --- | --- |
| `delta-v3-bronze` | Spark | `G.1X`, 2 workers | 10 min | 0 | 1 |
| `delta-v3-sql` | Spark | `G.1X`, 2 workers | 10 min | 0 | 1 |
| `delta-v3-silver` | Spark | `G.1X`, 2 workers | 10 min | 0 | 1 |
| `delta-v3-send` | Python Shell 3.9 | 0,0625 DPU | 10 min | 0 | 1 |

Configure os três jobs Spark com o runtime Spark/Delta utilizado pelo projeto, `--datalake-formats=delta` e:

```text
--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog
```

O job de envio usa Python Shell, boto3 e requests. Disponibilize requests nesse ambiente, por exemplo pelo parâmetro `--additional-python-modules=requests`.

## Conexões e permissões

A Bronze usa `delta-app-atlas-connection` para `db_delta_app` e `delta-telemetry-atlas-connection` para `db_delta_telemetry`. Associe as duas conexões ao job e configure a rede para acesso ao Atlas. O job SQL usa a conexão PostgreSQL prevista em seu script.

O bucket de referência é `delta-ofc-datalake`. Os caminhos Bronze ficam em `mongo-database/bronze/app/` e `mongo-database/bronze/telemetry/`. Ao adotar outro bucket, atualize as referências nos scripts Bronze, SQL, Silver e envio em conjunto.

A role dos jobs precisa acessar as origens, os objetos S3 do pipeline, as propriedades do workflow e o segredo Databricks usado pelo envio. A autorização para o segredo é configurada no IAM e o acesso aos dados depende também da rede e das conexões associadas aos jobs.

## Montar o workflow

Crie um workflow sob demanda, com **Max concurrent runs = 1**. Configure um trigger inicial para a Bronze e triggers condicionais para iniciar o job seguinte quando o anterior atingir `SUCCEEDED`: Bronze, SQL, Silver e envio.

Os jobs SQL, Silver e envio usam `WORKFLOW_NAME` e `WORKFLOW_RUN_ID` para identificar a execução. Na carga SQL, configure `SQL_CHECK_ONLY=false`. A Silver aguarda `delta_sql_status=READY`, contrato SQL 2 e identificação da mesma execução antes de processar o lote.

Ao substituir uma versão, desative os triggers e agendamentos antigos que escrevem nos mesmos destinos. A execução fica concentrada no workflow escolhido para o lote.

## Preparar o Databricks

Crie um job com duas tarefas: `import_silver`, usando o importador da v3, e `gold_bi`, dependente do sucesso da importação. Configure **Max concurrent runs = 1** e os parâmetros `catalog`, `volume_path` e `batch_id`, repassados às tarefas correspondentes.

O envio Glue recebe:

```text
--DATABRICKS_SECRET_ID <identificador-do-segredo>
--DATABRICKS_JOB_ID <identificador-do-job>
--TARGET_CATALOG workspace
--VOLUME_PATH /Volumes/workspace/delta/delta_silver
--CHECK_ONLY false
```

No Secrets Manager, o segredo contém um JSON com `host` HTTPS e `token`. O host identifica o workspace e o token autoriza as operações de upload e execução previstas no script. `CHECK_ONLY=true` permite conferir a configuração de acesso, job e volume antes de enviar um lote.

## Identificar e acompanhar o lote

O lote usa um `batch_id` e um manifest versão 5. A Silver exporta as 14 tabelas, publica o manifest e registra `delta_export_status=READY`. O envio confere esses dados, carrega os Parquets e publica o manifest no volume Databricks por último.

Depois do upload, o script chama `jobs/run-now` com um token de idempotência derivado do workflow, execução, lote e Job ID. A resposta traz o `run_id`, registrado nos logs e nas propriedades `delta_databricks_status=SUBMITTED` e `delta_databricks_run_id`.

O job de envio termina após a aceitação da execução. Acompanhe a conclusão de `import_silver` e `gold_bi` no Databricks pelo `run_id`. O resultado completo do lote reúne o estado do workflow Glue e o estado das tarefas Databricks.

## Rotina de execução

1. Confirme a versão dos scripts dos jobs, o bucket e o Job ID Databricks configurado.
2. Inicie o workflow Glue e acompanhe os quatro jobs em sequência.
3. Consulte os logs do job que apresentar erro e as propriedades da execução para identificar a etapa e o lote.
4. Após o envio, abra a execução Databricks pelo `run_id` e acompanhe importação e Gold.
5. Com a Gold concluída, atualize ou consulte os datasets do dashboard definidos em `v3/gold/CONSULTAS-DASHBOARD.sql`.

Para retomar uma execução, consulte primeiro os registros do lote e os arquivos já publicados. Em especial, se a API aceitou o disparo Databricks, use o `run_id` registrado para localizar o processamento antes de reenviar. Isso mantém a recuperação associada ao lote correto.

## Publicar alterações no pipeline

Mantenha os contratos do lote alinhados entre Bronze, SQL, Silver, envio, importador e Gold. Publique os scripts relacionados em conjunto quando houver mudança no manifest ou nos schemas. A v3 usa manifest 5, dez tabelas Mongo e quatro SQL; o SQL permanece no contrato 2.

O GitHub Actions executa os comandos definidos no workflow do repositório BI. A atualização dos scripts dos jobs e os disparos Glue/Databricks seguem a configuração operacional descrita aqui. Registre na PR quais scripts e parâmetros precisam ser publicados para a nova versão.
