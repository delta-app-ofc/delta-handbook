# Implementação: Guardrails de Entrada e Saída

## Objetivo

Implementar uma camada de validação que envolve toda a execução dos agentes, protegendo o sistema em duas frentes: bloqueando mensagens maliciosas na entrada e impedindo que dados pessoais apareçam na saída.

## Contexto

Modelos de linguagem são suscetíveis a **prompt injection** — tentativas de alterar o comportamento do modelo inserindo instruções falsas na mensagem do usuário. Além disso, o agente pode acidentalmente expor dados pessoais (CPF, telefone, e-mail) que o próprio usuário digitou ou que o modelo gerou.

Os guardrails combinam verificações determinísticas (regex, palavras-chave) com uma classificação semântica via LLM para os casos que o regex não consegue capturar.

---

## Arquitetura

```text
POST /chat → autenticação + sessão → run_workflow()
  │
  ├─ validate_input_rules()  ← tamanho, PII, injeção e dados internos
  ├─ prepare                ← classify_input() em paralelo com contexto/roteamento
  ├─ especialistas → composição → Juiz
  └─ output_guard           ← PII, ownership, limpeza e histórico
```

Se as regras de entrada recusarem a mensagem, os especialistas não são chamados. A classificação semântica precisa liberar antes de sua execução, mas contexto/roteamento podem ter iniciado em paralelo. No chat autenticado, o histórico recebe a pergunta anonimizada no estado e a resposta tratada; o console tem um caminho próprio que salva a pergunta original. Falha de saída troca o texto por mensagem segura e descarta gráfico, sem implicar HTTP 500.

---

## Guardrail de entrada — `app/guardrails/input.py`

### Etapa 1 — Anonimização de PII

Antes de qualquer verificação, dados pessoais são substituídos por tokens temporários:

```python
PII_PATTERNS = [
    ("CPF",      re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")),
    ("CNPJ",     re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")),
    ("TELEFONE", re.compile(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}")),
    ("EMAIL",    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
]
```

Uma mensagem como `"meu CPF é 123.456.789-00"` vira `"meu CPF é [PII_CPF_a3f9c1]"` antes de chegar ao agente. O mapa `{token: valor_original}` é passado ao guardrail de saída para omitir os tokens, sem restaurar os valores originais.

### Etapa 2 — Validações básicas

| Verificação | Regra | HTTP se falhar |
|-------------|-------|---------------|
| `user_id` válido | Inteiro positivo | 422 |
| Mensagem não vazia | Não pode ser só espaços | 422 |
| Tamanho máximo | Máximo 2.000 caracteres | 422 |

### Etapa 3 — Detecção de prompt injection

Exemplos de padrões; a lista também inclui tentativas de assumir outra identidade ou consultar outro usuário:

```python
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(as\s+)?instru[çc][oõ]es", re.I),
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.I),
    re.compile(r"forget\s+your\s+instructions", re.I),
    re.compile(r"(system|assistant)\s*:\s*", re.I),
    re.compile(r"<\s*/?system\s*>", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"act\s+as\s+(if\s+)?", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.I),
    re.compile(r"dan\s+mode", re.I),
    re.compile(r"modo\s+irrestrito", re.I),
    re.compile(r"\[INST\]", re.I),
    re.compile(r"###\s*instruction", re.I),
    re.compile(r"override\s+(your\s+)?instructions?", re.I),
    re.compile(r"desconsider[ea]\s+(suas\s+)?instru[çc][oõ]es", re.I),
]
```

### Etapa 4 — Detecção de tentativas de acesso a dados internos

Palavras-chave que indicam que o usuário está tentando extrair informações do sistema:

```python
_INTERNAL_DATA_KEYWORDS = [
    "prompt do sistema", "system prompt", "suas instruções",
    "variável de ambiente", "chave de api", "api key",
    "senha do sistema", "token de acesso", "banco de dados interno",
    "dados de outros usuários", "lista de usuários", "credenciais",
]
```

### Etapa 5 — Classificação semântica via LLM

Só é chamada se todas as etapas anteriores passarem. Usa `llm_rapido` para classificar a intenção em quatro categorias:

| Categoria | O que detecta |
|-----------|---------------|
| `APROVADO` | Pergunta legítima sobre consumo, vazamentos, previsão ou hábitos |
| `OFENSIVO` | Xingamentos, assédio ou discurso de ódio |
| `PERIGOSO` | Instruções que causam dano físico, psicológico ou coletivo |
| `ILICITO` | Pedido de auxílio para atividades ilegais |

Se o LLM estiver indisponível, a classificação é ignorada — os filtros determinísticos já cobrem os casos mais óbvios.

### Contrato de retorno

```python
# Aprovado — agente recebe a mensagem anonimizada
{"ok": True, "message": "<texto anonimizado>", "pii_map": {"[PII_CPF_a3f]": "123.456.789-00"}}

# Bloqueado
{"ok": False, "reason": "<motivo público>"}
```

---

## Guardrail de saída — `app/guardrails/output.py`

### Etapa 1 — Redação de PII gerada pelo modelo

Usa os mesmos `PII_PATTERNS` do guardrail de entrada para mascarar os dados que correspondem aos padrões de CPF, CNPJ, telefone e e-mail:

```python
response = pattern.sub(f"[{label} OMITIDO]", response)
```

### Etapa 2 — Resolução de tokens da entrada

Tokens como `[PII_CPF_a3f]` que aparecerem na resposta são substituídos por `[CPF OMITIDO]` — o valor original nunca é reposto.

### Etapa 3 — Detecção de credenciais

```python
_SENHA_RE = re.compile(r"\b(senha|password|secret)\b\s*[:=]\s*\S+", re.I)
```

Captura construções como `senha: abc123` ou `password=xyz`.

### Por que a saída não bloqueia na PII?

Diferente do guardrail de entrada, a saída **nunca bloqueia** por PII — ela **redige**. Mascarar permite manter o restante da resposta. Credenciais ou referência explícita a outro usuário podem provocar substituição por mensagem segura; as regex não garantem detecção de todo dado pessoal.

---

## Integração em `app/routes/chat.py`

A rota valida autenticação e propriedade da sessão e chama o grafo:

```python
state = run_workflow(user_id, session_id, req.message)
if state.get("_blocked"):
    raise HTTPException(status_code=422, detail=state["response"])
```

Dentro do grafo, o resultado de `validate_input_rules` alimenta `question` e `pii_map`; `classify_input` roda durante `prepare`. Depois dos especialistas e do Juiz, `output_guard` chama `validate_output` e `validate_ownership`, trata texto/gráfico e anexa o turno quando a persistência está habilitada. Não há parâmetro de usuário escolhido pelo cliente nesse caminho.

---

## Limitações e evolução prevista

- Coerência numérica depende dos cálculos determinísticos e da comparação com evidências pelo Juiz; um volume alto isoladamente não demonstra erro.
- O RAG está ativo e leva fontes/trechos ao Juiz. Similaridade vetorial não comprova relevância ou verdade.
- Regex podem ter falsos positivos e negativos, sem proteção universal contra PII ou injeção.

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seção "Guardrails".

## Julgamento e saída

O [Juiz](agente-juiz.md) avalia a candidata pronta e as evidências, com até uma revisão. Não substitui as regras de saída.

`validate_output` recusa resposta vazia, mascara os mesmos padrões de PII e troca tokens pelo rótulo de omissão, sem restaurar os dados originais. Expressão de possível credencial (`senha`, `password` ou `secret` com atribuição) bloqueia a saída.

`validate_ownership` procura referência explícita ao ID de outro usuário no texto. `chart_mentions_other_user` percorre dicionários/listas e descarta gráfico com campo `user_id` diferente do autenticado. São verificações por padrões/campos, sem capacidade de provar a origem de toda frase ou ponto de gráfico.

Após aprovação dessas regras, `hide_technical_details` remove frases que expõem nomes de agentes, ferramentas, status, bancos e erros técnicos. Se não restar conteúdo útil, usa mensagem genérica. `capitalize_habit_names` apresenta os nomes do catálogo em formato de título. Esse tratamento ocorre depois do Juiz, sem nova avaliação da versão limpa.

## Persistência e erros públicos

A entrada bloqueada termina o grafo; chat JSON retorna 422 e tenta remover a sessão recém-criada vazia. Em SSE já aberto, o bloqueio vira evento `error` com status 422.

Recusa do guardrail final substitui o texto por mensagem segura e remove gráfico; não é automaticamente erro HTTP. O turno pode ser salvo com essa resposta. O histórico recebe a pergunta do estado, já anonimizada pelas regras, e o texto final tratado. As duas gravações não formam transação única.

O console pode testar um especialista isoladamente e não deve ser confundido com o fluxo completo de autenticação, perfil, Juiz e saída da aplicação.

## Verificação e limites

`test_guardrails.py`, `test_hide_technical_details.py` e `tests/isolation/` cobrem padrões, saída e isolamento em cenários controlados. Proteção depende também de identidade vinda do JWT, seleção autorizada de unidades, consultas parametrizadas e ferramentas com escopo fixo.

Regras de texto podem ter falsos positivos/negativos. Não há promessa de detecção universal de injeção, PII ou conteúdo indevido.

## Código relacionado

- [app/guardrails/input.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/guardrails/input.py)
- [app/guardrails/output.py](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/app/guardrails/output.py)
