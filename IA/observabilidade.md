# Observabilidade e rastreamento do Delta AI

## Objetivo e referência

Explicar rastreamento, métricas e relatório da `main` de IA `f6f3d8c`, revisada em 02/11/2026. A revisão conferiu código; as rodadas reais de 31/10 registradas ao final são histórico anterior, sem reexecução nesta atualização.

## Implementação

| Peça | Arquivo / interface |
| --- | --- |
| Trace, eventos, erro seguro, modelos e embeddings | `app/observability/diagnostics.py` |
| Middleware ASGI e `X-Request-ID` | `app/observability/http.py` |
| Rótulos públicos de progresso | `app/observability/progress.py` |
| Registro, preços, percentis, resolução, ROI e projeção | `app/observability/metrics.py` |
| Funções de resumo/PDF | `app/routes/monitor.py`, `app/observability/report.py` |
| Monitor do console | `frontend/tabs/monitor.js`, `/playground/observability`, `/playground/observability/report.pdf` |
| Projeção por CLI | `python -m scripts.cost_projection --pdf relatorio.pdf` |
| LangSmith opcional | `app/observability/langsmith.py`, `scripts/langsmith_reconcile.py` |

`app/routes/monitor.py` fornece funções chamadas pelo console; não há router administrativo de observabilidade registrado em `app/main.py`. O Monitor depende do playground habilitado, sem Bearer próprio.

## Rastreamento de uma requisição

O servidor gera `X-Request-ID`, coloca-o na resposta e mantém o contexto ao longo dos nós, modelos, ferramentas e fases do RAG. Não reutiliza ID arbitrário do cliente. Erros são representados de forma segura, preservando tipos, localização e cadeia de causas sem expor texto bruto de credenciais/SDKs.

`set_event_sink` permite integrar um consumidor de eventos; a existência desse ponto não configura armazenamento ou handlers de logs externos. `public_data` trata dados do diagnóstico e não deve ser considerado detecção universal de PII. O console pode exibir informações de teste e candidatas para inspeção; o contrato público de `/chat` é mais restrito.

## Registro e recuperação

São gravados modos de fluxo completo `chat` e `judge`, incluindo SSE quando a rota define o modo do trace. O registro de métricas não guarda pergunta, resposta ou `user_id` bruto. Ele reúne tempos, modelos, tokens, custo, revisões, resultado e canal.

A coleção é `observability_requests` no Mongo de app. Persistência ocorre em thread daemon; falha não altera a resposta. Há buffer de até 2000 registros em RAM e leitura de até 1000 registros de banco por padrão, mesclados por ID. Após falha do Mongo, novas tentativas ficam suspensas por 60 segundos. Reinício perde o buffer; não é fila durável.

A IA não garante aplicação de validador, índices ou TTL no cluster. A referência de schema/governança deve ser conferida no `delta-mongo-database`. A especificação anterior previa TTL de 90 dias e índices por request/canal/usuário; esta revisão não verificou o cluster nem a aplicação desses scripts.

`X-Client: app` ou `web` identifica canal. Console usa `playground`; ausente/inválido vira `unknown`. `OBS_HASH_SECRET` com pelo menos 16 caracteres habilita HMAC do usuário; sem ele não há contagem confiável de usuários distintos. Não é o ID original nem deve ser usado como identificador público.

## Métricas e interpretação

- Latência total acompanha chegada até encerramento HTTP, incluindo streaming. Há p50/p95/p99 e tempos por nó/agente/fase RAG.
- Falhas 5xx, rejeições e resultados parciais são separados. Uma falha recuperada por fallback pode deixar o atendimento parcial.
- `resolved` significa resultado `success`, modo completo e ausência do nó de bloqueio do Juiz. **Não exige provar que uma ferramenta trouxe dados suficientes**; explicação de indisponibilidade sem erro registrado pode contar como resolução.
- Custo por resolução divide custo de IA pelas resoluções. ROI usa `(resoluções × custo de atendimento humano − custo IA) / custo IA`; não inclui infraestrutura, manutenção ou desenvolvimento.
- SLO padrão atual: **p95 até 15 segundos**, erro até 5%, configuráveis. Sem dados, não há avaliação.
- Tempos de nós podem se sobrepor pela preparação paralela. `overhead_ms` usa máximo entre zero e total menos soma de nós; não é decomposição rigorosa de tempo exclusivo.

## Custos e premissas configuradas

A tabela interna `DEFAULT_PRICES` representa USD por milhão de tokens e pode ser sobrescrita por `OBS_PRICES_JSON`. Estes são valores presentes no código, **não preços de mercado confirmados nesta revisão**:

| Modelo / prefixo | Entrada | Saída |
| --- | --- | --- |
| `gpt-6-luna` | 0,10 | 0,50 |
| `gemini-2.5-flash` | 0,30 | 2,50 |
| `openai/gpt-oss-120b` | 0,15 | 0,60 |
| `openai/gpt-oss-20b` | 0,075 | 0,30 |
| `gemini-embedding-001` | 0,15 | 0 |
| `gemini-embedding-2` | 0,20 | 0 |
| `jev` | 0,042 | 0 |

Zero de saída Jev é uma premissa da tabela, não prova de gratuidade. Modelo sem preço é sinalizado em `unpriced_models`; não interprete custo parcial como fatura completa. URLs de origem dos preços ficam em `PRICE_SOURCES` no código e precisam ser verificadas quando os valores forem usados para decisão financeira.

Embeddings usam contagem oficial `count_tokens` quando a resposta não traz usage. Contagem é concluída em background e o registro pode ter estado pendente; falha deixa chamada sem contagem e custo não estimado. Jev usa `usage` retornado pelo provedor. Cache, impostos e forma de cobrança podem divergir do cálculo.

Premissas: `OBS_SUPPORT_COST_USD=8.01` e `OBS_USD_TO_BRL=5.4212` são números configurados, sem atualização automática. O primeiro é referência externa de atendimento humano, não custo medido do Delta. `OBS_QUESTIONS_PER_USER_WEEK=0` usa taxa medida somente quando há janela suficiente (ao menos sete dias) e usuários identificáveis; valor explícito permite cenário assumido.

Projeções para 100/1000 usuários usam custo médio por requisição no cenário base e p95 no pessimista. Com poucas observações, percentis e ROI são frágeis; publicação de resposta não demonstra economia real de água.

## LangSmith

Habilite com `LANGSMITH_TRACING=true`, chave e projeto, somente no ambiente apropriado. `LANGSMITH_SEND_CONTENT=false` é o default: a integração define `LANGSMITH_HIDE_INPUTS=true` e `LANGSMITH_HIDE_OUTPUTS=true`. Com envio de conteúdo habilitado, prompts/respostas podem ir ao serviço externo.

`APP_ENV=test` impede leitura de `.env` quando definido no processo, mas não apaga variáveis LangSmith já presentes nele. O caminho de tracing deve ser conferido no ambiente de teste. Runs levam metadados como sessão e canal. `python -m scripts.langsmith_reconcile` consulta a comparação quando configurado; não foi executado nesta revisão.

## Lacunas e verificação

Não há autorização administrativa por papel exposta para o Monitor. Autenticação RS256 para chat/sessões já existe e não resolve, por si só, essa área administrativa. Aplicação da coleção/TTL em cluster, envio de `X-Client` pelos consumidores e observabilidade contínua precisam ser verificados nos ambientes responsáveis.

`test_observability.py`, `test_progress.py` e testes de SSE cobrem contratos e cálculos controlados. Nenhuma nova chamada, PDF ou conexão de banco foi executada nesta revisão documental.

## Registros históricos de validação

Os resultados abaixo foram preservados da versão anterior do handbook. Descrevem aquelas amostras, modelos, bancos e configuração; não comprovam desempenho da main revisada nem devem ser comparados sem controlar as condições.

**Validado em 31/10/2026**

- Testes automatizados (`tests/test_observability.py`, repositório de IA): custo, tokens, percentis, erros, resolução, ROI, projeção, SLO sem dados, mesclagem de registros, fonte de cada preço, ausência de texto no registro e geração do PDF.
- Três chamadas reais de chat com Gemini (`LLM_PROVIDER=gemini`, perguntas de consumo, previsão e vazamento): tokens e custo foram capturados (23.075 tokens de entrada e 2.019 de saída, US$ 0,0045 no total, cerca de US$ 0,0015 por pergunta). O valor **não** vem só das tarifas do Gemini: com as falhas do provedor, 8 chamadas foram para o modelo reserva do Groq (`openai/gpt-oss-120b`, US$ 0,15 / 0,60), mais barato. Aplicar a tarifa do Gemini 2.5 Flash (0,30 / 2,50) a todos os tokens daria cerca de US$ 0,012, o que não corresponde a essa execução. As três terminaram como parciais e o p95 foi de 46,7 s, porque o MongoDB e o provedor falharam nesse ambiente.
- LangSmith: os traces chegaram ao projeto `delta-ai` e `scripts.langsmith_reconcile` os leu (4 runs raiz, 27.576 tokens, US$ 0,0085 pelo cálculo do LangSmith).
- Aba **Monitor** no navegador: cartões, gráficos e tabela de projeção renderizados com dados dessa chamada real.
- **`gpt-6-luna` com uso real** (provedor padrão, OpenAI Responses): três perguntas custaram US$ 0,0019 no total, cerca de US$ 0,0006 por pergunta, com 15.332 tokens de entrada, 724 de saída e 5 chamadas ao modelo por pergunta, sem fallback. O custo bate com a tabela de preços (0,10 / 0,50).
- **MongoDB local descartável** (`docker-compose.dev.yml`, porta 27018, base `delta_test_obs`, apagada ao final): a gravação em `observability_requests` e a leitura de volta funcionaram, e o registro não contém pergunta, resposta nem `user_id`.
- **PDF** no estilo do relatório de BI: gerado e conferido página a página como imagem.
- **Atlas e PostgreSQL** (31/10/2026, depois de liberar o IP no Atlas e subir o Postgres do `docker-compose.dev.yml` com os scripts de `db/postgres-init/`): o `ping` dos dois clusters respondeu, e três perguntas reais com o `gpt-6-luna` terminaram com 2 sucessos e 1 parcial, p50 de 19,5 s e custo de US$ 0,0037 no total (US$ 0,0012 por pergunta, 5,7 chamadas ao modelo).
- **Jev e embeddings com contagem real**: o Jev devolveu `usage` (15.961 tokens numa pergunta, US$ 0,00067) e o `count_tokens` do Google contou 12 tokens para um texto de 51 caracteres.

## Fontes da implementação revisada

- [app/observability/http.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/observability/http.py)
- [app/observability/metrics.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/observability/metrics.py)
- [app/observability/langsmith.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/observability/langsmith.py)
