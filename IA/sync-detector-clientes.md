# Sincronização do detector e clientes

A API Mongo resolve o proprietário na rota interna da API Postgres antes de
persistir telemetria. Sem vínculo, responde 404; sem consulta confiável, 503.
O hardware continua enviando apenas o dispositivo e as medições.

## Escritas

| Escritor | Coleção | Campos |
| --- | --- | --- |
| Ingestão | db_delta_telemetry.consumption_summary | user_id obrigatório, user_ids, property_id e medições |
| Detector Java | db_delta_telemetry.consumption_summary | anomaly_detected, anomaly_reasons, anomaly_evidence, detection_error, detector_version, detection_status |
| Detector Java | db_delta_app.user_hour_baseline | cohort_key, estatísticas e regime; visit_until, visit_updated_by, visit_updated_at no estado de slot -1 |
| Detector/API interna | db_delta_app.alerts_history | source, severity, dedup_key, property_id, device_id opcional, title, message, evidence, resolved_at |
| Web/Android via API | db_delta_app.alerts_history | dismissed_at do usuário autenticado |
| Job IA via API interna | db_delta_app.alerts_history | alertas gluh por usuário/tipo/período |

Não há nova coleção, tabela SQL, escrita em tb_last_water_bill nem alteração de
firmware. Em imóvel compartilhado, user_id recebe o menor ID vinculado para
compatibilidade; user_ids preserva todos os usuários. O cadastro SQL é a origem
destes campos, inclusive property_id.

## Habilitação

1. Aplicar schemas, migrações de baseline/alertas/anomalias e índices antes do
   backend. Atualizar a role existente com listIndexes. Criar coleções não altera
   validators que já existem. Auditar duplicados antes de criar índices únicos.
2. Publicar a rota interna de proprietário no Postgres. AUTH_SERVICE_KEY nele
   deve coincidir com DELTA_DETECTION_OWNER_SERVICE_KEY no Mongo.
   DELTA_DETECTION_OWNER_URL aponta para a raiz da API Postgres.
3. Configurar MONGODB_TELEMETRY_URI, MONGODB_APP_URI e nomes dos bancos no Mongo.
   Habilitar DELTA_DETECTION_ENABLED e DELTA_ALERTS_ENABLED. AUTH_PUBLIC_KEY
   deve corresponder à chave que assina o JWT do Postgres, com mesmo issuer e
   audience. A chave pública não substitui a chave de serviço.
4. IA: ALERTS_API_URL aponta para a raiz da API Mongo e ALERTS_SERVICE_KEY deve
   coincidir com a variável homônima do Mongo. Pode ser uma chave diferente da
   usada entre Postgres e Mongo. Nenhuma chave de serviço vai para web ou APK.
5. Web: VITE_MONGO_API_URL e DELTA_ALLOWED_ORIGINS no Mongo com a origem da web.
   O login e refresh continuam em VITE_POSTGRES_API_URL. Android: deltaMongoApiUrl
   no debug e deltaMongoReleaseApiUrl HTTPS no release.
6. Operar uma réplica do detector nesta etapa. Validar em produção com usuário
   e medidor de teste: ingestão 201, reenvio 409, janela completed, alerta
   persistido, isolamento entre usuários e visita auditada. Somente depois
   integrar a remoção do detector Python. Esta branch não comprova o cutover.

## Ensaio local

O script scripts/run-sync-local.ps1 no delta-api-mongo cria PostgreSQL 16 e
MongoDB 7 descartáveis, provisiona validators/índices, compila o JAR Mongo e
executa ApiSyncPostgresIntegrationTest no Postgres. Informar JavaHome e MavenHome;
os três repositórios devem estar nas branches correspondentes da entrega.
O teste usa HTTP real, RSA temporária e usuários exclusivos. O schema Postgres
é criado pelas entidades JPA; o ensaio não certifica as migrações SQL completas,
funções analíticas, Redis ou a infraestrutura Render. Não conecta a produção.

## Contratos adicionais

GET /api/detection/devices/{deviceId}/evidence fornece série medida e evidências
persistidas. Aceita start/end, até sete dias e 100 janelas por página.
PUT /api/detection/devices/{deviceId}/visit recebe visit_until ISO UTC ou null,
com prazo máximo de 90 dias. Exige vínculo atual e registra autor/data.
Não desativa regras de vazamento. A web oferece formulário de visita; no Android a rota está disponível no cliente, sem formulário nesta etapa.

A coorte usa classificação, tipo do imóvel e região. Sem perfil, aguarda histórico
próprio. Documentos antigos sem cohort_key só entram na coorte após atualização.

O perfil Maven calibrate executa GridCalibrationTest e gera calibration-grid.csv
e detector-config-candidate.properties em target. São 24 combinações com seed 42,
duas casas sintéticas, 14 dias de aquecimento e sete de avaliação. Precision/recall
são por janela; false_house_weeks indica uma casa normal com qualquer falso alarme
na semana. A amostra não comprova taxa populacional e o candidato não é aplicado
automaticamente. Fixtures JSON registram diferenças intencionais perante o Python.

Na IA, scripts/generate_alerts.py é dry-run por padrão; --execute escreve na API
interna. Usuários vêm do cadastro ativo SQL e o escopo é verificado individualmente.
Lotes de 100 e concorrência de 1 a 16 isolam falhas. Templates não chamam LLM e
nunca declaram vazamento. O resumo JSON registra execução, propostas, criados,
falhas, duração e custo LLM zero. Agendamento e coleta pela observabilidade
dependem do deploy. O job não entrega notificações; o dispatcher deve aplicar
notifications_enabled e quiet_hours ao enviar push/e-mail.

A última conta é alternativa somente sem consumo medido. Zero é medição.
Sem tarifa e com medições, a previsão monetária fica indisponível.
