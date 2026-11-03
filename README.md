# Delta Handbook · Documentação do projeto

![Documentação](https://img.shields.io/badge/Conte%C3%BAdo-Markdown-083FA1?logo=markdown&logoColor=white)
![Validação](https://img.shields.io/badge/CI%20documental-Python%203.12-3776AB?logo=python&logoColor=white)
![Projeto](https://img.shields.io/badge/Projeto-Delta-2E8B57)

Este repositório reúne a documentação do Projeto Delta: arquitetura, modelagem de dados, regras de negócio, operação, requisitos e acordos de trabalho. Os scripts e aplicações ficam nos repositórios dos componentes.

**Tags:** `documentação` · `engenharia-de-dados` · `postgresql` · `mongodb` · `business-intelligence` · `devops` · `requisitos` · `ux`

## Sumário

- [Visão geral](#visão-geral)
- [Navegação por assunto](#navegação-por-assunto)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Padrões de documentação](#padrões-de-documentação)
- [Validar documentos](#validar-documentos)
- [Contribuir](#contribuir)
- [Repositórios relacionados](#repositórios-relacionados)

## Visão geral

O Projeto Delta é uma plataforma acadêmica de monitoramento inteligente do consumo residencial de água. A arquitetura de dados documentada usa PostgreSQL para dados relacionais e MongoDB para telemetria e dados documentais. As páginas de cada área descrevem seus componentes, decisões e fluxos.

| Área | O que você encontra |
|---|---|
| Engenharia de dados | Arquitetura, camadas analíticas, indicadores, modelagem e operação dos bancos. |
| Business Intelligence | Processo de análise e definições dos indicadores BI. |
| IA | Arquitetura, agentes, RAG, memória, conexões, configurações e observabilidade. |
| DevOps | Convenções de branch e commit, CI, revisão e governança de Pull Requests. |
| EQS | Requisitos funcionais, fluxo de trabalho, dinâmica de equipe e padrões de projeto e teste. |
| UX | Fluxos e funcionalidades das experiências do produto. |

## Navegação por assunto

- [Arquitetura de dados](DADOS/engenharia-dados.md) e [infraestrutura de bancos](DADOS/infra-bancos.md).
- [Processo de BI](DADOS/BI/processo-bi.md) e [indicadores de BI](DADOS/BI/indicadores-bi.md).
- [Modelagem relacional SQL](DADOS/SQL/modelagem-relacional.md), [regras de negócio SQL](DADOS/SQL/regras-negocio.md) e [camada de BI SQL](DADOS/SQL/camada-bi.md).
- [Modelagem MongoDB](DADOS/NoSQL/modelagem-mongodb.md) e [regras de negócio NoSQL](DADOS/NoSQL/regras-negocio.md).
- [Arquitetura de Inteligência Artificial](IA/arquitetura-inteligencia-artificial.md) e [observabilidade](IA/observabilidade.md).
- [Convenções de desenvolvimento](DEVOPS/convencoes-desenvolvimento.md), [CI](DEVOPS/ci-workflows.md) e [regras de revisão de PR](DEVOPS/pr-review-rules.md).
- [Requisitos funcionais](EQS/requisitos-funcionais.md), [fluxo de trabalho](EQS/fluxo-trabalho.md) e [fluxos de UX](UX/fluxos-e-funcionalidades.md).

## Estrutura do repositório

```text
delta-handbook/
├── DADOS/
│   ├── BI/              # Processo e indicadores de Business Intelligence
│   ├── NoSQL/           # Modelagem, regras e governança MongoDB/NoSQL
│   └── SQL/             # Modelagem, regras, auditoria, acesso e camada analítica
├── DEVOPS/              # Convenções, CI e governança de Pull Requests
├── EQS/                 # Requisitos, fluxo e práticas da equipe
├── GERAL/               # Documentação geral
├── IA/                  # Arquitetura, implementação e operação de IA
├── UX/                  # Fluxos e funcionalidades
├── scripts/             # Validador dos documentos Markdown
└── README.md            # Ponto de entrada desta documentação
```

## Inteligência artificial

A documentação do chatbot está em [IA/leia-me.md](IA/leia-me.md), com arquitetura, API, agentes, Juiz, memória, RAG/MCP, configuração e operação do serviço.

## Padrões de documentação

- Escreva em português claro e comece cada documento com título e objetivo.
- Use nomes em minúsculas com palavras separadas por hífens, por exemplo `modelagem-relacional.md`.
- Prefira links relativos e confirme que o destino existe.
- Registre contexto e justificativas; diferencie recursos implementados de planos ou propostas.
- Use tabelas para comparações e blocos de código para comandos e exemplos.

## Validar documentos

Com Python 3.12 instalado, execute na raiz:

```bash
python scripts/validate_markdown.py
```

O validador confere os arquivos Markdown rastreados pelo Git e sinaliza documentos vazios ou marcadores de conflito de merge. O workflow de CI documental executa esse validador; os testes das aplicações ficam nos respectivos repositórios.

## Contribuir

Antes de criar uma página, procure o assunto nas pastas acima e atualize a referência existente quando isso evitar duplicação. Para decisões de desenvolvimento, consulte as [convenções de branches e commits](DEVOPS/convencoes-desenvolvimento.md). Mantenha cada alteração no repositório responsável pelo conteúdo.

## Repositórios relacionados

- [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database) — scripts do banco PostgreSQL.
- [delta-mongo-database](https://github.com/delta-app-ofc/delta-mongo-database) — scripts de configuração do MongoDB.
- [delta-business-intelligence](https://github.com/delta-app-ofc/delta-business-intelligence) — pipelines e consultas de BI.

## Processos de DevOps

Consulte o [guia de DevOps](DEVOPS/README.md) para configurar CI/CD, publicar aplicações no Render e operar os pipelines Glue e Databricks.
