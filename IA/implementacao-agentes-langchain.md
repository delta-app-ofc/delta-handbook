# Implementação: Agentes Especializados com LangChain

## Objetivo

Implementar os agentes especializados do Delta — Previsão, Vazamento e Hábitos — usando **LangChain** para estruturar o ciclo de raciocínio do modelo de IA com ferramentas (tools) que acessam dados reais.

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
```

`ToolCall` registra o nome da tool, os argumentos usados e o resultado — útil para o Agente Juiz futuramente verificar se a resposta é coerente com os dados consultados.

---

## Agente de Previsão — `app/agents/forecast.py`

**Pergunta típica:** "Quanto vou gastar este mês?" ou "Vou ultrapassar minha meta?"

### Tools disponíveis

| Tool | O que faz | Fonte |
|------|-----------|-------|
| `get_consumption_history` | Busca histórico de consumo mensal | MongoDB |
| `get_last_water_bill` | Última conta de água (valor e consumo) | PostgreSQL |
| `get_tariff` | Tarifa da região do usuário | PostgreSQL |
| `calculate_forecast` | Calcula previsão determinística | cálculo interno |
| `simulate_consumption_change` *(em PR)* | Simula variação percentual do consumo diário; devolve litros, diferença e hipóteses | cálculo interno |
| `simulate_target_change` *(em PR)* | Compara o risco de passar da meta atual e de uma meta simulada | cálculo interno |
| `get_investment_scenarios` *(em PR)* | Cenários de investimento (aeradores, reúso, captação de chuva); só organização | PostgreSQL |
| `get_habit_baseline` *(em PR)* | Litros esperados dos hábitos cadastrados (contexto; fora da previsão); só residencial | PostgreSQL |

> Os nomes da tabela acima são os do código; `get_last_water_bill` e `get_tariff` aparecem no código como `get_last_bill` e `get_region_rate`.
> Com histórico diário, o gráfico é de linha (histórico + projeção); sem ele, mostra barras do mês (consumido, projeção e meta). Na simulação "e se", o gráfico compara cenário atual e simulado.

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
| `check_anomaly_status` | Verifica se há anomalia ativa na última janela |
| `get_alerts_history` | Lista alertas históricos do usuário |
| `summarize_anomalous_windows` | Resume janelas temporais com consumo atípico |
| `get_habit_windows` *(em PR)* | Hábitos cadastrados (dia e horário) para comparar com uma janela anômala; só contexto, só residencial |

---

## Agente de Hábitos — `app/agents/habits.py`

**Pergunta típica:** "Com que frequência lavo roupa?" ou "Quais hábitos tenho na segunda-feira?"

### Tools disponíveis

| Tool | O que faz | Fonte |
|------|-----------|-------|
| `list_habits` | Lista hábitos com frequência e dias | PostgreSQL |
| `get_habits_by_day` | Filtra hábitos por dia da semana | PostgreSQL |
| `get_realtime_weather` | Condições climáticas atuais | API Tomorrow.io |
| `create_habit` | Cadastra hábito; `days`, `start_time` e `end_time` opcionais; nome em linguagem natural | PostgreSQL (`fn_create_user_habit`) |
| `estimate_habit_water_impact` | Litros por ocorrência, semana e mês (referência) | cálculo interno |
| `estimate_habit_water_cost` *(em PR)* | Custo mensal em reais da água do hábito (cadastrado ou hipotético) com a tarifa do usuário | PostgreSQL + cálculo interno |

Regras do agente (em PR): simular não cadastra; cadastro só é confirmado quando o banco devolve o id gravado; na revisão do Juiz a tool `create_habit` é removida, então a gravação não se repete. Veja [`habitos-simulacao-e-saida-ao-usuario.md`](habitos-simulacao-e-saida-ao-usuario.md).

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

Em PR: os prompts de Consumo, Hábitos, Previsão e Vazamento recebem o bloco `_REGRA_LINGUAGEM_USUARIO` (nunca citar agentes, ferramentas, status internos, APIs, bancos ou erros técnicos; falar em linguagem comum e capitalizar nomes de hábitos). O prompt do RAG não recebe esse bloco.

---

## Modelos de IA — `app/services/llms.py`

Dois modelos configurados:

| Variável | Modelo padrão | Uso |
|----------|---------------|-----|
| `llm_gemini` | `gemini-2.5-flash` (fallback: `openai/gpt-oss-120b` via Groq) | Agentes especializados |
| `llm_rapido` | `openai/gpt-oss-20b` via Groq | Router, resumos, contexto |

Os modelos efetivos são lidos das variáveis de ambiente `GEMINI_MODEL`, `GROQ_SPECIALIST_MODEL` e `GROQ_FAST_MODEL`; os valores acima são os defaults definidos em `app/config.py`. O fallback para Groq garante que, se a cota do Gemini acabar ou o modelo estiver indisponível, a aplicação continua funcionando com outro provedor.

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
