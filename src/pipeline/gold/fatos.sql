-- Gold: fatos do modelo estrela.
--
-- A integridade referencial é validada aqui: os LEFT JOINs trazem as chaves do
-- lado do cadastro, de modo que um item sem venda ou sem produto fica com a chave
-- nula, viola a expectation e é descartado (aparecendo nas métricas do pipeline).

CREATE OR REFRESH MATERIALIZED VIEW fato_vendas (
  id_venda BIGINT COMMENT 'Identificador da venda (cupom). Uma venda tem um ou mais itens.',
  numero_item INT COMMENT 'Sequência do item dentro da venda.',
  data_venda DATE COMMENT 'Dia da venda. Liga com dim_data.data.',
  data_hora_venda TIMESTAMP COMMENT 'Data e hora da venda.',
  id_filial BIGINT COMMENT 'Filial que realizou a venda. Liga com dim_filial.',
  id_cliente BIGINT COMMENT 'Cliente identificado na venda. Nulo em vendas de balcão sem identificação. Liga com dim_cliente.',
  id_vendedor BIGINT COMMENT 'Vendedor que atendeu. Nulo no e-commerce. Liga com dim_vendedor.',
  id_produto BIGINT COMMENT 'Produto vendido. Liga com dim_produto.',
  canal STRING COMMENT 'Canal de venda: Loja Física, E-commerce, Delivery ou Convênio.',
  quantidade INT COMMENT 'Unidades vendidas do produto neste item.',
  preco_unitario DECIMAL(12,2) COMMENT 'Preço de tabela por unidade no momento da venda, em reais.',
  valor_bruto DECIMAL(14,2) COMMENT 'Quantidade vezes preço unitário, antes do desconto, em reais.',
  valor_desconto DECIMAL(14,2) COMMENT 'Desconto concedido no item, em reais.',
  faturamento DECIMAL(14,2) COMMENT 'Valor líquido do item (bruto menos desconto), em reais. É a medida de faturamento/receita.',
  custo_total DECIMAL(14,2) COMMENT 'Custo de aquisição das unidades vendidas, em reais.',
  margem_bruta DECIMAL(14,2) COMMENT 'Faturamento menos custo total, em reais.',
  CONSTRAINT venda_existente EXPECT (id_filial IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT produto_cadastrado EXPECT (id_produto IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Fato de vendas no grão de item de venda. Contém apenas vendas concluídas (canceladas ficam de fora). Para contar vendas use COUNT(DISTINCT id_venda); para faturamento use SUM(faturamento).'
AS SELECT
  i.id_venda,
  i.numero_item,
  v.data_venda,
  v.data_hora_venda,
  v.id_filial,
  v.id_cliente,
  v.id_vendedor,
  p.id_produto,
  v.canal,
  i.quantidade,
  i.preco_unitario,
  CAST(i.quantidade * i.preco_unitario AS DECIMAL(14,2)) AS valor_bruto,
  CAST(i.valor_desconto AS DECIMAL(14,2)) AS valor_desconto,
  CAST(i.valor_total_item AS DECIMAL(14,2)) AS faturamento,
  CAST(i.quantidade * i.custo_unitario AS DECIMAL(14,2)) AS custo_total,
  CAST(i.valor_total_item - i.quantidade * i.custo_unitario AS DECIMAL(14,2)) AS margem_bruta
FROM ${farma.schema_silver}.itens_venda AS i
LEFT JOIN ${farma.schema_silver}.vendas AS v ON v.id_venda = i.id_venda
LEFT JOIN ${farma.schema_silver}.produtos AS p ON p.id_produto = i.id_produto
WHERE v.id_venda IS NULL OR v.status = 'CONCLUIDA';

CREATE OR REFRESH MATERIALIZED VIEW fato_pagamentos (
  id_pagamento BIGINT COMMENT 'Identificador do pagamento.',
  id_venda BIGINT COMMENT 'Venda a que o pagamento se refere. Uma venda pode ter mais de um pagamento.',
  data_venda DATE COMMENT 'Dia da venda. Liga com dim_data.data.',
  id_filial BIGINT COMMENT 'Filial que realizou a venda. Liga com dim_filial.',
  canal STRING COMMENT 'Canal de venda: Loja Física, E-commerce, Delivery ou Convênio.',
  forma_pagamento STRING COMMENT 'PIX, Cartão de Crédito, Cartão de Débito, Dinheiro ou Convênio.',
  bandeira STRING COMMENT 'Bandeira do cartão. Nulo quando o pagamento não é em cartão.',
  parcelas INT COMMENT 'Número de parcelas. Só é maior que 1 no cartão de crédito.',
  valor_pago DECIMAL(14,2) COMMENT 'Valor recebido neste pagamento, em reais.',
  CONSTRAINT venda_existente EXPECT (id_filial IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Fato de pagamentos recebidos das vendas concluídas. Use para analisar formas de pagamento.'
AS SELECT
  pg.id_pagamento,
  pg.id_venda,
  v.data_venda,
  v.id_filial,
  v.canal,
  pg.forma_pagamento,
  pg.bandeira,
  pg.parcelas,
  CAST(pg.valor_pago AS DECIMAL(14,2)) AS valor_pago
FROM ${farma.schema_silver}.pagamentos AS pg
LEFT JOIN ${farma.schema_silver}.vendas AS v ON v.id_venda = pg.id_venda
WHERE v.id_venda IS NULL OR v.status = 'CONCLUIDA';

CREATE OR REFRESH MATERIALIZED VIEW fato_estoque (
  data_posicao DATE COMMENT 'Dia a que a posição de estoque se refere.',
  posicao_atual BOOLEAN COMMENT 'Verdadeiro para a posição mais recente. Filtre por este campo para ver o estoque de hoje.',
  id_filial BIGINT COMMENT 'Filial onde o estoque está. Liga com dim_filial.',
  id_produto BIGINT COMMENT 'Produto em estoque. Liga com dim_produto.',
  lote STRING COMMENT 'Código do lote do fabricante.',
  data_validade DATE COMMENT 'Data de validade do lote.',
  dias_para_vencer INT COMMENT 'Dias entre a data da posição e a validade. Negativo significa lote vencido.',
  situacao_validade STRING COMMENT 'Vencido, Vence em até 60 dias, Vence em 61 a 180 dias ou Acima de 180 dias.',
  quantidade_disponivel INT COMMENT 'Unidades disponíveis do lote na filial.',
  valor_estoque DECIMAL(14,2) COMMENT 'Quantidade disponível vezes o custo unitário, em reais.',
  CONSTRAINT filial_cadastrada EXPECT (id_filial IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT produto_cadastrado EXPECT (id_produto IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Fato de posição diária de estoque por filial, produto e lote, com situação de validade. Não some quantidades de dias diferentes: filtre uma data ou posicao_atual.'
AS SELECT
  e.data_posicao,
  e.data_posicao = max(e.data_posicao) OVER () AS posicao_atual,
  f.id_filial,
  p.id_produto,
  e.lote,
  e.data_validade,
  datediff(e.data_validade, e.data_posicao) AS dias_para_vencer,
  CASE
    WHEN e.data_validade < e.data_posicao THEN 'Vencido'
    WHEN datediff(e.data_validade, e.data_posicao) <= 60 THEN 'Vence em até 60 dias'
    WHEN datediff(e.data_validade, e.data_posicao) <= 180 THEN 'Vence em 61 a 180 dias'
    ELSE 'Acima de 180 dias'
  END AS situacao_validade,
  e.quantidade_disponivel,
  CAST(e.quantidade_disponivel * e.custo_unitario AS DECIMAL(14,2)) AS valor_estoque
FROM ${farma.schema_silver}.estoque_lotes AS e
LEFT JOIN ${farma.schema_silver}.filiais AS f ON f.id_filial = e.id_filial
LEFT JOIN ${farma.schema_silver}.produtos AS p ON p.id_produto = e.id_produto;
