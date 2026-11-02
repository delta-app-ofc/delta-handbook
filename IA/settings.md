# Configuração da aplicação de IA

## Objetivo e carregamento

`app/config.py` concentra `Settings` e validadores por componente. Referência: `main` `f6f3d8c`, revisada em 02/11/2026. Não exige todas as credenciais no import; cada integração valida o caminho de uso.

Variáveis do processo prevalecem sobre `.env`. `APP_ENV=test` definido no processo evita leitura de `.env`. `load_settings(environ=...)` usa o mapa injetado sem arquivo por padrão. `get_settings` guarda snapshot em cache; `reload_settings`, `clear_settings_cache` ou `get_settings(refresh=True)` permitem recarga controlada. Não recarregue por requisição.

Settings ocultam segredos/URIs na representação. Mensagens de configuração devem indicar nomes de variáveis, sem seus valores. Validação sintática não comprova DNS, conexão ou schema do produto.

## Ambientes

| Ambiente | Defaults de bancos | Console |
| --- | --- | --- |
| `development` (default) | SQL local e Mongo `localhost:27018` apenas se a variável estiver ausente. Vazio explícito não recebe default. | Ligado por padrão. |
| `test` | Sem URIs locais automáticas; processo em test ignora `.env`. | Ligado por padrão. |
| `staging` / `production` | Exigem conexões explícitas para cada componente utilizado. | Desligado por padrão. |

`DELTA_PLAYGROUND_ENABLED=true/false` sobrescreve o default do console. Habilitado, ele não exige Bearer; precisa de ambiente restrito. O Dockerfile define `APP_ENV=production`.

## Geração e Juiz

| Variável | Default no código | Uso |
| --- | --- | --- |
| `LLM_PROVIDER` | `openai` | Seleciona modo OpenAI ou Gemini. |
| `OPENAI_MODEL` | `gpt-6-luna` | Modelo generativo OpenAI. |
| `OPENAI_REASONING_EFFORT` | `medium` | Raciocínio geral e segundo juiz OpenAI. |
| `OPENAI_FAST_REASONING_EFFORT` | `low` | Guarda, roteador, síntese, metadados e resumos. Vazio usa geral. |
| `OPENAI_SPECIALIST_REASONING_EFFORT` | `high` | Especialistas. Vazio usa geral. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Especialista no modo Gemini. |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2-preview` | Embeddings, inclusive no modo OpenAI. |
| `GROQ_SPECIALIST_MODEL` | `openai/gpt-oss-120b` | Fallback especialista. |
| `GROQ_FAST_MODEL` | `openai/gpt-oss-20b` | Papel rápido no modo Gemini. |
| `LLM_FALLBACK_ENABLED` | `true` | Habilita fallback quando configurado. |
| `LLM_TIMEOUT_SECONDS` | `15` | Timeout por tentativa. |
| `LLM_MAX_RETRIES` | `1` | Retries adicionais por provedor. |
| `LLM_MAX_OUTPUT_TOKENS` | `4096` | Limite de saída da aplicação. |
| `JEV_MODEL` | `jev-1.14.0` | Juiz TypeSafe. |
| `JEV_TIMEOUT_SECONDS` | `5` | Timeout do classificador Jev. |
| `JEV_CONFIDENCE_THRESHOLD` | `0.70` | Encaminha baixa confiança ao segundo juiz. |
| `JEV_PROBABILITY_THRESHOLD` | `0.70` | Probabilidade mínima da gravidade. **`.env.example` usa `0.50`.** |
| `JEV_FACTS_SUPPORTED_THRESHOLD` | `0.60` | Suporte factual mínimo. |
| `JEV_RELEVANCE_THRESHOLD` | `0.25` | Relevância mínima. |
| `JUDGE_SPECIALIST_MODEL` | `gemini-2.5-flash` | Segundo juiz no modo Gemini. |

Chaves: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY` e `TYPESAFE_API_KEY`, sem segredo default. Configure apenas caminhos utilizados e seus fallbacks. Veja [modelos](llm-models.md) e [Juiz](agente-juiz.md).

## Bancos, RAG e MCP

| Variável | Default / regra |
| --- | --- |
| `DATABASE_URL` | URI SQL local em development quando ausente; é o formato usado pelo conector atual. |
| `DB_CONNECT_TIMEOUT_SECONDS` | 5 segundos. |
| `DB_QUERY_TIMEOUT_SECONDS` | 30 segundos. |
| `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` / `DB_POOL_WAIT_SECONDS` | 1 / 10 / 5, por processo. |
| `MONGODB_APP_URI` / `MONGODB_TELEMETRY_URI` | Dois alvos; local `mongodb://localhost:27018` apenas em development e se ausentes. |
| `MONGO_DB_APP` / `MONGO_DB_TELEMETRY` | `db_delta_app` / `db_delta_telemetry`. |
| `QDRANT_URL` / `QDRANT_API_KEY` | Sem URL remota default. RAG exige destino explícito; memória longa pode usar localhost. |
| `RAG_DOCUMENT_PATH` | `app/knowledge/delta-main-source.md`, relativo à raiz da IA. |
| `MCP_EXTERNAL_ENABLED` | `false`. |
| `MCP_TIMEOUT_SECONDS` / `MCP_CACHE_TTL_SECONDS` | 45 segundos / 3600 segundos. |

As antigas variáveis SQL separadas `HOST_DB`, `PORT_DB`, `USER_DB`, `PASSWORD_DB`, `NAME_DB` não são o contrato do conector desta revisão. Os CLIs `scripts.check_postgres` e `scripts.check_mongo` citados anteriormente não estão na árvore atual.

## Autenticação e CORS

`AUTH_PUBLIC_KEY` recebe chave pública RSA/PEM ou caminho; `AUTH_ISSUER=delta-api`, `AUTH_AUDIENCE=delta-api`, `AUTH_KEY_ID=delta-1` e `AUTH_CHECK_ACTIVE=true` controlam a validação RS256. `AUTH_KEY_ID` vazio desliga a comparação de `kid`. `JWT_SECRET` só permite HS256 em development/test, com 32 ou mais caracteres e sem chave pública definida.

`CORS_ALLOWED_ORIGINS` é lista por vírgula; vazio/padrão `*` permite qualquer origem, sem cookies (`allow_credentials=False`). Consulte o [contrato da API](implementacao-api-fastapi.md).

## Observabilidade e recarga

`OBS_SUPPORT_COST_USD=8.01`, `OBS_QUESTIONS_PER_USER_WEEK=0`, `OBS_USD_TO_BRL=5.4212`, `OBS_LATENCY_P95_LIMIT_MS=15000` e `OBS_ERROR_RATE_LIMIT=0.05` são premissas configuradas. `OBS_PRICES_JSON` sobrescreve preços internos. São valores do código, sem atualização externa automática.

`OBS_HASH_SECRET` de pelo menos 16 caracteres habilita hash de usuários. `LANGSMITH_TRACING=false`, `LANGSMITH_PROJECT=delta-ai` e `LANGSMITH_SEND_CONTENT=false` mantêm tracing opcional e conteúdo oculto por padrão; a chave é `LANGSMITH_API_KEY`.

Reinicie a API depois de trocar configurações em operação. Em testes/diagnósticos no mesmo processo, recarregar settings exige descartar/fechar caches afetados: modelos gerais, OpenAI, RAG, segundo juiz, pool SQL e Mongo têm funções próprias; memória longa mantém caches separados. Faça isso sem requisições em andamento. O `lifespan` atual não encerra todos esses caches, conforme [índice da revisão](leia-me.md).

## Fontes da implementação revisada

- [app/config.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/config.py)
- [.env.example](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/.env.example)
