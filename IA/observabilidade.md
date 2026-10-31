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

Só requisições de chat completo (`/chat` e as abas Chat e Juiz) são registradas. Cada registro fica na coleção `observability_requests` do MongoDB do app, sem pergunta nem resposta. Sem MongoDB, o painel usa os registros do processo atual; depois de uma falha de conexão o banco é ignorado por 60 s, para o painel não esperar o timeout a cada leitura.

### A coleção `observability_requests`

Ela é definida no repositório `delta-mongo-database` (schema com validador, índices e documentação em `collections/db_delta_app.md`), na branch `feat/colecao-observability-requests`. O papel `role_api_service` já tem permissão de escrita em `db_delta_app`. Os índices são:

- TTL de 90 dias em `created_at`, para a coleção não crescer sem limite;
- único em `request_id`;
- `client` + `created_at`, para o custo por canal;
- parcial em `user_hash` + `created_at`, para contar usuários distintos.

O `user_id` nunca é gravado. O campo `user_hash` é um HMAC do usuário com o segredo `OBS_HASH_SECRET` (16 caracteres ou mais), não reversível; sem o segredo, a contagem de usuários distintos fica indisponível.

### Cliente, usuários e custo por canal

O cliente é informado pelo cabeçalho **`X-Client`**, com os valores `app` ou `web`. Sem o cabeçalho (ou com outro valor) o registro fica como `unknown`, e o console de testes é sempre `playground`. O app e a plataforma web precisam enviar esse cabeçalho em toda chamada ao `/chat`. Com ele, o painel mostra o custo por cliente, qual cliente mais gasta, os usuários distintos e as perguntas por usuário (medidas, não mais um cenário).

### Embeddings e Jev no custo (sem estimativa)

- **Embeddings**: a resposta do `embed_content` do Google **não traz o uso** (testei: só `embeddings` e a resposta HTTP). Por isso o texto enviado é contado com o método oficial `count_tokens`, que aceita o modelo de embedding (medido: 12 tokens para 51 caracteres). Se a contagem falhar, a chamada é marcada como "sem contagem" e **o custo dela não é estimado**. Preços por 1 milhão de tokens de entrada: `gemini-embedding-001` US$ 0,15 e `gemini-embedding-2` US$ 0,20, na [página de preços do Gemini](https://ai.google.dev/gemini-api/docs/pricing) (leitura resumida, vale conferir). O custo aparece como o componente `embeddings`.
- **Jev** (Typesafe): a resposta da API traz `usage.input_tokens` e `usage.output_tokens`, que o `JudgeAgent` já lê, então o custo usa os tokens reais (medido: uma pergunta usou 15.961 tokens, US$ 0,00067). O preço de entrada é o da [home da TypeSafe](https://typesafe.ai) (US$ 42 por bilhão de tokens, ou US$ 0,042 por milhão); o de saída não é publicado e é tratado como 0, como diz a aula (Etapa 7).

## Definições

- **Tempo total**: da chegada da requisição ao fim da resposta. Latência por etapa vem dos eventos do grafo (guardrail, contexto, roteador, execução, síntese, Juiz, saída) e por agente das etapas de cada especialista. **Orquestração** = tempo total − soma das etapas.
- **Índice de erros** = requisições com falha (5xx ou etapa que quebrou) ÷ total. Bloqueios de guardrail e execuções parciais (ferramenta falhou, mas houve resposta) são contados à parte.
- **Resolução** = resposta publicada com sucesso, sem erro de agente e sem bloqueio do Juiz.
- **Custo por resolução** = custo de IA ÷ resoluções.
- **ROI** = (resoluções × custo de um atendimento − custo de IA) ÷ custo de IA. Acima de 0 há retorno. Só o custo de tokens entra no denominador; hospedagem, bancos, desenvolvimento e manutenção ficam de fora, então o ROI é um limite superior.
- **SLO**: p95 do tempo total ≤ 8 s e índice de erros ≤ 5%. Sem requisições, o SLO aparece como "sem dados".

## Indicadores da aba Monitor

- **Confiabilidade**: índice de erros, sucessos, parciais, falhas, bloqueios e chamadas ao modelo reserva (fallback).
- **Latência**: tempo total p50, p95 e p99, orquestração entre etapas, latência por etapa do grafo e por agente.
- **Custo**: custo total, por requisição e por componente, tokens de entrada e saída, tokens e chamadas ao modelo por requisição e taxa de revisão do Juiz.
- **Retorno**: taxa de resolução, custo por resolução, ROI e economia estimada.
- Gráficos: tempo por requisição com a linha do SLO, latência por etapa (p50 e p95), custo por componente e resultado das requisições. A projeção para 100 e 1000 usuários fica numa tabela. O estilo segue o console (paleta azul, fonte e painéis do projeto).

## Premissas e fontes

Todas as variáveis são lidas e validadas em `app/config.py` (`get_observability_config`), como as demais configurações; valor inválido ou negativo gera erro claro.

### Preço dos modelos (USD por 1 milhão de tokens, tarifa Standard)

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
| `OBS_LATENCY_P95_LIMIT_MS` | 8000 | Meta de SLO definida pela equipe, não é referência externa |
| `OBS_ERROR_RATE_LIMIT` | 0,05 | Meta de SLO definida pela equipe, não é referência externa |
| `OBS_PRICES_JSON` | tabela interna | Sobrescreve preços, ex. `{"gpt-6-luna": [0.10, 0.50]}` |

O **cenário base** da projeção usa o custo médio medido por requisição, e o **pessimista** usa o custo medido no **percentil 95** das requisições (antes era um fator de 1,5 sem fonte). Por isso o relatório só é confiável com muitas requisições: com poucas, a média e o p95 dependem de poucos pontos.

Limites: tokens vêm do que o provedor devolve ou do `count_tokens`; o custo real da fatura pode diferir (cache, lote, impostos).

## LangSmith (opcional)

1. Crie a chave em smith.langchain.com (Settings → API Keys).
2. No `.env` local (já ignorado pelo Git; lido por `app/config.py`) defina `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...` e `LANGSMITH_PROJECT=delta-ai`. Nunca coloque a chave em arquivos versionados.
3. Suba a API normalmente: os traces aparecem no projeto, agrupados por `session_id`.
4. `python -m scripts.langsmith_reconcile` compara tokens, custo e latência do LangSmith com o cálculo local.

Use só com dados de teste: prompts e respostas vão para um serviço externo. Em `APP_ENV=test` o `.env` é ignorado, mas variáveis `LANGSMITH_*` definidas no processo ainda ligam o envio.

## Validado e pendente

**Validado em 31/10/2026**

- Testes automatizados (`tests/test_observability.py`, repositório de IA): custo, tokens, percentis, erros, resolução, ROI, projeção, SLO sem dados, mesclagem de registros, fonte de cada preço, ausência de texto no registro e geração do PDF.
- Três chamadas reais de chat com Gemini (`LLM_PROVIDER=gemini`, perguntas de consumo, previsão e vazamento): tokens e custo foram capturados (23.075 tokens de entrada e 2.019 de saída, US$ 0,0045 no total, cerca de US$ 0,0015 por pergunta). As três terminaram como parciais e o p95 foi de 46,7 s, porque o MongoDB e o provedor falharam nesse ambiente.
- LangSmith: os traces chegaram ao projeto `delta-ai` e `scripts.langsmith_reconcile` os leu (4 runs raiz, 27.576 tokens, US$ 0,0085 pelo cálculo do LangSmith).
- Aba **Monitor** no navegador: cartões, gráficos e tabela de projeção renderizados com dados dessa chamada real.
- **`gpt-6-luna` com uso real** (provedor padrão, OpenAI Responses): três perguntas custaram US$ 0,0019 no total, cerca de US$ 0,0006 por pergunta, com 15.332 tokens de entrada, 724 de saída e 5 chamadas ao modelo por pergunta, sem fallback. O custo bate com a tabela de preços (0,10 / 0,50).
- **MongoDB local descartável** (`docker-compose.dev.yml`, porta 27018, base `delta_test_obs`, apagada ao final): a gravação em `observability_requests` e a leitura de volta funcionaram, e o registro não contém pergunta, resposta nem `user_id`.
- **PDF** no estilo do relatório de BI: gerado e conferido página a página como imagem.

**Pendente**

- **MongoDB Atlas e PostgreSQL reais**: o Atlas recusou a conexão (`SSL handshake failed`), provavelmente por IP não liberado na lista de acesso do cluster, e o PostgreSQL local não estava em execução. Por isso os agentes não leram dados reais e as três perguntas ficaram "parciais". A gravação no Atlas só foi validada num MongoDB local.
- **Resolução real**: sem acesso aos bancos, nenhuma pergunta terminou como resolvida; a taxa de resolução, o custo por resolução e o ROI só são significativos com os bancos acessíveis.
- **Preços do Groq e custo do Jev**: sem confirmação oficial (ver acima).
- **Endpoint administrativo**: o painel em produção deve ser um endpoint protegido por JWT com **papel de admin** (hoje a autenticação aceitaria qualquer usuário). Ele depende de `app/auth.py`, que ainda não está na `main` do repositório de IA, e de um claim de papel no token emitido pelo back-end; entra quando a autenticação for integrada. Até lá o painel existe só no console de testes.
- **Cabeçalho `X-Client`**: o app e a plataforma web ainda precisam enviá-lo para o custo por cliente deixar de aparecer como `unknown`.
- **Preço de saída do Jev** e limites de uso: a TypeSafe não publica; confirmar em typesafe.ai/contact.
- **LangSmith em produção**: ele envia prompts e respostas para fora. Em produção, deixe desligado ou use só com amostragem e depois do guardrail que mascara dados pessoais. Cada run leva `session_id` e `client` nos metadados, para filtrar por canal no próprio LangSmith.
