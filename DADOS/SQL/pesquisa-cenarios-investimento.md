# Pesquisa e cálculo dos cenários de investimento

Este documento registra a pesquisa pública usada para interpretar os cenários de `tb_investment_scenario`, as fórmulas mostradas no BI e o que os valores cadastrados podem (e não podem) afirmar. Os cenários são referências demonstrativas para o simulador, não orçamento, cotação de fornecedor ou recomendação de engenharia para uma instalação específica.

Implementação relacionada: `tb_investment_scenario`, `gold.ft_investment_scenario`, `dw.vw_ft_capex_comparison`, `dw.vw_ft_investment_impact` e `dw.vw_ft_organization_esg` no [repositório SQL](https://github.com/delta-app-ofc/delta-sql-database). A definição BI completa está em [camada-bi.md](camada-bi.md).

## O que os campos financeiros significam

| Campo | Significado no simulador |
|---|---|
| `investment_value` | CAPEX de referência cadastrado no cenário. Não vem de cotação vinculada à organização. |
| `reduction_pct` | Percentual estimado de redução cadastrado no cenário. O efeito real depende da medida, perfil da instalação, clima, uso, manutenção e base de consumo. |
| `annual_savings_value` | Economia financeira anual informada no cadastro. A view `vw_ft_capex_comparison` apenas a lê; não é calculada a partir da tarifa nem do consumo atual. |
| `payback_months` | Prazo simples de retorno informado no cadastro. A view o utiliza para ordenar cenários, não para calcular fluxo de caixa descontado. |

O payback simples consistente com os dois valores financeiros é:

```text
payback (meses) = investimento (R$) ÷ (economia anual (R$/ano) ÷ 12)
```

O indicador ignora manutenção, energia, financiamento, inflação, reajustes tarifários, vida útil, custo de capital, impostos e variação do volume economizado. É apenas divisão simples dos valores de referência.

Em contraste, `dw.vw_ft_investment_impact` deriva a **economia de água** do consumo observado:

```text
base anual (L) = média do total mensal dos meses marcados completos × 12
economia anual projetada (L) = base anual × redução_pct ÷ 100
caminhões equivalentes = litros poupados ÷ 10.000 L
meses familiares equivalentes = litros poupados ÷ 18.000 L
```

A view exige pelo menos uma linha de mês completo por organização para produzir base. A família de referência usa `4 pessoas × 150 L por pessoa/dia × 30 dias = 18.000 L/mês`. A [Embasa](https://www.ba.gov.br/comunicacao/2022/01/noticias/embasa-orienta-sobre-instalacao-de-reservatorio-para-prevenir-desabastecimento-em-imoveis) cita 150 L por morador/dia como estimativa para o Brasil e ressalta que o consumo varia conforme hábitos e condições econômicas. O divisor é, portanto, uma referência de equivalência, não uma média universal de todas as famílias.

Para caminhões, o modelo adota 10.000 L por veículo. Essa capacidade aparece como especificação em [contratação pública municipal de caminhão-pipa](https://ribasdoriopardo.ms.gov.br/wp-content/uploads/2024/08/FLS.-213-a-214-RESOLUCAO-N2-65-SEINFRA-2024.pdf), mas veículos podem ter tanques maiores ou menores; a equivalência não representa viagens ou água efetivamente entregue.

## Valores que estão cadastrados

Os scripts do banco contêm dois conjuntos: cenários genéricos da carga principal e alternativas específicas da demonstração Swift. Valores financeiros em reais permanecem nominais e sem data-base de orçamento no schema.

| Conjunto | Cenário | Investimento | Redução cadastrada | Economia anual cadastrada | Payback cadastrado | Payback recalculado |
|---|---|---:|---:|---:|---:|---:|
| Genérico | Aeradores e registros economizadores | R$ 15.000,00 | 12% | R$ 22.500,00/ano | 8,0 meses | 8,0 meses |
| Genérico | Reúso de água cinza | R$ 90.000,00 | 22% | R$ 11.250,00/ano | 96,0 meses | 96,0 meses |
| Genérico | Captação de água de chuva | R$ 70.000,00 | 18% | R$ 14.000,00/ano | 60,0 meses | 60,0 meses |
| Swift (demonstração) | Torneiras econômicas | R$ 18.000,00 | 12% | R$ 22.200,00/ano | 9,7 meses | 9,7 meses |
| Swift (demonstração) | Reúso de água | R$ 75.000,00 | 28% | R$ 51.800,00/ano | **17,4 meses** | **17,4 meses** |
| Swift (demonstração) | Captação de chuva | R$ 42.000,00 | 19% | R$ 35.400,00/ano | 14,2 meses | 14,2 meses |

O cenário Swift de reúso estava gravado como 17,3 meses. A conta `75.000 ÷ 51.800 × 12 = 17,3745...` arredonda para 17,4 meses; o valor foi corrigido no dataload. Isso corrige a consistência aritmética, mas não valida os valores originais de investimento ou economia.

## O que a pesquisa sustenta

### Aeradores e dispositivos economizadores

Um estudo brasileiro em prédio universitário mediu redução de 12,34% no consumo total após substituição de torneiras, e 20,43% no consumo específico das torneiras. Os resultados variam por ponto de uso e contexto; por isso, o dado de 20,43% não deve ser aplicado ao consumo total de uma unidade comercial. O estudo também registra fatores como quantidade de usuários e temperatura ([artigo na SciELO](https://www.scielo.br/j/esa/a/MQcDrVmPKgy33nQ4L7BMCJN/?lang=pt)). A pesquisa piloto da [Adasa/Programa Poupa DF](https://www.adasa.df.gov.br/images/storage/nota_tecnica/GUIA%20POUPA%20DF.pdf) documentou troca de torneiras, arejadores e outras intervenções em prédios públicos, com queda de consumo após o conjunto de ações; como houve várias intervenções em conjunto, isso não isola a economia atribuível só a arejadores.

Na consulta de 3 nov. 2026, uma loja brasileira listava torneiras automáticas para lavatório aproximadamente entre R$ 63,95 e R$ 79,95 por peça, sem que esse preço implique instalação, frete ou adequação da rede ([Reino das Torneiras](https://www.reinodastorneiras.com.br/torneira-automatica-c-mecanismo-temporizador-p-lavatorio)). O investimento genérico de R$ 15.000,00 não pode ser confirmado sem número de pontos, especificação, mão de obra e data de orçamento; ao preço consultado, representaria aproximadamente 187–234 peças antes dos custos de instalação. O percentual de 12% é compatível com o resultado de um estudo específico, mas não garante o resultado em outra edificação.

### Reúso de água cinza

Um estudo técnico apresentado em congresso da ABES estimou R$ 143.449,14 para uma solução de reúso em condomínio, com estação de tratamento, instalação, reservatórios, bombas e encanamentos; o próprio estudo ressalta dependência de demanda e área disponível. Seu payback calculado foi de oito anos para aquele projeto ([anais ABES, estudo de caso](https://abes-dn.org.br/anaiseletronicos/32cbesa/370_tema_ii.pdf)). É uma referência de escopo e ordem de grandeza, não preço atual nem diretamente comparável a uma loja ou indústria. O investimento genérico de R$ 90.000 e o Swift de R$ 75.000 não têm projeto/dimensionamento ou cotação associada no banco; não é possível dizer que são preços de mercado validados.

O [mapeamento empresarial do CEBDS, publicado em 2024](https://cebds.org/publicacoes/mapeamento-de-reuso-de-aguas-cinzas-e-aproveitamento-de-agua-de-chuva-no-setor-empresarial/) contextualiza barreiras e práticas de reúso no setor empresarial. O material reforça que a solução exige avaliação de cada caso; não transforma os valores deste seed em tabela de preços.

### Captação de água de chuva

A cartilha do [Senado Federal sobre edifícios públicos sustentáveis](https://www.senado.gov.br/senado/Programas/senadoverde/siges/Cartilha-edificios_publicos_sustentaveis_Visualizar.pdf) apresenta um exemplo de sistema com custo estimado de R$ 24.000, volume captável de 776 m³/ano e tarifa de referência de R$ 12,71/m³, resultando em payback simples aproximado de 29,2 meses. É um exemplo publicado com premissas e preços históricos, não um orçamento atual.

O [ProjetEEE, do Ministério de Minas e Energia](https://projeteee.mme.gov.br/equipamento/sistema-de-aproveitamento-de-aguas-pluviais/) descreve usos, componentes, dimensionamento de reservatório e análise econômica. O resultado depende de área de captação, chuva local, demanda não potável, armazenamento, tratamento e instalação. Não foi localizada nesta revisão uma cotação pública atual com escopo equivalente para justificar os R$ 70.000 (genérico) ou R$ 42.000 (Swift); esses números continuam estimativas didáticas, não valores pesquisados/confirmados de um sistema comercial específico.

## Conclusão de confiabilidade

- **Redução percentual de equipamentos economizadores:** existe evidência empírica brasileira para uma ordem de grandeza próxima a 12% no consumo total em um prédio estudado; transferir esse percentual para toda organização é hipótese de cenário.
- **Custos de investimento dos três cenários:** não há quantitativo de equipamentos, memorial de dimensionamento, cotações atuais ou composição de custos associada a esses registros. A pesquisa encontrou exemplos públicos, mas não equivalentes o bastante para validar os seis valores monetários cadastrados. Eles devem aparecer como **estimativas ilustrativas**, não orçamento.
- **Economia anual e payback estáticos:** a aritmética dos seis pares investimento/economia anual agora confere após arredondar a uma casa decimal. Isso só garante consistência matemática entre campos, não que a economia anual aconteça na prática.
- **Impacto hídrico personalizado:** litros poupados são calculados na view com base na média dos meses completos e na redução percentual cadastrada. Sua confiabilidade ainda depende da cobertura das leituras e da adequação do percentual ao caso real.
- **Equivalências:** caminhão de 10.000 L e família de 18.000 L/mês são denominadores de comunicação explicitados e referenciados, não alegações de padrão obrigatório.

Para transformar esses cenários em recomendação financeira, a organização precisa fornecer auditoria de consumo e contas, escopo técnico, número/área das unidades, projeto de engenharia e propostas comerciais datadas; a economia deve usar a tarifa aplicável e incluir O&M e custos de capital. A pesquisa não alterou os preços de CAPEX cadastrados.

## Referências e data da consulta

Fontes e páginas verificadas em **3 de novembro de 2026**. Preços varejistas e exemplos de obras são sensíveis a data, região, escala e especificação; confirme as páginas e obtenha orçamento antes de reutilizá-los como valores atuais.
