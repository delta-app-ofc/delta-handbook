# Camada de BI do PostgreSQL

Este documento descreve a implementação atual da camada analítica do Delta: de onde os dados vêm, como são transformados e como interpretar cada indicador que a API e a aplicação web consomem. O SQL é a fonte das fórmulas; o front apresenta os resultados e só agrega quando a consulta reúne mais de uma organização.

## Repositórios e fonte de verdade

- Implementação SQL: [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database), principalmente `datamart/` e `script-migration-indicadores.sql`.
- API de leitura: [delta-api-postgres](https://github.com/delta-app-ofc/delta-api-postgres), `AnalyticsRepository` e projeções de `modules/analytics/`.
- Web: [delta-web-app](https://github.com/delta-app-ofc/delta-web-app), serviços em `src/services/indicators.ts` e agregações em hooks de cada página.

Confira esses repositórios antes de alterar fórmulas. A view SQL define a regra analítica; formatação, seleção de período e agregação de resultados ficam na API ou no front conforme descrito abaixo. Uma view existente no branch de desenvolvimento não prova, por si só, que a migração correspondente já foi aplicada ao banco publicado.

## Fluxo de dados

```text
MongoDB (telemetria, alertas e estado dos dispositivos)
        │ bi_etl.py
        ▼
stage (espelho de entrada)
        │ procedures silver.sp_load_*
        ▼
silver (tipos, deduplicação e associação de device/property)
        │ procedures gold.sp_load_*
        ▼
gold (fatos e dimensões analíticas)
        │ views dw.vw_*
        ▼
API delta-api-postgres ──► web e mobile
```

Dados cadastrais e de referência que já estão no PostgreSQL, como unidades, organizações, metas e cenários, entram nas cargas silver/gold sem espelhamento pelo Mongo. As views de serviço `dw.vw_ft_*` leem o modelo gold; a view de trilha de auditoria lê `tb_log_region_rate` diretamente. O fluxo de ranking Redis é separado e não deve ser tratado como uma view desta camada.

### Grãos que afetam as fórmulas

| Objeto | Grão principal | Origem/transformação |
|---|---|---|
| `gold.ft_consumption_reading` | dispositivo × instante de leitura | `stage.consumption_summary`, resolvido por `tb_device.device_id`; conflito `(device_id, read_at)` é ignorado |
| `gold.ft_consumption_daily` | unidade × dia | soma dos volumes das leituras associadas à unidade naquele dia; custo calculado com a tarifa válida naquele dia |
| `gold.ft_water_bill_monthly` | pessoa × mês de fatura | faturas residenciais e dimensões de pessoa/data |
| `gold.ft_alert` | ocorrência de alerta | histórico de alertas tratado e associado às dimensões |
| `gold.dm_device_status` | dispositivo | estado mais recente carregado pela integração de status |
| `gold.ft_investment_scenario` | cenário de investimento | cópia dos valores cadastrados em `tb_investment_scenario`; a view de comparação não estima esses campos |

`volume_liters`/`consumption_liters` ficam em litros. A tarifa `m3_value` é aplicada como R$/m³: `litros / 1000 × tarifa`. O custo diário é arredondado a centavos na carga gold. Se não houver tarifa vigente para a classificação e a data, a junção lateral da carga não produz a linha diária; confirme a cobertura de tarifas ao investigar períodos ausentes.

## Views e definições dos indicadores

### Consumo diário — `dw.vw_ft_consumption_daily`

Retorna litros e custo por unidade/dia, além de:

- `running_total_liters`: soma acumulada desde o primeiro dia disponível para a unidade;
- `moving_avg_7d_liters`: média da linha atual e das até seis linhas anteriores.

**Interpretação:** a média é das últimas sete linhas/dias com registro, não necessariamente dos últimos sete dias corridos. Em dias sem telemetria não há linha com zero; portanto, lacunas fazem a janela cobrir mais de sete dias de calendário. O total acumulado também começa no histórico disponível, não em um ano civil específico.

### Variação mensal — `dw.vw_ft_monthly_variation`

Agrega litros por unidade e mês e usa `LAG(total_liters)` para obter a linha mensal observada anterior. A variação é:

```text
(consumo do mês − consumo da linha mensal observada anterior)
÷ consumo da linha mensal observada anterior × 100
```

O SQL arredonda a uma casa decimal. Se o valor anterior for zero ou inexistente, a variação é `NULL`. **`LAG` compara com o mês observado anterior, que pode não ser o mês de calendário imediatamente anterior se houver lacunas.** A mesma ressalva vale para `previous_month_liters` nas views mensais de unidade e organização.

### Indicadores mensais por unidade — `dw.vw_ft_property_monthly`

Uma linha por unidade e mês com consumo, custo, meta, variação, economia e sinalização de completude.

| Campo | Regra implementada | Observação |
|---|---|---|
| `total_liters` | soma de `gold.ft_consumption_daily.total_liters` no mês | Soma só os dias com fato; ausência de fato não vira zero. |
| `total_cost` | soma do custo diário já calculado com tarifa vigente | R$; não recalcula tarifa no front. |
| `days_with_data` | quantidade distinta de datas com fato | Não mede quantas leituras eram esperadas em cada dia. |
| `is_complete_month` | `days_with_data` maior ou igual ao número de dias do mês | Heurística baseada em presença de datas, não confirmação de cobertura de todos os dispositivos ou de horário de corte do ETL. |
| `liters_per_m2` | litros do mês ÷ área construída | Duas casas decimais; `NULL` quando área é nula ou zero. |
| `goal_pct` | litros do mês ÷ meta mensal em litros × 100 | Uma casa decimal; `NULL` sem meta. Em mês parcial compara o consumo acumulado até então com a meta mensal inteira, sem rateio pelos dias decorridos. |
| `daily_limit_liters` | meta mensal ÷ quantidade de dias do mês | Arredondado a litro; é uma média diária uniforme, não uma recomendação baseada no calendário restante. |
| `remaining_liters` | maior entre meta − consumo e zero | Nunca fica negativo; continua comparando com a meta mensal cheia em mês parcial. |
| `goal_status` | `OK` até 85%; `ATENCAO` acima de 85% até 100%; `CRITICO` acima de 100%; `SEM_META` sem percentual | Os limites se aplicam ao percentual não arredondado pelo SQL. |
| `variation_pct` | comparação percentual com a linha anterior do `LAG` | Só preenchida quando o mês está marcado completo e existe denominador diferente de zero; mês anterior pode ser não consecutivo. |
| `saved_liters` | maior entre litros do mês anterior e atual subtraídos, e zero | Só conta quando o mês atual está marcado completo. Se não houver mês anterior, `COALESCE` usa zero, resultando em zero para consumo não negativo. |
| `estimated_savings_value` | litros economizados × custo médio do mês em R$/m³ ÷ 1000 | Só em mês completo; custo médio é `total_cost ÷ total_liters × 1000`. É estimativa comparativa, não medição financeira independente. |

O status da meta não é uma previsão de fechamento do mês. Por exemplo, uma unidade pode estar abaixo de 85% no meio do mês e ultrapassar a meta depois.

### KPIs mensais da organização — `dw.vw_ft_organization_monthly_kpi`

Agrega por organização/mês as linhas disponíveis da view de unidade:

- litros, custo, litros anteriores, economia e litros poupados: soma;
- total de unidades: quantidade de linhas de unidade naquele mês;
- unidades dentro da meta, em atenção e críticas: contagem por `goal_status`;
- `avg_goal_pct`: média simples do percentual entre unidades com meta (percentuais nulos são ignorados), sem ponderar pela meta ou pelo consumo;
- `min_days_with_data`: menor quantidade de dias observada entre as unidades presentes;
- `is_complete_month`: `BOOL_AND` da completude das linhas de unidade presentes.

Variação percentual usa os totais atuais e anteriores da organização, apenas se `is_complete_month` for verdadeiro e o denominador não for zero. **A completude organizacional considera somente unidades que têm linha no mês.** Unidade sem fato no período não aparece no agrupamento; assim, a flag não garante que todas as unidades cadastradas nem todos os dispositivos tenham enviado dados.

Projeção simples:

```text
litros projetados = maior(total atual + (total atual − total anterior), 0)
custo projetado = litros projetados × (custo atual ÷ litros atuais)
```

O custo projetado usa o custo médio atual por litro. Não é modelo sazonal nem previsão estatística. Sem mês anterior, a fórmula substitui o anterior pelo valor atual e projeta o próprio consumo. Se litros atuais forem zero, o custo médio fica `NULL`.

### Monitoramento por hora — `dw.vw_ft_monitoring_hourly`

Agrupa leituras por organização, unidade, duração da janela de origem (`window_minutes`) e hora cheia (`DATE_TRUNC('hour', read_at)`). `total_liters` é a soma dos volumes no grupo, `avg_flow_lmin` é a média aritmética dos fluxos registrados (3 casas decimais) e `readings_count` é a quantidade de leituras. Não é interpolação: uma hora sem leituras não gera linha. Resultados de janelas diferentes permanecem separados.

### Status de dispositivos — `dw.vw_ft_device_status` e `dw.vw_ft_organization_device_summary`

- `is_online` é verdadeiro somente quando `connectivity_status`, sem distinção de maiúsculas, é `online` ou `connected`.
- `is_low_battery` é verdadeiro para bateria não nula menor ou igual a 20; bateria nula não é classificada como baixa.
- `devices_paired` conta dispositivos ativos; `devices_online` conta ativos cujo status foi mapeado como online; `devices_low_battery` conta ativos com bateria baixa.
- `properties_without_device` é o total de unidades da organização menos unidades distintas com pelo menos um dispositivo ativo.

O resumo depende da atualização da fonte `stage.device_status`/`gold.dm_device_status`. Status antigo pode produzir um KPI desatualizado; veja também `last_ping_at` e o horário da carga antes de interpretar como estado ao vivo.

### Alertas e vazamentos — `dw.vw_ft_alert` e `dw.vw_ft_leak`

`vw_ft_alert` expõe tipo, severidade, início, resolução e duração em minutos. A duração é a diferença entre `resolved_at` e `triggered_at`, dividida por 60; alerta ainda ativo tem duração nula nessa view.

`vw_ft_leak` filtra `alert_type = 'vazamento_continuo'`. A classificação é `ATIVO` sem `resolved_at`, caso contrário `RESOLVIDO`. Para cada alerta, a perda estimada soma `volume_liters` das leituras do mesmo dispositivo entre o início e a resolução (ou o horário atual para alerta ativo), inclusive nos extremos. O impacto em reais multiplica esses litros pelo custo médio histórico da unidade por m³.

**Limitação importante:** toda água medida durante o intervalo do alerta é tratada como perda. A view não subtrai consumo normal nem aplica uma vazão-base; `estimated_loss_liters` e `estimated_loss_cost` são estimativas-proxy e podem superestimar o vazamento. Alertas sobrepostos do mesmo dispositivo podem contar leituras mais de uma vez, uma vez em cada ocorrência.

### Impacto de investimentos — `dw.vw_ft_capex_comparison` e `dw.vw_ft_investment_impact`

`vw_ft_capex_comparison` apenas lê os valores de investimento, redução, economia anual e payback já cadastrados em `tb_investment_scenario`/gold e os ordena pelo payback. Esses valores não são derivados nesta view.

`vw_ft_investment_impact` calcula uma linha de base por organização usando a média do consumo mensal dos meses marcados completos multiplicada por 12. Para cada cenário aplicável:

```text
litros anuais poupados = linha de base anual × reduction_pct ÷ 100
caminhões-pipa equivalentes = litros poupados ÷ 10.000
meses de consumo familiar = litros poupados ÷ 18.000
```

Os equivalentes usam 10.000 L como capacidade de referência de um caminhão-pipa e 18.000 L como consumo mensal de referência de quatro pessoas (`4 × 150 L/dia × 30 dias`). A Embasa publica a estimativa nacional de 150 L por morador/dia e ressalta que o consumo varia por hábitos e condições econômicas ([fonte](https://www.ba.gov.br/comunicacao/2022/01/noticias/embasa-orienta-sobre-instalacao-de-reservatorio-para-prevenir-desabastecimento-em-imoveis)). Editais públicos usam caminhões-pipa de 10.000 L como especificação mínima, mas há veículos de outras capacidades ([exemplo municipal de 10.000 L](https://ribasdoriopardo.ms.gov.br/wp-content/uploads/2024/08/FLS.-213-a-214-RESOLUCAO-N2-65-SEINFRA-2024.pdf)). Portanto, os dois divisores são equivalências de referência, não constantes universais nem volumes físicos efetivamente transportados/consumidos. A linha de base só usa meses presentes e marcados completos, sem preencher meses ausentes com zero.

**Agregação na web:** quando uma conta tem mais de uma organização, os litros poupados por cenário são somados primeiro; a web divide esse total por 10.000 ou 18.000 para obter equivalências. Isso evita acumular o arredondamento das equivalências feitas separadamente por organização. Os litros fornecidos pelo SQL já são arredondados a litro por organização.

### ESG mensal — `dw.vw_ft_organization_esg`

`saved_liters_month` usa `saved_liters` da view de organização. `saved_liters_year_projection` multiplica o valor mensal por 12; caminhões-pipa e meses familiares dividem essa projeção por 10.000 e 18.000 e arredondam a uma casa decimal.

Isso é uma anualização do resultado de um mês fechado, não uma soma dos últimos doze meses nem uma previsão sazonal. Em um mês não completo, a economia mensal da view-base é zero e a projeção também será zero.

### Pesquisa e valores de referência de investimentos

Os cenários de investimento são registros de referência em `tb_investment_scenario`, copiados para `gold.ft_investment_scenario`. `dw.vw_ft_capex_comparison` apresenta os valores cadastrados e ordena pelo payback; não calcula preço de obra nem atualiza valores de mercado. A metodologia, fontes consultadas, valores carregados e limitações estão em [pesquisa de cenários de investimento](pesquisa-cenarios-investimento.md).

O campo financeiro estático usa a relação simples:

```text
payback em meses = investimento ÷ (economia anual cadastrada ÷ 12)
```

Exemplo: `R$ 75.000 ÷ (R$ 51.800 ÷ 12) = 17,3745...`, que arredondado a uma casa decimal dá **17,4 meses**. O dataload Swift informava 17,3; o valor foi corrigido para 17,4. Esse payback continua sendo uma premissa armazenada do cenário, independente do consumo medido da organização. Já `vw_ft_investment_impact` calcula litros evitados a partir do consumo observado e do percentual de redução do cenário. Não se deve interpretar o `annual_savings_value`/`payback_months` estático como uma previsão financeira personalizada.

### Rankings e distribuição

| View | Cálculo e ordenação | Escopo/limite |
|---|---|---|
| `vw_ft_property_ranking` | soma histórica de litros e custos; `liters_per_m2 = litros ÷ área`; `RANK` por menor L/m², `DENSE_RANK` por maior custo, `NTILE(4)` e `PERCENT_RANK` por L/m² | Sem filtro de mês. Exclui unidades sem área. Menor L/m² é tratado como melhor eficiência, embora unidades de usos/tamanhos diferentes possam não ser diretamente comparáveis. |
| `vw_ft_residential_efficiency_ranking` | ordena faturas pelo menor m³ por mês; `RANK` e `PERCENT_RANK` particionados pela data de referência | Mede menor volume faturado, não eficiência por pessoa ou área; pessoas/faturas ausentes não são estimadas. |
| `vw_ft_consumption_distribution` | mínimo, máximo, quartis contínuos e mediana sobre todos os fatos diários; `NTILE(5)` cria cinco grupos por volume | Distribuição global do conjunto carregado, não separada por organização ou mês. Empates podem fazer grupos terem tamanhos diferentes. |
| `vw_audit_history_chain` | CTE recursiva percorre `previous_log_id` e numera níveis | Trilha de auditoria, não métrica de consumo. |

Rankings de eficiência e de consumo têm sentidos distintos: menor L/m² pode ser classificado como maior eficiência, enquanto menor consumo faturado é apenas menor volume registrado naquele mês.

## Cálculos feitos depois da API

O front deve formatar indicadores e não substituir as regras SQL. Os hooks podem:

- escolher o mês mais recente disponível/fechado para apresentação;
- somar KPIs retornados para as organizações acessíveis à conta;
- contar ou resumir itens já calculados pelo banco;
- arredondar apenas para exibição.

Na tela de metas, o “potencial econômico anual” é a soma da economia estimada das unidades no mês selecionado multiplicada por 12. É uma anualização de um mês, não economia observada em doze meses. Na tela de investimentos, equivalências ambientais são derivadas do total de litros somados por cenário, como descrito acima.

## Atualização e migração

O `bi_etl.py` no repositório SQL extrai documentos do Mongo para `stage` e chama as cargas silver/gold. A view é recalculada pelo PostgreSQL quando consultada, mas seus fatos/dimensões só refletem o estado da última carga. O estado online, alertas, telemetria e indicadores não são automaticamente atualizados apenas porque a aplicação abriu uma página.

### Escopo do ETL e evidência de gravação

Na branch `feat/indicadores-views-medalhao`, o ETL Python carrega:

| Origem MongoDB | Banco/coleção | Destino PostgreSQL | Estratégia |
|---|---|---|---|
| Telemetria | `db_delta_telemetry.consumption_summary` | `stage.consumption_summary` | Busca incremental pela borda `window_started_at >= MAX(stage.window_started_at)`; `ON CONFLICT (mongo_id) DO NOTHING` torna a releitura idempotente. |
| Estado de dispositivos | `db_delta_telemetry.device_status` | `stage.device_status` | UPSERT por `mongo_id`, atualizando os campos de status. |
| Preferências | `db_delta_app.user_preferences` | `stage.user_preferences` | UPSERT por `mongo_id`, incluindo meta diária, notificações, horário silencioso e tema. |
| Alertas | `db_delta_app.alerts_history` | `stage.alerts_history` | UPSERT por `mongo_id`, permitindo atualizar resolução e severidade. |

Depois, `silver.sp_load()` trata e associa as linhas; `gold.sp_load()` atualiza dimensões e fatos; as views `dw` consultam a camada gold. `bi_etl.py` não escreve diretamente nas tabelas operacionais `public.tb_*`. Metas de unidade e cenários de investimento têm origem no PostgreSQL operacional, não nas coleções Mongo acima.

**Status da evidência:** leitura do código, presença de objetos no branch e testes offline demonstram que o fluxo foi implementado e que suas regras de idempotência foram verificadas com adaptadores simulados. Isso não demonstra uma execução recente contra os bancos hospedados. Até conferir o histórico do workflow, os logs de execução e as contagens Mongo/PostgreSQL no mesmo instante, não afirmar que os dados reais estão sendo gravados ou atualizados agora.

Na revisão de 03/11/2026, o ETL com carga de `device_status`, as views analíticas recentes e os objetos de metas/alertas estavam na branch `feat/indicadores-views-medalhao`, não na `main` observada. Portanto, os objetos encontrados na branch não comprovam que o banco publicado os recebeu. A sincronização de arquivos individuais com os agregadores SQL foi feita separadamente; compare cada camada antes de aplicar uma migração.

Para provar uma execução real sem expor credenciais, registre: URL/ambiente de destino (sem parâmetros secretos), commit/branch publicado, horário da execução, status dos jobs, contagens de documentos por coleção e contagens por `mongo_id` nos destinos `stage`, além do resultado das cargas Silver/Gold. Compare amostras por IDs e timestamps. Faça consultas somente de leitura; não rode o ETL manualmente em produção durante uma auditoria sem confirmar antes o destino e a política operacional.

As conexões Mongo usam `MONGODB_TELEMETRY_URI` e `MONGODB_APP_URI`; os nomes de banco usam `MONGO_DB_TELEMETRY` e `MONGO_DB_APP`. Se a conexão do Mongo de aplicação não estiver configurada no código/execução, preferências e alertas não são carregados. Configure esses valores como secrets do workflow e não os registre em logs ou documentação.

O workflow ETL observado na `main` roda de hora em hora e também tenta disparar uma sincronização do Redis ao concluir. Uma proposta local de cron a cada cinco minutos não está ativa até ser mergeada na branch padrão; antes de habilitar, confirme duração, concorrência, cota e carga que cada execução faz nos bancos. O estado e a atualização do ranking Redis pertencem ao fluxo Redis e devem ser verificados separadamente.

Para um banco vazio, siga a ordem documentada pelo `setup_db.py` no repositório SQL. Para banco existente, examine o `migrate_db.py` e `script-migration-indicadores.sql`, faça backup, confira o alvo e aplique a migração planejada; depois carregue silver/gold conforme o README do repositório. Não execute migração em produção como parte de uma revisão documental.

Antes de atribuir uma fórmula ao estado de produção, confirme se a migração que cria/recria a view foi aplicada nesse banco. O branch e o arquivo local são evidência do código-fonte, não evidência da versão em execução.

## Verificações recomendadas dos cálculos

Faça as conferências em banco descartável ou de teste, com dados determinísticos e rollback. Para cada fórmula, compare a saída da view com cálculo manual simples:

1. **Custo diário:** 1.500 L a R$ 8,00/m³ deve resultar em R$ 12,00 antes das regras de arredondamento.
2. **Variação:** 1.200 L contra 1.000 L resulta em +20%; contra zero ou sem observação anterior, a variação deve ser `NULL`.
3. **Meta:** meta de 1.000 L e consumo de 850 L resulta em 85% e `OK`; 1.000 L resulta em 100% e `ATENCAO`; acima disso, `CRITICO`.
4. **Meta diária:** meta mensal de 31.000 L em mês de 31 dias resulta em 1.000 L/dia.
5. **Projeção:** 1.200 L no mês contra 1.000 L na observação anterior projeta 1.400 L; redução projetada abaixo de zero fica limitada a zero.
6. **Impacto de cenário:** linha de base anual de 120.000 L e redução de 10% resulta em 12.000 L poupados/ano, 1,2 caminhões equivalentes e 0,7 mês familiar (`12.000 ÷ 18.000 = 0,666...`, uma casa decimal).
7. **Completude:** criar mês com uma data sem fato deve impedir a marcação de mês completo; testar separadamente uma unidade cadastrada sem nenhuma linha no mês, pois ela não participa do `BOOL_AND` organizacional.
8. **Vazamento:** usar intervalo conhecido de leituras para confirmar inclusão dos instantes inicial/final e demonstrar que leituras de consumo normal também entram na estimativa.

Esses exemplos verificam a aritmética e as regras declaradas. Não substituem a validação de qualidade/cobertura dos dados de origem, da execução do ETL ou da migração instalada.
