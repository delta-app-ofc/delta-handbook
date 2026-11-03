# 📑 Handbook de DevOps — Template de Pull Request

Este documento descreve o padrão, as diretrizes e a estrutura dos templates de Pull Request (PR) utilizados no Projeto Delta, garantindo a padronização, o rigor técnico e a rastreabilidade de todas as alterações feitas no sistema de monitoramento inteligente de consumo de água.

---

## 🎯 1. Objetivo do Template

O template de Pull Request funciona como uma linha de defesa para a qualidade do código antes de sua integração com as branches principais (`main`/`develop`). Ele foi desenhado para atender tanto aos critérios de engenharia de software do 1° e do 2° ano quanto às boas práticas de mercado.

### 📌 Benefícios do Uso:
* **Rastreabilidade:** Vincula o código diretamente aos Requisitos Funcionais (RF) documentados.
* **Governança de IA:** Monitora de forma transparente o uso de ferramentas de Inteligência Artificial no desenvolvimento.
* **Garantia de Qualidade:** Obriga o desenvolvedor a revisar um checklist de rigor técnico antes de solicitar o Code Review.

---

## 📂 2. Implementação no Repositório

No GitHub, um repositório pode manter seu próprio template no caminho abaixo. Quando não há template próprio, os repositórios elegíveis herdam o template padrão do repositório organizacional `.github`, onde ele fica em `pull_request_template.md`:

> **Caminho:** `.github/pull_request_template.md`

---

Consulte o [template organizacional completo](https://github.com/delta-app-ofc/.github/blob/main/pull_request_template.md). O esquema a seguir explica as seções; não substitui os textos e opções oficiais usados pela automação.

## 📝 3. Estrutura Oficial do Template
O template de Pull Request deve conter as seguintes seções, organizadas de forma clara e objetiva:

```markdown

## 📄 Descrição
[!NOTE] PREENCHIMENTO OBRIGATÓRIO
> Descrição objetiva do que foi implementado.

## ✨ Tipo de PR (Seguindo Conventional Commits) 
[!NOTE] PREENCHIMENTO OBRIGATÓRIO
> Seleção do tipo de PR (feat, fix, refactor, docs, test).

## 💻 Módulos Impactados - 1° ANO (Marque com um "x")
[!NOTE] PREENCHIMENTO OBRIGATÓRIO PARA O 1° ANO
> Seleção dos módulos mais simples que foram impactados pelo 1° ano.

## 💻 Módulos Impactados - 2° ANO (Marque com um "x")
[!NOTE] PREENCHIMENTO OBRIGATÓRIO PARA O 2° ANO
> Seleção dos módulos mais complexos que foram impactados pelo 2° ano.

## 🤖 Uso de Inteligência Artificial
[!NOTE] PREENCHIMENTO OBRIGATÓRIO
> Indicação clara se houve ou não uso de IA no desenvolvimento, para auxiliar na demanda de Memorial Descritivo do 1° ano.

## 🛠️ Padrões de Projeto e Testes 
[!NOTE] PREENCHIMENTO OPCIONAL
> Descrição do teste utilizado para garantir consistência da feature.

## ✅ Checklist de Rigor Técnico (Marque com um "x")
[!NOTE] PREENCHIMENTO OBRIGATÓRIO
> Seleção de itens de checklist que garantem o rigor técnico do código, como uso de Conventional Commits, acessibilidade, tratamento de exceções, validação de dados, etc.
```

## ⚙️ 4. Diretrizes de Preenchimento para a Equipe
Para garantir que o fluxo de integração contínua ocorra sem problemas, os desenvolvedores devem se atentar às seguintes regras ao preencher o PR:

- Conventional Commits: O título do Pull Request deve refletir o tipo de alteração principal (ex: feat: adiciona tabela tb_alerta).
- Descrições válidas: A descrição deve ser clara, objetiva e, no caso do 2° ano, deve mencionar o RF específico que está sendo atendido.
- Checklist de Rigor Técnico: Todos os itens aplicáveis devem ser marcados para garantir a qualidade do código antes do Code Review.
- Seleção de Módulos: Marcar corretamente os módulos impactados para facilitar a revisão e a rastreabilidade.
- Evidências de IA: O preenchimento do bloco de Inteligência Artificial é obrigatório. Ocultar o uso de IA ou omitir os prompts no Memorial Descritivo invalidará a entrega do 1° ano.

## 5. Responsabilidade de preenchimento e automação

Preserve os títulos `## 📄 Descrição` e `## ✨ Tipo de PR`, os textos dos checkboxes e os itens obrigatórios. A descrição precisa conter pelo menos 30 caracteres úteis, sem contar as instruções padrão. Para alterações de processo ou infraestrutura sem RF de produto, explique essa não aplicabilidade em vez de inventar um requisito.

| Item | Quem preenche ou confirma |
| --- | --- |
| Descrição, tipo e módulos | Autor da PR; marque pelo menos um tipo e um módulo reconhecidos. |
| Uso de IA | Autor da PR; informe se houve auxílio e mantenha as evidências acadêmicas exigidas. |
| Conventional Commits | Validador dos commits marca a opção após sucesso. O título da PR sozinho não comprova os commits. |
| Proteção de `.env` | Validador de `.gitignore` e arquivos rastreados marca a opção após sucesso. |
| Código testado | Reporter marca ou desmarca conforme o resultado dos jobs técnicos para a versão atual da PR. |
| Demais itens técnicos | Autor e revisores avaliam conforme aplicabilidade; justifique N/A sem declarar verificações não realizadas. |

O validador de checklist exige os itens de commits e testes, além de descrição, tipo, escopo e uso de IA. Os demais itens continuam relevantes para a revisão, mesmo sem uma checagem automática específica. Em uma PR documental, descreva a revisão do conteúdo, a validação Markdown e a conferência dos links; não declare testes de aplicação que não ocorreram.

Não marque uma caixa para contornar um check reprovado. Confira o resultado da versão atual em Checks e aguarde a atualização automática. Veja o [fluxo de revisão e merge](pr-review-rules.md) para corrigir falhas de governança, reporter ou permissões.
