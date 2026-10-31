# Redução de latência do chat

> **Estado:** implementado e testado na branch `feat/reduz-latencia-chat` do `delta-artificial-intelligence`
> (feita em cima da `feat/observabilidade`, para medir pelos registros dela),
> **ainda não mesclado na `main`**. Os caminhos de arquivo citados abaixo (como `app/data/db_postgres.py`) são desse
> repositório. Até o merge, os documentos [Conexão PostgreSQL](postgres-connection.md) e
> [Settings](settings.md) continuam descrevendo o comportamento anterior.

## Objetivo

Diminuir o tempo de resposta do `POST /chat` e a espera percebida pela pessoa usuária, sem mexer no Agente Juiz,
nos modelos de linguagem, no prompt do agente de consumo nem no `/playground`. Este documento registra **o que foi
feito, por quê, como configurar, o que foi medido e o que ficou de fora**.

## Contexto

Em uma rodada manual com Gemini real, contra bancos locais, o chat levou 1-3 s numa saudação, 4-20 s numa pergunta
com um agente e, em alguns casos, de 37 a 157 s. A leitura do código mostrou estes gargalos que não dependem de
modelo nem de Juiz:

| Gargalo | Onde estava |
| --- | --- |
| Cada operação no PostgreSQL abria uma conexão nova (conectar, autenticar, consultar, fechar) | `app/data/db_postgres.py` |
| A lista de unidades da organização era lida de novo a cada tool; o mesmo resumo de consumo chegava a ser pedido 3-4 vezes | `app/tools/consumption/tools.py`, `app/tools/forecast/tools.py` |
| O classificador de segurança da entrada (uma chamada de LLM) rodava antes de contexto e roteador, em série | `app/graph/workflow.py`, `app/guardrails/input.py` |
| O histórico da sessão era lido duas vezes no MongoDB por pergunta | `app/graph/workflow.py`, `app/graph/context.py` |
| O `/chat` só responde ao final: a pessoa não vê andamento | `app/routes/chat.py` |

## Situação (o que é implementado, medido e pendente)

| Item | Implementado | Testado | Medido |
| --- | --- | --- | --- |
| Pool de conexões PostgreSQL | sim | testes unitários, concorrência e PostgreSQL real (só leitura) | sim: 34,1 → 5,4 ms por operação (local); no chat, tempo fora do modelo caiu de 0,09-0,42 s para 0,04-0,22 s |
| Memória de consumo por pergunta | sim | testes unitários | não (reduz idas ao banco; ganho depende do banco) |
| Guarda em paralelo com contexto e roteador | sim | testes unitários e de grafo com modelos falsos | sim, antes e depois pela observabilidade: fase inicial de 2,6-3,5 s para 1,4-1,7 s |
| Histórico lido uma vez | sim | testes unitários | não |
| Nível de raciocínio por papel (`OPENAI_FAST_REASONING_EFFORT` e `OPENAI_SPECIALIST_REASONING_EFFORT`) | sim, **ligado por padrão** (chamadas rápidas em `low`, especialistas em `high`) | testes de configuração e de escolha do modelo | `low` nas chamadas rápidas: sem ganho relevante em `gpt-6-luna`; `high` nos especialistas: **não medido** |
| `POST /chat/stream` (SSE), com plano e progresso por tool | sim | testes de rota, de gerador e do grafo real; servidor real | sim: os rótulos não somam tempo; o primeiro chega em 0,3-0,4 s |
| Tools em lote / em paralelo | **não** (avaliado e descartado) | — | sim, perfil de voltas do agente: ver "Tools em paralelo e tool em lote" |

**Houve uma rodada pontual com a IA real** (`gpt-6-luna`), a pedido, descrita em "Medição com a IA real". Ela é
pequena (uma execução por pergunta) e com bancos locais. A medição contínua de latência, tokens e custo deve ser feita
pelos painéis de observabilidade da equipe depois que esta mudança for aplicada (veja "Como medir antes e depois").

## 1. Pool de conexões PostgreSQL

**Motivo.** Abrir uma conexão por operação custa de dezenas de milissegundos (TCP, autenticação, às vezes TLS) em
toda consulta; uma previsão organizacional fazia de 5 a 7 conexões.

**O que mudou** (`app/data/db_postgres.py`):

- `_cursor()` mantém a mesma assinatura e passa a **emprestar** uma conexão de um `ThreadedConnectionPool`
  (`psycopg2.pool`, sem dependência nova), criado no primeiro uso. As funções do módulo e os testes que
  substituem `_cursor` não mudam.
- A cada uso, o `statement_timeout` continua sendo aplicado com `set_config(..., true)`, que só vale dentro da
  transação e **não vaza** para o próximo uso da mesma conexão.
- Ao terminar, a conexão volta ao pool. Se a operação falhou, o `putconn` do psycopg2 desfaz a transação aberta.
  Conexão **fechada ou quebrada** é descartada; um erro de consulta com a conexão saudável (inclusive o timeout
  de consulta) **não** descarta a conexão.
- Se a conexão emprestada estiver quebrada antes do SQL, ela é trocada **uma vez** e a operação segue. A nova
  tentativa só acontece antes de rodar o SQL da operação, então nunca repete uma escrita.
- Quando o pool está cheio, a chamada espera até `DB_POOL_WAIT_SECONDS` e então responde com o mesmo
  `DatabaseConnectionError("PostgreSQL")` público de sempre.
- `close_pool()` fecha tudo e pode ser chamado mais de uma vez. É chamado no `lifespan` de `app/main.py`.
- **Detalhe importante do psycopg2:** o pool só guarda `minconn` conexões ociosas e fecha as demais ao devolvê-las.
  Com `minconn=1`, sob concorrência as conexões extras eram recriadas a cada uso (nosso teste achou isso: com 8
  threads o pool ficou *mais lento* que não usar pool). Por isso, depois de abrir as conexões iniciais, o código sobe
  `minconn` para o máximo e as conexões ociosas passam a ser mantidas.

**Configuração** (variáveis de ambiente; `.env.example`):

| Variável | Padrão | Significado |
| --- | --- | --- |
| `DB_POOL_MIN_SIZE` | 1 | Conexões abertas ao criar o pool |
| `DB_POOL_MAX_SIZE` | 10 | Máximo de conexões ao mesmo tempo, por processo |
| `DB_POOL_WAIT_SECONDS` | 5 | Quanto esperar por uma conexão livre antes de falhar |

Regra de tamanho: **`workers do Uvicorn × DB_POOL_MAX_SIZE` deve ficar abaixo do `max_connections` do PostgreSQL**
(padrão 100). O `Dockerfile` usa 1 worker, então hoje são no máximo 10 conexões.

**Medição local** (`python -m scripts.bench_pool`, 300 `SELECT 1`, PostgreSQL 16 em Docker na mesma máquina; só
leitura):

| Cenário | Uma conexão por operação | Com pool |
| --- | --- | --- |
| Sequencial, média por operação | 34,1 ms | 5,4 ms |
| 8 threads, total de 300 operações | 1367 ms | 406 ms |

Em banco remoto (a distância aumenta o custo de cada conexão) o ganho tende a ser maior. **Não** foi medido contra o
banco real da equipe.

**Riscos e limites.** (1) Alterar settings em um processo em execução exige `close_pool()` (veja a lista de
recarga no README). (2) Com `pgbouncer` em modo transação, mantenha o `set_config` local (já é o caso). (3) Um pool
cheio por muito tempo vira erro público; ajuste `DB_POOL_MAX_SIZE`.

**Como reverter.** Voltar `_cursor()` ao `get_conn()` direto (a função continua no arquivo) ou definir
`DB_POOL_MAX_SIZE=1`.

## 2. Memória de consumo por pergunta

**Motivo.** Dentro de uma pergunta, o modelo costuma chamar `get_consumption_summary` várias vezes e cada chamada
relia as unidades e o consumo do banco.

**O que mudou.** O conjunto de tools é criado a cada execução do agente (`build_tools`); dentro dele agora existe uma
memória que:

- guarda a **lista de unidades** (`get_user_organization_properties`) na primeira leitura;
- guarda cada **leitura de consumo por período** (chave: tipo de escopo, unidades, período e horário de referência).

Ao terminar a pergunta, o conjunto de tools é descartado e a memória some com ele. **Não é cache entre perguntas nem
entre usuários.** Leituras com unidade, período ou horário de referência diferentes continuam indo ao banco. Erro do
banco não fica guardado. A autorização continua no banco (`fn_user_authorized_property_ids`); o texto do prompt de
consumo **não foi alterado**. Também vale para a previsão (`forecast/tools.py`), só para a lista de unidades.

**Como reverter.** Trocar `_units()` e `_read()` pelas chamadas diretas que eles envolvem.

## 3. Guarda de entrada em paralelo e histórico lido uma vez

**Motivo.** O classificador de segurança é uma chamada de LLM e rodava antes de tudo; o roteador (outra chamada)
só começava depois dele.

**O que mudou** (`app/guardrails/input.py`, `app/graph/workflow.py`, `app/graph/context.py`):

- `validate_input` foi dividida em `validate_input_rules` (tamanho, PII, injeção, dados internos; instantânea) e
  `classify_input` (LLM). `validate_input` continua existindo e compõe as duas, então o `/playground` e os testes
  antigos não mudam.
- No grafo, depois das regras, um único nó `prepare` roda **ao mesmo tempo** o classificador (`guardrail_llm`) e o
  par `context` → `route`. **Nada executa antes do veredito**: se o classificador bloquear, o resultado do roteador é
  descartado e o grafo termina.
- Por que um nó só e não ramos do LangGraph: o LangGraph executa em passos com barreira, então `route` só
  começaria depois que o classificador terminasse e não haveria ganho. Dentro de `prepare`, cada ramo usa uma cópia
  do contexto da requisição (`contextvars.copy_context()`), e os eventos `graph.node.*` de `guardrail_llm`,
  `context` e `route` continuam sendo emitidos como antes (o nó `prepare` em si não emite eventos).
- Se o classificador falhar, a regra anterior vale: a mensagem **não** é bloqueada e o erro vai ao diagnóstico.
- O perfil da conta (PostgreSQL) e o histórico/memória (MongoDB, Qdrant) são lidos juntos no nó de contexto.
- O histórico validado é lido **uma vez** em `_start_run` e reaproveitado pelo contexto (`_history` no estado).
  Se a leitura inicial falhar, o contexto tenta de novo e registra o erro, como antes.

**Ganho medido** (`gpt-6-luna`, 4 repetições após aquecimento): guarda 1,4 s e roteador 1,1 s; os dois em série
levavam **2,5 s** e em paralelo **1,4 s**, ou seja, cerca de 1 s a menos por pergunta. Quando a guarda bloqueia, uma
chamada do roteador pode ter sido gasta à toa (aceito).

**Como reverter.** Religar `guardrail_input → context → route` em série e chamar `validate_input` no nó de entrada.

## 4. Nível de raciocínio por papel (configuração)

Decisão da equipe: as chamadas **leves** usam raciocínio baixo e os **agentes especialistas** usam raciocínio alto.
Vale quando `LLM_PROVIDER=openai`.

| Papel | Variável | Padrão | O que usa |
| --- | --- | --- | --- |
| Chamadas rápidas | `OPENAI_FAST_REASONING_EFFORT` | `low` | guarda de entrada, roteador, síntese e título da sessão |
| Agentes especialistas | `OPENAI_SPECIALIST_REASONING_EFFORT` | `high` | consumo, previsão, vazamento e hábitos |
| Demais usos (por exemplo, o Juiz) | `OPENAI_REASONING_EFFORT` | `medium` | **não foi alterado** |

Os valores aceitos são `none`, `low`, `medium`, `high`, `xhigh` e `max`. Deixar uma das duas primeiras variáveis vazia
faz o papel voltar a usar o `OPENAI_REASONING_EFFORT`. O Agente Juiz, o Jev, os modelos e os prompts não foram alterados.

**O que se sabe pela medição** (`gpt-6-luna`, 4 repetições): com `low` a guarda levou 1,13 s e o roteador 1,34 s; com
`medium`, 1,38 s e 1,11 s. **Sem diferença além do ruído**: `low` nas chamadas rápidas não reduz a latência de forma
mensurável, embora também não prejudique o roteamento nos testes feitos.

**O que não se mediu:** o efeito de `high` nos especialistas. O agente especialista já é de 55% a 70% do tempo da
pergunta (as voltas do modelo e a redação da resposta); raciocínio mais alto tende a **aumentar o tempo e o custo**
dessa parte. Meça antes e depois nos painéis de observabilidade (tempo do agente, tokens e custo por pergunta) e, se o
custo ou o tempo não compensarem, volte para `medium` pela variável, sem mudar código.

## 5. Etapas por SSE: `POST /chat/stream`

**Motivo.** O `/chat` pode levar dezenas de segundos sem dar sinal. Isso reduz a espera **percebida**, não o tempo total.

**Contrato.** Mesmo JWT e mesmo corpo do `/chat` (`message`, `session_id` opcional). JWT, dono da sessão e
disponibilidade do histórico são checados **antes** de abrir o fluxo, com os mesmos códigos do `/chat` (401, 404
idêntico para sessão alheia ou inexistente, 503). Depois de aberto, o status é sempre 200 e as falhas vêm como evento.

| Evento | Conteúdo |
| --- | --- |
| `stage` | `{"stage": "checking\|understanding\|planning\|working\|composing\|validating\|revising\|finishing", "label": "texto em português"}`. Só indica a etapa: **não carrega dados da conta, da pergunta ou da resposta** |
| `result` | O mesmo JSON do `/chat`, enviado **uma única vez, depois da validação** (Juiz e guardrail de saída) |
| `error` | `{"status": 422, "detail": "..."}` se a mensagem foi bloqueada; `{"status": 500, "detail": "...", "request_id": "..."}` se o processamento falhou |
| `: keep-alive` | Comentário SSE a cada 15 s sem evento, para proxies não derrubarem a conexão |

**Plano e progresso por consulta.** Depois que o roteador escolhe os agentes, sai um `planning` com a frase do que
será consultado (por exemplo, "Vou consultar o seu consumo e a previsão de consumo"; para conta comercial, "o consumo
das suas unidades"). Durante a execução, cada agente e cada tool emitem um `working` ("Consultando o consumo das suas
unidades", "Lendo o consumo registrado", "Calculando a previsão"). Rótulos iguais em sequência aparecem uma vez só
(se o modelo pedir o mesmo resumo 3 vezes, a linha não se repete). Os textos ficam em
`app/observability/progress.py`, são **fixos por nome de agente e de tool**, e nada escolhido pelo modelo (período,
nome de unidade, parâmetros) entra no rótulo, porque ainda não passou pela validação do Juiz. Tool sem rótulo
cadastrado não gera evento. O custo é praticamente nulo: sem chamada extra de LLM, só um item na fila por evento.

**A resposta nunca é enviada aos poucos.** Ela só sai depois de julgada, então não há risco de mostrar texto não
validado. Uma sessão criada para uma mensagem bloqueada ou que falhou é removida, como no `/chat`.

**Implementação** (`run_workflow_events` em `app/graph/workflow.py`): o grafo roda numa thread própria
(`workflow.stream`, modos `updates` e `values`) dentro do contexto de rastreamento da requisição; os eventos voltam
por uma fila e o endpoint os lê. O `RequestTracingMiddleware` é ASGI puro, compatível com streaming. O checkpoint do
grafo é apagado ao final, como no `/chat`.

**Para o app.** Leia com `fetch` e `ReadableStream` (o `EventSource` do navegador não envia `Authorization`). Se
houver proxy reverso, mantenha `X-Accel-Buffering: no` (já enviado) e desative buffer de resposta.

Verificado com o servidor real (`uvicorn`) e `curl -N`: cinco eventos `stage`, depois `result`; 401 sem token e 404 em
sessão inexistente.

## Medição com a IA real (gpt-6-luna)

Rodada pontual, feita a pedido, com a IA completa (guarda, roteador, agente, Juiz) e `POST /chat/stream`. **Limites:**
uma execução por pergunta (o provedor varia de uma chamada para outra), PostgreSQL e MongoDB **locais e descartáveis**
(sem rede de banco remoto), conta residencial sem telemetria no MongoDB, raciocínio padrão (`medium`). Serve para
entender onde o tempo vai, não como benchmark.

**Tempo total até o `result`:**

| Pergunta | Tempo | Etapas principais |
| --- | --- | --- |
| Hábitos (residencial) | 8,1 s | plano em 2,6 s; agente 4,5 s; Juiz 1,0 s |
| Previsão (residencial) | 8,7 s | plano em 1,7 s; agente 6,3 s; Juiz 0,6 s |
| Qual unidade consumiu mais (comercial) | 12,0 s | plano em 2,2 s; agente 8,0 s (listar unidades, ler consumo, redigir); Juiz 1,6 s |

**Onde o tempo vai:** o agente especialista (as voltas do modelo com tools e a redação da resposta) é de 55% a 70% do
total; guarda + roteador somam cerca de 1,4 s (em paralelo); o Juiz leva de 0,4 a 1,6 s. Em outra repetição com
`OPENAI_FAST_REASONING_EFFORT=low`, o Juiz de uma pergunta levou 6,3 s: uma variação do provedor, sem relação com `low`.
Banco, regras e LangGraph juntos levam de 0 a 10 ms.

**Os rótulos não adicionam tempo.** O fluxo de etapas só reporta o que já acontece: cada rótulo é um item na fila
(microssegundos) emitido durante a espera. O `/chat/stream` e o `/chat` fazem o mesmo trabalho e têm a mesma duração
total; o que muda é que a pessoa vê "Vou consultar o consumo das suas unidades" depois de cerca de 2 s em vez de
uma tela parada por 8 a 12 s. O primeiro rótulo ("Verificando a mensagem") chega em 0,3-0,4 s.

**Cuidado ao medir no Windows:** o cliente que usa `localhost` perde cerca de 2,4 s por conexão nova (tenta IPv6 antes
de IPv4). Uma medição minha inicial mostrou 24,6 s para a pergunta comercial, sendo cerca de 3 s desse atraso do
cliente e o resto variação do provedor; com `127.0.0.1` a mesma pergunta levou 12,0 s. Meça com `127.0.0.1`.

**Conclusão:** a IA completa leva de 8 a 12 s nestas perguntas, e o ganho que ainda existe está no agente especialista
(modelo, número de voltas e tamanho da resposta) e na espera, não em banco nem em rótulos. O que isso significa para tools em lote
e em paralelo está em "Tools em paralelo e tool em lote".

## Antes e depois pela observabilidade (A/B)

Para saber se as mudanças diminuem mesmo a latência, as duas versões rodaram lado a lado com a IA real
(`gpt-6-luna`) e foram comparadas **pelos registros que a própria observabilidade grava** (`observability_requests`:
tempo total, tempo por nó, tempo por agente, chamadas de modelo, tokens e custo):

- **A (antes):** a `feat/observabilidade` sozinha.
- **B (depois):** a mesma branch com as melhorias deste documento.
- Quatro perguntas (hábitos, previsão, "qual unidade consumiu mais", "compare as unidades"), `POST /chat`, bancos locais
  descartáveis. Duas baterias: a primeira (3 repetições) chamava sempre a A antes da B; como o cache de prefixo do
  provedor poderia favorecer a segunda chamada, a segunda bateria (**4 repetições, 16 pares**) **alternou a ordem** a
  cada repetição e fez um aquecimento por versão. Os números abaixo são da segunda.

| Mediana, 16 requisições por versão | A (antes) | B (depois) | Variação |
| --- | --- | --- | --- |
| Tempo total no servidor | 11,5 s | 8,7 s | -25% |
| Chamadas de modelo por pergunta | 5 | 5 | 0% |
| Tokens por pergunta (entrada + saída) | 10.106 | 10.083 | 0% |
| Custo por pergunta | US$ 0,00154 | US$ 0,00148 | -4% (ruído) |

B foi mais rápida em **12 dos 16 pares** (diferença mediana de 2,7 s). Não houve viés de ordem a favor da B: quando a B
rodou primeiro a vantagem foi maior (-3,2 s) do que quando rodou depois (-1,8 s).

**De onde vem o ganho** (medianas por pergunta):

| Parte | A | B | Ganho |
| --- | --- | --- | --- |
| Fase inicial (guarda + contexto + roteador) | 2,6 a 3,5 s | 1,4 a 1,7 s | cerca de **1,0 a 2,1 s**, de forma consistente |
| Tempo fora do modelo no agente (tools e banco) | 0,09 a 0,42 s | 0,04 a 0,22 s | 0,05 a 0,30 s (pool e memória por pergunta; o banco é local) |
| Tempo do próprio modelo no agente | varia | varia | sem mudança de código: **ruído do provedor** |

Parte da diferença total (cerca de 1,3 s) está no tempo do modelo, que mudou entre as versões **sem mudança de código**
nessa parte; ela **não** deve ser creditada a estas melhorias. O ganho que se explica por mecanismo é de cerca de
**1,3 a 1,4 s por pergunta (12% a 15% do total)**: a guarda em paralelo e, bem menos, o pool e a memória por pergunta.
Número de chamadas, tokens e custo ficaram iguais, como esperado, porque nada disso reduz trabalho do modelo.

**Limites:** 16 pares por versão, uma conta residencial e uma comercial, bancos locais (em rede remota o pool e a memória
por pergunta tendem a pesar mais), variação grande do provedor entre chamadas. O custo das duas baterias foi de
**US$ 0,09** no total.

## Tools em paralelo e tool em lote: avaliadas e não adotadas

Pedido: descobrir se compensam, com receio de o modelo errar números numa tool nova. Com o que foi medido, **não foram
adotadas**, e o código experimental da tool em lote foi descartado.

**O que o agente faz hoje** (conta comercial, "qual unidade consumiu mais"; 4 execuções com a sequência registrada):
três voltas do modelo. A **primeira** (1,2 a 2,1 s) chama `list_consumption_units`; a **segunda** (1,8 a 2,6 s) já
chama `get_consumption_summary` **uma vez por unidade, as três na mesma volta**; a **terceira** (3,0 a 4,8 s) redige a
resposta. Uma pergunta que mistura consumo e previsão chega a 25-27 s, com mais voltas.

**Por que não:**

- **Tools em paralelo:** o modelo já pede as leituras juntas, mas as tools somam só **0,1 a 0,4 s** (e 0,04 a 0,22 s com o
  pool). Rodá-las em paralelo economizaria cerca de 0,1 s. Não justifica o código.
- **Tool em lote** (`get_consumption_by_unit`, totais e ranking calculados em Python): ela só ganharia tempo se o modelo
  **pulasse a volta que lista as unidades** e chamasse a tool em lote direto, economizando uma volta (cerca de 2 s).
  Isso depende de o modelo mudar o jeito de chamar as tools, e a forma segura de conseguir isso é mudar o prompt do
  agente de consumo, que está fora do escopo. Sem isso, a tool nova seria só mais uma opção, e adicionar tools aumenta a
  superfície onde o modelo pode errar. A experiência foi encerrada por custo de requisições antes de testar.
- **Onde está o tempo de verdade:** nas voltas do modelo (principalmente a de redigir a resposta, de 3 a 5 s). Reduzi-las
  depende do prompt e do modelo, decisões da equipe fora desta mudança.

Se a equipe decidir mexer no prompt do agente de consumo, a tool em lote vira uma opção real a testar (o desenho é
simples: uma leitura por unidade com a mesma função de consumo, totais e ordem calculados em Python).

## Como medir antes e depois

1. **Pool:** `python -m scripts.bench_pool --ops 300 --threads 8` (só `SELECT 1`; usa `DATABASE_URL`).
2. **Chat:** cada resposta traz o cabeçalho `X-Request-ID`; as etapas (`input_guard`, `context`, `router`, agentes,
   `judge`, ...) ficam no rastro da requisição, com `duration_ms`. Compare os mesmos cenários nos painéis antes e
   depois de aplicar esta mudança, e com `OPENAI_FAST_REASONING_EFFORT` ligado e desligado.
3. **Streaming:** `curl -N -X POST .../chat/stream` com um JWT de teste mostra as etapas chegando.

## Fora do escopo (decisão da equipe)

Agente Juiz e Jev (timeout, payload, fallback, número de revisões), escolha e parâmetros de modelos e provedores
(inclusive circuito aberto para falhas do provedor), prompt do agente de consumo, agentes em paralelo e `/playground`.

## Documentos a atualizar quando a mudança for mesclada

- [Conexão PostgreSQL](postgres-connection.md): hoje diz que o módulo abre uma conexão por operação e que o projeto não
  tem pool, e cita `HOST_DB`, `PORT_DB`, `USER_DB`, `PASSWORD_DB` e `NAME_DB` e o `scripts.check_postgres`. Esses
  nomes e o script **não existem** no código atual do `delta-artificial-intelligence` (a conexão usa `DATABASE_URL`).
  Trecho sugerido para o parágrafo inicial depois do merge:

  > O conector PostgreSQL usa um pool de conexões por processo (`psycopg2.pool.ThreadedConnectionPool`), criado no
  > primeiro uso e fechado no encerramento da aplicação (`close_pool()`). A conexão vem de `DATABASE_URL`, com
  > `connect_timeout` e `statement_timeout` aplicados por operação (`set_config` local à transação). O tamanho é
  > configurado por `DB_POOL_MIN_SIZE`, `DB_POOL_MAX_SIZE` e `DB_POOL_WAIT_SECONDS`; `workers × DB_POOL_MAX_SIZE`
  > deve ficar abaixo do `max_connections` do PostgreSQL. Ao recarregar settings, chame `close_pool()`.

- [Settings](settings.md): incluir `DB_POOL_MIN_SIZE`, `DB_POOL_MAX_SIZE`, `DB_POOL_WAIT_SECONDS`,
  `OPENAI_FAST_REASONING_EFFORT` e `OPENAI_SPECIALIST_REASONING_EFFORT`.
- [API FastAPI](implementacao-api-fastapi.md): incluir a rota `POST /chat/stream` e o contrato dos eventos.
- [Guardrails](implementacao-guardrails.md) e [orquestração LangGraph](implementacao-langgraph-orquestracao.md):
  registrar que a guarda de entrada passou a ser dividida em regras instantâneas e classificador LLM, e que este roda
  em paralelo com contexto e roteador.

## O que foi implementado

Branch `feat/reduz-latencia-chat` (a partir de `feat/historico-conversas`):

- [x] Settings do pool e do raciocínio rápido (`0d60887`): `DB_POOL_MIN_SIZE`, `DB_POOL_MAX_SIZE`,
  `DB_POOL_WAIT_SECONDS`, `OPENAI_FAST_REASONING_EFFORT`, com validação e `.env.example`.
- [x] Raciocínio menor nas chamadas rápidas por configuração (`9465ea4`), sem mudar o padrão.
- [x] Pool de conexões PostgreSQL em `_cursor()` (`04f4630`), com `close_pool()` no `lifespan`.
- [x] Correção das conexões ociosas, testes do pool (18) e `scripts/bench_pool.py` (`0838942`).
- [x] Memória de consumo por pergunta: unidades e leituras por período (`b8e6101`), com 9 testes.
- [x] Guarda de entrada em paralelo com contexto e roteador; histórico lido uma vez (`7935429`), com 12 testes.
- [x] `POST /chat/stream` por SSE e `run_workflow_events` (`3304f72`), com 17 testes.
- [x] Plano ("Vou consultar ...") e progresso por agente e por tool no SSE, com rótulos fixos e 21 testes
  (`app/observability/progress.py`).
- [x] Documentação (este arquivo, README e AGENTS.md).
- [x] Rodada pontual com a IA real (`gpt-6-luna`): latência por etapa, guarda em paralelo e `low` (seção "Medição com a IA real").
- [x] Comparação antes e depois pela observabilidade, com ordem alternada (seção "Antes e depois pela observabilidade").
- [x] Tools em paralelo e em lote avaliadas e **descartadas**, com a evidência registrada.
- [ ] Medição contínua de latência, tokens e custo: **pendente**, pelos painéis de observabilidade.
