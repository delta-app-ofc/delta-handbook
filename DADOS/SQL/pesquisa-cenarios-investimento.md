# 💰 Pesquisa de mercado - Cenários de investimento (CAPEX)

Este documento explica de onde vêm os valores de `tb_investment_scenario` (3 cenários: aeradores/registros
economizadores, reuso de água cinza, captação de água de chuva), usados pela view `dw.vw_ft_capex_comparison`
(camada de BI, `camada-bi.md`). Escrito porque esses números podem ser reutilizados pelo protótipo web e,
no futuro, por um agente de IA (RAG) — por isso a fonte de cada número precisa estar clara, e não só o
resultado final.

⚠️ **Leia isto antes de usar os valores em qualquer lugar novo**: os três cenários são **referências
ilustrativas de mercado brasileiro**, não cotações auditadas de um fornecedor específico nem de uma
instalação real do Projeto Delta. Os percentuais de redução foram escolhidos dentro do intervalo real
encontrado nas fontes abaixo (sempre no lado conservador do que os fornecedores anunciam, nunca no teto da
propaganda). Os valores monetários (investimento, economia anual) são estimativas de ordem de grandeza
compatíveis com o que foi encontrado, escaladas para porte comercial/industrial - não é o mesmo que uma
cotação real de obra. Se este conteúdo for usado no app ou num RAG, ele deve ser apresentado como
"estimativa de referência", nunca como "valor garantido".

---

## 1. Aeradores e registros economizadores

**Cenário no banco**: investimento R$ 15.000,00, redução de 12%, economia anual R$ 22.500,00, payback 8
meses.

**O que a pesquisa encontrou**:
- Torneiras/registros com fechamento automático (temporizado) anunciam economia de até 70% no ponto de uso,
  chegando a 85% quando combinados com outros mecanismos.
- Preço de mercado por unidade (varejo online, sem instalação): entre R$ 94,91 e R$ 437,25.

**Como isso virou o número do cenário**: 12% de redução no **consumo total** de uma unidade comercial
inteira é bem mais conservador que os "até 70%" anunciados por fornecedor, porque aquele percentual é
medido no ponto de uso (só na torneira), não no consumo total do prédio (que inclui vazamentos, processos,
limpeza etc. que a troca de torneira não afeta). O investimento (R$ 15.000,00) é compatível com trocar
dezenas de pontos de água numa rede de lojas de porte médio, ao preço unitário encontrado nas fontes.

**Fontes**:
- [Reino das Torneiras - Torneira Automática Temporizada](https://www.reinodastorneiras.com.br/torneira-automatica-c-mecanismo-temporizador-p-lavatorio)
- [Certiva - Torneiras de Pressionamento Automáticas](https://www.certiva.com.br/torneiras-de-pressionamento)
- [Ecosoli - Torneiras Econômicas com Temporizador](https://www.ecosoli.com.br/economia-agua/torneiras-e-duchas-economicas)

---

## 2. Reuso de água cinza

**Cenário no banco**: investimento R$ 90.000,00, redução de 22%, economia anual R$ 11.250,00, payback 96
meses.

**O que a pesquisa encontrou**:
- Payback de 8 a 12 meses é possível pra indústrias de grande porte (contando manutenção e energia).
- Pra negócio de porte médio: investimento de ~R$ 35.000,00, economia de ~R$ 972,00/mês, payback de ~36
  meses.
- Reuso pode reduzir consumo de água potável entre 30% e 50%, dependendo do perfil de uso.
- Indústria grande (1.500-2.000 funcionários) pode economizar ~R$ 40.000,00/mês.

**Leitura honesta**: o payback de 96 meses do cenário atual está no extremo pessimista do que a pesquisa
encontrou (o benchmark real de porte médio mostra ~36 meses para um investimento bem menor). Isso não
significa que o número esteja errado - o intervalo real de mercado é muito largo (8 a 96+ meses,
dependendo de escala, se conta energia/manutenção, e do perfil de consumo do imóvel) - mas significa que
**este cenário específico representa o lado mais conservador/pessimista da faixa real**, não a média. Se o
objetivo for mostrar um cenário "típico" em vez de "conservador", o valor correto a usar seria mais perto
de 36-60 meses de payback, não 96 - fica registrado aqui como recomendação, sem eu decidir sozinho por já
ser uma entrega anterior.

**Fontes**:
- [ROI de um projeto de reúso para a indústria - Opersan](https://info.opersan.com.br/roi-de-um-projeto-de-re%C3%BAso-para-a-ind%C3%BAstria-por-que-o-retorno-vai-muito-al%C3%A9m-da-economia-na-conta-de-%C3%A1gua)
- [Reúso de águas cinzas na indústria brasileira - Climate Tracker LatAm](https://climatetrackerlatam.org/historias/reuso-de-aguas-cinzas-pode-evitar-que-recursos-financeiros-e-ambientais-descam-pelo-ralo-na-industria-brasileira/)
- [Reuso de água pode levar a economia de até 40% - Neowater](https://www.neowater.com.br/post/reuso-agua-economia)
- [Tratamento e reuso da água: um investimento recompensador - Consumidor Moderno](https://consumidormoderno.com.br/tratamento-e-reuso-da-agua-um-investimento-recompensador/)

---

## 3. Captação de água de chuva

**Cenário no banco**: investimento R$ 70.000,00, redução de 18%, economia anual R$ 14.000,00, payback 60
meses.

**O que a pesquisa encontrou**:
- Sistemas residenciais/pequenos: de R$ 4.000,00 (compacto, jardim/lavagem externa) a mais de R$ 20.000,00
  (cisterna maior, bomba, filtros, rede de distribuição própria).
- Economia financeira "bem utilizado" chega a até 50%.
- Lei federal nº 14.546 (2026) já obriga a União a estimular reúso/captação de chuva em construções novas
  e atividades industriais - contexto regulatório real, não só tendência de mercado.
- **Não encontrei** fonte específica pra sistema de captação em escala industrial/comercial grande (só
  residencial e pequeno comercial) - o valor de R$ 70.000,00 é uma extrapolação de escala a partir dos
  valores residenciais/pequenos encontrados, não um benchmark direto de mercado pra esse porte.

**Como isso virou o número do cenário**: 18% de redução está bem abaixo do teto de 50% relatado - lado
conservador, coerente com o critério usado nos outros dois cenários. O investimento (R$ 70.000,00) é uma
estimativa de escala industrial, sem citação direta - **este é o ponto mais fraco dos três cenários em
termos de evidência real**, registrado aqui com honestidade em vez de esconder.

**Fontes**:
- [Quanto custa instalar sistema de captação de água da chuva - Monitor do Mercado](https://monitordomercado.com.br/economia-2/420944-quanto-custa-instalar-um-sistema-de-captacao-de-agua-da-chuva-em-casa/)
- [Retorno de Investimento em captação de água de chuva - RW Engenharia](https://rwengenharia.eng.br/retorno-de-investimento-em-captacao-de-agua-de-chuva/)
- [Coletar água de chuva - Custos e Benefícios - Ecocasa](https://www.ecocasa.com.br/coletar-agua-de-chuva-custos-e-beneficios/)

---

## 4. Metodologia geral e limitações

- Pesquisa feita via busca web em 2026-09-27, focada em fontes brasileiras (fornecedores, engenharia,
  imprensa especializada) - não é uma consultoria de engenharia nem um estudo de viabilidade formal.
- Critério usado nos três cenários: pegar o percentual de redução relatado pelas fontes e escolher um valor
  **conservador** dentro desse intervalo (nunca o teto da propaganda de fornecedor), depois estimar o
  investimento/economia em R$ compatível com porte comercial/industrial (não residencial).
- Isso é diferente do que já existe para `tb_region_rate` (tarifa de água): aquela tabela é atualizada por
  script (`update_tariffs.py`, no `delta-business-rules`) com fonte oficial ARSESP/Sabesp citada e
  processo de atualização anual definido. Os cenários de investimento **não têm** esse processo - são uma
  carga única, de referência, sem atualização automática nem fonte oficial única.
- Antes de usar estes valores num RAG ou em qualquer lugar do app onde o usuário final vai ver o número
  como se fosse uma cotação real, isso precisa ficar explícito: são estimativas de mercado, não uma
  proposta comercial.
