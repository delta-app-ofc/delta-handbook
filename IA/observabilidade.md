# Observabilidade do Delta AI

## Objetivo

Medir custo, latência, erros, resolução e ROI do chatbot, com relatório em PDF e projeção para 100 e 1000 usuários por semana.

## O que está implementado

Os caminhos abaixo são do repositório `delta-artificial-intelligence`.

| Peça | Arquivo |
| --- | --- |
| Tokens por chamada de modelo | `app/observability/diagnostics.py` (`ModelDiagnostics`) |
| Custo, latência, resolução, ROI, projeção | `app/observability/metrics.py` |
| Gravação ao fim de cada requisição | `app/observability/http.py` |
| Resumo e PDF (funções) | `app/routes/monitor.py` (`build_summary`, `pdf_response`) |
| Aba **Monitor** e PDF no console (sem autenticação, só com o playground ativo) | `frontend/tabs/monitor.js`, `GET /playground/observability` e `/playground/observability/report.pdf` |
| Projeção por linha de comando | `python -m scripts.cost_projection --pdf relatorio.pdf` |
| LangSmith opcional | `app/observability/langsmith.py`, `scripts/langsmith_reconcile.py` |

Requisições dos modos completos `chat` e `judge` são registradas, incluindo o caminho `/chat/stream` e as abas Chat e Juiz. Cada registro fica na coleção `observability_requests` do MongoDB do app, sem pergunta nem resposta. Sem MongoDB, o painel usa os registros do processo atual; depois de uma falha de conexão o banco é ignorado por 60 s, para o painel não esperar o timeout a cada leitura.

### A coleção `observability_requests`

A definição de schema, validador, índices e permissões pertence ao repositório `delta-mongo-database`, com documentação em `collections/db_delta_app.md`. A especificação de `observability_requests` prevê os índices abaixo; é necessário conferir sua aplicação no cluster utilizado:

- TTL de 90 dias em `created_at`, para a coleção não crescer sem limite;
- único em `request_id`;
- `client` + `created_at`, para o custo por canal;
- parcial em `user_hash` + `created_at`, para contar usuários distintos.

O `user_id` bruto não é gravado no registro de métricas. O campo `user_hash` é um HMAC do usuário com o segredo `OBS_HASH_SECRET` (16 caracteres ou mais), não reversível; sem o segredo, a contagem de usuários distintos fica indisponível.

### Cliente, usuários e custo por canal

O cliente é informado pelo cabeçalho **`X-Client`**, com os valores `app` ou `web`. Sem o cabeçalho (ou com outro valor) o registro fica como `unknown`, e o console de testes é sempre `playground`. O app e a plataforma web precisam enviar esse cabeçalho nas chamadas ao `/chat` e `/chat/stream`. Com ele, o painel mostra o custo por cliente, qual cliente mais gasta, os usuários distintos e as perguntas por usuário (medidas, não mais um cenário).

### Embeddings e Jev no custo (sem estimativa)

- **Embeddings**: a resposta do `embed_content` do Google **não traz o uso** (testei: só `embeddings` e a resposta HTTP). Por isso o texto enviado é contado com o método oficial `count_tokens`, que aceita o modelo de embedding (medido: 12 tokens para 51 caracteres). Se a contagem falhar, a chamada é marcada como "sem contagem" e **o custo dela não é estimado**. Preços por 1 milhão de tokens de entrada: `gemini-embedding-001` US$ 0,15 e `gemini-embedding-2` US$ 0,20, na [página de preços do Gemini](https://ai.google.dev/gemini-api/docs/pricing) (leitura resumida, vale conferir). O custo aparece como o componente `embeddings`.
- **Jev** (Typesafe): a resposta da API traz `usage.input_tokens` e `usage.output_tokens`, que o `JudgeAgent` já lê, então o custo usa os tokens reais (medido: uma pergunta usou 15.961 tokens, US$ 0,00067). O preço de entrada é o da [home da TypeSafe](https://typesafe.ai) (US$ 42 por bilhão de tokens, ou US$ 0,042 por milhão); o de saída não é publicado e é tratado como 0, como diz a aula (Etapa 7).

## Definições

- **Tempo total**: da chegada da requisição ao fim da resposta. Latência por etapa vem dos eventos do grafo (guardrail, contexto, roteador, execução, síntese, Juiz, saída) e por agente das etapas de cada especialista. **Orquestração** = tempo total − soma das etapas.
- **Índice de erros** = requisições com falha (5xx ou etapa que quebrou) ÷ total. Bloqueios de guardrail e execuções parciais (ferramenta falhou, mas houve resposta) são contados à parte.
- **Resolução** = resposta publicada com sucesso, sem erro de agente e sem bloqueio do Juiz.
- **Custo por resolução** = custo de IA ÷ resoluções.
- **ROI** = (resoluções × custo de um atendimento − custo de IA) ÷ custo de IA. Acima de 0 há retorno. Só o custo de tokens entra no denominador; hospedagem, bancos, desenvolvimento e manutenção ficam de fora, então o ROI é um limite superior.
- **SLO**: p95 do tempo total ≤ 15 s e índice de erros ≤ 5%. Sem requisições, o SLO aparece como "sem dados".

## Indicadores da aba Monitor

- **Confiabilidade**: índice de erros, sucessos, parciais, falhas, bloqueios e chamadas ao modelo reserva (fallback).
- **Latência**: tempo total p50, p95 e p99, orquestração entre etapas, latência por etapa do grafo e por agente.
- **Custo**: custo total, por requisição e por componente, tokens de entrada e saída, tokens e chamadas ao modelo por requisição e taxa de revisão do Juiz.
- **Retorno**: taxa de resolução, custo por resolução, ROI e economia estimada.
- Gráficos: tempo por requisição com a linha do SLO, latência por etapa (p50 e p95), custo por componente e resultado das requisições. A projeção para 100 e 1000 usuários fica numa tabela. O estilo segue o console (paleta azul, fonte e painéis do projeto).

## Premissas e fontes

Todas as variáveis são lidas e validadas em `app/config.py` (`get_observability_config`), como as demais configurações; valor inválido ou negativo gera erro claro.

### Preço dos modelos (USD por 1 milhão de tokens, tarifa Standard)

Os valores abaixo registram as premissas da tabela interna e as fontes utilizadas para defini-las. Não há atualização automática de preços: confirme os valores do provedor antes de utilizá-los em uma decisão financeira.

| Modelo | Entrada | Saída | Fonte | Situação |
| --- | --- | --- | --- | --- |
| `gpt-6-luna` | 0,10 | 0,50 | [OpenAI, pricing](https://developers.openai.com/api/docs/pricing) | Oficial, lida em 31/10/2026. Cache de entrada 0,01. Acima de 272 mil tokens de entrada: 0,20 / 0,75 |
| `gemini-2.5-flash` | 0,30 | 2,50 | [Google, pricing](https://ai.google.dev/gemini-api/docs/pricing) | Oficial; a saída inclui tokens de raciocínio. A leitura da página veio resumida, vale conferir o trecho |
| `openai/gpt-oss-120b` | 0,15 | 0,60 | [Groq, página do modelo](https://console.groq.com/docs/model/openai/gpt-oss-120b) | Oficial. Entrada em cache 0,075. A página não mostra data de atualização |
| `openai/gpt-oss-20b` | 0,075 | 0,30 | [Groq, página do modelo](https://console.groq.com/docs/model/openai/gpt-oss-20b) | Oficial. Entrada em cache 0,037 |
| `jev` (`jev-1.14.0`) | 0,042 | 0 | [TypeSafe, home](https://typesafe.ai) | Oficial para a entrada: "US$ 42 por bilhão de tokens de entrada" (US$ 0,042 por milhão é conversão). **O preço de saída não é publicado**: 0 vem da aula (Etapa 7) e de fontes de terceiros. A TypeSafe não tem página de preços (`/pricing` dá 404) nem limites publicados na documentação lida. Confirmar a saída em typesafe.ai/contact |

O Groq só atua como fallback do especialista. Para corrigir um preço sem alterar o código, use `OBS_PRICES_JSON`.

### Custo de um atendimento humano

`OBS_SUPPORT_COST_USD` = **8,01** por contato: pesquisa da Gartner com líderes de atendimento (2019), que mede o custo médio de canais atendidos por pessoas (telefone, chat ao vivo e e-mail) em [US$ 8,01](https://www.gartner.com/en/newsroom/press-releases/2019-09-25-gartner-says-only-9--of-customers-report-solving-thei), contra cerca de US$ 0,10 do autoatendimento. Não consegui abrir a página da Gartner diretamente; o valor vem do resumo e de cópias dela, então vale conferir. A própria Gartner publica depois uma [mediana de US$ 13,50](https://www.gartner.com/en/documents/5164231) por contato assistido. São valores de mercado, não dados da Delta nem do Brasil: se a equipe tiver o custo real de um atendimento, informe-o.

### Demais premissas

| Variável | Padrão | Fonte e observação |
| --- | --- | --- |
| `OBS_USD_TO_BRL` | 5,4212 | PTAX de venda do Banco Central em 30/10/2026, pela [API Olinda do BCB](https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/aplicacao#!/recursos/CotacaoDolarDia). Atualize na data da apresentação |
| `OBS_QUESTIONS_PER_USER_WEEK` | 0 (usar o medido) | **Não existe fonte externa confiável.** Sem valor definido, o relatório usa a taxa **medida** (perguntas por usuário ÷ semanas observadas), e só depois de 7 dias de dados; antes disso a projeção aparece como "n/d" |
| `OBS_LATENCY_P95_LIMIT_MS` | 15000 | Meta de SLO definida pela equipe, não é referência externa |
| `OBS_ERROR_RATE_LIMIT` | 0,05 | Meta de SLO definida pela equipe, não é referência externa |
| `OBS_PRICES_JSON` | tabela interna | Sobrescreve preços, ex. `{"gpt-6-luna": [0.10, 0.50]}` |

O **cenário base** da projeção usa o custo médio medido por requisição, e o **pessimista** usa o custo medido no **percentil 95** das requisições (antes era um fator de 1,5 sem fonte). Por isso o relatório só é confiável com muitas requisições: com poucas, a média e o p95 dependem de poucos pontos.

Limites: tokens vêm do que o provedor devolve ou do `count_tokens`; o custo real da fatura pode diferir (cache, lote, impostos).

## LangSmith (opcional)

1. Crie a chave em smith.langchain.com (Settings → API Keys).
2. No `.env` local (já ignorado pelo Git; lido por `app/config.py`) defina `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...` e `LANGSMITH_PROJECT=delta-ai`. Nunca coloque a chave em arquivos versionados.
3. Suba a API normalmente: os traces aparecem no projeto, agrupados por `session_id`.
4. `python -m scripts.langsmith_reconcile` compara tokens, custo e latência do LangSmith com o cálculo local.

Por padrão, `LANGSMITH_SEND_CONTENT=false` configura ocultação de inputs/outputs: prompts e respostas não devem ser enviados por essa integração. Com `true`, use somente dados de teste apropriados. Quando `APP_ENV=test` está no processo, `.env` é ignorado, mas variáveis `LANGSMITH_*` herdadas ainda podem ligar tracing.

## Validado e pendente

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

**Pendente**

- **Definição de resolução**: hoje conta como resolvida a resposta publicada sem erro e sem bloqueio do Juiz, o que inclui respostas do tipo "não consegui consultar a fonte". Na validação, a pergunta de consumo foi contada como resolvida mesmo sem ler os dados. A definição precisa exigir que as ferramentas tenham devolvido dados.
- **Projeção**: só aparece depois de 7 dias de dados medidos (ver premissas); com poucas requisições o relatório mostra "n/d".
- **Preço de saída do Jev** e limites de uso: a TypeSafe não publica; confirmar em typesafe.ai/contact.
- **Preço da Gartner**: a página original não pôde ser aberta; o valor vem do resumo e de cópias. Conferir.
- **Cabeçalho `X-Client`**: o app e a plataforma web ainda precisam enviá-lo para o custo por cliente deixar de aparecer como `unknown`.
- **Coleção no cluster real**: conferir se schema, índices e TTL de `observability_requests` foram aplicados no cluster do app; a presença de scripts não comprova aplicação.
- **Área administrativa**: ver a seção seguinte.
- **LangSmith em produção**: mantenha `LANGSMITH_SEND_CONTENT=false` para ocultar inputs/outputs. O envio explícito de conteúdo exige tratamento apropriado de dados pessoais e configuração do ambiente. Cada run leva `session_id` e `client` nos metadados, para filtrar por canal no próprio LangSmith.

## Área administrativa (planejada)

O painel de observabilidade existe só no console de testes da API de IA, que é desligado em produção. A decisão é levá-lo para um **perfil administrativo na plataforma web** (`delta-web-app`), que também terá o CRUD das tabelas do produto, como uma parte a mais do projeto. A tarefa está descrita no `TASK.md` da raiz do repositório web (arquivo local, ignorado pelo Git por convenção).

Dependências:

1. **Papel de administrador no JWT**, a combinar com quem emite o token no back-end.
2. **Endpoint administrativo de observabilidade** na API de IA, protegido por esse papel. A autenticação de chat/sessões já existe em `app/auth.py`, mas não há router administrativo de observabilidade registrado. Esse acesso precisa de autorização por papel, além da autenticação.
3. **Cabeçalho `X-Client`** enviado pelo app e pela web.
4. **Segredo `OBS_HASH_SECRET`** (16 caracteres ou mais) na API de IA, para contar usuários distintos.

O relatório só é confiável com muitas requisições medidas; por isso essa área é urgente.

## Rastreamento de uma requisição

O servidor gera `X-Request-ID`, coloca-o na resposta e mantém o contexto ao longo dos nós, modelos, ferramentas e fases do RAG. Não reutiliza ID arbitrário do cliente. Erros são representados de forma segura, preservando tipos, localização e cadeia de causas sem expor texto bruto de credenciais/SDKs.

`set_event_sink` permite integrar um consumidor de eventos; a existência desse ponto não configura armazenamento ou handlers de logs externos. `public_data` trata dados do diagnóstico e não deve ser considerado detecção universal de PII. O console pode exibir informações de teste e candidatas para inspeção; o contrato público de `/chat` é mais restrito.

## Registro e recuperação

São gravados modos de fluxo completo `chat` e `judge`, incluindo SSE quando a rota define o modo do trace. O registro de métricas não guarda pergunta, resposta ou `user_id` bruto. Ele reúne tempos, modelos, tokens, custo, revisões, resultado e canal.

A coleção é `observability_requests` no Mongo de app. Persistência ocorre em thread daemon; falha não altera a resposta. Há buffer de até 2000 registros em RAM e leitura de até 1000 registros de banco por padrão, mesclados por ID. Após falha do Mongo, novas tentativas ficam suspensas por 60 segundos. Reinício perde o buffer; não é fila durável.

A IA não garante aplicação de validador, índices ou TTL no cluster. A referência de schema/governança deve ser conferida no `delta-mongo-database`. A especificação anterior previa TTL de 90 dias e índices por request/canal/usuário; a aplicação desses scripts precisa ser verificada no cluster.

`X-Client: app` ou `web` identifica canal. Console usa `playground`; ausente/inválido vira `unknown`. `OBS_HASH_SECRET` com pelo menos 16 caracteres habilita HMAC do usuário; sem ele não há contagem confiável de usuários distintos. Não é o ID original nem deve ser usado como identificador público.

## Métricas e interpretação

- Latência total acompanha chegada até encerramento HTTP, incluindo streaming. Há p50/p95/p99 e tempos por nó/agente/fase RAG.
- Falhas 5xx, rejeições e resultados parciais são separados. Uma falha recuperada por fallback pode deixar o atendimento parcial.
- `resolved` significa resultado `success`, modo completo e ausência do nó de bloqueio do Juiz. **Não exige provar que uma ferramenta trouxe dados suficientes**; explicação de indisponibilidade sem erro registrado pode contar como resolução.
- Custo por resolução divide custo de IA pelas resoluções. ROI usa `(resoluções × custo de atendimento humano − custo IA) / custo IA`; não inclui infraestrutura, manutenção ou desenvolvimento.
- SLO padrão atual: **p95 até 15 segundos**, erro até 5%, configuráveis. Sem dados, não há avaliação.
- Tempos de nós podem se sobrepor pela preparação paralela. `overhead_ms` usa máximo entre zero e total menos soma de nós; não é decomposição rigorosa de tempo exclusivo.

## Código relacionado

- [app/observability/http.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/observability/http.py)
- [app/observability/metrics.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/observability/metrics.py)
- [app/observability/langsmith.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/observability/langsmith.py)
