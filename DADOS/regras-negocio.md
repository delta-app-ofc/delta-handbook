# 📘 Regras de Negócio — Projeto Delta (PostgreSQL)

Este documento descreve todas as regras de negócio do banco de dados relacional PostgreSQL do Projeto Delta.

## 1. Padrão de letras nos registros

Todos os dados inseridos no banco devem ser armazenados em letras minúsculas, quando aplicável.

✔ Exemplos:
- nomes → "maria silva"
- cidades → "sao paulo"
- tipos → "residencial", "comercial"


## 2. Padrão de idioma

- Todos os objetos do banco devem estar em **português**
- Isso inclui tabelas, colunas, constraints e registros

## 3. Padrão de acentuação

- Todos os objetos do banco devem estar sem acentos, quando aplicável, para facilitar consultas e verificações.
- Isso inclui tabelas, colunas, constraints e registros

# 4. Prefixos utilizados no projeto

## 4.1 Prefixo de tabelas

- tbl_ → identifica tabelas do sistema

✔ Exemplos:
tbl_usuario  
tbl_instalacao  
tbl_dispositivo  

---

## 4.2 Prefixo de Foreign Keys (FK)

- fk_ → identifica chaves estrangeiras

Formato:
fk_<tabela_origem>_<tabela_destino>

✔ Exemplos:
fk_usuario_instalacao_usuario  
fk_usuario_instalacao_instalacao  

---

## 4.3 Prefixo de CHECK constraints

- chk_ → regras de validação

✔ Exemplos:
chk_tipo_classificacao  
chk_percentual_consumo  

---

## 4.4 Prefixo de UNIQUE constraints

- uq_ → regras de unicidade

✔ Exemplos:
uq_usuario_instalacao  
uq_usuario_habito  

---

## 4.5 Prefixo de SYS 

Todas as roles seguem o prefixo: sys_
✔ Exemplos:
sys_devops  
sys_analista_bi  
---