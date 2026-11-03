# Implantação de CI/CD

O CI executa as verificações do projeto a cada alteração. O CD publica a versão integrada. No Delta, os workflows ficam em `.github/workflows/` de cada repositório e usam os scripts compartilhados do repositório [`.github`](https://github.com/delta-app-ofc/.github).

## Fluxo de uma Pull Request

Ao abrir ou atualizar uma PR, o workflow técnico prepara o ambiente da tecnologia e executa os comandos definidos no YAML. Aplicações Java usam Maven; aplicações Python usam suas suítes e dependências; o frontend usa os scripts npm. Os projetos de banco utilizam os serviços de teste configurados em cada repositório.

Os principais resultados aparecem na aba **Checks**:

| Check | Função |
| --- | --- |
| `ci-tecnico` | Executa os comandos de verificação e testes do repositório. |
| `Testes Sonar` | Executa a etapa de testes e relatórios definida pelo workflow Sonar. Nos projetos documentais, registra a aplicabilidade e o resultado da verificação técnica. |
| `validate-pr-checks / Governança da Pull Request` | Confere descrição, tipo de alteração, módulos e checklist da PR. |
| `Delta / Política Sonar` | Avalia a análise Sonar do commit atual nos projetos que usam essa política. |

Os nomes publicados pelos jobs são os nomes usados na proteção de branch. O arquivo `test.yml` identifica o workflow; o campo `name` do job define como seu resultado aparece.

## Preparar um repositório

1. Identifique os comandos de instalação, teste e build usados pelo projeto e registre-os no workflow técnico. Use as versões de runtime declaradas pelo repositório.
2. Configure os serviços temporários necessários aos testes, como PostgreSQL, MongoDB, Redis ou Neo4j. Mantenha as credenciais de teste separadas das usadas pelas aplicações publicadas.
3. Mantenha o workflow de governança que chama as automações compartilhadas da organização.
4. Nos projetos com Sonar, configure a geração dos relatórios e seus caminhos antes de executar o scanner.
5. Abra a PR dos workflows e acompanhe os resultados na aba **Actions**. Cada falha indica o job e a etapa que precisam de ajuste.
6. Integre os workflows e configure os checks obrigatórios no ruleset ou na proteção da branch padrão.

Workflows com evento `workflow_run`, como a avaliação da política Sonar, são carregados da branch padrão. Publique esses workflows na `main` antes de exigir seus resultados nas demais PRs.

## Variáveis e secrets

Configure em **Settings → Secrets and variables → Actions** os nomes usados pelos workflows:

| Nome | Uso |
| --- | --- |
| `SONAR_TOKEN` | Autenticação do scanner que envia a análise. |
| `SONAR_POLICY_TOKEN` | Consulta da análise e das métricas pela política compartilhada. |
| `SONAR_PROJECT_KEY` | Identificação do projeto Sonar; use a variável ou configuração referenciada no YAML. |
| `DELTA_ORG_AUTOMATION_TOKEN` | Operações da automação no GitHub, como publicação de status e atualização da PR, conforme o workflow. |
| `RENDER_DEPLOY_HOOK` | Endereço autenticado que solicita um deploy do serviço no Render. |

Cadastre os valores em cada repositório ou disponibilize os secrets organizacionais aos repositórios selecionados. O token de automação precisa das permissões usadas pelos scripts: leitura dos recursos consultados e escrita de status, comentários ou PRs quando essas operações estiverem configuradas.

## Testes, cobertura e análise

A suíte precisa terminar com sucesso. Relatórios JUnit e de cobertura são gerados pelo comando de teste e enviados ao Sonar pelos caminhos configurados no projeto.

A [política compartilhada](https://github.com/delta-app-ofc/.github/blob/main/scripts/sonar_policy.py) avalia a análise da PR e do SHA atual. Ela bloqueia novos achados graves de segurança e cobertura inferior a 70% nas linhas novas instrumentáveis. A classificação grave corresponde a `High`/`Blocker` por impacto ou `Critical`/`Blocker` no modelo legado. Confiabilidade, manutenibilidade e dívida já existente na base aparecem no relatório; aprovações e regras de revisão são configuradas no GitHub.

Para alterações sem linhas instrumentáveis, a política registra a aplicabilidade da cobertura a partir das métricas da análise. Uma análise pendente ou uma falha de consulta exige acompanhamento do job antes da integração.

## Proteger a branch principal

Em **Settings → Rules → Rulesets**, selecione a branch padrão e configure a exigência de PR, os checks técnicos publicados e as regras de revisão da equipe. Inclua `Delta / Política Sonar` nos projetos que publicam esse status.

Faça a configuração depois que os checks tiverem aparecido no repositório. O nome exigido precisa corresponder exatamente ao contexto publicado. Ao alterar os nomes dos jobs, ajuste também o ruleset.

## Ligar o CD

Os workflows de CD consultados nas APIs PostgreSQL e IA usam `push` na `main` para enviar um POST ao deploy hook do Render. A sequência é: PR aprovada, merge, push na `main` e solicitação de deploy.

A aprovação técnica antes do merge depende dos checks exigidos na proteção da branch. Os workflows atuais de CD são acionados pelo push; a configuração do ruleset estabelece a passagem obrigatória pelo CI.

Siga o [guia do Render](deploys-render.md) para cadastrar o serviço e o hook. Para dados de BI, use o [guia do Glue e Databricks](operacao-glue-databricks.md).

## Acompanhar uma falha

Abra a execução na aba **Actions** e consulte a primeira etapa que falhou. Em testes, use o relatório da suíte; no Sonar, consulte o projeto e o SHA indicados; em deploy, acompanhe também os eventos do serviço no Render.

Após corrigir código, dependências ou configuração, envie o novo commit pela mesma branch. As verificações passam a avaliar a nova revisão da PR.
