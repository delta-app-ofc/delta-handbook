# Política de qualidade e análise Sonar

Este documento explica as condições avaliadas por `Delta / Política Sonar` nos projetos com análise configurada. O fluxo geral de PR e as regras de merge estão em [validação e revisão de PRs](pr-review-rules.md).

## 1. Critérios para aprovação

| Critério | Regra |
| --- | --- |
| Testes obrigatórios | Todos devem passar. Uma suíte com zero testes não comprova aprovação. |
| Cobertura | Mínimo de 70% no código novo/alterado instrumentável. Não é uma exigência de 70% sobre todo o legado. |
| Segurança | Achados novos graves bloqueiam a política. |
| Confiabilidade | Achados novos graves exigem uma aprovação humana adicional às revisões normais. |
| Manutenibilidade | Achados são apresentados no comentário e não bloqueiam por essa categoria. |
| Dívida existente | Achados anteriores da branch principal são informados e não bloqueiam a PR por serem antigos. |
| Dados ausentes | Falta de análise, configuração ou dados não é convertida em aprovação. |

A classificação de gravidade considera High/Blocker no modelo por impacto ou Critical/Blocker no modelo legado. Achados menores não bloqueiam nem exigem aprovação extra pela política.

Para confiabilidade, a aprovação extra é somada ao maior número normal exigido pelas proteções e rulesets. Se a regra normal exige duas aprovações, uma PR com achado novo grave de confiabilidade precisa de três aprovações válidas. A política não aumenta globalmente o número de revisões para todas as PRs.

As aprovações contadas precisam ser da versão atual da PR, de pessoas diferentes do autor e com permissão de escrita. Comentários não revogam aprovações; uma revisão de mudanças solicitadas ou uma aprovação dispensada deixa de valer conforme a política. Novos commits exigem reavaliação das aprovações.

## 2. Análise, relatórios e aplicabilidade

Os testes geram relatórios de cobertura consumidos pela análise. A avaliação da política executa a partir de código confiável da base, por `pull_request_target` e `workflow_run`, sem executar código da PR com o token de avaliação. Eventos de revisão sinalizam a necessidade de reavaliar as aprovações; não há consulta periódica por cron nesse fluxo.

O comentário Sonar é separado do comentário técnico de CI e não altera os checkboxes da PR. A análise da branch principal atualiza a referência e a dívida histórica. Uma análise de uma versão anterior não comprova a versão atual.

Cobertura deve corresponder ao código real. SQL e Cypher são validados por comportamento, contratos, constraints e consultas, sem inventar percentual de cobertura de linhas. Um smoke MongoDB executado por `mongosh` também não produz automaticamente cobertura de linhas. No handbook e no template, `Testes Sonar` informa N/A e depende da validação documental/configuração; não há scanner ou cobertura Sonar nesses workflows.

Security Hotspots exigem triagem humana e não equivalem automaticamente a vulnerabilidades confirmadas. A política de achados usa as vulnerabilidades e impactos retornados pela análise; a triagem de hotspots precisa ser considerada na configuração de qualidade adotada.

## 3. Configuração e checks obrigatórios

A integração depende do projeto SonarQube Cloud, das variáveis `SONAR_ORGANIZATION` e `SONAR_PROJECT_KEY`, e dos secrets `SONAR_TOKEN`, `SONAR_POLICY_TOKEN` e `DELTA_ORG_AUTOMATION_TOKEN`, com permissões adequadas a cada função. O token de análise é separado do token da avaliação confiável. Nunca exponha esses valores ao código não confiável da PR ou em documentação.

Estabeleça uma análise de referência da branch principal e configure a análise por GitHub Actions, evitando uma análise automática paralela que não use os mesmos relatórios. No plano Free, o fluxo documentado considera PRs com destino à `main` e utiliza o check próprio Delta: o Quality Gate padrão do Sonar pode impor critérios diferentes, como bloqueios de manutenibilidade, e não deve ser usado como substituto da política da equipe.

Depois de publicar e validar os workflows, configure os checks obrigatórios da branch. O workflow manual `Ativar checks obrigatórios Sonar`, no repositório `.github`, permite acrescentar os checks de testes informados e `Delta / Política Sonar` à proteção existente. Ele não substitui as revisões ou demais regras. Informe os nomes reais dos checks de testes e integrações; preserve os checks já exigidos.

Workflows `workflow_run` precisam estar na branch padrão. Sem acesso às proteções/rulesets ou ao contexto necessário da análise, a avaliação permanece pendente ou reprovada com diagnóstico. A presença dos arquivos YAML não comprova que secrets, projeto externo e proteção de merge estejam configurados.

Para instalação, permissões e manutenção, consulte o [guia Sonar da automação organizacional](https://github.com/delta-app-ofc/.github/blob/main/docs/sonar.md).
