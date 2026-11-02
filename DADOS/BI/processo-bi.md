# Processo de Business Intelligence — Delta v3

Este documento explica como transformar os registros do Delta em informações para acompanhar o consumo de água e o atendimento digital. A referência de implementação é a pasta `v3` do repositório `delta-business-intelligence`.

## 1. Pergunta de gestão

Onde concentrar esforços para reduzir excessos de consumo e melhorar a continuidade e a qualidade do serviço?

A análise relaciona quatro perspectivas: clima e consumo, disponibilidade e alertas, metas e tarifas, e atendimento por IA. O objetivo é apoiar a investigação e a comparação entre períodos, sem interpretar associação estatística como causa ou apresentar dados incompletos como resultados medidos.

## 2. Conhecer a base e o grão

| Origem | Informação utilizada | Unidade de observação |
| --- | --- | --- |
| PostgreSQL | Dispositivo, imóvel, localização, classificação, tarifa e vínculo usuário/imóvel | Cadastro ou vigência |
| MongoDB `consumption_summary` | Litros e início/fim de cada janela | Dispositivo/janela |
| MongoDB `device_status` | Período monitorado e intervalos indisponíveis | Dispositivo e histórico de disponibilidade |
| MongoDB `weather_daily` | Observações de clima em `hours[]` | Localização/dia, expandido para hora |
| MongoDB `alerts_history` | Tipo e data do alerta | Alerta |
| MongoDB `user_preferences` | Meta diária atual | Usuário |
| MongoDB `observability_requests` | Resultado global e duração dos agentes | Requisição, com mapa `agents_ms` |

## 3. Preparar e conferir os dados

O tratamento preserva o significado das informações antes de agregar medidas:

1. **Identificar a origem e o período.** Conferir o corte comum do lote e a cobertura disponível antes de comparar indicadores.
2. **Resolver duplicatas pelo grão.** Escolher o registro mais recente para a chave da fonte, sem confundir dois horários, duas requisições ou dois agentes com duplicação.
3. **Conferir valores e datas.** Janelas com volume inválido, fim não posterior ao início ou leitura anterior à instalação são descartadas antes do cálculo. Registros sem relacionamento também são descartados. Cada descarte gera contagem e amostra no log; não altera o banco de origem.
4. **Preservar desconhecidos.** Ausência de consumo, duração, coordenada ou disponibilidade não vira zero. As demais validações, incluindo coordenadas, sobreposição de janelas, vigências e reconciliação dos contadores, continuam ativas.

Os descartes alteram a população analisada e devem ser considerados na interpretação. O mesmo conjunto pode ser avaliado em mais de uma saída; não somar mensagens repetidas de descarte como se fossem registros distintos. Uma contagem alta de dispositivos fora do contexto pede conferência do cadastro, do recorte SP e do lote SQL, além da origem dos eventos.


## 4. Produzir a base final

A Gold v3 materializa oito tabelas analíticas, além do vínculo técnico privado `tb_user_key`. Este vínculo não é um nono fato do dashboard.

| Tabela Gold | Grão | Uso |
| --- | --- | --- |
| `tb_weather_hourly` | Cidade/estado/hora | Clima e cruzamento com consumo |
| `tb_consumption_hourly` | Imóvel/hora | Volume, mapa, perfil horário e grupo tarifário |
| `tb_alert_count_daily` | Dia/dispositivo/tipo | Distribuição e evolução de alertas |
| `tb_tariff_validity` | Região/classificação/início de vigência | Contexto tarifário |
| `tb_target_compliance_daily` | Usuário pseudonimizado/dia elegível | Consumo, meta e excedente |
| `tb_device_availability_daily` | Dispositivo/dia local | Disponibilidade observada |
| `tb_ai_request` | `request_id` | Resultado global e duração total da requisição |
| `tb_agent_call` | `request_id`/agente | Tempo acumulado do agente na requisição |

`tb_agent_call` mantém o nome técnico, mas não representa cada chamada de modelo. Uma requisição pode envolver vários agentes ou nenhum. Por isso, a contagem geral vem de `tb_ai_request`; contar linhas depois de expandir `agents_ms` multiplicaria requisições com vários agentes.

## 5. Calcular e interpretar os indicadores

O [catálogo BI01–BI18](indicadores-bi.md) registra os conceitos de leitura. Antes de interpretar um resultado, conferir período, filtros, população elegível, unidade e denominador.

- **Consumo:** volumes são repartidos pela duração real das janelas e agregados por imóvel/hora. Uma janela não precisa ter cinco minutos.
- **Metas:** a comparação usa a meta diária atual e somente dias com cobertura completa e meta positiva; não reconstrói metas históricas.
- **Disponibilidade:** usa o período efetivamente monitorado, sem preencher lacunas como online.
- **Tarifas:** preservam classe e vigência. O recorte extraído depende das regiões com endereço cadastrado em SP.
- **IA:** `total_ms` é duração total da requisição; `agents_ms` é duração acumulada de cada agente; `by_component.*.model_ms` mede chamadas de modelo. São medidas diferentes.

No BI17, `outcome=error` é um resultado da requisição inteira. A taxa por participante não permite concluir que aquele agente causou o erro. Resultados `partial` e `rejected` permanecem separados de `error` e integram o denominador.

## 6. Apresentar e revisar

O dashboard e o relatório devem usar a mesma definição de KPI e a mesma base final. Títulos, unidades e legendas precisam acompanhar mudanças nas fórmulas. Os filtros devem respeitar as dimensões realmente disponíveis: as requisições de IA não recebem uma localização de usuário inventada.

O relatório gerencial apresenta a base, o problema, as decisões de tratamento, os KPIs e os limites de interpretação. Gráficos mostram comparações e evolução; cards resumem medidas; boxplots descrevem distribuições; o mapa utiliza as coordenadas cadastrais. Espaços reservados para evidências não comprovam uma execução.

Na entrega, anexar o arquivo Databricks ou referência ao código, o relatório e os links específicos com acesso dos professores. As evidências devem mostrar fonte da aplicação, configuração do job, histórico/status e resultado gerado.

## 7. Automação e rastreabilidade

A execução automatiza leitura, preparação, cálculo e gravação. O transporte v3 possui dez tabelas Mongo e quatro SQL em um manifesto v5. O job SQL mantém o contrato 2. No Databricks, a importação precede a Gold; o sucesso do envio não comprova a conclusão do cálculo.

A preparação tenta as saídas previstas e registra falhas. Se alguma falhar, a barreira final impede iniciar a publicação das tabelas analíticas; ela não transforma um resultado parcial em carga completa. As gravações finais não constituem uma única transação entre tabelas: conferir o lote comum e os estados da execução também após falhas de escrita.

Os códigos são a referência operacional. A existência da v3 local não comprova que os jobs, o dashboard ou o relatório publicado já foram atualizados. É necessário validar a execução completa e a correspondência das consultas antes de apresentar resultados como atuais.

## Referências

- [Indicadores da v3](indicadores-bi.md).
- [Engenharia de dados](../engenharia-dados.md).
- [Datamart PostgreSQL — estrutura distinta](../SQL/camada-bi.md).
- Implementação: `delta-business-intelligence/v3`, especialmente `gold/gold_bi.py` e `gold/CONSULTAS-DASHBOARD.sql`.
- Relatório: repositório `delta-bi-management-report`.

Atualização: 02/11/2026.
