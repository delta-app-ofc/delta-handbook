# Previsões, metas e simulações

## Objetivo

Descrever as ferramentas de `ForecastAgent` e os cálculos determinísticos da `main` de IA `f6f3d8c` (02/11/2026). Fontes: `app/tools/forecast/`, `app/tools/simulation/calculations.py`, `app/data/db_postgres.py` e `app/tools/charts.py`.

O LLM escolhe ferramentas e explica saídas. Totais, médias, projeção, comparação de metas e cenários são calculados em Python. Não são previsões feitas numericamente pelo modelo de linguagem.

## Fontes e elegibilidade

O caminho residencial consulta cadastro, última conta e tarifa no SQL, histórico de janelas no MongoDB e meta em preferências do app. O organizacional resolve unidades autorizadas, usa dados consolidados no PostgreSQL, último período faturado e tarifa efetiva registrada para o recorte. Nome de unidade ambíguo pede esclarecimento antes da análise.

`check_can_estimate` e `calculate_forecast` verificam elegibilidade residencial ou organizacional. Sem cadastro suficiente, a previsão retorna `insufficient_data` e não calcula. Isso não bloqueia o agente de consumo observado, cuja finalidade é outra.

As ferramentas expostas são `check_can_estimate`, `get_last_bill`, `get_consumption_history`, `get_daily_target`, `get_region_rate`, `calculate_forecast`, `get_habit_baseline`, `simulate_consumption_change`, `simulate_target_change` e `get_investment_scenarios`.

## Projeção e estimativa de conta

`calculations.py` agrega histórico em série diária. Considera histórico suficiente com pelo menos **sete datas com registros**. A média móvel recorta os últimos 14 dias e divide a soma pelo número de dias corridos entre a primeira e a última data disponíveis no recorte (`span`), não pela quantidade de datas com leitura. Lacunas internas afetam essa média. Esse denominador difere da média do agente de consumo, que usa somente dias com registro. Não há comprovação de cobertura contínua por esse cálculo.

A projeção mensal combina o consumo registrado no mês até a referência temporal e a média diária aplicada aos dias restantes. A tendência divide as datas observadas em duas partes, requer pelo menos seis datas e considera estável uma variação absoluta abaixo de 5%.

Com histórico suficiente e tarifa, estima valor com volume projetado em m³ multiplicado pela tarifa. Sem histórico suficiente **ou sem tarifa**, usa a última conta como referência quando ela existe (`base=last_bill`); sem ela, a estimativa de conta pode ser nula. Não se deve apresentar esse fallback como cálculo atualizado pela tarifa.

Meta diária é convertida em meta mensal pelo número de dias do mês e comparada à projeção. Sem meta, o risco não é avaliável. A resposta deve indicar fonte, hipóteses, falta de dados e que projeção não é certeza ou fatura oficial.

## Cenários de mudança

| Ferramenta | Hipótese | Efeito |
| --- | --- | --- |
| `simulate_consumption_change` | Variação percentual da média diária, aplicada uniformemente por um número de dias (padrão 30). Negativo reduz; positivo aumenta. | Retorna base, cenário e diferença em litros. Não altera registros. |
| `simulate_target_change` | Nova meta diária positiva, mantendo a projeção atual do mês. | Compara risco com meta atual e simulada; não muda a preferência cadastrada. |
| `get_habit_baseline` | Litros estimados de hábitos residenciais cadastrados. | Contexto de referência; não modifica a projeção calculada. |
| `get_investment_scenarios` | Cenários cadastrados para organização ou catálogo geral. | Exibe investimento, redução, economia anual e retorno cadastrados; pode acrescentar litros anuais estimados pela média diária. |

Simulações de consumo/meta exigem histórico suficiente; sem ele, retornam `insufficient_data`. A mudança percentual não modela sazonalidade ou clima. A troca de meta não muda consumo: muda somente a comparação.

Cenários de investimento são organizacionais. O código lê `tb_investment_scenario`, incluindo catálogo geral e organizações vinculadas ao usuário. Valores e prazo de retorno do cadastro não comprovam economia futura nem viabilidade financeira; a IA deve apresentá-los como referências. Não há contratação ou gravação de investimento nessa ferramenta.

Para litros e custo de um hábito hipotético, use as ferramentas descritas em [hábitos](habitos.md); elas não exigem criar o hábito.

## Gráficos e verificação

O gráfico de previsão é construído a partir dos resultados de ferramentas, com séries de histórico/projeção. Não é fonte independente para o Juiz.

Testes versionados incluem `test_forecast_calculations.py`, `test_forecast_sources.py`, `test_forecast_chart.py`, `test_consumption_simulation.py`, `test_goals_and_investments.py` e `test_habits_in_forecast_and_leak.py`. Validar com dados reais exige conferir schema, views, carga do ETL, tarifas e permissão do usuário; um teste isolado não comprova essas condições.

## Fontes da implementação revisada

- [app/tools/forecast/tools.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/forecast/tools.py)
- [app/tools/forecast/calculations.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/forecast/calculations.py)
- [app/tools/simulation/calculations.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/simulation/calculations.py)
