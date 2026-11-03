# DevOps — Validação, revisão e merge de Pull Requests

Este documento explica como preparar uma PR, acompanhar as verificações automáticas e obter as revisões necessárias para integrá-la. O processo combina governança, validação técnica e revisão humana. Um workflow aprovado só impede ou permite o merge automaticamente quando o GitHub exige seu check na proteção da branch ou em um ruleset.

## 1. Caminho da alteração até o merge

1. Atualize a branch principal e crie uma branch própria seguindo as [convenções de desenvolvimento](convencoes-desenvolvimento.md).
2. Implemente a tarefa, revise o diff e execute as verificações locais do repositório. Agrupe os commits por alteração lógica.
3. Faça push e abra a PR para a branch de destino definida pelo projeto. Preencha o [template de PR](template-prs.md), incluindo objetivo, impacto, testes e limitações. Use draft enquanto a entrega estiver incompleta.
4. Aguarde `ci-tecnico` e `Testes Sonar`, além das integrações e da política Sonar quando aplicáveis. Leia os logs dos checks reprovados.
5. Acompanhe a atualização automática do checklist e a execução de `validate-pr-checks / Governança da Pull Request`. Confira também se os times revisores foram solicitados.
6. Responda à revisão, faça os ajustes na mesma branch e aguarde as novas verificações. Um resultado de uma versão anterior não comprova a versão atual da PR.
7. Antes do merge, confira os checks obrigatórios, as aprovações exigidas, as conversas pendentes conforme as regras da branch e a ausência de conflitos. Siga a estratégia de merge do repositório.
8. Depois do merge, acompanhe os workflows da branch principal e conclua a tarefa no board. Publicação e implantação dependem do CD de cada projeto; a aprovação da PR não comprova implantação.

```text
Branch e validação local → PR e template → CI técnico e relatórios
                                               ↓
                                   Checklist e governança
                                               ↓
                          Revisão humana e política Sonar aplicável
                                               ↓
                            Checks e regras atendidos → Merge
```

A governança não substitui os testes e o roteamento de times não equivale a uma aprovação humana.

## 2. O que cada check significa

| Check ou resultado | Responsabilidade | Como agir |
| --- | --- | --- |
| `ci-tecnico` | Executa as verificações técnicas definidas pelo repositório. | Corrigir a falha e aguardar nova execução. |
| `Testes Sonar` | Executa testes e gera relatórios; em fluxos documentais/configuração, registra N/A e depende da validação técnica. | Ler o resumo para saber o que foi realmente validado. |
| `validate-pr-checks / Governança da Pull Request` | Valida commits, proteção de arquivos, descrição e checklist; solicita revisores. | Corrigir o conteúdo ou a configuração indicada nos logs. |
| `Delta / Política Sonar` | Avalia cobertura, achados novos e aprovações adicionais nos projetos com análise configurada. | Seguir a [política de qualidade](politica-sonar.md). |
| Comentários de CI e Sonar | Resumem resultados e apontam logs e diagnósticos. | Usar para investigar; o comentário não substitui o check obrigatório. |

No handbook, `ci-tecnico` verifica Markdown rastreado pelo Git e `Testes Sonar` registra que análise e cobertura Sonar não se aplicam. Isso não é uma análise Sonar nem um teste de aplicação. Os comandos e limites dos demais projetos estão em [workflows de CI](ci-workflows.md).

## 3. Arquitetura centralizada da governança

O repositório organizacional [`.github`](https://github.com/delta-app-ofc/.github) mantém os scripts compartilhados. Cada satélite precisa ter seu próprio workflow chamador; estar na organização não ativa automaticamente os workflows.

```text
.github/
├── .github/workflows/
│   ├── main.yml          # Governança reutilizável
│   ├── local_checks.yml  # Governança do próprio .github
│   └── report_ci.yml     # Relatório técnico e checklist
├── pull_request_template.md
└── scripts/
    ├── check_ci_bypass.py
    ├── validate_commits.py
    ├── validate_gitignore.py
    ├── route_checks.py
    └── route_reviewers.py
```

O chamador do handbook reage a `opened`, `synchronize`, `reopened`, `edited`, `labeled` e `unlabeled`. Assim, novos commits, edições e mudanças de label podem reavaliar a governança. A CI documental roda em `pull_request` e por disparo manual.

A governança do handbook aguarda um marcador de resultado do CI referente à versão atual da PR. O reporter publica esse marcador no corpo da PR e marca ou desmarca o item de testes conforme os jobs necessários. Uma execução antiga não atualiza o resultado de uma versão mais nova. O marcador registra o resultado, inclusive quando houve falha; sua presença não significa aprovação.

Se a atualização do corpo falhar, a governança condicionada ao marcador pode ficar pulada ou pendente. Nesse caso, consulte o resumo do reporter, corrija o acesso e reexecute o fluxo. Marcar manualmente o checkbox não substitui a publicação do resultado nem os checks técnicos.

### Execução do workflow compartilhado

O `main.yml` faz checkout do projeto e baixa os scripts organizacionais em `actions-scripts`, sem persistir credenciais no checkout. A sequência é:

1. Verificar o bypass emergencial.
2. Validar os commits incluídos na PR.
3. Validar o `.gitignore` e procurar arquivos de ambiente indevidamente rastreados.
4. Validar descrição e opções do template.
5. Solicitar os times revisores correspondentes aos módulos marcados.

Os satélites fornecem `DELTA_ORG_AUTOMATION_TOKEN` como secret `GH_TOKEN` ao workflow reutilizável. As permissões precisam permitir as operações de leitura, edição da PR e solicitação de revisão. Nunca copie o valor de um token para documentação, logs ou descrição da PR.

## 4. Regras de validação

### Commits e arquivos de ambiente

`validate_commits.py` verifica os títulos de todos os commits incluídos, com tipo, escopo opcional e descrição. Após sucesso, marca o checkbox de Conventional Commits e disponibiliza o corpo atualizado às próximas etapas. Alterar somente o título da PR não corrige commits inválidos.

`validate_gitignore.py` exige as regras ativas do `.gitignore` organizacional, permitindo regras extras e diferenças de ordem ou comentários. Também verifica arquivos já rastreados: adicionar uma regra de ignore não retira um arquivo do histórico. Os modelos `.env.example`, `.env.sample`, `.env.template` e `.env.test` são exceções permitidas pelo validador e devem conter somente valores adequados ao uso público/teste. Após sucesso, marca o checkbox de proteção de variáveis de ambiente.

### Checklist e descrição

`route_checks.py` procura os textos esperados do template, ignorando maiúsculas/minúsculas nas opções. Preserve os nomes dos itens e os títulos usados para localizar a descrição.

| Grupo | Regra automática |
| --- | --- |
| Escopo/módulo | Pelo menos um módulo marcado entre as opções dos dois anos. |
| Tipo de PR | Pelo menos um dos tipos reconhecidos no template marcado. |
| Uso de IA | Pelo menos uma opção marcada; informe a situação real. |
| Rigor técnico | Os itens de Conventional Commits e de testes precisam estar marcados. |
| Descrição | Pelo menos 30 caracteres úteis na seção de descrição. |

A descrição é extraída entre `## 📄 Descrição` e `## ✨ Tipo de PR`. O script remove as orientações padrão e parte da formatação antes de contar os caracteres. Copiar apenas as instruções não atende à regra. A regra mínima de tamanho não avalia se a explicação é boa: descreva o problema, o resultado e a validação.

Os outros itens de rigor técnico continuam sendo responsabilidades de quem desenvolve e revisa, conforme aplicabilidade. A automação não prova acessibilidade, tratamento de exceções ou atualização do Swagger apenas porque uma caixa foi marcada.

### Relatório dos testes

O reporter avalia os jobs recebidos em `needs`: o conjunto deve ser não vazio e todos precisam concluir com sucesso. Falhas, cancelamentos ou jobs necessários pulados não são aprovação. Ele tenta publicar o comentário e atualizar o corpo da PR de forma independente; falhas de publicação geram avisos, sem converter testes reprovados em aprovados. Confira sempre os checks técnicos da versão atual.

## 5. Roteamento dos times revisores

`route_reviewers.py` relaciona os módulos aos times abaixo e elimina solicitações duplicadas para o mesmo time.

| Módulo | Time |
| --- | --- |
| Backend Java / Servlets / DAO | `backend-1ano` |
| Frontend HTML / CSS / Landing Page | `frontend-1ano` |
| Database Modelo Lógico / Script SQL | `dados-1ano` |
| Planilha de Controle / SO | `gestao-1ano` |
| API REST Spring Boot | `backend-2ano` |
| Aplicação Dinâmica React / TypeScript | `frontend-2ano` |
| Mobile Android / iOS / Firebase | `backend-2ano` |
| IA Multiagente FastAPI / Langgraph | `dados-2ano` |
| Banco de Dados Postgres, MongoDB, Redis ou Neo4J | `dados-2ano` |
| Infraestrutura / Pipeline de CI/CD | `gestao-2ano` |
| Gestão de projetos / Documentação / UX | `gestao-2ano` |

O comando usa o formato `gh pr edit <PR> --add-reviewer <organizacao>/<time>`. Falhas de solicitação aparecem como avisos e no resumo do roteamento. Confira a área Reviewers da PR e solicite revisão manualmente quando necessário; sucesso do job não garante que todos os pedidos foram aceitos pela API.

## 6. Proteção de branch e revisão humana

A execução do workflow e a exigência de seu resultado são configurações diferentes. Para impedir merge com falhas, uma pessoa com permissão administrativa deve configurar a proteção de branch ou o ruleset, preservando as regras existentes:

- Exigir PR e as revisões normais definidas para o repositório.
- Exigir os checks publicados com seus nomes exatos: `ci-tecnico`, `Testes Sonar` e `validate-pr-checks / Governança da Pull Request`.
- Acrescentar checks de integração e `Delta / Política Sonar` quando aplicáveis.
- Atender às regras configuradas de atualização da branch, conflitos e resolução de conversas.

Primeiro publique e valide os workflows, depois selecione os contextos reais nas regras. Workflows com `workflow_run` precisam existir na branch padrão para operar. Esta documentação não ativa proteções nem comprova que todos os repositórios já possuem a mesma configuração. Confira as regras da branch de destino e os checks exigidos pela própria PR.

## 7. Bypass emergencial

A label `ci-bypass` só autoriza pular a governança quando sua última aplicação foi feita diretamente pela conta `samuelpimentah`, conforme o histórico da PR. Registre a justificativa da emergência. Uma aplicação por outra conta não autoriza o bypass e uma falha ao consultar a API faz a verificação falhar.

O bypass permanece enquanto a label autorizada estiver presente, inclusive em novos commits. Ele pula os validadores de commits, `.gitignore`, checklist e o roteamento; não aprova testes, análise Sonar ou checks externos e não marca checkboxes. Remova a label para reativar as validações. Consulte o [guia operacional do bypass](https://github.com/delta-app-ofc/.github/blob/main/docs/ci-bypass.md).

## 8. Resolução de problemas

| Sintoma | O que conferir e corrigir |
| --- | --- |
| Commit inválido | Leia os títulos apontados e ajuste os commits da própria branch conforme as convenções; aguarde nova execução. |
| `.gitignore` reprovado | Inclua as regras ausentes e retire arquivos de ambiente do rastreamento. Se houve exposição de segredo, revogue-o e substitua-o. |
| Descrição ou checklist reprovado | Preserve os títulos e textos do template; escreva a descrição e selecione os itens exigidos. |
| Governança pulada após novo commit | Aguarde o CI atual e verifique se o reporter conseguiu atualizar o corpo da PR. |
| Testes passaram, mas não há comentário | Consulte os checks e o resumo do reporter; uma falha informativa de publicação não altera o resultado dos testes. |
| Times não aparecem | Confira o resumo do roteamento, o slug do time, acesso ao repositório e permissões do token. |
| Script não encontrado | O workflow compartilhado usa `actions-scripts/scripts/`; confira o checkout e os caminhos. |
| Sonar pendente ou reprovado | Confira análise da versão atual, artefatos, configuração e regras descritas na política Sonar. |
| Checks verdes, mas merge bloqueado | Verifique revisões, conflitos, conversas e outros checks exigidos pela branch. |

## Referências operacionais

- [Workflow compartilhado de governança](https://github.com/delta-app-ofc/.github/blob/main/.github/workflows/main.yml)
- [Validação do template](https://github.com/delta-app-ofc/.github/blob/main/scripts/route_checks.py)
- [Roteamento dos revisores](https://github.com/delta-app-ofc/.github/blob/main/scripts/route_reviewers.py)
- [Reporter de CI](https://github.com/delta-app-ofc/.github/blob/main/.github/workflows/report_ci.yml)
