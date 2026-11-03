# Deploys no Render

O Render hospeda serviços HTTP do Delta. O código é integrado no GitHub e o workflow de CD solicita a publicação por um deploy hook. O Render executa o build e inicia a aplicação com as variáveis configuradas no serviço.

## Configurações nos repositórios

| Componente | Configuração versionada |
| --- | --- |
| API PostgreSQL | [`cd.yml`](https://github.com/delta-app-ofc/delta-api-postgres/blob/main/.github/workflows/cd.yml): push na `main`, conferência do secret e POST ao deploy hook. As solicitações usam o grupo de concorrência `render-deploy-main`. |
| IA | [`cd.yml`](https://github.com/delta-app-ofc/delta-artificial-intelligence/blob/main/.github/workflows/cd.yml): push na `main`, checkout e POST ao deploy hook. |
| API Redis | [`render.yaml`](https://github.com/delta-app-ofc/delta-redis-database/blob/main/render.yaml): serviço Docker `delta-redis-api`, health check em `/health` e variáveis de integração. |

O `render.yaml` descreve os campos usados na criação por Blueprint. Os valores de domínio, ambiente, instância e credenciais são administrados no painel do Render.

## Criar ou conectar um serviço

1. No Render, conecte o repositório e selecione a branch `main`.
2. Use o Dockerfile do componente quando o serviço for Docker. Selecione a raiz correta do projeto no caso de uma aplicação em subpasta.
3. Cadastre as variáveis exigidas pelo componente: conexões de banco, autenticação e integrações. Os nomes ficam no README e nos arquivos de configuração do respectivo repositório.
4. Configure o endpoint de saúde de acordo com a aplicação. Na API Redis, o Blueprint usa `/health`.
5. Faça a publicação inicial e acompanhe build, inicialização e resposta HTTP nos eventos e logs do serviço.

A aplicação precisa escutar na interface `0.0.0.0` e na porta fornecida pelo ambiente. Os detalhes de inicialização são definidos pelo Dockerfile ou pelo comando de start do serviço.

## Configurar o deploy hook

Abra as configurações do serviço no Render e copie seu **Deploy Hook**. No repositório GitHub correspondente, cadastre a URL como secret de Actions chamado `RENDER_DEPLOY_HOOK`.

O hook contém a autorização para disparar a publicação. Armazene-o no secret, junto das demais credenciais administradas pela equipe.

Quando o GitHub Actions for o responsável pelo disparo, ajuste o auto-deploy do Render para evitar uma segunda publicação independente para o mesmo push. Se a equipe optar pelo auto-deploy do próprio Render, organize os disparos com essa escolha.

## Publicar uma versão

1. Abra a PR e conclua a revisão com os checks exigidos pelo repositório.
2. Integre a PR à `main`.
3. Acompanhe o workflow **Continuous Delivery** no GitHub Actions.
4. Abra os eventos do serviço no Render para acompanhar o build e a entrada da nova versão.
5. Confira a resposta do endpoint de saúde e o fluxo da aplicação que usa o serviço.

O resultado do POST registra a solicitação do deploy. O estado final da versão fica nos eventos do Render. Na API PostgreSQL, o workflow registra no resumo quando o secret ainda precisa ser cadastrado; com o hook configurado, envia a solicitação com timeout e tratamento de erro HTTP.

## Variáveis da API Redis

O Blueprint da API Redis declara:

| Variável | Finalidade |
| --- | --- |
| `REDIS_URL` | Conexão com o Redis usado pelo ranking. |
| `POSTGRES_API_URL` | Endereço da API PostgreSQL. |
| `POSTGRES_API_EMAIL` e `POSTGRES_API_PASSWORD` | Autenticação da integração com a API PostgreSQL. |
| `MIN_COVERAGE_RATIO` | Critério de cobertura dos dados; o arquivo usa `0.5`. |
| `RETENTION_MONTHS` | Retenção dos dados; o arquivo usa `13`. |

As variáveis com `sync: false` recebem seus valores pelo ambiente do serviço.

## Atualizações de banco e recuperação

Planeje alterações de schema junto da versão da aplicação. Execute as migrations pelo procedimento definido no repositório do banco ou no workflow responsável, preservando a compatibilidade durante a troca de versão.

Em caso de falha, consulte os logs de build e runtime, confira as variáveis e identifique o commit publicado. Use o histórico de deploys do serviço para selecionar uma versão anterior ou publique a correção pela `main`. Quando houver mudança de schema, considere a compatibilidade dos dados ao recuperar uma versão da aplicação.
