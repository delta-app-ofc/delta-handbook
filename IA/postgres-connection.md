# Conexão PostgreSQL da IA

## Objetivo e configuração

Documentar `app/data/db_postgres.py` na `main` de IA `f6f3d8c`, revisada em 02/11/2026. O caminho normal usa **pool por processo**, criado no primeiro uso com `psycopg2.pool.ThreadedConnectionPool`; não abre uma conexão independente por operação.

Use `DATABASE_URL`, preservando opções de URI como TLS. A interface antiga de cinco variáveis separadas não é usada por este conector. Não copie credenciais reais para documentação.

| Variável | Default | Aplicação |
| --- | --- | --- |
| `DB_CONNECT_TIMEOUT_SECONDS` | 5 | `connect_timeout` ao abrir conexão. |
| `DB_QUERY_TIMEOUT_SECONDS` | 30 | `statement_timeout` local à transação, via `set_config`. |
| `DB_POOL_MIN_SIZE` | 1 | Conexões iniciais. |
| `DB_POOL_MAX_SIZE` | 10 | Limite e retenção máxima de conexões no pool. |
| `DB_POOL_WAIT_SECONDS` | 5 | Espera por vaga no semáforo do pool. |

`workers × DB_POOL_MAX_SIZE` precisa caber na capacidade disponível do servidor, considerando também outras aplicações. O pool não é compartilhado entre workers.

## Ciclo de uma operação

`_cursor` adquire uma vaga, obtém conexão, prepara timeout transacional e entrega cursor. Sucesso faz commit; a limpeza fecha cursor, devolve ou descarta conexão e libera vaga. Transação aberta após falha é desfeita ao devolver conexão saudável ao pool.

Uma conexão quebrada pode ser trocada uma vez **antes de executar o SQL da operação**. Esse preparo não repete uma escrita já concluída. Erros de driver viram exceções públicas seguras; ausência de linha não deve ser confundida com indisponibilidade.

`close_pool` fecha conexões e permite recriação, inclusive após recarga controlada de settings. A API o chama no `lifespan`. `get_conn` permanece como conexão direta de diagnóstico, fora do pool.

## Consultas e dependências

A IA depende de cadastro ativo, vínculos, unidades autorizadas, tarifas, contas e hábitos. Consumo/previsão organizacionais leem camada consolidada SQL, incluindo `dw.vw_ft_consumption_daily` e funções auxiliares. Cadastro de hábito usa `fn_create_user_habit`, cuja disponibilidade e permissão precisam ser conferidas no banco alvo.

Consultas usam parâmetros e IDs vinculados ao usuário. A seleção de unidade precisa ocorrer antes da leitura. Não ter dados suficientes é diferente de falha de conexão ou função/view ausente.

## Diagnóstico e bootstrap local

O CLI `scripts.check_postgres` não existe nessa revisão. O diagnóstico versionado disponível é `python -m scripts.bench_pool`; é benchmark com acesso real e deve ser usado somente contra um banco de teste configurado, conforme o próprio script. Conexão simples não valida schema completo ou dados do produto.

`docker-compose.dev.yml` oferece SQL local. `db/postgres-init/` tem seis scripts de bootstrap nesta `main` (01 a 06). São cópias para desenvolvimento; a fonte oficial é o repositório `delta-sql-database`. Não assuma que a cópia local tem todas as migrações/funções recentes do banco oficial.

`test_pg_pool.py` e `test_database_adapters.py` verificam comportamento com substitutos. Não foi executada conexão real nesta revisão documental. Veja [operação](operacao-validacao.md) e [redução de latência](reducao-latencia.md) para metodologia e medições históricas identificadas.

## Fontes da implementação revisada

- [app/data/db_postgres.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/data/db_postgres.py)
- [scripts/bench_pool.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/scripts/bench_pool.py)
