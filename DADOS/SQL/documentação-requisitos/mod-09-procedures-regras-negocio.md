### MOD-09 — Criar no mínimo duas Procedures para regras críticas de negócio

**Evidência direta:**

- [Pasta das Procedures](https://github.com/delta-app-ofc/delta-sql-database/tree/main/procedures)
- [Script que agrega as Functions e Procedures](https://github.com/delta-app-ofc/delta-sql-database/blob/main/script-optimization.sql)
- [Procedure de reajuste de tarifa](https://github.com/delta-app-ofc/delta-sql-database/blob/main/procedures/sp_change_region_rate.sql)
- [Procedure de cadastro de propriedade](https://github.com/delta-app-ofc/delta-sql-database/blob/main/procedures/sp_register_property.sql)
- [Documentação das Functions e Procedures](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/otimizacao.md)

- [Print das cinco Procedures do schema public](../anexos/evidencias-requisitos/mod-09-procedures-01.png)
- [Chamada de `sp_change_region_rate`](../anexos/evidencias-requisitos/mod-09-chamada-sp-change-region-rate.png)
- [Tarifa anterior encerrada e nova tarifa registrada](../anexos/evidencias-requisitos/mod-09-tarifa-encerrada-e-nova.png)

**Localização e como comprovar:**

O banco possui **cinco Procedures** em `procedures/`, reunidas em `script-optimization.sql`. Cada uma executa uma operação com várias etapas dentro de uma única chamada e transação.

| Procedure | Regra de negócio |
|---|---|
| `sp_change_region_rate` | Valida região, classificação e valor, encerra a tarifa vigente e insere a nova. Uma combinação de região e classificação nunca tem duas tarifas vigentes |
| `sp_register_property` | Valida usuário ativo e endereço, insere o imóvel e cria o vínculo em `tb_user_property`. Devolve o id pelo parâmetro `OUT` |
| `sp_disable_user` | Marca o usuário como inativo e desativa seus dispositivos, preservando o histórico |
| `sp_update_property_classification` | Troca a classificação do imóvel pelo nome informado. A mudança é registrada pelo trigger `trg_log_property` |
| `sp_register_user_access` | Valida que o usuário está ativo e registra o acesso em `tb_user_access_log` (MOD-14) |

#### Por que Procedures

As Procedures (`CALL`) agrupam alterações em mais de uma tabela. Quando uma validação falha, a exceção desfaz a operação inteira. Assim, `sp_disable_user` nunca deixa o usuário inativo com dispositivos ainda ativos, e `sp_change_region_rate` nunca deixa duas tarifas vigentes para a mesma combinação.

#### Como comprovar

1. Executar `script-schema.sql`, `script-optimization.sql`, `script-audit.sql` e `script-dataload.sql`.
2. Executar `CALL sp_change_region_rate(1, 1, 31.00, CURRENT_DATE);` e consultar `tb_region_rate` para ver a tarifa anterior encerrada e a nova registrada.
3. Consultar `tb_log_region_rate` e conferir os registros de auditoria gerados pela alteração.
4. Executar `CALL sp_disable_user(<id>);` e conferir `is_active = FALSE` no usuário e nos dispositivos.
