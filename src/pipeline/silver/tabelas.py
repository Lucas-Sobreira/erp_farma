"""Silver: dados tipados, padronizados, validados e sem duplicatas.

Cada entidade é descrita de forma declarativa em ENTIDADES:
  - `colunas`: nome da coluna Silver -> expressão SQL sobre a Bronze;
  - `regras`: expectations; a linha que violar qualquer uma é descartada e
    contabilizada nas métricas de qualidade do pipeline;
  - `chaves` + `sequencia`: o AUTO CDC mantém uma linha por chave, ficando com a
    versão mais recente (SCD tipo 1). Isso elimina duplicatas e aplica as
    alterações de cadastro e de status que chegam nas cargas diárias.

A integridade entre tabelas (item -> venda -> produto) é validada na Gold.
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

BRONZE = spark.conf.get("farma.schema_bronze")
SILVER = spark.conf.get("farma.schema_silver")


def texto(coluna: str) -> str:
    """Remove espaços nas pontas e repetidos; vazio vira nulo."""
    return f"nullif(trim(regexp_replace({coluna}, ' +', ' ')), '')"


def inteiro(coluna: str) -> str:
    return f"try_cast({coluna} AS BIGINT)"


def decimal_br(coluna: str) -> str:
    """Aceita decimal com vírgula (CSV do ERP) ou com ponto (JSON)."""
    return f"try_cast(replace({coluna}, ',', '.') AS DECIMAL(12,2))"


def data(coluna: str) -> str:
    return f"try_cast({coluna} AS DATE)"


def carimbo(coluna: str) -> str:
    return f"try_cast({coluna} AS TIMESTAMP)"


def sim_nao(coluna: str) -> str:
    return f"upper(trim({coluna})) = 'S'"


CANAL = """CASE lower(trim(canal))
    WHEN 'loja física' THEN 'Loja Física'
    WHEN 'e-commerce' THEN 'E-commerce'
    WHEN 'delivery' THEN 'Delivery'
    WHEN 'convênio' THEN 'Convênio'
END"""

# O ERP manda a data em ISO, mas alguns registros chegam no formato brasileiro.
DATA_HORA_VENDA = """coalesce(
    try_cast(data_hora_venda AS TIMESTAMP),
    try_to_timestamp(data_hora_venda, 'dd/MM/yyyy HH:mm:ss')
)"""

ENTIDADES = {
    "filiais": {
        "comentario": "Filiais (lojas) da rede.",
        "chaves": ["id_filial"],
        "sequencia": "atualizado_em",
        "colunas": {
            "id_filial": inteiro("id_filial"),
            "nome_filial": texto("nome_filial"),
            "cnpj": texto("cnpj"),
            "cidade": texto("cidade"),
            "uf": f"upper({texto('uf')})",
            "bairro": texto("bairro"),
            "tipo_loja": texto("tipo_loja"),
            "data_abertura": data("data_abertura"),
            "atualizado_em": carimbo("atualizado_em"),
        },
        "regras": {"id_filial_valido": "id_filial IS NOT NULL", "nome_preenchido": "nome_filial IS NOT NULL"},
    },
    "fornecedores": {
        "comentario": "Fornecedores: laboratórios, indústrias de consumo e distribuidoras.",
        "chaves": ["id_fornecedor"],
        "sequencia": "atualizado_em",
        "colunas": {
            "id_fornecedor": inteiro("id_fornecedor"),
            "razao_social": texto("razao_social"),
            "cnpj": texto("cnpj"),
            "tipo_fornecedor": texto("tipo_fornecedor"),
            "cidade": texto("cidade"),
            "uf": f"upper({texto('uf')})",
            "atualizado_em": carimbo("atualizado_em"),
        },
        "regras": {"id_fornecedor_valido": "id_fornecedor IS NOT NULL"},
    },
    "produtos": {
        "comentario": "Cadastro de produtos (medicamentos e não medicamentos) com preço vigente.",
        "chaves": ["id_produto"],
        "sequencia": "atualizado_em",
        "colunas": {
            "id_produto": inteiro("id_produto"),
            "ean": texto("ean"),
            "nome_produto": texto("nome_produto"),
            "principio_ativo": texto("principio_ativo"),
            "laboratorio": texto("laboratorio"),
            "categoria": texto("categoria"),
            "tipo_produto": texto("tipo_produto"),
            "tarja": f"coalesce({texto('tarja')}, 'Não se aplica')",
            "controlado": sim_nao("controlado"),
            "exige_receita": sim_nao("exige_receita"),
            "id_fornecedor": inteiro("id_fornecedor"),
            "preco_custo": decimal_br("preco_custo"),
            "preco_venda": decimal_br("preco_venda"),
            "ativo": sim_nao("ativo"),
            "data_cadastro": data("data_cadastro"),
            "atualizado_em": carimbo("atualizado_em"),
        },
        "regras": {
            "id_produto_valido": "id_produto IS NOT NULL",
            "nome_preenchido": "nome_produto IS NOT NULL",
            "categoria_preenchida": "categoria IS NOT NULL",
            "preco_venda_positivo": "preco_venda > 0",
        },
    },
    "vendedores": {
        "comentario": "Equipe de atendimento das filiais.",
        "chaves": ["id_vendedor"],
        "sequencia": "atualizado_em",
        "colunas": {
            "id_vendedor": inteiro("id_vendedor"),
            "nome_vendedor": texto("nome_vendedor"),
            "cargo": texto("cargo"),
            "id_filial": inteiro("id_filial"),
            "data_admissao": data("data_admissao"),
            "ativo": sim_nao("ativo"),
            "atualizado_em": carimbo("atualizado_em"),
        },
        "regras": {"id_vendedor_valido": "id_vendedor IS NOT NULL"},
    },
    # Dados pessoais não passam da Bronze: nome, e-mail e telefone são descartados
    # e o CPF vira um hash irreversível, útil apenas para identificar a mesma pessoa.
    "clientes": {
        "comentario": "Clientes identificados, sem dados pessoais em claro (CPF apenas como hash).",
        "chaves": ["id_cliente"],
        "sequencia": "atualizado_em",
        "colunas": {
            "id_cliente": inteiro("id_cliente"),
            "cpf_hash": "sha2(regexp_replace(cpf, '[^0-9]', ''), 256)",
            "data_nascimento": data("data_nascimento"),
            "sexo": f"upper({texto('sexo')})",
            "cidade": texto("cidade"),
            "uf": f"upper({texto('uf')})",
            "programa_fidelidade": sim_nao("programa_fidelidade"),
            "possui_email": f"{texto('email')} IS NOT NULL",
            "data_cadastro": data("data_cadastro"),
            "atualizado_em": carimbo("atualizado_em"),
        },
        "regras": {"id_cliente_valido": "id_cliente IS NOT NULL"},
    },
    "vendas": {
        "comentario": "Cabeçalho das vendas (cupons), incluindo as canceladas.",
        "chaves": ["id_venda"],
        "sequencia": "extraido_em",
        "colunas": {
            "id_venda": inteiro("id_venda"),
            "numero_cupom": texto("numero_cupom"),
            "data_hora_venda": DATA_HORA_VENDA,
            "data_venda": f"CAST({DATA_HORA_VENDA} AS DATE)",
            "id_filial": inteiro("id_filial"),
            "id_cliente": inteiro("id_cliente"),
            "id_vendedor": inteiro("id_vendedor"),
            "canal": CANAL,
            "status": "upper(trim(status))",
            "valor_bruto": decimal_br("valor_bruto"),
            "valor_desconto": decimal_br("valor_desconto"),
            "valor_total": decimal_br("valor_total"),
            "extraido_em": carimbo("extraido_em"),
        },
        "regras": {
            "id_venda_valido": "id_venda IS NOT NULL",
            "data_valida": "data_hora_venda IS NOT NULL",
            "filial_preenchida": "id_filial IS NOT NULL",
            "canal_reconhecido": "canal IS NOT NULL",
            "status_reconhecido": "status IN ('CONCLUIDA', 'CANCELADA')",
            "valor_total_nao_negativo": "valor_total >= 0",
        },
    },
    "itens_venda": {
        "comentario": "Itens (produtos) de cada venda.",
        "chaves": ["id_venda", "numero_item"],
        "sequencia": "extraido_em",
        "colunas": {
            "id_venda": inteiro("id_venda"),
            "numero_item": "try_cast(numero_item AS INT)",
            "id_produto": inteiro("id_produto"),
            "quantidade": "try_cast(quantidade AS INT)",
            "preco_unitario": decimal_br("preco_unitario"),
            "custo_unitario": decimal_br("custo_unitario"),
            "valor_desconto": decimal_br("valor_desconto"),
            "valor_total_item": decimal_br("valor_total_item"),
            "extraido_em": carimbo("extraido_em"),
        },
        "regras": {
            "chave_valida": "id_venda IS NOT NULL AND numero_item IS NOT NULL",
            "produto_preenchido": "id_produto IS NOT NULL",
            "quantidade_positiva": "quantidade > 0",
            "preco_nao_negativo": "preco_unitario >= 0",
        },
    },
    "pagamentos": {
        "comentario": "Pagamentos recebidos por venda (uma venda pode ter mais de um).",
        "chaves": ["id_pagamento"],
        "sequencia": "extraido_em",
        "colunas": {
            "id_pagamento": inteiro("id_pagamento"),
            "id_venda": inteiro("id_venda"),
            "forma_pagamento": texto("forma_pagamento"),
            "bandeira": texto("bandeira"),
            "parcelas": "try_cast(parcelas AS INT)",
            "valor_pago": decimal_br("valor_pago"),
            "extraido_em": carimbo("extraido_em"),
        },
        "regras": {
            "id_pagamento_valido": "id_pagamento IS NOT NULL",
            "venda_preenchida": "id_venda IS NOT NULL",
            "forma_preenchida": "forma_pagamento IS NOT NULL",
            "valor_pago_positivo": "valor_pago > 0",
        },
    },
    "estoque_lotes": {
        "comentario": "Posição diária de estoque por filial, produto e lote.",
        "chaves": ["data_posicao", "id_filial", "id_produto", "lote"],
        "sequencia": "extraido_em",
        "colunas": {
            "data_posicao": data("data_posicao"),
            "id_filial": inteiro("id_filial"),
            "id_produto": inteiro("id_produto"),
            "lote": texto("lote"),
            "data_validade": data("data_validade"),
            "quantidade_disponivel": "try_cast(quantidade_disponivel AS INT)",
            "custo_unitario": decimal_br("custo_unitario"),
            "extraido_em": carimbo("extraido_em"),
        },
        "regras": {
            "chave_valida": "data_posicao IS NOT NULL AND id_filial IS NOT NULL AND id_produto IS NOT NULL AND lote IS NOT NULL",
            "validade_preenchida": "data_validade IS NOT NULL",
            "quantidade_nao_negativa": "quantidade_disponivel >= 0",
        },
    },
}


def criar_tabela_silver(entidade: str, definicao: dict) -> None:
    visao_tratada = f"{entidade}_tratada"

    @dp.temporary_view(name=visao_tratada)
    @dp.expect_all_or_drop(definicao["regras"])
    def tratada():
        colunas = [F.expr(expressao).alias(nome) for nome, expressao in definicao["colunas"].items()]
        return spark.readStream.table(f"{BRONZE}.{entidade}").select(*colunas, "_data_ingestao")

    dp.create_streaming_table(name=f"{SILVER}.{entidade}", comment=definicao["comentario"])
    dp.create_auto_cdc_flow(
        target=f"{SILVER}.{entidade}",
        source=visao_tratada,
        keys=definicao["chaves"],
        # Em empate na data do ERP, vale o arquivo ingerido por último.
        sequence_by=F.struct(definicao["sequencia"], "_data_ingestao"),
        stored_as_scd_type=1,
    )


for _entidade, _definicao in ENTIDADES.items():
    criar_tabela_silver(_entidade, _definicao)
