-- Conferência pós-execução do farma_workflow. Rode no SQL Editor com o catálogo
-- `erp_farma` selecionado. Cada consulta diz, no comentário, o resultado esperado.

-- 1. Volume por camada. Esperado: bronze >= silver em todas as entidades
--    (a diferença são duplicatas e linhas reprovadas nas expectations).
SELECT 'vendas' AS entidade,
       (SELECT count(*) FROM bronze.vendas) AS bronze,
       (SELECT count(*) FROM silver.vendas) AS silver
UNION ALL
SELECT 'itens_venda', (SELECT count(*) FROM bronze.itens_venda), (SELECT count(*) FROM silver.itens_venda)
UNION ALL
SELECT 'pagamentos', (SELECT count(*) FROM bronze.pagamentos), (SELECT count(*) FROM silver.pagamentos)
UNION ALL
SELECT 'produtos', (SELECT count(*) FROM bronze.produtos), (SELECT count(*) FROM silver.produtos)
UNION ALL
SELECT 'clientes', (SELECT count(*) FROM bronze.clientes), (SELECT count(*) FROM silver.clientes);

-- 2. Chaves únicas na Silver. Esperado: zero linhas.
SELECT 'vendas' AS tabela, id_venda AS chave, count(*) AS repeticoes
FROM silver.vendas GROUP BY id_venda HAVING count(*) > 1
UNION ALL
SELECT 'itens_venda', id_venda * 100 + numero_item, count(*)
FROM silver.itens_venda GROUP BY id_venda, numero_item HAVING count(*) > 1;

-- 3. Faturamento da Gold x Silver. Esperado: diferenca = 0.
SELECT
  (SELECT sum(faturamento) FROM gold.fato_vendas) AS total_gold,
  (SELECT sum(i.valor_total_item)
   FROM silver.itens_venda AS i
   JOIN silver.vendas AS v ON v.id_venda = i.id_venda AND v.status = 'CONCLUIDA'
   JOIN silver.produtos AS p ON p.id_produto = i.id_produto) AS total_silver,
  total_gold - total_silver AS diferenca;

-- 4. Itens x cabeçalho x pagamentos na Gold. Esperado: as três somas próximas;
--    itens e cabecalho só divergem pelos itens descartados na Silver.
SELECT
  (SELECT sum(faturamento) FROM gold.fato_vendas) AS itens,
  (SELECT sum(valor_total) FROM silver.vendas WHERE status = 'CONCLUIDA') AS cabecalho,
  (SELECT sum(valor_pago) FROM gold.fato_pagamentos) AS pagamentos;

-- 5. Chaves órfãs nos fatos. Esperado: zero em todas as colunas.
SELECT
  count_if(p.id_produto IS NULL) AS sem_produto,
  count_if(f.id_filial IS NULL) AS sem_filial,
  count_if(d.data IS NULL) AS sem_data,
  count_if(v.id_cliente IS NOT NULL AND c.id_cliente IS NULL) AS sem_cliente
FROM gold.fato_vendas AS v
LEFT JOIN gold.dim_produto AS p ON p.id_produto = v.id_produto
LEFT JOIN gold.dim_filial AS f ON f.id_filial = v.id_filial
LEFT JOIN gold.dim_data AS d ON d.data = v.data_venda
LEFT JOIN gold.dim_cliente AS c ON c.id_cliente = v.id_cliente;

-- 6. Idempotência da carga diária. Rode antes e depois de repetir o modo
--    `diario` para a mesma data. Esperado: os mesmos números.
SELECT count(*) AS itens, count(DISTINCT id_venda) AS vendas, sum(faturamento) AS faturamento, max(data_venda) AS ultima_data
FROM gold.fato_vendas;
