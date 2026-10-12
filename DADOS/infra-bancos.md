# Documento de Arquitetura e Modelagem de Dados
Este documento descreve as especificações técnicas de infraestrutura de informações geradas pelo Arduino, 
modelagem e tráfego de dados para o sistema de monitoramento de consumo de água via telemetria IoT. 
A arquitetura foi planejada para garantir escalabilidade, segurança e eficiência computacional, 
dividindo as responsabilidades entre MongoDB, Redis e PostgreSQL.
OBS.: Este documento **não** abrange a modelagem de todos os dados que transitarão na aplicação, apenas as informações de telemetria IoT.

## Diagrama de Arquitetura de Fluxo de Dados
Fluxo atual: **hardware → janela consolidada → API → MongoDB (`consumption_summary`) → app / detecção / agregações**.

O arquivo `diagrama-infra.png` pertence ao desenho anterior e não representa o contrato atualizado; use o fluxo acima e a modelagem oficial.

## 1. Comunicação de Borda (Arduino Uno R4 Wifi/ESP32-C3 Super Mini)
Para mitigar problemas de concorrência e sobrecarga no servidor de aplicação, 
o hardware do Arduino consolidará as medições magnéticas localmente em lotes temporais (janelas de 5 a 10 minutos) 
e utilizará uma estratégia de escalonamento (Load Leveling/Jittering) para envio das requisições.

### 1.1. Payload consolidado do hardware

O hardware calcula o consumo antes do envio e transmite diretamente uma janela destinada a `consumption_summary`. A API autentica o dispositivo, associa o `user_id` cadastrado e converte datas e números para os tipos BSON do validator.

```json
{
  "device_id": "ESP32-SP-0912",
  "window_started_at": "2026-06-21T17:05:00Z",
  "window_finished_at": "2026-06-21T17:10:00Z",
  "consumption_liters": 14.0,
  "lpm_average": 2.8
}
```

## 2. Ingestão no Back-end

A conversão dos pulsos em litros é responsabilidade do hardware, conforme a calibração do hidrômetro. Não há persistência intermediária de pulsos brutos. A API persiste `device_id` (string), `user_id` (int), início/fim da janela (date), `consumption_liters` (double) e, quando enviado, `lpm_average` (double). `anomaly_detected` é opcional e pode ser atualizado pela detecção de anomalias após a ingestão.

O contrato de persistência está em [Modelagem MongoDB](NoSQL/modelagem-mongodb.md). Os exemplos representam a decisão de arquitetura, sem comprovar uma integração HTTP ou firmware executados.

## 3. Infraestrutura e Modelagem MongoDB (NoSQL)
O MongoDB é o nosso banco de ingestão de alta performance (write-heavy), responsável por armazenar todo 
o histórico analítico e logs que alimentarão o motor de inteligência artificial.

### 3.1. Collections Necessárias
#### A. Collection: `consumption_summary`

Coleção convencional com `$jsonSchema` e índices por usuário/tempo e dispositivo. Guarda permanentemente as janelas consolidadas pelo hardware, sem TTL. Os scripts atuais não a criam como Time-Series. `device_status` mantém o estado atual de cada dispositivo. Consulte a [modelagem oficial](NoSQL/modelagem-mongodb.md) para os campos e índices.

#### B. Collection: historico_ia_treino
Armazena as conclusões e padrões de rotina gerados periodicamente pela inteligência artificial para cada usuário.

```javascript
{
  "_id": ObjectId("61a8c9b2f1d8b2bad7239999"),
  "usuario_id": "60c72b2f9b1d8b2bad723456",
  "faixas_rotina": {
    "madrugada_00_06": { "max_recomendado_litros": 5.0, "desvio_padrao": 1.2 },
    "manha_06_12": { "max_recomendado_litros": 45.0, "desvio_padrao": 5.5 },
    "tarde_12_18": { "max_recomendado_litros": 30.0, "desvio_padrao": 4.1 },
    "noite_18_00": { "max_recomendado_litros": 60.0, "desvio_padrao": 8.0 }
  },
  "ultima_atualizacao": "2026-06-21T02:00:00Z"
}
```

## 4. Infraestrutura e Comandos Redis (In-Memory)
O Redis atua como o motor de tempo real do sistema. Ele impede que o fluxo contínuo do IoT onere os bancos persistentes (Mongo/Postgres).

### 4.1. Ranking de Performance (Sorted Sets)
Para exibir o ranking de economia na Web de forma instantânea, usamos a estrutura ZSET. 
O score armazenado será o consumo acumulado no mês (quanto menor o consumo, melhor a posição no ranking).

- Adicionar/Atualizar consumo do usuário no ranking mensal:

```redis
# Incrementa o score (consumo) do usuário no ranking de Junho/2026
ZINCRBY ranking:agua:202606 14 "user_id_60c72b2f"
```

- Buscar o TOP 10 usuários mais econômicos (menor consumo):
```redis
# Retorna os usuários ordenados do menor consumo para o maior
ZRANGE ranking:agua:202606 0 9 WITHSCORES
```

### 4.2. Cache de Regras de Alerta da IA (Evitando gargalo no MongoDB)

> ⚠️ **Design anterior, não implementado.** O que foi de fato implementado
> (`delta-nosql-database`, `delta-business-rules/detection/`) é diferente do
> descrito nesta seção 4.2 e na tabela `alertas_vazamentos` (seção 5.1)
> abaixo: os alertas ficam em **MongoDB** (`db_delta_app.alerts_history`, ver
> `DADOS/NoSQL/modelagem-mongodb.md`), não em Postgres via cache de limites no
> Redis. Quem calcula o indício de vazamento é o motor de detecção
> (`detection/`, regras explicáveis, sem modelo de ML), não uma checagem de
> `limite:madrugada` fixo por usuário no Redis. Esta seção fica como registro
> histórico da ideia original — não trate como implementada sem conferir o
> código real (mesmo aviso do `AGENTS.md` deste repositório sobre Redis).

Para evitar que cada payload recebido execute um find() no MongoDB buscando a rotina de consumo, 
o Back-end carrega as metas e limites do usuário direto no cache do Redis. A verificação do alerta 
se torna uma operação extremamente rápida de leitura de memória (GET).

- Armazenar limites de segurança definidos pela IA (atualizado uma vez por dia ou semana):
```redis
SET limite:madrugada:60c72b2f "5.0"
```

- Verificação em milissegundos no Back-end:
```javascript
// Lógica no Back-end ao receber dado de madrugada (ex: 3h AM)
const limiteMaximo = await redis.get(`limite:madrugada:${usuarioId}`);
if (payload.consumo_litros > parseFloat(limiteMaximo)) {
    dispararAlertaExcesso();
}
```

### 4.3. Gerenciamento de Sessão e Recuperação de Senhas (TTL)
Tokens de recuperação de senha usam o tempo de expiração nativa do Redis (Time-To-Live) para autolimpeza da memória.
```redis
# Define o token de redefinição de senha com validade estrita de 15 minutos (900 segundos)
SET token:recuperar:user_60c72b2f "982134" EX 900
```

## 5. Infraestrutura PostgreSQL (Relacional)
O PostgreSQL é a âncora relacional da aplicação. Ele é responsável por manter a integridade transacional 
de dados cadastrais e o consumo consolidado para os Dashboards Web.

### 5.1. DDL Crítico para Dashboards e Relatórios Rápidos
#### Tabela: dashboard_consumo_diario
Tabela atualizada por um processo assíncrono (Cron Job / Background Worker) que lê as janelas consolidadas de `consumption_summary` uma vez ao dia e salva o resumo estruturado no PostgreSQL para consulta instantânea do Frontend Web.

```sql
CREATE TABLE dashboard_consumo_diario (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(24) NOT NULL, -- Referência ID do Mongo/Auth
    data_consolidada DATE NOT NULL,
    consumo_total_litros NUMERIC(10, 2) NOT NULL,
    media_vazao_lpm NUMERIC(5, 2),
    alerta_disparado BOOLEAN DEFAULT FALSE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuario_data UNIQUE (usuario_id, data_consolidada)
);

CREATE INDEX idx_dash_usuario_data ON dashboard_consumo_diario(usuario_id, data_consolidada);
```

#### Tabela: alertas_vazamentos

> ⚠️ **Não implementada — ver nota da seção 4.2.** O alerta real fica em
> `db_delta_app.alerts_history` (MongoDB), não nesta tabela Postgres.

Para alimentar a área de auditoria e controle de anomalias na aplicação Web, esta tabela registra todos os alertas confirmados pelo processamento de eventos do Redis.

```sql
CREATE TABLE alertas_vazamentos (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(24) NOT NULL,
    data_alerta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tipo_alerta VARCHAR(50) NOT NULL, -- 'EXCESSO_MADRUGADA', 'GARGALO_VAZAMENTO_DIRETO'
    volume_registrado_litros NUMERIC(10, 2) NOT NULL,
    status_resolvido BOOLEAN DEFAULT FALSE,
    resolvido_em TIMESTAMP WITH TIME ZONE
);
```

## 🛠️ Resumo Técnico das Responsabilidades
| Tecnologia | Responsabilidade Principal | Justificativa Técnica |
|------------|---------------------------|-----------------------|
| MongoDB    | Janelas consolidadas de consumo, histórico analítico, IA e os alertas de vazamento reais (`alerts_history` — ver aviso da seção 4.2). | Coleções convencionais com validators e índices definidos nos scripts MongoDB. |
| Redis      | Rankings Web e controle de Sessões/TTL. Cache de limites da IA é design antigo, não implementado (ver aviso da seção 4.2). | Uso de Sorted Sets para ordenação sem CPU-bound e verificação direta em memória RAM. |
| PostgreSQL | Cadastro (CRUD) e Tabelas de Consumo Consolidado. Auditoria de Alertas é design antigo, não implementado (ver aviso da seção 4.2). | Indexes compostos nas chaves estrangeiras e datas. Dados agregados de forma assíncrona. |
