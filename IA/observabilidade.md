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
- **Jev** (Typesafe): a resposta da API traz `usage.input_tokens` e `usage.output_tokens`, que o `JudgeAgent` já lê, então o custo usa os tokens reais (medido: uma pergunta usou 15.961 tokens, US$ 0,00067). O preço é US$ 0,042 por milhão de tokens de entrada, com saída gratuita. **Esse preço vem de fontes secundárias** ([eesel.ai](https://www.eesel.ai/blog/typesafe-jev-pricing), e o roteiro da Etapa 7); não encontrei página oficial de preços da TypeSafe. Confirme com a TypeSafe ou no contrato antes de apresentar.

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
| `openai/gpt-oss-120b` | 0,15 | 0,60 | [Groq, pricing](https://groq.com/pricing) | **Não confirmada**: a página não exibe a tabela sem JavaScript. Valor de agregadores; o lançamento listava 0,15 / 0,75 |
| `openai/gpt-oss-20b` | 0,075 | 0,30 | [Groq, pricing](https://groq.com/pricing) | **Não confirmada**, mesmo caso |

O Groq só atua como fallback do especialista, então o impacto no custo total é pequeno. Para corrigir um preço sem alterar o código, use `OBS_PRICES_JSON`. O cenário pessimista da projeção multiplica o custo por 1,5. O custo do Jev e dos embeddings entra no total, com tokens contados (ver acima); o preço do Jev ainda não tem fonte oficial.

### Custo de um atendimento humano

`OBS_SUPPORT_COST_USD` = **6,0**, o extremo baixo da faixa de referência de mercado. Fontes, todas de blogs de fornecedores de atendimento (não são dados da Delta):

- [StealthAgents, benchmarks de custo por ticket 2026](https://stealthagents.com/research/customer-support-cost-per-ticket-benchmarks-2026): mediana de US$ 13,50 por contato nos EUA (atribuída ao Gartner) e faixa de US$ 6 a 12 conforme geografia e complexidade;
- [Lorikeet, custo por ticket](https://lorikeetcx.ai/articles/customer-service-cost-per-ticket): faixas por setor, de US$ 2,70 no varejo a US$ 60 em B2B;
- MetricNet, citado pelas mesmas fontes: US$ 15,56 por ticket em help desk de TI.

O valor para o Brasil provavelmente é menor. Se a equipe tiver o custo real de um atendimento, informe-o: ele muda o ROI na mesma proporção.

### Demais premissas

| Variável | Padrão | Observação |
| --- | --- | --- |
| `OBS_QUESTIONS_PER_USER_WEEK` | 5 | **Sem fonte.** É um cenário, não um dado. O ideal é medir: contar mensagens por usuário por semana nas sessões do MongoDB depois de algumas semanas de uso |
| `OBS_USD_TO_BRL` | 5,5 | Câmbio aproximado; atualize na data da apresentação |
| `OBS_LATENCY_P95_LIMIT_MS` | 8000 | Limite do p95 do tempo total no SLO |
| `OBS_ERROR_RATE_LIMIT` | 0.05 | Limite do índice de erros no SLO (entre 0 e 1) |
| `OBS_PRICES_JSON` | tabela interna | Sobrescreve preços, ex. `{"gpt-6-luna": [0.10, 0.50]}` |

Limites: tokens vêm do que o provedor devolve; o custo real da fatura pode diferir (cache, lote, impostos). Com dados mockados, os números mostram o funcionamento, não o uso real.

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
- **Preço do Jev**: US$ 0,042 por milhão de tokens vem de fontes secundárias; falta a confirmação oficial da TypeSafe.
- **LangSmith em produção**: ele envia prompts e respostas para fora. Em produção, deixe desligado ou use só com amostragem e depois do guardrail que mascara dados pessoais. Cada run leva `session_id` e `client` nos metadados, para filtrar por canal no próprio LangSmith.
