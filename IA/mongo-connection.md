# Conexão MongoDB

`app/data/db_mongo.py` mantém dois clientes lazy: um para a aplicação e outro
para telemetria. O cliente é criado no primeiro uso, reutilizado pelo processo
e não executa ping durante o import do módulo. Em produção, configure URIs
independentes para os clusters Atlas; no ambiente local, ambos podem apontar
para o mesmo serviço e usar databases diferentes.

## Configuração

Configure as variáveis de ambiente ou copie os valores de desenvolvimento de
`.env.example` para `.env`:

| Variável | Uso |
| --- | --- |
| `MONGODB_APP_URI` | URI do cluster que contém preferências e alertas. |
| `MONGODB_TELEMETRY_URI` | URI independente do cluster de telemetria. |
| `MONGO_DB_APP` | Database da aplicação, padrão `db_delta_app` em desenvolvimento. |
| `MONGO_DB_TELEMETRY` | Database de telemetria, padrão `db_delta_telemetry` em desenvolvimento. |
| `DB_CONNECT_TIMEOUT_SECONDS` | Tempo de seleção do servidor e conexão; convertido para milissegundos no driver. |
| `DB_QUERY_TIMEOUT_SECONDS` | Limite de leitura; aplicado como timeout de socket e `maxTimeMS`. |

As URIs são validadas separadamente antes de criar cada cliente. `APP_ENV=test`
não usa valores padrão locais nem lê `.env`; passe as configurações necessárias
explicitamente nesse ambiente. As mensagens de falha não incluem URI,
credenciais ou detalhes internos do driver.

As consultas mantêm os filtros por `user_id` e as ordenações atuais. Se a
consulta falhar, o acesso a dados levanta uma exceção segura; ela não é
convertida em lista vazia ou ausência legítima. Documentos que não atendem aos
campos obrigatórios produzem `DatabaseDataError`, uma subclasse de
`DatabaseQueryError`. O fechamento explícito é feito por
`app.data.db_mongo.close_clients()`, que fecha os dois clientes e limpa ambos
os caches.

## Verificação atual

O CLI `python -m scripts.check_mongo` e seu modo `--fixture` não fazem parte do serviço. Os comandos anteriormente documentados foram retirados deste guia para evitar instrução inexistente.

`tests/conftest.py` tem fixture com MongoDB real para histórico, `DELTA_TEST_MONGO_URI` (default `mongodb://localhost:27018`) e database **`delta_test_historico`**. Ela apaga esse database de teste no preparo/limpeza. Execute esses testes somente contra serviço descartável destinado aos testes; o nome fixo pode colidir com outra execução.

Sem Mongo acessível, esses casos são pulados. A suíte verde com skips não prova persistência real. Outros testes usam substitutos para filtros, conversão e falhas.

## Registro de verificação de conectividade

Em 4 de outubro de 2026, `python -m scripts.check_mongo` terminou com código
1. Os alvos `app` e `telemetry` retornaram a mensagem segura de falha de
conexão. O ambiente local não tinha `.env` nem variáveis de banco configuradas;
os padrões de desenvolvimento apontaram para `localhost:27018`, mas o Docker
Engine estava desligado e não havia serviço escutando nessa porta. O comando
não tentou reconectar nem acessar clusters Atlas.

Naquela execução, ping e leitura real de coleção com documento sintético ficaram
pendentes. Os 26 testes de `db_mongo` substituem clientes, databases e
coleções; outros 3 testes cobrem o CLI, incluindo a falha independente de um
alvo e a limpeza exata da fixture. Esses testes verificam filtros, ordenações,
conversão, erros e recusa de alvos não isolados, sem comprovar conectividade
real. A suíte completa, executada com
`python -m pytest -q -p no:cacheprovider`, terminou com 122 testes aprovados e
uma advertência de depreciação da dependência `google.genai`.

O comando e as contagens de testes acima descrevem essa execução anterior, não uma instrução para executar um módulo ausente. Os scripts de diagnóstico antigos não fazem parte do serviço.

## Dados usados

- Telemetria: janelas em `consumption_summary`, filtradas pelo usuário e recorte temporal.
- App: preferências e meta diária, `alerts_history`, `weather_daily`, `chat_sessions` e `observability_requests`, conforme cada consumidor.
- Clima é histórico armazenado por localização; não é chamada meteorológica em tempo real.
- Sessões validam ObjectId, proprietário e exclusão lógica; detalhes em [memória](implementacao-memoria-sessoes.md).

Falha de conexão ou autorização não vira lista vazia legítima. `_run_query` traduz erros de driver e documentos inválidos para exceções seguras; documento inválido pode gerar `DatabaseDataError`. As ferramentas podem traduzir isso para um status de indisponibilidade, conforme seu contrato.

## Fechamento e persistência

`close_clients` fecha os dois clientes inicializados e limpa caches, tentando encerrar ambos mesmo se um falhar. A função existe, mas não está ligada ao `lifespan` atual da API. Não confunda disponibilidade da função com execução automática no encerramento.

Schema, índices, permissões e TTL precisam ser aplicados pelo responsável do banco; a IA não é substituto dos scripts oficiais do `delta-mongo-database`. A gravação de histórico e de métricas tem caminhos próprios e pode falhar sem impedir a resposta final do chatbot.

## Código relacionado

- [app/data/db_mongo.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/data/db_mongo.py)
- [tests/conftest.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/tests/conftest.py)
