### BD2-01 — Usar obrigatoriamente MongoDB

**Evidência direta:**

- [Repositório de versionamento do MongoDB](https://github.com/delta-app-ofc/delta-mongo-database)
- [Script de criação das coleções da aplicação](https://github.com/delta-app-ofc/delta-mongo-database/blob/main/scripts/delta-app/script-collections.js)
- [Script de índices da aplicação](https://github.com/delta-app-ofc/delta-mongo-database/blob/main/scripts/delta-app/script-indexes.js)
- [Teste automatizado das coleções, validações e índices](https://github.com/delta-app-ofc/delta-mongo-database/blob/main/tests/smoke.js)
- [API sobre o MongoDB](https://github.com/delta-app-ofc/delta-api-mongo)
- [Business Intelligence, que lê o MongoDB](https://github.com/delta-app-ofc/delta-business-intelligence)
- [Inteligência Artificial, que grava no MongoDB](https://github.com/delta-app-ofc/delta-artificial-intelligence)
- [Documentação da modelagem MongoDB](../modelagem-mongodb.md)

**Localização e como comprovar:**

O MongoDB guarda os dados de alto volume e de formato flexível do Delta. Ele é dividido em dois bancos, cada um com responsabilidade própria.

| Banco | Coleção | Função |
|---|---|---|
| `db_delta_telemetry` | `consumption_summary` | Resumo de consumo em janelas de 5 minutos, enviado pelo hardware |
| `db_delta_telemetry` | `device_status` | Um documento por dispositivo, com o último estado |
| `db_delta_app` | `user_preferences` | Preferências de cada usuário |
| `db_delta_app` | `alerts_history` | Histórico de alertas (vazamento, fluxo atípico, dispositivo offline) |
| `db_delta_app` | `chat_sessions` | Conversas com o chatbot |
| `db_delta_app` | `chat_feedback` | Avaliação positiva ou negativa da sessão |
| `db_delta_app` | `weather_daily` | Observações climáticas por localidade e dia |
| `db_delta_app` | `observability_requests` | Métricas de cada requisição da IA, com expiração em 90 dias |

#### 1. Por que MongoDB

- A telemetria chega em grande volume e em janelas fixas. O formato documental evita um `INSERT` por pulso e mantém o PostgreSQL só com dados cadastrais e transacionais.
- Os documentos de alerta, clima e observabilidade têm campos que mudam com o tempo, e o modelo documental aceita isso sem migração.
- Os dados de conversa ficam em um só documento por sessão, o que simplifica a leitura do histórico.

#### 2. Integridade sem esquema fixo

Cada coleção tem um validador `$jsonSchema` com `validationLevel: "moderate"`, que rejeita documentos com tipo ou valor inválido. O `user_id` e o `device_id` apontam para o PostgreSQL de forma lógica, sem chave estrangeira, porque o MongoDB não a oferece.

#### 3. Como comprovar

1. Abrir `script-collections.js` e conferir os validadores `$jsonSchema`.
2. Abrir `script-indexes.js` e conferir os índices, incluindo o índice com expiração (`expireAfterSeconds: 7776000`) de `observability_requests`.
3. Abrir `tests/smoke.js` e conferir os testes que rejeitam tipo inválido, valor fora do enum e chave duplicada.
4. Abrir o banco no Atlas ou no Compass e conferir as oito coleções.

> **Pendente:** anexar o print das oito coleções no Atlas ou no Compass.
