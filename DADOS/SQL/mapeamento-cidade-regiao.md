# 🏙️ Mapeamento Cidade → Região de Tarifa

Este documento explica como o Delta descobre qual tarifa de água da Sabesp vale para um endereço: a cidade informada no cadastro é procurada na tabela `tb_city_region`, que devolve a região (`tb_region`) e, com ela, as tarifas de `tb_region_rate`.

🔗 Repositórios: [delta-database](https://github.com/delta-app-ofc/delta-database) (tabela e carga) e [delta-api-postgres](https://github.com/delta-app-ofc/delta-api-postgres) (quem preenche a região).

---

## 1. Por que existe

Antes, a API recebia o `regionId` pronto do aplicativo. Nada ligava uma cidade a uma região, então um endereço em Osasco só entrava em `GRANDE_SP` se quem chamava a API enviasse o id certo. Como a região define a tarifa, um id errado gerava custo de água errado.

Agora o aplicativo **não envia mais a região**. A API a calcula pela cidade e pela UF.

## 2. Fluxo

```
Usuário digita o CEP
  → o app consulta a API de CEP e preenche cidade e UF ("Osasco", "SP")
  → a API recebe city + state no cadastro do endereço
  → procura (city, state) em tb_city_region, sem diferenciar maiúsculas
  → achou: grava tb_address.region_id
  → não achou: erro 400 "O Delta atende apenas cidades de São Paulo cobertas pela Sabesp."
```

| Antes | Depois |
| --- | --- |
| O app enviava `regionId` no endereço | O app envia só `cep`, `city`, `state` (e coordenadas, se tiver) |
| Qualquer id de região era aceito | A região vem sempre da cidade |
| Cidade sem tarifa cadastrava com a região escolhida | Cidade sem tarifa não cadastra e o app mostra o erro |

O erro vale tanto para cidade de outro estado quanto para cidade paulista que não está nos cinco grupos abaixo.

## 3. A tabela `tb_city_region`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | `SERIAL` | Chave primária |
| `city` | `VARCHAR(60)` | Nome como a API de CEP devolve (acento e maiúscula inicial). Único junto com `state` |
| `state` | `CHAR(2)` | UF em maiúsculas (`CHECK`) |
| `region_id` | `INTEGER` | FK para `tb_region` |

- A comparação ignora maiúsculas (`LINS` acha `Lins`), mas **não ignora acento**. Isso basta porque a cidade vem preenchida pela API de CEP, que usa a grafia do IBGE. Se um dia o usuário puder digitar a cidade, será preciso comparar sem acento (extensão `unaccent`).
- Latitude e longitude de `tb_address` **não** entram na decisão.
- A tabela é de referência: só muda por script, por isso não tem trigger de auditoria.

## 4. Cidades atendidas

Total: 45 cidades em 5 regiões.

| Região | Tabela tarifária | Cidades |
| --- | --- | --- |
| `GRANDE_SP` (33) | Tabela 1 | São Paulo; Arujá, Biritiba Mirim, Ferraz de Vasconcelos, Itaquaquecetuba, Poá, Salesópolis, Suzano; Caieiras, Cajamar, Francisco Morato, Franco da Rocha, Guarulhos, Mairiporã; Barueri, Carapicuíba, Cotia, Itapevi, Jandira, Osasco, Pirapora do Bom Jesus, Santana de Parnaíba, Taboão da Serra, Vargem Grande Paulista; Diadema, Embu das Artes, Embu-Guaçu, Itapecerica da Serra, Ribeirão Pires, Rio Grande da Serra, São Bernardo do Campo; Guararema, Santa Isabel |
| `BRAGANCA_PAULISTA` (8) | Tabela 2 | Bragança Paulista, Joanópolis, Nazaré Paulista, Pedra Bela, Pinhalzinho, Piracaia, Socorro, Vargem |
| `LINS` (1) | Tabela própria de Lins | Lins |
| `PRESIDENTE_PRUDENTE` (1) | Tabela 8 | Presidente Prudente |
| `ADAMANTINA_PIRAPOZINHO` (2) | Tabela 7 | Adamantina, Pirapozinho |

As Tabelas 7 e 8 trazem valores próprios só para algumas categorias; nas demais valem os preços da Tabela 5 (interior).

## 5. Como a lista foi levantada

Cada cidade só entrou com fonte oficial. Consulta feita em 30/10/2026.

1. **Anexo IV do Contrato de Concessão 01/2024 (URAE-1 Sudeste)**, item 6.4: diz quais municípios usam cada tabela. A Tabela 1 vale para as unidades de negócio OC, OL, OO, ON (exceto 8 municípios) e OS, mais Guararema e Santa Isabel. A Tabela 2 lista os 8 municípios de Bragança Paulista e região. As Tabelas 7 e 8 citam Adamantina, Pirapozinho e Presidente Prudente pelo nome. [Anexo IV (PDF oficial)](https://urae1.sp.gov.br/wp-content/uploads/sites/26/2025/02/ANEXO-IV_Apostilado.pdf).
2. **Deliberação ARSESP nº 1.749, de 1º/12/2025**: reajuste vigente desde 01/01/2026. Cita Lins como caso à parte, com tabela tarifária própria incluída no Anexo 4 do contrato pelo 1º Termo Aditivo.
3. **[Relação de Municípios Operados pela Sabesp](anexos/sabesp-municipios-por-unidade.pdf)** (PDF guardado neste repositório): lista os municípios de cada unidade de negócio. Foi usado para transformar "unidades OC, OL, OO, ON, OS" em nomes de cidades. O PDF usa os códigos antigos ML, MN, MO e MS para Leste, Norte, Oeste e Sul; a equivalência com OL, ON, OO e OS foi deduzida pelos nomes das unidades e não está escrita em nenhum dos documentos.
4. **API de municípios do IBGE** (estado 35): todos os nomes foram conferidos. A única diferença foi `Biritiba-Mirim` no PDF da Sabesp, que o IBGE (e a API de CEP) escreve `Biritiba Mirim`.

## 6. Limites conhecidos

- **Não cobertas:** as demais cidades da Sabesp (Tabela 5 do interior, Baixada Santista, Litoral Norte, Vale do Ribeira, Vale do Paraíba etc.) e todas as cidades de outros operadores. Elas recebem o erro do item 2.
- A "Relação de Municípios" não tem data impressa. A unidade da capital aparece como "Diretoria Metropolitana" e o contrato de 2024 fala em OC. Confirme a lista na Sabesp quando houver nova revisão tarifária.
- O Anexo IV de fevereiro de 2025 ainda não traz a Tabela de Lins. Ela vem do termo aditivo citado na Deliberação 1.749.
- O `state` precisa chegar como UF (`SP`). A API de CEP já devolve assim.

## 7. Como atualizar

1. Conferir nas fontes do item 5 se alguma cidade entrou ou saiu de uma tabela.
2. Validar o nome na [lista do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios).
3. Alterar `script-dataload.sql` (carga de teste) e criar um script de migração para ambientes já em uso.
4. Atualizar a tabela do item 4 e a data de consulta do item 5.
