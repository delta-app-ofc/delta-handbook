# 🏙️ Mapeamento Município → Grupo Tarifário

Este documento explica como o Delta descobre qual tarifa de água da Sabesp vale para um endereço: o município informado no cadastro é procurado na tabela `tb_municipality`, que devolve o grupo tarifário (`tb_region`) e, com ele, as tarifas de `tb_region_rate`.

🔗 Repositórios: [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database) (tabelas e carga) e [delta-api-postgres](https://github.com/delta-app-ofc/delta-api-postgres) (quem preenche a região).

---

## 1. Por que existe

Antes, a API recebia o `regionId` pronto do aplicativo. Nada ligava uma cidade a uma região, então um endereço em Osasco só entrava em `GRANDE_SP` se quem chamava a API enviasse o id certo. Como a região define a tarifa, um id errado gerava custo de água errado.

Agora o aplicativo **não envia mais a região**. A API a calcula pelo município.

Duas ideias separam o que é local do que é preço:

| Conceito | Tabela | O que guarda |
| --- | --- | --- |
| Onde fica o endereço | `tb_municipality` | Os 371 municípios atendidos pela Sabesp na URAE-1 |
| Qual tabela de preços vale | `tb_region` | 9 grupos tarifários; vários municípios dividem o mesmo grupo |

Dividir assim evita repetir tarifas: os 269 municípios do interior apontam para o mesmo `INTERIOR`, que tem uma única linha de preço por categoria.

## 2. Fluxo

```
Usuário digita o CEP
  → o app consulta a API de CEP e preenche cidade e UF ("Osasco", "SP")
  → a API recebe city + state no cadastro do endereço
  → a UF não é SP?           erro 400
  → procura a cidade em tb_municipality, sem diferenciar maiúsculas
  → achou: grava tb_address.region_id com o grupo do município
  → não achou: erro 400 "O Delta atende apenas cidades de São Paulo cobertas pela Sabesp."
```

| Antes | Depois |
| --- | --- |
| O app enviava `regionId` no endereço | O app envia só `cep`, `city`, `state` e as coordenadas `latitude` e `longitude`, que são obrigatórias |
| Qualquer id de região era aceito | A região vem sempre do município |
| Município sem tarifa cadastrava com a região escolhida | Município sem tarifa não cadastra e o app mostra o erro |

`tb_address` não mudou: continua guardando `city`, `state` e `region_id`. Funções, datamart e a IA seguem lendo esses campos como antes.

## 3. A tabela `tb_municipality`

| Coluna | Tipo | Regra |
| --- | --- | --- |
| `id` | `SERIAL` | Chave primária |
| `name` | `VARCHAR(60)` | Nome como a API de CEP devolve (acento e maiúscula inicial). Único |
| `ibge_code` | `INTEGER` | Código IBGE de 7 dígitos (`CHECK` entre 3500000 e 3599999). Único; serve para conferir o nome |
| `region_id` | `INTEGER` | FK para `tb_region` |

- Não há coluna de UF: a tabela só tem municípios de SP, e a API confere `state = 'SP'` antes de consultar. Isso também resolve nomes repetidos em outros estados (Santa Isabel e Vargem existem em GO e SC).
- A comparação ignora maiúsculas (`LINS` acha `Lins`), mas **não ignora acento**. Basta porque a cidade vem preenchida pela API de CEP, que usa a grafia do IBGE. Se um dia o usuário puder digitar a cidade, será preciso comparar sem acento (extensão `unaccent`).
- Latitude e longitude de `tb_address` **não** entram na decisão.
- A validade das tarifas fica em `tb_region_rate` (`initial_validity` e `final_validity`), não no município.
- A tabela de referência só muda por script, por isso não tem trigger de auditoria.

## 4. Grupos tarifários

Cada grupo é uma tabela do Anexo IV do Contrato de Concessão 01/2024. Os valores de 2026 vêm da [Nota Técnica do 1º Reajuste](anexos/arsesp-nt-1-reajuste-urae1-2026.pdf), com a metodologia descrita em `tariffs/README.md` do delta-business-rules (faixa de 21 a 50 m³, média das sub-faixas social e vulnerável).

| Grupo (`tb_region.name`) | Tabela | Municípios | Quem usa |
| --- | --- | --- | --- |
| `GRANDE_SP` | 1 | 35 | Unidades OC, OL, OO, ON (menos 8) e OS, mais Guararema e Santa Isabel; Mauá e Santo André (ver item 7) |
| `BRAGANCA_PAULISTA` | 2 | 8 | Bragança Paulista e 7 vizinhos, nomeados no contrato |
| `LITORAL` | 3 | 13 | Unidades OX e OI: Baixada Santista e Litoral Norte |
| `VALE_DO_RIBEIRA` | 4 | 18 | Unidade OR, exceto 5 municípios |
| `INTERIOR` | 5 | 269 | Unidades OP, OU, OF, OJ, OM, OT (menos Lins) e 5 municípios da OR; Tapiratiba e Tejupá (ver item 7) |
| `VALE_DO_PARAIBA` | 6 | 24 | Unidade OV, exceto Guararema e Santa Isabel |
| `ADAMANTINA_PIRAPOZINHO` | 7 (+5) | 2 | Adamantina e Pirapozinho |
| `PRESIDENTE_PRUDENTE` | 8 (+5) | 1 | Presidente Prudente |
| `LINS` | 10 | 1 | Lins, com tabela própria |

Total: 371 municípios em 9 grupos. As Tabelas 7 e 8 trazem valores próprios só para algumas categorias; nas demais valem os preços da Tabela 5.

## 5. Municípios por grupo

**GRANDE_SP (35):** Arujá, Barueri, Biritiba Mirim, Caieiras, Cajamar, Carapicuíba, Cotia, Diadema, Embu das Artes, Embu-Guaçu, Ferraz de Vasconcelos, Francisco Morato, Franco da Rocha, Guararema, Guarulhos, Itapecerica da Serra, Itapevi, Itaquaquecetuba, Jandira, Mairiporã, Mauá, Osasco, Pirapora do Bom Jesus, Poá, Ribeirão Pires, Rio Grande da Serra, Salesópolis, Santa Isabel, Santana de Parnaíba, Santo André, Suzano, São Bernardo do Campo, São Paulo, Taboão da Serra, Vargem Grande Paulista.

**BRAGANCA_PAULISTA (8):** Bragança Paulista, Joanópolis, Nazaré Paulista, Pedra Bela, Pinhalzinho, Piracaia, Socorro, Vargem.

**LITORAL (13):** Bertioga, Caraguatatuba, Cubatão, Guarujá, Ilhabela, Itanhaém, Mongaguá, Peruíbe, Praia Grande, Santos, São Sebastião, São Vicente, Ubatuba.

**VALE_DO_RIBEIRA (18):** Barra do Turvo, Cajati, Cananéia, Eldorado, Iguape, Ilha Comprida, Iporanga, Itariri, Jacupiranga, Juquitiba, Juquiá, Miracatu, Pariquera-Açu, Pedro de Toledo, Registro, Sete Barras, São Lourenço da Serra, Tapiraí.

**VALE_DO_PARAIBA (24):** Arapeí, Bananal, Cachoeira Paulista, Campos do Jordão, Canas, Caçapava, Igaratá, Jambeiro, Lagoinha, Lavrinhas, Lorena, Monteiro Lobato, Pindamonhangaba, Queluz, Redenção da Serra, Roseira, Santa Branca, Santo Antônio do Pinhal, Silveiras, São Bento do Sapucaí, São José dos Campos, São Luiz do Paraitinga, Taubaté, Tremembé.

**ADAMANTINA_PIRAPOZINHO (2):** Adamantina, Pirapozinho.

**PRESIDENTE_PRUDENTE (1):** Presidente Prudente. **LINS (1):** Lins.

<details>
<summary>INTERIOR (269 municípios)</summary>

Adolfo, Aguaí, Agudos, Alambari, Alfredo Marcondes, Altair, Alto Alegre, Alumínio, Alvinlândia, Angatuba, Anhembi, Anhumas, Aparecida d'Oeste, Apiaí, Arandu, Araçariguama, Arco-Íris, Arealva, Areiópolis, Aspásia, Assis, Auriflama, Avaré, Avaí, Balbinos, Barra do Chapéu, Barão de Antonina, Bastos, Bento de Abreu, Bernardino de Campos, Bocaina, Bofete, Boituva, Bom Sucesso de Itararé, Boracéia, Borá, Botucatu, Brejo Alegre, Buri, Buritizal, Cabreúva, Caiabu, Cajuru, Campina do Monte Alegre, Campo Limpo Paulista, Capela do Alto, Capão Bonito, Cardoso, Catiguá, Cesário Lange, Charqueada, Colômbia, Conchas, Coroados, Coronel Macedo, Cruzália, Cássia dos Coqueiros, Cândido Rodrigues, Dirce Reis, Divinolândia, Dolcinópolis, Dourado, Duartina, Echaporã, Elias Fausto, Emilianópolis, Espírito Santo do Pinhal, Espírito Santo do Turvo, Estrela d'Oeste, Estrela do Norte, Euclides da Cunha Paulista, Fartura, Fernando Prestes, Fernandópolis, Fernão, Flora Rica, Floreal, Florínea, Flórida Paulista, Franca, Gabriel Monteiro, Gastão Vidigal, General Salgado, Glicério, Guapiara, Guarani d'Oeste, Guareí, Guariba, Guzolândia, Gália, Hortolândia, Iacri, Iaras, Ibirá, Ibiúna, Icém, Indiaporã, Inúbia Paulista, Iperó, Irapuã, Itaberá, Itaoca, Itapetininga, Itapeva, Itapirapuã Paulista, Itaporanga, Itararé, Itatiba, Itatinga, Itaí, Itirapuã, Itobi, Itupeva, Jaborandi, Jales, Jarinu, Jeriquara, Laranjal Paulista, Lourdes, Lucianópolis, Lucélia, Luiziânia, Lupércio, Lutécia, Macedônia, Magda, Marabá Paulista, Maracaí, Marinópolis, Mariápolis, Meridiano, Mesópolis, Mira Estrela, Mirante do Paranapanema, Mococa, Mombuca, Monte Alto, Monte Aprazível, Monte Mor, Monções, Morungaba, Narandiba, Nhandeara, Nipoã, Nova Campina, Nova Canaã Paulista, Nova Granada, Nova Luzitânia, Novo Horizonte, Onda Verde, Oriente, Orindiúva, Oscar Bressane, Osvaldo Cruz, Ouroeste, Palmares Paulista, Palmeira d'Oeste, Paraguaçu Paulista, Paranapanema, Paranapuã, Parapuã, Pardinho, Paulistânia, Paulo de Faria, Paulínia, Pederneiras, Pedranópolis, Pedregulho, Pedrinhas Paulista, Pereiras, Piacatu, Piedade, Pilar do Sul, Piquerobi, Piraju, Piratininga, Planalto, Platina, Poloni, Pongaí, Pontalinda, Pontes Gestal, Populina, Porangaba, Pracinha, Pratânia, Presidente Alves, Presidente Bernardes, Presidente Epitácio, Quadra, Quatá, Queiroz, Regente Feijó, Restinga, Ribeira, Ribeirão Branco, Ribeirão Corrente, Ribeirão do Sul, Ribeirão dos Índios, Ribeirão Grande, Rifaina, Riolândia, Riversul, Rosana, Rubinéia, Rubiácea, Sagres, Salmourão, Saltinho, Salto de Pirapora, Sandovalina, Santa Albertina, Santa Clara d'Oeste, Santa Cruz da Esperança, Santa Cruz do Rio Pardo, Santa Ernestina, Santa Maria da Serra, Santa Mercedes, Santa Rosa de Viterbo, Santa Salete, Santana da Ponte Pensa, Santo Anastácio, Santo Antônio do Jardim, Santo Expedito, Santópolis do Aguapeí, Sarapuí, Sarutaiá, Sebastianópolis do Sul, Serra Azul, Serra Negra, Sud Mennucci, São Francisco, São João da Boa Vista, São João das Duas Pontes, São Manuel, São Miguel Arcanjo, São Roque, Taciba, Taguaí, Tapiratiba, Taquarituba, Taquarivaí, Tarabai, Tarumã, Tatuí, Tejupá, Teodoro Sampaio, Terra Roxa, Timburi, Torre de Pedra, Torrinha, Três Fronteiras, Tupã, Turiúba, Turmalina, Ubirajara, União Paulista, Uru, Urânia, Valentim Gentil, Vitória Brasil, Várzea Paulista, Zacarias, Águas da Prata, Águas de Santa Bárbara, Águas de São Pedro, Álvares Machado, Álvaro de Carvalho, Óleo.

</details>

## 6. Como a lista foi levantada

Consulta feita em 30/10/2026. Cada município só entrou com fonte oficial.

1. **[Anexo I do Contrato 01/2024](anexos/urae1-anexo-i-municipios-atendidos.pdf) (URAE-1 Sudeste)**: lista numerada dos 371 municípios atendidos. É a lista de quem pode ser cadastrado. [Fonte original](https://semil.sp.gov.br/desestatizacaosabesp/wp-content/uploads/sites/24/2024/05/Anexo-I.pdf).
2. **Anexo IV do Contrato, item 6.4** ([PDF oficial](https://urae1.sp.gov.br/wp-content/uploads/sites/26/2025/02/ANEXO-IV_Apostilado.pdf)) e **[Nota Técnica do 1º Reajuste da ARSESP](anexos/arsesp-nt-1-reajuste-urae1-2026.pdf)**: dizem quais unidades de negócio (OC, OL, OX, OR...) usam cada tabela e trazem os valores de 2026.
3. **[Relação de Municípios Operados pela Sabesp](anexos/sabesp-municipios-por-unidade.pdf)**: lista os municípios de cada unidade. Usa códigos antigos (M e R); o contrato usa os novos (O).
4. **Deliberação ARSESP nº 1.749/2025**: reajuste de 6,1106% desde 01/01/2026; trata Lins à parte (Tabela 10).
5. **API de municípios do IBGE** (estado 35): nome e código de todos os 371 municípios conferidos.

### Como os códigos antigos foram ligados aos novos

Nenhum documento traz a tabela de equivalência, mas o contrato confirma as ligações pelas **exceções que ele mesmo cita**:

- Tabela 4 (OR) exclui Apiaí, Barra do Chapéu, Itaóca, Itapirapuã Paulista e Ribeira. Esses 5 aparecem na unidade RR da Relação, então **OR = RR (Vale do Ribeira)**.
- Tabela 6 (OV) exclui Guararema e Santa Isabel, ambos na unidade RV, então **OV = RV (Vale do Paraíba)**.
- Tabela 5 (OT) exclui Lins, que está na unidade RT, então **OT = RT (Baixo Tietê)**.
- A Tabela 3 lista "Baixada Santista - RS" e "Litoral Norte - RN" entre os serviços das unidades OX e OI, então **OX e OI = RS e RN (litoral)**.
- A Diretoria Metropolitana (M, ML, MN, MO, MS) corresponde às unidades OC, OL, ON, OO e OS pelos nomes (Centro/Leste/Norte/Oeste/Sul). Os 33 municípios dão o mesmo resultado que o contrato descreve.
- O que sobra (RA, RB, RG, RJ, RM e RT) são as unidades de interior da Tabela 5.

## 7. Decisões sem fonte escrita e limites

- **Mauá, Santo André, Tapiratiba e Tejupá** estão no Anexo I, mas **não** constam da Relação de unidades, então nenhum documento diz qual tabela usam. Por decisão da equipe, Mauá e Santo André ficaram em `GRANDE_SP` e Tapiratiba e Tejupá em `INTERIOR`, por serem da região metropolitana e do interior. Confirmar com a ARSESP ou a Sabesp e corrigir `tb_municipality.region_id` se forem diferentes.
- **Fora da lista:** Igarapava, Miguelópolis, Nova Guataporanga e Quintana (não aderiram à URAE-1; a tarifa deles é da Deliberação ARSESP 1.514/2024, que não está no banco). Mogi das Cruzes e São Caetano do Sul (fornecimento por atacado, Tabela 9). Todas as cidades de outros operadores, como Campinas e Ribeirão Preto. Elas recebem o erro do item 2.
- **Grafia:** o nome segue o IBGE, que é o que a API de CEP devolve. Há diferenças em relação aos documentos: `Itaoca` (contrato: Itaóca), `Biritiba Mirim` (Relação: Biritiba-Mirim) e `São Luiz do Paraitinga` (Relação: São Luízs).
- A Relação de Municípios não tem data impressa. O Anexo I é o que decide quem entra; a Relação só liga o município à tabela.
- O Anexo IV de fevereiro de 2025 ainda não traz a Tabela de Lins. Ela vem do 1º Termo Aditivo, citado na Deliberação 1.749.
- Os valores de `tb_region_rate` seguem a simplificação já documentada no delta-business-rules: uma tarifa por categoria (faixa de 21 a 50 m³) e categorias "Especial" sem tabela própria usam o valor "Normal". O arquivo `tarifas-2026.json` e o `update_tariffs.py` de lá ainda listam só os 5 grupos antigos.

## 8. Como atualizar

1. Conferir nas fontes do item 6 se algum município entrou, saiu ou mudou de tabela.
2. Validar o nome e o código na [lista do IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios).
3. Alterar `tb_municipality` em `script-dataload.sql` (carga de teste) e aplicar o mesmo `INSERT` ou `UPDATE` nos ambientes em uso.
4. Grupo novo: acrescentar o nome ao `CHECK` de `tb_region` (`script-schema.sql` e `tables/tb_region.sql`), ao enum `RegionName` da API e inserir as 8 tarifas em `tb_region_rate`.
5. Atualizar este documento e a data de consulta do item 6.

Ambiente já em uso (que não recria o schema): troque o `CHECK` de `tb_region` pelos 9 nomes, crie `tb_municipality` com `tables/tb_municipality.sql`, carregue os municípios com o bloco do `script-dataload.sql` e insira as tarifas dos novos grupos.
