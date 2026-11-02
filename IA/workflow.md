# Fluxo de uma pergunta no LangGraph

## Objetivo

Descrever o percurso implementado em `app/graph/workflow.py`, na `main` de IA `f6f3d8c`, revisada em 02/11/2026. Para contratos internos e extensão, consulte [implementação LangGraph](implementacao-langgraph-orquestracao.md).

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

## Etapas

1. A rota autentica, cria/valida a sessão e chama `run_workflow` ou `run_workflow_events`.
2. `guardrail_input` valida tamanho e identidade, anonimiza padrões de PII e bloqueia injeção/dados internos. Recusa termina sem executar especialistas.
3. `prepare` roda o classificador LLM em paralelo com contexto e roteador. O contexto resolve perfil SQL em paralelo à leitura de histórico/memória. Se a guarda bloquear, o resultado preparado é descartado e nenhum especialista roda. Consultas de contexto e roteamento podem já ter ocorrido.
4. `route` escolhe nomes do registro, remove duplicados/desconhecidos e aplica a lista permitida pelo perfil. Sem vínculo ou com perfil desconhecido, não chama o roteador e não seleciona agentes.
5. `execute` roda especialistas **em sequência**, com o ID confiável, histórico recente e resumo das respostas anteriores. Uma falha vira resultado `error`, sem impedir os próximos agentes.
6. `synthesize` usa o modelo rápido somente quando pelo menos dois agentes tiveram sucesso. `respond` usa a síntese ou respostas disponíveis e o primeiro gráfico aplicável; saudações e restrições recebem mensagens fixas.
7. `compose` forma a candidata. Violação de privacidade, ausência de agentes ou ausência de sucesso seguem direto à saída; candidata pronta vai ao Juiz.
8. `judge` avalia pergunta, candidata, contexto, gráfico e outputs reais. Aprovação publica; pedido de correção na primeira passagem prepara uma única revisão; rejeição, falha ou nova correção bloqueiam.
9. `revise` preserva candidata e resultados anteriores, acrescenta feedback e repete execução/composição. Tools e fontes anteriores são mantidas como evidência. A ferramenta de cadastro de hábito é retirada da revisão.
10. `output_guard` mascara PII, verifica referência a terceiros no texto/gráfico, remove detalhes técnicos e formata nomes de hábitos. Persiste o turno quando habilitado e inicia geração de metadados em background.

A revisão pode executar ferramentas de leitura novamente. Não há mecanismo geral que transforme todas as escritas em operações posteriores ao Juiz; veja [hábitos](habitos.md).

## Estado e memória

O checkpoint em RAM usa `thread_id = user_id:session_id`. A execução inicializa campos de resultado e julgamento para cada pergunta. No chat persistente, tenta ler histórico Mongo uma vez e compartilhá-lo com o contexto; falha nessa leitura permite nova tentativa. Ao terminar, remove o checkpoint do chat persistente. A chamada do console com `persist_session=False` mantém checkpoint em memória; a rota ainda grava mensagens por caminho próprio, conforme [operação](operacao-validacao.md).

São usadas até seis mensagens recentes no contexto. Memória longa é consultada quando a pergunta contém gatilhos temporais/conversacionais. Isso é uma heurística por termos, não uma garantia de recuperação para toda referência ao passado.

## Saída, bloqueios e progresso

Um bloqueio do Juiz devolve a mensagem segura e remove o gráfico; não equivale ao erro 422 de entrada. O guardrail final também pode substituir texto ou descartar gráfico. A candidata aprovada é verificada na saída e pode ser alterada por essa limpeza, sem novo julgamento.

`run_workflow_events` usa worker e fila para publicar etapas, keepalive e estado final. O cliente recebe apenas rótulos fixos até a resposta final. Detalhes em [API](implementacao-api-fastapi.md), [guardrails](implementacao-guardrails.md) e [Juiz](agente-juiz.md).

## Fontes da implementação revisada

- [app/graph/workflow.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/graph/workflow.py)
