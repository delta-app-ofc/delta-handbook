# Ambientes Docker para desenvolvimento e testes locais

## Objetivo

Definir a organização dos ambientes Docker do Projeto Delta, as responsabilidades de cada serviço e os limites das verificações locais. Os ambientes oferecem dependências reproduzíveis e isolamento para desenvolvimento e testes, sem depender dos bancos oficiais.

O passo a passo de execução pertence ao `DOCKER-HELP.md` na raiz do repositório responsável. Este documento concentra a arquitetura, o funcionamento e as decisões compartilhadas. Os arquivos Dockerfile, Compose, scripts e testes de cada repositório são a referência executável da configuração.

## Organização dos ambientes

Cada repositório mantém o ambiente necessário à sua própria responsabilidade. Os serviços usam a rede do projeto Compose, sem exigir uma rede compartilhada entre todos os componentes do Delta.

Existem três formas de execução:

| Forma | Finalidade | Repositórios |
| --- | --- | --- |
| Imagem com alvo de teste | Executar uma suíte durante a construção de uma imagem | `delta-api-mongo` |
| Compose de desenvolvimento | Disponibilizar bancos persistentes para uma aplicação executada no host | `delta-artificial-intelligence`, `delta-business-rules` |
| Compose de verificação | Executar um serviço de verificação, com dependências locais quando necessárias | `delta-api-postgres`, `delta-mongo-database`, `delta-sql-database`, `delta-rpa`, `delta-hardware-data-simulator`, `delta-web-app` |

O Dockerfile é usado quando há código próprio a empacotar. Bancos e ferramentas disponíveis em imagens oficiais são declarados diretamente no Compose. A ausência de Dockerfile nesses serviços é uma decisão de organização, não uma falta de configuração.

## Serviços e imagens

| Repositório | Configuração | Serviços ou alvos | Imagens base |
| --- | --- | --- | --- |
| `delta-api-mongo` | `Dockerfile` | `build`, `test` e imagem final da API | Maven 3.9 com Eclipse Temurin 17; Eclipse Temurin 17 JRE Jammy |
| `delta-api-postgres` | `Dockerfile`, `docker-compose.test.yml` | `tests`; alvos `build`, `test`, `runtime` | Maven 3.9 com Eclipse Temurin 17; Eclipse Temurin 17 JRE Jammy |
| `delta-artificial-intelligence` | `docker-compose.dev.yml` | `postgres`, `mongo` | PostgreSQL 16 Alpine; MongoDB 7 |
| `delta-business-rules` | `docker-compose.dev.yml` | `postgres`, `mongo`, `mongo-init-replica` | PostgreSQL 16 Alpine; MongoDB 7 |
| `delta-mongo-database` | `docker-compose.test.yml` | `mongo`, `runner` | MongoDB 7 |
| `delta-sql-database` | `docker-compose.test.yml` | `test-db`, `smoke` | PostgreSQL 16 |
| `delta-rpa` | `Dockerfile`, `docker-compose.test.yml` | `legacy-db`, `new-db`, `rpa` | PostgreSQL 16 Alpine; Python 3.12 Slim |
| `delta-hardware-data-simulator` | `Dockerfile`, `docker-compose.test.yml` | `dry-run` | Python 3.12 Slim |
| `delta-web-app` | `Dockerfile`, `docker-compose.test.yml` | `checks` | Node.js 22 Slim |

As tags adotadas fixam a família e a versão principal, mas podem receber atualizações de imagem. Reprodutibilidade por digest e equivalência de versão com serviços externos não são garantidas por essas tags.

### APIs Java

No `delta-api-mongo`, o alvo `build` empacota a aplicação sem executar testes. O alvo `test` executa a suíte Maven padrão. A imagem final contém o JRE e o JAR, com usuário sem privilégios de root. Os testes live permanecem separados e dependem de habilitação explícita; não integram automaticamente a verificação padrão da imagem.

No `delta-api-postgres`, o alvo `test` executa a suíte Maven existente e utiliza o H2 em memória configurado em `src/test/resources/application.properties`, em modo de compatibilidade PostgreSQL. A configuração de teste gera suas próprias chaves de autenticação. O Compose tem somente o runner `tests`, sem servidor PostgreSQL ou variáveis de datasource impostas. Os alvos `build` e `runtime` preservam o empacotamento e a execução da API, com usuário sem privilégios na imagem final.

A configuração de produção da API mantém `ddl-auto=none`. Os testes usam a configuração própria `create-drop` do H2 e cobrem os cenários implementados de serviços, mapper, autenticação, validação de dispositivos e cadastro. Essa suíte não comprova compatibilidade integral com PostgreSQL nem execução das procedures e do schema oficial.

### IA e regras de negócio

Os Composes de desenvolvimento fornecem somente PostgreSQL e MongoDB; o código Python continua executado no host. Os scripts de inicialização são montados em modo somente leitura. As suítes isoladas existentes podem executar sem os bancos.

O ambiente de IA inicializa o PostgreSQL a partir de `db/postgres-init/`. O Mongo inicia sem carga própria. A configuração da aplicação distingue os databases de app e telemetria, mesmo quando usam o mesmo servidor local.

O motor de regras exige MongoDB com replica set para utilizar Change Streams. O serviço `mongo-init-replica` inicializa o replica set `rs0` com um único membro, anunciado como `mongo:27017` na rede interna. A inicialização é idempotente e limita as tentativas de conexão. O inicializador aguarda o primário antes de executar o seed montado em `/bootstrap`; a carga ocorre somente quando os dois databases de app e telemetria não possuem coleções, evitando sobrescrever dados existentes. Para clientes executados no host, `directConnection=true` evita tentar resolver o nome interno anunciado pelo replica set.

### MongoDB

O serviço `runner` usa o `mongosh` da imagem oficial. Ele executa os scripts de collections dos dois databases e, depois, os respectivos scripts de indexes. Os arquivos de `scripts/` e `tests/` são montados somente para leitura.

O smoke verifica as coleções esperadas, a presença de validators JSON Schema, os nomes dos índices e a rejeição de um tipo inválido em `user_preferences`, identificada pelo código 121. Esses checks não substituem testes completos de todas as regras de schema ou de compatibilidade entre versões.

Os scripts de roles do Atlas e os seeds não fazem parte da inicialização automática deste ambiente. O servidor local não comprova compatibilidade de versão ou configuração com o Atlas.

### PostgreSQL e ferramentas SQL

O ambiente `docker-compose.test.yml` do `delta-sql-database` é independente do ambiente de ferramentas definido em `docker-compose.yml`.

O runner `smoke` usa `psql` com `ON_ERROR_STOP=1` e aplica os scripts nesta ordem:

1. `script-schema.sql`: tabelas de negócio e constraints.
2. `script-optimization.sql`: functions e procedures.
3. `script-audit.sql`: objetos e triggers de auditoria.
4. `script-roles.sql`: roles e privilégios.

O smoke verifica objetos esperados, uma inserção válida em `tb_region` e a rejeição de um valor inválido por check constraint. A verificação de inserção é revertida por transação. A carga volumétrica `script-dataload.sql` não é necessária a esse fluxo.

O Compose de ferramentas mantém a imagem Python com cliente PostgreSQL 18 e a configuração própria em `.env` para os scripts de backup/setup. Ele não deve ser confundido com o ambiente de smoke nem com uma imagem do servidor PostgreSQL. Seu serviço `tools` monta o checkout em `/app`, preservando a finalidade de execução das ferramentas existentes.

### RPA

O ambiente de integração possui dois bancos independentes: `legacy-db`, inicializado por `test/init-legacy/`, e `new-db`, inicializado por `test/init-new/`. O serviço `rpa` aguarda a disponibilidade de ambos e executa o pipeline existente.

O Compose define explicitamente host, porta, banco, usuário e senha das duas conexões com valores dos serviços locais. As demais opções vêm de `.env.test`. Logs e mapa de IDs ficam em volumes nomeados do projeto, separados dos diretórios do host.

A avaliação da migração deve considerar os dados resultantes e os registros de execução. O encerramento do processo sem erro não constitui, sozinho, uma asserção de todos os resultados esperados da migração.

### Simulador e frontend

O simulador empacota a CLI Python e executa uma geração de `consumption_summary` em `dry-run`. Não precisa de banco, arquivo de ambiente ou volume do host. A geração verifica o caminho da CLI, mas não a aceitação do documento pelo MongoDB.

O frontend usa `npm ci` com o lockfile do repositório e executa `lint` seguido de `build`. Esse runner não serve a aplicação no navegador nem implementa testes funcionais; sua responsabilidade é verificar análise estática e compilação.

## Rede, portas e prontidão

Os ambientes SQL, MongoDB e API PostgreSQL de teste não publicam portas. Os runners de simulador e frontend também não publicam portas. A comunicação necessária ocorre pelos nomes de serviço na rede interna do Compose.

| Ambiente com acesso pelo host | PostgreSQL | MongoDB |
| --- | --- | --- |
| IA | `127.0.0.1:5432` | `127.0.0.1:27018` |
| Regras de negócio | `127.0.0.1:5435` | `127.0.0.1:27019` |
| RPA | Legado: `127.0.0.1:5433`; novo: `127.0.0.1:5434` | Não se aplica |

IA e regras permitem alterar as portas do host com `POSTGRES_HOST_PORT` e `MONGO_HOST_PORT`. As URLs da aplicação devem acompanhar essa alteração; a porta interna do serviço permanece a mesma.

PostgreSQL usa `pg_isready` como healthcheck. Mongo usa um ping com código de saída explícito; no motor de regras, o healthcheck exige um primário gravável. `depends_on` com condição de saúde organiza a inicialização dos runners. Saúde do serviço não significa que o schema está correto ou que a aplicação consegue executar todas as operações.

## Armazenamento e ciclo de vida

| Ambiente | Dados de banco | Outros volumes |
| --- | --- | --- |
| IA e regras | Volumes nomeados de PostgreSQL e MongoDB | Scripts de inicialização em binds somente leitura |
| API PostgreSQL de teste | H2 em memória, dentro do runner | Sem volumes do host |
| MongoDB de teste | `tmpfs` em `/data/db` e `/data/configdb` | Scripts e smoke em binds somente leitura |
| SQL de teste | `tmpfs` no diretório de dados do PostgreSQL | Scripts SQL em binds somente leitura |
| RPA | Dados associados aos containers/imagens de PostgreSQL, sem volume nomeado próprio | Binds de inicialização somente leitura; volumes nomeados `test-logs` e `test-state` |
| Simulador e frontend | Não se aplica | Sem volumes do host; código incluído na imagem |

Volumes nomeados de desenvolvimento preservam os dados entre recriações dos containers. Scripts de inicialização do PostgreSQL executam apenas em diretório de dados vazio. Trocar armazenamento anônimo por volume nomeado não migra os dados existentes; exige planejamento próprio caso seja necessário preservar esse conteúdo.

`tmpfs` é armazenamento temporário e não deve ser usado para dados que precisam sobreviver ao ciclo do ambiente de teste. Imagens oficiais podem declarar volumes anônimos em outros caminhos; sua existência não equivale a uma política de persistência do projeto.

Os logs e o estado do RPA sobrevivem à remoção dos containers enquanto os volumes nomeados forem mantidos. Remover apenas os bancos e reaproveitar o mapa de IDs exige atenção à consistência entre esse mapa e a base nova. Um teste iniciado do zero precisa de bancos e estado correspondentes ao mesmo ciclo.

Cache de imagem ou de dependências não é volume de dados. A limpeza de volumes deve ficar restrita ao projeto identificado e aos dados explicitamente descartáveis; o procedimento operacional está nos guias locais.

## Configuração e alcance das verificações

Arquivos de ambiente reais não devem integrar o contexto da imagem. Os Dockerfiles locais usam `.dockerignore` para excluir segredos e artefatos gerados. Os runners de teste usam conexões locais explícitas; acesso a serviços oficiais exige configuração e validação próprias.

As verificações têm alcances diferentes:

| Verificação | O que demonstra | O que não demonstra |
| --- | --- | --- |
| Validação da configuração Compose | Estrutura, interpolação e referências de configuração | Construção da imagem ou execução dos serviços |
| Build da imagem | Execução das instruções de construção | Testes, quando não fazem parte dessas instruções |
| Suíte Maven padrão | Comportamento coberto pelos testes existentes | Testes live não habilitados ou regras fora da suíte |
| Smoke de banco | Inicialização e asserções definidas no runner | Cobertura integral do schema e integração com produção |
| Dry-run do simulador | Geração local pela CLI | Inserção aceita pelo MongoDB |
| Lint e build do frontend | Análise estática e compilação | Fluxos funcionais no navegador |

Imagens, bancos e aplicações precisam de execução real para comprovar integração. A arquitetura local não implica disponibilidade dos serviços oficiais nem aprovação de todos os cenários do produto.

## Repositórios sem ambiente Docker próprio

`delta-handbook` é documental, e `delta-template-repository` não define runtime. Não precisam de containers próprios. Os repositórios `delta-app-mobile`, `delta-mobile-app`, `delta-neo4j-database` e `delta-redis-database` ainda não possuem, no conjunto considerado, build ou operações implementadas que justifiquem runners específicos.

A criação de ambiente nesses componentes deve partir da stack e dos casos de teste efetivamente implementados. Imagens oficiais podem atender dependências futuras; um Dockerfile adicional só é necessário quando houver código próprio a construir.
