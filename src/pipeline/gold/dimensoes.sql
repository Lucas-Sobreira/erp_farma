-- Gold: dimensões do modelo estrela. Os comentários de tabela e coluna são o
-- vocabulário que o Genie e o dashboard usam; mantenha-os em linguagem de negócio.

CREATE OR REFRESH MATERIALIZED VIEW dim_produto (
  id_produto BIGINT COMMENT 'Identificador do produto no ERP. Chave da dimensão.',
  ean STRING COMMENT 'Código de barras (EAN-13) do produto.',
  nome_produto STRING COMMENT 'Nome comercial completo, com dosagem e apresentação.',
  principio_ativo STRING COMMENT 'Princípio ativo do medicamento. Nulo para não medicamentos.',
  laboratorio STRING COMMENT 'Laboratório ou marca fabricante.',
  categoria STRING COMMENT 'Categoria comercial, ex.: Analgésicos e Antitérmicos, Dermocosméticos, Higiene Pessoal.',
  tipo_produto STRING COMMENT 'Referência, Genérico, Similar ou Não medicamento.',
  eh_medicamento BOOLEAN COMMENT 'Verdadeiro para medicamentos (Referência, Genérico ou Similar).',
  eh_generico BOOLEAN COMMENT 'Verdadeiro quando o produto é um medicamento genérico.',
  tarja STRING COMMENT 'Tarja do medicamento: Sem tarja, Vermelha, Preta ou Não se aplica.',
  controlado BOOLEAN COMMENT 'Verdadeiro quando a venda exige retenção de receita (antibióticos e psicotrópicos).',
  exige_receita BOOLEAN COMMENT 'Verdadeiro quando o medicamento só pode ser vendido com prescrição.',
  fornecedor STRING COMMENT 'Razão social do fornecedor que abastece o produto.',
  tipo_fornecedor STRING COMMENT 'Laboratório, Indústria de Consumo ou Distribuidora.',
  preco_venda_atual DECIMAL(12,2) COMMENT 'Preço de venda vigente no cadastro, em reais. Para o preço praticado em cada venda use fato_vendas.preco_unitario.',
  preco_custo_atual DECIMAL(12,2) COMMENT 'Custo de aquisição vigente no cadastro, em reais.',
  data_cadastro DATE COMMENT 'Data em que o produto entrou no cadastro.'
)
COMMENT 'Dimensão de produtos da farmácia: medicamentos e não medicamentos, com categoria, laboratório e regras de receita.'
AS SELECT
  p.id_produto,
  p.ean,
  p.nome_produto,
  p.principio_ativo,
  p.laboratorio,
  p.categoria,
  p.tipo_produto,
  p.tipo_produto <> 'Não medicamento' AS eh_medicamento,
  p.tipo_produto = 'Genérico' AS eh_generico,
  p.tarja,
  p.controlado,
  p.exige_receita,
  f.razao_social AS fornecedor,
  f.tipo_fornecedor,
  p.preco_venda AS preco_venda_atual,
  p.preco_custo AS preco_custo_atual,
  p.data_cadastro
FROM ${farma.schema_silver}.produtos AS p
LEFT JOIN ${farma.schema_silver}.fornecedores AS f ON f.id_fornecedor = p.id_fornecedor;

CREATE OR REFRESH MATERIALIZED VIEW dim_filial (
  id_filial BIGINT COMMENT 'Identificador da filial no ERP. Chave da dimensão.',
  nome_filial STRING COMMENT 'Nome da loja. A filial Matriz Centro também fatura os pedidos do e-commerce.',
  cidade STRING COMMENT 'Cidade da filial.',
  uf STRING COMMENT 'Sigla do estado da filial.',
  bairro STRING COMMENT 'Bairro da filial.',
  tipo_loja STRING COMMENT 'Rua, Shopping ou Hospitalar.',
  data_abertura DATE COMMENT 'Data de inauguração da filial.'
)
COMMENT 'Dimensão de filiais (lojas) da rede de farmácias.'
AS SELECT id_filial, nome_filial, cidade, uf, bairro, tipo_loja, data_abertura
FROM ${farma.schema_silver}.filiais;

CREATE OR REFRESH MATERIALIZED VIEW dim_vendedor (
  id_vendedor BIGINT COMMENT 'Identificador do vendedor no ERP. Chave da dimensão.',
  nome_vendedor STRING COMMENT 'Nome do vendedor.',
  cargo STRING COMMENT 'Atendente, Farmacêutico ou Gerente.',
  id_filial BIGINT COMMENT 'Filial em que o vendedor está lotado.',
  nome_filial STRING COMMENT 'Nome da filial em que o vendedor está lotado.',
  data_admissao DATE COMMENT 'Data de admissão.',
  ativo BOOLEAN COMMENT 'Verdadeiro se o vendedor está ativo.'
)
COMMENT 'Dimensão de vendedores. Vendas do e-commerce não têm vendedor.'
AS SELECT v.id_vendedor, v.nome_vendedor, v.cargo, v.id_filial, f.nome_filial, v.data_admissao, v.ativo
FROM ${farma.schema_silver}.vendedores AS v
LEFT JOIN ${farma.schema_silver}.filiais AS f ON f.id_filial = v.id_filial;

CREATE OR REFRESH MATERIALIZED VIEW dim_cliente (
  id_cliente BIGINT COMMENT 'Identificador do cliente no ERP. Chave da dimensão.',
  sexo STRING COMMENT 'F ou M.',
  faixa_etaria STRING COMMENT 'Faixa de idade atual: Até 24, 25 a 39, 40 a 59 ou 60 ou mais.',
  cidade STRING COMMENT 'Cidade de residência.',
  uf STRING COMMENT 'Sigla do estado de residência.',
  programa_fidelidade BOOLEAN COMMENT 'Verdadeiro se o cliente participa do programa de fidelidade.',
  data_cadastro DATE COMMENT 'Data em que o cliente foi cadastrado.'
)
COMMENT 'Dimensão de clientes identificados, sem dados pessoais. Vendas de balcão sem identificação não têm cliente.'
AS SELECT
  id_cliente,
  sexo,
  CASE
    WHEN floor(months_between(current_date(), data_nascimento) / 12) < 25 THEN 'Até 24'
    WHEN floor(months_between(current_date(), data_nascimento) / 12) < 40 THEN '25 a 39'
    WHEN floor(months_between(current_date(), data_nascimento) / 12) < 60 THEN '40 a 59'
    ELSE '60 ou mais'
  END AS faixa_etaria,
  cidade,
  uf,
  programa_fidelidade,
  data_cadastro
FROM ${farma.schema_silver}.clientes;

CREATE OR REFRESH MATERIALIZED VIEW dim_data (
  data DATE COMMENT 'Dia do calendário. Chave da dimensão.',
  ano INT COMMENT 'Ano, ex.: 2025.',
  trimestre INT COMMENT 'Trimestre do ano, de 1 a 4.',
  mes INT COMMENT 'Mês do ano, de 1 a 12.',
  nome_mes STRING COMMENT 'Nome do mês em português.',
  ano_mes STRING COMMENT 'Ano e mês no formato AAAA-MM.',
  dia INT COMMENT 'Dia do mês.',
  dia_semana STRING COMMENT 'Nome do dia da semana em português.',
  fim_de_semana BOOLEAN COMMENT 'Verdadeiro para sábado e domingo.'
)
COMMENT 'Dimensão calendário, cobrindo do primeiro ao último dia com vendas.'
AS SELECT
  data,
  year(data) AS ano,
  quarter(data) AS trimestre,
  month(data) AS mes,
  element_at(
    array('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'),
    month(data)
  ) AS nome_mes,
  date_format(data, 'yyyy-MM') AS ano_mes,
  day(data) AS dia,
  element_at(array('Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'), dayofweek(data)) AS dia_semana,
  dayofweek(data) IN (1, 7) AS fim_de_semana
FROM (
  SELECT explode(sequence(min(data_venda), max(data_venda), INTERVAL 1 DAY)) AS data
  FROM ${farma.schema_silver}.vendas
);
