# Provedores e modelos por papel

## Objetivo e referência

Registrar a seleção feita pelo código de `app/services/llms.py`, `app/agents/judge_specialist.py` e `app/config.py` na `main` `f6f3d8c` (02/11/2026). Os IDs abaixo são defaults do repositório: não são recomendação de compra, comparação de qualidade ou confirmação de catálogo/acesso da conta.

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

## Modo alternativo: `LLM_PROVIDER=gemini`

`llm_especialista` usa `GEMINI_MODEL=gemini-2.5-flash` (`temperature=0.3`, `top_p=0.95`). O papel rápido usa `GROQ_FAST_MODEL=openai/gpt-oss-20b` (`temperature=0.0`). O segundo juiz usa `JUDGE_SPECIALIST_MODEL=gemini-2.5-flash` (`temperature=0.0`). Embeddings e Jev mantêm seus papéis.

O fallback especialista usa `GROQ_SPECIALIST_MODEL=openai/gpt-oss-120b`; o adaptador preserva `bind_tools` nos dois provedores. `llm_gemini` é o cliente de provedor individual, não o adaptador com fallback.

## Falhas, retries e histórico de ferramentas

`LLM_FALLBACK_ENABLED=true` permite fallback do especialista para Groq; no modo OpenAI também depende de chave Groq configurada. O papel rápido não recebe esse mesmo adaptador.

Fallback cobre falhas transitórias reconhecidas de transporte, timeout, HTTP 408/429 e 5xx. Erros permanentes reconhecidos recebem mensagem pública segura; erros de programação não devem virar troca silenciosa de provedor.

O fallback recebe o histórico do turno, incluindo resultados de ferramentas executadas. O adaptador não executa novamente uma ferramenta já concluída; uma nova decisão do modelo ou uma revisão do grafo é outro caminho de execução.

`LLM_TIMEOUT_SECONDS=15` vale por tentativa; `LLM_MAX_RETRIES=1` admite retries além da inicial. O cliente Gemini recebe `R+1` como total de tentativas; OpenAI/Groq recebem `R` retries. `LLM_MAX_OUTPUT_TOKENS=4096` limita saída. Nenhum desses valores é um timeout total de toda a pergunta.

## Cache e encerramento

A criação é lazy. O `lifespan` aguarda `close_openai_clients`, `close_judge_clients` e `close_rag_clients`, além de fechar o pool SQL. `clear_llm_cache` descarta referências dos papéis gerais, sem substituir o encerramento de transportes abertos. Reiniciar o processo é a forma operacional simples de aplicar uma mudança de configuração.

Os clientes de memória longa têm caches separados; seu ciclo de vida não é o mesmo dos clientes RAG. Consulte [settings](settings.md) e [memória](implementacao-memoria-sessoes.md).

## Verificação

Testes de raciocínio, runtime e especialistas usam substitutos em cenários controlados. Eles não comprovam disponibilidade dos IDs na conta, limites de uso nem qualidade em português. A revisão não consultou catálogos externos nem executou chamadas pagas; o objetivo é documentar a seleção existente.

## Fontes da implementação revisada

- [app/services/llms.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/services/llms.py)
- [app/agents/judge_specialist.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/f6f3d8c/app/agents/judge_specialist.py)
