# Configuração da aplicação

`app/config.py` reúne as variáveis de ambiente em `Settings`. O carregamento não abre conexões nem exige credenciais: cada caminho valida apenas o componente que vai usar. Isso mantém imports, cálculos puros e agentes com LLM falso independentes de bancos e provedores reais.

## Precedência e recarga

As variáveis do processo prevalecem sobre o arquivo `.env`. Em desenvolvimento, o módulo lê `.env` sem alterar `os.environ`; quando `APP_ENV=test` está definido no processo, não lê nenhum arquivo `.env`, mesmo quando passado explicitamente. Uma chamada `load_settings(environ=...)` usa apenas o mapa recebido, sem ler arquivo por padrão, para permitir testes isolados. Um caminho de arquivo pode ser passado explicitamente para testar a precedência com dados temporários.

`get_settings()` devolve um snapshot em cache. Use `get_settings(refresh=True)` depois de alterar variáveis durante a execução; não recarregue por requisição. Acesse os campos desse snapshot para ler os valores efetivos. `reload_settings()`, `clear_settings_cache()` e os antigos aliases uppercase não fazem parte dessa interface.

A representação de `Settings` omite chaves, senhas e URIs de conexão. Erros de validação identificam os nomes das variáveis, sem incluir seus valores. A checagem das URIs é local e sintática; não tenta conectar nem consultar DNS.

## Comportamento por ambiente

| `APP_ENV` | Comportamento |
| --- | --- |
| `development` (padrão) | Pode usar os serviços descartáveis definidos em `docker-compose.dev.yml`: PostgreSQL local e as duas URIs Mongo locais. O fallback local só é aplicado quando a variável correspondente não foi informada. |
| `test` | Não usa defaults locais e não lê `.env`. Testes isolados injetam valores sintéticos com `load_settings(environ=...)` ou `monkeypatch`; casos de histórico também podem usar MongoDB real descartável e ser pulados quando ele falta. |
| `staging` / `production` | Não recebe URI local automaticamente. O componente precisa de configuração explícita antes de ser usado. Os nomes dos bancos Mongo mantêm os defaults `db_delta_app` e `db_delta_telemetry`. |

Em desenvolvimento, `DATABASE_URL` usa a conta pública e descartável do container local quando a variável está ausente. A conexão é configurada por essa URI; o conector não usa o conjunto antigo de variáveis SQL separadas.

As conexões Mongo de aplicação e telemetria sempre permanecem independentes. Os dois exemplos locais podem apontar para o mesmo container; staging e produção devem informar cada URI do cluster correspondente.

## Variáveis disponíveis

| Variável | Default | Regra de uso |
| --- | --- | --- |
| `APP_ENV` | `development` | Aceita `development`, `test`, `staging` ou `production`. |
| `GEMINI_API_KEY` | vazio | Exigida ao selecionar o caminho Gemini. Sem segredo default. |
| `GROQ_API_KEY` | vazio | Exigida para o caminho rápido Groq, Groq especialista ou fallback Groq habilitado. |
| `DATABASE_URL` | URI do PostgreSQL local em desenvolvimento | A URI inteira é repassada para preservar senha codificada e opções como TLS. |
| `MONGODB_APP_URI` | `mongodb://localhost:27018` em desenvolvimento | Cluster Mongo de dados do aplicativo. |
| `MONGODB_TELEMETRY_URI` | `mongodb://localhost:27018` em desenvolvimento | Cluster Mongo de telemetria; variável separada da URI de aplicação. Aceita `mongodb://` com vários hosts e `mongodb+srv://`. |
| `MONGO_DB_APP` | `db_delta_app` | Nome não vazio do banco de aplicação. |
| `MONGO_DB_TELEMETRY` | `db_delta_telemetry` | Nome não vazio do banco de telemetria. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo configurável para o provedor Gemini. |
| `GROQ_SPECIALIST_MODEL` | `openai/gpt-oss-120b` | Modelo configurável para o caminho especialista Groq. |
| `GROQ_FAST_MODEL` | `openai/gpt-oss-20b` | Modelo configurável para o caminho rápido Groq. |
| `LLM_FALLBACK_ENABLED` | `true` | Aceita explicitamente `true` ou `false`. |
| `LLM_TIMEOUT_SECONDS` | `15` | Tempo positivo em segundos. |
| `LLM_MAX_RETRIES` | `1` | Número inteiro não negativo. |
| `LLM_MAX_OUTPUT_TOKENS` | `4096` | Limite inteiro positivo de saída. |
| `DB_CONNECT_TIMEOUT_SECONDS` | `5` | Timeout inteiro positivo de conexão com banco. |
| `DB_QUERY_TIMEOUT_SECONDS` | `30` | Timeout inteiro positivo para operações de banco. |

Temperatura e `top_p` do modo Gemini/Groq são parâmetros fixos; OpenAI usa configuração de raciocínio por papel. A seleção dos modelos e os parâmetros LLM são aplicados em `app/services/llms.py`; os drivers PostgreSQL/MongoDB aplicam os timeouts de banco. Consulte [provedores](llm-models.md), [PostgreSQL](postgres-connection.md) e [MongoDB](mongo-connection.md) para a semântica de cada parâmetro.

## Validação por componente

```python
from app.config import (
    validate_llm_config,
    validate_mongo_config,
    validate_postgres_config,
)

validate_llm_config("specialist")  # provedor selecionado e fallback aplicável
validate_llm_config("gemini")      # somente Gemini
validate_llm_config("fast")        # papel rápido do provedor selecionado
validate_postgres_config()          # DATABASE_URL e parâmetros do pool
validate_mongo_config("app")       # URI e nome do banco de aplicação
validate_mongo_config("telemetry") # URI e nome do banco de telemetria

```

Os validadores lançam `ConfigurationError` se o componente não estiver pronto. Eles verificam esquema de URI, variáveis obrigatórias, nomes e intervalos numéricos sem tentar conectar. Chamadas isoladas devem usar o validador do componente correspondente.

Defina `APP_ENV=test` no processo para impedir leitura de `.env`. `tests/conftest.py` configura fixtures de histórico e autenticação; não se deve assumir que ele apaga toda variável herdada ou torna todos os casos independentes de banco.

## Geração e Juiz

| Variável | Default no código | Uso |
| --- | --- | --- |
| `LLM_PROVIDER` | `openai` | Seleciona modo OpenAI ou Gemini. |
| `OPENAI_MODEL` | `gpt-6-luna` | Modelo generativo OpenAI. |
| `OPENAI_REASONING_EFFORT` | `medium` | Raciocínio geral e segundo juiz OpenAI. |
| `OPENAI_FAST_REASONING_EFFORT` | `low` | Guarda, roteador, síntese, metadados e resumos. Vazio usa geral. |
| `OPENAI_SPECIALIST_REASONING_EFFORT` | `high` | Especialistas. Vazio usa geral. |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2-preview` | Embeddings, inclusive no modo OpenAI. |
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
| `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` / `DB_POOL_WAIT_SECONDS` | 1 / 10 / 5, por processo. |
| `MONGODB_APP_URI` / `MONGODB_TELEMETRY_URI` | Dois alvos; local `mongodb://localhost:27018` apenas em development e se ausentes. |
| `MONGO_DB_APP` / `MONGO_DB_TELEMETRY` | `db_delta_app` / `db_delta_telemetry`. |
| `QDRANT_URL` / `QDRANT_API_KEY` | Sem URL remota default. RAG exige destino explícito; memória longa pode usar localhost. |
| `RAG_DOCUMENT_PATH` | `app/knowledge/delta-main-source.md`, relativo à raiz da IA. |
| `MCP_EXTERNAL_ENABLED` | `false`. |
| `MCP_TIMEOUT_SECONDS` / `MCP_CACHE_TTL_SECONDS` | 45 segundos / 3600 segundos. |

As antigas variáveis SQL separadas `HOST_DB`, `PORT_DB`, `USER_DB`, `PASSWORD_DB`, `NAME_DB` não são usadas pelo conector. Os CLIs `scripts.check_postgres` e `scripts.check_mongo` citados anteriormente não fazem parte do serviço.

## Autenticação e CORS

`AUTH_PUBLIC_KEY` recebe chave pública RSA/PEM ou caminho; `AUTH_ISSUER=delta-api`, `AUTH_AUDIENCE=delta-api`, `AUTH_KEY_ID=delta-1` e `AUTH_CHECK_ACTIVE=true` controlam a validação RS256. `AUTH_KEY_ID` vazio desliga a comparação de `kid`. `JWT_SECRET` só permite HS256 em development/test, com 32 ou mais caracteres e sem chave pública definida.

`CORS_ALLOWED_ORIGINS` é lista por vírgula; vazio/padrão `*` permite qualquer origem, sem cookies (`allow_credentials=False`). Consulte o [contrato da API](implementacao-api-fastapi.md).

## Observabilidade e recarga

`OBS_SUPPORT_COST_USD=8.01`, `OBS_QUESTIONS_PER_USER_WEEK=0`, `OBS_USD_TO_BRL=5.4212`, `OBS_LATENCY_P95_LIMIT_MS=15000` e `OBS_ERROR_RATE_LIMIT=0.05` são premissas configuradas. `OBS_PRICES_JSON` sobrescreve preços internos. São valores do código, sem atualização externa automática.

`OBS_HASH_SECRET` de pelo menos 16 caracteres habilita hash de usuários. `LANGSMITH_TRACING=false`, `LANGSMITH_PROJECT=delta-ai` e `LANGSMITH_SEND_CONTENT=false` mantêm tracing opcional e conteúdo oculto por padrão; a chave é `LANGSMITH_API_KEY`.

Reinicie a API depois de trocar configurações em operação. Em testes/diagnósticos no mesmo processo, recarregar settings exige descartar/fechar caches afetados: modelos gerais, OpenAI, RAG, segundo juiz, pool SQL e Mongo têm funções próprias; memória longa mantém caches separados. Faça isso sem requisições em andamento. O `lifespan` atual não encerra todos esses caches, conforme os [pontos de atenção](leia-me.md).

## Código relacionado

- [app/config.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/config.py)
- [.env.example](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/.env.example)
