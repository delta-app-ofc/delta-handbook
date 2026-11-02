# Inteligência artificial do Delta

## Objetivo

Esta área descreve o funcionamento do chatbot, como integrar a API e como operar e verificar seus componentes.

Os caminhos `app/`, `frontend/`, `tests/`, `scripts/` e `db/` citados nestes documentos pertencem ao repositório de IA. Os nomes de modelos e valores de configuração descrevem a configuração da aplicação; não atestam disponibilidade comercial, preços atuais ou acesso pela conta.

## Por onde começar

| Assunto | Documento |
| --- | --- |
| Componentes, responsabilidades e limites | [Arquitetura](arquitetura-inteligencia-artificial.md) |
| Percurso de uma pergunta e ramificações | [Workflow](workflow.md) |
| Estado, roteador, execução e extensão do grafo | [Implementação LangGraph](implementacao-langgraph-orquestracao.md) |
| Agentes e runtime de ferramentas | [Implementação LangChain](implementacao-agentes-langchain.md) |
| Consumo observado, períodos e autorização | [Agente de consumo](consumption-agent.md) |
| Previsão, metas e cenários de investimento | [Previsões e simulações](previsoes-simulacoes.md) |
| Cadastro, estimativa de litros e custo dos hábitos | [Hábitos](habitos.md) |
| Critérios Jev, segundo juiz e revisão única | [Agente Juiz](agente-juiz.md) |
| HTTP, autenticação RS256, SSE e sugestões | [API FastAPI](implementacao-api-fastapi.md) |
| PII, injeção, isolamento e saída pública | [Guardrails](implementacao-guardrails.md) |
| Histórico MongoDB, metadados e resumos Qdrant | [Memória e sessões](implementacao-memoria-sessoes.md) |
| Indexação automática e proveniência documental | [RAG](rag-retrieval.md) |
| Fontes públicas aprovadas e transporte stdio | [MCP externo](mcp-conhecimento-externo.md) |
| Ambientes e parâmetros | [Settings](settings.md) |
| Papéis e escolha de provedores | [Modelos](llm-models.md) |
| Pool e dependências SQL | [PostgreSQL](postgres-connection.md) |
| Clientes app/telemetria e contratos documentais | [MongoDB](mongo-connection.md) |
| Rastreamento, métricas, PDF e LangSmith | [Observabilidade](observabilidade.md) |
| Otimizações e medições históricas | [Redução de latência](reducao-latencia.md) |
| Desenvolvimento, console, testes e entrega | [Operação e validação](operacao-validacao.md) |

## Estado implementado e limites

Cinco especialistas são roteáveis: consumo, previsão, vazamento, hábitos e RAG. Perfil é resolvido em Python a partir dos vínculos da conta; não há `ProfileAgent` no registro. O Juiz avalia candidatas de especialistas antes da publicação. Saudações e orientações fixas seguem caminhos sem julgamento.

A API tem autenticação, histórico, SSE de etapas e sugestões por regras. O console de testes e o Monitor também existem. Há cálculos determinísticos de projeção, cenários e custo de hábitos; o LLM explica os resultados. O agente de vazamento lê sinais existentes e não executa o motor de detecção.

MCP recupera artigos de um catálogo fechado. Não há implementação A2A, integração Redis no fluxo da IA ou consulta meteorológica ao vivo: hábitos consultam `weather_daily` no MongoDB.

## Limites e pontos de atenção

- `JEV_PROBABILITY_THRESHOLD` tem default **0,70** em `app/config.py`, mas `.env.example` define **0,50**. O valor efetivo depende do ambiente. O default de confiança é 0,70, e não 0,50.
- `create_habit` grava no SQL durante a execução da ferramenta, **antes do Juiz**. A revisão retira essa ferramenta, mas rejeitar a resposta não desfaz um cadastro já confirmado.
- O README de IA ainda cita `scripts.check_postgres`, `scripts.check_mongo`, guias em `DADOS/IA/agentes/` e documentos/testes de reutilização ausentes no serviço. Os comandos atuais estão em [operação](operacao-validacao.md).
- A descrição 503 em `AUTH_ERRORS` ainda menciona somente `JWT_SECRET`; o comportamento real aceita RS256 e restringe HS256 a desenvolvimento/teste.
- O `lifespan` fecha clientes RAG, segundo juiz, OpenAI e pool SQL. O fechamento de MongoDB e dos caches próprios da memória longa não está conectado a esse encerramento.
- O console chama o grafo sem persistência, mas salva pelo próprio caminho a pergunta original e a resposta. Não é modo somente leitura nem garante a mesma anonimização do histórico do chat autenticado.
- A média de previsão usa intervalo corrido entre datas disponíveis, diferente da média de consumo por dias com registros.
- O histórico usa dois anexos independentes por turno e ignora falhas de salvamento no grafo. Uma resposta HTTP bem-sucedida não comprova persistência completa.
- O Dockerfile copia `app/` e `frontend/`, mas não `scripts/`. O MCP inicia `app.integrations.mcp.server` por módulo e está dentro dessa cópia; CLIs de diagnóstico não estão na imagem.
- O CD chama o hook do Render em push na `main`, sem dependência explícita dos jobs de teste no mesmo workflow. A presença do YAML não comprova deploy nem configuração de proteção de branch.

Testes isolados e resultados históricos não comprovam disponibilidade de provedores ou integração com bancos de produção. A validação de ambiente exige execução própria.
