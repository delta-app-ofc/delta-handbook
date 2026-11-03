# Implementação: API FastAPI — Estrutura Base

## Objetivo

Definir a estrutura HTTP da aplicação de inteligência artificial do Projeto Delta: endpoints, contratos de entrada e saída, e organização dos módulos de rotas.

## Contexto

A API é a porta de entrada para o chatbot do Delta. Toda requisição do app Web/Mobile passa por aqui antes de chegar aos agentes de IA. O framework escolhido foi o **FastAPI** — uma biblioteca Python moderna que gera documentação automática, faz validação de dados via Pydantic e tem suporte nativo a tipagem.

---

## Estrutura implementada

Os arquivos abaixo compõem a API e separam configuração, contratos e rotas:

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

Cada router é registrado com `include_router`. O exemplo mostra o registro dos routers. `main.py` também configura CORS, rastreamento, playground e encerramento de recursos; a lógica de negócio fica nos agentes e serviços.

---

## `app/schemas.py` — Contratos de dados

O FastAPI usa Pydantic para validar automaticamente os dados que entram e saem da API.

```python
class ChatRequest(BaseModel):
    session_id: str | None = None   # gerado automaticamente se não informado
    message: str = Field(..., min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    response: str          # texto da resposta do agente
    session_id: str        # id da sessão (novo ou recebido)
    chart_data: dict | None = None  # gráfico Plotly serializado, quando houver
    suggestions: list[str] = Field(default_factory=list)
```

`session_id` é opcional na entrada — se não for enviado, o servidor cria uma sessão MongoDB e devolve seu ObjectId em texto. Isso permite tanto sessões novas quanto a continuação de conversas anteriores.

`chart_data` é um dicionário com a estrutura de um gráfico Plotly, que o frontend renderiza com `Plotly.newPlot()`.

---

## `app/routes/health.py` — Verificação de saúde

Endpoint simples para monitorar se a API está no ar:

```
GET /health → {"status": "ok", "issues": []}
```

Pode ser usado para verificar a disponibilidade HTTP. Ele apenas carrega settings; não testa bancos nem provedores. Problema de configuração pode produzir `status=degraded`.

---

## `app/routes/chat.py` — Fluxo principal

O endpoint `/chat` é o coração da API. O fluxo completo de uma requisição é:

```text
POST /chat + Authorization: Bearer <JWT>
  │
  ├─ 1. get_current_user_id()   ← valida token e conta ativa
  ├─ 2. _open_session()        ← cria sessão ou verifica proprietário
  ├─ 3. run_workflow()         ← entrada, contexto, agentes, Juiz e saída
  │       └─ append_turn() x2  ← pergunta anonimizada + resposta tratada
  └─ 4. return ChatResponse    ← texto, sessão, gráfico e sugestões
```

Exemplo resumido do contrato da rota, sem reproduzir tratamento de todas as falhas:

```python
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user_id: int = Depends(get_current_user_id)):
    session_id, created = _open_session(req, user_id)
    state = run_workflow(user_id, session_id, req.message)
    if state.get("_blocked"):
        _discard_new_session(user_id, session_id, created)
        raise HTTPException(status_code=422, detail=state["response"])
    return ChatResponse(
        response=state["response"],
        session_id=session_id,
        chart_data=state.get("chart_data"),
        suggestions=_suggestions(user_id, state, req.message),
    )
```

Os guardrails pertencem ao grafo. Bloqueio de entrada interrompe os especialistas; rejeição do Juiz ou da saída produz mensagem segura. As duas gravações finais do histórico são independentes e suas falhas não impedem necessariamente a resposta HTTP.

---

## `app/routes/sessions.py` — Histórico de sessões

Três endpoints para gerenciar o histórico de conversas:

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET`  | `/sessions?limit=20&offset=0` | Lista todas as sessões do usuário |
| `GET`  | `/sessions/{session_id}/messages` | Retorna as mensagens de uma sessão |
| `POST` | `/sessions/{session_id}/close` | Encerra a sessão e salva na memória de longo prazo |

O `user_id` é obtido do JWT e não do corpo ou da URL. A API valida ownership antes de devolver histórico ou encerrar a sessão.

---

## Camada de dados

A camada de acesso ao banco está em `app/data/`:

- **`db_postgres.py`** — conexão com PostgreSQL (dados cadastrais, tarifas, hábitos)
- **`db_mongo.py`** — conexão com MongoDB (telemetria IoT, histórico de chat)

Os módulos de dados não fazem lógica de negócio — apenas executam queries e retornam resultados. A lógica fica nos agentes e services.

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) para a descrição completa dos componentes e a estrutura de pastas.

## Autenticação

A integração com o backend usa **RS256**, verificado com `AUTH_PUBLIC_KEY`: PEM RSA de pelo menos 2048 bits ou caminho de arquivo, inclusive prefixo `file:`. Não se fornece chave privada à IA.

A IA exige `exp`, `sub`, `iss` e `aud`, valida emissor e audiência e aceita 10 segundos de tolerância de relógio no caminho RS256. `AUTH_KEY_ID` confere `kid` quando não está vazio. Defaults: issuer/audience `delta-api`, key ID `delta-1`. O `sub` deve ser texto com inteiro positivo, sem zeros à esquerda e até `2**31 - 1`.

`AUTH_CHECK_ACTIVE=true` consulta o usuário no PostgreSQL a cada requisição autenticada. Conta inexistente/inativa é recusada; falha da consulta retorna 503. Definir `false` desliga essa verificação.

**HS256** existe somente para `development` e `test`, com `JWT_SECRET` de 32 ou mais caracteres. Quando há chave pública, só RS256 é aceito; os algoritmos não ficam habilitados ao mesmo tempo. Staging/produção recusam a alternativa HS256.

| Status | Situação |
| --- | --- |
| 401 | Bearer ausente, inválido, expirado ou conta recusada. Inclui `WWW-Authenticate: Bearer`. |
| 503 | Autenticação sem configuração válida, chave ilegível ou verificação de conta indisponível. |
| 404 | Sessão inexistente, excluída ou de outro usuário; mesma mensagem para os três casos. |
| 422 | Corpo inválido pelo Pydantic ou bloqueio de entrada no chat JSON. Os formatos desses erros podem diferir. |
| 500 | Falha não tratada ou encerramento de sessão malsucedido. |

A descrição 503 compartilhada em `app/schemas.py` ainda fala só de `JWT_SECRET`; o comportamento acima é o de `app/auth.py`.

## Contrato do chat

```json
{"message": "Quanto consumi esta semana?", "session_id": null}
```

`message` tem de 1 a 2000 caracteres. Sem `session_id`, o servidor cria um documento em `chat_sessions` e devolve seu ObjectId como texto. Com ID, valida ownership antes do grafo. Não cria sessões a partir de IDs arbitrários do cliente.

```json
{
  "response": "Texto validado da resposta",
  "session_id": "507f1f77bcf86cd799439011",
  "chart_data": null,
  "suggestions": ["Como foi meu consumo comparado com o mês passado?"]
}
```

`chart_data`, quando presente, é uma estrutura Plotly. `agent_used`, evidências e candidatas bloqueadas não integram esse contrato público.

Sugestões são escolhidas por regras de `app/graph/suggestions.py`, sem LLM: até três, sem duplicatas e sem repetir a pergunta atual por comparação de texto sem diferença entre maiúsculas/minúsculas. Há catálogo residencial e organizacional; perfil desconhecido usa sugestões residenciais como fallback. Essas sugestões não autorizam consultas nem contornam a restrição de agentes por perfil.

## Eventos SSE

Use `fetch` com POST, JSON e Bearer. O `EventSource` nativo não cobre esse contrato de POST com cabeçalho de autenticação.

```text
event: stage
data: {"stage":"checking","label":"Verificando a mensagem"}

event: result
data: {"response":"Texto validado","session_id":"507f1f77bcf86cd799439011","chart_data":null,"suggestions":[]}

```

- `stage`: etapas `checking`, `understanding`, `planning`, `working`, `composing`, `validating`, `revising` e `finishing`. Rótulos fixos, sem valores da conta ou texto da candidata.
- `result`: um único JSON final, com o contrato de `ChatResponse`.
- `error`: `status` 422 ou 500 e `detail`; falha de processamento pode incluir `request_id`.
- `: keep-alive`: comentário a cada 15 segundos sem evento.

Auth, ownership e abertura do histórico são verificados antes do streaming e podem retornar erro HTTP. Depois de aberto, HTTP permanece 200 e o cliente precisa interpretar `error`. Use `Cache-Control: no-cache` e respeite o comportamento sem buffering indicado por `X-Accel-Buffering: no`.

## Histórico, rastreamento e limites

A listagem retorna título, prévia, ícone, datas e `is_open`. Título tem até 40 caracteres e prévia até 80; ícone desconhecido deve ser mostrado como `general`. Mensagens usam papéis `user`/`bot` e timestamp UTC.

O servidor gera `X-Request-ID` e o expõe por CORS. `X-Client: app` ou `web` identifica o canal na observabilidade; outros valores viram `unknown`. `CORS_ALLOWED_ORIGINS` define origens separadas por vírgulas; padrão/vazio permite `*`, com `allow_credentials=False`.

Uma sessão nova sem mensagens é removida em falha ou bloqueio de entrada. A gravação final do turno usa duas operações independentes e suas falhas são ignoradas pelo grafo; HTTP 200 não garante histórico persistido. Veja [memória](implementacao-memoria-sessoes.md).

## Código relacionado

- [app/auth.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/auth.py)
- [app/schemas.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/schemas.py)
- [app/routes/chat.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/routes/chat.py)
- [app/routes/sessions.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/routes/sessions.py)
