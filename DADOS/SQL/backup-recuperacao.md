# Backup e Recuperação de Falhas — PostgreSQL (Projeto Delta)

Este documento define os procedimentos de backup e recuperação de falhas do
banco relacional do Projeto Delta (`delta-sql-database`). Complementa
[`governanca-acesso.md`](./governanca-acesso.md) (quem pode acessar o quê) e
[`modelagem-relacional.md`](./modelagem-relacional.md) (o que existe).

## 1. Situação atual

Hoje não existe uma infraestrutura de produção definida — o banco roda
localmente via Docker (ex. `docker-compose.dev.yml` do `delta-business-rules`,
que sobe um Postgres com o schema de `delta-sql-database` aplicado). Este
documento cobre esse cenário. A seção 4 lista o que muda se/quando o projeto
migrar pra um serviço gerenciado.

## 2. Backup

### 2.1. Comando

Usa `pg_dump` no formato *custom* (`-Fc`), que permite restauração seletiva
(tabela por tabela, se necessário) e já vem comprimido:

```bash
pg_dump \
  --host="$SECOND_YEAR_DB_HOST" \
  --port="$SECOND_YEAR_DB_PORT" \
  --username="$SECOND_YEAR_DB_USER" \
  --dbname="$SECOND_YEAR_DB_NAME" \
  --format=custom \
  --file="backups/delta_$(date +%Y-%m-%d_%H%M).dump"
```

As variáveis `SECOND_YEAR_DB_*` são as mesmas já usadas por `setup_db.py`
(ver `.env.example` na raiz de `delta-sql-database`) — o comando funciona
tanto contra o Postgres local do Docker quanto contra qualquer outro host,
sem precisar reescrever nada além do `.env`.

### 2.2. Frequência e retenção

Proposta adequada ao porte do projeto (não uma política enterprise):

- **Frequência**: 1 backup por dia, ao final do dia de desenvolvimento (ou
  antes de qualquer operação arriscada — `script-schema.sql` dá `DROP TABLE`
  em tudo).
- **Retenção**: manter os últimos 7 backups diários. Um script simples de
  limpeza (`find backups/ -mtime +7 -delete`) já resolve, sem precisar de
  ferramenta dedicada nesse estágio do projeto.
- **Local de armazenamento**: fora do container do Postgres (ex. pasta
  `backups/` no host, fora do volume Docker) — um backup que mora no mesmo
  volume que ele protege não serve de nada se o volume for perdido.

## 3. Recuperação de falhas

Do cenário mais simples ao mais grave:

1. **Container caiu, mas o volume Docker está intacto**: `docker compose up
   -d` de novo. Os dados persistem no volume nomeado — não é preciso
   restaurar nada.
2. **Container e volume foram removidos, mas o schema não mudou**: recriar o
   container (`docker compose up -d`), rodar `setup_db.py` (schema +
   dataload) e, se havia dado real de teste que importava preservar,
   restaurar por cima com `pg_restore` (comando abaixo).
3. **Perda total (volume apagado, banco corrompido, migração mal aplicada)**:
   restaurar do último `pg_dump`:

```bash
pg_restore \
  --host="$SECOND_YEAR_DB_HOST" \
  --port="$SECOND_YEAR_DB_PORT" \
  --username="$SECOND_YEAR_DB_USER" \
  --dbname="$SECOND_YEAR_DB_NAME" \
  --clean --if-exists \
  backups/delta_2026-09-20_1800.dump
```

`--clean --if-exists` derruba os objetos existentes antes de recriar,
evitando conflito de "já existe" numa restauração sobre um banco não vazio.

4. **Restauração seletiva** (ex. só corrompeu `tb_region_rate`): `pg_restore`
   aceita `--table=tb_region_rate` pra restaurar só uma tabela do dump,
   graças ao formato `-Fc` escolhido na seção 2.1.

## 4. Se migrar pra um serviço gerenciado

Esta seção precisa ser **reescrita**, não só complementada, quando a decisão
de hospedagem for tomada — hoje não há infraestrutura de produção definida.
Serviços gerenciados (AWS RDS, Supabase, Railway, entre outros) costumam já
oferecer backup automático point-in-time e retenção configurável nativamente,
o que tornaria as seções 2 e 3 acima (cron manual de `pg_dump`) redundantes
ou só uma camada extra de segurança. Ao decidir o serviço, revisar:

- O que o serviço já cobre nativamente (RPO/RTO do backup automático);
- Se ainda vale manter um `pg_dump` manual periódico como cópia fora do
  provedor (proteção contra falha do próprio provedor, não só do banco);
- Quem tem permissão pra disparar uma restauração (ligar com
  `governanca-acesso.md` — hoje só `sys_devops` teria essa responsabilidade).
