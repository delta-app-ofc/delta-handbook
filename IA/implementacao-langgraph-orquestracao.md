# Implementação: Orquestração com LangGraph

## Objetivo

Implementar o fluxo de orquestração multiagente usando **LangGraph** — uma biblioteca que modela a execução como um grafo de nós e arestas, onde cada nó é uma etapa do processamento.

## Contexto

Antes do LangGraph, cada requisição ia diretamente para um agente fixo. Com o LangGraph, o sistema decide dinamicamente qual(is) agente(s) deve(m) responder com base na intenção detectada na pergunta. Uma pergunta sobre hábitos vai para o HabitsAgent; uma análise cruzada de consumo + vazamento vai para dois agentes — executados em sequência dentro do nó `execute`.

---

## Estrutura do grafo

```text
guardrail_input → prepare → execute → synthesize → respond → compose
       │             │                                      │
       └─ bloqueio ──┴─→ END                  sem candidata → output_guard → END
                                                            │ candidata
                                                            ▼
                                                          judge
                                                ┌───────────┼───────────┐
                                             approve     correct      reject
                                                ▼           ▼           ▼
                                             publish     revise       block
                                                │           │           │
                                                │        execute        │
                                                └────→ output_guard ←───┘
                                                            │
                                                           END
```

| Nó | Responsabilidade |
|----|-----------------|
| `context` | Carrega histórico recente (MongoDB) e memórias relevantes (Qdrant, quando necessário) |
| `route` | Classifica a intenção e escolhe os agentes via `llm_rapido` |
| `execute` | Instancia e executa cada agente selecionado |
| `respond` | Escolhe síntese, resposta disponível ou orientação fixa |
| `prepare` | Classifica segurança em paralelo com contexto seguido de roteamento |
| `synthesize` | Unifica resultados de dois ou mais agentes bem-sucedidos |
| `compose` | Forma candidata; sem candidata útil segue à saída sem julgamento |
| `judge` | Aprova, pede uma correção ou bloqueia |
| `revise` | Prepara feedback e retorna à execução uma única vez |
| `publish` / `block` | Publica candidata ou mensagem segura |
| `output_guard` | Trata saída e salva histórico quando habilitado |

`context` e `route` são etapas rastreadas dentro de `prepare`, não nós independentes do grafo compilado. Bloqueio de entrada encerra; saídas sem candidata também podem pular o Juiz. O [workflow](workflow.md) apresenta as ramificações completas.

---

## Estado compartilhado — `app/graph/state.py`

O LangGraph passa um dicionário de estado por todos os nós. Cada nó recebe o estado atual, processa e retorna o estado atualizado. Os exemplos abaixo mostram um recorte dos campos; o estado também inclui perfil, fontes e campos do Juiz.

```python
class GraphState(MessagesState, total=False):
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
    status: Literal["success", "error", "skipped"]
    answer: str
    chart_data: dict | None = None
    warnings: list[str] = []
```

---

## Nó 1: context — `app/graph/context.py`

Monta o contexto da pergunta antes do roteamento:

```python
# Forma resumida: o chamador pode passar o histórico já lido para evitar nova consulta.
def build_context(user_id: int, session_id: str, question: str, history=None) -> dict:
    if history is None:
        history = load_history_validated(user_id, session_id)
    return {
        "recent_messages": to_chat_messages(history[-6:]),
        "relevant_memory": find_relevant_memory(user_id, question),
    }
```

A busca de memória de longo prazo só ocorre quando a pergunta contém gatilhos como "lembra", "antes" e "semana passada". Isso evita uma chamada de embedding e uma busca vetorial em perguntas diretas; a latência depende do ambiente.

---

## Nó 2: route — `app/graph/router.py`

Usa `llm_rapido` para classificar a intenção e escolher os agentes. O modelo recebe o histórico recente + a pergunta e retorna um JSON:

```json
{"intent": "habits_impact", "complexity": "medium", "agents": ["habits", "forecast"]}
```

### Parsing robusto do JSON

O LLM pode retornar texto antes ou depois do JSON. O parser tenta carregar o texto completo e, se falhar, extrai do primeiro `{` ao último `}`:

```python
try:
    data = json.loads(content)
except json.JSONDecodeError:
    start = content.find("{")
    end = content.rfind("}") + 1
    data = json.loads(content[start:end]) if start >= 0 and end > start else {}
decision = RoutingDecision(**data)
```

A validação Pydantic confere o contrato. Conteúdo inválido gera intenção `unknown` sem agentes; esse recorte não é um parser geral para vários objetos JSON concatenados.

### Registro de agentes

```python
AGENT_REGISTRY = {
    "consumption": "app.agents.consumption.ConsumptionAgent",
    "forecast": "app.agents.forecast.ForecastAgent",
    "leak": "app.agents.leak.LeakAgent",
    "habits": "app.agents.habits.HabitsAgent",
    "rag": "app.agents.rag.RagAgent",
}
```

O router filtra agentes desconhecidos — se o LLM inventar um nome, ele é ignorado e pode ser registrado no diagnóstico. Também são removidos duplicados e agentes não permitidos pelo perfil.

---

## Nó 3: execute — `app/graph/workflow.py`

Itera sobre os agentes selecionados, instancia cada um com `load_agent` e executa:

```python
# Forma resumida: execute_agent carrega o agente e produz AgentOutput seguro.
results = []
for name in selected_agents:
    output = execute_agent(name, user_id, question, access_kind=access_kind)
    results.append(output)
```

O fluxo também aplica perfil antes de executar, inclui contexto das respostas anteriores e, em revisão, fornece feedback e evidências da tentativa anterior. Não devolve `str(exc)` bruto como resposta pública.

Erros em um agente não derrubam os outros — o nó captura a exceção, registra em `warnings` e continua para o próximo agente da lista.

---

## Nó 4: respond — `app/graph/workflow.py`

Consolida os resultados:

- **0 agentes selecionados** → saudação ou orientação fixa conforme intenção e perfil
- **1 agente com sucesso** → retorna a resposta diretamente
- **Múltiplos agentes** → usa a síntese quando disponível; sem ela, une respostas com `---` e prioriza o primeiro gráfico disponível

---

## Checkpointing com MemorySaver

```python
_memory = MemorySaver()
workflow = _graph.compile(checkpointer=_memory)
```

`MemorySaver` persiste o estado do grafo em memória, vinculado ao `thread_id = user_id:session_id`. O chat persistente lê histórico MongoDB e tenta apagar o checkpoint ao final. Chamadas com `persist_session=False` mantêm checkpoint em RAM; isso não torna a rota do console sem persistência, pois ela salva mensagens por caminho próprio.

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
    # thread_id inclui user_id para evitar colisão entre usuários diferentes
    # que possam usar o mesmo identificador numa chamada interna
    thread_id = f"{user_id}:{session_id}"
    return workflow.invoke(
        initial,
        config={"configurable": {"thread_id": thread_id}},
    )
```

O `thread_id` composto (`user_id:session_id`) é obrigatório para o `MemorySaver` identificar qual sessão está sendo retomada sem risco de dois usuários lerem o checkpoint um do outro.

---

## Fluxo completo de uma requisição

```text
POST /chat {"message": "Quais meus hábitos afetam a conta?"} + Bearer
  │
  ├─ autenticação e validação/criação da sessão
  ├─ run_workflow()
  │    ├─ guardrail_input: regras e anonimização
  │    ├─ prepare: guarda semântica || (contexto → roteador)
  │    ├─ execute: HabitsAgent.run() + ForecastAgent.run(), em sequência
  │    ├─ synthesize → respond → compose
  │    ├─ judge → aprovação / uma revisão / bloqueio
  │    └─ output_guard: PII, ownership, limpeza e append_turn x2
  └─ return ChatResponse
```

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seções "LangGraph" e "Arquitetura Multiagente".

## Estado compartilhado

`GraphState` reúne a entrada (`user_id`, `session_id`, `question`), mensagens e contexto (`recent_messages`, `relevant_memory`, `access_kind`), intenção/complexidade e agentes selecionados. Resultados carregam resposta, gráfico, fontes, outputs de ferramentas e avisos.

Campos de julgamento incluem `candidate`, `previous_candidate`, `previous_agent_results`, `revision_feedback`, `revision_count`, `judge_history`, `judge_action` e `composition_status`. `_blocked` interrompe o caminho de entrada; `_persist_session` controla salvamento do histórico, sem desabilitar todas as escritas de ferramentas.

`AgentOutput` usa `status` igual a `success`, `error` ou `skipped`, com `agent`, `answer`, `sources`, `chart_data`, `tool_calls` e `warnings`. Não é o JSON público do chat.

## Registro e perfis

`AGENT_REGISTRY` registra `consumption`, `forecast`, `leak`, `habits` e `rag`. O carregamento importa a classe pelo caminho cadastrado e constrói a instância com `user_id` e, quando disponível, `access_kind`.

| Perfil | Especialistas permitidos |
| --- | --- |
| `residential` | consumption, forecast, leak, habits, rag |
| `organizational` | consumption, forecast, leak, rag |
| `none` / `unknown` | Nenhum; orientação fixa. |

O classificador recebe perfil, até quatro mensagens recentes e até duas memórias. Tenta ler JSON completo e, em falha, extrai do primeiro `{` ao último `}`. O contrato Pydantic valida intenção, complexidade e lista. Falha gera `intent=unknown`, `complexity=simple`, sem agentes. Nomes desconhecidos e duplicados são removidos; nomes fora do perfil são registrados em `unavailable`.

Essa filtragem acontece novamente na execução. Ela complementa autorização nas ferramentas e consultas; não substitui filtros SQL/Mongo de ownership.

## Revisão e checkpoint

O grafo admite no máximo uma correção. Cada especialista recebe feedback, candidata anterior e seu resultado anterior. O grafo combina chamadas anteriores/novas com marcadores `previous`, `initial` ou `revision` e reúne fontes sem duplicação. O especialista de hábitos remove `create_habit` na revisão.

`MemorySaver` usa `user_id:session_id`. O histórico persistente vem do MongoDB e o checkpoint é apagado ao final do chat, inclusive no caminho de eventos. A chamada do console com `persist_session=False` conserva checkpoint no processo; reinício não o recupera. A rota do console ainda salva mensagens em Mongo por caminho próprio, conforme [operação](operacao-validacao.md).

## Adicionar ou alterar um especialista

1. Implementar a classe com `run(question, revision_feedback=..., revision_context=...)` retornando `AgentResult`.
2. Construir ferramentas vinculadas ao usuário e validar qualquer seleção de imóvel/unidade.
3. Registrar o caminho em `AGENT_REGISTRY` e os perfis aplicáveis em `AGENTS_BY_PROFILE`.
4. Ajustar prompt do roteador, prompts do especialista e rótulos de progresso quando necessário.
5. Preservar fontes e outputs reais para o julgamento, incluindo o comportamento de revisão e efeitos de escrita.
6. Cobrir seleção, isolamento, falha, composição e revisão nos testes pertinentes.

Testes relevantes incluem `test_parallel_guard.py`, `test_rag_workflow_integration.py`, `test_suggestions.py`, `test_progress.py` e `tests/user_profile/test_profile.py`. São evidência de contratos testados; não substituem integração com serviços reais.

## Código relacionado

- [app/graph/state.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/graph/state.py)
- [app/graph/router.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/graph/router.py)
- [app/graph/workflow.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/graph/workflow.py)
