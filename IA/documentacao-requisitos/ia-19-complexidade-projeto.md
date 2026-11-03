### IA-19 — Demonstrar e justificar a complexidade do projeto

**Evidência direta:**

- [Repositório da IA](https://github.com/delta-app-ofc/delta-artificial-intelligence)
- [README da IA](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/README.md)
- [Documentação da IA no handbook](https://github.com/delta-app-ofc/delta-handbook/tree/main/IA)
- [Grafo do LangGraph (`workflow.py`)](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/graph/workflow.py)
- [Agentes](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/app/agents)
- [Guardrails](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/app/guardrails)
- [Memória de sessão e de longo prazo](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/app/memory)
- [Autenticação por JWT (`auth.py`)](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/auth.py)
- [Integração MCP](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/app/integrations/mcp)
- [Observabilidade, custo e ROI (`metrics.py`)](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/observability/metrics.py)
- [Testes de isolamento entre usuários](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/tests/isolation)
- [Conjuntos de avaliação](https://github.com/delta-app-ofc/delta-artificial-intelligence/tree/main/evals/datasets)

**Localização e como comprovar:**

Este documento reúne, em um só lugar, os componentes que fazem a IA do Delta ser mais do que uma chamada a um modelo de linguagem. Para cada componente, ele indica onde está no código, por que existe e qual problema resolve. Os detalhes de cada peça estão nos documentos da pasta `IA/`, citados na seção 4.

#### 1. Visão geral

Uma pergunta do usuário passa por validação, perfil e contexto, escolha de especialistas, cálculo com dados reais, composição da resposta e uma revisão independente, antes de ser publicada e gravada. O modelo de linguagem interpreta resultados. Os cálculos de consumo e previsão acontecem em Python, com ferramentas determinísticas.

```
guardrail de entrada → prepare (perfil e contexto) → execute (especialistas)
        → synthesize → respond → compose → judge ──┬─ publish ──→ guardrail de saída → persist
                                                   ├─ revise ──→ execute (uma única vez)
                                                   └─ block ───→ guardrail de saída → persist
```

#### 2. Os componentes e por que existem

| # | Componente | O que é | Onde está | Por que existe |
|---|---|---|---|---|
| 1 | Sete agentes | `ConsumptionAgent`, `ForecastAgent`, `LeakAgent`, `HabitsAgent`, `RagAgent`, `JudgeAgent` e `SpecialistJudgeAgent` | `app/agents/` | Cada um tem ferramentas e responsabilidade próprias, e nenhum recebe acesso a dados de que não precisa |
| 2 | Orquestração em grafo | `StateGraph` do LangGraph com 13 nós e arestas condicionais | `app/graph/workflow.py` | O caminho da pergunta muda conforme o perfil, o roteador e o parecer do Juiz, e o grafo deixa esses desvios explícitos |
| 3 | RAG com fontes externas via MCP | Busca vetorial no Qdrant e um servidor MCP local, que lê um catálogo fechado de artigos públicos | `app/agents/rag.py`, `app/tools/rag.py`, `app/integrations/mcp/` | A IA responde com base em fonte citável, e não de memória, e o modelo não escolhe URLs |
| 4 | Memória de sessão | Histórico na coleção `chat_sessions` do MongoDB | `app/memory/session.py` | A conversa continua entre mensagens, com um documento por sessão |
| 5 | Memória de longo prazo | Resumos com embeddings no Qdrant | `app/memory/long_term.py` | Perguntas que citam o passado encontram o contexto de conversas anteriores |
| 6 | JWT com isolamento de usuário | O `user_id` vem do token RS256, e as ferramentas recebem o `user_id` já fixado | `app/auth.py`, `build_tools(user_id)` | O modelo nunca recebe o `user_id` como argumento, então não consegue consultar dados de outra pessoa |
| 7 | Guardrails | Validação na entrada e na saída | `app/guardrails/input.py`, `output.py` | Bloqueia injeção de prompt, anonimiza dados pessoais e impede vazamento de credenciais e de ids alheios |
| 8 | Juiz com segunda avaliação | O Juiz com Jev avalia a resposta e, se a confiança for menor que 0,70, um segundo juiz decide | `app/agents/judge.py`, `judge_specialist.py` | Nenhuma resposta é publicada sem revisão independente do modelo que a escreveu |
| 9 | Dados reais em PostgreSQL e MongoDB | Cadastro, tarifas e faturas no PostgreSQL, e telemetria, alertas e sessões no MongoDB | `app/data/db_postgres.py`, `db_mongo.py` | A resposta usa os números do usuário, e não valores inventados |
| 10 | Observabilidade com custo e ROI | Tokens, custo, latência, erros, resolução e ROI por requisição | `app/observability/` | Mostra quanto cada pergunta custa e se a IA compensa o atendimento que substitui |

#### 3. Justificativa de cada decisão

##### 3.1 Sete agentes em vez de um

Um agente único precisaria de todas as ferramentas e de um prompt enorme. Dividir por responsabilidade traz três ganhos:

- **Ferramentas restritas.** O agente de consumo só lê consumo, o de previsão só calcula previsão, e assim por diante.
- **Perfis.** A conta residencial usa consumo, previsão, vazamento, hábitos e RAG. A conta comercial usa os mesmos, sem hábitos. A conta sem vínculo não aciona agente algum.
- **Revisão separada.** Dois dos sete agentes são juízes, e nenhum deles escreve a resposta que avalia.

O agente de vazamento não detecta vazamentos. Ele descreve sinais que o motor de regras (`delta-business-rules`) já registrou. Essa fronteira evita que o modelo invente um diagnóstico.

##### 3.2 Orquestração em grafo

O grafo tem os nós `guardrail_input`, `prepare`, `execute`, `synthesize`, `respond`, `compose`, `judge`, `revise`, `publish`, `block`, `confirm`, `output_guard` e `persist`. As arestas condicionais decidem, por exemplo, se a pergunta é bloqueada antes de chamar um agente, se o Juiz pede revisão ou se a resposta é bloqueada.

Cada nó recebe o mesmo `X-Request-ID`, o que permite medir o tempo e o custo por etapa. O ponto de salvamento (checkpoint) do LangGraph é apagado depois de cada chat, e o histórico vem do MongoDB.

##### 3.3 RAG com fontes externas via MCP

O RAG tem duas fontes:

- **Base do produto.** O documento `delta-main-source.md` é indexado no Qdrant, e o agente recebe trechos com capítulos e linhas para citar.
- **Conhecimento externo.** Um servidor MCP local, iniciado por stdio, lê só artigos públicos cadastrados em `app/integrations/mcp/sources.py` (MIDR/gov.br e EPA). Não há porta HTTP nem URL escolhida pelo modelo.

Perguntas, histórico, dados da conta e chaves não são enviados à fonte pública. O cache é limitado ao catálogo e não serve conteúdo vencido quando a fonte falha. O prompt declara que as páginas educativas não comprovam tarifas, normas brasileiras nem dados da conta.

##### 3.4 Memória de sessão e de longo prazo

| Memória | Onde fica | Quando é lida |
|---|---|---|
| Sessão | MongoDB, `chat_sessions` | A cada mensagem, para montar o histórico da conversa |
| Longo prazo | Qdrant (embeddings Gemini) | Quando a pergunta faz referência ao passado |

O `session_id` é sempre criado pelo servidor. As funções de sessão só operam em sessões do próprio usuário e ignoram sessões excluídas (`is_deleted`).

##### 3.5 JWT e isolamento entre usuários

O back-end emite o JWT (RS256), e este serviço apenas o valida com `AUTH_PUBLIC_KEY`, `AUTH_ISSUER` e `AUTH_AUDIENCE`. O isolamento tem camadas:

- o `user_id` fica preso às ferramentas por `build_tools(user_id)`;
- as funções organizacionais do PostgreSQL recebem o `user_id` e descartam propriedades que não sejam das organizações dele;
- uma sessão de outro usuário devolve o mesmo 404 que uma sessão inexistente;
- o guardrail de entrada bloqueia tentativas de agir como outro usuário, e o de saída descarta respostas e gráficos com o id de outro usuário.

Há uma pasta de testes de isolamento (`tests/isolation/`) com testes de autenticação, sessões, camada de dados, ferramentas e guardrails. Os testes de sessão usam um MongoDB real descartável.

##### 3.6 Guardrails

| Camada | Verificações |
|---|---|
| Entrada | Rejeita mensagem vazia, com mais de 2.000 caracteres ou com `user_id` inválido, detecta padrões de injeção de prompt e anonimiza CPF, CNPJ, telefone e e-mail antes de enviar ao modelo |
| Saída | Rejeita resposta vazia ou com padrão de credencial, redige CPF, CNPJ e telefone e troca os tokens de dados pessoais por `[TIPO OMITIDO]`, sem devolver o valor original |

Os guardrails existem na rota HTTP e dentro do grafo (defesa em profundidade). Há também conjuntos de avaliação de segurança em `evals/datasets/` (entrada, PII, titularidade, roteador, RAG e Juiz).

##### 3.7 Juiz com segunda avaliação

1. O `JudgeAgent` avalia a resposta composta com o Jev, junto com as ferramentas e as fontes usadas, em três critérios: gravidade, suporte factual e relevância.
2. Se a confiança for igual ou maior que **0,70**, vale o parecer do Jev.
3. Se for menor, o `SpecialistJudgeAgent` dá um segundo parecer (padrão OpenAI `gpt-6-luna`), podendo aprovar, pedir correção ou bloquear.
4. Há **no máximo uma correção** por pergunta. Uma segunda solicitação de correção bloqueia a resposta, e a candidata rejeitada não é publicada.
5. Uma falha do Jev bloqueia a resposta, e não conta como baixa confiança.
6. Se o provedor do segundo juiz falhar de forma transitória e `LLM_FALLBACK_ENABLED` estiver ligado, o mesmo pedido vai ao Groq.

O parecer do segundo juiz fica no histórico com `assessment.reviewer=specialist`, e o parecer original do Jev permanece em `assessment.jev_result`.

##### 3.8 Dados reais em PostgreSQL e MongoDB

| Banco | O que a IA lê ou grava |
|---|---|
| PostgreSQL | Perfil de acesso, imóveis autorizados, tarifas e faturas, por funções `fn_*` do `delta-sql-database` |
| MongoDB | Telemetria de consumo, histórico de alertas, sessões de chat e métricas de observabilidade |

Os dois bancos têm clientes reaproveitados e configuração centralizada em `app/config.py`. As credenciais não são exigidas no import, e os erros não expõem senhas nem URIs.

##### 3.9 Observabilidade com custo e ROI

Cada requisição de chat completo grava, na coleção `observability_requests`, os tokens por agente, o custo de modelo, de embeddings e do Jev, a latência por etapa, o resultado e a revisão do Juiz, sem guardar pergunta nem resposta. O `user_id` não é gravado, só um HMAC (`user_hash`).

```
ROI = (resoluções × custo de um atendimento − custo de IA) ÷ custo de IA
```

O ROI é um limite superior, porque só entram os tokens. Hospedagem, bancos e manutenção ficam de fora. O custo de embeddings sem contagem oficial não é estimado: a chamada fica marcada como "sem contagem". Os indicadores aparecem na aba Monitor do console e em um relatório em PDF.

#### 4. Documentação detalhada de cada peça

| Tema | Documento |
|---|---|
| Arquitetura geral | [arquitetura-inteligencia-artificial.md](../arquitetura-inteligencia-artificial.md) |
| Agentes | [implementacao-agentes-langchain.md](../implementacao-agentes-langchain.md) |
| Orquestração | [implementacao-langgraph-orquestracao.md](../implementacao-langgraph-orquestracao.md) |
| RAG | [rag-retrieval.md](../rag-retrieval.md) |
| Memória de sessão | [implementacao-memoria-sessoes.md](../implementacao-memoria-sessoes.md) |
| Autenticação | [autenticacao.md](../autenticacao.md) |
| Guardrails | [implementacao-guardrails.md](../implementacao-guardrails.md) |
| Modelos de linguagem | [llm-models.md](../llm-models.md) |
| Observabilidade | [observabilidade.md](../observabilidade.md) |
| Redução de latência | [reducao-latencia.md](../reducao-latencia.md) |
| Detecção de anomalias | [deteccao-anomalias.md](../deteccao-anomalias.md) |

#### 5. Como comprovar

1. Abrir `app/agents/` e conferir os sete agentes. O `_runtime.py` é a base comum, e não conta como agente.
2. Abrir `app/graph/workflow.py` e conferir os 13 nós e as arestas condicionais.
3. Rodar `python -m pytest tests -q` com `APP_ENV=test` e conferir os testes. O repositório tem mais de 600 funções de teste, e os testes de isolamento de sessão exigem um MongoDB local (`docker-compose.dev.yml`).
4. Rodar `python -m scripts.check_mcp --all` e conferir que o servidor MCP lê as fontes públicas.
5. Abrir o console em `/playground/`, enviar uma pergunta e conferir a aba **Monitor** com custo, latência e ROI.

#### 6. Limitações conhecidas

- **Testes com substitutos.** Os testes de agentes, perfis e ferramentas usam modelos falsos e bancos substituídos, então não medem a qualidade semântica das respostas com os provedores reais.
- **Vazamento em conta comercial.** O vazamento por unidade ainda não existe: os alertas do MongoDB só têm `user_id` e `device_id`, e separar por unidade exige uma função nova no `delta-sql-database`.
- **Papéis dentro da organização.** Todo usuário vinculado a uma organização vê todas as unidades dela, por decisão de produto.
- **Classificador de injeção.** Se o modelo do classificador falhar, a mensagem passa (disponibilidade acima de bloqueio).
- **Console sem autenticação.** O `/playground` não exige login e vem ativo em desenvolvimento e teste.
- **README desatualizado.** O fluxo mostrado na seção "Orquestração LangGraph" do README ainda não mostra os nós `compose`, `judge`, `revise`, `publish` e `block`. O grafo real em `workflow.py` os tem.
- **Redis e A2A.** O Redis aparece nas dependências, mas não tem integração neste repositório. O protocolo A2A está fora do escopo por decisão de negócio.
