### MOD-03 — Carregar pelo menos 500 registros verossímeis para testes de volume

**Evidência direta:**

- [Script da carga de dados](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-dataload.sql)
- [Documentação da carga e contagem por tabela](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/dataload.md)
- [Mapeamento de municípios e regiões tarifárias](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/mapeamento-cidade-regiao.md)

**Localização e como comprovar:**

A implementação está no arquivo `script-dataload.sql`, localizado no repositório `delta-sql-database`. O script contém os comandos SQL responsáveis pela inserção e complementação dos dados utilizados para popular o banco PostgreSQL.

A carga contempla **2.331 registros distribuídos entre 22 tabelas**, ultrapassando o requisito mínimo de 500 registros. Os dados foram elaborados para representar situações plausíveis de utilização do Projeto Delta, considerando usuários, imóveis, organizações, dispositivos, hábitos de consumo, tarifas e informações operacionais.

A distribuição dos registros permite testar não apenas o armazenamento individual das informações, mas também os relacionamentos entre as entidades, as consultas do sistema e as diferentes situações previstas nas regras de negócio.

**1. Volume de registros e distribuição por tabela**

A carga está organizada em dois conjuntos principais: o perfil residencial e a extensão comercial/industrial.

**Perfil residencial**

Contempla os dados utilizados na estrutura inicial do sistema, com usuários, imóveis residenciais, dispositivos, hábitos e informações relacionadas ao consumo de água.

| Tabela | Registros | Finalidade |
|---|---:|---|
| `tb_region` | 9 | Grupos tarifários da Sabesp utilizados na organização das tarifas. |
| `tb_municipality` | 371 | Municípios atendidos pela Sabesp, com código IBGE e região tarifária. |
| `tb_day_of_week` | 7 | Dias da semana utilizados nos cadastros de hábitos e funcionamento. |
| `tb_habit` | 6 | Tipos de hábitos relacionados ao consumo de água. |
| `tb_property_classification` | 8 | Classificações de imóveis residenciais e comerciais. |
| `tb_address` | 156 | Endereços associados às propriedades cadastradas. |
| `tb_user` | 201 | 200 usuários de teste e um administrador fixo. |
| `tb_property` | 155 | 150 imóveis residenciais e 5 unidades comerciais/industriais. |
| `tb_user_property` | 148 | Associações entre usuários e imóveis residenciais. |
| `tb_device` | 155 | Dispositivos associados às propriedades. |
| `tb_region_rate` | 72 | Tarifas distribuídas entre 9 regiões e 8 classificações. |
| `tb_user_habit` | 400 | Hábitos cadastrados pelos usuários, com frequências variadas. |
| `tb_user_habit_day` | 400 | Dias associados às rotinas cadastradas. |
| `tb_last_water_bill` | 200 | Contas de água associadas aos usuários. |

**Perfil comercial/industrial**

A extensão da carga contempla informações adicionais necessárias para representar organizações e unidades com características operacionais específicas.

| Tabela | Registros | Finalidade |
|---|---:|---|
| `tb_organization` | 3 | Organizações de diferentes segmentos de atuação. |
| `tb_user_organization` | 2 | Associações entre usuários gestores e organizações. |
| `tb_property_operational_profile` | 2 | Perfis operacionais de unidades industriais. |
| `tb_property_shift` | 5 | Turnos de funcionamento das unidades. |
| `tb_water_usage_type` | 4 | Tipos de utilização da água. |
| `tb_property_water_usage` | 8 | Associações entre unidades e finalidades de consumo. |
| `tb_property_operation_day` | 16 | Dias de funcionamento das unidades. |
| `tb_investment_scenario` | 3 | Cenários de investimento relacionados à gestão do consumo. |

**Total: 2.331 registros em 22 tabelas.**

**2. Verossimilhança e coerência dos dados**

Os registros foram elaborados para representar situações compatíveis com o contexto de utilização do Projeto Delta, evitando que a carga seja composta apenas por valores repetidos ou inserções sem relação com as regras de negócio.

Entre os principais exemplos estão:

- **Usuários:** são cadastrados 200 usuários de teste e um administrador fixo, permitindo representar diferentes perfis de acesso ao sistema.
- **Imóveis:** são contempladas 150 propriedades residenciais e unidades comerciais/industriais, possibilitando testar diferentes classificações e contextos de utilização.
- **Endereços:** são utilizados CEPs plausíveis, distribuídos conforme as regiões consideradas pelo sistema.
- **Dispositivos:** os registros são associados aos imóveis correspondentes, representando a estrutura de monitoramento do consumo de água.
- **Hábitos de consumo:** são cadastradas 400 rotinas de usuários, com frequências entre 1 e 7 dias por semana, além de horários e estimativas de consumo.
- **Contas de água:** são inseridas 200 contas, distribuídas entre os usuários de teste, com referências mensais de janeiro a junho de 2025.
- **Tarifas:** são cadastrados 72 registros, considerando as nove regiões e as oito classificações de imóveis, com vigência definida.
- **Municípios:** são cadastrados 371 municípios com código IBGE, associados ao grupo tarifário correspondente.
- **Organizações:** são representados três contextos organizacionais distintos: varejo, indústria e condomínio.
- **Informações operacionais:** as unidades industriais possuem dados complementares sobre turnos, dias de funcionamento e finalidades de utilização da água.
- **Cenários de investimento:** são inseridos registros que permitem representar situações de análise de investimentos relacionados à gestão hídrica.

Dessa forma, a carga contempla diferentes cenários de utilização, permitindo testar o comportamento do banco tanto em contextos residenciais quanto comerciais e industriais.

**3. Respeito aos relacionamentos e à integridade dos dados**

As inserções também consideram a estrutura relacional definida no `script-schema.sql`, respeitando as chaves primárias, estrangeiras e restrições de integridade implementadas no PostgreSQL.

Os registros são distribuídos de maneira que as associações entre as entidades representem situações possíveis dentro do sistema.

Alguns exemplos:

- Os imóveis possuem endereços associados e podem estar vinculados a organizações.
- Os dispositivos estão associados às propriedades correspondentes.
- Os hábitos pertencem a usuários e possuem associações com os dias da semana.
- As contas de água estão vinculadas aos usuários responsáveis.
- As tarifas relacionam regiões e classificações de imóveis.
- Os perfis operacionais complementam as informações das unidades industriais.
- Os cenários de investimento podem estar associados a organizações.

Também existem particularidades intencionais na distribuição dos registros. Por exemplo, os usuários administradores e gestores organizacionais não recebem necessariamente as mesmas associações dos usuários residenciais. Da mesma forma, apenas as unidades que necessitam de informações operacionais específicas recebem perfis e turnos de funcionamento.

Essas diferenças permitem representar situações distintas sem obrigar que todas as entidades possuam exatamente os mesmos dados associados.

**4. Como validar a quantidade de registros**

A própria documentação `dataload.md` apresenta uma consulta SQL de verificação que utiliza `COUNT(*)` em cada uma das 22 tabelas.

A consulta está disponível ao final da documentação e também é apresentada no script de carga.

Para comprovar o requisito:

1. Executar o `script-schema.sql` para criar a estrutura do banco, caso ainda não esteja criada.
2. Executar o `script-dataload.sql` para inserir os registros de teste.
3. Aguardar a conclusão da execução e verificar se não ocorreram erros de inserção ou integridade.
4. Executar a consulta de contagem por tabela apresentada ao final da documentação.
5. Conferir se as quantidades retornadas correspondem aos valores esperados, totalizando 2.331 registros.
6. Registrar o resultado da consulta por meio de uma captura de tela, identificando as tabelas e suas respectivas quantidades.

A consulta permite verificar individualmente cada tabela, evitando que a comprovação dependa apenas de uma contagem geral do banco.

**5. Importância da carga para o Projeto Delta**

A disponibilização de uma base de dados com volume e variedade permite validar diferentes funcionalidades do sistema em condições mais próximas de sua utilização.

Entre as possibilidades de utilização estão:

- Testar consultas que envolvem múltiplas tabelas e relacionamentos.
- Validar a associação entre usuários, imóveis, dispositivos e organizações.
- Verificar o comportamento das consultas relacionadas a hábitos e estimativas de consumo.
- Testar cálculos e consultas relacionados às tarifas e contas de água.
- Representar diferentes perfis de imóveis e suas características operacionais.
- Avaliar consultas analíticas e a integração das informações utilizadas pelas funcionalidades do projeto.

A separação entre os dados residenciais e comerciais/industriais também permite verificar se o modelo atende aos diferentes contextos de utilização previstos para a aplicação.
