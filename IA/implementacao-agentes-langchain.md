# Agentes especialistas e runtime LangChain

## Objetivo

Descrever o contrato compartilhado dos agentes implementados na `main` de IA `f6f3d8c`, revisada em 02/11/2026. O grafo e o console usam as mesmas classes; rodar uma classe diretamente não aplica automaticamente todas as etapas de segurança do chat.

## Ciclo de ferramentas

`app/agents/_runtime.py` oferece `run_agent`: recebe modelo, prompt, ferramentas e pergunta; vincula ferramentas com `bind_tools`; chama o modelo; executa as ferramentas solicitadas; acrescenta `AIMessage`/`ToolMessage` e repete até obter texto. O limite padrão é seis iterações; depois pede resposta final sem novas ferramentas.

`AgentResult` contém `response`, `tool_calls`, `chart_data` e `sources`. Cada `ToolCall` registra nome, entrada e output efetivo. O runtime remove chaves `user_id` do output apresentado ao modelo; a autorização já está aplicada na construção das ferramentas.

Ferramentas são executadas pela aplicação. O modelo escolhe entre operações expostas, mas não deve definir o usuário confiável nem calcular números que as funções determinísticas retornam.

## Especialistas e ferramentas

| Agente | Ferramentas implementadas |
| --- | --- |
| `ConsumptionAgent` | `get_consumption_summary`, `compare_consumption_periods`, `get_consumption_peaks`, `list_consumption_units`. |
| `ForecastAgent` | `check_can_estimate`, `get_last_bill`, `get_consumption_history`, `get_daily_target`, `get_region_rate`, `calculate_forecast`, `get_habit_baseline`, `simulate_consumption_change`, `simulate_target_change`, `get_investment_scenarios`. |
| `LeakAgent` | `get_anomalous_windows`, `get_alerts_history`, `summarize_anomalous_windows`, `get_habit_windows`. |
| `HabitsAgent` | `list_habits`, `get_habits_by_day`, `create_habit`, `estimate_habit_water_impact`, `estimate_habit_water_cost`, `get_weather_history`. |
| `RagAgent` | `search_knowledge_base` e ferramenta externa vinculada ao perfil, `search_external_knowledge`. |

Consulte [consumo](consumption-agent.md), [previsões](previsoes-simulacoes.md), [hábitos](habitos.md), [RAG](rag-retrieval.md) e [MCP](mcp-conhecimento-externo.md).

## Vazamento: leitura e explicação dos sinais

O `LeakAgent` consulta janelas marcadas com `anomaly_detected` na telemetria e registros de `alerts_history` do app. `app/tools/leak/analysis.py` faz resumo descritivo; não cria um limiar ou motor de detecção. Esse motor pertence ao componente de regras de negócio.

A janela padrão é 30 dias. Lista vazia informa falta de indícios/alertas no recorte, sem garantir ausência de vazamento. Falha da fonte não equivale à ausência. Uma anomalia não comprova causa, diagnóstico ou envio de notificação.

`get_habit_windows` consulta dias e horários de hábitos somente para perfil residencial. Coincidência com uma janela é contexto possível; não descarta o sinal. Sem horário, só permite comparação por dia. No perfil organizacional, essa ferramenta retorna `not_applicable`; as ferramentas de janelas/alertas continuam filtradas pelo usuário e não oferecem seleção de unidade.

## Prompts, gráficos e revisão

`app/services/prompts.py` delimita papéis e incorpora regras do perfil. Ter texto de prompt para um papel não o torna um agente registrado.

Os gráficos são construídos em `app/tools/charts.py` a partir dos resultados das ferramentas e devolvidos como dicionários Plotly. Não são evidência independente de medição. Na composição multiagente, a saída usa o primeiro gráfico disponível.

O runtime aceita feedback e contexto de revisão em mensagens separadas da pergunta. O grafo preserva evidências anteriores para o [Juiz](agente-juiz.md). Hábitos retira `create_habit` da segunda execução; isso evita novo cadastro pela revisão, sem desfazer a escrita inicial.

## Modelos e verificação

`llm_especialista` usa o provedor selecionado em `LLM_PROVIDER`; `llm_rapido` atende guarda, roteador, síntese e metadados. Veja [modelos](llm-models.md).

Os testes `test_ci_consumption.py`, `test_ci_forecast.py`, `test_ci_leak.py`, `test_ci_habits.py`, `test_ci_rag.py` e `test_agent_runtime.py` verificam contratos com modelos e ferramentas substituídos. A suíte inclui outros testes de cálculo, autorização e fontes. Não se deve inferir qualidade semântica ou acesso remoto por esses resultados.

## Fontes da implementação revisada

- [app/agents/_runtime.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/agents/_runtime.py)
- [app/tools/leak/tools.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/tools/leak/tools.py)
