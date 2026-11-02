# Implementação da orquestração LangGraph

## Objetivo

Orientar manutenção do grafo implementado em `app/graph/`, conforme a `main` de IA `f6f3d8c` (02/11/2026). O percurso completo, sem duplicar o código, está em [workflow](workflow.md).

## Módulos

| Arquivo | Responsabilidade |
| --- | --- |
| `state.py` | `GraphState`, mensagens acumuladas e `AgentOutput`. |
| `workflow.py` | Grafo, preparação paralela, execução sequencial, revisão/publicação e gerador de eventos. |
| `context.py` | Até seis mensagens recentes e memória longa condicional. |
| `profile.py` | Perfil confiável e conjuntos de agentes permitidos. |
| `router.py` | Classificação via `llm_rapido`, validação do JSON e registro dinâmico de especialistas. |
| `synthesis.py` | Síntese das respostas com sucesso quando há mais de um especialista. |
| `suggestions.py` | Perguntas iniciais e de continuação por regras, chamadas pelas rotas após o grafo. |

## Estado compartilhado

`GraphState` reúne a entrada (`user_id`, `session_id`, `question`), mensagens e contexto (`recent_messages`, `relevant_memory`, `access_kind`), intenção/complexidade e agentes selecionados. Resultados carregam resposta, gráfico, fontes, outputs de ferramentas e avisos.

Campos de julgamento incluem `candidate`, `previous_candidate`, `previous_agent_results`, `revision_feedback`, `revision_count`, `judge_history`, `judge_action` e `composition_status`. `_blocked` interrompe o caminho de entrada; `_persist_session` controla salvamento do histórico, sem desabilitar todas as escritas de ferramentas.

`AgentOutput` usa `status` igual a `success`, `error` ou `skipped`, com `agent`, `answer`, `sources`, `chart_data`, `tool_calls` e `warnings`. Não é o JSON público do chat.

## Registro e perfis

`AGENT_REGISTRY` registra `consumption`, `forecast`, `leak`, `habits` e `rag`. O carregamento importa a classe pelo caminho cadastrado e constrói a instância com `user_id` e, quando disponível, `access_kind`.

| Perfil | Especialistas permitidos |
| --- | --- |
| `residential` | consumption, forecast, leak, habits, rag |
| `organizational` | consumption, forecast, leak, rag |
| `none` / `unknown` | Nenhum; orientação fixa. |

O classificador recebe perfil, até quatro mensagens recentes e até duas memórias. Tenta ler JSON completo e, em falha, extrai do primeiro `{` ao último `}`. O contrato Pydantic valida intenção, complexidade e lista. Falha gera `intent=unknown`, `complexity=simple`, sem agentes. Nomes desconhecidos e duplicados são removidos; nomes fora do perfil são registrados em `unavailable`.

Essa filtragem acontece novamente na execução. Ela complementa autorização nas ferramentas e consultas; não substitui filtros SQL/Mongo de ownership.

## Concorrência e composição

`prepare` usa duas tarefas: guarda semântica e contexto seguido de roteamento. Contexto também pode resolver perfil em paralelo ao histórico. Cada tarefa recebe uma cópia do contexto de rastreamento. A guarda precisa liberar antes de `execute`.

Os especialistas não executam em paralelo. O próximo recebe um resumo de até 300 caracteres por resposta anterior bem-sucedida. A síntese usa resultados bem-sucedidos, preservando evidências individuais para o Juiz. Se ela não produzir saída, `respond` reúne as respostas e escolhe o primeiro gráfico disponível.

## Revisão e checkpoint

O grafo admite no máximo uma correção. Cada especialista recebe feedback, candidata anterior e seu resultado anterior. O grafo combina chamadas anteriores/novas com marcadores `previous`, `initial` ou `revision` e reúne fontes sem duplicação. O especialista de hábitos remove `create_habit` na revisão.

`MemorySaver` usa `user_id:session_id`. O histórico persistente vem do MongoDB e o checkpoint é apagado ao final do chat, inclusive no caminho de eventos. A chamada do console com `persist_session=False` conserva checkpoint no processo; reinício não o recupera. A rota do console ainda salva mensagens em Mongo por caminho próprio, conforme [operação](operacao-validacao.md).

## Adicionar ou alterar um especialista

1. Implementar a classe com `run(question, revision_feedback=..., revision_context=...)` retornando `AgentResult`.
2. Construir ferramentas vinculadas ao usuário e validar qualquer seleção de imóvel/unidade.
3. Registrar o caminho em `AGENT_REGISTRY` e os perfis aplicáveis em `AGENTS_BY_PROFILE`.
4. Ajustar prompt do roteador, prompts do especialista e rótulos de progresso quando necessário.
5. Preservar fontes e outputs reais para o julgamento, incluindo o comportamento de revisão e efeitos de escrita.
6. Cobrir seleção, isolamento, falha, composição e revisão nos testes pertinentes.

Testes relevantes incluem `test_parallel_guard.py`, `test_rag_workflow_integration.py`, `test_suggestions.py`, `test_progress.py` e `tests/user_profile/test_profile.py`. São evidência de contratos testados; não substituem integração com serviços reais.

## Fontes da implementação revisada

- [app/graph/state.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/state.py)
- [app/graph/router.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/router.py)
- [app/graph/workflow.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/workflow.py)
