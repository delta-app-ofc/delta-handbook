### MOD-02 — Definir claramente PKs, FKs e cardinalidades 1:1, 1:N e N:N

**Evidência direta:**

- [Script de criação do banco — script-schema.sql](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-schema.sql)
- [Diagrama lógico do banco](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-logica.png)
- [Documentação do modelo relacional](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/modelagem-relacional.md)

**Localização e como comprovar:**

A definição das chaves está implementada diretamente no `script-schema.sql`, por meio das declarações `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE` e das restrições de integridade referencial.

O modelo possui 22 tabelas principais e 24 vínculos de chave estrangeira, estabelecendo os relacionamentos entre usuários, organizações, imóveis, endereços, dispositivos, hábitos, tarifas e demais entidades.

**1. Chaves Primárias (PK)**

Todas as tabelas possuem identificação por chave primária, garantindo que cada registro seja identificado individualmente.

Nas 21 tabelas, a identificação utiliza `id SERIAL PRIMARY KEY`, com geração automática dos identificadores. A exceção é `tb_property_operational_profile`, cuja coluna `property_id` funciona simultaneamente como chave primária e estrangeira, garantindo seu relacionamento 1:1 com `tb_property`.

**2. Chaves Estrangeiras (FK)**

As 24 chaves estrangeiras foram definidas para garantir que os registros associados correspondam a entidades existentes.

Os relacionamentos estão organizados da seguinte forma:

| Tabela que contém a FK | Referência | Finalidade |
|---|---|---|
| `tb_municipality.region_id` | `tb_region.id` | Município associado ao grupo tarifário |
| `tb_address.region_id` | `tb_region.id` | Endereço associado à região tarifária |
| `tb_property.classification_id` | `tb_property_classification.id` | Classificação do imóvel |
| `tb_property.address_id` | `tb_address.id` | Endereço do imóvel |
| `tb_property.organization_id` | `tb_organization.id` | Organização responsável pelo imóvel (opcional) |
| `tb_property_operational_profile.property_id` | `tb_property.id` | Perfil operacional do imóvel |
| `tb_property_shift.property_id` | `tb_property.id` | Turnos de funcionamento |
| `tb_property_water_usage.property_id` | `tb_property.id` | Associação de utilização de água |
| `tb_property_water_usage.water_usage_type_id` | `tb_water_usage_type.id` | Tipo de utilização da água |
| `tb_property_operation_day.property_id` | `tb_property.id` | Dias de operação do imóvel |
| `tb_property_operation_day.day_of_week_id` | `tb_day_of_week.id` | Dia da semana |
| `tb_user_property.user_id` | `tb_user.id` | Associação entre usuário e imóvel |
| `tb_user_property.property_id` | `tb_property.id` | Associação entre imóvel e usuário |
| `tb_user_organization.user_id` | `tb_user.id` | Associação entre usuário e organização |
| `tb_user_organization.organization_id` | `tb_organization.id` | Associação entre organização e usuário |
| `tb_device.property_id` | `tb_property.id` | Imóvel ao qual o dispositivo pertence |
| `tb_region_rate.region_id` | `tb_region.id` | Região da tarifa |
| `tb_region_rate.classification_id` | `tb_property_classification.id` | Categoria da tarifa |
| `tb_user_habit.user_id` | `tb_user.id` | Usuário responsável pela rotina |
| `tb_user_habit.habit_id` | `tb_habit.id` | Tipo de hábito cadastrado |
| `tb_user_habit_day.user_habit_id` | `tb_user_habit.id` | Rotina associada aos dias |
| `tb_user_habit_day.day_of_week_id` | `tb_day_of_week.id` | Dia de ocorrência da rotina |
| `tb_last_water_bill.user_id` | `tb_user.id` | Usuário responsável pela conta |
| `tb_investment_scenario.organization_id` | `tb_organization.id` | Organização relacionada ao investimento (opcional) |

**3. Definição das cardinalidades**

**Relacionamento 1:1 — Um para um**

Implementado entre `tb_property` e `tb_property_operational_profile`.

A coluna `property_id` da tabela de perfil é simultaneamente PK e FK de `tb_property`. Isso garante que cada perfil pertença a um único imóvel e que um imóvel possua, no máximo, um perfil operacional.

O relacionamento é opcional do lado do imóvel, pois nem todas as propriedades necessitam de informações operacionais complementares.

**Relacionamento 1:N — Um para muitos**

Utilizado quando uma entidade pode possuir vários registros associados, mas cada registro filho pertence a uma única entidade de origem.

Os principais exemplos são:

- `tb_region` → `tb_municipality`: uma região pode agrupar diversos municípios.
- `tb_region` → `tb_address`: uma região pode estar associada a diversos endereços.
- `tb_address` → `tb_property`: um endereço pode possuir diferentes imóveis cadastrados.
- `tb_property_classification` → `tb_property`: uma classificação pode ser utilizada em diversos imóveis.
- `tb_organization` → `tb_property`: uma organização pode possuir diversas unidades, enquanto o vínculo do imóvel com a organização é opcional.
- `tb_property` → `tb_device`: um imóvel pode possuir diversos dispositivos.
- `tb_property` → `tb_property_shift`: um imóvel pode possuir diferentes turnos.
- `tb_user` → `tb_user_habit`: um usuário pode cadastrar diversas rotinas.
- `tb_habit` → `tb_user_habit`: um tipo de hábito pode estar presente nas rotinas de diferentes usuários.
- `tb_user_habit` → `tb_user_habit_day`: uma rotina pode estar associada a diferentes dias.
- `tb_user` → `tb_last_water_bill`: um usuário pode cadastrar contas referentes a diferentes meses.
- `tb_organization` → `tb_investment_scenario`: uma organização pode possuir diferentes cenários de investimento, sendo a associação opcional.

Também são utilizados relacionamentos 1:N nas entidades associativas e tarifárias, como `tb_region_rate`, que recebe referências de `tb_region` e `tb_property_classification`.

**Relacionamento N:N — Muitos para muitos**

Implementado por meio de tabelas associativas, permitindo que diferentes registros de uma entidade sejam relacionados a diferentes registros de outra.

Os principais casos são:

- **Usuários e imóveis:** `tb_user_property` permite que um usuário esteja associado a diversos imóveis e que um imóvel tenha diversos usuários vinculados.
- **Usuários e organizações:** `tb_user_organization` permite que pessoas estejam associadas a diferentes organizações e que cada organização possua diversos usuários.
- **Imóveis e tipos de utilização da água:** `tb_property_water_usage` permite cadastrar diferentes finalidades de consumo para cada imóvel.
- **Imóveis e dias de funcionamento:** `tb_property_operation_day` permite que um imóvel funcione em vários dias da semana e que cada dia esteja associado a diversos imóveis.
- **Rotinas e dias da semana:** `tb_user_habit_day` permite que uma rotina ocorra em vários dias e que um mesmo dia seja utilizado em diversas rotinas.
- **Usuários e tipos de hábitos:** `tb_user_habit` representa essa associação, armazenando também frequência, horários e estimativa de consumo. A ausência de unicidade apenas no par usuário-hábito permite cadastrar rotinas diferentes para o mesmo hábito.

**4. Restrições de unicidade e integridade referencial**

Além das chaves primárias e estrangeiras, foram definidas restrições `UNIQUE` para impedir duplicidades em cadastros e associações.

Entre os exemplos estão:

- E-mail único em `tb_user`.
- CNPJ único em `tb_organization`.
- CEP único em `tb_address`.
- Identificador físico único em `tb_device`.
- Combinação de usuário e imóvel em `tb_user_property`.
- Combinação de usuário e organização em `tb_user_organization`.
- Combinação de imóvel e tipo de utilização em `tb_property_water_usage`.
- Combinação de imóvel e dia de operação em `tb_property_operation_day`.
- Combinação de rotina e dia em `tb_user_habit_day`.
- Combinação de região, classificação e início da vigência em `tb_region_rate`.
- Combinação de usuário e mês em `tb_last_water_bill`.

As políticas `ON DELETE` também foram definidas conforme a dependência entre as entidades. Em associações e registros dependentes, utiliza-se `CASCADE` para manter a consistência da exclusão. Em cadastros de referência que não devem ser removidos enquanto estiverem sendo utilizados, utiliza-se `RESTRICT`. As chaves também possuem `ON UPDATE CASCADE`.

**5. Decisões específicas de relacionamento**

Algumas decisões foram importantes para representar corretamente as regras do Projeto Delta:

- O relacionamento entre `tb_property` e `tb_property_operational_profile` utiliza uma PK compartilhada, em vez de criar uma associação 1:N desnecessária.
- Os relacionamentos entre usuários, imóveis e organizações são N:N, representados por tabelas associativas com identificação própria e data de associação.
- `tb_user_habit` não possui unicidade entre usuário e hábito, pois o mesmo hábito pode representar diferentes rotinas, com dias e horários distintos.
- `tb_region_rate` relaciona regiões e classificações, permitindo diferentes registros tarifários ao longo do tempo, identificados pelo início da vigência.
- `tb_property.organization_id` e `tb_investment_scenario.organization_id` são opcionais, permitindo manter cenários residenciais e de referência que não estejam vinculados a uma organização.

No mapeamento geográfico, `tb_municipality` e `tb_address` não possuem uma FK direta entre si. A associação é resolvida pela API, que utiliza cidade e UF para consultar o município e preencher `tb_address.region_id`. Isso foi definido para manter o endereço ligado diretamente ao grupo tarifário utilizado pelo sistema.