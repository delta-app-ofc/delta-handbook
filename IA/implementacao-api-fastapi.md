# API FastAPI do chatbot

## Objetivo e componentes

Documentar o contrato implementado na `main` de IA `f6f3d8c` (02/11/2026). Fontes: `app/main.py`, `app/auth.py`, `app/schemas.py` e `app/routes/`.

`main.py` registra os routers, o middleware de rastreamento, CORS e o encerramento de recursos. As rotas chamam o grafo; guardrails e gravação do turno estão dentro dele. Swagger fica em `/docs`.

## Rotas da aplicação

| Método | Rota | Comportamento |
| --- | --- | --- |
| GET | `/health` | Público. Retorna `status` e `issues`; só carrega settings, sem testar bancos ou LLM. |
| GET | `/chat/suggestions` | Até três perguntas iniciais conforme o perfil autenticado. |
| POST | `/chat` | Pergunta e resposta JSON, criando ou continuando sessão. |
| POST | `/chat/stream` | Mesmo processamento, com eventos SSE de progresso. |
| GET | `/sessions?limit=20&offset=0` | Sessões com mensagens, ordenadas por atividade, e `total`. Limite de 1 a 100. |
| GET | `/sessions/{session_id}/messages` | Mensagens da sessão do usuário, em ordem cronológica. |
| POST | `/sessions/{session_id}/close` | Gera resumo de longo prazo e marca sessão fechada. Nova mensagem a reabre. |

Chat e sessões exigem `Authorization: Bearer <JWT>`. Não há `user_id` no contrato de entrada. As rotas de console em `/playground` têm configuração própria e não exigem Bearer; veja [operação](operacao-validacao.md).

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

## Fontes da implementação revisada

- [app/auth.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/auth.py)
- [app/schemas.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/schemas.py)
- [app/routes/chat.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/routes/chat.py)
- [app/routes/sessions.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/routes/sessions.py)
