# Integração do Web App com a API

## Objetivo

Documentar como o `delta-web-app` (React, TypeScript e Vite) se comunica com a `delta-api-postgres` (Spring Boot), com foco nos fluxos de login, cadastro de usuário, cadastro de empresa e instalações.

## Contexto

Não existe um servidor BFF (Backend For Frontend) separado. O web app chama a API diretamente, e a camada de integração fica dentro do próprio front, em `src/services/`. A origem da API é configurada em `VITE_POSTGRES_API_URL` (sem o sufixo `/delta`) e nunca é versionada.

Os endpoints abaixo foram conferidos na branch `develop` da `delta-api-postgres`. A rota `GET /delta/auth/classification` existe só nessa branch.

---

## Camadas do front

```
pages / components  →  hooks  →  services  →  http.ts (único fetch)
```

| Camada | Responsabilidade |
|---|---|
| `components/`, `pages/` | Renderização e eventos; erros exibidos com `role="alert"`. |
| `hooks/` | Estado `loading`, `error` e `success`, com `AbortController`. |
| `services/` | Uma função tipada por operação, `signal: AbortSignal`, validação da resposta (`utils/apiValidation.ts`) e mensagens de erro em português. |
| `services/http.ts` | Único ponto com `fetch`; Bearer, renovação de token e tratamento de status. |
| `services/session.ts` | Sessão (access e refresh token) em `sessionStorage`, chave `delta.session`. |

A renovação ocorre quando faltam menos de 5 segundos para expirar ou após um `401`; renovações simultâneas são deduplicadas. Escritas só são repetidas após `401`, nunca por falha de rede.

---

## Endpoints usados

| Método e rota | Uso no front | Situação |
|---|---|---|
| `POST /delta/auth/login` | Login | Implementado |
| `POST /delta/auth/refresh` | Renovar sessão | Implementado |
| `GET /delta/auth/me` | Usuário atual | Implementado |
| `POST /delta/auth/create-account` | Cadastro de usuário | Implementado |
| `POST /delta/organizations` | Cadastro de empresa | Implementado |
| `POST /delta/auth/complete-registration` | Endereço e unidade da empresa | Implementado |
| `GET /delta/user-properties/{userId}`, `GET /delta/property/{id}`, `GET /delta/address/{id}` | Lista e detalhe de instalações | Implementado |
| `GET /delta/analytics/monthly-variation/{propertyId}`, `GET /delta/analytics/consumption-daily/{propertyId}` | Consumo das instalações | Implementado |
| `GET /delta/region-rate/{regionId}` | Validar região tarifária | Implementado |
| `POST /delta/address`, `POST` e `PUT /delta/property`, `POST /delta/device` | Cadastro e edição de instalação | Implementado |
| `GET`, `PUT` e `DELETE /delta/device` | Listar, trocar e remover dispositivos | Planejado (a API oferece; o front não usa) |
| `/delta/analytics/property-ranking` e demais views `dw` | Dashboard, ranking, vazamentos | Planejado (telas usam dados fixos) |

---

## Cadastro de usuário

1. As telas `/` e `/cadastro/credenciais` guardam os dados no `RegisterContext`.
2. Ao enviar as credenciais, o front valida os campos (`utils/registerValidation.ts`) e chama `POST /delta/auth/create-account`.
3. Corpo enviado: `name`, `email`, `password` (mínimo 8 caracteres), `phone` (somente dígitos, opcional) e `birthDate` (convertida de `dd/mm/aaaa` para `aaaa-mm-dd`).
4. A resposta traz os tokens, que são salvos na sessão; em seguida o fluxo segue para `/cadastro/loading`.
5. Erros: `409` (e-mail já cadastrado), `400` (dados inválidos) e `429` (limite de tentativas).

## Cadastro de empresa

Na rota `/cadastro/empresa/vinculando`, o hook `useCompanyRegistration` executa, em ordem:

1. `POST /delta/organizations` com razão social, nome fantasia, CNPJ (14 números), segmento e `declaredUnitCount` fixo em `1`.
2. `POST /delta/auth/complete-registration` com `address` (CEP de 8 números, cidade e estado), `property` (nome da unidade, tipo `PRÉDIO`, classificação e `organizationId`) e `habits` vazio.
3. `POST /delta/device` quando o código do dispositivo foi informado.

O progresso de cada etapa fica em memória: em uma nova tentativa após falha, o que já foi criado não é criado de novo.

### Mapeamentos

| Campo do formulário | Valor enviado |
|---|---|
| Tipo da indústria | `COMERCIAL_NORMAL_INDUSTRIAL`, `COMERCIAL_ENTIDADE_ASSISTENCIA_SOCIAL`, `PUBLICA_COM_CONTRATO` ou `COMERCIAL_ESPECIAL` |
| Segmento (texto livre) | `VAREJO`, `CONDOMINIO` ou `FACILITIES` se o texto contiver esse termo; caso contrário `INDUSTRIA` |

### Dados que não são enviados

A API não possui campos para os itens abaixo, que ficam apenas no estado do front (`localStorage`, com versão de schema):

- porte da empresa, rua e número;
- dias e horários de operação e turnos;
- usos e fonte de água;
- consumo médio mensal.

---

## Pendências conhecidas

- O cadastro de usuário e o de empresa ainda não foram validados contra uma API em execução; os testes automatizados do front usam `fetch` simulado.
- O segmento da empresa é texto livre no formulário e a API aceita quatro valores; hoje a conversão é por palavra-chave.
- Metas, alertas, vazão e clima não têm endpoint e aparecem como indisponíveis.
