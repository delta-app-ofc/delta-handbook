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
| chore    | Tarefas de manutenção / configuração           |

### Exemplos

```text
feat/cadastro-usuario
fix/validacao-cpf
refactor/reorganizar-services
docs/convencao-desenvolvimento
test/testes-cadastro-usuario
chore/atualizar-dependencias
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
| chore    | Tarefas de manutenção                      |

### Exemplos

```text
feat: adiciona endpoint de cadastro de usuário

fix: corrige validação de CPF

refactor: reorganiza camada de serviço

docs: atualiza documentação de onboarding

test: adiciona testes para autenticação

chore: atualiza dependências do projeto
```
---

## 3. Boas Práticas

* Utilizar nomes descritivos.
* Evitar commits muito grandes.
* Dividir commits para gerar histórico.
* Manter branches atualizadas.
* Documentar alterações relevantes.
* Priorizar código simples e legível.

---

### Atualizações

Este documento pode ser atualizado conforme a evolução dos processos e necessidades da organização.
