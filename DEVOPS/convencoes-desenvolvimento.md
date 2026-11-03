# Convenções de Desenvolvimento - Delta 💧

# Objetivo 🎯

Este documento define os padrões e convenções adotados pela equipe Delta para garantir consistência, organização e colaboração eficiente entre todos os membros da equipe.

O cumprimento destas diretrizes é recomendado para todos os projetos mantidos pela organização.

## 1. Nomenclatura de Branches

### Objetivo

Padronizar a criação de branches para facilitar rastreabilidade e entendimento das alterações realizadas.

### Estrutura

```text
<tipo>/<descricao-da-alteracao>
```

### Tipos permitidos

| Tipo     | Descrição                       |
| -------- | ------------------------------- |
| feat     | Nova funcionalidade             |
| fix      | Correção de bugs                |
| refactor | Refatoração                     |
| docs     | Alterações em documentação      |
| test     | Criação ou manutenção de testes |
| style    | Alteração de estilização           |

### Exemplos

```text
feat/cadastro-usuario
fix/validacao-cpf
refactor/reorganizar-services
docs/convencao-desenvolvimento
test/testes-cadastro-usuario
style/remove-espaços-brancos
```

---

## 2. Padrão de Commits

### Objetivo

Manter um histórico de alterações claro e padronizado utilizando o padrão Conventional Commits.

### Estrutura

```text
<tipo>: descrição
```

### Tipos permitidos

| Tipo     | Descrição                                  |
| -------- | ------------------------------------------ |
| feat     | Nova funcionalidade                        |
| fix      | Correção de bugs                           |
| refactor | Refatoração sem alteração de comportamento |
| docs     | Alterações em documentação                 |
| test     | Criação ou manutenção de testes            |
| style    | Alterações de estilização                      |

### Exemplos

```text
feat: adiciona endpoint de cadastro de usuário

fix: corrige validação de CPF

refactor: reorganiza camada de serviço

docs: atualiza documentação de onboarding

test: adiciona testes para autenticação

style: remove espaços em branco
```
---

## 3. Boas Práticas

* Utilizar nomes descritivos.
* Evitar commits muito grandes.
* Agrupar commits por alteração lógica, inclusive quando envolver vários arquivos relacionados.
* Manter branches atualizadas.
* Documentar alterações relevantes.
* Priorizar código simples e legível.

---

### Atualizações

Este documento pode ser atualizado conforme a evolução dos processos e necessidades da organização.

## 4. Validação automática dos commits e abertura da PR

Crie a branch a partir da branch principal atualizada e mantenha a alteração em uma branch própria. Para documentação, use `docs/<descricao>` e commits `docs: ...`.

O validador aceita `<tipo>(escopo opcional): descrição`, com `!` opcional para indicar incompatibilidade. Além dos tipos recomendados acima, aceita `chore`, `merge` e `wip`, títulos de merge gerados pelo Git e `Initial Commit`. Essa compatibilidade não dispensa uma descrição clara nem recomenda entregar trabalho incompleto para merge.

```text
fix(api): corrige validação do usuário
feat(api)!: altera contrato de consulta
chore: atualiza dependências
```

Todos os commits incluídos na PR são verificados. Alterar apenas o título da PR não corrige mensagens inválidas. Após a validação, a automação marca o item correspondente no checklist. Consulte o [fluxo completo de PR](pr-review-rules.md) e as [instruções do template](template-prs.md) antes de solicitar revisão.
