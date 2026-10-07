-- Consultas de referência do Genie space (Instructions -> SQL queries).
-- Cada bloco: a pergunta no comentário e o SQL que a responde.
-- Execute com o schema erp_farma.gold selecionado.

-- 1. Qual foi o faturamento por canal no último trimestre?
SELECT
  v.canal,
  SUM(v.faturamento) AS faturamento,
  COUNT(DISTINCT v.id_venda) AS quantidade_vendas
FROM fato_vendas AS v
WHERE v.data_venda >= date_trunc('QUARTER', add_months(current_date(), -3))
  AND v.data_venda < date_trunc('QUARTER', current_date())
GROUP BY v.canal
ORDER BY faturamento DESC;

-- 2. Quais são os 10 produtos mais vendidos em unidades neste ano?
SELECT
  p.nome_produto,
  p.laboratorio,
  p.categoria,
  SUM(v.quantidade) AS unidades,
  SUM(v.faturamento) AS faturamento
FROM fato_vendas AS v
JOIN dim_produto AS p ON p.id_produto = v.id_produto
WHERE year(v.data_venda) = year(current_date())
GROUP BY p.nome_produto, p.laboratorio, p.categoria
ORDER BY unidades DESC
LIMIT 10;

-- 3. Qual a participação dos genéricos no faturamento de medicamentos, mês a mês?
SELECT
  d.ano_mes,
  SUM(CASE WHEN p.eh_generico THEN v.faturamento ELSE 0 END) AS faturamento_genericos,
  SUM(v.faturamento) AS faturamento_medicamentos,
  ROUND(100 * SUM(CASE WHEN p.eh_generico THEN v.faturamento ELSE 0 END) / SUM(v.faturamento), 1) AS participacao_percentual
FROM fato_vendas AS v
JOIN dim_produto AS p ON p.id_produto = v.id_produto
JOIN dim_data AS d ON d.data = v.data_venda
WHERE p.eh_medicamento
GROUP BY d.ano_mes
ORDER BY d.ano_mes;

-- 4. Qual o ticket médio por filial no mês passado?
SELECT
  f.nome_filial,
  COUNT(DISTINCT v.id_venda) AS quantidade_vendas,
  SUM(v.faturamento) AS faturamento,
  ROUND(SUM(v.faturamento) / COUNT(DISTINCT v.id_venda), 2) AS ticket_medio
FROM fato_vendas AS v
JOIN dim_filial AS f ON f.id_filial = v.id_filial
WHERE v.data_venda >= date_trunc('MONTH', add_months(current_date(), -1))
  AND v.data_venda < date_trunc('MONTH', current_date())
GROUP BY f.nome_filial
ORDER BY ticket_medio DESC;

-- 5. Quais lotes vencem nos próximos 30 dias e quanto valem em estoque?
SELECT
  f.nome_filial,
  p.nome_produto,
  e.lote,
  e.data_validade,
  e.dias_para_vencer,
  e.quantidade_disponivel,
  e.valor_estoque
FROM fato_estoque AS e
JOIN dim_filial AS f ON f.id_filial = e.id_filial
JOIN dim_produto AS p ON p.id_produto = e.id_produto
WHERE e.posicao_atual
  AND e.dias_para_vencer BETWEEN 0 AND 30
  AND e.quantidade_disponivel > 0
ORDER BY e.dias_para_vencer, e.valor_estoque DESC;
