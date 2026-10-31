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

Só requisições de chat completo (`/chat` e as abas Chat e Juiz) são registradas. Cada registro fica na coleção `observability_requests` do MongoDB do app, sem pergunta, resposta ou `user_id`. Sem MongoDB, o painel usa os registros do processo atual; depois de uma falha de conexão o banco é ignorado por 60 s, para o painel não esperar o timeout a cada leitura.

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

O Groq só atua como fallback do especialista, então o impacto no custo total é pequeno. Para corrigir um preço sem alterar o código, use `OBS_PRICES_JSON`. O cenário pessimista da projeção multiplica o custo por 1,5. O custo do Jev (Typesafe) e dos embeddings não entra no cálculo: não encontrei tabela pública do Jev, então o custo total fica subestimado nessa parte.

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
| `OBS_JEV_COST_USD` | 0 | Custo do Jev por avaliação; ele não passa pelo LangChain, então é informado à mão |
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

**Pendente**

- **MongoDB real**: a conexão com o Atlas falhou com `SSL handshake failed` neste ambiente, provavelmente por IP não liberado na lista de acesso do cluster. A gravação em `observability_requests` e a leitura de volta não foram validadas.
- **`gpt-6-luna` com uso real**: o `.env` não tem `OPENAI_API_KEY`, então o custo real do provedor padrão não foi medido; só o preço foi conferido na página oficial.
- **Resolução real**: a chamada de teste teve falhas de banco e de modelo, então ficou sem resolução; a taxa só é significativa com dados e provedores funcionando.
- **Preços do Groq e custo do Jev**: sem confirmação oficial (ver acima).
- **Endpoints com Bearer** (`/observability/*`): dependem de `app/auth.py`, que ainda não está na `main` do repositório de IA; entram quando a autenticação for integrada.
