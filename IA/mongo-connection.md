# Conexão MongoDB da IA

## Objetivo e clientes

Descrever `app/data/db_mongo.py` e seus consumidores na `main` `f6f3d8c` (02/11/2026). Há clientes lazy separados de app e telemetria, criados no primeiro uso e reutilizados por processo. O import não executa ping.

| Variável | Uso |
| --- | --- |
| `MONGODB_APP_URI` | Alvo de dados do aplicativo. |
| `MONGODB_TELEMETRY_URI` | Alvo de telemetria. |
| `MONGO_DB_APP` | Database de app, default `db_delta_app`. |
| `MONGO_DB_TELEMETRY` | Database de telemetria, default `db_delta_telemetry`. |
| `DB_CONNECT_TIMEOUT_SECONDS` | Seleção de servidor e conexão, convertido em ms. |
| `DB_QUERY_TIMEOUT_SECONDS` | Timeout de socket e limites de consultas aplicados no acesso de dados. |

Em desenvolvimento, URIs ausentes podem apontar para `localhost:27018`; em staging/produção são explícitas. `APP_ENV=test` não fornece URI local automaticamente. Os clientes usam `tz_aware=True`.

## Dados usados

- Telemetria: janelas em `consumption_summary`, filtradas pelo usuário e recorte temporal.
- App: preferências e meta diária, `alerts_history`, `weather_daily`, `chat_sessions` e `observability_requests`, conforme cada consumidor.
- Clima é histórico armazenado por localização; não é chamada meteorológica em tempo real.
- Sessões validam ObjectId, proprietário e exclusão lógica; detalhes em [memória](implementacao-memoria-sessoes.md).

Falha de conexão ou autorização não vira lista vazia legítima. `_run_query` traduz erros de driver e documentos inválidos para exceções seguras; documento inválido pode gerar `DatabaseDataError`. As ferramentas podem traduzir isso para um status de indisponibilidade, conforme seu contrato.

## Fechamento e persistência

`close_clients` fecha os dois clientes inicializados e limpa caches, tentando encerrar ambos mesmo se um falhar. A função existe, mas não está ligada ao `lifespan` atual da API. Não confunda disponibilidade da função com execução automática no encerramento.

Schema, índices, permissões e TTL precisam ser aplicados pelo responsável do banco; a IA não é substituto dos scripts oficiais do `delta-mongo-database`. A gravação de histórico e de métricas tem caminhos próprios e pode falhar sem impedir a resposta final do chatbot.

## Verificação atual

O CLI `python -m scripts.check_mongo` e seu modo `--fixture` não estão na árvore revisada. Os comandos anteriormente documentados foram retirados deste guia para evitar instrução inexistente.

`tests/conftest.py` tem fixture com MongoDB real para histórico, `DELTA_TEST_MONGO_URI` (default `mongodb://localhost:27018`) e database **`delta_test_historico`**. Ela apaga esse database de teste no preparo/limpeza. Execute esses testes somente contra serviço descartável destinado aos testes; o nome fixo pode colidir com outra execução.

Sem Mongo acessível, esses casos são pulados. A suíte verde com skips não prova persistência real. Outros testes usam substitutos para filtros, conversão e falhas. Nenhum ping, leitura, fixture ou alteração de cluster foi executado nesta revisão documental.

## Fontes da implementação revisada

- [app/data/db_mongo.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/data/db_mongo.py)
- [tests/conftest.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/tests/conftest.py)
