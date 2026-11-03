# Workflows de CI do Delta

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

O comando de referência para cada componente fica em seu README e em `.github/workflows/` na revisão usada pela PR. Para reproduzir um job localmente, use o mesmo runtime, dependências e comando declarados no YAML.

## Resultado e correção

Quando um job falha, abra seus logs e identifique a primeira etapa com erro. Os relatórios de teste e cobertura ajudam a localizar o problema; falhas de instalação ou de configuração aparecem nas etapas anteriores à suíte.

Envie a correção pela mesma branch. O novo commit recebe uma nova execução e a política Sonar consulta a análise correspondente a esse SHA. A revisão e a integração seguem as regras configuradas no repositório.

## Arquivos de referência

- [Workflows compartilhados](https://github.com/delta-app-ofc/.github/tree/main/.github/workflows)
- [Política Sonar](https://github.com/delta-app-ofc/.github/blob/main/scripts/sonar_policy.py)
- [CI do handbook](https://github.com/delta-app-ofc/delta-handbook/blob/main/.github/workflows/test.yml)
- [Convenções de desenvolvimento](convencoes-desenvolvimento.md)
- [Revisão de PRs](pr-review-rules.md)
