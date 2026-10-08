# Implementação: Orquestração com LangGraph

## Objetivo

Implementar o fluxo de orquestração multiagente usando **LangGraph** — uma biblioteca que modela a execução como um grafo de nós e arestas, onde cada nó é uma etapa do processamento.

## Contexto

Antes do LangGraph, cada requisição ia diretamente para um agente fixo. Com o LangGraph, o sistema decide dinamicamente qual(is) agente(s) deve(m) responder com base na intenção detectada na pergunta. Uma pergunta sobre hábitos vai para o HabitsAgent; uma análise cruzada de consumo + vazamento vai para dois agentes ao mesmo tempo.

---

## Estrutura do grafo

```
[context] → [route] → [execute] → [respond] → END
```

| Nó | Responsabilidade |
|----|-----------------|
| `context` | Carrega histórico recente (MongoDB) e memórias relevantes (Qdrant, quando necessário) |
| `route` | Classifica a intenção e escolhe os agentes via `llm_rapido` |
| `execute` | Instancia e executa cada agente selecionado |
| `respond` | Consolida as respostas em uma única saída |

---

## Estado compartilhado — `app/graph/state.py`

O LangGraph passa um dicionário de estado por todos os nós. Cada nó recebe o estado atual, processa e retorna o estado atualizado.

```python
class GraphState(_GraphStateRequired, total=False):
    # entrada
    user_id: int
    session_id: str
    question: str
    # contexto (preenchido por context_node)
    recent_messages: list[dict]
    relevant_memory: list[str]
    # decisão de roteamento (preenchido por route_node)
    intent: str
    complexity: str           # "simple" | "medium" | "complex"
    selected_agents: list[str]
    agent_used: str
    # resultados (preenchido por execute_node)
    agent_results: list[dict]
    warnings: list[str]
    # saída final (preenchida por respond_node)
    response: str
    chart_data: dict | None
```

`AgentOutput` é o contrato entre o nó de execução e o nó de resposta:

```python
class AgentOutput(BaseModel):
    agent: str
    status: Literal["success", "error"]
    answer: str
    chart_data: dict | None = None
    warnings: list[str] = []
```

---

## Nó 1: context — `app/graph/context.py`

Monta o contexto da pergunta antes do roteamento:

```python
def build_context(user_id: int, session_id: str, question: str) -> dict:
    recent = load_history_validated(user_id, session_id)  # MongoDB, sempre

    relevant = []
    if _needs_long_term_memory(question):  # só se a pergunta pede memória anterior
        relevant = search_memory(user_id, question)

    return {
        "recent_messages": recent[-6:],    # últimas 6 mensagens
        "relevant_memory": relevant,
    }
```

A busca de memória de longo prazo (Qdrant) só ocorre quando a pergunta contém palavras como "lembra", "antes", "semana passada". Isso evita ~500ms de latência em perguntas diretas.

---

## Nó 2: route — `app/graph/router.py`

Usa `llm_rapido` para classificar a intenção e escolher os agentes. O modelo recebe o histórico recente + a pergunta e retorna um JSON:

```json
{"intent": "habits_impact", "complexity": "medium", "agents": ["habits", "forecast"]}
```

### Parsing robusto do JSON

O LLM pode retornar texto antes ou depois do JSON. O parser tenta carregar o texto completo e, se falhar, extrai o primeiro `{...}` encontrado:

```python
try:
    data = json.loads(content)
except json.JSONDecodeError:
    start = content.find("{")
    end = content.rfind("}") + 1
    data = json.loads(content[start:end]) if start >= 0 and end > start else {}
```

### Registro de agentes

```python
AGENT_REGISTRY = {
    "forecast": "app.agents.forecast.ForecastAgent",
    "leak": "app.agents.leak.LeakAgent",
    "habits": "app.agents.habits.HabitsAgent",
}
```

O router filtra agentes desconhecidos — se o LLM inventar um nome, ele é ignorado silenciosamente.

---

## Nó 3: execute — `app/graph/workflow.py`

Itera sobre os agentes selecionados, instancia cada um com `load_agent` e executa:

```python
for name in selected:
    agent = load_agent(name, user_id)  # importação dinâmica via AGENT_REGISTRY
    internal = agent.run(question)
    output = AgentOutput(
        agent=name,
        status="success",
        answer=internal.response,
        chart_data=internal.chart_data,
    )
    results.append(output.model_dump())
```

Erros em um agente não derrubam os outros — o nó registra o erro em `warnings` e continua.

---

## Nó 4: respond — `app/graph/workflow.py`

Consolida os resultados:

- **0 agentes selecionados** → resposta padrão de escopo ("Posso ajudar com previsão, vazamentos ou hábitos.")
- **1 agente com sucesso** → retorna a resposta diretamente
- **Múltiplos agentes** → une as respostas com `---` como separador; prioriza o `chart_data` do primeiro agente que gerou gráfico

---

## Checkpointing com MemorySaver

```python
_memory = MemorySaver()
workflow = _graph.compile(checkpointer=_memory)
```

`MemorySaver` persiste o estado do grafo em memória, vinculado ao `thread_id = session_id`. Isso permite que o LangGraph retome uma conversa a partir do ponto onde parou — relevante quando o sistema for expandido com nós assíncronos ou retentativas.

---

## Inicialização e execução

```python
def run_workflow(user_id: int, session_id: str, question: str) -> GraphState:
    initial: GraphState = {
        "user_id": user_id,
        "session_id": session_id,
        "question": question,
        "response": "",
        ...
    }
    return workflow.invoke(
        initial,
        config={"configurable": {"thread_id": session_id}},
    )
```

O `thread_id` é obrigatório para o `MemorySaver` identificar qual sessão está sendo retomada.

---

## Fluxo completo de uma requisição

```
POST /chat {"user_id": 42, "message": "Quais meus hábitos afetam a conta?"}
  │
  ├─ validate_input() → ok
  │
  ├─ run_workflow()
  │    ├─ context: carrega últimas 6 mensagens do MongoDB
  │    ├─ route: llm_rapido → {"intent": "habits_impact",
  │    │                        "agents": ["habits", "forecast"]}
  │    ├─ execute: HabitsAgent.run() + ForecastAgent.run()
  │    └─ respond: une as duas respostas
  │
  ├─ validate_output() → ok
  ├─ append_turn() x2 → salva no MongoDB
  └─ return ChatResponse
```

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seções "LangGraph" e "Arquitetura Multiagente".
