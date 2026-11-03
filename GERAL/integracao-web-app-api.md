# Integração do Web App com a API

## Objetivo

Documentar como o `delta-web-app` (React, TypeScript e Vite) se comunica com a `delta-api-postgres` (Spring Boot), com foco nos fluxos de login, cadastro de usuário, cadastro de empresa e instalações.

## Contexto

Não existe um servidor BFF (Backend For Frontend) separado. O web app chama a API diretamente, e a camada de integração fica dentro do próprio front, em `src/services/`. A origem da API é configurada em `VITE_POSTGRES_API_URL` (sem o sufixo `/delta`) e nunca é versionada.

Referências verificadas: API `develop` no commit `6b8530fc6af28b63a57afb7c0cf6c6d9c7a21bf2`, serviços de autenticação da API no commit `e78fb66e35e71d2bb4939b7db1cb765e892a162a` e web app no commit `56782e36bf18926b0e22b3a991134d5a17fa9617`. A rota `GET /delta/auth/classification` aparece nessa versão da API, mas não é chamada pelos serviços do front inspecionados.

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

A sessão é guardada em `sessionStorage` para continuar disponível após recargas na mesma aba, sem criar uma sessão persistente em `localStorage`. Scripts da mesma origem podem ler os tokens; essa escolha não os isola de XSS. O front descarta o estado restaurado quando o refresh expira e chama `saveSession(null)` em respostas de autenticação inválida. Falhas de rede não limpam a sessão automaticamente. Ao renovar, substitui apenas o access token e sua expiração; não rotaciona o refresh. No backend verificado, o refresh é associado ao usuário no Redis com TTL e a renovação exige usuário ativo. Encerrar a aba encerra o armazenamento da aba, mas não revoga o token no Redis; esta documentação não afirma existir um endpoint de logout/revogação nesse fluxo.

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

`declaredUnitCount = 1` representa a única unidade criada nessa etapa do formulário, sem afirmar ser o total definitivo da organização. `habits = []` reutiliza o contrato de conclusão de cadastro sem criar hábitos residenciais no cadastro empresarial; são escolhas do payload atual do front, não exigências gerais da API.

O progresso fica no `progressRef` do hook: novas tentativas pulam etapas concluídas enquanto a mesma instância permanece montada. Recarregar, fechar a aba ou remontar o hook perde esse progresso e pode repetir os `POST`s. O fluxo usa os IDs retornados para retomar etapas nessa instância; não oferece uma chave de idempotência persistida entre execuções.

### Mapeamentos

| Campo do formulário | Valor enviado |
|---|---|
| Tipo da indústria | `COMERCIAL_NORMAL_INDUSTRIAL`, `COMERCIAL_ENTIDADE_ASSISTENCIA_SOCIAL`, `PUBLICA_COM_CONTRATO` ou `COMERCIAL_ESPECIAL` |
| Segmento (texto livre) | `VAREJO`, `CONDOMINIO` ou `FACILITIES` se o texto contiver esse termo; caso contrário `INDUSTRIA` |

### Dados que não são enviados

Os itens abaixo não são enviados no payload atual e ficam no rascunho do front (`localStorage`, com versão de schema). A persistência permite retomar o formulário após recargas. `CompanyRegisterContext` restaura versões 1 e 2, grava a versão 2 após alterações, remove JSON inválido e possui ação `RESET`; não define expiração automática. Isso descreve o estado local, sem atribuir essas informações ao banco:

- porte da empresa, rua e número;
- dias e horários de operação e turnos;
- usos e fonte de água;
- consumo médio mensal.

