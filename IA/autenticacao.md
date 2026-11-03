# Autenticação da API de IA

> **Estado:** a validação do token do back-end descrita aqui está implementada e testada na branch
> `feat/reduz-latencia-chat` do `delta-artificial-intelligence` (PR 50), **ainda não mesclada na `main`**. Até o
> merge, a `main` da API de IA aceita só o token HS256 de desenvolvimento descrito na seção
> [Histórico de conversas e autenticação](arquitetura-inteligencia-artificial.md#histórico-de-conversas-e-autenticação-implementado-no-delta-artificial-intelligence).

## Objetivo

Explicar como o aplicativo, o back-end e a API de IA se entendem sobre **quem é o usuário**: quem emite o token,
o que a API de IA confere e o que o app precisa fazer.

## Quem faz o quê

Pense em um prédio com recepção: o **back-end** é a recepção (confere quem você é e entrega um crachá), e a **API de IA**
é o andar que só olha o crachá.

| Peça | Papel | Onde |
| --- | --- | --- |
| Back-end (`delta-api-postgres`) | Faz o login e **emite** o token; renova com o refresh token | `POST /delta/auth/login`, `/create-account`, `/refresh`, `/me` |
| API de IA (`delta-artificial-intelligence`) | **Só confere** o token e usa o `sub` como `user_id`; não emite nada | `app/auth.py` |
| Aplicativo (mobile e web) | Faz o login no back-end e manda o token à IA | cabeçalho `Authorization: Bearer <token>` |

O `user_id` vem **somente do token**. O app não envia `user_id` no corpo nem na URL; se enviar, é ignorado.

## O token que o back-end emite

Definido em `TokenService` do back-end:

| Item | Valor |
| --- | --- |
| Algoritmo | **RS256**: assinado com a chave **privada** RSA do back-end; quem confere usa a chave **pública** |
| Validade do token de acesso | 15 minutos |
| Cabeçalho | `alg=RS256`, `typ=JWT`, `kid` (padrão `delta-1`) |
| `sub` | id do usuário em `tb_user` (o mesmo `user_id` que a IA usa), como texto |
| `iss` e `aud` | padrão `delta-api` e `delta-api` (configuráveis no back-end) |
| `jti`, `iat`, `exp` | id do token, emissão e validade |
| Renovação | refresh token de 30 dias, guardado no Redis (`/delta/auth/refresh`) |

## O que a API de IA confere

Em **cada requisição**, nesta ordem:

1. A API tem uma forma de conferir configurada? Se não, **503**.
2. O token vem no cabeçalho `Authorization: Bearer`? Se não, **401**.
3. O algoritmo do cabeçalho é o que **a API configurou** (RS256)? O algoritmo nunca é escolhido pelo token: um token
   HS256 assinado com o texto da chave pública (o ataque de "confusão de algoritmo") e um token `alg=none` são recusados.
4. O `kid` é o esperado (`AUTH_KEY_ID`)? Vazio desliga essa conferência.
5. A assinatura, o `exp` (com tolerância de 10 s de relógio), o `iss` e o `aud` conferem, e todos os quatro campos
   (`exp`, `sub`, `iss`, `aud`) estão presentes?
6. O `sub` é um inteiro positivo de até 2.147.483.647 (o tipo `int` usado no MongoDB)?
7. **O usuário existe e está ativo** em `tb_user` (`fn_user_is_active`)? Se não, **401**. Se o banco não
   responder, **503** (a requisição é bloqueada, sem detalhes).

Qualquer falha dos passos 2 a 7 responde **401** com a mesma mensagem ("Token ausente ou inválido."), para não ajudar quem
tenta adivinhar. O passo 7 só roda depois de o token ser válido: tokens inválidos nunca consultam o banco.

### Por que conferir se o usuário está ativo, e como não pesar

O token vale 15 minutos. Sem a conferência, um usuário desativado continuaria usando a IA até o token vencer. O back-end já
faz essa checagem em toda requisição; a IA faz a mesma.

- **Custo:** é uma consulta pela chave primária, na conexão que já está no pool: cerca de **5 ms** (medido com o
  PostgreSQL local), contra os 8 a 12 s de uma resposta do chat. Sem pool seria ~40 ms.
- **Sem cache:** ela é refeita a cada requisição, então a desativação vale na hora. Um cache curto reduziria o número de
  consultas, mas abriria uma janela em que um usuário desativado ainda passa; por isso não foi usado.
- **Desligar:** `AUTH_CHECK_ACTIVE=false` (por exemplo em desenvolvimento sem banco).

## Configuração da API de IA

| Variável | Padrão | O que é |
| --- | --- | --- |
| `AUTH_PUBLIC_KEY` | (vazio) | Chave **pública** do back-end: caminho do PEM (com ou sem `file:`) ou o texto PEM. RSA de 2048 bits ou mais. **Obrigatória em staging e produção** |
| `AUTH_ISSUER` | `delta-api` | Deve ser igual a `auth.issuer` do back-end |
| `AUTH_AUDIENCE` | `delta-api` | Deve ser igual a `auth.audience` do back-end |
| `AUTH_KEY_ID` | `delta-1` | Deve ser igual a `auth.key-id` do back-end; vazio = não confere o `kid` |
| `AUTH_CHECK_ACTIVE` | `true` | Confere em `tb_user` se o usuário está ativo |
| `JWT_SECRET` | (vazio) | **Só desenvolvimento e teste** (HS256, 32 caracteres ou mais) |

- **Uma forma por vez:** com `AUTH_PUBLIC_KEY` definida vale só RS256 e o `JWT_SECRET` é ignorado. Sem ela, em desenvolvimento
  e teste, vale só HS256. Em `staging` e `production` o HS256 é recusado (503).
- **A chave pública é pública:** pode ficar em arquivo ou variável de ambiente sem risco; a **privada nunca sai do
  back-end**. A IA nunca registra o caminho nem o conteúdo da chave.
- **Troca de chave:** a chave é lida uma vez por processo. Ao trocar o par no back-end (e o `kid`), atualize
  `AUTH_PUBLIC_KEY` e `AUTH_KEY_ID` e **reinicie** a API de IA.

## Como o aplicativo deve chamar

1. **Login no back-end:** `POST /delta/auth/login` com e-mail e senha; guardar o `accessToken` (e o refresh token).
2. **Chamar a IA** com o token de acesso:

```http
POST /chat
Authorization: Bearer <accessToken>
Content-Type: application/json

{"message": "Quanto consumi esta semana?"}
```

3. **Se a IA responder 401:** o token venceu (15 min) ou o usuário foi desativado. Renovar no back-end
   (`POST /delta/auth/refresh`) e repetir a chamada **uma vez**. Se o refresh também falhar, voltar à tela de login.
4. **503** significa problema do lado do servidor (autenticação não configurada ou banco indisponível): mostrar
   "tente novamente" e **não** apagar a sessão de login.

As rotas que exigem o token: `POST /chat`, `POST /chat/stream`, `GET /sessions`, `GET /sessions/{id}/messages` e
`POST /sessions/{id}/close`. `GET /health` é aberta. O `/playground` é um console de desenvolvimento, **sem autenticação**,
com um usuário fixo de teste; vem ligado só em `development` e `test`.

## O que ainda depende de decisão ou de outro repositório

- **Papéis dentro de uma organização:** não existem; todo usuário vinculado a uma organização enxerga todas as unidades dela.
- **Revogar um token antes de vencer:** não é possível; vale o limite de 15 minutos mais a conferência de usuário ativo.
- **Testado com tokens no formato do back-end** (gerados por um par RSA de teste, com `aud` em lista e `kid`), **não** com
  um token emitido pelo back-end em execução: vale uma conferência ponta a ponta no ambiente de homologação.
