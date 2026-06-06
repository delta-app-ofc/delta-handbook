# Governança de Acesso — Projeto Delta

Este documento define as roles e permissões do banco de dados relacional PostgreSQL do Projeto Delta.

Estruturas consideradas:

- tbl_alerta  
- tbl_dispositivo  
- tbl_habito  
- tbl_instalacao  
- tbl_meta_consumo  
- tbl_tarifa_agua  
- tbl_usuario  
- tbl_usuario_habito  
- tbl_usuario_instalacao  
- views analíticas  
- functions, procedures, triggers e auditoria  

---

## sys_engenheiro_dados

Permissões:
- Criação e manutenção de tabelas normalizadas
- Definição de PKs, FKs e constraints
- Criação de functions
- Criação de procedures
- Criação de triggers de auditoria
- Criação de views analíticas
- Controle estrutural do banco

---

## sys_desenvolvedor_backend

Permissões:
- CRUD completo (SELECT, INSERT, UPDATE, DELETE) nas tabelas do sistema

---

## sys_analista_bi

Permissões:
- Apenas SELECT em views analíticas
- Acesso à camada analítica

---

## sys_devops

Permissões:
- Gerenciamento de usuários e roles
- Backup e restore do banco
- Controle de permissões e segurança
- Administração do PostgreSQL

---

## sys_primeiro_ano

Permissões:
- Apenas leitura (SELECT)
- Acesso restrito às tabelas do sistema
- Sem permissões de escrita ou execução

---

# 2. Atribuição de Usuários

| Integrante | Disciplinas | Roles |
|------------|------------|------|
| Ana | UX, DAD, BI, EQS | sys_analista_bi |
| Davi | Mobile, DAD, DS2, EQS | sys_desenvolvedor_backend |
| João | Mobile, DS2, IA, EQS | sys_desenvolvedor_backend |
| Mariana | MDD, BD2, DS2, IA, EQS | sys_engenheiro_dados, sys_desenvolvedor_backend |
| Rahquel | Mobile, DAD, UX, EQS | sys_desenvolvedor_backend |
| Samuel | BI, DevOps, BD2, IA, MDD, EQS | sys_devops, sys_engenheiro_dados, sys_analista_bi |
| Primeiro Ano | Apoio / Leitura | sys_primeiro_ano |

---
