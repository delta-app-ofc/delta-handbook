### MOD-04 — Orquestrar RPA para mover dados do banco legado ao novo normalizado, garantindo integridade e tratamento de falhas de carga

**Evidência direta:**

- [Repositório delta-rpa](https://github.com/delta-app-ofc/delta-rpa)
- [README — documentação da migração](https://github.com/delta-app-ofc/delta-rpa/blob/main/README.md)
- [Orquestração principal do RPA](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/main.py)
- [Módulo de extração](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/extraction.py)
- [Módulo de validação](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/validation.py)
- [Módulo de transformação](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/transformation.py)
- [Módulo de carga e sincronização](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/load.py)
- [Persistência do mapa de identificadores](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/state.py)
- [Registro das execuções](https://github.com/delta-app-ofc/delta-rpa/blob/main/app/modules/execution_log.py)
- [Testes automatizados](https://github.com/delta-app-ofc/delta-rpa/tree/main/tests)
- [Ambiente de integração com Docker](https://github.com/delta-app-ofc/delta-rpa/blob/main/docker-compose.test.yml)
- [Workflow de testes e integração contínua](https://github.com/delta-app-ofc/delta-rpa/blob/main/.github/workflows/test.yml)
- [Workflow de execução automatizada do RPA](https://github.com/delta-app-ofc/delta-rpa/blob/main/.github/workflows/rpa.yml)
- [Execução #44 do RPA no GitHub Actions: sucesso](../anexos/evidencias-requisitos/mod-04-rpa-execucao-github-actions.png)
- [Log da execução: extração, validação, transformação, carga e COMMIT](../anexos/evidencias-requisitos/mod-04-rpa-log-execucao.png)

**Localização e como comprovar:**

A implementação está no repositório `delta-rpa`, desenvolvido em Python, responsável por orquestrar a migração entre dois bancos PostgreSQL: o banco legado do Primeiro Ano e o novo banco normalizado do Segundo Ano.

O processo utiliza SQLAlchemy para conexão com os bancos, Pandas para manipulação dos registros e um pipeline ETL composto por quatro etapas principais: extração, validação, transformação e carga. A execução completa é centralizada no arquivo `app/main.py`, que coordena os módulos, registra os resultados e trata exceções.

#### 1. Conexão e extração dos dados (Extract)

O módulo `app/database/connections.py` estabelece conexões independentes com os dois bancos PostgreSQL, utilizando variáveis de ambiente para configurar hosts, portas, nomes dos bancos e credenciais.

A extração é realizada em `app/modules/extraction.py`, por meio de consultas SQL executadas com `pandas.read_sql`, que retornam os registros em DataFrames para processamento.

O RPA possui uma lista de tabelas permitidas (`ALLOWED_TABLES`), evitando consultas a estruturas não autorizadas e restringindo a extração ao conjunto definido para a migração:

- `tb_user`;
- `tb_address`;
- `tb_property`;
- `tb_user_property`;
- `tb_device`;
- `tb_user_habit`;
- `tb_user_habit_day`;
- `tb_last_water_bill`.

Também foi implementada uma compatibilização inicial dos nomes das colunas entre os dois modelos. Por exemplo, `user_name` passa a ser `name`, `user_password` passa a ser `password`, `bill_month` passa a ser `month` e `adress_state` passa a ser `state`.

Essa etapa permite trabalhar com uma estrutura padronizada nas fases seguintes, mesmo quando o banco legado utiliza nomes diferentes dos adotados no novo modelo.

#### 2. Validação e integridade dos registros (Validate)

Após a extração, os dados passam pelo módulo `app/modules/validation.py`, que aplica regras de negócio e verificações de consistência antes da inserção no banco de destino.

As regras são organizadas em três configurações principais:

- `RULES`: validações específicas de negócio;
- `UNIQUE_COLUMNS`: identificação de combinações que não podem apresentar duplicidade;
- `FOREIGN_KEYS`: verificações de integridade referencial entre as tabelas extraídas.

Entre as validações implementadas estão:

- Idade mínima de 18 anos para usuários;
- Valores permitidos para os tipos de imóveis;
- Verificação de que as datas das contas de água representem o primeiro dia do mês;
- Identificação de registros duplicados por meio das combinações de colunas configuradas como únicas;
- Verificação da existência dos registros referenciados pelas chaves estrangeiras, quando as tabelas relacionadas estão disponíveis no conjunto extraído.

Um tratamento importante ocorre nas relações entre as tabelas. Quando um registro possui uma FK inválida, ele é removido do conjunto válido. A verificação é repetida até que não existam mais referências órfãs entre os DataFrames validados.

Por exemplo, se um imóvel for removido por apresentar algum problema de integridade, uma associação em `tb_user_property` que dependa desse imóvel também será identificada e removida do conjunto destinado à carga.

Os registros inválidos são separados e contabilizados, enquanto os válidos seguem para a transformação. Isso impede que dados incompatíveis sejam enviados diretamente ao novo banco.

#### 3. Transformação e adequação ao novo modelo (Transform)

A etapa de transformação está implementada em `app/modules/transformation.py`, responsável por converter os dados legados para os formatos, identificadores e padrões esperados pelo banco normalizado.

As transformações são configuradas individualmente por tabela, considerando as diferenças entre os modelos de origem e destino.

Entre os principais exemplos estão:

**Padronização textual:**

- Conversão de nomes, e-mails, cidades e estados para letras maiúsculas;
- Padronização dos dados cadastrais para evitar inconsistências de formatação.

**Compatibilização de classificações:**

- Substituição de `APARTAMENTO` por `PRÉDIO`, conforme o domínio de valores do novo banco;
- Conversão de classificações textuais para identificadores de `tb_property_classification`;
- Mapeamento de `RESIDENCIAL` para o identificador 1 e `COMERCIAL` para o identificador 5;
- Renomeação da coluna `classification` para `classification_id`.

**Adequação geográfica:**

Os identificadores de regiões antigas 4, 12 e 13 são convertidos para o identificador 1, correspondente a `GRANDE_SP` no modelo de destino, conforme o mapeamento definido no código.

**Segurança das credenciais:**

As senhas dos usuários são convertidas para hashes utilizando Argon2id, com parâmetros compatíveis com o mecanismo de autenticação da API Delta. Caso o valor já esteja no formato Argon2, ele é preservado para evitar gerar hash sobre outro hash.

**Compatibilização de dispositivos:**

O identificador físico de `tb_device` é convertido de numérico para texto, pois o legado utiliza um tipo numérico enquanto o novo banco utiliza `VARCHAR(100)`.

**Formatação dos telefones:**

Os números são padronizados para o formato brasileiro quando possuem dez ou onze dígitos, preservando os demais valores quando não se enquadram nos formatos reconhecidos.

Essas transformações permitem que informações que anteriormente eram armazenadas como texto livre ou em formatos diferentes sejam convertidas para a estrutura esperada pelo novo banco.

#### 4. Carga, sincronização e remapeamento de identificadores (Load)

A etapa de carga está implementada em `app/modules/load.py` e representa uma das partes mais importantes do RPA.

O processo utiliza `LOAD_PRIORITY` para organizar a inserção de acordo com as dependências entre as tabelas, carregando primeiro as entidades necessárias para as relações posteriores.

A ordem configurada é:

1. `tb_user`;
2. `tb_address`;
3. `tb_property`;
4. `tb_user_property`;
5. `tb_device`;
6. `tb_user_habit`;
7. `tb_user_habit_day`;
8. `tb_last_water_bill`.

Essa organização permite que os registros dependentes sejam inseridos depois das entidades referenciadas, respeitando as FKs do novo modelo.

**Mapeamento de IDs antigos e novos**

Como os bancos possuem identificadores próprios, o RPA não presume que o ID do legado seja igual ao ID gerado no banco novo.

Para solucionar isso, foi implementado um mapa de identificadores em `state/id_map.json`, que armazena a correspondência entre o ID de origem e o ID de destino de cada registro.

Por exemplo:

- Usuário com ID 15 no legado;
- Usuário com ID 103 no banco novo;
- O mapa registra `15 → 103`.

Quando outro registro utiliza o usuário 15 como chave estrangeira, o RPA consulta o mapa e substitui o identificador pelo 103 antes da carga.

Esse mecanismo é aplicado por `_replace_foreign_keys()`, permitindo preservar os relacionamentos mesmo quando os identificadores gerados pelos dois bancos são diferentes.

As tabelas de referência que não são migradas pelo RPA, como regiões, hábitos, dias da semana e classificações, mantêm seus identificadores originais. Essa estratégia considera que esses cadastros já estão previamente disponíveis no banco novo com identificadores compatíveis.

**Inserção e atualização (UPSERT)**

O processo diferencia registros novos de registros que já foram migrados:

- Quando o ID do legado já existe no mapa, o registro correspondente no banco novo é atualizado.
- Quando ainda não existe no mapa, o registro é inserido e o novo ID é armazenado.
- Para tabelas com chaves naturais, é utilizado `INSERT ... ON CONFLICT DO UPDATE`, como mecanismo adicional para evitar duplicações e reconciliar registros já existentes.

Dessa forma, o RPA realiza sincronização entre os bancos, e não apenas uma importação pontual.

**Replicação de exclusões**

Também foi implementado um mecanismo para identificar registros excluídos no banco legado.

A execução compara os IDs extraídos na execução atual com os identificadores armazenados no mapa. Quando um registro anteriormente migrado deixa de existir na origem, sua exclusão é replicada no banco de destino.

Essa operação respeita a ordem inversa de `LOAD_PRIORITY`, removendo primeiro os registros dependentes e depois suas respectivas entidades de origem.

O processo não realiza exclusões no banco legado: ele apenas sincroniza o destino com as alterações identificadas na origem.

#### 5. Transações e tratamento de falhas

A carga inteira, incluindo exclusões, inserções e atualizações, ocorre dentro de uma única transação PostgreSQL, implementada por `connection.begin()`.

Isso garante que uma falha durante qualquer operação de escrita interrompa a transação e provoque `ROLLBACK`, evitando deixar o banco novo parcialmente atualizado.

O mapa de IDs só é salvo depois do `COMMIT`. Uma falha na gravação desse arquivo não desfaz a transação já confirmada: o banco pode ter sido atualizado mesmo que a execução seja registrada com erro. Extração, validação, transformação e registro de execução também ficam fora da transação de carga.

O módulo `app/modules/state.py` utiliza um arquivo temporário e a operação `os.replace()` para atualizar o JSON. Isso evita corromper o arquivo anterior caso a gravação seja interrompida durante sua atualização.

Esses mecanismos preservam a correspondência entre os bancos e evitam atualizar o estado local quando a carga não foi concluída com sucesso.

#### 6. Logs, monitoramento e rastreabilidade

O RPA possui dois mecanismos complementares de registro das execuções.

**Logs técnicos:**

O módulo `app/modules/logs.py` registra as etapas em console e em arquivos diários, seguindo o padrão `logs/rpa_AAAA-MM-DD.log`.

São registrados:

- Início e término da execução;
- Quantidade de registros extraídos;
- Quantidade de registros válidos e inválidos;
- Quantidade de registros transformados;
- Inserções, atualizações e exclusões;
- Confirmação de `COMMIT` ou ocorrência de `ROLLBACK`;
- Mensagens de erros e suas exceções.

**Histórico no PostgreSQL:**

O módulo `app/modules/execution_log.py` registra cada execução na tabela `tb_log_rpa` do banco de destino.

O registro começa com status `RUNNING` e, ao final, recebe:

- `started_at`: início da execução;
- `finished_at`: término;
- `status`: resultado da execução (`SUCCESS` ou `ERROR`);
- `inserted_count`: total inserido;
- `updated_count`: total atualizado;
- `deleted_count`: total excluído;
- `validation_error_count`: erros encontrados na validação;
- `error_message`: descrição da falha, quando existente.

O registro de início e o encerramento são realizados em transações independentes da transação de carga. Assim, uma falha na migração não impede que o resultado da execução seja registrado no banco, desde que a conexão de monitoramento continue disponível.

O `main.py` também captura exceções e registra o encerramento com status de erro, sem ocultar a falha original do processo.

#### 7. Orquestração e automação da execução

Toda a sequência é centralizada em `app/main.py`, que controla a ordem das etapas e consolida os resultados.

O fluxo executado é:

1. Inicialização dos logs e abertura do registro da execução.
2. Extração dos dados do banco legado.
3. Identificação dos IDs existentes na origem.
4. Validação dos registros.
5. Transformação dos dados válidos.
6. Carga e sincronização no banco novo.
7. Consolidação dos contadores e finalização do registro de execução.

A automação também está configurada no GitHub Actions por meio de `.github/workflows/rpa.yml`, permitindo execução manual (`workflow_dispatch`) ou programada diariamente (`schedule`).

O projeto possui ainda um workflow de integração contínua em `.github/workflows/test.yml`, que executa os testes automatizados e o ambiente de integração com Docker.

#### 8. Testes e comprovação do funcionamento

O repositório contém testes específicos para as principais etapas do processo:

- `test_extraction.py`: verifica a extração, a lista de tabelas permitidas e a compatibilização de colunas.
- `test_validation.py`: verifica idade mínima, valores permitidos, duplicidades, datas e integridade referencial.
- `test_transformation.py`: verifica padronização textual, conversão de classificação, Argon2id, telefone e identificador de dispositivo.
- `test_load.py`: verifica inserções, atualizações, `ON CONFLICT`, exclusões e ordem de dependência.
- `test_load_transaction.py`: verifica `COMMIT`, `ROLLBACK`, persistência do mapa de IDs e remapeamento de chaves estrangeiras.
- `test_state.py`: verifica a leitura e gravação do mapa de identificadores.
- `test_execution_log.py`: verifica o registro inicial e final das execuções.
- `test_main.py`: verifica a orquestração e o tratamento de falhas no fluxo principal.

O projeto também possui `docker-compose.test.yml`, que provisiona dois bancos PostgreSQL independentes, um legado e outro de destino, além do container responsável pela execução do RPA. Isso permite testar a migração em um ambiente controlado, com dados de preparação próprios, sem utilizar os bancos de produção.

#### 9. Resumo da implementação

O RPA implementa a migração e a sincronização de oito tabelas selecionadas entre o banco legado e o novo PostgreSQL normalizado. O funcionamento é estruturado em um pipeline ETL com validação, transformação, remapeamento de identificadores, operações de UPSERT, sincronização de exclusões e controle transacional.

O tratamento de falhas aplica rollback à carga quando o erro ocorre antes do commit. O mapa é persistido após a confirmação, e logs estruturados e `tb_log_rpa` registram o resultado da execução.

A implementação também contempla testes automatizados para extração, validação, transformação, carga, integridade referencial, transações e orquestração, além de um ambiente de integração com dois bancos PostgreSQL provisionados por Docker.

**Justificativa:** o RPA foi construído como um repositório separado, em Python, para que a migração seja repetível, testável e independente do banco de destino. A transação única garante que o banco novo nunca fique em estado parcial, e o mapa de IDs só é gravado depois do `COMMIT`.
