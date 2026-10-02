# 📊 Modelagem de Dados - PostgreSQL (Projeto Delta)

Este documento descreve a modelagem relacional do banco de dados PostgreSQL do Projeto Delta, responsável por armazenar informações de usuários, imóveis, dispositivos IoT, hábitos de consumo e regras regionais de tarifação de água.

🔗 Repositório: https://github.com/delta-app-ofc/delta-database

---

## 🌎 1. Tabela: `tb_region`

Armazena as regiões utilizadas para cálculo de tarifas — cada uma representa
uma área com tarifa Sabesp realmente diferente (fonte: ARSESP), não uma zona
da Grande SP (essas cobram a mesma tarifa entre si).

### 📌 Atributos
- **id (PK)**: Identificador da região.
- **name**: Nome da região.
  - Valores permitidos: `GRANDE_SP`, `LINS`, `PRESIDENTE_PRUDENTE`, `ADAMANTINA_PIRAPOZINHO`, `BRAGANCA_PAULISTA`

---

## 📅 2. Tabela: `tb_day_of_week`

Define os dias da semana utilizados na associação de hábitos.

### 📌 Atributos
- **id (PK)**: Identificador do dia da semana.
- **name**: Nome do dia.
  - Valores permitidos: `SEGUNDA`, `TERÇA`, `QUARTA`, `QUINTA`, `SEXTA`, `SÁBADO`, `DOMINGO`

---

## 🧠 3. Tabela: `tb_habit`

Armazena os tipos de hábitos de consumo de água.

### 📌 Atributos
- **id (PK)**: Identificador do hábito.
- **name**: Nome do hábito.
  - Valores permitidos: `BANHO LONGO`, `LAVAR QUINTAL`, `LAVAR ROUPA`, `REGAR PLANTAS`, `LAVAR CARRO`, `LAVAR LOUÇA`
- **description**: Descrição opcional do hábito.

---

## 📍 4. Tabela: `tb_address`

Armazena os endereços dos imóveis cadastrados.

### 📌 Atributos
- **id (PK)**: Identificador do endereço.
- **region_id (FK)**: Referência para `tb_region`.
- **cep**: CEP (8 dígitos numéricos).
- **city**: Cidade.
- **state**: Estado.

---

## 👤 5. Tabela: `tb_user`

Armazena os usuários do sistema.

### 📌 Atributos
- **id (PK)**: Identificador do usuário.
- **name**: Nome completo.
- **email**: E-mail (único).
- **password**: Senha criptografada.
- **phone**: Telefone.
- **birth_date**: Data de nascimento.
- **registration_date**: Data de cadastro (padrão: CURRENT_DATE).
- **is_active**: Indica se o usuário está ativo.
- **is_admin**: Indica se o usuário é administrador.
- **is_manager**: Indica se o usuário é gerente, para a versão comercial.
  - ⚠️ Coluna antiga, nunca lida por nenhuma function/procedure. Desde a extensão comercial/industrial
    (seção 12), o vínculo pessoa-organização passou a ser modelado de verdade por `tb_user_organization`,
    que bate 1:1 com `is_manager` nos dados de teste atuais. As duas colunas descrevem o mesmo fato hoje;
    unificação registrada como pendência, ainda não implementada.

---

## 🏠 6. Tabela: `tb_property`

Representa os imóveis cadastrados no sistema.

### 📌 Atributos
- **id (PK)**: Identificador do imóvel.
- **name**: Nome do imóvel.
- **type**: Tipo do imóvel (`CASA`, `PRÉDIO`).
- **classification_id (FK)**: Referência para `tb_property_classification`.
- **address_id (FK)**: Referência para `tb_address`.
- **registration_date**: Data de cadastro.
- **organization_id (FK, opcional)**: Referência para `tb_organization` (seção 12). `NULL` = imóvel
  residencial de pessoa física (comportamento original, preservado); preenchido = unidade de uma
  organização (perfil comercial/industrial).
- **built_area_m2 (opcional)**: Área construída em m², usada para ranking de eficiência (litros/m²) na
  camada de BI (`camada-bi.md`).

---

## 🏷️ 6.1. Tabela: `tb_property_classification`

Categorias de imóvel usadas para classificação e para a tarifa por
categoria (`tb_region_rate`). Cada categoria pertence a um grupo mais amplo
(`group_name`), usado pelo motor de detecção de vazamento para regras que
só se aplicam a um dos dois grupos (ex. a regra de madrugada não vale pra
imóveis comerciais).

### 📌 Atributos
- **id (PK)**: Identificador da categoria.
- **name**: Nome da categoria (único).
  - Valores permitidos: `RESIDENCIAL_NORMAL`, `RESIDENCIAL_SOCIAL`, `RESIDENCIAL_FAVELA`, `RESIDENCIAL_ESPECIAL`, `COMERCIAL_NORMAL_INDUSTRIAL`, `COMERCIAL_ESPECIAL`, `COMERCIAL_ENTIDADE_ASSISTENCIA_SOCIAL`, `PUBLICA_COM_CONTRATO`
- **group_name**: Grupo da categoria.
  - Valores permitidos: `RESIDENCIAL`, `COMERCIAL`

---

## 🔗 7. Tabela: `tb_user_property`

Tabela de relacionamento N:N entre usuários e imóveis.

### 📌 Atributos
- **id (PK)**: Identificador do relacionamento.
- **user_id (FK)**: Referência para `tb_user`.
- **property_id (FK)**: Referência para `tb_property`.
- **association_date**: Data de vinculação.


---

## 📟 8. Tabela: `tb_device`

Armazena os dispositivos IoT instalados nos imóveis.

### 📌 Atributos
- **id (PK)**: Identificador interno.
- **device_id**: Identificador físico do dispositivo (único).
- **property_id (FK)**: Referência para `tb_property`.
- **is_active**: Status do dispositivo (ativo/inativo).
- **installation_date**: Data de instalação.

---

## 💧 9. Tabela: `tb_region_rate`

Define tarifas de água por região e por categoria de imóvel. Uma
combinação `region_id` + `classification_id` pode ter várias linhas ao
longo do tempo (uma por período de vigência), mas só uma vigente por vez.

### 📌 Atributos
- **id (PK)**: Identificador da tarifa.
- **region_id (FK)**: Referência para `tb_region`.
- **classification_id (FK)**: Referência para `tb_property_classification`.
- **m3_value**: Valor por m³ (> 0).
- **initial_validity**: Início da vigência.
- **final_validity**: Fim da vigência (pode ser NULL).

Atualizada uma vez ao ano pelo `update_tariffs.py` (`delta-business-rules`)
— ver `tariffs/README.md` nesse repositório para as fontes e a metodologia
dos valores.

---

## 👥 10. Tabela: `tb_user_habit`

Relaciona usuários aos seus hábitos de consumo.

### 📌 Atributos
- **id (PK)**: Identificador.
- **user_id (FK)**: Referência para `tb_user`.
- **habit_id (FK)**: Referência para `tb_habit`.
- **frequency**: Frequência do hábito (> 0).


---

## 📆 11. Tabela: `tb_user_habit_day`

Define em quais dias da semana cada hábito ocorre.

### 📌 Atributos
- **id (PK)**: Identificador.
- **user_habit_id (FK)**: Referência para `tb_user_habit`.
- **day_of_week_id (FK)**: Referência para `tb_day_of_week`.

---

## 🏭 12. Extensão comercial/industrial

Tabelas adicionadas para o perfil comercial/industrial (unidades operadas por uma organização, não por
pessoa física direto). Não existe diferenciação de papel/hierarquia dentro da organização (gestor,
supervisor etc.) — decisão de escopo, não lacuna. Detalhamento completo de origem, grão e uso na camada de
BI em `camada-bi.md`.

### 🏢 12.1. Tabela: `tb_organization`

Empresa dona de uma ou mais unidades (`tb_property.organization_id`).

#### 📌 Atributos
- **id (PK)**: Identificador da organização.
- **corporate_name**: Razão social.
- **trade_name**: Nome fantasia.
- **cnpj**: CNPJ (14 dígitos, único).
- **business_segment**: Segmento do negócio.
  - Valores permitidos: `VAREJO`, `INDUSTRIA`, `CONDOMINIO`, `FACILITIES`
- **declared_unit_count**: Quantidade de unidades declarada no cadastro (opcional).
- **registration_date**: Data de cadastro.

---

### 🔗 12.2. Tabela: `tb_user_organization`

Relacionamento N:N entre usuários e organizações — mesmo padrão de `tb_user_property`, sem papel/
hierarquia.

#### 📌 Atributos
- **id (PK)**: Identificador do relacionamento.
- **user_id (FK)**: Referência para `tb_user`.
- **organization_id (FK)**: Referência para `tb_organization`.
- **association_date**: Data de vinculação.

---

### ⚙️ 12.3. Tabela: `tb_property_operational_profile`

Dados operacionais extras que só existem quando o cadastro industrial da unidade está completo — por isso
é uma extensão 1:1 de `tb_property` (chave primária igual à chave estrangeira), não uma tabela com `id`
próprio. Nem toda `tb_property` tem uma linha aqui.

#### 📌 Atributos
- **property_id (PK, FK)**: Referência para `tb_property`. Mesma coluna serve como chave primária e
  estrangeira (extensão 1:1).
- **main_water_source**: Fonte principal de água da unidade.
  - Valores permitidos: `CONCESSIONARIA`, `POCO_ARTESIANO`, `CISTERNA`, `REUSO`

---

### ⏰ 12.4. Tabela: `tb_property_shift`

Turnos de funcionamento reais da unidade (podem ser vários por propriedade).

#### 📌 Atributos
- **id (PK)**: Identificador do turno.
- **property_id (FK)**: Referência para `tb_property`.
- **start_time**: Horário de início.
- **end_time**: Horário de término (deve ser depois do início).

---

### 🚿 12.5. Tabela: `tb_water_usage_type`

Tipos de uso da água na operação industrial (lookup).

#### 📌 Atributos
- **id (PK)**: Identificador do tipo.
- **name**: Nome do tipo (único).
  - Valores permitidos: `LIMPEZA`, `CONSUMO_HUMANO`, `PROCESSO_PRODUTIVO`, `IRRIGACAO`
- **description**: Descrição opcional.

---

### 🔗 12.6. Tabela: `tb_property_water_usage`

Relacionamento N:N entre propriedades e tipos de uso da água.

#### 📌 Atributos
- **id (PK)**: Identificador do relacionamento.
- **property_id (FK)**: Referência para `tb_property`.
- **water_usage_type_id (FK)**: Referência para `tb_water_usage_type`.

---

### 📆 12.7. Tabela: `tb_property_operation_day`

Dias da semana em que a unidade opera — reaproveita `tb_day_of_week`, já existente.

#### 📌 Atributos
- **id (PK)**: Identificador do relacionamento.
- **property_id (FK)**: Referência para `tb_property`.
- **day_of_week_id (FK)**: Referência para `tb_day_of_week`.

---

### 💰 12.8. Tabela: `tb_investment_scenario`

Cenário de investimento (CAPEX) — reforma hidráulica, reuso de água cinza, captação de chuva. Dado de
referência estático, não depende de telemetria. Valores pesquisados (mercado brasileiro, contexto
industrial/comercial), não fictícios.

#### 📌 Atributos
- **id (PK)**: Identificador do cenário.
- **organization_id (FK, opcional)**: Referência para `tb_organization`. `NULL` = cenário genérico, não
  ligado a uma empresa específica.
- **name**: Nome do cenário.
- **investment_value**: Valor do investimento (≥ 0).
- **reduction_pct**: Percentual de redução de consumo esperado (0-100).
- **annual_savings_value**: Economia anual esperada (≥ 0).
- **payback_months**: Prazo de retorno em meses (opcional, ≥ 0).
- **description**: Descrição opcional.

---

## 🗄️ 13. Tabela: `tb_backup_restore_log`

Registra cada execução do teste de restauração de backup, uma linha por
tabela verificada — ver `backup-recuperacao.md` para o procedimento.

### 📌 Atributos
- **id (PK)**: Identificador.
- **started_at**: Início do teste de restauração.
- **finished_at**: Fim do teste de restauração. NULL enquanto o teste está em andamento.
- **status**: `RUNNING`, `SUCCESS` ou `ERROR` — resultado da verificação daquela tabela.
- **table_name**: Tabela verificada nesse teste.
- **expected_row_count**: Quantidade de linhas esperada, conforme o manifesto gerado no backup.
- **restored_row_count**: Quantidade de linhas realmente restauradas no banco descartável.
- **note**: Observação livre sobre a execução.

---

## 🧾 14. Tabela: `tb_last_water_bill`

Guarda a última conta de água conhecida de cada usuário, usada nas
estimativas de gasto do app.

### 📌 Atributos
- **id (PK)**: Identificador.
- **user_id (FK)**: Referência para `tb_user`. Único em conjunto com `month`.
- **month**: Mês de referência da conta. Sempre o primeiro dia do mês (CHECK).
- **total_value**: Valor total pago na conta (>= 0).
- **m3_value**: Consumo em m³ registrado na conta (>= 0).

---

## 🤖 15. Tabela: `tb_log_rpa`

Registra cada execução do RPA que migra dado do banco legado (Primeiro
Ano) para este banco.

### 📌 Atributos
- **id (PK)**: Identificador.
- **started_at**: Início da execução.
- **finished_at**: Fim da execução. NULL enquanto em andamento.
- **status**: `RUNNING`, `SUCCESS` ou `ERROR`.
- **inserted_count**: Quantidade de registros inseridos (>= 0).
- **updated_count**: Quantidade de registros atualizados (>= 0).
- **deleted_count**: Quantidade de registros excluídos (>= 0).
- **validation_error_count**: Quantidade de erros de validação (>= 0).
- **error_message**: Mensagem de erro, quando a execução falha. NULL quando não há erro.

---

## 📚 16. Tabela: `tb_data_catalog`

Catálogo técnico de metadados do schema — uma linha por coluna de cada
tabela funcional, usado pra governança de dados (classificação de
sensibilidade). Não cobre as tabelas `tb_log_*` de auditoria, que são
espelhos automáticos das tabelas principais.

### 📌 Atributos
- **id (PK)**: Identificador.
- **table_name**: Nome da tabela documentada. Único em conjunto com `column_name`.
- **column_name**: Nome da coluna documentada.
- **data_type**: Tipo da coluna (ex. `VARCHAR(60)`).
- **description**: Descrição da coluna.
- **business_rule**: Regra de negócio associada à coluna, quando houver.
- **access_level**: Classificação de sensibilidade — `PUBLICO`, `INTERNO`, `RESTRITO` ou `SENSIVEL` (este último para PII/LGPD, ex. e-mail, telefone, senha, data de nascimento).
