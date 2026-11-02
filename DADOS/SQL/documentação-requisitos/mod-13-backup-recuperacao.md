### MOD-13 — Documentar procedimentos para backup e recuperação de falhas

**Evidência direta:**

- [Documentação de backup e recuperação](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/backup-recuperacao.md)
- [Script de backup e teste de restauração](https://github.com/delta-app-ofc/delta-sql-database/blob/main/backup_db.py)
- [Workflow automatizado de backup](https://github.com/delta-app-ofc/delta-sql-database/blob/main/.github/workflows/backup-postgres.yml)
- [Tabela de registro dos testes de restauração](https://github.com/delta-app-ofc/delta-sql-database/blob/main/tables/tb_backup_restore_log.sql)
- [Evidência da janela de PITR no Neon](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/anexos/evidencia-neon.png)

**Localização e como comprovar:**

O banco PostgreSQL do Projeto Delta é hospedado no Neon. A estratégia usa duas camadas, e uma cobre a limitação da outra.

#### 1. Estratégia de backup

| Camada | Mecanismo | Cobertura |
|---|---|---|
| Primária | PITR (Point-in-Time Recovery) do Neon | Restauração para qualquer instante das últimas 6 horas, sem ação manual |
| Complementar | `pg_dump` pelo workflow `backup-postgres.yml` | Exporta o banco inteiro a cada 6 horas e guarda o resultado como artefato, fora do Neon |

O `pg_dump` protege também contra falhas do próprio provedor, como conta suspensa ou projeto apagado por engano.

#### 2. Objetivos de recuperação

- **RPO de até 6 horas:** o ponto de restauração mais antigo nunca fica a mais de cerca de 6 horas da falha, pelo PITR ou pelo `pg_dump` mais recente.
- **RTO medido de 11 segundos em 26/09/2026:** restauração completa de 28 tabelas (cerca de 2.700 linhas) mais a verificação de contagem, contra o banco real.

#### 3. Recuperação por gravidade

1. Neon fora do ar temporariamente: aguardar e reconectar, sem nada para restaurar.
2. Dado apagado ou corrompido há menos de 6 horas: restaurar o projeto pelo PITR para um instante anterior ao problema.
3. Falha há mais de 6 horas ou PITR insuficiente: restaurar a partir do `pg_dump` mais recente nos artefatos do workflow.
4. Uma única tabela corrompida: `pg_restore` restaura só aquela tabela, sem mexer no restante.
5. Nenhum backup disponível: criar um projeto novo no Neon, aplicar os scripts do schema e executar o `delta-rpa` para importar o dado fundacional do banco legado.

#### 4. Teste de restauração e trilha de auditoria

`python backup_db.py restore-test --yes` restaura o dump em um banco de teste e compara, tabela por tabela, a contagem esperada com a restaurada. Cada comparação é gravada em `tb_backup_restore_log` (início, fim, `SUCCESS` ou `ERROR`, linhas esperadas e restauradas), e qualquer pessoa da equipe consegue consultar quando foi o último teste e se ele passou.

#### 5. Como comprovar

1. Abrir `backup-postgres.yml` e conferir o `cron` `0 */6 * * *` e o disparo manual (`workflow_dispatch`).
2. Abrir a aba Actions do `delta-sql-database` e conferir as execuções do workflow `Backup Postgres` e seus artefatos.
3. Executar `SELECT * FROM tb_backup_restore_log ORDER BY id DESC;` e conferir os testes de restauração registrados.
4. Abrir `evidencia-neon.png` e conferir a janela de PITR configurada no Neon.
