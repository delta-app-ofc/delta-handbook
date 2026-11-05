# Histórico técnico das alterações do Delta em 2026

Este documento reúne, por área, as alterações de produto e engenharia identificadas nas branches locais do Projeto Delta em **4 de novembro de 2026**. Ele serve como mapa para revisão e continuidade do trabalho; não substitui os READMEs, contratos de API, documentação de dados ou histórico Git de cada repositório.

## Como interpretar este registro

- O levantamento considera os repositórios e branches que estavam disponíveis neste workspace na data acima. Alterações feitas em outras cópias, já descartadas ou ainda não trazidas para cá podem não estar representadas.
- Uma alteração em branch ou no working tree comprova a existência do código, não que ele foi mesclado, publicado ou executado em produção.
- “Persistido no banco” só deve ser afirmado com evidência da execução no ambiente correspondente, como log do job e consulta de conferência. Os estados atuais de bancos remotos não são inferidos deste documento.
- Os nomes de branches abaixo são os observados localmente e podem mudar depois de merge ou reorganização.

## Resumo por área

| Área | Mudanças registradas | Repositório e estado observado |
|---|---|---|
| Web | Integração de páginas com indicadores SQL e APIs, cadastro e autenticação, metas, investimentos, detalhes de instalação, IA, tema, acessibilidade, gráficos e PDFs. | `delta-web-app`, branch `codex/consolidated-web`; várias alterações locais ainda sem commit. |
| API PostgreSQL | Recuperação segura de senha, envio de e-mail HTML e configuração de SMTP/URL pública, além de ajustes relacionados ao cadastro e organização. | `delta-api-postgres`, branch `fix/editar-organizacao`; commit local `2e3b907` inclui recuperação de senha. |
| API de telemetria | Contexto de consumo, visita e calibração; ingestão resiliente com último vínculo conhecido; integração de evidências do detector e alertas. | Cópias `delta-api-mongo` e `delta-artificial-intelligence` sob `repo-api-mongo`; branches `feat/completa-deteccao` e `feat/integra-alertas-detector`. |
| Assistente IA | Ajustes no juiz e prompts, consultas gerais, consumo e previsão, tratamento de dados ausentes, gráficos e integração de ranking. | `repo-ia/delta-artificial-intelligence`, branch `fix/juiz-antes-persistencia`; alterações locais sem commit e branch 21 commits atrás da referência remota observada. |
| ETL de BI | Agendamento de cinco em cinco minutos, controle de concorrência e duração, Mongo de aplicação opcional e testes correspondentes. | `repo-api-mongo/delta-sql-database-bi-etl`, branch `fix/bi-etl-agendamento-5min`; alterações locais sem commit. |
| Ranking Redis | Filtragem de instalações comerciais por organização válida e IDs positivos na sincronização. | `repo-redis/delta-redis-database`, branch `codex/consolidated-ranking`; alteração local sem commit. |
| Banco relacional | Dataload e arquivos de demonstração/backup presentes no working tree; capitalização e descrições de cenários de investimento ajustadas. | `repo-database/delta-database`, branch `docs/evidencias-backup`; mudanças locais sem commit. |
| Handbook | Regras e fórmulas de BI detalhadas, limitações, pesquisa de investimento e requisitos de views/CTEs. | `repo-docs/delta-handbook`, branch `docs/bi-calculos-detalhados`; quatro documentos locais modificados. |

## Web: telas, serviços e experiência

### Dados e indicadores

As páginas de Dashboard, Instalações, Monitoramento, Alertas, Vazamentos, Ranking, Metas, Dispositivos, Investimentos e Detalhes da instalação foram conectadas a serviços que consultam as APIs e, por meio delas, os indicadores SQL. O trabalho também inclui:

- seleção do período disponível, gráficos históricos e estados vazios mais claros;
- filtro/ordenação de unidades, tratamento de nomes e cidades para leitura humana e exibição de rankings;
- edição de metas e atualização dos indicadores relacionados;
- resumo e detalhamento de vazamentos, incluindo histórico horário e orientações gerais;
- previsão de consumo, clima atual e previsão meteorológica por instalação, com ícone que varia conforme a condição;
- cenários de investimento retornados pelo serviço, impacto hídrico/ambiental e projeções agregadas da organização.

Os indicadores devem continuar vinculados às fontes e regras do banco descritas em [camada-bi.md](../DADOS/SQL/camada-bi.md). Quando faltam fatos de origem, a interface deve exibir ausência de dados, sem inventar valores.

### Cadastro, conta e configurações

Foram trabalhados os fluxos de cadastro/login, validação de CNPJ e CEP no passo correspondente, criação de organização/unidade pelo fluxo de cadastro completo e melhoria da tela de recuperação de senha. Configurações receberam ações de sessão e organização, preferências visuais e ajustes de apresentação. O comportamento que depende da API deve ser conferido no serviço correspondente; uma mensagem na interface, por si só, não confirma gravação no servidor.

O envio real do e-mail de recuperação depende de configurar SMTP, Redis para o token e a URL pública/base da aplicação no backend. Consulte o README e o exemplo de ambiente da API antes de publicar ou operar esse fluxo.

### Assistente Gluh

Na web foram ajustados cabeçalho, alinhamento, histórico de conversas, perguntas sugeridas e estados de envio/carregamento. Também foram adicionados componentes de renderização de Markdown e Plotly para respostas formatadas e gráficos, além de ajustes de integração e autenticação do cliente. A validade da sessão depende do contrato e da configuração do serviço de IA; a tela não substitui os testes de autenticação do backend.

### Interface, acessibilidade e exportação

O trabalho inclui alinhamento e espaçamento de páginas e cartões, navegação lateral e marca, tema claro/escuro, capitalização de nomes, menus suspensos, barras de rolagem e estados vazios. Foram feitos ajustes de responsividade e contraste em vários componentes.

Os PDFs usam a impressão do navegador (`window.print`) e regras de impressão próprias para aproximar o relatório do padrão visual da plataforma, preservar gráficos e distribuir o conteúdo entre páginas. Na tela de investimentos, a impressão passou a montar uma versão estática separada dos controles clicáveis para não perder cenários e detalhamentos quando o navegador oculta botões. A aparência final ainda depende das opções do diálogo de impressão, especialmente “imprimir gráficos de fundo”.

## APIs e integrações

### API PostgreSQL

O commit local `2e3b907` implementa recuperação de senha com token temporário, rate limiting, envio de e-mail HTML e configuração documentada. O backend usa Redis para guardar o token e SMTP para entregar a mensagem. Configure as variáveis documentadas no `.env.example`; não registre credenciais em documentação nem no repositório.

### API Mongo e detector

Na branch `feat/completa-deteccao`, os commits observados adicionam contexto de consumo, visita e calibração e mantêm a ingestão associada ao último proprietário conhecido quando a consulta cadastral falha. A branch `feat/integra-alertas-detector` integra evidências do detector e a rotina de alertas, e contém uma correção para permitir consultar informações do job sem inicializar bancos. Consulte os READMEs e testes dessas branches para os contratos e condições de operação.

### Ranking Redis

A sincronização filtra registros que não sejam unidades comerciais e descarta `organizationId` ausente, inválido, booleano ou menor/igual a zero. Isso evita que registros sem organização sejam tratados como parte de um ranking organizacional. O código está alterado localmente na branch `codex/consolidated-ranking`; sua publicação e execução precisam ser confirmadas no serviço Redis/API.

## Dados, BI e execução

### ETL MongoDB → PostgreSQL

O working tree do ETL altera o cron do GitHub Actions para `*/5 * * * *`, adiciona limite de quatro minutos e grupo de concorrência, e permite que as coleções do MongoDB de aplicação sejam ignoradas quando suas credenciais não estão configuradas. As coleções de telemetria continuam dependendo das variáveis próprias. O workflow também deixa de disparar o evento de sincronização Redis que existia no final da execução; se essa sincronização automática for necessária, ela precisa ser reintroduzida ou substituída por um agendamento/integração configurado.

Essas mudanças estão no working tree da branch `fix/bi-etl-agendamento-5min`; não significam que o GitHub Actions executou com sucesso, que a cota foi verificada ou que houve gravação nos bancos reais. A validação deve consultar o histórico do workflow e conferir contagens/IDs de origem e destino no mesmo ambiente. O teste alterado no repositório também ainda precisa ser executado antes de declarar a mudança validada.

### Dataloads e dados de meses

O repositório relacional contém alterações locais em `script-dataload.sql`, arquivos específicos de demonstração e material de backup. No snapshot consultado, a diferença de `script-dataload.sql` altera a capitalização de nomes/descrições dos cenários de investimento; ela **não** comprova a inclusão de leituras para junho, julho e agosto. Antes de dizer que esses meses foram populados, confirme os arquivos de carga e execute consultas de contagem/agregação no banco de destino.

Não execute dataload de demonstração em banco de produção sem identificar explicitamente o ambiente e revisar o conteúdo: uma carga pode inserir ou alterar dados persistentes. Os arquivos de backup/teste também não são evidência de que um restore foi feito em produção.

### Documentação da camada BI

Os documentos já alterados no handbook detalham grãos e origens, fórmulas das views, comportamento de `LAG`, completude de meses, metas e projeções, telemetria por hora, status de dispositivos, estimativas de vazamentos e cenários de investimento. A pesquisa de investimentos documenta valores armazenados, cálculo do payback, equivalências ambientais, fontes públicas e limitações das referências. Consulte:

- [Camada BI](../DADOS/SQL/camada-bi.md)
- [Pesquisa e cálculos de cenários de investimento](../DADOS/SQL/pesquisa-cenarios-investimento.md)
- [Requisito de views analíticas (MOD-05)](../DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-05-views-analiticas-data-mart.md)
- [Requisito de CTEs e ETL SQL (MOD-06)](../DADOS/SQL/documenta%C3%A7%C3%A3o-requisitos/mod-06-ctes-etl-sql.md)

## O que ainda exige comprovação

O levantamento de código não autoriza afirmar que todos os serviços foram publicados ou que os dados reais estão atualizados. Para fechar essa comprovação por ambiente:

1. registre o commit implantado e a URL/ambiente de cada serviço;
2. confirme que secrets e variáveis de ambiente necessários estão definidos sem copiá-los para logs/documentação;
3. confira execuções recentes e logs do ETL, API, ranking Redis e serviço de IA;
4. compare contagens e IDs Mongo ↔ tabelas `stage`, confirme as procedures silver/gold e consulte as views;
5. confirme junho, julho e agosto com dados no destino antes de tratá-los como meses populados;
6. gere os PDFs no navegador e confira o número de páginas, gráficos e cores com as opções de impressão escolhidas.

## Revisão deste registro

Atualize este histórico quando uma alteração desta lista for mesclada, publicada, revertida ou substituída. Para o estado atual, prefira a branch padrão e os logs do serviço ao snapshot das branches locais descrito aqui.
