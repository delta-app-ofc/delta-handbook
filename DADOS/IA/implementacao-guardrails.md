# Implementação: Guardrails de Entrada e Saída

## Objetivo

Implementar uma camada de validação que envolve toda a execução dos agentes, bloqueando mensagens maliciosas na entrada e protegendo dados sensíveis na saída.

## Contexto

Modelos de linguagem são suscetíveis a **prompt injection** — tentativas de alterar o comportamento do modelo inserindo instruções falsas na mensagem do usuário. Além disso, a resposta do agente pode acidentalmente expor dados pessoais (CPF, credenciais) que nunca devem aparecer para o usuário.

Os guardrails são verificações simples e determinísticas — não usam LLM — que funcionam como um filtro antes e depois da execução dos agentes.

---

## Arquitetura

```
POST /chat
  │
  ▼
validate_input()   ← GUARDRAIL DE ENTRADA
  │ ok? → run_workflow() (LangGraph + agentes)
  │           │
  ▼           ▼
validate_output()  ← GUARDRAIL DE SAÍDA
  │ ok? → salva no MongoDB + retorna resposta
  │ falha? → HTTP 500
```

Se qualquer guardrail falhar, a requisição é interrompida e nenhuma mensagem é salva no histórico.

---

## Guardrail de entrada — `app/guardrails/input.py`

### Validações implementadas

| Verificação | Regra | Resposta se falhar |
|-------------|-------|--------------------|
| `user_id` válido | Deve ser inteiro positivo | 422 "user_id inválido" |
| Mensagem não vazia | Não pode ser apenas espaços | 422 "Mensagem vazia" |
| Tamanho máximo | Máximo 2.000 caracteres | 422 "Mensagem excede 2000 caracteres" |
| Prompt injection | Detecta padrões suspeitos | 422 "Mensagem contém padrão não permitido" |

### Padrões de prompt injection detectados

```python
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.I),
    re.compile(r"(system|assistant)\s*:\s*", re.I),
    re.compile(r"<\s*/?system\s*>", re.I),
    re.compile(r"jailbreak", re.I),
]
```

**O que cada padrão bloqueia:**

- `ignore all previous instructions` — tentativa clássica de sobrescrever o prompt de sistema
- `system:` ou `assistant:` — simulação de mensagens de outros papéis (role injection)
- `<system>` ou `</system>` — tentativa de inserir tags de sistema via texto
- `jailbreak` — palavra diretamente associada a contorno de restrições

### Código da função

```python
def validate_input(user_id: int, message: str) -> dict:
    if not isinstance(user_id, int) or user_id <= 0:
        return {"ok": False, "reason": "user_id inválido."}

    if not message or not message.strip():
        return {"ok": False, "reason": "Mensagem vazia."}

    if len(message) > _MAX_LEN:
        return {"ok": False, "reason": f"Mensagem excede {_MAX_LEN} caracteres."}

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(message):
            return {"ok": False, "reason": "Mensagem contém padrão não permitido."}

    return {"ok": True}
```

A função retorna um dicionário em vez de lançar exceção diretamente. O router HTTP (em `chat.py`) decide o código de status HTTP baseado em `ok`.

---

## Guardrail de saída — `app/guardrails/output.py`

### Validações implementadas

| Verificação | Regra | Resposta se falhar |
|-------------|-------|--------------------|
| Resposta não vazia | O agente deve ter retornado algo | 500 "Resposta vazia do agente" |
| CPF | Detecta formato de CPF no texto | 500 "Resposta contém dado sensível (CPF)" |
| Credenciais | Detecta padrões `senha:`, `password=` | 500 "Resposta contém possível credencial" |

### Expressões regulares usadas

```python
_CPF_RE = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}")
_SENHA_RE = re.compile(r"\b(senha|password|secret)\b\s*[:=]\s*\S+", re.I)
```

O padrão de CPF cobre formatos com e sem pontuação (123.456.789-00 e 12345678900). O padrão de senha captura construções como `senha: abc123` ou `password=xyz`.

---

## Limitações e evolução prevista

Os guardrails implementados são uma **primeira camada** — eficientes para os casos mais comuns, mas não exaustivos. A arquitetura prevê evolução futura com:

- Classificação semântica via LLM para detectar intenções maliciosas não cobertas por regex
- Verificação de coerência numérica (ex.: consumo de 50.000 litros num dia provavelmente é erro do agente)
- Validação de fontes do RAG (quando o Agente RAG estiver ativo)

Ver [arquitetura-inteligencia-artificial.md](arquitetura-inteligencia-artificial.md) — seção "Guardrails" para a lista completa de validações propostas.
