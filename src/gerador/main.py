"""Simula a extração do ERP da farmácia, gravando arquivos na camada Landing.

Layout de saída: <destino>/<entidade>/dt=<data da extração>/<arquivo>
  - cadastros em CSV (separador ";" e decimal com vírgula, como um ERP brasileiro exporta);
  - movimento em JSON Lines.

Modos:
  backfill  carga inicial: cadastros completos + N anos de movimento até a véspera
            da data de referência (um arquivo de movimento por mês);
  diario    carga incremental: movimento e cadastros alterados na data de referência.

Uso local:
  python src/gerador/main.py --modo backfill --destino _landing --anos-historico 1
"""

import argparse
import csv
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from random import Random

from entidades import Gerador, sujar_cadastro

CAMPOS_TEXTO_SUJEIRA = {
    "filiais": ["nome_filial", "cidade", "uf"],
    "fornecedores": ["razao_social", "cidade", "uf"],
    "produtos": ["nome_produto", "categoria", "laboratorio"],
    "vendedores": ["nome_vendedor", "cargo"],
    "clientes": ["nome_cliente", "cidade", "uf"],
}


def _hoje_brasilia() -> date:
    # O serverless roda em UTC; Brasília é UTC-3 fixo (sem horário de verão).
    return (datetime.now(UTC) - timedelta(hours=3)).date()


def _formatar_csv(valor):
    if valor is None:
        return ""
    if isinstance(valor, float):
        return f"{valor:.2f}".replace(".", ",")
    return valor


def gravar_csv(caminho: Path, registros: list[dict]) -> None:
    if not registros:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(registros[0].keys())
        escritor.writerows([_formatar_csv(v) for v in r.values()] for r in registros)


def gravar_jsonl(caminho: Path, registros: list[dict]) -> None:
    if not registros:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        arquivo.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in registros)


def _gravar_cadastros(gerador: Gerador, destino: Path, dt: date, cadastros: dict[str, list[dict]]) -> dict[str, int]:
    contagem = {}
    for entidade, registros in cadastros.items():
        rng = Random(f"{gerador.semente}|sujeira|{entidade}|{dt.isoformat()}")
        registros = sujar_cadastro(rng, registros, CAMPOS_TEXTO_SUJEIRA[entidade])
        gravar_csv(destino / entidade / f"dt={dt.isoformat()}" / f"{entidade}.csv", registros)
        contagem[entidade] = len(registros)
    return contagem


def _gravar_movimento(destino: Path, dt: date, sufixo: str, movimento: dict[str, list[dict]]) -> None:
    for entidade, registros in movimento.items():
        gravar_jsonl(destino / entidade / f"dt={dt.isoformat()}" / f"{entidade}_{sufixo}.json", registros)


def executar_backfill(gerador: Gerador, destino: Path, referencia: date, anos_historico: int) -> dict[str, int]:
    fim = referencia - timedelta(days=1)
    inicio = fim - timedelta(days=365 * anos_historico)
    contagem = _gravar_cadastros(gerador, destino, fim, gerador.cadastros(fim))
    contagem.update(vendas=0, itens_venda=0, pagamentos=0)

    mes: dict[str, list[dict]] = {"vendas": [], "itens_venda": [], "pagamentos": []}
    dia = inicio
    while dia <= fim:
        vendas, itens, pagamentos = gerador.vendas_do_dia(dia)
        for entidade, registros in (("vendas", vendas), ("itens_venda", itens), ("pagamentos", pagamentos)):
            mes[entidade].extend(registros)
            contagem[entidade] += len(registros)
        amanha = dia + timedelta(days=1)
        if amanha.month != dia.month or amanha > fim:
            _gravar_movimento(destino, fim, f"{dia:%Y-%m}", mes)
            mes = {entidade: [] for entidade in mes}
        dia = amanha

    estoque = gerador.estoque_do_dia(fim)
    _gravar_movimento(destino, fim, fim.isoformat(), {"estoque_lotes": estoque})
    contagem["estoque_lotes"] = len(estoque)
    return contagem


def executar_diario(gerador: Gerador, destino: Path, referencia: date) -> dict[str, int]:
    contagem = _gravar_cadastros(gerador, destino, referencia, gerador.cadastros_alterados(referencia))
    vendas, itens, pagamentos = gerador.vendas_do_dia(referencia)
    movimento = {
        "vendas": vendas,
        "itens_venda": itens,
        "pagamentos": pagamentos,
        "estoque_lotes": gerador.estoque_do_dia(referencia),
    }
    _gravar_movimento(destino, referencia, referencia.isoformat(), movimento)
    contagem.update({entidade: len(registros) for entidade, registros in movimento.items()})
    return contagem


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modo", choices=["backfill", "diario"], required=True)
    parser.add_argument("--destino", required=True, help="Pasta raiz da Landing (ex.: /Volumes/<catalogo>/landing/erp)")
    parser.add_argument(
        "--data-referencia",
        type=lambda texto: date.fromisoformat(texto) if texto else _hoje_brasilia(),
        default="",
        help="AAAA-MM-DD (padrão: hoje, no horário de Brasília)",
    )
    parser.add_argument("--anos-historico", type=int, default=3)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--vendas-dia", type=int, default=270, help="Média de vendas por dia no início do histórico")
    args = parser.parse_args(argv)

    gerador = Gerador(semente=args.semente, vendas_dia=args.vendas_dia)
    destino = Path(args.destino)
    if args.modo == "backfill":
        contagem = executar_backfill(gerador, destino, args.data_referencia, args.anos_historico)
    else:
        contagem = executar_diario(gerador, destino, args.data_referencia)

    print(f"Modo {args.modo} | referência {args.data_referencia} | destino {destino}")
    for entidade, total in contagem.items():
        print(f"  {entidade:<14} {total:>9,} registros".replace(",", "."))


if __name__ == "__main__":
    main()
