# Conexão PostgreSQL

O módulo `app/data/db_postgres.py` empresta conexões de um pool `psycopg2.pool.ThreadedConnectionPool` por processo. Cria o pool no primeiro uso, fecha o cursor de cada operação e devolve a conexão ao concluir ou falhar. A aplicação chama `close_pool()` no encerramento.

## Configuração

Use `DATABASE_URL` para uma URI PostgreSQL completa. A URI é passada ao `psycopg2` sem ser remontada, preservando opções como TLS e senhas percent-encoded. O conector não lê as cinco variáveis SQL separadas anteriormente usadas.

Os limites são definidos em segundos:

| Variável | Aplicação |
| --- | --- |
| `DB_CONNECT_TIMEOUT_SECONDS` | Passado ao `psycopg2` como `connect_timeout`, em segundos. |
| `DB_QUERY_TIMEOUT_SECONDS` | Convertido para milissegundos e aplicado à sessão PostgreSQL como `statement_timeout`. |

O `statement_timeout` é configurado localmente à transação via `set_config`, para não vazar entre usos do pool. O timeout de conexão limita a abertura da conexão; o timeout de consulta limita a execução no servidor.

## Verificação

Com as variáveis de ambiente configuradas e um PostgreSQL de teste acessível, o benchmark de leitura permite verificar conexão direta e pool:

```bash
python -m scripts.bench_pool --ops 20 --threads 2
```

Ele executa `SELECT 1` sem depender das tabelas do produto e compara operações diretas com o pool. Não exige LLM. O antigo `scripts.check_postgres` não faz parte do serviço.

Uma resposta de `SELECT 1` confirma conectividade, autenticação e acesso ao banco
indicado. Ela não comprova que esse banco tenha as tabelas e funções usadas pelo
Agente de Previsão.

Na execução de **4 de outubro de 2026**, o antigo diagnóstico `scripts.check_postgres` retornou código 1 com o
diagnóstico seguro `Não foi possível conectar ao PostgreSQL.`. O Docker Engine
local estava indisponível, a porta local 5432 não tinha serviço escutando e
esta execução não dispunha de `DATABASE_URL` nem das variáveis separadas. A
configuração padrão de desenvolvimento apontou para o serviço local. Portanto,
o `SELECT 1` real ficou pendente naquela execução, que não acessou o banco oficial. Esse registro não substitui uma verificação do ambiente utilizado.

## Banco local e banco oficial

`docker-compose.dev.yml` oferece um PostgreSQL local para desenvolvimento. Os
arquivos de `db/postgres-init/` são cópias de bootstrap desse ambiente; a fonte
oficial do schema permanece no repositório
[`delta-sql-database`](https://github.com/delta-app-ofc/delta-sql-database). Uma conexão validada no
container local não valida acesso ao PostgreSQL oficial nem garante que suas
views e dados organizacionais estejam disponíveis.

## Ciclo de uma operação

`_cursor` adquire uma vaga, obtém conexão, prepara timeout transacional e entrega cursor. Sucesso faz commit; a limpeza fecha cursor, devolve ou descarta conexão e libera vaga. Transação aberta após falha é desfeita ao devolver conexão saudável ao pool.

Uma conexão quebrada pode ser trocada uma vez **antes de executar o SQL da operação**. Esse preparo não repete uma escrita já concluída. Erros de driver viram exceções públicas seguras; ausência de linha não deve ser confundida com indisponibilidade.

`close_pool` fecha conexões e permite recriação, inclusive após recarga controlada de settings. A API o chama no `lifespan`. `get_conn` permanece como conexão direta de diagnóstico, fora do pool.

## Consultas e dependências

A IA depende de cadastro ativo, vínculos, unidades autorizadas, tarifas, contas e hábitos. Consumo/previsão organizacionais leem camada consolidada SQL, incluindo `dw.vw_ft_consumption_daily` e funções auxiliares. Cadastro de hábito usa `fn_create_user_habit`, cuja disponibilidade e permissão precisam ser conferidas no banco alvo.

Consultas usam parâmetros e IDs vinculados ao usuário. A seleção de unidade precisa ocorrer antes da leitura. Não ter dados suficientes é diferente de falha de conexão ou função/view ausente.

## Código relacionado

- [app/data/db_postgres.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/data/db_postgres.py)
- [scripts/bench_pool.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/scripts/bench_pool.py)
