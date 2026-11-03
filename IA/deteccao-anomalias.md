# Detecção de anomalias e contrato de alertas

Este documento descreve a implementação local da migração do detector para o `delta-api-mongo` e seu contrato com a IA e o aplicativo. Conferência do código: 02/11/2026. Implementação local não significa implantação validada em produção.

**Fontes verificadas** (branches das PRs abertas em 02/11/2026; os commits podem mudar até o merge):

| Repositório | PR | Conteúdo | Último commit conferido |
|---|---|---|---|
| `delta-api-mongo` | #16 | detector (`modules/detection`) | [`c12c825`](https://github.com/delta-app-ofc/delta-api-mongo/commit/c12c825) |
| `delta-api-mongo` | #17 | API de alertas (`modules/alerts`) e integração com o detector | [`c056aa8`](https://github.com/delta-app-ofc/delta-api-mongo/commit/c056aa8) |
| `delta-mongo-database` | #14 | `user_hour_baseline`, campos de anomalia, migrações | [`ba86e4b`](https://github.com/delta-app-ofc/delta-mongo-database/commit/ba86e4b) |
| `delta-mongo-database` | #16 | contrato de `alerts_history` | [`a27d662`](https://github.com/delta-app-ofc/delta-mongo-database/commit/a27d662) |
| `delta-api-postgres` | #52 | rota interna do dono do dispositivo | `5a7364d` |

## Estado e responsabilidades

O detector e a API de alertas estão presentes no código Java e desligados por padrão. A habilitação depende das migrações e índices do MongoDB, das configurações do Render e da validação em ambiente integrado. A remoção de `delta-business-rules/detection/` e do `watcher.py` permanece planejada, condicionada à validação do novo fluxo em produção; não se deve manter dois detectores escrevendo alertas simultaneamente.

O detector decide as regras de consumo medido. O LeakAgent lê os resultados e explica os indícios, sem criar limiares ou afirmar uma causa física confirmada. O job diário da IA cuida das metas e previsões; o detector não consulta `user_preferences.daily_liters_target` nem a última conta de água. A IA usa a última conta somente como referência alternativa quando falta consumo medido; consumo registrado igual a zero não é ausência de dados.

## Fluxo implementado

1. A API insere a janela em `db_delta_telemetry.consumption_summary`. Uma janela duplicada retorna 409 antes de agendar detecção.
2. Com a detecção habilitada, o insert já contém `detection_status=pending`. Um worker busca até 100 pendências por rodada, ordenadas por `window_finished_at` e `_id`, fora da requisição HTTP. O POST só sinaliza trabalho, sem esperar espaço em fila. Uma varredura periódica recupera pendências após reinício.
3. O detector confere duração e ordem temporal, consulta o cadastro do dispositivo pela API Postgres com cache e timeout, aplica regras e atualiza o baseline em `db_delta_app.user_hour_baseline`.
4. O detector abre ou resolve alertas em `db_delta_app.alerts_history`. O resultado da janela é atualizado com evidências e versão.

Uma janela anterior ou igual à última processada não altera o baseline. Falhas de avaliação não desfazem o insert: são tratadas como resultado não avaliado. As pendências ficam em `consumption_summary`, com índice `idx_detection_pending`; resultado e `detection_status=completed` são gravados no mesmo update. Documentos antigos sem status não são reprocessados. A operação atual prevê uma réplica de detecção. Não há transação distribuída entre os clusters: uma falha após atualizar baseline/alertas e antes de salvar o resultado pode exigir reconciliação; esta implementação não promete processamento exatamente uma vez nessa situação.

## Resultado de consumo

| Campo | Significado |
| --- | --- |
| `anomaly_detected` | `true`: regras confirmadas; `false`: avaliado sem confirmação; `null`/ausente: não avaliado |
| `anomaly_reasons` | Identificadores das regras confirmadas |
| `anomaly_evidence` | Valores observados, contexto e evidências por regra |
| `detection_error` | Motivo de não avaliação ou erro registrado |
| `detector_version` | Versão do detector e de sua configuração |
| `detection_status` | `pending`: janela aguarda avaliação; `completed`: resultado persistido |

`null` nunca significa ausência de vazamento. Há uma divergência anterior à migração: a modelagem documenta `consumption_summary.user_id`, mas a ingestão Java persiste o dispositivo e não preenche esse campo. Esta migração não corrige a autorização de consultas de consumo da IA; isso requer tratamento próprio antes da integração.

## Baseline e regras

O baseline é identificado por `device_id`, com índice único em `(device_id, hour_of_week)`. Os slots de 0 a 167 representam a hora da semana no fuso configurado (`America/Sao_Paulo` por padrão); `-1` guarda o estado do dispositivo. `property_id` é contexto desnormalizado, não a chave. O código atual tem um fuso de configuração global; suporte a um fuso diferente por imóvel permanece pendente.

| Grupo de campos | Uso |
| --- | --- |
| `samples`, `median`, `mad`, `count` | Histórico aceito e estatísticas robustas por slot |
| `slow_ready` | Referência lenta promovida continua utilizável enquanto o histórico de amostras é reconstruído |
| `ewma_mean`, `ewma_var` | Adaptação rápida ao consumo recente |
| `night_floor_lpm`, `min_flow_median` | Referência de vazão mínima |
| `regime_state`, `regime_since`, `cusum_pos`, `cusum_neg` | Mudança persistente de nível e retorno |
| `rule_state`, `regime_acc`, `visit_until` | Contadores, acumulação horária e visita declarada |
| `last_window_finished_at`, `config_version`, `updated_at` | Controle de ordem e rastreabilidade |

Dias de operação identificam o dia em que o turno começa: segunda 22h–06h inclui terça 01h; fim de turno é exclusivo e horários iguais não significam 24h. O cache do dono tem limite de 1.000 dispositivos, remove expirados e usa TTL curto para falhas/cadastro ausente.

O fluxo contínuo considera janelas consecutivas com vazão pouco variável. O piso noturno se aplica a imóveis residenciais; o fluxo fora do expediente usa turnos e dias de operação comerciais obtidos do Postgres. Ausência de cadastro não autoriza presumir uma classificação ou emitir alerta para um usuário desconhecido.

O z-score usa mediana e MAD com fator 1,4826 e escala mínima para MAD zero, exigindo confirmação em janelas consecutivas. O rastreador de regime acumula resíduos por hora e percorre `NORMAL`, `CANDIDATE`, `SHIFTED` e `RETURNING`. Mantém referências rápida e lenta para permitir adaptação sem incorporar imediatamente um possível vazamento. Uma mudança sustentada pode ser promovida ao baseline após o período configurado. Cold start pode usar a coorte enquanto falta histórico próprio.

## Parâmetros e calibração

Os valores efetivos estão em `DetectionProperties`; `application.properties` expõe as configurações de ambiente. Os padrões atuais incluem:

| Parâmetro | Padrão |
| --- | --- |
| Janela / tolerância / lacuna máxima | 5 min / 30 s / 15 min |
| Amostras máximas / mínimas por slot | 28 / 4 |
| Z-score / escala mínima / confirmação | 4 / 5 litros / 4 janelas |
| Fluxo contínuo / coeficiente de variação máximo | 6 janelas / 0,35 |
| Período noturno / confirmação / vazão mínima | 00–05h / 3 janelas / 0,05 L/min |
| Regime: persistência / promoção / retorno | 24 h / 30 dias / 12 resíduos horários |
| Resolução de alertas | 36 janelas normais (3 h em cadência de 5 min) |
| Consulta de cadastro: timeout / cache | 2 s / 30 min |

`ScenarioCalibrationTest` e `SyntheticHome` simulam consumo com sementes fixas, residência normal, vazamentos, alterações de rotina e empresas. Resultados sintéticos não comprovam sensibilidade ou falso alarme em imóveis reais. Alterações nos limiares exigem executar a suíte e revisar `config_version`.

O código atual não oferece uma flag separada para cada regra avançada, busca em grade nem fixtures JSON de paridade com o detector Python. Esses itens do plano permanecem pendentes; a suíte sintética existente não deve ser descrita como se os cobrisse.

## Contrato de alertas

Todos usam `alerts_history`. O detector escreve diretamente pelo fluxo de detecção; IA e sistema devem usar o endpoint interno da API Mongo. Não há uma segunda coleção de alertas.

| `alert_type` | `source` | Severidade |
| --- | --- | --- |
| `vazamento_continuo` | `detector` | `high` |
| `fluxo_atipico` | `detector` | `medium` |
| `consumo_fora_do_expediente` | `detector` | `high` |
| `mudanca_padrao` | `detector` | `low` |
| `consumo_acima_esperado`, `previsao_ultrapassagem_meta`, `previsao_conta_disponivel`, `dica_personalizada` | `gluh` | `low` ou `medium` |
| `limite_ultrapassado` | `gluh` | `low`, `medium` ou `high` |
| `tarifa_atualizada` | `gluh` ou `system` | `low` ou `medium` |

A exceção de `high` para `limite_ultrapassado` foi confirmada em 02/11/2026 e substitui a proibição geral do plano anterior. `dispositivo_offline` e `leitura_impossivel` continuam no enum do banco, sem escritor neste fluxo.

| Campo | Contrato |
| --- | --- |
| `user_id` | Destinatário; um alerta do detector para cada usuário associado ao imóvel |
| `device_id`, `property_id` | Contexto; dispositivo não é obrigatório para alertas da IA/sistema |
| `alert_type`, `severity`, `source` | Tipo, prioridade e escritor |
| `title`, `message` | Texto do detector por template pt-BR |
| `rule`, `evidence`, `window_id` | Regra e evidências quando disponíveis |
| `triggered_at`, `resolved_at`, `dismissed_at` | Criação, encerramento da condição e dispensa visual |
| `dedup_key` | Unicidade entre alertas abertos, garantida por índice parcial |

A chave do detector é `detector:{deviceId}:{rule}:{userId}`. Internos usam prefixos `gluh:{userId}:` ou `system:`. Repetir uma criação com chave aberta devolve o alerta existente. Encerrar libera a chave para um novo episódio; dispensar não encerra a condição.

Evidências de vazamento incluem `lpm`, `duration_minutes` e `liters_per_day_estimate`; comparações podem incluir `value`, `baseline`, `pct` e período. A projeção de litros/dia não é um volume já desperdiçado. O contrato não inclui custo em reais, pressão da rede ou identificação de cômodo.

O alerta informativo de regime é separado da confirmação de anomalia. O código atual o gera para subida de rotina sem suspeita recente de vazamento; uma visita declarada não dispara esse alerta. A intenção mais ampla do plano de notificar também visita confirmada precisa ser conciliada antes de declarar esse caso entregue.

## API e autenticação

| Método e rota | Autenticação e comportamento |
| --- | --- |
| `GET /api/alerts` | JWT; paginação, filtro `severity` e `include_dismissed=false` |
| `PATCH /api/alerts/{id}/dismiss` | JWT; só o dono, idempotente; outro usuário recebe 404 |
| `GET /api/alerts/leak-summary` | JWT; litros/dia e dispositivos, sem R$ |
| `POST /api/internal/alerts` | `X-Service-Key`; 201 ao criar, 200 se chave aberta já existe |
| `POST /api/internal/alerts/resolve` | `X-Service-Key`; encerra por `dedup_key` dos prefixos `gluh:` e `system:`; alertas do detector são encerrados pelo próprio detector |

O nome implementado do parâmetro é `include_dismissed`, diferente de `includeDismissed` no plano inicial. O resumo inclui alertas de vazamento abertos e aqueles disparados nas últimas 24 h, contando cada dispositivo uma vez pela maior estimativa.

A validação JWT atual usa Nimbus com filtros próprios, RS256, chave pública RSA, emissor, audiência, expiração, emissão e `nbf`; o plano sugeria `spring-boot-starter-oauth2-resource-server`, ainda não adotado. O usuário vem exclusivamente do `sub` autenticado. Telemetria e status mantêm o contrato anterior.

`DELTA_DETECTION_OWNER_SERVICE_KEY` copia a `AUTH_SERVICE_KEY` da API Postgres. `ALERTS_SERVICE_KEY` é outra chave, compartilhada apenas com os escritores internos autorizados. Configurar `AUTH_PUBLIC_KEY`, `AUTH_ISSUER` e `AUTH_AUDIENCE` com os valores do back-end. Exemplos usam valores fictícios; segredos ficam fora de Git e desta documentação. Push/e-mail e horário silencioso são responsabilidade do componente de notificação.

## Impacto na IA e implantação

O LeakAgent deve ler os campos de detecção de `consumption_summary` e `rule`, `evidence`, `title` e `message` em `alerts_history`. Deve distinguir anomalia confirmada pela regra de hipótese de causa e informar falta de avaliação. O ConsumptionAgent continua descrevendo consumo observado; um pico diário não equivale a vazão atípica detectada por janela.

Antes de remover o motor antigo: aplicar e testar migrações/índices, habilitar conexões e autenticação, verificar POST real e repetido, conferir baseline e deduplicação por usuário e validar a leitura pela IA/app. Remoção do watcher e do módulo Python somente após essa comprovação. Este documento não certifica merge de PRs, configuração no Render ou produção.

## Referências

Veja [a tabela de referências e sua conferência](deteccao-anomalias-referencias.md). O fator robusto segue o identificador de Hampel; CUSUM, acompanhamento de visitas e coortes residenciais são decisões de projeto, não algoritmos residenciais validados pelas fontes listadas. A conferência encontrou links que não sustentam a descrição do plano original; esses limites estão registrados na tabela.

## Atualização de uma instalação existente

Execute as migrações de `consumption_summary`, `alerts_history` e `user_hour_baseline`, antes dos índices
nos respectivos clusters. `script-migrate-user-hour-baseline.js` cria a coleção já validada quando ausente,
ou atualiza seu validator sem apagar os documentos. A conta do serviço precisa de `listIndexes` para as
verificações de inicialização; criação/alteração de schema e índices é responsabilidade administrativa.
As instruções operacionais estão em `delta-mongo-database/QUICK_START.md`.
