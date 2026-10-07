"""Bronze: cópia fiel dos arquivos da Landing, uma streaming table por entidade.

Nenhuma regra de negócio aqui. Todas as colunas chegam como texto (sem inferência
de tipos) e o que não couber no schema vai para `_rescued_data`. A pasta
`dt=AAAA-MM-DD` vira a coluna `dt` (data da extração).
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

LANDING = spark.conf.get("farma.landing")
BRONZE = spark.conf.get("farma.schema_bronze")

ENTIDADES = {
    "filiais": "csv",
    "fornecedores": "csv",
    "produtos": "csv",
    "vendedores": "csv",
    "clientes": "csv",
    "vendas": "json",
    "itens_venda": "json",
    "pagamentos": "json",
    "estoque_lotes": "json",
}


def criar_tabela_bronze(entidade: str, formato: str) -> None:
    @dp.table(
        name=f"{BRONZE}.{entidade}",
        comment=f"Dados brutos de {entidade} extraídos do ERP, como chegaram na Landing.",
    )
    def tabela():
        leitor = (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", formato)
            .option("cloudFiles.inferColumnTypes", "false")
        )
        if formato == "csv":
            leitor = leitor.option("header", "true").option("sep", ";")
        return leitor.load(f"{LANDING}/{entidade}/").select(
            "*",
            F.col("_metadata.file_path").alias("_arquivo_origem"),
            F.current_timestamp().alias("_data_ingestao"),
        )


for _entidade, _formato in ENTIDADES.items():
    criar_tabela_bronze(_entidade, _formato)
