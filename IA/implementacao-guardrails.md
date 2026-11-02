# Guardrails de entrada e saída

## Objetivo

Explicar as barreiras implementadas em `app/guardrails/` e `app/graph/workflow.py`, conforme a `main` de IA `f6f3d8c` (02/11/2026). São camadas complementares à [autenticação](implementacao-api-fastapi.md) e aos filtros de ownership nas consultas.

## Entrada em duas partes

`validate_input_rules` valida usuário positivo, mensagem não vazia e limite de 2000 caracteres. Anonimiza padrões de CPF, CNPJ, telefone e e-mail com tokens temporários; aplica padrões de injeção e tentativas de assumir outro usuário; recusa palavras/expressões relacionadas à exposição de dados internos.

O mapa de PII permanece no estado da execução para substituir tokens por omissões na saída. A anonimização é por expressões regulares e não detecta todo dado pessoal, nome ou endereço. Não deve ser descrita como anonimização completa de qualquer conteúdo.

Depois das regras, `classify_input` chama `llm_rapido` para categorias `APROVADO`, `OFENSIVO`, `PERIGOSO` e `ILICITO`. Categorias bloqueadas recebem texto fixo. **Falha do classificador é registrada e permite continuar**; resposta sem categoria reconhecida também não bloqueia por si só.

No grafo, o classificador roda em paralelo com contexto e roteador dentro de `prepare`. Nenhum especialista executa antes da liberação, mas leituras de contexto e chamada de roteamento podem já ter acontecido. Recusa determinística ocorre antes dessa preparação paralela.

## Julgamento e saída

O [Juiz](agente-juiz.md) avalia a candidata pronta e as evidências, com até uma revisão. Não substitui as regras de saída.

`validate_output` recusa resposta vazia, mascara os mesmos padrões de PII e troca tokens pelo rótulo de omissão, sem restaurar os dados originais. Expressão de possível credencial (`senha`, `password` ou `secret` com atribuição) bloqueia a saída.

`validate_ownership` procura referência explícita ao ID de outro usuário no texto. `chart_mentions_other_user` percorre dicionários/listas e descarta gráfico com campo `user_id` diferente do autenticado. São verificações por padrões/campos, sem capacidade de provar a origem de toda frase ou ponto de gráfico.

Após aprovação dessas regras, `hide_technical_details` remove frases que expõem nomes de agentes, ferramentas, status, bancos e erros técnicos. Se não restar conteúdo útil, usa mensagem genérica. `capitalize_habit_names` apresenta os nomes do catálogo em formato de título. Esse tratamento ocorre depois do Juiz, sem nova avaliação da versão limpa.

## Persistência e erros públicos

A entrada bloqueada termina o grafo; chat JSON retorna 422 e tenta remover a sessão recém-criada vazia. Em SSE já aberto, o bloqueio vira evento `error` com status 422.

Recusa do guardrail final substitui o texto por mensagem segura e remove gráfico; não é automaticamente erro HTTP. O turno pode ser salvo com essa resposta. O histórico recebe a pergunta do estado, já anonimizada pelas regras, e o texto final tratado. As duas gravações não formam transação única.

O console pode testar um especialista isoladamente e não deve ser confundido com o fluxo completo de autenticação, perfil, Juiz e saída da aplicação.

## Verificação e limites

`test_guardrails.py`, `test_hide_technical_details.py` e `tests/isolation/` cobrem padrões, saída e isolamento em cenários controlados. Proteção depende também de identidade vinda do JWT, seleção autorizada de unidades, consultas parametrizadas e ferramentas com escopo fixo.

Regras de texto podem ter falsos positivos/negativos. A revisão documental não executou ataque real nem prova ausência de vazamento. Não há promessa de detecção universal de injeção, PII ou conteúdo indevido.

## Fontes da implementação revisada

- [app/guardrails/input.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/guardrails/input.py)
- [app/guardrails/output.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/guardrails/output.py)
