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

Para que o provedor de Git (como o GitHub ou GitLab) carregue este template automaticamente sempre que um novo Pull Request for aberto, o arquivo deve ser salvo exatamente no seguinte caminho do repositório:

> **Caminho:** `.github/pull_request_template.md`

---

## 📝 3. Estrutura Oficial do Template
O template de Pull Request deve conter as seguintes seções, organizadas de forma clara e objetiva:

```markdown

## 📄 Descrição
> Descrição objetiva do que foi implementado.

## ✨ Tipo de PR (Seguindo Conventional Commits) 
> Seleção do tipo de PR (feat, fix, refactor, docs, test).

## 💻 Módulos Impactados - 1° ANO (Marque com um "x")
> Seleção dos módulos mais simples que foram impactados pelo 1° ano.

## 💻 Módulos Impactados - 2° ANO (Marque com um "x")
> Seleção dos módulos mais complexos que foram impactados pelo 2° ano.

## 🤖 Uso de Inteligência Artificial
> Indicação clara se houve ou não uso de IA no desenvolvimento, para auxiliar na demanda de Memorial Descritivo do 1° ano.

## 🛠️ Padrões de Projeto e Testes (Se aplicável) 
> Descrição do teste utilizado para garantir consistência da feature.

## ✅ Checklist de Rigor Técnico (Marque com um "x")
> Seleção de itens de checklist que garantem o rigor técnico do código, como uso de Conventional Commits, acessibilidade, tratamento de exceções, validação de dados, etc.
```

## ⚙️ 4. Diretrizes de Preenchimento para a Equipe
Para garantir que o fluxo de integração contínua ocorra sem problemas, os desenvolvedores devem se atentar às seguintes regras ao preencher o PR:

- Conventional Commits: O título do Pull Request deve refletir o tipo de alteração principal (ex: feat: adiciona tabela tbl_alerta). 
- Descrições válidas: A descrição deve ser clara, objetiva e, no caso do 2° ano, deve mencionar o RF específico que está sendo atendido.
- Checklist de Rigor Técnico: Todos os itens aplicáveis devem ser marcados para garantir a qualidade do código antes do Code Review.
- Seleção de Módulos: Marcar corretamente os módulos impactados para facilitar a revisão e a rastreabilidade.
- Evidências de IA: O preenchimento do bloco de Inteligência Artificial é obrigatório. Ocultar o uso de IA ou omitir os prompts no Memorial Descritivo invalidará a entrega do 1° ano.