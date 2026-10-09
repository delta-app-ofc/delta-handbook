# Implementação: Guardrails de Entrada e Saída

## Objetivo

Implementar uma camada de validação que envolve toda a execução dos agentes, protegendo o sistema em duas frentes: bloqueando mensagens maliciosas na entrada e impedindo que dados pessoais apareçam na saída.

## Contexto

Modelos de linguagem são suscetíveis a **prompt injection** — tentativas de alterar o comportamento do modelo inserindo instruções falsas na mensagem do usuário. Além disso, o agente pode acidentalmente expor dados pessoais (CPF, telefone, e-mail) que o próprio usuário digitou ou que o modelo gerou.

Os guardrails combinam verificações determinísticas (regex, palavras-chave) com uma classificação semântica via LLM para os casos que o regex não consegue capturar.

---

## Arquitetura

```
POST /chat
  │
  ▼
anonymize()            ← substitui CPF, CNPJ, telefone e e-mail por tokens
  │
  ▼
validate_input()       ← GUARDRAIL DE ENTRADA
  │  ok? → agente recebe mensagem anonimizada
  │
  ▼
run_workflow()         ← LangGraph + agentes
  │
  ▼
validate_output()      ← GUARDRAIL DE SAÍDA
  │  ok? → salva no MongoDB + retorna resposta limpa
  │  falha? → HTTP 500
```

Se `validate_input` falhar, nenhum agente é chamado e nada é salvo. Se `validate_output` falhar, a resposta é descartada. O MongoDB recebe sempre a mensagem **original** do usuário (não a anonimizada) e a resposta **revisada** (com PII omitida).

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

Uma mensagem como `"meu CPF é 123.456.789-00"` vira `"meu CPF é [PII_CPF_a3f9c1]"` antes de chegar ao agente. O mapa `{token: valor_original}` é passado ao guardrail de saída para desfazer ou omitir os tokens.

### Etapa 2 — Validações básicas

| Verificação | Regra | HTTP se falhar |
|-------------|-------|---------------|
| `user_id` válido | Inteiro positivo | 422 |
| Mensagem não vazia | Não pode ser só espaços | 422 |
| Tamanho máximo | Máximo 2.000 caracteres | 422 |

### Etapa 3 — Detecção de prompt injection (15 padrões)

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

Usa os mesmos `PII_PATTERNS` do guardrail de entrada para remover qualquer dado pessoal que o modelo possa ter inserido diretamente na resposta:

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

Diferente do guardrail de entrada, a saída **nunca bloqueia** por PII — ela **redige**. Bloquear geraria um HTTP 500 ao usuário sem motivo aparente. Redigir é mais seguro: a resposta chega limpa.

---

## Integração em `app/routes/chat.py`

```python
guard = validate_input(req.user_id, req.message)
if not guard["ok"]:
    raise HTTPException(status_code=422, detail=guard["reason"])

anonymized = guard["message"]   # mensagem sem PII → vai para o agente
pii_map    = guard["pii_map"]   # tokens → usados na saída

state = run_workflow(user_id=req.user_id, session_id=session_id, question=anonymized)

out_guard = validate_output(state["response"], pii_map=pii_map)
if not out_guard["ok"]:
    raise HTTPException(status_code=500, detail=out_guard["reason"])

append_turn(session_id, req.user_id, "human", req.message)          # original
append_turn(session_id, req.user_id, "assistant", out_guard["response"])  # revisada
```

---

## Limitações e evolução prevista

- Verificação de coerência numérica (ex.: consumo de 50.000 litros em um dia provavelmente é erro do agente)
- Validação de fontes do RAG (quando o Agente RAG estiver ativo)

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seção "Guardrails".
