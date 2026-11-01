### MOD-01 — Criar novo banco relacional PostgreSQL normalizado até 3FN

**Evidência direta:**

- [Script de criação do banco e tabelas](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-schema.sql)
- [Documentação do modelo relacional](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-relacional.md)
- [Diagrama lógico do banco](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-logica.png)
- [Documentação das regras de negócio](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/regras-negocio.md)
- [Mapeamento de municípios e regiões tarifárias](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/mapeamento-cidade-regiao.md)

**Localização e como comprovar:**

A implementação pode ser comprovada diretamente no `script-schema.sql`, que define a estrutura relacional do PostgreSQL, incluindo tabelas, atributos, chaves primárias, chaves estrangeiras, restrições de unicidade e validações de integridade. A documentação `modelagem-relacional.md` apresenta a finalidade das entidades, suas dependências e os relacionamentos estabelecidos durante a evolução do projeto. O diagrama lógico permite visualizar a separação das entidades e suas cardinalidades.

Para este requisito, a análise considera as **22 tabelas principais do modelo relacional**, responsáveis por representar as entidades e regras de negócio do Projeto Delta.

A normalização foi desenvolvida considerando as três primeiras formas normais:

#### 1. Primeira Forma Normal (1FN) — Atomicidade dos dados

As informações foram organizadas em atributos individuais, evitando armazenar conjuntos de valores ou informações repetidas em uma única coluna.

Isso pode ser observado em diferentes partes do modelo:

- **Cadastros principais:** `tb_user`, `tb_organization`, `tb_property`, `tb_address` e `tb_device` mantêm separadas as informações de pessoas, organizações, imóveis, endereços e dispositivos.
- **Tabelas de referência:** `tb_region`, `tb_municipality`, `tb_property_classification`, `tb_day_of_week`, `tb_habit` e `tb_water_usage_type` armazenam individualmente os valores de referência utilizados pelo sistema.
- **Relacionamentos N:N:** `tb_user_property`, `tb_user_organization`, `tb_property_water_usage`, `tb_property_operation_day` e `tb_user_habit_day` representam associações por registros independentes.
- **Informações operacionais:** `tb_property_operational_profile` separa o perfil complementar do imóvel, enquanto `tb_property_shift` permite armazenar cada turno em um registro próprio.
- **Hábitos e rotinas:** `tb_user_habit` armazena as características de cada rotina, e `tb_user_habit_day` registra individualmente os dias em que ela acontece.
- **Informações financeiras e tarifárias:** `tb_region_rate`, `tb_last_water_bill` e `tb_investment_scenario` mantêm separadamente as tarifas, contas de água e cenários de investimento.

Essa organização permite que usuários, imóveis, organizações, hábitos, turnos e demais entidades possuam múltiplos registros relacionados, sem depender de listas de valores ou estruturas fixas.

#### 2. Segunda Forma Normal (2FN) — Dependência completa das chaves

Os atributos foram organizados para depender da identificação completa de cada registro. Nos relacionamentos associativos, as restrições de unicidade garantem que as combinações que representam uma mesma associação não sejam duplicadas.

Isso pode ser observado principalmente em:

- `tb_user_property`: relaciona usuários e imóveis, armazenando também a data de associação.
- `tb_user_organization`: representa a associação entre pessoas e organizações.
- `tb_property_water_usage`: relaciona imóveis aos tipos de utilização da água.
- `tb_property_operation_day`: associa imóveis aos seus dias de funcionamento.
- `tb_user_habit_day`: associa cada rotina aos respectivos dias da semana.
- `tb_region_rate`: identifica uma tarifa pela combinação de região, classificação e início da vigência.
- `tb_last_water_bill`: utiliza a combinação de usuário e mês para identificar uma conta de referência.

As tabelas associativas mantêm as informações próprias de cada relacionamento, sem replicar os atributos cadastrais das entidades relacionadas. As restrições `UNIQUE` sobre as combinações de identificadores preservam a integridade dessas associações.

Um exemplo importante está em `tb_user_habit`: durante a evolução do projeto, foi removida a restrição que impedia um usuário de cadastrar o mesmo hábito mais de uma vez. Isso ocorreu porque uma pessoa pode ter rotinas diferentes para o mesmo hábito, como tomar banho em horários distintos durante a semana e o fim de semana.

Para atender a essa necessidade, os dias foram separados em `tb_user_habit_day`, enquanto triggers aplicam a regra de não permitir o mesmo hábito no mesmo dia e horário de início. Assim, a estrutura atende à realidade do uso do sistema sem limitar artificialmente os registros.

#### 3. Terceira Forma Normal (3FN) — Separação de informações independentes

As entidades foram divididas de acordo com suas responsabilidades, evitando repetir informações que pertencem a outros cadastros.

As principais decisões podem ser verificadas nos seguintes conjuntos:

**Cadastros e classificações:**

- `tb_user` mantém os dados das pessoas, enquanto `tb_organization` concentra os dados empresariais.
- `tb_property` referencia `tb_property_classification`, que centraliza as categorias dos imóveis e seus grupos.
- `tb_address` mantém as informações de localização e o vínculo com `tb_region`.
- `tb_device` mantém os dados específicos dos dispositivos, sem duplicar informações do imóvel.

**Localização e tarifação:**

- `tb_municipality` centraliza os municípios e seus códigos IBGE.
- `tb_region` representa os grupos tarifários.
- `tb_region_rate` armazena os valores por região, classificação e período de vigência.

Essa separação contempla o mapeamento de 371 municípios atendidos pela Sabesp em nove grupos tarifários. A API consulta `tb_municipality` para identificar a região correspondente à cidade e à UF informadas, persistindo a região resolvida em `tb_address.region_id`. Assim, os valores tarifários não precisam ser repetidos para cada município.

**Hábitos e operação:**

- `tb_habit` mantém o catálogo de hábitos, enquanto `tb_user_habit` armazena as rotinas cadastradas por cada usuário.
- `tb_day_of_week` centraliza os dias da semana, reutilizados tanto em `tb_user_habit_day` quanto em `tb_property_operation_day`.
- `tb_water_usage_type` mantém os tipos de utilização da água, associados às propriedades por `tb_property_water_usage`.
- `tb_property_shift` armazena os turnos separadamente, permitindo diferentes jornadas de funcionamento.
- `tb_property_operational_profile` mantém informações complementares, como a fonte principal de abastecimento, sem obrigar todos os imóveis a possuir esses atributos.

**Relacionamentos e informações financeiras:**

- `tb_user_property` e `tb_user_organization` mantêm os vínculos entre pessoas, imóveis e organizações sem replicar seus dados cadastrais.
- `tb_last_water_bill` mantém as contas dos usuários independentemente de seus cadastros.
- `tb_investment_scenario` armazena informações de planejamento de investimentos separadamente dos dados de telemetria, podendo estar associado opcionalmente a uma organização.

#### 4. Adaptação do modelo às necessidades do Projeto Delta

A normalização também orientou a evolução do projeto, principalmente na ampliação do atendimento residencial para os contextos comercial e industrial.

Em vez de criar estruturas duplicadas para cada perfil de utilização, o modelo reutiliza `tb_user` e `tb_property`, complementando-os com `tb_organization`, `tb_user_organization`, `tb_property_operational_profile`, `tb_property_shift`, `tb_property_operation_day` e as entidades relacionadas à utilização da água.

A associação entre usuários e organizações é representada por `tb_user_organization`, enquanto `is_manager` permanece como indicador de perfil do usuário, sem substituir o relacionamento associativo. Essa distinção permite que a associação de uma pessoa a uma ou mais organizações seja representada independentemente de seu indicador de perfil. A ausência de uma hierarquia interna de gestores e supervisores também foi uma decisão de escopo documentada.

Outro exemplo é a organização dos hábitos: a possibilidade de cadastrar o mesmo hábito em horários e dias diferentes foi incorporada à estrutura, com a separação entre rotina e dias de ocorrência e validações específicas no PostgreSQL.

#### 5. Regras de integridade e consistência dos dados

Além da separação das entidades, a normalização é complementada por restrições implementadas diretamente no PostgreSQL:

- `PRIMARY KEY`: identificação única dos registros.
- `FOREIGN KEY`: integridade dos relacionamentos.
- `UNIQUE`: prevenção de cadastros e associações duplicadas.
- `NOT NULL`: obrigatoriedade de informações essenciais.
- `CHECK`: validação das regras de negócio.
- `DEFAULT`: preenchimento automático de valores padrão.

Entre os exemplos estão a validação do formato do CNPJ e do CEP, a restrição de idade mínima dos usuários, os limites geográficos das coordenadas, a consistência dos horários de funcionamento, os períodos de vigência tarifária e a validação dos valores de consumo, faturas e investimentos.

As regras que envolvem mais de uma tabela ou condições específicas de negócio são complementadas por triggers, Functions e Procedures.

O modelo foi normalizado até a Terceira Forma Normal (3FN), atendendo ao requisito estabelecido. Após a análise das entidades e dos relacionamentos, não foram identificadas dependências de junção complexas que justificassem decomposições adicionais até a Quinta Forma Normal (5FN).
Os relacionamentos N:N foram representados por tabelas associativas próprias, e as informações independentes foram distribuídas em entidades específicas. Dessa forma, a estrutura atende às necessidades do domínio sem a necessidade de fragmentação adicional das tabelas, preservando a integridade e a consistência dos dados.

