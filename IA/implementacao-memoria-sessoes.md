# Memória de sessão e de longo prazo

## Objetivo

Descrever `app/memory/session.py`, `long_term.py`, `app/graph/context.py` e `app/services/session_meta.py` na `main` de IA `f6f3d8c` (02/11/2026).

## Histórico persistente: MongoDB

A coleção usada é **`chat_sessions`**, no database configurado por `MONGO_DB_APP`. Não é `conversations`. O servidor cria `_id` ObjectId e o expõe como `session_id` textual. As operações filtram por `_id`, `user_id` e exclusão lógica quando aplicável.

O documento contém `started_at`, `last_activity_at`, `is_open`, `is_active`, `is_deleted` e `messages`. Cada mensagem tem `role` (`user` ou `bot`), `content_type=text`, `content`, `sent_at` e `api_status_code`.

`create_session` insere sessão vazia; `append_turn` só anexa a uma sessão já pertencente ao usuário e a reabre. Não faz upsert para materializar IDs escolhidos pelo cliente. `discard_empty_session` remove somente uma sessão do usuário ainda sem mensagens.

A listagem ignora sessões vazias/excluídas, ordena por última atividade e pagina por `limit`/`offset`. O histórico completo usa os papéis do banco; `to_chat_messages` converte para `human`/`assistant` ao alimentar o grafo.

## Título, prévia e ícone

Após salvar o par de mensagens, o grafo inicia uma thread daemon para `refresh_session_meta`. O serviço gera metadados quando ainda não há título e evita trabalho duplicado em andamento no mesmo processo.

O título tem até 40 caracteres e a prévia até 80. Ícone é validado contra `ICON_NAMES` e desconhecido vira `general`. Se a geração falha ou não terminou, a listagem deriva título da primeira pergunta e prévia da última mensagem. Não há garantia de metadados prontos na resposta imediata.

## Contexto recente e checkpoint

O contexto usa até seis mensagens recentes e tenta reutilizar a leitura já realizada ao iniciar a pergunta. Se a leitura inicial falhar, o nó de contexto pode tentar novamente.

O LangGraph usa `MemorySaver` com `thread_id=user_id:session_id`. No chat persistente, o checkpoint é apagado ao final da execução; o MongoDB é a fonte de histórico para a próxima pergunta. Na chamada do grafo pelo console, `persist_session=False` deixa checkpoint em RAM. A rota do console salva mensagens por caminho próprio, inclusive a pergunta original; não é modo sem persistência. Reinício ou outro worker não recupera o checkpoint em RAM. Veja [operação](operacao-validacao.md).

## Resumos no Qdrant

`POST /sessions/{session_id}/close` verifica ownership, lê mensagens, gera resumo com `llm_rapido`, gera embedding Gemini e faz upsert na coleção **`session_summaries`**. Depois marca a sessão fechada. Falha retorna 500; não há transação distribuída entre Qdrant e MongoDB.

| Propriedade | Valor implementado |
| --- | --- |
| Vetor | 3072 dimensões, Cosine ao criar a coleção. |
| Modelo | `GEMINI_EMBEDDING_MODEL`, default `gemini-embedding-2-preview`. |
| Payload | `user_id`, `session_id`, `summary`. |
| ID do ponto | UUID determinístico por `user_id:session_id`. |
| Filtro de busca | Sempre `user_id` confiável. |

A gravação cria a coleção se faltar e recusa dimensão diferente; nunca a recria automaticamente. A busca não cria coleções e retorna lista vazia em falha, registrando diagnóstico quando há trace.

O payload de resumos não registra o modelo de embedding para filtragem por versão. Trocar o modelo exige plano explícito de reindexação dos resumos, mesmo quando a dimensão continua igual. A segurança de revisão/modelo do RAG documental não deve ser atribuída automaticamente à memória longa.

`find_relevant_memory` consulta resumos somente quando encontra termos como “lembra”, “antes” ou “mês passado”. Retorna até três resumos pelo caminho padrão. É uma heurística de gatilhos, com possibilidade de não recuperar uma referência implícita.

## Limites de consistência e operação

- Pergunta anonimizada e resposta tratada são anexadas por duas operações independentes. O grafo ignora exceções de salvamento; pode haver turno parcial ou resposta devolvida sem persistência.
- Fechar uma sessão não impede reabertura por nova mensagem e não exclui seu histórico.
- Não há rotação automática implementada por 50–100 mensagens nesta camada; os limites de documento Mongo continuam relevantes.
- Clientes da memória longa têm caches próprios; não aparecem no fechamento do `lifespan` atual. O fechamento Mongo também é explícito por função, sem ligação nesse `lifespan`.
- Não se deve usar o checkpoint como substituto de persistência compartilhada entre workers.

Verificação: `test_session_memory.py`, `test_session_meta.py`, `test_question_memory.py`, `test_history_api.py` e `tests/isolation/test_isolation_sessions.py`. Parte dos testes de histórico usa Mongo real descartável e pode ser pulada quando falta o serviço; veja [operação](operacao-validacao.md).

## Fontes da implementação revisada

- [app/memory/session.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/memory/session.py)
- [app/memory/long_term.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/memory/long_term.py)
- [app/services/session_meta.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/services/session_meta.py)
