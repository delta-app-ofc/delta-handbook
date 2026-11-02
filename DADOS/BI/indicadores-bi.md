# Indicadores de Business Intelligence — Delta v3

Catálogo conceitual BI01–BI18. As consultas executáveis ficam em `delta-business-intelligence/v3/gold/CONSULTAS-DASHBOARD.sql`. A interpretação deve seguir o [processo de BI](processo-bi.md) e considerar os descartes e a cobertura do lote.

| ID | Indicador | Base e interpretação |
| --- | --- | --- |
| BI01 | Temperatura e sensação térmica | Observações climáticas horárias, resumidas por dia e cidade |
| BI02 | Clima × consumo | Imóvel/hora pareado ao clima; associação não comprova causalidade |
| BI03 | Consumo por imóvel no período | Volume por imóvel e coordenadas cadastrais |
| BI04 | Consumo médio por hora | Perfil horário; a consulta preservada usa hora UTC |
| BI05 | Alertas por tipo | Contagem dos alertas registrados |
| BI06 | Evolução dos alertas | Contagem diária por tipo |
| BI07 | Disponibilidade dos dispositivos | Evolução da disponibilidade observada |
| BI08 | Mediana de disponibilidade | Referência central da distribuição dos dispositivos |
| BI09 | Consumo por grupo tarifário | Volume observado por classificação; não normaliza automaticamente pelo porte |
| BI10 | Tarifas vigentes por região | Valores por classificação e vigência; não é a fatura calculada |
| BI11 | Consumo médio e meta diária | Médias dos dias elegíveis e metas atuais |
| BI12 | Cumprimento da meta diária | Dias dentro da meta / dias elegíveis |
| BI13 | Litros excedentes à meta | Soma de `max(consumo - meta, 0)` nos dias elegíveis |
| BI14 | Resultado das requisições de IA | Uma contagem por requisição e `outcome`, sem multiplicar pelos agentes |
| BI15 | Participações acima de cinco segundos | Participações com duração > 5.000 ms / participações medidas; fração convertida uma vez para percentual |
| BI16 | Tempo por agente participante | Distribuição de `agents_ms`, acumulada por agente/requisição |
| BI17 | Requisições com erro por agente participante | 100 × requisições com `outcome=error` / requisições em que o agente participou |
| BI18 | P90 diário do tempo por agente | Percentil 90 de `agents_ms` por dia local e agente, em segundos |



## Cuidados de leitura

- Os indicadores de IA usam período e dia local de São Paulo; não presumem vínculo com usuário, imóvel, cidade ou região.
- Ausência de registros é não apurado, não zero. A retenção da observabilidade limita a série histórica disponível.
- Os indicadores de consumo e metas representam a base elegível depois dos descartes auditados; conferir perdas antes de comparar períodos.
- Não misturar tempo total da requisição, tempo do agente e tempo das chamadas de modelo.
