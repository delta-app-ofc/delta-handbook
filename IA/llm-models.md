# Provedores e modelos de linguagem

Esta aplicação seleciona provedores e lê os parâmetros de `Settings`. A configuração não é uma afirmação de qualidade comparativa: o projeto não possui benchmark próprio em português. As justificativas abaixo consideram o idioma dos prompts, a finalidade de cada papel e o suporte documentado a chamadas de ferramentas.

As fontes oficiais abaixo foram registradas na documentação em **4 de outubro de 2026**. Disponibilidade, modelos e limites podem mudar; verifique os links oficiais antes de alterar os identificadores.

## Modelos por papel no modo Gemini/Groq

As linhas abaixo descrevem `LLM_PROVIDER=gemini`. O modo padrão é `openai`, detalhado em seção própria.

| Papel | Provedor e identificador configurável | Uso no código | Ferramentas e justificativa | Amostragem |
| --- | --- | --- | --- | --- |
| Especialista principal | Google Gemini, `GEMINI_MODEL` (padrão `gemini-2.5-flash`) | Os especialistas usam `llm_especialista`, cujo primeiro provedor nesse modo é Gemini. | O modelo consta na documentação oficial e suporta function calling. Os prompts do projeto são em português e os agentes podem consultar ferramentas locais. Isso torna o modelo compatível com o fluxo; não há benchmark próprio que permita afirmar superioridade em português. A referência de disponibilidade registrada nessa consulta restringia o acesso a projetos/usuários com uso ativo; confira a disponibilidade da conta antes de configurar outro modelo compatível com ferramentas. | `temperature=0.3`; `top_p=0.95`. |
| Especialista alternativo | Groq, `GROQ_SPECIALIST_MODEL` (padrão `openai/gpt-oss-120b`) | Fallback de `llm_especialista`; também preservado como `llm_groq_especialista` para compatibilidade. | O catálogo oficial da Groq lista o identificador e documenta tool use. Ele mantém uma segunda opção de provedor para falhas transitórias do principal. Seu uso com prompts em português é uma escolha operacional, não uma garantia de qualidade medida pelo projeto. | `temperature=0.3`. |
| Modelo rápido | Groq, `GROQ_FAST_MODEL` (padrão `openai/gpt-oss-20b`) | Construído sob demanda em `llm_rapido`, usado por guarda de entrada, roteador, síntese, metadados e resumos nesse modo. | O catálogo da Groq lista o identificador e documenta tool use. O nome de configuração separa as chamadas rápidas dos especialistas; a escolha não garante qualidade ou latência para todo pedido. | `temperature=0.0`. |
| Embedding | Google, constante pública `EMBEDDING_MODEL_NAME` (`gemini-embedding-2-preview`) | Embedding configurado por `GEMINI_EMBEDDING_MODEL`, usado por RAG e memória longa. | A documentação oficial lista o identificador de embedding. O serviço implementa clientes de embedding, indexação e recuperação documental; a memória longa usa coleção separada. | Não se aplica. |

Os nomes públicos `llm_especialista`, `llm_gemini`, `llm_groq_especialista`, `llm_rapido` e `EMBEDDING_MODEL_NAME` são mantidos. `llm_especialista` é a interface usada pelos agentes especialistas. Os modelos de provedor individuais não incluem fallback.

## Parâmetros e configuração

| Setting | Padrão | Efeito |
| --- | ---: | --- |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Identificador do especialista principal. |
| `GROQ_SPECIALIST_MODEL` | `openai/gpt-oss-120b` | Identificador do fallback especialista. |
| `GROQ_FAST_MODEL` | `openai/gpt-oss-20b` | Identificador do modelo rápido no modo Gemini/Groq. |
| `LLM_FALLBACK_ENABLED` | `true` | Habilita a construção e validação do Groq especialista no papel especialista. Com `false`, esse papel não exige nem cria um cliente de fallback Groq. O modelo rápido exige Groq no modo Gemini; no modo padrão usa OpenAI. |
| `LLM_TIMEOUT_SECONDS` | `15` | Timeout finito aplicado a cada tentativa individual nos dois provedores. |
| `LLM_MAX_RETRIES` | `1` | Número de retries além da tentativa inicial em cada provedor. Deve ser inteiro não negativo. |
| `LLM_MAX_OUTPUT_TOKENS` | `4096` | Limite de saída configurado pela aplicação; não é o máximo anunciado pelos provedores. |

As chaves generativas são `OPENAI_API_KEY`, `GEMINI_API_KEY` e `GROQ_API_KEY`, conforme o caminho selecionado. A construção é lazy: importar `app.services.llms` não cria clientes, não valida chaves e não faz chamadas de rede. A primeira leitura de cada nome público valida os settings do caminho solicitado e então cria o cliente em cache. Após recarregar settings em testes ou desenvolvimento, `clear_llm_cache()` descarta os modelos já construídos.

Os modelos descritos na consulta original anunciavam até 65.536 tokens de saída, acima do limite padrão mais conservador de 4.096 usado pela aplicação. Os limites publicados estão sujeitos a mudanças e não substituem os limites aplicados pela conta ou endpoint.

## Chamadas de ferramentas e fallback

O runtime chama `bind_tools(tools)` e, em cada turno, `invoke(messages)`. A integração `RunnableWithFallbacks` disponível na versão instalada do `langchain-core` não expõe `bind_tools`; por isso, `llm_especialista` usa um adaptador pequeno que vincula a mesma lista de ferramentas ao provedor principal selecionado e ao Groq. Em uma falha transitória, o fallback recebe a mesma lista de mensagens daquele turno, incluindo `AIMessage` e `ToolMessage` anteriores.

O adaptador troca de provedor apenas para falhas de transporte/timeout, HTTP 408 ou 429, e indisponibilidade HTTP 5xx reconhecidas pelas integrações dos SDKs. A integração Gemini transforma `google.genai.errors.ClientError` em `ChatGoogleGenerativeAIError`; o adaptador só classifica esse wrapper quando seu `__cause__` é um erro protocolar Google (`APIError`/`ClientError`) e usa o código HTTP dessa causa. Wrapper sem uma causa reconhecida propaga sem fallback nem conversão, para não esconder erros de conversão ou programação. Respostas rejeitadas (por exemplo, HTTP 400, 401 ou 403) viram `LLMProviderError` com uma mensagem pública sem corpo da resposta ou texto do SDK. Se ambos os provedores falharem de forma transitória, a aplicação levanta `LLMUnavailableError` com mensagem genérica. Erros de programação como `TypeError`, `ValueError` e `KeyError` não são convertidos em fallback.

O fallback cobre somente uma chamada do modelo. Se o runtime já recebeu uma chamada de ferramenta, executou-a e recebeu uma falha do modelo no turno seguinte, o fallback recebe o `ToolMessage` daquele resultado. A execução anterior da ferramenta não é repetida pelo adaptador. Ferramentas continuam sendo executadas pela aplicação, não pela API do provedor.

`LLM_MAX_RETRIES=R` limita cada provedor a no máximo `R + 1` requisições por invocação: a integração Gemini recebe `R + 1` como total de tentativas, enquanto OpenAI e Groq recebem `R` como retries além da tentativa inicial. Com fallback habilitado, o pior caso para uma invocação do papel especialista é `2 × (R + 1)` requisições, somando as tentativas do provedor principal e do Groq. Com o padrão atual (`R=1`), são no máximo quatro requisições ao todo. O timeout vale por tentativa; intervalos internos de retry também podem aumentar o tempo total do turno.

## Fontes oficiais

- Google, [lista de modelos Gemini](https://ai.google.dev/gemini-api/docs/models?hl=en) e [ficha do Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash?hl=en): identificador, disponibilidade atual documentada, function calling e limites publicados.
- Google, [function calling](https://ai.google.dev/gemini-api/docs/generate-content/function-calling?hl=en): fluxo de chamada e retorno de ferramentas.
- Integração LangChain, [ChatGoogleGenerativeAI](https://reference.langchain.com/python/langchain-google-genai/chat_models/ChatGoogleGenerativeAI): interface Python e parâmetros da integração.
- Groq, [GPT-OSS 120B](https://console.groq.com/docs/model/openai/gpt-oss-120b), [GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b) e [tool use local](https://console.groq.com/docs/tool-use/local-tool-calling): IDs do catálogo, uso de ferramentas e execução local pela aplicação.
- Integração LangChain, [ChatGroq](https://reference.langchain.com/python/langchain-groq/chat_models/ChatGroq) e [bind_tools](https://reference.langchain.com/python/langchain-groq/chat_models/ChatGroq/bind_tools): interface e suporte da integração a ferramentas.
- SDKs oficiais, [Groq Python](https://github.com/groq/groq-python) e [Google Gen AI Python](https://github.com/googleapis/python-genai): categorias de erros, timeout e semântica de retries considerados na configuração.
- LangChain Core, [with_fallbacks](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/with_fallbacks): abstração genérica de fallback que motivou o adaptador de `bind_tools`.

### Escopo da validação

Os testes isolados usam clientes substituídos e não gastam créditos. A validação original descrita aqui não executou smoke test real contra Gemini ou Groq, por falta de credenciais naquele ambiente. Os testes verificam o contrato `bind_tools` → `invoke`, os erros transitórios e permanentes, a passagem do histórico com `ToolMessage` e que o efeito da ferramenta ocorre uma única vez.

## Modo padrão: `LLM_PROVIDER=openai`

| Papel | Modelo configurado | Raciocínio default | Consumidores |
| --- | --- | --- | --- |
| Especialista | `OPENAI_MODEL=gpt-6-luna` | `OPENAI_SPECIALIST_REASONING_EFFORT=high` | Consumo, previsão, vazamento, hábitos e RAG via `llm_especialista`. |
| Rápido | Mesmo `OPENAI_MODEL` | `OPENAI_FAST_REASONING_EFFORT=low` | Guarda de entrada, roteador, síntese, título/prévia e resumo de sessão. |
| Segundo juiz | Mesmo `OPENAI_MODEL` | `OPENAI_REASONING_EFFORT=medium` | Parecer estruturado quando o Jev tem baixa confiança. |
| Embeddings | `GEMINI_EMBEDDING_MODEL=gemini-embedding-2-preview` | Não se aplica | RAG e memória longa, 3072 dimensões. |
| Juiz inicial | `JEV_MODEL=jev-1.14.0` | Não se aplica | Choice e Noul via TypeSafe. |

Os modelos OpenAI usam Responses pela integração `ChatOpenAI`, `output_version=responses/v1`, `store=False` e inclusão de `reasoning.encrypted_content`. O runtime extrai texto dos blocos de resposta com `_message_text`.

Vazio nos overrides de raciocínio rápido/especialista usa o valor geral. Clientes são compartilhados por snapshot de settings e nível de raciocínio; o cache não reutiliza respostas ou evidências entre perguntas.

## Cache e encerramento

A criação é lazy. O `lifespan` aguarda `close_openai_clients`, `close_judge_clients` e `close_rag_clients`, além de fechar o pool SQL. `clear_llm_cache` descarta referências dos papéis gerais, sem substituir o encerramento de transportes abertos. Reiniciar o processo é a forma operacional simples de aplicar uma mudança de configuração.

Os clientes de memória longa têm caches separados; seu ciclo de vida não é o mesmo dos clientes RAG. Consulte [settings](settings.md) e [memória](implementacao-memoria-sessoes.md).

## Código relacionado

- [app/services/llms.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/services/llms.py)
- [app/agents/judge_specialist.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/agents/judge_specialist.py)
