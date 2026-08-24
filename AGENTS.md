# AGENTS.md — Contexto do Delta Handbook para Agentes de IA

Este arquivo orienta agentes de IA e pessoas desenvolvedoras que atuam neste repositório. As instruções valem para todo o `delta-handbook`, salvo quando um arquivo `AGENTS.md` mais específico definir regras adicionais em uma subpasta.

## 1. Visão geral do Projeto Delta

O Delta é um projeto acadêmico do Ensino Médio Técnico em Análise e Desenvolvimento de Sistemas. O produto é uma plataforma IoT de monitoramento inteligente do consumo residencial de água: dispositivos como ESP32 e Arduino Uno R4 WiFi coletam pulsos de hidrômetros, enquanto os demais componentes do sistema consolidam consumo, apoiam a detecção de vazamentos, estimam gastos e disponibilizam informações em aplicações e em um chatbot.

A arquitetura de dados documentada é multi-banco:

- PostgreSQL para dados cadastrais, transacionais, regras de negócio e auditoria;
- MongoDB para telemetria IoT e dados de aplicação adequados ao modelo documental;
- Redis para necessidades planejadas de cache, ranking e tempo real;
- Neo4j para necessidades planejadas de análise de relações em grafos.

Redis e Neo4j aparecem na documentação de arquitetura, mas não possuem implementação neste workspace. Não apresente componentes planejados como se já estivessem implementados e não invente repositórios, caminhos, serviços ou integrações.

## 2. Contexto deste repositório

O `delta-handbook` é o repositório central de conhecimento do Projeto Delta. Ele reúne documentação técnica, arquitetura de dados, requisitos, práticas de Engenharia e Qualidade de Software, DevOps, governança e padrões de desenvolvimento. Este repositório é documental: não contém a implementação dos bancos, do backend, do frontend, do aplicativo mobile ou dos agentes de IA.

Responsabilidades principais:

- manter uma fonte de referência comum para decisões e processos do projeto;
- descrever a arquitetura e as responsabilidades dos componentes sem substituir seus repositórios de implementação;
- registrar regras de negócio, modelagens, governança, auditoria e carga de dados;
- documentar requisitos, fluxo de trabalho, convenções de desenvolvimento e revisão de Pull Requests;
- reservar áreas para documentação futura sem tratar arquivos placeholder como funcionalidades concluídas.

### Estrutura atual do repositório

```text
delta-handbook/
├── .github/workflows/       # Integração com as automações compartilhadas da organização
├── DADOS/                   # Arquitetura e engenharia de dados
│   ├── NoSQL/               # Modelagem, regras e governança do MongoDB
│   └── SQL/                 # Modelagem, regras, auditoria, governança e dataload do PostgreSQL
├── DEVOPS/                  # Branches, commits, Pull Requests e regras de revisão
├── EQS/                     # Fluxo da equipe e requisitos funcionais
├── GERAL/                   # Área reservada para documentação geral
├── UX/                      # Área reservada para documentação de experiência do usuário
└── README.md                # Apresentação e padrões gerais do handbook
```

Antes de descrever qualquer estrutura, decisão ou tecnologia, confira os arquivos atuais. Preserve distinções entre estado implementado, estado apenas documentado ou planejado e hipótese ainda não validada.

## 3. Leitura obrigatória do `TASK.md`

Antes de executar qualquer tarefa, leia integralmente o arquivo `TASK.md` localizado na raiz deste repositório e trate seus requisitos e critérios de aceite como escopo operacional da atividade.

Se o `TASK.md` não existir:

- não crie esse arquivo;
- não invente requisitos ausentes;
- use somente o escopo fornecido explicitamente pela pessoa solicitante e peça esclarecimento quando faltar uma decisão indispensável.

Também leia os documentos diretamente relacionados à área alterada. Para mudanças de processo, consulte primeiro `DEVOPS/`; para dados, consulte `DADOS/`; para requisitos ou dinâmica de trabalho, consulte `EQS/`.

## 4. Padrão de branches e commits

Cada alteração deve partir da `main` mais recente e ser desenvolvida em uma branch própria:

```bash
git checkout main
git pull origin main
git checkout -b <tipo>/<descricao-da-alteracao>
```

Use uma descrição curta, clara, em minúsculas e separada por hífens. Os tipos documentados em `DEVOPS/convencoes-desenvolvimento.md` são:

| Tipo | Uso |
| --- | --- |
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança de comportamento |
| `docs` | Criação ou atualização de documentação |
| `test` | Criação ou manutenção de testes |
| `style` | Alteração de estilização |

Exemplos adequados para este repositório:

```text
docs/agents-md
docs/atualiza-governanca-mongodb
fix/corrige-link-modelagem
```

Os commits seguem Conventional Commits no formato `<tipo>: descrição`, por exemplo:

```text
docs: adiciona contexto do repositorio para agentes
fix: corrige referencia da documentacao de auditoria
```

Não trabalhe diretamente na `main`, não misture assuntos sem relação na mesma branch e mantenha o escopo documental deste repositório.

## 5. Padrão de documentação

Ao criar ou alterar arquivos Markdown, siga o padrão definido no `README.md` e observado no handbook:

- use extensão `.md`, com nome em minúsculas e palavras separadas por hífens;
- comece com um título claro e informe o objetivo ou o contexto do documento;
- organize o conteúdo em seções e subseções com hierarquia coerente de títulos;
- explique decisões e justificativas, não apenas o resultado final;
- use listas para conjuntos de regras, tabelas para comparações e blocos de código para comandos ou exemplos técnicos;
- use diagramas somente quando ajudarem a compreender relações ou arquitetura e mantenha o arquivo de imagem próximo ao documento relacionado;
- prefira links relativos e verifique se os caminhos apontam para arquivos existentes;
- preserve termos técnicos, nomes de objetos de banco e exemplos que tenham significado para as regras de negócio;
- registre atualizações relevantes quando o histórico for necessário;
- antes de criar um novo documento, verifique se o assunto já está coberto e atualize a fonte existente quando isso evitar duplicação.

Não declare uma tecnologia, fluxo, regra ou integração como existente sem evidência nos repositórios ou na documentação oficial vigente. Quando houver divergência entre documentos, exponha-a em vez de escolher silenciosamente uma versão.

## 6. Limites de atuação

- Não crie código executável de outros componentes dentro deste repositório.
- Não invente caminhos ou estruturas de repositórios que não estejam clonados no workspace.
- Não altere documentação não relacionada à tarefa apenas para padronização estética.
- Não crie `TASK.md`.
- Mantenha as mudanças restritas aos arquivos documentais solicitados.
- Valide links, nomes e estrutura contra o estado real antes de concluir.

## 7. Limite de complexidade e nível técnico

As soluções devem ser compatíveis com o conhecimento de estudantes do Ensino Médio Técnico em Análise e Desenvolvimento de Sistemas.

- Priorize código simples, legível e dividido em pequenas responsabilidades.
- Utilize primeiro os recursos já presentes no repositório e conhecidos pela equipe.
- Não adicione frameworks, bibliotecas, padrões arquiteturais ou infraestrutura sem necessidade comprovada.
- Evite abstrações prematuras, metaprogramação, arquiteturas distribuídas e padrões avançados quando uma solução direta atender ao requisito.
- Não reestruture grandes partes do projeto para resolver uma tarefa localizada.
- Explique decisões técnicas e trechos não óbvios com linguagem didática.
- Quando a solução exigir conhecimento acima do limite registrado abaixo, apresente primeiro uma alternativa mais simples e solicite aprovação antes de prosseguir.
- Não implemente automaticamente uma solução avançada sem justificativa e autorização explícita.

### Stack e nível de aprofundamento da equipe

| Tecnologia ou assunto | Nível atual | Limite esperado |
| --- | --- | --- |
| Lógica de programação | Intermediário | Avançado |
| Git e GitHub | Intermediário | Avançado |
| HTML e CSS | Básico | Intermediário |
| JavaScript | Básico | Intermediário |
| Java | Intermediário | Avançado |
| Spring Boot | Básico | Avançado |
| Python | Intermediário | Avançado |
| FastAPI | Básico | Intermediário |
| SQL e PostgreSQL | Avançado | Avançado |
| MongoDB | Básico | Intermediário |
| APIs REST | Intermediário | Intermediário |
| Testes automatizados | Básico | Intermediário |
| Docker e CI/CD | Básico | Intermediário |
| Arquitetura e padrões de projeto | Básico | Intermediário |
| IoT e comunicação com hardware | Básico | Básico |

O **nível atual** representa o conhecimento que a equipe já possui e consegue aplicar com alguma autonomia. O **limite esperado** representa o nível máximo de complexidade que a IA pode utilizar.

Quando o limite esperado for superior ao nível atual, a IA deve explicar os novos conceitos de forma simples e didática, relacionando-os ao código produzido. Qualquer solução que ultrapasse o limite esperado exige aprovação explícita antes da implementação.

## 8. Aviso de manutenção

A seção **Estrutura atual do repositório** deve ser revisada periodicamente nesta conversa e atualizada depois
de commits oficiais que adicionem, removam ou reorganizem arquivos. Antes de cada atualização, compare esta
descrição com a árvore real da `main`; o conteúdo deste arquivo não substitui a inspeção do estado atual.
