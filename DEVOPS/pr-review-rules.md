# DevOps — Checks e fluxo de Pull Requests

Este documento descreve os checks compartilhados do Projeto Delta para Pull Requests. O workflow central fica no repositório `.github`; cada repositório satélite chama esse workflow por meio de um arquivo local em `.github/workflows/`.

## 1. Disparo do fluxo

O workflow padrão dos repositórios satélites, como `.github/workflows/trigger_actions.yml`, é executado nestes eventos:

- `opened`: a PR foi aberta;
- `synchronize`: novos commits foram enviados para a branch;
- `reopened`: a PR foi reaberta;
- `edited`: o título ou a descrição da PR foi editado.

Esse workflow chama `delta-app-ofc/.github/.github/workflows/main.yml@main`. O workflow central é reutilizável (`workflow_call`) e organiza dois jobs independentes. O repositório `.github` também possui um workflow local, `local_checks.yml`, que executa as mesmas verificações em PRs abertas contra ele próprio.

O workflow chamador fornece o segredo `GH_TOKEN` — nos repositórios satélites, por meio de `DELTA_ORG_AUTOMATION_TOKEN` — para os scripts consultarem e atualizarem a PR e solicitarem revisores. O Super-Linter recebe o `GITHUB_TOKEN` do próprio GitHub Actions.

## 2. Visão do pipeline

Os jobs de qualidade e governança são iniciados em paralelo. Dentro do job de governança, as etapas são sequenciais:

```text
Pull Request (opened / synchronize / reopened / edited)
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
┌────────────────────────┐  ┌──────────────────────────┐
│ Qualidade e sintaxe    │  │ Governança da PR         │
│ Super-Linter           │  │ 1. Validar commits        │
└────────────────────────┘  │ 2. Validar .gitignore    │
                            │ 3. Validar descrição e   │
                            │    checklists da PR       │
                            │ 4. Adicionar revisores    │
                            └──────────────────────────┘
```

Se uma etapa do job de governança falhar, as etapas seguintes desse job não são executadas. O job de qualidade continua independente.

## 3. Qualidade e sintaxe do código

O job `code-quality` usa o Super-Linter (`super-linter/slim@v8.7.0`) para analisar os arquivos alterados na PR. Ele não analisa o repositório inteiro (`VALIDATE_ALL_CODEBASE: false`) e consolida o resultado em um status (`MULTI_STATUS: false`).

Na configuração atual, estão habilitadas verificações para:

- **Segurança e integridade:** Gitleaks e marcadores de conflito de merge;
- **GitHub e configuração:** GitHub Actions, JSON, YAML e XML;
- **Python:** Ruff;
- **Java;**
- **JavaScript e TypeScript;**
- **Web:** HTML e CSS;
- **Banco de dados:** SQL.

O Super-Linter verifica problemas de lint, formatação e sintaxe cobertos pelos validadores habilitados. Ele **não executa os testes do projeto, não substitui builds ou compilação específicos e não prova que a alteração não introduz bugs**. Cada repositório deve manter seus próprios testes e verificações de build quando aplicável.

A configuração também faz o workflow falhar quando encontra uma configuração inválida de eventos do GitHub Actions. Em caso de falha, consulte o resumo do Super-Linter e os logs para identificar o validador e os arquivos apontados.

## 4. Governança da Pull Request

O job `pr-checks` baixa o código da PR e os scripts centralizados do repositório `.github`. Em seguida, executa estas etapas na ordem:

### 4.1 Validar commits

O script `scripts/validate_commits.py` verifica os títulos dos commits entre a branch base e a branch da PR. O formato esperado é Conventional Commits, com os tipos Delta:

```text
feat: adiciona consulta de consumo
fix(api): corrige validação do usuário
refactor: reorganiza camada de serviço
docs: atualiza instruções do projeto
test: adiciona testes para autenticação
style: remove espaços em branco
```

O escopo entre parênteses e o marcador de breaking change (`!`) são opcionais. Na versão atualmente publicada em `main`, commits de merge são excluídos dessa análise, mas títulos como `Initial Commit` ainda são analisados e falham por não seguirem o formato permitido. Após a validação passar, o script marca automaticamente no corpo da PR o item de Conventional Commits do checklist. Se algum commit analisado não seguir o padrão, a etapa falha e informa os títulos inválidos.

### 4.2 Validar `.gitignore` e arquivos de ambiente

O script `scripts/validate_gitignore.py` roda em **toda PR**, mesmo quando o arquivo `.gitignore` não foi alterado. Ele:

1. compara o `.gitignore` do projeto com as regras mínimas do arquivo `.github/.gitignore` central, exigindo que elas apareçam na ordem definida; regras adicionais são permitidas;
2. consulta os arquivos rastreados pelo Git e falha se encontrar arquivos de ambiente protegidos versionados;
3. em caso de falha, imprime o conteúdo completo do `.gitignore` padrão para orientar a correção.

Na versão atualmente publicada em `main`, `.env.example`, `.env.sample` e `.env.template` são nomes permitidos. Um arquivo `.env` ou outro nome iniciado por `.env.` — incluindo `.env.test` — é considerado protegido e não pode estar rastreado. Depois de passar pelas duas verificações, o script marca automaticamente no corpo da PR o item que declara a proteção das variáveis de ambiente.

### 4.3 Validar descrição e checklists da PR

O script `scripts/route_checks.py` verifica se a descrição contém:

- pelo menos um módulo ou escopo impactado selecionado;
- pelo menos um tipo de PR selecionado;
- pelo menos uma opção de uso de IA respondida;
- os itens obrigatórios do checklist marcados;
- 30 ou mais caracteres úteis na seção de descrição, sem contar as instruções fixas do template.

O item de Conventional Commits é validado e marcado automaticamente pela etapa 4.1. O item **“O código foi devidamente testado e não causa novos bugs” continua sendo preenchido manualmente**: o Super-Linter não executa os testes específicos de cada projeto. Marque-o somente após realizar as verificações adequadas à alteração.

### 4.4 Adicionar revisores

Depois que as validações anteriores passam, `scripts/route_reviewers.py` lê os módulos selecionados e solicita revisão aos times correspondentes da organização. O mapeamento entre módulos e times fica no próprio script centralizado.

A solicitação de revisão não equivale a uma aprovação. Regras de proteção da branch e aprovações exigidas são configuradas separadamente no GitHub.

## 5. O que faz o check ser obrigatório

Um check vermelho mostra que a execução falhou. Para impedir o merge, o repositório também precisa exigir os checks correspondentes nas regras de proteção da branch ou no ruleset. A configuração dessas regras é feita no GitHub e não pelo workflow reutilizável.

## 6. Resolução de problemas

| Sintoma | O que verificar |
| --- | --- |
| **Falha em “Qualidade e sintaxe do código”** | Abra o resumo do Super-Linter, identifique o validador e corrija os arquivos apontados. As mensagens indicam o problema; o workflow não aplica correções automaticamente. |
| **Falha em “Validar commits”** | Confira cada título de commit listado e ajuste-o ao formato Conventional Commits e aos tipos permitidos pelo Delta. |
| **Falha em “Validar .gitignore”** | Compare o arquivo com o conteúdo padrão impresso no log. Remova do versionamento arquivos de ambiente protegidos e mantenha as exceções permitidas. |
| **Falha em “Validar checks da PR”** | Revise os módulos, tipo de PR, uso de IA, checklist obrigatório e a descrição com pelo menos 30 caracteres úteis. O item sobre testes continua manual. |
| **Os revisores não foram adicionados** | Confirme o módulo marcado, o mapeamento do time em `route_reviewers.py` e as permissões do token de automação. A atribuição só ocorre se as etapas anteriores passarem. |

## 7. Fontes de configuração

- Workflow reutilizável: `.github/.github/workflows/main.yml`, no repositório central `.github`.
- Workflow local do repositório central: `.github/.github/workflows/local_checks.yml`.
- Workflow chamador dos repositórios satélites: `.github/workflows/trigger_actions.yml`.
- Scripts de validação e roteamento: `.github/scripts/`.
- `.gitignore` mínimo de referência: `.github/.gitignore`.
