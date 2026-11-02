# Arquitetura do sistema de IA do Delta

## Objetivo

Explicar os componentes implementados e suas responsabilidades. Base: `main` de IA. O [índice da área](leia-me.md) reúne os detalhes e as divergências encontradas.

## Visão geral

O serviço Python recebe perguntas autenticadas, resolve o perfil de acesso, seleciona especialistas, consulta ferramentas e avalia a resposta candidata antes de devolvê-la. FastAPI expõe HTTP; LangGraph controla as etapas; LangChain integra modelos e ferramentas. Cálculos de consumo, projeção e cenários são feitos em Python.

```text
App/web → FastAPI → autenticação + sessão → guardrails e contexto
                                             ↓
                             perfil confiável + roteador
                                             ↓
                       especialistas + ferramentas de dados
                                             ↓
                           síntese → candidata → Juiz
                                             ↓
                      aprovação / uma revisão / bloqueio
                                             ↓
                        guardrail de saída → histórico → HTTP
```

O streaming envia rótulos de progresso; o texto só sai ao final. Não há geração token a token para o cliente.

## Responsabilidades

| Componente | Implementação | Responsabilidade |
| --- | --- | --- |
| Consumo | `app/agents/consumption.py` | Totais observados, comparação de períodos, picos diários e unidades autorizadas. |
| Previsão | `app/agents/forecast.py` | Projeção mensal, estimativa de conta, meta e simulações determinísticas. |
| Vazamento | `app/agents/leak.py` | Explicar janelas anômalas e alertas já registrados, com hábitos como contexto residencial. |
| Hábitos | `app/agents/habits.py` | Consultar/cadastrar hábitos, estimar litros e custo e consultar clima histórico. |
| RAG | `app/agents/rag.py` | Recuperar regras do produto e práticas gerais de fontes externas aprovadas. |
| Juiz | `app/agents/judge.py`, `judge_specialist.py` | Avaliar candidata e evidências, pedir no máximo uma correção ou bloquear. |
| Perfil | `app/graph/profile.py` | Resolver vínculos e limitar agentes; não é um especialista LLM. |

Os cinco primeiros estão em `AGENT_REGISTRY`. O Juiz é uma etapa do grafo. Prompts reservados não comprovam agentes adicionais.

## Dados e integrações

| Dependência | Uso efetivo na IA |
| --- | --- |
| PostgreSQL | Conta ativa, vínculos, imóveis/unidades, tarifas, contas, hábitos e consultas organizacionais consolidadas. Pool por processo. |
| MongoDB app | `chat_sessions`, preferências/metas, alertas, clima histórico e métricas operacionais. |
| MongoDB telemetria | Janelas de `consumption_summary`, incluindo sinais de anomalia. |
| Qdrant | `rag_documents` para conhecimento e `session_summaries` para memória de conversas. Coleções distintas, 3072 dimensões. |
| Modelos generativos | OpenAI por padrão; modo Gemini/Groq configurável e fallback de especialista para erros transitórios. |
| Jev / TypeSafe | Classificação tipada de gravidade, suporte factual e relevância. |
| MCP local | Subprocesso stdio para ler artigos públicos cadastrados; não é um serviço HTTP externo do Delta. |
| LangSmith | Rastreamento opcional; conteúdo oculto por padrão pela configuração da integração. |


## Perfil e autorização

O ID vem do `sub` do JWT. As ferramentas são construídas com esse ID e não o oferecem como argumento livre ao LLM. O perfil residencial libera os cinco especialistas; o organizacional libera consumo, previsão, vazamento e RAG. Perfil `none` ou `unknown` não executa especialistas.

Para consumo e previsão organizacionais, a aplicação resolve unidades autorizadas e pede esclarecimento quando nomes são ambíguos. O consumo residencial consulta janelas pelo usuário, sem prometer separação por imóvel. Vazamento continua lendo janelas e alertas pelo usuário, sem seletor de unidade equivalente ao de consumo/previsão.

## Regras que delimitam as respostas

- Consumo observado, projeção e simulação têm significados distintos. Falta de registro não significa zero.
- O LLM não calcula valores de previsão, tarifas ou economias por conta própria.
- Indício anômalo não confirma vazamento e alerta registrado não comprova notificação entregue.
- Hábitos usam médias de referência ou valores cadastrados; não identificam consumo real por atividade.
- RAG interno explica o produto. Fontes externas oferecem práticas gerais, sem tarifas nem dados pessoais.
- O Juiz avalia texto e evidências; não é uma transação de banco. Cadastro de hábito pode ocorrer antes da aprovação da resposta.

## Operação e qualidade

`app/main.py` registra routers, CORS e middleware de rastreamento. O `lifespan` encerra recursos selecionados. O console em `frontend/` oferece abas por agente, roteador, chat, Juiz e Monitor.

Há testes isolados e testes de histórico que dependem de MongoDB descartável e podem ser pulados quando ele falta. Workflows de testes, Sonar, governança e CD existem, mas sua existência não comprova execução bem-sucedida nem proteção do merge.

Consulte [operação e validação](operacao-validacao.md), [workflow](workflow.md), [API](implementacao-api-fastapi.md) e [Juiz](agente-juiz.md). A imagem `desenho-arquitetura.png` é um artefato anterior; o fluxo textual desta revisão descreve o comportamento atual.

## Fontes da implementação revisada

- [app/main.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/main.py)
- [app/graph/router.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/router.py)
- [app/graph/profile.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/profile.py)
