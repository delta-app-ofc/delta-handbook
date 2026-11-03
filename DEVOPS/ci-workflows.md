# Workflows de CI do Delta

Para entender como os checks se combinam com checklist, revisão humana e proteção de merge, consulte o [fluxo de aprovação de PRs](pr-review-rules.md) e a [política Sonar](politica-sonar.md).

Esta página reúne o que os workflows de integração contínua executam e como reproduzir localmente. A validação de checklist e encaminhamento de revisores segue separada nos workflows organizacionais já existentes. Estes CIs rodam em pull requests e, quando indicado no workflow, também podem ser acionados manualmente.
Os workflows de cada repositório definem o ambiente, os comandos e os relatórios usados nas PRs. O GitHub Actions publica o resultado dos jobs na aba **Checks** e guarda os logs na aba **Actions**.

Para configurar os workflows e a proteção da branch, consulte [Implantação de CI/CD](implantacao-ci-cd.md). Para publicação das aplicações, veja [Deploys no Render](deploys-render.md); para as cargas analíticas, veja [Operação do Glue e Databricks](operacao-glue-databricks.md).

## Organização dos workflows

| Arquivo ou processo | Responsabilidade |
| --- | --- |
| `test.yml` | Instala o ambiente e executa a verificação técnica do projeto. |
| Workflow Sonar | Gera os relatórios definidos pelo projeto e envia a análise ao Sonar. |
| `sonar-policy.yml` | Aciona a avaliação compartilhada da política Sonar para as PRs. |
| Workflow de governança | Confere a descrição e o checklist da PR e encaminha os revisores. |
| Reporter de CI | Registra o resultado técnico na PR conforme a configuração do workflow. |
| `cd.yml`, nos serviços com esse arquivo | Solicita publicação no Render após push na `main`. |

## Checks apresentados na PR

O job técnico usa o nome `ci-tecnico`. Os projetos com a etapa correspondente publicam `Testes Sonar`; a avaliação compartilhada publica o status `Delta / Política Sonar`. A governança usa `validate-pr-checks / Governança da Pull Request`.

No handbook e no template, o workflow registra a aplicabilidade da etapa Sonar a partir da verificação documental ou de configuração. A análise de código e os relatórios de cobertura seguem os workflows dos projetos executáveis.

Os rulesets devem exigir os nomes efetivamente publicados no repositório. Workflows acionados por `workflow_run` precisam estar na branch padrão para receber os eventos.

## Verificações por componente

| Componente | Ambiente e verificações |
| --- | --- |
| APIs PostgreSQL e MongoDB | Java 17 e testes Maven, com o ambiente definido pelo projeto. |
| Inteligência artificial | Dependências Python, compilação e suíte de testes. |
| Regras de negócio | Python e pytest para as regras de consumo e detecção. |
| API Redis | Python, pytest e Redis temporário para os testes de ranking e endpoints. |
| Aplicação web | Node, testes, lint e build definidos nos scripts npm. |
| Android | Gradle e tarefas configuradas no workflow do aplicativo. |
| RPA | Testes Python e execução com bancos descartáveis via Compose. |
| Simulador | Verificações dos módulos Python e execução de teste configurada no projeto. |
| PostgreSQL | Aplicação dos scripts e verificações SQL em banco temporário. |
| MongoDB | Aplicação de coleções, índices e verificações em MongoDB temporário. |
| Neo4j | Preparação do grafo e verificações com Neo4j temporário. |
| Business Intelligence | Verificação dos scripts e suítes locais configuradas no repositório. A operação dos jobs está no guia de Glue. |
| `.github` | Sintaxe e testes dos scripts de automação. |
| Handbook | Verificação dos Markdown rastreados pelo Git. |
| Template | Verificação dos arquivos de configuração e regras de ignore. |

## Cobertura de código e limites por repositório

A política compartilhada exige 100% dos testes aprovados e pelo menos 70% de cobertura **somente nas linhas novas ou alteradas que possam ser instrumentadas**. O percentual não representa a cobertura global do repositório. Testes de comportamento e cobertura de linhas são evidências diferentes: não converta asserções em um percentual fictício.

| Repositório | Evidência automatizada | Cobertura de linhas |
| --- | --- | --- |
| `delta-sql-database` | Integra PostgreSQL temporario e testa bi_etl.py offline com adaptadores simulados. | Python ETL gera XML/JUnit; arquivos SQL sao validados por comportamento, sem cobertura de linhas SQL. Exigir ambos os checks. |
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

## Arquivos de referência

- [Workflows compartilhados](https://github.com/delta-app-ofc/.github/tree/main/.github/workflows)
- [Política Sonar](https://github.com/delta-app-ofc/.github/blob/main/scripts/sonar_policy.py)
- [CI do handbook](https://github.com/delta-app-ofc/delta-handbook/blob/main/.github/workflows/test.yml)
- [Convenções de desenvolvimento](convencoes-desenvolvimento.md)
- [Revisão de PRs](pr-review-rules.md)
