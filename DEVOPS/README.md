# DevOps do Delta

Os serviços do Delta usam o GitHub para revisão e integração de código, o Render para publicação das aplicações e o AWS Glue com Databricks para processamento dos dados de BI.

| Processo | Guia |
| --- | --- |
| Preparar workflows, secrets e proteção de branches | [Implantação de CI/CD](implantacao-ci-cd.md) |
| Configurar serviços, publicar versões e acompanhar a aplicação | [Deploys no Render](deploys-render.md) |
| Executar Bronze, SQL, Silver e carga analítica | [Operação do Glue e Databricks](operacao-glue-databricks.md) |
| Consultar os checks e workflows de cada repositório | [Workflows de CI](ci-workflows.md) |
| Preparar branches e commits | [Convenções de desenvolvimento](convencoes-desenvolvimento.md) |
| Entender a revisão e a automação das PRs | [Regras de revisão](pr-review-rules.md) |
| Preencher a descrição de uma PR | [Template de PR](template-prs.md) |
| Trabalhar na documentação | [CI documental](ci-documental.md) |

## Da alteração à publicação

1. A pessoa responsável cria uma branch e abre uma PR no repositório do componente.
2. O GitHub Actions executa os testes e as verificações configuradas para esse projeto. A governança confere o preenchimento da PR e encaminha a revisão.
3. Com os checks exigidos e a revisão concluídos, a alteração é integrada à `main`.
4. Nos serviços com CD para Render, o push na `main` aciona o deploy hook. A publicação é acompanhada nos eventos e logs do serviço no Render.
5. No BI, os scripts são publicados nos jobs correspondentes. A execução segue a sequência do workflow Glue e continua nas tarefas do Databricks.

As configurações ficam nos repositórios de cada componente. Os guias desta pasta explicam como a equipe monta e opera esses processos.
