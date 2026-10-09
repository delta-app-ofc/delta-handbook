# Implementação: API FastAPI — Estrutura Base

## Objetivo

Definir a estrutura HTTP da aplicação de inteligência artificial do Projeto Delta: endpoints, contratos de entrada e saída, e organização dos módulos de rotas.

## Contexto

A API é a porta de entrada para o chatbot do Delta. Toda requisição do app Web/Mobile passa por aqui antes de chegar aos agentes de IA. O framework escolhido foi o **FastAPI** — uma biblioteca Python moderna que gera documentação automática, faz validação de dados via Pydantic e tem suporte nativo a tipagem.

---

## Arquivos implementados

```
app/
├── main.py          ← ponto de entrada da aplicação
├── schemas.py       ← contratos de dados (request/response)
└── routes/
    ├── health.py    ← verificação de disponibilidade
    ├── chat.py      ← endpoint principal do chatbot
    └── sessions.py  ← gerenciamento de sessões e histórico
```

---

## `app/main.py` — Ponto de entrada

```python
from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.sessions import router as sessions_router

app = FastAPI(title="Delta AI", version="0.1.0")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(sessions_router)
```

Cada router é registrado com `include_router`. O arquivo `main.py` só faz isso — não contém lógica de negócio. Lógica fica nos agentes e serviços.

---

## `app/schemas.py` — Contratos de dados

O FastAPI usa Pydantic para validar automaticamente os dados que entram e saem da API.

```python
class ChatRequest(BaseModel):
    user_id: int
    session_id: str | None = None   # gerado automaticamente se não informado
    message: str = Field(..., min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    response: str          # texto da resposta do agente
    agent_used: str        # qual(is) agente(s) responderam
    session_id: str        # id da sessão (novo ou recebido)
    chart_data: dict | None = None  # gráfico Plotly serializado, quando houver
```

`session_id` é opcional na entrada — se não for enviado, o sistema gera um UUID automaticamente. Isso permite tanto sessões novas quanto a continuação de conversas anteriores.

`chart_data` é um dicionário com a estrutura de um gráfico Plotly, que o frontend renderiza com `Plotly.newPlot()`.

---

## `app/routes/health.py` — Verificação de saúde

Endpoint simples para monitorar se a API está no ar:

```
GET /health → {"status": "ok"}
```

Usado por ferramentas de monitoramento e pelo CI/CD para confirmar que o serviço subiu corretamente.

---

## `app/routes/chat.py` — Fluxo principal

O endpoint `/chat` é o coração da API. O fluxo completo de uma requisição é:

```
POST /chat
  │
  ├─ 1. validate_input()        ← guardrail de entrada
  ├─ 2. session_id = uuid4()    ← gera se não informado
  ├─ 3. run_workflow()          ← LangGraph executa os agentes
  ├─ 4. validate_output()       ← guardrail de saída
  ├─ 5. append_turn() x2        ← salva no MongoDB (human + assistant)
  └─ 6. return ChatResponse     ← resposta ao cliente
```

```python
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    guard = validate_input(req.user_id, req.message)
    if not guard["ok"]:
        raise HTTPException(status_code=422, detail=guard["reason"])

    session_id = req.session_id or str(uuid.uuid4())
    state = run_workflow(user_id=req.user_id, session_id=session_id, question=req.message)

    out_guard = validate_output(state["response"])
    if not out_guard["ok"]:
        raise HTTPException(status_code=500, detail=out_guard["reason"])

    append_turn(session_id, req.user_id, "human", req.message)
    append_turn(session_id, req.user_id, "assistant", state["response"])

    return ChatResponse(
        response=state["response"],
        agent_used=state.get("agent_used", ""),
        session_id=session_id,
        chart_data=state.get("chart_data"),
    )
```

Os guardrails (validação de entrada e saída) envolvem toda a execução dos agentes. Se qualquer um falhar, a API retorna um erro HTTP antes de salvar no banco.

---

## `app/routes/sessions.py` — Histórico de sessões

Três endpoints para gerenciar o histórico de conversas:

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/sessions/{user_id}` | Lista todas as sessões do usuário |
| `GET`  | `/sessions/{session_id}/history?user_id=X` | Retorna as mensagens de uma sessão |
| `POST` | `/sessions/{session_id}/close?user_id=X` | Encerra a sessão e salva na memória de longo prazo |

O parâmetro `user_id` é obrigatório para verificar que quem está pedindo o histórico é dono daquela sessão.

---

## Camada de dados

A camada de acesso ao banco está em `app/data/`:

- **`db_postgres.py`** — conexão com PostgreSQL (dados cadastrais, tarifas, hábitos)
- **`db_mongo.py`** — conexão com MongoDB (telemetria IoT, histórico de chat)

Os módulos de dados não fazem lógica de negócio — apenas executam queries e retornam resultados. A lógica fica nos agentes e services.

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) para a descrição completa dos endpoints propostos e a estrutura de pastas.
