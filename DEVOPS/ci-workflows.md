# Workflows de CI do Delta

Esta página reúne o que os workflows de integração contínua executam e como reproduzir localmente. A validação de checklist e encaminhamento de revisores segue separada nos workflows organizacionais já existentes. Estes CIs rodam em pull requests e, quando indicado no workflow, também podem ser acionados manualmente.

## Aplicações e serviços

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `delta-api-postgres` | Suíte Maven existente em Java 17, executada em container com H2. Não comprova compatibilidade completa com PostgreSQL, schema e procedures oficiais ou integrações externas. | Na raiz: `docker compose -f docker-compose.test.yml config --quiet`, `docker compose -f docker-compose.test.yml run --build --rm tests`. Depois: `docker compose -f docker-compose.test.yml down`. |
| `delta-api-mongo` | Suíte padrão Maven com Java 17. Os testes HTTP que precisam de MongoDB real são opt-in e não entram neste CI. | Java 17: `bash ./mvnw --batch-mode --no-transfer-progress test` (Linux/macOS) ou `mvnw.cmd test` (Windows). |
| `delta-artificial-intelligence` | 37 testes offline, relatorios JUnit e cobertura de app; bancos e provedores simulados. Cobertura global legada de 26%, sem exclusoes artificiais. | `python -m pip install -r requirements-dev.txt`; `python tests/run_ci.py`. |
| `delta-business-rules` | Suíte pytest em Python 3.12. Usa dados locais e não conecta a PostgreSQL, MongoDB ou Change Streams reais. | `python -m pip install -r requirements-dev.txt`; `python -m pytest -q`. |
| `delta-redis-database` | Suíte pytest em Python 3.12 com Redis 7 descartável. Exercita a API e os rankings; as respostas da API PostgreSQL usadas na sincronização são simuladas. `sonar.yml` publica JUnit e relatórios de cobertura Python. | Com Docker e Compose: `docker compose --env-file docker-compose.test.env -p delta-redis-audit-test -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from tests`; depois `docker compose --env-file docker-compose.test.env -p delta-redis-audit-test -f docker-compose.test.yml down`. Para executar pytest fora do Compose, aponte `TEST_REDIS_URL` para um Redis descartável e defina `TEST_REDIS_ISOLATED=1`; a fixture limpa o banco selecionado. |
| `delta-web-app` | `npm ci`, testes, lint e build com Node 22. Testes usam respostas simuladas; não validam backend real nem navegador. | Com Node 22: `npm ci`, `npm test`, `npm run lint`, `npm run build`. |
| `delta-app-mobile` | Confere se `README.md`, `AGENTS.md` e `LICENSE` existem, estão em UTF-8 e não estão vazios. A `main` não contém código mobile, stack definida nem ferramenta de build. | O mesmo smoke documental do workflow: Python 3, lendo os três arquivos em UTF-8 e rejeitando conteúdo vazio. Acrescente build e testes de aplicativo quando houver código e stack versionados. |
| `delta-mobile-app` | Confere se `README.md`, `AGENTS.md` e `LICENSE` existem, estão em UTF-8 e não estão vazios. A `main` não contém código mobile, stack definida nem ferramenta de build. | O mesmo smoke documental do workflow: Python 3, lendo os três arquivos em UTF-8 e rejeitando conteúdo vazio. Acrescente build e testes de aplicativo quando houver código e stack versionados. |
| `delta-rpa` | Testes pytest e execução do pipeline contra PostgreSQLs descartáveis do Compose. Não compara automaticamente os registros migrados com um resultado esperado e não comprova funcionamento com bancos de produção. | `python -m pip install -r requirements-dev.txt`; `python -m pytest`; `docker compose -p delta-rpa-ci -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from rpa`; `docker compose -p delta-rpa-ci -f docker-compose.test.yml down -v`. |
| `delta-hardware-data-simulator` | 26 testes offline dos geradores e adaptador Mongo, com 99% de cobertura total; preserva dry-run Compose. Nenhum Mongo real e acessado pela suite offline. | `python -m pip install -r requirements-dev.txt`; `python tests/run_ci.py`. |

## Bancos de dados

Use Docker Engine e Docker Compose v2 ativos para os comandos que iniciam serviços. Os bancos de teste são descartáveis e não usam credenciais de produção.

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `delta-sql-database` | PostgreSQL 16 temporário. Executa schema, otimização e auditoria; os smokes validam criação e regras de autorização e contexto organizacional com dados mínimos. Não cobre todas as funções, procedures, triggers, permissões ou dataload. | `docker compose --env-file docker-compose.test.env -p delta-sql-audit-test -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from smoke`; depois `docker compose --env-file docker-compose.test.env -p delta-sql-audit-test -f docker-compose.test.yml down`. |
| `delta-mongo-database` | MongoDB 7 temporário, sem conexão com Atlas. Aplica coleções e índices e executa verificações comportamentais de validação e unicidade em `tests/smoke.js`. `sonar.yml` também analisa estaticamente os scripts JavaScript e publica um JUnit agregado da execução. | `docker compose -p delta-mongo-audit-test -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from runner`; depois `docker compose -p delta-mongo-audit-test -f docker-compose.test.yml down`. |
| `delta-neo4j-database` | Há dois jobs independentes: `test.yml` inicia Neo4j 5 temporário, carrega setup e seed e verifica contagens; `sonar.yml` executa testes unitários do loader Python com driver simulado e publica JUnit e cobertura. O teste unitário não acessa Aura nem mede os arquivos `.cypher`. | Para o job unitário: `python -m pip install -r requirements-dev.txt` e `python -m pytest -q`. O job de integração requer Neo4j descartável e variáveis de conexão de teste; não use Aura ou produção para executar `setup.cypher`. |

## Documentação, governança e template

| Repositório | O que o CI valida | Execução local |
| --- | --- | --- |
| `.github` | 44 testes de governanca e politica Sonar com APIs simuladas, incluindo filtro de gravidade, SHA, aprovacoes e YAML duplicado. | `python -m pip install -r requirements-dev.txt`; `python -m unittest discover -s tests -v`. |
| `delta-business-intelligence` | Sintaxe dos scripts Python em `v1` com Python 3.9, sem executá-los ou conectar a bancos, Glue ou Databricks. | `python -m compileall -q v1`. |
| `delta-handbook` | Valida documentos rastreados e testa o proprio script validador: UTF-8, conteudo vazio, conflitos, falha de leitura/Git. | `python -m pip install -r requirements-dev.txt`; `python tests/run_ci.py`; `python scripts/validate_markdown.py`. |
| `delta-template-repository` | Sintaxe YAML, `LICENSE` e `.gitignore` não vazios e regras essenciais de ignore para `.env`, `node_modules`, `target` e a exceção `.env.example`. A análise YAML não verifica semântica do Actions. O repositório é um scaffold e ainda não contém aplicativo executável. | Com Ruby e Git: `ruby -e 'require "psych"; Dir.glob(".github/workflows/*.{yml,yaml}").each { |f| Psych.parse_file(f); puts "OK: #{f}" }'`; `test -s LICENSE && test -s .gitignore`; valide as regras com `git check-ignore --no-index`. |

## Cobertura de código e limites por repositório

A política compartilhada exige 100% dos testes aprovados e pelo menos 70% de cobertura **somente nas linhas novas ou alteradas que possam ser instrumentadas**. O percentual não representa a cobertura global do repositório. Testes de comportamento e cobertura de linhas são evidências diferentes: não converta asserções em um percentual fictício.

| Repositório | Evidência automatizada | Cobertura de linhas |
| --- | --- | --- |
| `delta-sql-database` | Testes de integração executam scripts em PostgreSQL temporário e verificam comportamentos com dados mínimos. | N/A para percentual de linhas SQL: o fluxo não instrumenta SQL. Os smokes continuam obrigatórios e verificam comportamento real do banco. |
| `delta-mongo-database` | Smoke em MongoDB temporário verifica validação e índices; Sonar analisa estaticamente os scripts JavaScript. | O runner `mongosh` não gera LCOV e não declara percentual. Isso não concede isenção automática para mudanças JavaScript: antes de alterá-los, a cobertura instrumentada deve ser compatibilizada com a política central. |
| `delta-redis-database` | Testes pytest exercitam a aplicação Python contra Redis 7 descartável e produzem JUnit, XML de cobertura e relatório HTML. | Instrumentada para Python; o mínimo de 70% se aplica apenas às linhas Python novas ou alteradas, não ao repositório inteiro. |
| `delta-neo4j-database` | Testes pytest instrumentam o loader Python com driver simulado; um job separado valida setup e seed em Neo4j temporário. | Instrumentada para `load_graph.py`; arquivos `.cypher` não são contabilizados como cobertura e não recebem percentual inventado. |
| `delta-app-mobile` e `delta-mobile-app` | CI valida arquivos documentais essenciais. Nenhum dos dois repositórios tem código mobile, stack ou build versionados na `main` inspecionada. | N/A enquanto não houver código de aplicação instrumentável. Não se cria uma suite de aplicação vazia. |
| `delta-template-repository` | CI valida YAML dos workflows, licença e regras essenciais de `.gitignore`; não há aplicativo executável no scaffold atual. | N/A enquanto o repositório contiver apenas arquivos de template e configuração. |
| `delta-handbook` | Valida Markdown e instrumenta o codigo Python do validador em scripts/. | Cobertura Python medida para o validador. Os documentos Markdown em si nao recebem percentual de cobertura. |

Quando um repositório não contém código instrumentável, o handbook registra a razão de N/A. Se código testável for adicionado, a suite, o relatório e o critério de cobertura devem acompanhar essa mudança no repositório responsável. Não abra uma alteração sem efeito apenas para produzir um percentual ou um workflow vazio.

## Politica Sonar e ativacao

O scanner recebe relatorios produzidos depois de todos os testes obrigatorios passarem. A politica usa somente achados novos graves: Critical/Blocker no modelo legado e High/Blocker nos impactos. Seguranca grave nova bloqueia; confiabilidade grave nova exige uma aprovacao humana a mais do que a maior exigencia normal da branch/rulesets; manutenibilidade apenas avisa. Graves antigos da main aparecem somente no comentario como divida, para nao bloquear a PR que os corrige.

O comentario Sonar e independente do comentario CI/Compose. As aprovacoes devem pertencer ao SHA atual e a pessoas com escrita diferentes do autor. A ausencia de analise ou de configuracao nao e aprovada automaticamente. O plano Free nao exige Quality Gate personalizado: a regra e implementada pelo check proprio `Delta / Politica Sonar` (veja o nome exato com acento no workflow).

Consulte [a configuracao compartilhada](https://github.com/delta-app-ofc/.github/blob/ci/validacao-relatorios-sonar/docs/sonar.md). Secrets `SONAR_TOKEN`, `SONAR_POLICY_TOKEN` e o token organizacional existente devem estar disponiveis aos repos participantes. Crie repository secrets ou organization secrets; estes workflows nao usam environment secrets.

Depois de mesclar a infraestrutura e validar o onboarding, o workflow manual `Ativar checks obrigatorios Sonar` no repo .github acrescenta os checks de testes/integracao e politica preservando as protecoes existentes. Nao ha alteracao de CD nem merge automatico.

Na validacao de 31/10/2026, as suites de integracao ampliadas de MongoDB e PostgreSQL passaram no GitHub Actions, embora o daemon Docker local nao estivesse disponivel. Resultados de Sonar sao separados desses resultados de testes.
