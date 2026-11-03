# Evidência de backup e recuperação — MOD-13

## Objetivo

Registrar o teste executado em 02/11/2026 com `backup_db.py`: geração de um backup completo em formato custom e restauração em um PostgreSQL 18 local separado do banco de origem.

## Resultado confirmado

As 47 tabelas públicas verificadas pelo script apresentaram as mesmas quantidades de registros do manifesto. O teste terminou com sucesso e gravou 47 resultados em `tb_backup_restore_log` no banco de origem.

- [Print da consulta de confirmação](resultado-backup.png): `SUCCESS`, 47 tabelas e contagens corretas.
- [Saída completa da restauração](resultado-restauracao.txt): conferência individual das 47 tabelas.
- [Consultas SQL de verificação](consultas-evidencias.sql): detalhes e resumo do teste mais recente.
- [Relatório da execução](evidencia-execucao.html): contagens antes e depois da atualização e saída da restauração.

## Execução

O backup foi gerado com `python backup_db.py backup` e restaurado com `python backup_db.py restore-test --dump <arquivo.dump> --yes`, usando as ferramentas PostgreSQL 18 da imagem Docker do projeto. As variáveis `TEST_DB_*` apontaram exclusivamente para um container local descartável.

O dump testado foi `delta_2026-11-02_1608.dump`, acompanhado do respectivo `.manifest.json`. Os arquivos de backup permanecem no armazenamento local.

Antes desse backup final, o `setup_db.py` executou uma carga complementar dos dados de referência ausentes e atualizou os dois catálogos e os comentários. O banco passou a conter 371 municípios, 9 regiões, 72 tarifas e 261 entradas no catálogo. As contagens das demais tabelas de dados foram preservadas.

O verificador de `backup_db.py` compara as contagens das tabelas públicas `tb_*`; essa conferência não mede, por si só, a equivalência de cada valor nem o funcionamento das views e rotinas restauradas.
