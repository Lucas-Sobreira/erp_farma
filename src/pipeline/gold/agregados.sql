-- Gold: agregados que alimentam o dashboard "Análise Comercial". Mantêm as colunas
-- de filtro (data, filial, canal) para que os filtros do dashboard funcionem.

CREATE OR REFRESH MATERIALIZED VIEW agg_vendas_diarias (
  data_venda DATE COMMENT 'Dia da venda.',
  nome_filial STRING COMMENT 'Filial que realizou a venda.',
  canal STRING COMMENT 'Canal de venda: Loja Física, E-commerce, Delivery ou Convênio.',
  categoria STRING COMMENT 'Categoria comercial do produto.',
  tipo_produto STRING COMMENT 'Referência, Genérico, Similar ou Não medicamento.',
  quantidade_itens BIGINT COMMENT 'Total de unidades vendidas.',
  faturamento DECIMAL(18,2) COMMENT 'Faturamento líquido, em reais.',
  valor_desconto DECIMAL(18,2) COMMENT 'Descontos concedidos, em reais.',
  custo_total DECIMAL(18,2) COMMENT 'Custo das unidades vendidas, em reais.',
  margem_bruta DECIMAL(18,2) COMMENT 'Faturamento menos custo, em reais.'
)
COMMENT 'Vendas concluídas por dia, filial, canal, categoria e tipo de produto. Não use para contar vendas (cupons): uma venda pode ter itens em várias categorias.'
AS SELECT
  v.data_venda,
  f.nome_filial,
  v.canal,
  p.categoria,
  p.tipo_produto,
  CAST(sum(v.quantidade) AS BIGINT) AS quantidade_itens,
  CAST(sum(v.faturamento) AS DECIMAL(18,2)) AS faturamento,
  CAST(sum(v.valor_desconto) AS DECIMAL(18,2)) AS valor_desconto,
  CAST(sum(v.custo_total) AS DECIMAL(18,2)) AS custo_total,
  CAST(sum(v.margem_bruta) AS DECIMAL(18,2)) AS margem_bruta
FROM fato_vendas AS v
JOIN dim_filial AS f ON f.id_filial = v.id_filial
JOIN dim_produto AS p ON p.id_produto = v.id_produto
GROUP BY ALL;

CREATE OR REFRESH MATERIALIZED VIEW agg_pagamentos_diarios (
  data_venda DATE COMMENT 'Dia da venda.',
  nome_filial STRING COMMENT 'Filial que realizou a venda.',
  canal STRING COMMENT 'Canal de venda: Loja Física, E-commerce, Delivery ou Convênio.',
  forma_pagamento STRING COMMENT 'PIX, Cartão de Crédito, Cartão de Débito, Dinheiro ou Convênio.',
  quantidade_pagamentos BIGINT COMMENT 'Número de pagamentos recebidos.',
  valor_pago DECIMAL(18,2) COMMENT 'Valor recebido, em reais.'
)
COMMENT 'Pagamentos recebidos por dia, filial, canal e forma de pagamento.'
AS SELECT
  pg.data_venda,
  f.nome_filial,
  pg.canal,
  pg.forma_pagamento,
  count(*) AS quantidade_pagamentos,
  CAST(sum(pg.valor_pago) AS DECIMAL(18,2)) AS valor_pago
FROM fato_pagamentos AS pg
JOIN dim_filial AS f ON f.id_filial = pg.id_filial
GROUP BY ALL;

CREATE OR REFRESH MATERIALIZED VIEW agg_vendas_cupons_diarios (
  data_venda DATE COMMENT 'Dia da venda.',
  nome_filial STRING COMMENT 'Filial que realizou a venda.',
  canal STRING COMMENT 'Canal de venda: Loja Física, E-commerce, Delivery ou Convênio.',
  quantidade_vendas BIGINT COMMENT 'Número de vendas (cupons) concluídas.',
  quantidade_clientes_identificados BIGINT COMMENT 'Número de vendas com cliente identificado.',
  faturamento DECIMAL(18,2) COMMENT 'Faturamento líquido, em reais. Dividido por quantidade_vendas dá o ticket médio.'
)
COMMENT 'Número de vendas (cupons) e faturamento por dia, filial e canal. Use para ticket médio: SUM(faturamento) / SUM(quantidade_vendas).'
AS SELECT
  data_venda,
  nome_filial,
  canal,
  count(*) AS quantidade_vendas,
  count(id_cliente) AS quantidade_clientes_identificados,
  CAST(sum(faturamento) AS DECIMAL(18,2)) AS faturamento
FROM (
  SELECT v.id_venda, v.data_venda, f.nome_filial, v.canal, max(v.id_cliente) AS id_cliente, sum(v.faturamento) AS faturamento
  FROM fato_vendas AS v
  JOIN dim_filial AS f ON f.id_filial = v.id_filial
  GROUP BY ALL
)
GROUP BY ALL;
