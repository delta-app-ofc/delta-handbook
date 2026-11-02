# Hábitos, simulações e saída ao usuário — mudanças dos agentes de IA

## Objetivo

Este documento reúne, em um só lugar, as mudanças feitas no repositório `delta-artificial-intelligence` para
responder à história de dívidas técnicas de IA (conversação, simulações e hábitos) e às melhorias que surgiram
durante a execução. Ele explica **o que mudou, por que mudou, como funciona e o que foi realmente validado**.

Caso motivador: *"quanto eu gastaria em dinheiro se eu lavasse roupa 3 vzs por semana?"*. Simular um hábito não
deve exigir cadastro nem criar registros, e a pessoa não deve conhecer a estrutura interna dos agentes.

> **Situação (01/11/2026):** tudo abaixo está implementado em branches com Pull Request aberto no
> `delta-artificial-intelligence`, **ainda não mesclado na `main`**. Os documentos antigos desta pasta descrevem a
> `main`; onde houver diferença, ela está sinalizada como "em PR".

## Resumo das mudanças

| Tema | O que muda para a pessoa usuária | Onde |
| --- | --- | --- |
| Custo de hábitos | Estimativa em reais da água de um hábito, com a tarifa dela | `estimate_habit_water_cost` |
| Simulação sem cadastro | "E se eu lavasse roupa 3x por semana?" responde na hora, sem gravar nada | prompt de Hábitos + `parse_frequency` |
| Cadastro em linguagem natural | "Adicione lavar roupas 3x na semana" cadastra de verdade | `create_habit` |
| Simulação "e se" | Impacto em litros de uma variação percentual do consumo, com gráfico e hipóteses | `simulate_consumption_change` |
| Metas e investimentos | "E se minha meta fosse X?" e cenários de aeradores, reúso e captação de chuva | `simulate_target_change`, `get_investment_scenarios` |
| Hábitos em Previsão e Vazamento | Os dois agentes passam a conhecer os hábitos cadastrados | `get_habit_baseline`, `get_habit_windows` |
| Sem detalhes técnicos | A resposta não cita agentes, ferramentas, API ou erros | filtro de saída + prompts |
| Nomes capitalizados | `Regar Plantas` em vez de `REGAR PLANTAS` | filtro de saída + prompt |
| Sugestões | Até 3 próximas perguntas em cada resposta e uma rota inicial | `suggestions` + `GET /chat/suggestions` |
| Observabilidade | Nível de raciocínio no log; SLO de latência de 15 s | `reasoning_effort`, `OBS_LATENCY_P95_LIMIT_MS` |
| Console de testes | Markdown, resposta "digitando", progresso completo, gráfico sem ficar vazio | `frontend/`, `progress.py`, `charts.py` |
| Banco local | Scripts de `db/postgres-init/` iguais ao schema oficial | `db/postgres-init/` |

## Mapa de Pull Requests e ordem de merge

Os PRs foram **encadeados**: cada branch já contém a anterior, então a ordem abaixo mescla sem conflito. Os PRs
dependentes têm como base a branch anterior, não a `main`.

| Ordem | Branch | PR | Base |
| --- | --- | --- | --- |
| 1 | `feat/custo-agua-habitos` | #57 | `main` |
| 2 | `feat/simulacao-habito-hipotetico` | #58 | `feat/custo-agua-habitos` |
| 3 | `fix/cadastro-habitos-linguagem-natural` | #59 | `feat/simulacao-habito-hipotetico` |
| 4 | `feat/habitos-em-previsao-e-vazamento` | #60 | `fix/cadastro-habitos-linguagem-natural` |
| 5 | `feat/simulacao-cenarios-e-se` | #61 | `feat/habitos-em-previsao-e-vazamento` |
| 6 | `fix/oculta-detalhes-tecnicos` | #62 | `feat/simulacao-cenarios-e-se` |
| 7 | `fix/nomes-de-habitos-capitalizados` | #63 | `fix/oculta-detalhes-tecnicos` |
| 8 | `feat/effort-no-log` | #64 | `fix/nomes-de-habitos-capitalizados` |
| 9 | `feat/metas-e-investimento` | #65 | `fix/oculta-detalhes-tecnicos` |
| 10 | `fix/grafico-previsao-vazio` | #66 | `feat/metas-e-investimento` |
| — | `chore/sincroniza-schema-local` | #67 | `main` |
| — | `fix/estagios-sse-ausentes` | #69 | `main` |
| — | `feat/sugestoes-proximas-perguntas` | #70 | `main` |
| — | `feat/markdown-no-console` | #71 | `main` |
| — | `fix/slo-latencia-15s` | sem PR ainda | `main` |
| — | `feat/resposta-digitando-console` | sem PR ainda | `feat/markdown-no-console` |

O PR #68 (`fix/erro-session-save`) ficou sem diferença: a `main` resolveu o mesmo erro de outro jeito e a branch
deve ser fechada sem mesclar.

## Hábitos

### Custo da água de um hábito

O cálculo é feito em Python (`app/tools/habits/calculations.py`), nunca pelo modelo de linguagem:

```text
litros por semana = litros por ocorrência × frequência por semana
litros por mês    = litros por semana × 4,33        (convenção de semanas por mês)
m³ por mês        = litros por mês ÷ 1000
custo por mês     = m³ por mês × tarifa (R$/m³), arredondado a 2 casas (meio para cima)
```

Exemplo de referência dos testes: 100 L por lavagem, 3 vezes por semana e tarifa sintética de R$ 10/m³ dão
**300 L/semana, 1.299 L/mês e R$ 12,99/mês**. Com a tarifa real do banco de teste (R$ 15,95/m³), o mesmo hábito
dá R$ 20,72/mês.

A tool `estimate_habit_water_cost` busca a tarifa do próprio usuário (região e classificação do imóvel) e **diferencia**
os casos, sem inventar valores:

| Status | Significado | O que a resposta traz |
| --- | --- | --- |
| `ok` | Tarifa encontrada | litros e custo mensal |
| `rate_unavailable` | Região sem tarifa vigente | só litros; pede a informação necessária |
| `property_not_found` | Imóvel não identificado | só litros |
| `needs_frequency` | Frequência ausente ou ilegível | pergunta só a frequência |
| `not_applicable` | Conta de organização | explica que hábitos são residenciais |
| `error` | Falha de banco | mensagem simples, sem detalhe técnico |

O valor é sempre o **custo estimado da água daquele hábito**: não é medição do hidrômetro nem o total da conta. Os
litros por ocorrência vêm do catálogo de referência (`LITERS_PER_SESSION`); a coluna `estimated_liters` do banco
existe, mas **nenhum caminho de escrita a preenche**, então costuma estar vazia.

### Simulação sem cadastro

Simular não cadastra, atualiza nem duplica nada. O prompt do agente de Hábitos agora manda chamar
`estimate_habit_water_cost` direto, na mesma resposta, sem pedir confirmação vazia e sem acrescentar energia,
detergente ou outros custos. O helper `parse_frequency` entende "3 vzs por semana", "3x", "três vezes" e "todo
dia" (7); frequência mensal ou ambígua devolve `None` e a pergunta é refeita.

### Cadastro em linguagem natural

- `days` (e `start_time`/`end_time`) são **opcionais**; antes, omitir `days` causava erro de schema.
- `resolve_habit_name` normaliza plural, acento e abreviações ("lavar roupas" → `LAVAR ROUPA`); nome ambíguo
  (por exemplo "lavar") devolve `needs_clarification` com as opções.
- Frequência pode vir dos dias informados ("toda segunda e sexta" → 2); mais dias do que a frequência pede
  esclarecimento.
- O prompt separa **cadastrar** de **listar**: listar não substitui o cadastro pedido.
- A confirmação só acontece quando o banco devolve o id gravado (`ok`). Conflito, dia inválido e falha de banco têm
  respostas próprias.
- Na revisão do Juiz, o agente de Hábitos roda **sem** a tool de escrita, então a gravação nunca é repetida.

### Schema oficial de hábitos (mudança importante)

O repositório `delta-database` mudou o modelo, e o código acompanha:

| Antes | Agora |
| --- | --- |
| `UNIQUE(user_id, habit_id)`: um hábito por usuário | Sem esse `UNIQUE`: o mesmo hábito pode ter horários diferentes |
| Duplicidade = hábito já cadastrado | **Conflito** = mesmo usuário, hábito, dia e `start_time` (gatilho `fn_check_user_habit_conflict`) |
| `fn_create_user_habit` com 4 argumentos | 6 argumentos (`p_start_time`, `p_end_time` opcionais) e retorna o id |

Sem horário, dois cadastros do mesmo hábito em dias que se sobrepõem colidem (NULL conta como igual a NULL); a
resposta orienta a informar o horário.

### Nomes capitalizados

O banco guarda `REGAR PLANTAS`. Para a pessoa, a resposta final troca os seis nomes do catálogo por `Regar Plantas`,
`Lavar Louça` etc. O nome em maiúsculas continua só para gravar no banco.

## Previsão

### Simulação "e se" (consumo)

`simulate_consumption_change(change_pct, days=30)` aplica uma variação percentual à média diária recente (a mesma
da previsão), compara com o cenário atual e devolve litros por dia e no período, a diferença e a lista de
hipóteses. O cálculo está em `app/tools/simulation/calculations.py` e o gráfico de barras é montado só com os dados
da tool. Sem 7 dias de histórico, a tool responde `insufficient_data` e não calcula nada. Exemplo (dados reais de
teste): −10 % levou 474,2 para 426,8 L/dia, ou 1.422,5 L a menos em 30 dias.

### Metas e investimentos

- `simulate_target_change(new_daily_target)` compara o risco de passar da meta atual e da simulada com a **mesma**
  projeção do mês. Não altera a meta cadastrada no app.
- `get_investment_scenarios()` lê `tb_investment_scenario` (cenários do catálogo, sem organização, e os da
  organização do usuário) e, havendo histórico, estima os litros economizados por ano com a redução de cada
  cenário. São valores de referência, nunca garantia. Só para conta de organização.

### Hábitos como contexto

`get_habit_baseline()` soma os litros esperados dos hábitos cadastrados por semana, mês e dia da semana, usando
`estimated_liters` quando existe e a referência do catálogo quando não. Serve para explicar picos e sustentar
simulações; **não entra** no cálculo da previsão.

### Gráfico sem série diária

Quando o agente só calcula a previsão e não lê o histórico diário, o gráfico antes saía vazio. Agora ele mostra
barras do mês: consumido até hoje, projeção e meta.

## Vazamento

`get_habit_windows(day)` devolve os hábitos (dia, horário, litros) para o agente dizer se uma janela anômala
**coincide** com um hábito. As regras seguem o princípio do agente de Vazamento:

- hábito só atenua a interpretação; nunca descarta o indício nem confirma ou afasta vazamento;
- hábito sem horário só permite comparar pelo dia;
- sem hábitos cadastrados, o agente não comenta hábitos;
- limiares e janelas de madrugada do motor de detecção não mudam.

## O que a pessoa vê e o que fica oculto

| Item | Antes | Agora |
| --- | --- | --- |
| Campo `agents_used` na resposta do `/chat` e do `/chat/stream` | Lista de agentes | Removido |
| Rótulo das respostas enviadas à síntese | `[HABITS]`, `[FORECAST]` | `[Informação 1]`, `[Informação 2]` |
| Prompt da síntese | Pedia "qual agente forneceu o quê" | Pede voz única do Delta e proíbe nomes internos |
| Frases técnicas na resposta final | Podiam aparecer (ferramenta, status, API, banco) | Removidas por filtro; se sobrar nada, aviso genérico |
| Regra de linguagem | Não existia | Bloco `_REGRA_LINGUAGEM_USUARIO` nos prompts de Consumo, Hábitos, Previsão e Vazamento |

O filtro (`hide_technical_details`, `app/guardrails/output.py`) corta frases que citam nomes `snake_case`, agentes,
ferramentas, `status:`, traceback/exception/timeout/JSON, nomes de provedores e bancos, e "API/banco/servidor"
junto de palavra de falha. Ele roda **só na resposta final** ao usuário, não nos campos de diagnóstico do console,
que precisam dos nomes internos. **Limitação:** é uma regra por padrão de texto; pode deixar passar uma frase
técnica escrita de outro jeito e pode cortar uma frase normal. O prompt do RAG não recebe a regra de linguagem.

### Sugestões de próximas perguntas

Cada resposta traz `suggestions` (até 3 perguntas ligadas aos assuntos tratados, sem repetir a que acabou de ser
feita) e a rota autenticada `GET /chat/suggestions` devolve perguntas iniciais pelo perfil. As regras são fixas, em
`app/graph/suggestions.py`: sem LLM, sem custo e sem risco de expor detalhes técnicos. Conta de organização nunca
recebe perguntas de hábitos.

## Observabilidade

- **Nível de raciocínio no log:** cada chamada ao modelo registra `reasoning_effort` ao lado de `model` (por
  exemplo `gpt-6-luna` com `high`), também nos eventos `model.start` e `model.end`. Só vale para chamadas OpenAI.
  O cartão de modelo do console exibe o esforço.
- **SLO de latência:** o limite padrão do p95 passou de 8 s para **15 s** (`OBS_LATENCY_P95_LIMIT_MS`, ainda
  configurável). Medições antigas passam a ser avaliadas contra o novo limite.
- **Progresso (SSE):** toda ferramenta de agente precisa de um rótulo em `app/observability/progress.py`; sem rótulo
  não há evento e a pessoa fica sem mensagem de progresso. Um teste varre as ferramentas e falha se alguma ficar sem.

## Console de testes

- Respostas do Delta são renderizadas em **Markdown** (títulos, listas, negrito, itálico e código), montando o DOM
  com `createElement`/`textContent`; HTML vindo do modelo continua sendo texto.
- A resposta do chat aparece **aos poucos** (até cerca de 2,5 s, com cursor), respeitando
  `prefers-reduced-motion`.
- O erro `session_save · ValueError` vinha de o console criar um id de sessão que não existia no MongoDB; a `main`
  passou a criar uma sessão real nesse caso.

## Banco local de desenvolvimento

`db/postgres-init/` foi sincronizado com o `delta-database` na ordem do `setup_db.py` oficial:

| Arquivo | Origem |
| --- | --- |
| `01-schema.sql` | `script-schema.sql` |
| `02-optimization.sql` | `script-optimization.sql` (funções e gatilhos) |
| `03-audit.sql` | `script-audit.sql` |
| `04-local-roles.sql` | **Só local**: cria as roles `sys_*` exigidas pelos GRANTs do datamart |
| `05-dataload.sql` | `script-dataload.sql` |
| `06-datamart-schema.sql` | `script-datamart.sql` |

Validação: os seis arquivos subiram num PostgreSQL 16 descartável sem erro (371 municípios; funções de hábitos e
gatilho de conflito respondendo). O `script-roles.sql` oficial não é copiado porque cria usuários com senha e usa o
banco `deltadb`. O schema oficial continua sendo mantido no `delta-database`; não edite as cópias à mão.

## O que foi validado e o que não foi

| Verificação | Resultado |
| --- | --- |
| Testes automatizados (modelo e bancos substituídos), todas as branches juntas com a `main` de 01/11/2026 | 604 passaram, 65 ignorados |
| Testes de sessão e histórico com MongoDB real descartável | Passaram |
| PostgreSQL real (Neon) do `.env`: leituras, tarifa, funções de hábitos | Funcionaram |
| Cadastro com PostgreSQL real | Função real executada em transação com `ROLLBACK`; o usuário continuou com os mesmos hábitos |
| MongoDB real (somente leitura): simulação "e se", baseline | Funcionaram |
| OpenAI real: 3 perguntas pelo fluxo completo (custo de hábito, "e se" e cadastro), cerca de 16 chamadas | Respostas corretas, sem nomes internos, `reasoning_effort` no log |
| Gravação do cadastro com a conexão do app e commit real | **Não validada** (usou `ROLLBACK`) |
| Qualidade semântica de todas as respostas do modelo | **Não validada** além das 3 perguntas |
| Markdown e efeito de digitação | Verificados no navegador com um teste isolado; a tela completa do console não foi percorrida |

## Limitações e dívidas

- `estimated_liters` não é gravado por nenhum caminho; o custo usa o catálogo de referência.
- O filtro de detalhes técnicos é por padrão de texto (ver acima).
- Os cenários de investimento da organização de teste não têm histórico de consumo, então a economia em litros fica
  vazia nela.
- O CodeRabbit pulou a revisão dos PRs empilhados (base diferente da `main`) e atingiu o limite gratuito; use
  `@coderabbitai review` quando a cota voltar.
- O Sonar ficou "pendente" em alguns PRs por indisponibilidade da análise (não por teste quebrado).
- `AGENTS.md` do `delta-artificial-intelligence` deve ser atualizado depois do merge.

## Como reproduzir

```bash
# no delta-artificial-intelligence, com todas as branches mescladas
APP_ENV=test python -m pytest -q          # suíte com substitutos (ignora o .env)
node --test frontend/markdown.test.mjs    # parser de Markdown do console
docker compose -f docker-compose.dev.yml up -d   # PostgreSQL e MongoDB locais
```

Documentos relacionados: [`arquitetura-inteligencia-artificial.md`](arquitetura-inteligencia-artificial.md),
[`implementacao-agentes-langchain.md`](implementacao-agentes-langchain.md),
[`implementacao-api-fastapi.md`](implementacao-api-fastapi.md),
[`implementacao-guardrails.md`](implementacao-guardrails.md), [`observabilidade.md`](observabilidade.md) e
[`postgres-connection.md`](postgres-connection.md).
