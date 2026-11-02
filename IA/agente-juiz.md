# Agente Juiz e revisão da resposta

## Objetivo e entradas

Descrever a política de `app/agents/judge.py`, `judge_specialist.py`, `app/config.py` e `app/graph/workflow.py` na `main` `f6f3d8c` (02/11/2026).

O Juiz recebe `JudgeInput`: pergunta, candidata completa, `agent_results`, contexto e gráfico. Evidências são os outputs reais das ferramentas e os trechos recuperados. Pergunta, candidata, gráfico e pareceres anteriores não comprovam fatos por si mesmos. O contexto inclui perfil, mensagens recentes tratadas, memória relevante, avisos e dados de revisão.

## Avaliação Jev

Uma chamada tipada contém uma `Choice` de gravidade (`no_error`, `correctable_error`, `critical_error`) e duas `Noul`: `facts_supported` e `relevant`. A rubrica versionada é `delta-judge-fixed-v8`. A aplicação não usa uma etapa Score nem calcula projeções pelo Juiz.

| Critério | Variável | Default do código |
| --- | --- | --- |
| Confiança na gravidade | `JEV_CONFIDENCE_THRESHOLD` | 0,70 |
| Probabilidade da categoria escolhida | `JEV_PROBABILITY_THRESHOLD` | 0,70 |
| Suporte factual | `JEV_FACTS_SUPPORTED_THRESHOLD` | 0,60 |
| Relevância | `JEV_RELEVANCE_THRESHOLD` | 0,25 |

Os limites são inclusivos (`>=`).

Sem falhas nos critérios e com `no_error`, aprova. Erro corrigível ou limite não atingido pede correção na primeira rodada; na revisão rejeita. Erro crítico é rejeitado pela política Jev. Falha de configuração, provedor ou formato retorna `status=unavailable`, sem liberar a candidata.

## Segundo juiz quando há baixa confiança

`JudgeAgent.run` encaminha **qualquer resultado Jev avaliado cuja confiança fique abaixo do limite** ao `SpecialistJudgeAgent`. Isso inclui um resultado com gravidade crítica de baixa confiança: o parecer especialista substitui a decisão inicial. Não há fallback ao segundo juiz por indisponibilidade do Jev nem somente por probabilidade/suporte/relevância baixos com confiança suficiente.

O segundo juiz usa o provedor generativo selecionado: OpenAI no modo padrão. Sua resposta é tipada em `decision`, `severity` e `justification`; ele não reescreve a candidata.

Parecer crítico é rejeitado. Aprovação com gravidade diferente de `no_error` é rejeitada como inconsistente. Se o segundo juiz pedir correção, a revisão volta diretamente a ele, com seu parecer anterior e a avaliação Jev original. Não há segunda correção.

## Ação no grafo

| Resultado | Ação |
| --- | --- |
| `evaluated` + `approve` | Publica candidata e segue ao guardrail final. |
| `evaluated` + `correct`, sem revisão anterior | Preserva evidências, acrescenta feedback e executa uma revisão. |
| `reject`, `unavailable` ou correção esgotada | Mensagem segura e gráfico nulo. |


## Limites da garantia

O julgamento não é garantia de verdade, diagnóstico de vazamento ou validação de transação. Os thresholds controlam decisões do código, sem constituir acurácia medida no domínio.

Cadastro de hábito já pode ter sido gravado antes desse parecer. Rejeitar a candidata não desfaz o cadastro. O guardrail final pode limpar texto aprovado e descartar gráfico, sem um segundo julgamento do texto limpo.

Testes versionados: `test_ci_judge.py`, `test_ci_judge_specialist.py` e integração no grafo. A inspeção desses testes não equivale à execução real com Jev ou à avaliação de qualidade semântica.

## Fontes da implementação revisada

- [app/agents/judge.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/agents/judge.py)
- [app/agents/judge_specialist.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/agents/judge_specialist.py)
- [app/config.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/config.py)
