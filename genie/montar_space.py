"""Monta o payload do Genie space a partir dos arquivos desta pasta.

Uso (na raiz do repositório):
  python genie/montar_space.py > genie/space.json
  databricks genie create-space <warehouse_id> "" --json @genie/space.json

As fontes de verdade continuam sendo instrucoes.md (bloco "Instruções gerais" e
tabela de relacionamentos), perguntas_exemplo.md (perguntas com ★) e
consultas_exemplo.sql.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

PASTA = Path(__file__).parent
CATALOGO_SCHEMA = "erp_farma.gold"
TITULO = "Farma - Assistente Comercial"
DESCRICAO = "Chatbot da área comercial da farmácia: vendas, pagamentos, produtos e estoque."
TABELAS = [
    "dim_cliente", "dim_data", "dim_filial", "dim_produto", "dim_vendedor",
    "fato_estoque", "fato_pagamentos", "fato_vendas",
]  # fmt: skip


def _id(*partes: str) -> str:
    return hashlib.md5("|".join(partes).encode()).hexdigest()


def _linhas(texto: str) -> list[str]:
    return [linha + "\n" for linha in texto.strip().split("\n")]


def instrucoes_gerais() -> str:
    markdown = (PASTA / "instrucoes.md").read_text(encoding="utf-8")
    return re.search(r"## Instruções gerais\s+```\n(.*?)```", markdown, re.S).group(1)


def relacionamentos() -> list[dict]:
    markdown = (PASTA / "instrucoes.md").read_text(encoding="utf-8")
    juncoes = []
    for esquerda, coluna_e, direita, coluna_d in re.findall(r"^\| (\w+) \| (\w+) \| (\w+) \| (\w+) \|", markdown, re.M):
        juncoes.append(
            {
                "id": _id("join", esquerda, coluna_e, direita),
                "left": {"identifier": f"{CATALOGO_SCHEMA}.{esquerda}", "alias": esquerda},
                "right": {"identifier": f"{CATALOGO_SCHEMA}.{direita}", "alias": direita},
                "sql": [
                    f"`{esquerda}`.`{coluna_e}` = `{direita}`.`{coluna_d}`",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--",
                ],
            }
        )
    return juncoes


def consultas() -> list[dict]:
    sql = (PASTA / "consultas_exemplo.sql").read_text(encoding="utf-8")
    exemplos = []
    for pergunta, corpo in re.findall(r"^-- \d+\. (.+?)\n(.*?;)", sql, re.S | re.M):
        corpo = re.sub(r"\b(fato_\w+|dim_\w+) AS", rf"{CATALOGO_SCHEMA}.\1 AS", corpo.rstrip(";"))
        exemplos.append({"id": _id("sql", pergunta), "question": [pergunta], "sql": _linhas(corpo)})
    return exemplos


def perguntas_sugeridas() -> list[dict]:
    markdown = (PASTA / "perguntas_exemplo.md").read_text(encoding="utf-8")
    return [{"id": _id("pergunta", p), "question": [p]} for p in re.findall(r"^(?:\d+\.|-) ★ (.+)", markdown, re.M)]


def por_id(itens: list[dict]) -> list[dict]:
    return sorted(itens, key=lambda item: item["id"])


def main() -> None:
    space = {
        "version": 2,
        "config": {"sample_questions": por_id(perguntas_sugeridas())},
        "data_sources": {"tables": [{"identifier": f"{CATALOGO_SCHEMA}.{t}"} for t in sorted(TABELAS)]},
        "instructions": {
            "text_instructions": [{"id": _id("instrucoes"), "content": _linhas(instrucoes_gerais())}],
            "example_question_sqls": por_id(consultas()),
            "join_specs": por_id(relacionamentos()),
        },
    }
    payload = {"title": TITULO, "description": DESCRICAO, "serialized_space": json.dumps(space, ensure_ascii=False)}
    if len(sys.argv) > 1:
        payload["warehouse_id"] = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
