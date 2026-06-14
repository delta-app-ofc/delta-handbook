# **📘 DevOps — Validação de Pull Requests e Roteamento de Times**

Esta documentação descreve o funcionamento, a arquitetura e a configuração do ecossistema de CI/CD do **Projeto Delta** voltado para a governança de Pull Requests (PRs). O objetivo desta automação é garantir que nenhuma alteração de código seja integrada sem a descrição adequada, preenchimento correto dos checklists organizacionais e a atribuição automática dos times revisores responsáveis.

## **🎯 1. Visão Geral do Fluxo**

A automação opera de forma reativa e centralizada sempre que um Pull Request é **aberto (opened)** ou **editado (edited)** em qualquer repositório da organização. O fluxo segue três etapas sequenciais obrigatórias:

```markdown
[Abertura/Edição do PR]   
          │  
          ▼  
┌──────────────────────────────────┐  
│  1. Validação de Checklists      │ ──► Falhou? ──► Comenta no PR & Barra o Merge (sys.exit(1))  
└──────────────────────────────────┘  
          │ Passou!  
          ▼  
┌──────────────────────────────────┐  
│  2. Validação da Descrição       │ ──► Menos de 30 chars úteis? ──► Barra o Merge (sys.exit(1))  
└──────────────────────────────────┘  
          │ Passou!  
          ▼  
┌──────────────────────────────────┐  
│  3. Roteamento de Times (Review) │ ──► Executa 'gh pr edit' adicionando os revisores mapeados  
└──────────────────────────────────┘  
          │  
          ▼  
[Pipeline Liberado (sys.exit(0))]
```

## **📂 2. Arquitetura Centralizada (Repositório .github)**

Para evitar a replicação de scripts em múltiplos repositórios do ecossistema (como delta-database, serviços backend e aplicações frontend), adotou-se o padrão de **Repositório Central de Organização** (.github).

### **Estrutura de Pastas no Repositório .github**

```plaintext
.github/
├── .github/
├── └── workflows/
│       └── main.yml  # Workflow do GitHub Actions herdado globalmente
├── profile/  
├── scripts/  
│   ├── route_checks.py          # Script Python com a inteligência de validação e roteamento  
│   └── route_reviewers.py       # Script Python com a lógica de roteamento de revisores
```

*Nota de Implementação:* Quando o workflow é disparado em um repositório satélite (ex: delta-database), o GitHub Actions realiza o download temporário do repositório .github em uma pasta isolada chamada central-scripts para conseguir executar o interpretador Python sem expor ou poluir o diretório do projeto principal. Esse processo é executado a partir de um .github/workflows/*.yml que centraliza a lógica de execução de workflow do repositório central da organização.

## **⚙️ 3. Configuração do Workflow (main.yml)**

Este arquivo de workflow fica localizado na pasta .github/workflows/ no repositório central. Ele é responsável por gerenciar o ciclo de vida da execução, solicitar as credenciais corretas e baixar tanto o projeto atual quanto o repositório centralizador de scripts.

### **Trecho Principal da Execução do Workflow:**
```yaml
steps:  
    # 1. Baixa o código do projeto onde o PR foi aberto (ex: delta-database)  
    - name: Checkout do código do projeto  
      uses: actions/checkout@v4

    # 2. Baixa o repositório centralizador de scripts (.github) na pasta temporária 'central-scripts'  
    - name: Checkout dos scripts globais (.github)  
      uses: actions/checkout@v4  
      with:  
        repository: '${{ github.repository_owner }}/.github'  
        path: 'central-scripts'

    # 3. Executa o script Python apontando para a pasta temporária de scripts  
    - name: Executar script de validação e roteamento  
      env:  
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}  
        PR_BODY: ${{ github.event.pull_request.body }}  
        PR_URL: ${{ github.event.pull_request.html_url }}  
        ORG_NAME: ${{ github.repository_owner }}  
      run: python ./central-scripts/scripts/route_checks.py
```

## **🧠 4. Funcionamento do Script**

O script Python é modularizado em três principais pilares lógicos para garantir flexibilidade e manutenibilidade.

### **4.1 Validação de Caixas de Seleção (route_checks.py -> check_options)**

Valida de forma rigorosa se os blocos de opções do template foram devidamente respondidos. Ela utiliza o método any() e all() para as seguintes condições:

* **Escopo/Módulo Impactado:** Mínimo de 1 item marcado (any).  
* **Tipo de PR (Conventional Commits):** Mínimo de 1 item marcado (any).  
* **Uso de Inteligência Artificial:** Mínimo de 1 item marcado (any).  
* **Checks de Rigor Técnico (Mandatórios):** Todos os itens obrigatoriamente marcados (all).

### **4.2 Validação Inteligente da Descrição (route_checks.py -> check_description)**

A validação de conteúdo real de descrição utiliza expressões regulares para extrair o texto digitado entre as seções, expurgando as formatações e orientações fixas do template.

#### Isolamento da seção de Descrição usando Regex  
```python
match = re.search(r"## 📄 Descrição(.*?)## ✨ Tipo de PR", str_pr_body, re.DOTALL)
```

#### Remoção de sintaxe Markdown que polui a contagem de caracteres reais  
```python
clean_text = raw_description.replace(">", "").replace("\n", "").replace("*", "")
```

#### Expurgo das frases instrutivas padrões do template  
```python
template_phrases = [
    r"Descreva o que foi implementado.",  
    r"2° ANO: Lembre-se de registrar qual Requisito Funcional (RF) do documento de Engenharia de Software está sendo atendido."  
]  
for phrase in template_phrases:  
    clean_text = re.sub(phrase, "", clean_text, flags=re.IGNORECASE)

# Contagem final de caracteres reais (Mínimo de 30 caracteres)  
character_count = len(clean_text.strip())
```

### **4.3 Roteamento Dinâmico de Times (route_reviewers.py -> assign_teams)**

Caso o PR passe em todas as validações anteriores, o script mapeia os checkboxes do escopo e utiliza a ferramenta de linha de comando oficial do GitHub (gh cli) para adicionar os times correspondentes de forma transparente.
```python
mapping = {  
    "- [x] Backend (Java": "back-primeiro",  
    "- [x] Frontend (HTML": "front-primeiro",  
    "- [x] API REST (Spring Boot)": "back-segundo",  
    "- [x] Aplicação Dinâmica (React": "front-segundo",  
    "- [x] Infraestrutura / Pipeline de CI/CD": "sys_devops"  
}

for template_text, team_slug in mapping.items():  
    if template_text.lower() in body_lower:  
        full_team = f"{org_name}/{team_slug}"  
        # Solicita revisão para o time via CLI do GitHub no ambiente do runner  
        subprocess.run(["gh", "pr", "edit", pr_url, "--add-reviewer", full_team])

```

## **🛠️ 5. Guia de Resolução de Problemas (Troubleshooting)**

| **Sintoma**                                             | **Causa Provável**                                                                                                          | **Solução**                                                                                                                                                                                         |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Pipeline falha por arquivo não encontrado**           | O caminho configurado no .yml não condiz com a estrutura do repositório central.                                            | Verifique se o caminho no workflow aponta exatamente para ./central-scripts/scripts/route_checks.py (ou route_reviewers.py). Garanta que a pasta do script no repositório central se chama scripts. |
| **O checklist passa, mas os times não são adicionados** | O token temporário do GitHub Actions não tem permissões suficientes para interagir com o PR ou com os times da organização. | Certifique-se de que o bloco permissions: pull-requests: write está explicitado no arquivo de workflow .yml.                                                                                        |
| **Times marcados como revisores inexistentes**          | O slug mapeado no dicionário do Python não existe na organização do GitHub.                                                 | Confirme se o nome do time no GitHub bate exatamente com a chave mapeada (ex: gestao-2ano).                                                                                                         |
