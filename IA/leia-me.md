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
