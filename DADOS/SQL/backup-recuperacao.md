# Backup e Recuperação de Falhas — PostgreSQL 

Este documento define como o banco relacional do Projeto Delta é protegido
contra perda ou corrupção de dados, e o que fazer quando isso acontece.

## 1. Objetivo e escopo

O Projeto Delta guarda os dados cadastrais e de consumo de água num banco
PostgreSQL hospedado no [Neon](https://neon.tech), um serviço gerenciado
(ou seja: quem cuida do servidor, do disco e da maior parte da
infraestrutura é o Neon, não a equipe do projeto). Este documento cobre
**só esse banco**.

## 2. Conceitos-base

Antes de entrar em procedimento, dois termos que o resto do documento usa
o tempo todo:

- **RPO (Recovery Point Objective)**: quantidade máxima de dado que a
  equipe aceita perder se algo der errado agora. Se o RPO é de 6 horas,
  significa que, na pior das hipóteses, o restauro mais recente
  disponível tem até 6 horas de atraso em relação ao momento da falha,
  tudo que foi gravado nesse intervalo pode não voltar.
- **RTO (Recovery Time Objective)**: quanto tempo o banco pode ficar fora
  do ar até voltar a funcionar, contado a partir do momento em que o
  problema é percebido.

E duas formas diferentes de proteger o banco, que este documento combina:

- **Backup lógico**: um arquivo (`pg_dump`) com o conteúdo do banco
  exportado num formato que o próprio Postgres sabe ler de volta
  (`pg_restore`). É "tirar uma foto" do banco num instante específico e
  guardar essa foto em outro lugar.
- **PITR (Point-in-Time Recovery)**: um recurso do Neon que grava
  continuamente o histórico de mudanças do banco, permitindo voltar para
  *qualquer* momento dentro de uma janela de tempo (não só para os
  instantes em que alguém tirou uma "foto"). É mais preciso que o backup
  lógico, mas só cobre o período que o plano gratuito garante.

## 3. RPO e RTO do Projeto Delta

**RPO: até 6 horas.** O Neon mantém PITR continuamente pelas últimas 6
horas no plano gratuito (limite de 1 GB de mudanças acumuladas nesse
período). Para cobrir o que fica *fora* dessa janela, um `pg_dump`
completo do banco roda automaticamente a cada 6 horas. Juntando
os dois: em qualquer momento, o ponto de restauração disponível mais
antigo nunca fica a mais de ~6h de distância da falha, seja pelo PITR
(dentro da janela) ou pelo `pg_dump` mais recente (fora dela).

**RTO: 11 segundos, medido em 26/09/2026.** Restauração completa (28
tabelas, ~2.700 linhas) mais a verificação de contagem, contra o banco
real de produção.

## 4. Estratégia de backup

Duas camadas, uma cobrindo a limitação da outra:

1. **PITR do Neon (camada primária)**: cobertura contínua das últimas 6h,
   sem nenhuma ação manual da equipe. É a primeira opção sempre que o
   problema aconteceu recentemente.
2. **`pg_dump` automatizado (camada complementar)**:  um workflow do
   GitHub Actions (`.github/workflows/backup-postgres.yml` no
   `delta-sql-database`) roda a cada 6 horas, exporta o banco inteiro e
   guarda o resultado como artefato da execução, fora do Neon. Existe porque é uma cópia fora do Neon, protege contra um problema no próprio provedor (conta suspensa,projeto apagado por engano), não só contra um erro no banco.

## 5. Procedimento de recuperação por gravidade

Do cenário mais simples ao mais grave:

1. **Neon fora do ar temporariamente** (instabilidade do serviço, não
   perda de dado): aguardar e reconectar. Nada para restaurar.
2. **Dado apagado ou corrompido, aconteceu há menos de 6 horas**: usar o
   PITR do Neon, restaurar o projeto para um instante anterior ao
   problema.
3. **Aconteceu há mais de 6 horas, ou o PITR não é suficiente** (ex.: o
   próprio Neon está inacessível): restaurar a partir do `pg_dump`
   automatizado mais recente disponível nos artefatos do workflow.
4. **Só uma tabela específica foi corrompida** (ex.: `tb_region_rate`):
   `pg_restore` permite restaurar uma única tabela do `pg_dump`, sem
   mexer no resto do banco.
5. **Cenário extremo: nem o PITR nem o `pg_dump` estão disponíveis**
   (ex.: o próprio Neon ficou inacessível por tempo indeterminado, ou
   ainda não existe nenhum backup rodado). Como último recurso, dá pra
   criar um projeto novo no Neon, aplicar o schema do zero (os scripts
   presentes no `delta-database`) e rodar o `delta-rpa` apontando pra esse
   banco novo — ele importa o dado do banco legado. Isso **não recupera os
   registros recentes**, só o dado fundacional que o RPA migra do banco
   legado, mas devolve o sistema a um estado funcional em vez de ficar
   totalmente fora do ar.


## 6. Registro e trilha de auditoria
Cada execução do teste de restauração grava uma linha por tabela na
tabela `tb_backup_restore_log`, no próprio banco: quando começou e
terminou, se bateu (`SUCCESS`) ou não (`ERROR`), quantas linhas eram
esperadas e quantas realmente vieram na restauração. É a forma de
qualquer pessoa da equipe conferir, sem precisar perguntar a ninguém,
quando foi o último teste de restauração e se ele funcionou.


## 7. Anexo técnico

### 7.1. Comandos de backup e restauração

O repositório `delta-sql-database` tem um script (`backup_db.py`) que
executa os dois comandos abaixo automaticamente, além de conferir as
contagens de linha e gravar o resultado em `tb_backup_restore_log`.

Pra rodar localmente sem instalar nada (Python, cliente do Postgres na
versão certa) na própria máquina, o repositório também tem um
`docker-compose.yml` que já cuida disso:

```bash
docker compose run --rm tools python backup_db.py backup
docker compose run --rm tools python backup_db.py restore-test --yes
```

As credenciais de conexão (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_SSLMODE`) vêm do `.env` local ou, no workflow do
GitHub Actions, dos *secrets* do repositório.

### 7.2. Como confirmar a janela de PITR no Neon

1. No [console do Neon](https://console.neon.tech), abrir o projeto do
   Delta.
2. Em **Branches**, criar uma branch de teste a partir do branch
   principal, confirma que o recurso de branching (base do PITR)
   funciona no projeto.
3. Em **Settings** (ou **Billing**, dependendo da versão do console),
   procurar "Point-in-time restore" / "Restore window" e anotar o valor
   exato mostrado, é esse número que substitui a estimativa da seção 3.
4. Restaurar um instante específico: **Branches** → **Restore** →
   escolher o timestamp desejado.

### 7.3. Workflow de backup automatizado

Arquivo: `.github/workflows/backup-postgres.yml` (repositório
`delta-sql-database`).

- Roda sozinho a cada 6 horas (`cron: "0 */6 * * *"`) e faz só o backup:
  `pg_dump` contra o Neon, resultado publicado como artefato da execução
  (guardado por 7 dias, o suficiente para ~28 backups disponíveis a
  qualquer momento, sem estourar o espaço gratuito de armazenamento de
  artefatos do GitHub).
