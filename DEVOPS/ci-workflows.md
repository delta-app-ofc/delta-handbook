# Workflows de CI do Delta

Esta página reúne o que os workflows de integração contínua executam e como reproduzir localmente. A validação de checklist e encaminhamento de revisores segue separada nos workflows organizacionais já existentes. Estes CIs rodam em pull requests e, quando indicado no workflow, também podem ser acionados manualmente.

## Aplicações e serviços

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `delta-api-postgres` | Suíte Maven existente em Java 17, executada em container com H2. Não comprova compatibilidade completa com PostgreSQL, schema e procedures oficiais ou integrações externas. | Na raiz: `docker compose -f docker-compose.test.yml config --quiet`, `docker compose -f docker-compose.test.yml run --build --rm tests`. Depois: `docker compose -f docker-compose.test.yml down`. |
| `delta-api-mongo` | Suíte padrão Maven com Java 17. Os testes HTTP que precisam de MongoDB real são opt-in e não entram neste CI. | Java 17: `bash ./mvnw --batch-mode --no-transfer-progress test` (Linux/macOS) ou `mvnw.cmd test` (Windows). |
| `delta-artificial-intelligence` | Instala dependências de desenvolvimento com Python 3.12, roda `pip check`, compila `app` e executa `tests/` com `APP_ENV=test`. Os testes atuais cobrem dois cenários isolados de previsão, sem bancos ou provedores externos. | `python -m pip install -r requirements-dev.txt`; defina `APP_ENV=test`; rode `python -m pip check`, `python -m compileall -q app` e `python -m unittest discover -s tests -v`. |
| `delta-business-rules` | Suíte pytest em Python 3.12. Usa dados locais e não conecta a PostgreSQL, MongoDB ou Change Streams reais. | `python -m pip install -r requirements-dev.txt`; `python -m pytest -q`. |
| `delta-redis-database` | Suíte pytest em Python 3.12 com Redis 7 descartável. Exercita endpoints e ranking; as respostas da API PostgreSQL usadas nos testes de sincronização são simuladas. | Com Python 3.12, Docker e Compose: `docker compose -f docker-compose.dev.yml up -d`; `python -m pip install -r requirements.txt -r requirements-dev.txt`; `python -m pytest -q`; `docker compose -f docker-compose.dev.yml down`. Os testes limpam o banco lógico 1 de `localhost:6379`; use uma instância descartável. |
| `delta-web-app` | `npm ci`, testes, lint e build com Node 22. Testes usam respostas simuladas; não validam backend real nem navegador. | Com Node 22: `npm ci`, `npm test`, `npm run lint`, `npm run build`. |
| `delta-mobile-app` | Confere se `README.md`, `AGENTS.md` e `LICENSE` existem, estão em UTF-8 e não estão vazios. A `main` atual ainda não contém código mobile nem ferramenta de build. | Na raiz: `python -c "from pathlib import Path; files = ('README.md', 'AGENTS.md', 'LICENSE'); [(print('OK:', f) if Path(f).read_text(encoding='utf-8').strip() else (_ for _ in ()).throw(ValueError(f'{f} vazio'))) for f in files]"`. Atualize o CI quando houver build e testes reais de aplicativo. |
| `delta-rpa` | Testes pytest e execução do pipeline contra PostgreSQLs descartáveis do Compose. Não compara automaticamente os registros migrados com um resultado esperado e não comprova funcionamento com bancos de produção. | `python -m pip install -r requirements-dev.txt`; `python -m pytest`; `docker compose -p delta-rpa-ci -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from rpa`; `docker compose -p delta-rpa-ci -f docker-compose.test.yml down -v`. |
| `delta-hardware-data-simulator` | Compila módulos Python e executa o smoke test Compose em `dry-run`. Não verifica inserções, todos os validadores MongoDB ou todos os geradores; `chat_feedback` consulta MongoDB mesmo em `dry-run` e fica fora desse smoke test. | `python -m compileall -q dataload`; `docker compose -f docker-compose.test.yml run --build --rm dry-run`. |

## Bancos de dados

Use Docker Engine e Docker Compose v2 ativos para os comandos que iniciam serviços. Os bancos de teste são descartáveis e não usam credenciais de produção.

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `delta-sql-database` | PostgreSQL 16 temporário. Carrega schema, otimização, auditoria e roles; verifica tabelas, FK, função `fn_user_is_active` e constraint de região. Não cobre todas as funções, procedures, triggers, permissões ou dataload. | `docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from smoke`; depois `docker compose -f docker-compose.test.yml down --volumes --remove-orphans`. |
| `delta-mongo-database` | MongoDB temporário. Aplica coleções e índices; verifica presença, validadores e rejeição de documento inválido em `user_preferences`. Não acessa Atlas nem executa roles/seeds. | `docker compose -p delta-mongo-ci -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from runner`; depois `docker compose -p delta-mongo-ci -f docker-compose.test.yml down`. |
| `delta-neo4j-database` | Neo4j 5 temporário. Compila `load_graph.py`, carrega setup e seed e verifica quantidades de usuários, dias e relações. Não acessa Aura nem cobre todas as consultas e regras. O setup apaga os nós do banco selecionado: nunca o execute em produção. | Configure `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` e `NEO4J_DATABASE` para um Neo4j descartável; instale `neo4j` e `python-dotenv`; rode `python -m py_compile load_graph.py`, `python load_graph.py setup.cypher` e `python load_graph.py seed.cypher`. |

## Documentação, governança e template

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `.github` | Compilação dos scripts Python e 12 testes unitários existentes. Os testes usam respostas simuladas e não chamam a API do GitHub. A governança local continua em `local_checks.yml`. | `python -m compileall -q scripts tests`; `python -m unittest discover -s tests -v`. |
| `delta-business-intelligence` | Sintaxe dos scripts Python em `v1` com Python 3.9, sem executá-los ou conectar a bancos, Glue ou Databricks. | `python -m compileall -q v1`. |
| `delta-handbook` | Arquivos Markdown rastreados pelo Git: leitura UTF-8, conteúdo não vazio e marcadores comuns de conflito. Não valida links, sintaxe Markdown completa ou correção do conteúdo. Arquivos novos precisam estar no índice Git para a validação local incluí-los. | `python scripts/validate_markdown.py`. |
| `delta-template-repository` | Sintaxe YAML, `LICENSE` e `.gitignore` não vazios e regras essenciais de ignore para `.env`, `node_modules`, `target` e a exceção `.env.example`. A análise YAML não verifica semântica do Actions. | Com Ruby e Git: `ruby -e 'require "psych"; Dir.glob(".github/workflows/*.{yml,yaml}").each { |f| Psych.parse_file(f); puts "OK: #{f}" }'`; `test -s LICENSE && test -s .gitignore`; valide as regras com `git check-ignore --no-index`. |

## Falhas vistas na primeira execução

Na primeira execução das novas PRs, o smoke test de `delta-sql-database` falhou porque `script-roles.sql` referencia o schema `stage`, que não existe no banco temporário criado pelo Compose. Em `delta-rpa`, os testes unitários passaram, mas o pipeline com fixtures tentou inserir `NULL` em `tb_user_property.property_id`, que é obrigatório. Os workflows reportam essas falhas em vez de ignorá-las. Consulte as PRs correspondentes para o estado atual dos checks.
