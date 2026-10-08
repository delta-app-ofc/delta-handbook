# Implementação: Memória de Sessão e Longo Prazo

## Objetivo

Implementar dois tipos de memória para o chatbot do Delta:

1. **Memória de sessão** — armazena o histórico da conversa atual no MongoDB
2. **Memória de longo prazo** — persiste resumos de conversas anteriores no Qdrant, permitindo que o agente "lembre" de interações de semanas ou meses atrás

## Contexto

Sem memória, cada mensagem começa do zero — o agente não sabe o que você perguntou antes. Com sessão, ele mantém o contexto da conversa atual. Com longo prazo, ele consegue responder perguntas como "você se lembra do que discutimos na semana passada?".

---

## Arquitetura de memória

```
Conversa atual
  │
  ├─ MongoDB (chat_sessions)
  │    └─ histórico de mensagens da sessão ativa
  │
  └─ Ao encerrar a sessão:
       ├─ LLM gera resumo da conversa
       ├─ Gemini Embeddings transforma o resumo em vetor
       └─ Qdrant armazena o vetor com user_id
            └─ busca semântica em sessões futuras
```

---

## Memória de sessão — `app/memory/session.py`

### Coleção MongoDB: `conversations`

Cada documento representa uma sessão:

```json
{
  "session_id": "abc-123",
  "user_id": 42,
  "created_at": "2026-03-01T10:00:00Z",
  "messages": [
    {"role": "human", "content": "Quanto consumi hoje?", "timestamp": "..."},
    {"role": "assistant", "content": "Você consumiu 120 litros.", "timestamp": "..."}
  ]
}
```

### Funções implementadas

| Função | Descrição |
|--------|-----------|
| `load_history(session_id)` | Retorna todas as mensagens da sessão |
| `load_history_validated(user_id, session_id)` | Igual ao anterior, mas verifica que a sessão pertence ao usuário |
| `append_turn(session_id, user_id, role, content)` | Adiciona uma mensagem; cria o documento se for a primeira mensagem |
| `get_sessions_for_user(user_id)` | Lista todas as sessões do usuário (sem mensagens) |

### Por que duas funções de carregamento?

`load_history` é interno — usado pelo próprio sistema para operações confiáveis. `load_history_validated` é usado nas rotas HTTP — quando um usuário pede o histórico de uma sessão, verificamos que ele é o dono antes de devolver.

```python
def load_history_validated(user_id: int, session_id: str) -> list[dict]:
    doc = _col().find_one(
        {"session_id": session_id},
        {"_id": 0, "user_id": 1, "messages": 1},
    )
    if doc is None or doc.get("user_id") != user_id:
        return []  # sessão não existe ou pertence a outro usuário
    return doc.get("messages", [])
```

Retornar lista vazia (em vez de um erro 404) é intencional: não revela ao solicitante se aquela sessão existe ou não.

### `append_turn` — upsert MongoDB

```python
_col().update_one(
    {"session_id": session_id},
    {
        "$setOnInsert": {"user_id": user_id, "created_at": datetime.now(timezone.utc)},
        "$push": {"messages": {"role": role, "content": content, "timestamp": ...}},
    },
    upsert=True,
)
```

`$setOnInsert` só executa na primeira mensagem (quando o documento é criado). `$push` sempre adiciona a nova mensagem. Assim, uma única operação serve tanto para criar quanto para atualizar.

---

## Memória de longo prazo — `app/memory/long_term.py`

### Como funciona o Qdrant

O Qdrant é um banco de dados vetorial — armazena vetores (listas de números) que representam o "significado" de um texto. Para buscar memórias relevantes, o sistema:

1. Converte a pergunta em vetor (embedding)
2. Busca os vetores mais próximos na coleção do usuário
3. Retorna os resumos associados

```
"você lembra da minha meta?"
     │
     ▼ Gemini Embeddings (3072 dimensões)
[0.12, -0.34, 0.87, ...]
     │
     ▼ Qdrant query_points (filtrado por user_id)
→ "Usuário disse que quer consumir menos de 10m³/mês"
→ "Usuário perguntou sobre o custo alto em fevereiro"
```

### Coleção: `session_summaries`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `user_id` | int | Dono da memória |
| `session_id` | str | Sessão de origem |
| `summary` | str | Resumo gerado pelo LLM |
| vetor | 3072 floats | Embedding do resumo (gemini-embedding-2-preview) |

### Funções implementadas

#### `save_summary(user_id, session_id, messages)`

1. Gera resumo: `llm_rapido.invoke("Resuma em até 3 frases esta conversa:\n\n{transcript}")`
2. Cria embedding: `_embed_model().embed_query(summary_text)`
3. Grava no Qdrant com `upsert` (substitui se a sessão já existia)

O ID do ponto usa `uuid5(NAMESPACE_URL, session_id)` — determinístico, então re-executar com a mesma sessão atualiza em vez de duplicar.

#### `search_memory(user_id, query, top_k=3)`

```python
response = _qdrant().query_points(
    collection_name=_COLLECTION,
    query=vector,
    query_filter=Filter(
        must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
    ),
    limit=top_k,
)
```

O filtro `user_id` é obrigatório — cada usuário acessa apenas suas próprias memórias.

#### `close_session(session_id, user_id)`

Chamado pelo endpoint `POST /sessions/{id}/close`. Lê o histórico com `load_history_validated` (validação de propriedade) e chama `save_summary`.

### Otimização: `_collection_initialized`

Criar/verificar a coleção no Qdrant envolve 2–3 chamadas de rede. Para evitar esse custo em toda requisição, um flag `_collection_initialized = False` é definido no módulo. Após a primeira inicialização bem-sucedida, `_ensure_collection()` retorna imediatamente.

```python
_collection_initialized = False

def _ensure_collection() -> None:
    global _collection_initialized
    if _collection_initialized:
        return
    # ... setup ...
    _collection_initialized = True
```

### Otimização: busca condicional

A busca no Qdrant só ocorre quando a pergunta indica referência a sessões anteriores. Palavras como "lembra", "antes", "semana passada", "você disse" ativam a busca. Perguntas diretas ("quanto consumi hoje?") não ativam.

```python
_MEMORY_TRIGGERS = {
    "antes", "anterior", "última vez",
    "você disse", "você falou",
    "lembra", "histórico", "já falamos", ...
}

def _needs_long_term_memory(question: str) -> bool:
    q = question.lower()
    return any(trigger in q for trigger in _MEMORY_TRIGGERS)
```

Isso evita o custo de embedding (~500ms) em toda pergunta.

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seção "Controle de Sessões".
