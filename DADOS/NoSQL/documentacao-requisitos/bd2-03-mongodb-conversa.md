### BD2-03 — Usar MongoDB em alguma interação conversacional

**Evidência direta:**

- [Persistência das sessões de chat na IA (`session.py`)](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/memory/session.py)
- [Schema e índices de `chat_sessions` e `chat_feedback`](https://github.com/delta-app-ofc/delta-mongo-database/blob/main/scripts/delta-app/script-collections.js)
- [Documentação da modelagem MongoDB](../modelagem-mongodb.md)

**Localização e como comprovar:**

O chatbot grava cada conversa na coleção `chat_sessions` do banco `db_delta_app`. A coleção usa o padrão de *bucket*: um documento por sessão, com um array `messages` que recebe cada mensagem nova.

| Função em `session.py` | O que faz no MongoDB |
|---|---|
| `create_session` | Insere a sessão, com `is_open`, `is_active` e `messages` vazio |
| `append_turn` | Faz `$push` da mensagem e atualiza `last_activity_at` |
| `load_history_validated` | Lê o histórico, só se a sessão pertencer ao usuário |
| `get_sessions_for_user` | Lista as sessões do usuário por atividade recente, com paginação |
| `set_session_meta` | Grava `title`, `preview` e `icon` da sessão |
| `mark_session_closed` | Encerra a sessão (`is_open` e `is_active` falsos) |

Cada mensagem tem `role` (`user` ou `bot`), `content_type`, `content`, `sent_at` e `api_status_code`. O validador da coleção rejeita papéis fora desse conjunto. A coleção `chat_feedback` guarda a avaliação de cada sessão pelo `session_id`, que referencia `chat_sessions._id`.

#### 1. Por que um documento por sessão

O histórico inteiro de uma conversa é lido junto a cada resposta da IA. Com um documento por sessão, isso vira uma leitura só, e a gravação de uma mensagem nova é um `$push` atômico.

#### 2. Segurança do histórico

O código confere se a sessão pertence ao `user_id` antes de ler ou gravar (`session_belongs_to_user`). A exclusão é lógica (`is_deleted`), e as sessões vazias não aparecem na listagem.

#### 3. Como comprovar

1. Conversar com o chatbot pelo app ou pela web.
2. Abrir o Compass, banco `db_delta_app`, coleção `chat_sessions`, e conferir o documento da sessão com as mensagens.
3. Enviar uma segunda mensagem e conferir que o array `messages` cresceu e que `last_activity_at` mudou.

> **Pendente:** anexar o print da coleção `chat_sessions` no Compass.
