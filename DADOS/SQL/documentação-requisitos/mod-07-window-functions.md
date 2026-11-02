### MOD-07 — Usar Window Functions para cálculos analíticos, por exemplo Running Total ou Ranking, nas views de BI

**Evidência direta:**

- [Views analíticas do schema `dw`](https://github.com/delta-app-ofc/delta-sql-database/tree/main/datamart/dw/views)
- [View com Running Total e média móvel](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_consumption_daily.sql)
- [View com rankings e distribuição](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_property_ranking.sql)
- [View com comparação mês a mês (`LAG`)](https://github.com/delta-app-ofc/delta-sql-database/blob/main/datamart/dw/views/vw_ft_monthly_variation.sql)
- [Documentação da camada de BI, seção 5](https://github.com/delta-app-ofc/delta-handbook/blob/main/DADOS/SQL/camada-bi.md)

**Localização e como comprovar:**

As window functions calculam, sobre as tabelas fato do schema `gold`, indicadores que dependem da posição de cada linha no conjunto, sem perder o detalhe de cada registro.

| Tipo | Função e cláusula | View | Resultado |
|---|---|---|---|
| Running Total | `SUM() OVER (PARTITION BY property_id ORDER BY full_date ROWS UNBOUNDED PRECEDING)` | `vw_ft_consumption_daily` | Consumo acumulado por propriedade ao longo do tempo |
| Média móvel | `AVG() OVER (... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` | `vw_ft_consumption_daily` | Média dos últimos 7 dias, que suaviza a variação diária |
| Ranking | `RANK()` e `DENSE_RANK()` | `vw_ft_property_ranking`, `vw_ft_capex_comparison`, `vw_ft_residential_efficiency_ranking` | Eficiência (L/m²), custo, payback e consumo residencial por mês (`PARTITION BY`) |
| Distribuição | `NTILE(4)`, `NTILE(5)` e `PERCENT_RANK()` | `vw_ft_property_ranking`, `vw_ft_consumption_distribution` | Quartil, quintil e posição relativa entre 0 e 1 |
| Período anterior | `LAG()` | `vw_ft_monthly_variation` | Variação percentual em relação ao mês anterior |

#### Como comprovar

1. Abrir `vw_ft_consumption_daily.sql` e localizar `SUM() OVER` e `AVG() OVER`.
2. Abrir `vw_ft_property_ranking.sql` e localizar `RANK()`, `DENSE_RANK()`, `NTILE()` e `PERCENT_RANK()`.
3. Abrir `vw_ft_monthly_variation.sql` e localizar `LAG()`.
4. Com o Data Mart carregado, executar `SELECT * FROM dw.vw_ft_consumption_daily ORDER BY property_id, full_date;` e conferir que a coluna acumulada cresce a cada dia dentro de cada propriedade.

As views são testadas com a telemetria real do MongoDB (gerada pelo `delta-hardware-data-simulator`), com os dados cadastrais do dataload e com os cenários de investimento pesquisados.
