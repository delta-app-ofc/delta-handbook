# Fluxo de Desenvolvimento - DELTA 💧

#  Objetivo 🎯

Este documento descreve o fluxo padrão de desenvolvimento utilizado pela equipe Delta, desde a seleção de uma tarefa até a entrega final do código.

### 1. Seleção da Tarefa

1. Acesse o board de tarefas.
2. Escolha uma tarefa disponível ou atribuída a você.
3. Leia atentamente a descrição, critérios de aceite e dependências.
4. Em caso de dúvidas, alinhe com o responsável antes de iniciar o desenvolvimento.

### 2. Criação da Branch

Toda implementação deve ser realizada em uma branch específica.

### Padrão de nomenclatura

```text
feat/nome-da-feature
```

### Exemplos

```text
feat/cadastro-de-usuarios
fix/correcao-login
docs/governanca-de-dados
refactor/ajusta-variaveis
test/cobertura-endpoint-login
chore/atualizar-dependencias
```

### Passos

```bash
git checkout main
git pull origin main
git checkout -b feat/cadastro-de-usuarios
```

### 3. Desenvolvimento

Durante o desenvolvimento:

* Seguir os padrões de código definidos pela equipe.
* Realizar commits frequentes e descritivos.
* Garantir que a solução atende aos critérios de aceite.

Boas práticas de commit:

```text
feat: adiciona endpoint de cadastro de usuário
fix: corrige validação de CPF
refactor: reorganiza camada de serviço
docs: atualiza documentação
chore: atualiza arquivo .gitignore
test: adiciona testes para cadastro de usuário
```


### 4. Abertura da Pull Request

Após concluir o desenvolvimento:

1. Faça push da branch.

```bash
git push origin feat/cadastro-de-usuarios
```

2. Abra uma Pull Request para a branch principal definida pelo projeto.
3. Siga o template de Pull Request.
4. Aguarde revisão.

### 6. Revisão de Código

Após abrir a Pull Request:

1. Solicite revisão dos responsáveis do repo.
2. Aguarde feedback.
3. Realize os ajustes solicitados.
4. Responda comentários quando necessário.

### 7. Aprovação e Merge

Após aprovação:

1. Verifique se não existem conflitos.
2. Realize o merge seguindo a estratégia definida pelo projeto.

### 8. Conclusão da Tarefa

Após o merge:

1. Mova a tarefa para "Concluído".
2. Atualize horas trabalhadas, quando aplicável.
3. Adicione comentários relevantes sobre a entrega.

### Fluxo Resumido

```text
Selecionar tarefa
        ↓
Criar branch
        ↓
Desenvolver
        ↓
Testar
        ↓
Abrir Pull Request
        ↓
Revisão
        ↓
Ajustes (se necessário)
        ↓
Aprovação
        ↓
Merge
        ↓
Concluir tarefa
```
