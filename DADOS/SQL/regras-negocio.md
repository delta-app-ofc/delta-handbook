# 📘 Regras de Negócio — Projeto Delta (PostgreSQL)

Este documento descreve todas as regras de negócio do banco de dados relacional PostgreSQL do Projeto Delta.

---

## 1. 🔤 Padrão de letras nos registros

Todos os **dados inseridos no banco devem ser armazenados em MAIÚSCULAS**, quando aplicável.

✔ Exemplos:
- nomes → "MARIA SILVA"
- cidades → "SAO PAULO"
- tipos → "RESIDENCIAL", "COMERCIAL"

---

## 2. 🌐 Padrão de idioma

- Todos os **objetos do banco de dados devem estar em INGLÊS**
- Isso inclui:
  - tabelas
  - colunas
  - constraints
  - procedures
  - functions

---

## 3. 🔡 Padrão de acentuação

- Os **registros podem conter acentuação normalmente**
- Já os **objetos do banco NÃO devem conter acentos**
- Isso inclui:
  - tabelas
  - colunas
  - constraints
  - procedures
  - functions

---

## 4. 🏷️ Prefixos utilizados no projeto

---

## 4.1 📦 Prefixo de tabelas

- Prefixo: `tb_`
- Todas as tabelas do sistema devem seguir este padrão

✔ Exemplos:
tb_user  
tb_property  
tb_device  

---

## 4.2 🔑 Prefixo de Foreign Keys (FK)

- Prefixo: `fk_`
- Formato:
    fk_<tabela_origem>_<tabela_destino>

✔ Exemplos:
fk_user_property_user  
fk_user_property_property  

---

## 4.3 ✅ Prefixo de CHECK constraints

- chk_ → regras de validação

✔ Exemplos:
chk_property_type  
chk_region_name 
---

## 4.4 🔒 Prefixo de UNIQUE constraints

- uq_ → regras de unicidade

✔ Exemplos:
uq_user_email  
uq_user_property  

---

## 4.5 Prefixo de SYS 

Todas as roles seguem o prefixo: sys_
✔ Exemplos:
sys_devops  
sys_analyst  
---