# Implementação: Agentes Especializados com LangChain

## Objetivo

Implementar os agentes especializados do Delta — Consumo, Previsão, Vazamento, Hábitos e RAG — usando **LangChain** para estruturar o ciclo de raciocínio do modelo de IA com ferramentas (tools) que acessam dados reais.

## Contexto

Cada agente sabe responder um tipo específico de pergunta. Isso é uma decisão arquitetural importante: um único agente genérico tenderia a "misturar" conceitos e dar respostas menos precisas. Separar por especialidade permite prompts mais focados e ferramentas específicas.

O motor compartilhado é o `_runtime.py` — um laço de tool-calling simples que funciona sem LangGraph e serve de base para todos os agentes.

---

## Motor compartilhado: `app/agents/_runtime.py`

### Como funciona o loop de tool-calling

```
1. LLM recebe: system_prompt + pergunta
2. LLM decide: responder diretamente OU chamar uma tool
3. Se chamar tool:
   a. Executa a tool com os argumentos fornecidos
   b. Adiciona o resultado ao histórico
   c. Volta ao passo 2 (LLM decide de novo)
4. Quando LLM responde diretamente → retorna AgentResult
```

```python
@dataclass
class AgentResult:
    response: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    chart_data: dict | None = None  # gráfico Plotly, quando gerado
    sources: list[str] = field(default_factory=list)
```

`ToolCall` registra o nome da tool, os argumentos usados e o resultado — usado pelo Agente Juiz para verificar se a resposta é coerente com os dados consultados.

---

## Agente de Previsão — `app/agents/forecast.py`

**Pergunta típica:** "Quanto vou gastar este mês?" ou "Vou ultrapassar minha meta?"

### Tools disponíveis

| Tool | O que faz | Fonte |
|------|-----------|-------|
| `get_consumption_history` | Busca histórico recente de consumo | MongoDB residencial / PostgreSQL organizacional |
| `get_last_bill` | Última conta de água (valor e consumo) | PostgreSQL |
| `get_region_rate` | Tarifa da região do usuário | PostgreSQL |
| `calculate_forecast` | Calcula previsão determinística | cálculo interno |

### Gráfico gerado

Após a execução, o agente constrói automaticamente um gráfico de linha combinando histórico + projeção:

```python
fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=values, name="Histórico"))
fig.add_trace(go.Scatter(x=proj_dates, y=proj_values, name="Projeção",
                         line={"dash": "dot"}))
```

O resultado é serializado como `fig.to_dict()` — um dicionário JSON que o frontend renderiza com `Plotly.newPlot()`. Nenhuma imagem é gerada no servidor.

---

## Agente de Vazamento — `app/agents/leak.py`

**Pergunta típica:** "Existe algum indício de vazamento?" ou "Meu consumo está anormal?"

### Importante: o que este agente FAZ e NÃO FAZ

O agente de vazamento **não detecta** vazamentos — ele **lê e explica** o que o motor de regras já calculou.

```
delta-business-rules (outro repositório)
  └── motor de detecção (regras + EWMA)
       ├── consumption_summary.anomaly_detected = true/false
       └── alerts_history → registros de alertas

delta-artificial-intelligence (este repositório)
  └── LeakAgent → lê esses dados e explica em linguagem natural
```

O motor de detecção usa regras explicáveis (fluxo contínuo, consumo de madrugada, desvio da baseline) sem modelo de ML. O agente de IA só lê o resultado final.

### Tools disponíveis

| Tool | O que faz |
|------|-----------|
| `get_anomalous_windows` | Lê janelas já sinalizadas como anômalas no período |
| `get_alerts_history` | Lista alertas históricos do usuário |
| `summarize_anomalous_windows` | Resume janelas temporais com consumo atípico |

---

## Agente de Hábitos — `app/agents/habits.py`

**Pergunta típica:** "Com que frequência lavo roupa?" ou "Quais hábitos tenho na segunda-feira?"

### Tools disponíveis

| Tool | O que faz | Fonte |
|------|-----------|-------|
| `list_habits` | Lista hábitos com frequência e dias | PostgreSQL |
| `get_habits_by_day` | Filtra hábitos por dia da semana | PostgreSQL |
| `get_weather_history` | Histórico meteorológico por localização | MongoDB `weather_daily` |

O agente de hábitos inclui ferramentas de clima porque hábitos ao ar livre (regar plantas, lavar quintal, lavar carro) dependem do tempo.

### Gráfico gerado

O agente constrói um gráfico de barras horizontal com a frequência semanal de cada hábito:

```python
fig = go.Figure(
    go.Bar(
        x=freqs,        # frequência semanal
        y=names,        # nome do hábito
        orientation="h",
    )
)
```

A altura do gráfico se adapta ao número de hábitos: `height=max(250, 60 * len(habits))`.

---

## Prompts — `app/services/prompts.py`

Cada agente tem seu prompt de sistema definido aqui. Os prompts delimitam:
- o papel do agente ("Você é o agente de previsão do Delta...")
- o que ele pode e não pode fazer ("Nunca invente dados; use apenas o que as tools retornarem")
- o formato esperado da resposta (texto corrido, tabela Markdown quando listar itens)

Os identificadores (nomes de variáveis, funções) são em inglês; os prompts são em português.

---

## Modelos de IA — `app/services/llms.py`

Os papéis de modelo são selecionados por `LLM_PROVIDER`:

| Variável | Modelo padrão | Uso |
|----------|---------------|-----|
| `llm_especialista` | `OPENAI_MODEL=gpt-6-luna` por padrão; `GEMINI_MODEL` no modo Gemini | Agentes especializados |
| `llm_rapido` | Mesmo modelo OpenAI com raciocínio próprio; `GROQ_FAST_MODEL` no modo Gemini | Guarda, roteador, síntese, metadados e resumos |

Os modelos e parâmetros são configurados em `app/config.py`; veja [modelos](llm-models.md). O adaptador especialista permite fallback para Groq em falhas transitórias reconhecidas, quando habilitado e configurado. Isso oferece uma alternativa de provedor, sem garantir resposta se ambos falharem. `llm_gemini` é o cliente individual Gemini, sem fallback próprio.

---

## Testes — `tests/`

Os testes dos agentes usam `ScriptedChatModel` — um modelo fake que retorna respostas pré-definidas sem fazer chamadas reais à API de IA. Isso permite testar o fluxo completo (prompt → tool → resposta) sem custo e sem acesso à internet.

```python
def test_forecast_agent_runs():
    model = ScriptedChatModel([...])  # respostas fixas para o teste
    agent = ForecastAgent(user_id=1, llm=model)
    result = agent.run("Quanto vou gastar este mês?")
    assert result.response != ""
```

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seções "Responsabilidade dos Agentes" e "LangChain".

## Agente de Consumo

`ConsumptionAgent` está registrado no roteador. Soma registros, compara períodos, lista unidades autorizadas e encontra picos diários. O recorte temporal, a diferença entre ausência e zero e a autorização estão detalhados em [consumo](consumption-agent.md).

## Agente RAG

`RagAgent` recupera regras do produto com `search_knowledge_base` e práticas gerais por `search_external_knowledge`, vinculada ao perfil. Veja [recuperação documental](rag-retrieval.md) e [MCP](mcp-conhecimento-externo.md).

## Ferramentas adicionais

Além das consultas acima, previsão expõe elegibilidade, meta, baseline de hábitos, simulação percentual, troca de meta e cenários de investimento. Vazamento expõe `get_habit_windows` para contexto residencial. Hábitos expõe cadastro, estimativas de litros e custo. Os contratos completos estão em [previsões e simulações](previsoes-simulacoes.md) e [hábitos](habitos.md).

## Ciclo de ferramentas

`app/agents/_runtime.py` oferece `run_agent`: recebe modelo, prompt, ferramentas e pergunta; vincula ferramentas com `bind_tools`; chama o modelo; executa as ferramentas solicitadas; acrescenta `AIMessage`/`ToolMessage` e repete até obter texto. O limite padrão é seis iterações; depois pede resposta final sem novas ferramentas.

`AgentResult` contém `response`, `tool_calls`, `chart_data` e `sources`. Cada `ToolCall` registra nome, entrada e output efetivo. O runtime remove chaves `user_id` do output apresentado ao modelo; a autorização já está aplicada na construção das ferramentas.

Ferramentas são executadas pela aplicação. O modelo escolhe entre operações expostas, mas não deve definir o usuário confiável nem calcular números que as funções determinísticas retornam.

## Prompts, gráficos e revisão

`app/services/prompts.py` delimita papéis e incorpora regras do perfil. Ter texto de prompt para um papel não o torna um agente registrado.

Os gráficos são construídos em `app/tools/charts.py` a partir dos resultados das ferramentas e devolvidos como dicionários Plotly. Não são evidência independente de medição. Na composição multiagente, a saída usa o primeiro gráfico disponível.

O runtime aceita feedback e contexto de revisão em mensagens separadas da pergunta. O grafo preserva evidências anteriores para o [Juiz](agente-juiz.md). Hábitos retira `create_habit` da segunda execução; isso evita novo cadastro pela revisão, sem desfazer a escrita inicial.

## Código relacionado

- [app/agents/_runtime.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/agents/_runtime.py)
- [app/tools/leak/tools.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/tools/leak/tools.py)
