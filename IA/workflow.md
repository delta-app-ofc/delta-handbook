# Orquestração LangGraph — workflow.md

Este documento descreve o grafo LangGraph do Delta (`app/graph/workflow.py`),
explicando cada nó, as transições condicionais e como adicionar um novo agente.

## Grafo


```text
guardrail_input → prepare → execute → synthesize → respond → compose
       ↓             ↓                                      ↓
   bloqueio/END  bloqueio/END                 sem candidata: output_guard → END
                                                           ↓ candidata pronta
                                                         judge
                                               approve / correct / reject
                                                  ↓         ↓         ↓
                                               publish    revise     block
                                                  ↓         ↓         ↓
                                            output_guard  execute  output_guard
                                                  ↓                   ↓
                                                 END                 END
```

`prepare` reúne classificador semântico e contexto/roteamento. `context` e `route` são funções rastreadas executadas dentro desse nó; não são nós independentes conectados no grafo compilado.

## Nós

### `guardrail_input`

Valida a mensagem antes de qualquer lógica de negócio. Chama `validate_input_rules`
de `app/guardrails/input.py`, que:

1. Rejeita mensagens vazias, longas demais ou com `user_id` inválido.
2. Detecta padrões de injeção de prompt.
3. Anonimiza PII (CPF, CNPJ, telefone, e-mail) e armazena o mapa de tokens
   em `GraphState.pii_map`.

A parte semântica (`classify_input`) roda em `prepare`, em paralelo com contexto seguido de roteamento. Não existe `skip_guardrail_input` nesse contrato. A guarda precisa liberar antes de executar especialistas; leituras de contexto e roteamento podem ter começado.

Quando bloqueado, `_blocked=True` é setado no estado e a aresta condicional
roteia para `END` sem executar nenhum agente.

### `prepare`

Coordena a guarda semântica e a preparação do contexto/roteamento em paralelo. Se a guarda bloquear, o resultado preparado não é usado para executar especialistas.

### `context`

Recupera contexto externo antes do roteamento:

- Histórico recente da sessão (`app/memory/session.py`).
- Memória de longo prazo relevante para a pergunta (`app/memory/long_term.py`).

Armazena o resultado em `GraphState.recent_messages` e `GraphState.relevant_memory`.

### `route`

Usa `llm_rapido` (OpenAI por padrão; Groq no modo Gemini) para classificar a intenção e escolher os agentes.
A classificação vem de `app/graph/router.py` — função `classify(question, context)`.

Intenções possíveis:

| Intenção | Agentes selecionados |
|----------|---------------------|
| `consumption` | `["consumption"]` |
| `forecast` | `["forecast"]` |
| `leak` | `["leak"]` |
| `habits` | `["habits"]` |
| `rag` | `["rag"]` |
| `greeting` | `[]` — saudação por perfil |
| `no_profile` | `[]` — conta sem perfil autorizado |
| `comprehensive` | dois ou mais agentes |
| `privacy_violation` | `[]` — encerra no nó `respond` |
| `unknown` | `[]` |

A intenção `privacy_violation` é ativada quando a pergunta solicita dados de
outros usuários, rankings ou comparações entre residências distintas.

### `execute`

Chama cada agente da lista `selected_agents` em sequência.

**Context-passing entre agentes:** o primeiro agente recebe a pergunta original.
O segundo em diante recebe:

```
{pergunta original}

Contexto dos agentes anteriores:
- forecast: {primeiros 300 chars da resposta do forecast}
```

Isso permite que o LeakAgent mencione, por exemplo, que "o agente de previsão
identificou consumo elevado neste período" usando contexto anterior, sem que isso o transforme em evidência independente nem impeça uma nova consulta necessária.

Cada resultado é registrado em `GraphState.agent_results` com os campos:
`agent`, `status` (`success`, `error` ou `skipped`), `answer`, `chart_data`, `sources`, `warnings` e `tool_calls`.

### `synthesize`

Ativado apenas quando ≥ 2 agentes tiveram `status=success`. Usa `llm_rapido`
para unificar as respostas em texto coeso, indicando a origem de cada dado e
sinalizando contradições.

Se `llm_rapido` falhar (exceção), o diagnóstico registra a falha e a resposta usa concatenação
bruta com separador `---`.

### `respond`

Verifica se a intenção é `privacy_violation`. Se for, retorna:
> "Não tenho acesso a dados de outros usuários. Posso ajudar apenas com
> informações da sua conta."

Caso contrário, usa o resultado do nó `synthesize` (ou a resposta do único
agente) como candidata, que passa por composição e julgamento quando aplicável.

### `compose`, `judge`, `revise`, `publish` e `block`

`compose` decide se há candidata útil para o Juiz. `judge` avalia as evidências: aprovação segue a `publish`, correção inicial segue a `revise` e uma nova execução, rejeição/indisponibilidade seguem a `block`. Há no máximo uma revisão. Sem agentes, sem sucesso ou em orientação fixa de privacidade, o grafo pode seguir direto à saída. Veja [Juiz](agente-juiz.md).

### `output_guard`

Sanitiza a resposta antes de entregá-la:

- Remove CPF/CNPJ/telefone com `validate_output` de `app/guardrails/output.py`.
- Resolve tokens PII do mapa de entrada (ex.: `[PII_CPF_abc]` → `[CPF OMITIDO]`).
- Persiste o histórico de sessão via `append_turn` (best-effort — falha não
  interrompe o fluxo).

## Estado (`GraphState`)

Definido em `app/graph/state.py` a partir de `MessagesState`, com campos adicionais opcionais (`total=False`):

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `user_id` | `int` | Usuário autenticado |
| `session_id` | `str` | Identificador da sessão |
| `question` | `str` | Pergunta original (anonimizada após `guardrail_input`) |
| `response` | `str` | Resposta final |
| `agent_results` | `list[dict]` | Resultados de cada agente |
| `selected_agents` | `list[str]` | Agentes escolhidos pelo router |
| `intent` | `str` | Intenção classificada |
| `complexity` | `str` | `simple`, `medium` ou `complex` |
| `pii_map` | `dict` | Mapa token → valor original (opcional) |
| `_blocked` | `bool` | True se a entrada foi bloqueada |
| `access_kind` | `str` | Perfil confiável da conta |
| `candidate` | `str` | Texto composto antes da aprovação |
| `revision_count` | `int` | Número de revisões, limitado a uma |
| `judge_history` | `list[dict]` | Evidências e pareceres de cada passagem |
| `_persist_session` | `bool` | Habilita gravação do histórico pelo grafo |

## Como adicionar um novo agente

1. Implemente o agente em `app/agents/<nome>.py` seguindo o padrão de
   `ForecastAgent` — método `.run(question)` que devolve um objeto com
   `.response`, `.chart_data` e `.tool_calls`.

2. Registre o agente em `app/graph/router.py`, no dicionário `AGENT_REGISTRY`:
   ```python
   AGENT_REGISTRY["meu_agente"] = "app.agents.meu_agente.MeuAgente"
   ```

3. Adicione a intenção ao `ROUTER_PROMPT` em `app/services/prompts.py` com
   exemplos de perguntas que mapeiam para esse agente.

4. Defina os perfis permitidos em `AGENTS_BY_PROFILE`, preserve evidências e suporte a feedback/contexto de revisão.

5. Escreva testes em `tests/` com modelo roteirizado e ferramentas substituídas.

## Limitações conhecidas

- Consumo e RAG estão registrados; o Juiz já participa do grafo. Não há um especialista de perfil registrado: a resolução é feita em Python.
- A busca de memória longa usa gatilhos textuais e pode perder referências implícitas ao passado.
- Não há rate limiting por `user_id` no workflow — isso cabe a um middleware
  de API.

## Estado e memória

O checkpoint em RAM usa `thread_id = user_id:session_id`. A execução inicializa campos de resultado e julgamento para cada pergunta. No chat persistente, tenta ler histórico Mongo uma vez e compartilhá-lo com o contexto; falha nessa leitura permite nova tentativa. Ao terminar, remove o checkpoint do chat persistente. A chamada do console com `persist_session=False` mantém checkpoint em memória; a rota ainda grava mensagens por caminho próprio, conforme [operação](operacao-validacao.md).

São usadas até seis mensagens recentes no contexto. Memória longa é consultada quando a pergunta contém gatilhos temporais/conversacionais. Isso é uma heurística por termos, não uma garantia de recuperação para toda referência ao passado.

## Saída, bloqueios e progresso

Um bloqueio do Juiz devolve a mensagem segura e remove o gráfico; não equivale ao erro 422 de entrada. O guardrail final também pode substituir texto ou descartar gráfico. A candidata aprovada é verificada na saída e pode ser alterada por essa limpeza, sem novo julgamento.

`run_workflow_events` usa worker e fila para publicar etapas, keepalive e estado final. O cliente recebe apenas rótulos fixos até a resposta final. Detalhes em [API](implementacao-api-fastapi.md), [guardrails](implementacao-guardrails.md) e [Juiz](agente-juiz.md).

## Código relacionado

- [app/graph/workflow.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/graph/workflow.py)
