### MOD-12 — Criar tabela técnica de catálogo de metadados com tabelas, colunas, regras de negócio e níveis de acesso

**Evidência direta:**

- [Definição da tabela `tb_data_catalog`](https://github.com/delta-app-ofc/delta-sql-database/blob/main/tables/tb_data_catalog.sql)
- [Carga do catálogo do banco relacional](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-catalogo-dados.sql)
- [Carga do catálogo do Data Mart](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-catalogo-datamart.sql)
- [Geração dos comentários das colunas a partir do catálogo](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-comments.sql)
- [Governança de acesso](../governanca-acesso.md)
- [Catálogo de `tb_user`: coluna, tipo, regra e nível de acesso](../anexos/evidencias-requisitos/mod-12-catalogo-tb-user.png)

**Localização e como comprovar:**

A tabela `tb_data_catalog` guarda uma linha por coluna das tabelas funcionais e das camadas do Data Mart.

| Coluna | Conteúdo |
|---|---|
| `table_name` | Tabela ou view documentada (por exemplo `tb_user` ou `gold.dm_property`) |
| `column_name` | Coluna documentada |
| `data_type` | Tipo de dado |
| `description` | Descrição do significado da coluna |
| `business_rule` | Regra de negócio, como `CHECK`, unicidade, obrigatoriedade e valores permitidos |
| `access_level` | Nível de acesso: `PUBLICO`, `INTERNO`, `RESTRITO` ou `SENSIVEL` |

A restrição `uq_tb_data_catalog_table_column` impede duas linhas para a mesma coluna, e `chk_tb_data_catalog_access_level` limita os níveis aceitos.

#### 1. Níveis de acesso

| Nível | Critério |
|---|---|
| `PUBLICO` | Valor de referência, sem sensibilidade |
| `INTERNO` | Dado operacional do negócio, sem identificar pessoa diretamente |
| `RESTRITO` | Identifica pessoa ou local com mais precisão, ou é dado administrativo |
| `SENSIVEL` | Credencial ou dado pessoal sob a LGPD (e-mail, telefone, senha e data de nascimento) |

#### 2. Cobertura

- `script-catalogo-dados.sql` cadastra **132 colunas** do banco relacional: 38 `PUBLICO`, 71 `INTERNO`, 19 `RESTRITO` e 4 `SENSIVEL`.
- `script-catalogo-datamart.sql` cadastra **129 colunas** dos schemas `stage`, `silver`, `gold` e `dw`: 68 `PUBLICO`, 53 `INTERNO` e 8 `RESTRITO`.
- As tabelas `tb_log_*` não entram no catálogo, porque são espelhos automáticos das tabelas principais e não acrescentam metadado novo.
- `script-comments.sql` usa o catálogo como fonte única para gerar `COMMENT ON COLUMN`, e as tabelas `tb_log_*` herdam o comentário da coluna correspondente.

#### 3. Como comprovar

1. Executar os scripts na ordem de `setup_db.py`, incluindo os dois scripts de catálogo e `script-comments.sql`.
2. Executar `SELECT access_level, COUNT(*) FROM tb_data_catalog GROUP BY access_level;` e conferir a distribuição.
3. Executar `SELECT * FROM tb_data_catalog WHERE table_name = 'tb_user';` e conferir descrição, regra e nível de acesso de cada coluna.
4. Executar `\d+ tb_user` e conferir os comentários das colunas, gerados a partir do catálogo.
