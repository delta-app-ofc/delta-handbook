# Hábitos: cadastro, água estimada e custo

## Objetivo e escopo

Explicar o `HabitsAgent` e suas ferramentas. Fontes: `app/tools/habits/`, `app/agents/habits.py`, `app/data/db_postgres.py` e `app/tools/charts.py`.

O agente de hábitos é liberado para contas residenciais. O usuário fica preso às ferramentas. Consultas, cadastro e cenários são operações distintas: simular não cadastra e listar não satisfaz um pedido explícito de cadastro.

## Catálogo e operações

| Hábito canônico | Litros de referência por ocorrência |
| --- | --- |
| BANHO LONGO | 80 |
| LAVAR QUINTAL | 150 |
| LAVAR ROUPA | 100 |
| REGAR PLANTAS | 15 |
| LAVAR CARRO | 200 |
| LAVAR LOUÇA | 20 |

Esses números são constantes do projeto, **não medições do usuário**. `names.py` resolve variações de escrita; ambiguidade devolve opções e pede esclarecimento.

`list_habits` lista frequência/dias; `get_habits_by_day` aceita dias completos ou abreviados em português. `create_habit` recebe nome, frequência e, opcionalmente, dias e horários. Sem frequência, usa o número de dias distintos; sem ambos, devolve `needs_frequency`.

Dias são normalizados e deduplicados. Mais dias que frequência pede esclarecimento. Horários exigem início e fim, ambos válidos, com fim posterior ao início. O SQL `fn_create_user_habit` aplica as regras de persistência/conflito; repetir hábito no mesmo dia/horário pode retornar `conflict`. Nomes/argumentos inválidos não devem ser apresentados como cadastro concluído.

O agente só confirma cadastro quando o retorno é `status=ok`. Falha de banco retorna mensagem segura; não é confirmação de gravação.

## Momento da escrita e Juiz

A ferramenta chama `db_postgres.create_habit`, que executa `fn_create_user_habit` dentro da transação do cursor e faz commit ao concluir. **Essa escrita ocorre durante a execução do especialista, antes da avaliação do Juiz.**

Na revisão, `HabitsAgent.run` remove `create_habit` da lista de ferramentas. Isso impede repetir o cadastro nessa passada, mas não existe rollback ligado à rejeição posterior do texto. `persist_session=False` controla histórico da conversa e não torna o console ou os agentes somente leitura.

## Estimativas de litros e reais

`estimate_habit_water_impact` calcula litros de referência por frequência. `estimate_habit_water_cost` aceita frequência numérica ou `frequency_text` e litros por ocorrência informados pelo usuário, quando existirem. A interpretação textual reconhece frequências semanais e expressões diárias; não converte periodicidade mensal/anual automaticamente.

O cálculo monetário usa `Decimal`, com arredondamento de reais em duas casas, meia para cima:

```text
litros/semana = litros/ocorrência × vezes/semana
litros/mês = litros/semana × 4,33
m³/mês = litros/mês ÷ 1000
custo/mês = m³/mês × tarifa de água por m³
```

A tarifa vem da região/classificação do imóvel e da vigência na data da consulta. Sem tarifa ou imóvel aplicável, a ferramenta devolve só litros, com `rate_unavailable` ou `property_not_found`. Erro de consulta é `error`, não custo zero.

É custo estimado **da água desse hábito**, sem representar conta completa, medição do hidrômetro ou economia garantida. Não acrescenta esgoto, cobrança mínima ou regras tarifárias que não constem no cálculo.

## Hábitos em previsão e vazamento

`get_habit_baseline` no agente de previsão soma referências ou `estimated_liters` cadastrados. Esse resumo contextualiza o consumo e **não entra automaticamente no cálculo da projeção**. `get_habit_windows` no agente de vazamento compara dias/horários; coincidência não prova nem afasta vazamento.

## Clima e gráficos

`get_weather_history` consulta localização SQL e `weather_daily` no MongoDB, com intervalo limitado de 1 a 30 dias. Resume temperaturas, chuva e condição a partir de `hours`. Não consulta Tomorrow.io em tempo real nem prevê o clima futuro.

Gráficos de hábitos derivam dos outputs, sem converter médias em medições. Testes relacionados: `test_habit_create.py`, `test_habit_cost.py`, `test_habit_simulation.py` e `test_habits_in_forecast_and_leak.py`.

## Código relacionado

- [app/tools/habits/tools.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/tools/habits/tools.py)
- [app/tools/habits/calculations.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/tools/habits/calculations.py)
- [app/agents/habits.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/agents/habits.py)
