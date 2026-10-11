# Modelagem NoSQL (MongoDB) — Projeto Delta

Este documento define a modelagem oficial das coleções MongoDB do Projeto Delta, complementando o
[`modelagem-relacional.md`](./DADOS/SQL/modelagem-relacional.md) (que trata do PostgreSQL) e a documentação de
infraestrutura de ingestão (payloads do ESP32/Arduino e camada Redis).

O escopo aqui é estritamente o **modelo de dados**: quais coleções existem, o que cada uma armazena,
como se relacionam (ou deliberadamente não se relacionam) e quais índices sustentam essa modelagem em
produção.

---

## 1. Papel do MongoDB na Arquitetura

O Projeto Delta usa três motores de persistência, cada um com uma responsabilidade fechada:

| Motor          | Responsabilidade                                                                                       |
|----------------|--------------------------------------------------------------------------------------------------------|
| **PostgreSQL** | CRUD relacional obrigatório, cadastro de usuários/propriedades/dispositivos, tabelas agregadas para BI |
| **MongoDB**    | Ingestão de telemetria do ESP32, domínio de aplicativo (preferências, alertas, chat)                   |
| **Redis**      | Cache de rotina calculada pela IA, throttling de notificações, rankings (Sorted Sets)                  |

O MongoDB entra especificamente onde o SQL sofreria: escrita de alto volume vinda dos dispositivos IoT e
documentos com estrutura variável (histórico de mensagens de chat, preferências flexíveis por usuário).
Dados de cadastro, permissões e tudo que exige integridade referencial forte permanecem no PostgreSQL —
o MongoDB **não duplica** esse domínio.

---

## 2. Organização em Databases

A modelagem oficial usa **dois databases** dentro do mesmo cluster Atlas, separando a carga de máquina
(alto volume, escrita constante) da carga de usuário (baixo volume, leitura predominante):

| Database             | Conteúdo                                                               | Padrão de carga                                            |
|----------------------|------------------------------------------------------------------------|------------------------------------------------------------|
| `db_delta_telemetry` | `consumption_summary`, `device_status`                   | Escrita pesada e constante (ESP32 → API a cada 5 min)      |
| `db_delta_app`       | `user_preferences`, `alerts_history`, `chat_sessions`, `chat_feedback`, `weather_daily` | Leitura predominante, escrita esporádica (ação do usuário) |

> A separação em dois databases também define o perímetro das *custom roles* documentadas na governança
> de acesso: a credencial que a API usa para ingestão de telemetria não precisa (e não deve) ter acesso ao
> database de aplicativo, e vice-versa.

---

## 3. Database: `db_delta_telemetry`

### 3.1. `consumption_summary`

Documento consolidado e leve, calculado pelo hardware e enviado diretamente para `consumption_summary`. A API associa o usuário e persiste a janela; a detecção de anomalias consome os resumos depois da ingestão. É a fonte dos gráficos e do histórico de consumo do aplicativo.

| Campo                | Tipo      | Obrigatório | Descrição                             |
|----------------------|-----------|-------------|---------------------------------------|
| `_id`                | ObjectId  | Sim         | Identificador do documento            |
| `device_id`          | string    | Sim         | Dispositivo de origem                 |
| `user_id` | int | Sim | Usuário dono do dispositivo (referência ao PostgreSQL) |
| `window_started_at`  | timestamp | Sim         | Início da janela resumida             |
| `window_finished_at` | timestamp | Sim         | Fim da janela resumida                |
| `consumption_liters` | double    | Sim         | Volume total consumido na janela      |
| `lpm_average`        | double    | Não         | Vazão média (litros/minuto)           |
| `anomaly_detected`   | bool      | Não         | Ver nota abaixo sobre quem calcula este campo |

```json
{
  "_id": { "$oid": "60c72b2f9b1d8b2bad723a12" },
  "device_id": "ESP32-SP-0912",
  "user_id": 212,
  "window_started_at": "2026-07-17T17:05:00Z",
  "window_finished_at": "2026-07-17T17:10:00Z",
  "consumption_liters": 14.4,
  "lpm_average": 2.5,
  "anomaly_detected": false
}
```

> **Quem calcula `anomaly_detected`?** Não é o agente de chat (`delta-artificial-intelligence`,
> Agente de Vazamento) — ele só *lê* este campo e o histórico de `alerts_history`, nunca decide
> limiar por conta própria (regra explícita do prompt desse agente: "nunca invente limiares/padrões").
> Quem calcula é um componente separado, o motor de detecção
> (`delta-business-rules/detection/`): regras explicáveis (fluxo contínuo, consumo de
> madrugada, desvio da baseline estatística do próprio usuário), sem modelo de ML, reagindo
> quase em tempo real via MongoDB Change Streams sobre as janelas recém-inseridas nesta
> coleção. Ver `detection/README.md` naquele repositório para o detalhe completo.

Esta é a coleção **permanente** do banco de telemetria: não tem TTL e é ela quem sustenta o histórico do
app e a exportação diária para as tabelas de dashboard no PostgreSQL.

### 3.2. `device_status`

Documento único por dispositivo (padrão *upsert*), atualizado a cada ping. Alimenta o painel administrativo
de saúde do hardware.

| Campo                   | Tipo      | Obrigatório | Descrição                                                           |
|-------------------------|-----------|-------------|---------------------------------------------------------------------|
| `_id`                   | ObjectId  | Sim         | Identificador do documento                                          |
| `device_id`             | string    | Sim         | Identificador do dispositivo                                        |
| `last_ping_at`          | timestamp | Não         | Último contato recebido                                             |
| `wifi_signal_rssi`      | enum      | Não         | Faixa de sinal Wi-Fi (ex.: `excellent`, `good`, `weak`, `critical`) |
| `firmware_version`      | string    | Não         | Versão do firmware instalado                                        |
| `connectivity_status`   | enum      | Não         | `online` / `offline` / `unstable`                                   |
| `unavailability_reason` | string    | Não         | Motivo registrado quando `connectivity_status != online`            |

```json
{
  "_id": { "$oid": "60c72b2f9b1d8b2bad723a20" },
  "device_id": "ESP32-SP-0912",
  "last_ping_at": "2026-07-17T17:10:00Z",
  "wifi_signal_rssi": "good",
  "firmware_version": "v1.2.3",
  "connectivity_status": "online",
  "unavailability_reason": null
}
```

---

## 4. Database: `db_delta_app`

### 4.1. `user_preferences`

Documento único por usuário, armazenando preferências de notificação, metas, tema e outras configurações.

| Campo                    | Tipo     | Obrigatório | Descrição                          |
|--------------------------|----------|-------------|------------------------------------|
| `_id`                    | ObjectId | Sim         | Identificador do documento         |
| `user_id`                | int      | Sim         | Usuário dono das preferências      |
| `daily_liters_target`    | double   | Não         | Meta diária de consumo             |
| `notifications_enabled`  | bool     | Não         | Liga/desliga notificações push     |
| `quiet_hours`            | objeto   | Não         | Janela de silêncio de alertas      |
| `quiet_hours.start_hour` | string   | Não         | Início do período (ex.: `"22:00"`) |
| `quiet_hours.end_hour`   | string   | Não         | Fim do período (ex.: `"06:00"`)    |
| `dark_mode_enabled`      | bool     | Sim         | Preferência visual do app          |

```json
{
  "_id": { "$oid": "60c72b2f9b1d8b2bad723b01" },
  "user_id": 212,
  "daily_liters_target": 300,
  "notifications_enabled": true,
  "quiet_hours": { "start_hour": "22:00", "end_hour": "06:00" },
  "dark_mode_enabled": false
}
```

### 4.2. `alerts_history`

Registro definitivo de cada anomalia disparada pela IA/regras de negócio — é o que o app renderiza na tela
de notificações do usuário.

| Campo          | Tipo      | Obrigatório | Descrição                                                         |
|----------------|-----------|-------------|-------------------------------------------------------------------|
| `_id`          | ObjectId  | Sim         | Identificador do documento                                        |
| `device_id`    | string    | Sim         | Dispositivo que originou o alerta                                 |
| `user_id`      | int       | Não         | Usuário notificado                                                |
| `alert_type`   | string    | Sim         | Ex.: `vazamento_continuo`, `fluxo_atipico`, `dispositivo_offline` |
| `triggered_at` | timestamp | Sim         | Momento de abertura do alerta                                     |
| `resolved_at`  | timestamp | Não         | Momento de resolução (`null` enquanto ativo)                      |
| `severity`     | enum      | Não         | `low` / `medium` / `high`                                         |

```json
{
  "_id": { "$oid": "60c72b2f9b1d8b2bad723b02" },
  "device_id": "ESP32-SP-0912",
  "user_id": 212,
  "alert_type": "vazamento_continuo",
  "triggered_at": "2026-07-17T03:12:00Z",
  "resolved_at": null,
  "severity": "high"
}
```

> **Coleção relacionada:** o motor de detecção (`delta-business-rules/detection/`)
> mantém, na mesma database, `user_hour_baseline` — um documento por `user_id`
> (`int`, mesma representação de `alerts_history.user_id`) + hora do dia, com a
> média/desvio de consumo daquele usuário naquele horário, atualizado de
> forma incremental. É estado interno do motor de detecção (não telemetria
> bruta nem dado consumido pelo app) — ver `detection/README.md`.

### 4.3. `chat_sessions`

Cada documento representa **uma sessão de chat completa** — não uma mensagem isolada. As mensagens
ficam embutidas em um array dentro do próprio documento (padrão *Bucket*).

| Campo                        | Tipo             | Obrigatório | Descrição                                              |
|------------------------------|------------------|-------------|--------------------------------------------------------|
| `_id`                        | ObjectId         | Sim         | Identificador da sessão                                |
| `user_id`                    | timestamp        | Sim         | Usuário dono da sessão                                 |
| `started_at`                 | timestamp        | Sim         | Início da sessão                                       |
| `last_activity_at`           | timestamp        | Sim         | Última interação                                       |
| `is_open`                    | bool             | Não         | Sessão aceita novas mensagens                          |
| `is_active`                  | bool             | Não         | Sessão em atendimento no momento                       |
| `is_deleted`                 | bool             | Não         | Soft delete (não remove o documento)                   |
| `messages[]`                 | array de objetos | Não         | Mensagens da sessão, em ordem cronológica              |
| `messages[].role`            | enum             | Sim         | `user` ou `bot`                                        |
| `messages[].content_type`    | enum             | Sim         | Tipo do conteúdo da mensagem (`text`, `function`)      |
| `messages[].content`         | string           | Sim         | Conteúdo da mensagem                                   |
| `messages[].sent_at`         | timestamp        | Sim         | Horário de envio                                       |
| `messages[].api_status_code` | int              | Sim         | Status retornado pela API de IA na geração da resposta |

```json
{
  "_id": { "$oid": "61a8f9c2b9d1b2bad723c001" },
  "user_id": 212,
  "started_at": "2026-07-17T14:00:00Z",
  "last_activity_at": "2026-07-17T14:05:00Z",
  "is_open": false,
  "is_active": false,
  "is_deleted": false,
  "messages": [
    { "role": "user", "content_type": "text", "content": "Por que meu consumo subiu tanto ontem?", "sent_at": "2026-07-17T14:00:05Z", "api_status_code": 200 },
    { "role": "bot", "content_type": "text", "content": "Identifiquei um fluxo contínuo de 2.8 LPM de madrugada. Pode ser um vazamento.", "sent_at": "2026-07-17T14:00:12Z", "api_status_code": 200 }
  ]
}
```

> ⚠️ **Limite de tamanho do array.** Recomenda-se travar `messages[]` em, no máximo, 50–100 entradas por
> sessão no código da aplicação. Ao atingir o limite, o back-end deve fechar a sessão (`is_open: false`) e abrir
> uma nova, evitando que o documento cresça indefinidamente e ultrapasse limites de leitura/gravação do
> MongoDB.

### 4.4. `chat_feedback`

Avaliação do usuário sobre uma sessão encerrada. Referencia `chat_sessions` por `session_id` — uma
referência lógica, não uma *foreign key* imposta pelo banco.

| Campo          | Tipo      | Obrigatório | Descrição                        |
|----------------|-----------|-------------|----------------------------------|
| `_id`          | ObjectId  | Sim         | Identificador do documento       |
| `session_id`   | ObjectId  | Sim         | Referência a `chat_sessions._id` |
| `is_satisfied` | bool      | Sim         | Avaliação binária (👍/👎)        |
| `user_comment` | string    | Não         | Comentário livre opcional        |
| `created_at`   | timestamp | Não         | Momento do envio do feedback     |

```json
{
  "_id": { "$oid": "61a8f9c2b9d1b2bad723c050" },
  "session_id": { "$oid": "61a8f9c2b9d1b2bad723c001" },
  "is_satisfied": true,
  "user_comment": "Resolveu minha dúvida rápido.",
  "created_at": "2026-07-17T14:06:00Z"
}
```

---

### 4.5. `weather_daily`

Histórico meteorológico permanente em `db_delta_app`: um documento agrupa até 24 observações horárias por localização e dia. Não há TTL.

#### Campos do schema atual

| Campo | Tipo BSON | Obrigatório | Regra |
| --- | --- | --- | --- |
| `_id` | objectId | Gerado pelo MongoDB | Identificador |
| `location` | object | Sim | Exige `city`, `state` e `country`, todos string |
| `weather_date` | date | Não | Data de referência normalizada para o início do dia |
| `hours` | array de objetos | Sim | No máximo 24 itens; pode estar vazio |
| `samples` | int | Sim | Entre 0 e 24 |
| `created_at` | date | Sim | Criação do documento |
| `updated_at` | date | Não | Última atualização |

Todos os campos abaixo são obrigatórios em cada item de `hours`:

| Campo | Tipo BSON | Regra |
| --- | --- | --- |
| `hour` | int | De 0 a 23 |
| `observed_at` | date | Momento da observação |
| `temperature_c` | double, int, long ou decimal | Temperatura em °C |
| `feels_like_c` | double, int, long ou decimal | Sensação térmica em °C |
| `humidity_percent` | int, long, double ou decimal | De 0 a 100 |
| `rain_mm` | double, int, long ou decimal | Maior ou igual a zero |
| `wind_speed_mps` | double, int, long ou decimal | Vento em m/s, maior ou igual a zero |
| `condition` | string | Sem enum definido no validator |

`date`, `wind_speed_m_s`, `wind_gust_m_s`, pressão, direção do vento e códigos meteorológicos não fazem parte dos campos definidos no schema atual. O validator não declara `additionalProperties: false`, portanto campos extras não são automaticamente rejeitados.

O produtor deve manter `samples == hours.length`, evitar horas repetidas e alinhar `observed_at` ao dia de referência. Essas relações não são verificadas pelo `$jsonSchema` atual. O schema também não exige `weather_date` nem um mínimo de observações.

#### Exemplo para mongosh

```javascript
db.weather_daily.insertOne({
  location: { city: "São Paulo", state: "SP", country: "BR" },
  weather_date: ISODate("2026-09-27T00:00:00Z"),
  hours: [{
    hour: NumberInt(0),
    observed_at: ISODate("2026-09-27T00:00:00Z"),
    temperature_c: 18.2,
    feels_like_c: 18.0,
    humidity_percent: NumberInt(82),
    rain_mm: 0.0,
    wind_speed_mps: 2.1,
    condition: "Clouds"
  }],
  samples: NumberInt(1),
  created_at: ISODate("2026-09-27T00:01:00Z")
});

db.weather_daily.find({
  "location.country": "BR",
  "location.state": "SP",
  "location.city": "São Paulo",
  weather_date: {
    $gte: ISODate("2026-09-01T00:00:00Z"),
    $lt: ISODate("2026-10-01T00:00:00Z")
  }
}).sort({ weather_date: -1 });
```

#### Índice: divergência pendente

O script de índices ainda cria `idx_location_date_unique`, único, sobre `{ "location.country": 1, "location.state": 1, "location.city": 1, date: -1 }`. O schema e o seed usam `weather_date`. Portanto, o índice atual não garante unicidade por `weather_date`: documentos sem `date` para a mesma localização podem colidir no índice mesmo em dias diferentes.

A intenção é garantir um documento por localização e dia, mas isso depende de alinhar o índice a `weather_date`. Esta atualização é documental e não modifica o script nem os índices de um banco existente.

---

## 5. Índices e Configurações de Coleção

| Coleção               | Índice                                  | Tipo                                    | Justificativa                                                                                                                                                                                                                                                                        |
|-----------------------|-----------------------------------------|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `consumption_summary` | `{ user_id: 1, window_started_at: -1 }` | Composto                                | Este é o índice mais crítico do database de telemetria: sustenta a leitura do histórico/gráfico de consumo do usuário no app, sempre ordenado por tempo.                                                                                                                             |
| `consumption_summary` | `{ device_id: 1 }`                      | Simples                                 | Consultas administrativas e de suporte por dispositivo, independente do usuário.                                                                                                                                                                                                     |
| `device_status`       | `{ device_id: 1 }`                      | **Único**                               | A coleção segue padrão *upsert* (um documento por dispositivo). O índice único é o que garante essa unicidade e viabiliza `updateOne({ device_id }, ..., { upsert: true })` sem duplicatas.                                                                                          |
| `alerts_history`      | `{ user_id: 1, triggered_at: -1 }`      | Composto                                | Alimenta a tela de notificações do app, sempre lida por usuário e ordenada por data.                                                                                                                                                                                                 |
| `alerts_history`      | `{ device_id: 1, resolved_at: 1 }`      | Composto (parcial, `resolved_at: null`) | Consulta rápida de "alertas ainda ativos" por dispositivo, sem varrer o histórico já resolvido.                                                                                                                                                                                      |
| `user_preferences`    | `{ user_id: 1 }`                        | **Único**                               | Cada usuário deve ter exatamente um documento de preferências; o back-end lê esse documento a cada pacote de telemetria processado para checar `quiet_hours`.                                                                                                                        |
| `chat_sessions`       | `{ user_id: 1, last_activity_at: -1 }`  | Composto                                | Lista de "atendimentos anteriores" do usuário, ordenada por atividade recente.                                                                                                                                                                                                       |
| `chat_sessions`       | `{ user_id: 1, is_open: 1 }`            | Composto                                | Localiza rapidamente uma sessão em aberto para decidir entre reabrir ou criar uma nova.                                                                                                                                                                                              |
| `chat_feedback`       | `{ session_id: 1 }`                     | Simples                                 | Suporta o cruzamento (via `$lookup` em agregação) entre sessão e sua avaliação, usado em métricas de satisfação do bot.                                                                                                                                                              |

---

## 6. Justificativas de Design

**Por que dois databases, e não um só ou três (como no rascunho com MongoDB/Postgres/Redis fundidos)?**
A separação entre `db_delta_telemetry` e `db_delta_app` isola dois perfis de carga completamente
diferentes — escrita massiva e constante vs. leitura esporádica orientada a usuário — e permite aplicar
*custom roles* distintas por database, reduzindo a superfície de ataque caso uma credencial vaze.

**Por que o hardware envia resumos de consumo?**
O hardware consolida as medições antes do envio, reduzindo o volume de dados. O MongoDB recebe diretamente as janelas em `consumption_summary`, com retenção permanente e sem coleção intermediária de pulsos ou TTL de sete dias.

**Por que `chat_sessions` embute as mensagens em vez de uma coleção `chat_messages` separada?**
Uma coleção com um documento por mensagem cresceria rápido demais e exigiria uma consulta com
paginação toda vez que o app abrisse uma conversa. O padrão *Bucket* (uma sessão = um documento, array
de mensagens embutido) resolve isso com uma única leitura por `_id`, ao custo de exigir um teto no
tamanho do array — daí a recomendação de 50–100 mensagens por sessão na seção 4.3.

**Por que `device_status` abandonou a ideia de usar `device_id` como `_id`?**
A proposta original (usar o identificador natural do dispositivo como `_id`) funcionaria, mas quebraria a
consistência de driver/ORM com as demais coleções, todas usando `ObjectId`. A modelagem oficial optou
por unicidade garantida via índice (`{ device_id: 1 }`, único) em vez de sobrescrever o `_id` padrão — troca
pequena, mas que evita tratamento especial nessa única coleção.

---

## 7. Diagrama de Referência

Fluxo atual de telemetria: **hardware → resumo da janela → API → `consumption_summary` → consultas do app e detecção de anomalias**. `device_status` mantém o estado atual do dispositivo.

O antigo arquivo `modelagem-delta.png` é uma referência histórica e não representa o contrato atual; consulte as tabelas deste documento.
