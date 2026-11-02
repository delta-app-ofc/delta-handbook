# Implementação: API FastAPI — Estrutura Base

## Objetivo

Definir a estrutura HTTP da aplicação de inteligência artificial do Projeto Delta: endpoints, contratos de entrada e saída, e organização dos módulos de rotas.

## Contexto

A API é a porta de entrada para o chatbot do Delta. Toda requisição do app Web/Mobile passa por aqui antes de chegar aos agentes de IA. O framework escolhido foi o **FastAPI** — uma biblioteca Python moderna que gera documentação automática, faz validação de dados via Pydantic e tem suporte nativo a tipagem.

---

## Estrutura planejada

Os arquivos abaixo estão reservados no repositório mas ainda não têm implementação ativa — a API completa é um componente pendente (ver `AGENTS.md`).

```
app/
├── main.py          ← ponto de entrada da aplicação (vazio)
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

> **Em PR (01/11/2026):** a resposta pública do `/chat` e do `/chat/stream` **não traz mais** a lista de agentes usados (o usuário não deve conhecer a estrutura interna) e ganha `suggestions: list[str]` (até 3 perguntas para continuar a conversa). A rota autenticada `GET /chat/suggestions` devolve `{"suggestions": [...]}` com perguntas iniciais pelo perfil da conta (residencial ou organização). As sugestões seguem regras fixas, sem LLM. O bloco de código acima é didático e já diverge do código atual (por exemplo, o usuário vem do token JWT, não do corpo). Veja [`habitos-simulacao-e-saida-ao-usuario.md`](habitos-simulacao-e-saida-ao-usuario.md).

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
  ├─ 1. validate_input()        ← guardrail: anon. PII + detecta injection
  ├─ 2. session_id = uuid4()    ← gera se não informado
  ├─ 3. run_workflow()          ← LangGraph executa os agentes (recebe mensagem anonimizada)
  ├─ 4. validate_output()       ← guardrail: redige PII da resposta
  ├─ 5. append_turn() x2        ← salva no MongoDB (msg original + resposta revisada)
  └─ 6. return ChatResponse     ← retorna resposta revisada ao cliente
```

```python
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    guard = validate_input(req.user_id, req.message)
    if not guard["ok"]:
        raise HTTPException(status_code=422, detail=guard["reason"])

    session_id = req.session_id or str(uuid.uuid4())
    state = run_workflow(user_id=req.user_id, session_id=session_id, question=guard["message"])

    out_guard = validate_output(state["response"], pii_map=guard["pii_map"])
    if not out_guard["ok"]:
        raise HTTPException(status_code=500, detail=out_guard["reason"])

    append_turn(session_id, req.user_id, "human", req.message)          # original
    append_turn(session_id, req.user_id, "assistant", out_guard["response"])  # revisada

    return ChatResponse(
        response=out_guard["response"],
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
