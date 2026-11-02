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

### Coleção MongoDB: `chat_sessions`

Cada documento representa uma sessão:

Exemplo de representação JSON; no banco, `_id` é ObjectId e os timestamps são datas BSON:

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": 42,
  "started_at": "2026-03-01T10:00:00Z",
  "last_activity_at": "2026-03-01T10:01:00Z",
  "is_open": true,
  "is_active": true,
  "is_deleted": false,
  "messages": [
    {"role": "user", "content_type": "text", "content": "Quanto consumi hoje?", "sent_at": "2026-03-01T10:00:00Z", "api_status_code": 200},
    {"role": "bot", "content_type": "text", "content": "Você consumiu 120 litros.", "sent_at": "2026-03-01T10:01:00Z", "api_status_code": 200}
  ]
}
```

### Funções implementadas

| Função | Descrição |
|--------|-----------|
| `create_session(user_id)` | Cria sessão vazia e devolve ObjectId textual. |
| `session_belongs_to_user(user_id, session_id)` | Verifica ID, proprietário e exclusão lógica. |
| `load_history_validated(user_id, session_id)` | Retorna mensagens somente para o dono. |
| `append_turn(session_id, user_id, role, content)` | Anexa mensagem em sessão existente do usuário; reabre se fechada. |
| `get_sessions_for_user(user_id, limit, offset)` | Lista sessões com mensagens, paginadas por última atividade. |
| `count_sessions_for_user(user_id)` | Conta sessões visíveis para a paginação. |
| `mark_session_closed(user_id, session_id)` | Marca sessão fechada. |
| `discard_empty_session(user_id, session_id)` | Remove somente a sessão do usuário ainda vazia. |

### Por que validar o proprietário no carregamento?

O identificador de uma sessão não é autorização de acesso. A consulta inclui usuário e exclusão lógica antes de devolver mensagens. O leitor retorna lista vazia para ID inválido, sessão inexistente ou de outro usuário; as rotas verificam ownership e respondem 404 sem distinguir essas situações. Não há um leitor público sem validação do dono.

```python
# Recorte da consulta de load_history_validated:
doc = _collection().find_one(
    {"_id": object_id, "user_id": user_id, "is_deleted": {"$ne": True}},
    {"_id": 0, "messages": 1},
)
```

### `append_turn` — atualização de sessão existente

A sessão é criada pelo servidor antes do primeiro turno. O anexo usa `_id`, `user_id` e exclusão lógica no filtro, sem `upsert`; assim não materializa um ID arbitrário enviado pelo cliente:

```python
result = _collection().update_one(
    {"_id": object_id, "user_id": user_id, "is_deleted": {"$ne": True}},
    {
        "$push": {"messages": {
            "role": db_role, "content_type": "text", "content": content,
            "sent_at": now, "api_status_code": api_status_code,
        }},
        "$set": {"last_activity_at": now, "is_open": True, "is_active": True},
    },
)
```

`$push` acrescenta a mensagem e `$set` atualiza atividade/abertura. Sem documento correspondente, a função levanta erro; criar e anexar são operações distintas. `to_chat_messages` converte `user`/`bot` do armazenamento para `human`/`assistant` do modelo.

---

## Memória de longo prazo — `app/memory/long_term.py`

### Como funciona o Qdrant

O Qdrant é um banco de dados vetorial — armazena vetores (listas de números) que representam o "significado" de um texto. Para buscar memórias relevantes, o sistema:

1. Converte a pergunta em vetor (embedding)
2. Busca os vetores mais próximos na coleção compartilhada, filtrando pelo usuário
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

O ID do ponto usa `uuid5(NAMESPACE_URL, f"{user_id}:{session_id}")` — determinístico, então re-executar com a mesma sessão atualiza em vez de duplicar.

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

def find_relevant_memory(user_id: int, question: str) -> list[str]:
    if not any(trigger in question.lower() for trigger in _MEMORY_TRIGGERS):
        return []
    return search_memory(user_id, question)
```

Isso evita uma chamada de embedding e uma consulta vetorial em perguntas sem referência ao passado; o ganho depende do ambiente.

---

## Referência arquitetural

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seção "Controle de Sessões".

## Título, prévia e ícone

Após salvar o par de mensagens, o grafo inicia uma thread daemon para `refresh_session_meta`. O serviço gera metadados quando ainda não há título e evita trabalho duplicado em andamento no mesmo processo.

O título tem até 40 caracteres e a prévia até 80. Ícone é validado contra `ICON_NAMES` e desconhecido vira `general`. Se a geração falha ou não terminou, a listagem deriva título da primeira pergunta e prévia da última mensagem. Não há garantia de metadados prontos na resposta imediata.

## Contexto recente e checkpoint

O contexto usa até seis mensagens recentes e tenta reutilizar a leitura já realizada ao iniciar a pergunta. Se a leitura inicial falhar, o nó de contexto pode tentar novamente.

O LangGraph usa `MemorySaver` com `thread_id=user_id:session_id`. No chat persistente, o checkpoint é apagado ao final da execução; o MongoDB é a fonte de histórico para a próxima pergunta. Na chamada do grafo pelo console, `persist_session=False` deixa checkpoint em RAM. A rota do console salva mensagens por caminho próprio, inclusive a pergunta original; não é modo sem persistência. Reinício ou outro worker não recupera o checkpoint em RAM. Veja [operação](operacao-validacao.md).

## Limites de consistência e operação

- Pergunta anonimizada e resposta tratada são anexadas por duas operações independentes. O grafo ignora exceções de salvamento; pode haver turno parcial ou resposta devolvida sem persistência.
- Fechar uma sessão não impede reabertura por nova mensagem e não exclui seu histórico.
- Não há rotação automática implementada por 50–100 mensagens nesta camada; os limites de documento Mongo continuam relevantes.
- Clientes da memória longa têm caches próprios; não aparecem no fechamento do `lifespan` atual. O fechamento Mongo também é explícito por função, sem ligação nesse `lifespan`.
- Não se deve usar o checkpoint como substituto de persistência compartilhada entre workers.

Verificação: `test_session_memory.py`, `test_session_meta.py`, `test_question_memory.py`, `test_history_api.py` e `tests/isolation/test_isolation_sessions.py`. Parte dos testes de histórico usa Mongo real descartável e pode ser pulada quando falta o serviço; veja [operação](operacao-validacao.md).

## Código relacionado

- [app/memory/session.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/memory/session.py)
- [app/memory/long_term.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/memory/long_term.py)
- [app/services/session_meta.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/services/session_meta.py)
