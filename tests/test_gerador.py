import csv
import json
from datetime import date, timedelta

import catalogos as c
import main
import pytest
from entidades import STATUS_CANCELADA, Gerador, fator_reajuste

DIA = date(2025, 7, 15)


@pytest.fixture(scope="module")
def gerador():
    return Gerador(semente=42, vendas_dia=270)


def _centavos(valor):
    return round(valor * 100)


def test_mesma_semente_gera_os_mesmos_dados(gerador):
    outro = Gerador(semente=42, vendas_dia=270)
    assert gerador.vendas_do_dia(DIA) == outro.vendas_do_dia(DIA)
    assert gerador.cadastros(DIA) == outro.cadastros(DIA)
    assert gerador.estoque_do_dia(DIA) == outro.estoque_do_dia(DIA)


def test_sementes_diferentes_geram_dados_diferentes(gerador):
    assert gerador.vendas_do_dia(DIA) != Gerador(semente=7).vendas_do_dia(DIA)


def test_integridade_referencial_do_movimento_limpo(gerador):
    cadastros = gerador.cadastros(DIA)
    ids = {
        entidade: {r[f"id_{entidade[:-1]}"] for r in registros}
        for entidade, registros in cadastros.items()
        if entidade in ("produtos", "clientes")
    }
    ids_filiais = {f["id_filial"] for f in cadastros["filiais"]}
    ids_vendedores = {v["id_vendedor"] for v in cadastros["vendedores"]}
    vendas, itens, pagamentos = gerador.vendas_do_dia(DIA, sujeira=False)

    ids_vendas = [v["id_venda"] for v in vendas]
    assert len(ids_vendas) == len(set(ids_vendas))
    for venda in vendas:
        assert venda["id_filial"] in ids_filiais
        assert venda["id_cliente"] is None or venda["id_cliente"] in ids["clientes"]
        assert venda["id_vendedor"] is None or venda["id_vendedor"] in ids_vendedores
    assert {i["id_venda"] for i in itens} == set(ids_vendas)
    assert all(i["id_produto"] in ids["produtos"] for i in itens)
    assert {p["id_venda"] for p in pagamentos} <= set(ids_vendas)


def test_totais_da_venda_batem_com_itens_e_pagamentos(gerador):
    vendas, itens, pagamentos = gerador.vendas_do_dia(DIA, sujeira=False)
    soma_itens, soma_pagamentos = {}, {}
    for item in itens:
        assert _centavos(item["valor_total_item"]) == _centavos(item["preco_unitario"]) * item[
            "quantidade"
        ] - _centavos(item["valor_desconto"])
        soma_itens[item["id_venda"]] = soma_itens.get(item["id_venda"], 0) + _centavos(item["valor_total_item"])
    for pagamento in pagamentos:
        soma_pagamentos[pagamento["id_venda"]] = soma_pagamentos.get(pagamento["id_venda"], 0) + _centavos(
            pagamento["valor_pago"]
        )
    for venda in vendas:
        assert _centavos(venda["valor_total"]) == soma_itens[venda["id_venda"]]
        assert _centavos(venda["valor_total"]) == _centavos(venda["valor_bruto"]) - _centavos(venda["valor_desconto"])
        if venda["status"] == STATUS_CANCELADA:
            assert venda["id_venda"] not in soma_pagamentos
        else:
            assert soma_pagamentos[venda["id_venda"]] == _centavos(venda["valor_total"])


def test_regras_de_negocio_do_canal(gerador):
    controlados = {p["id_produto"] for p in gerador.produtos if p["controlado"]}
    vendas, itens, pagamentos = gerador.vendas_do_dia(DIA, sujeira=False)
    canal = {v["id_venda"]: v["canal"] for v in vendas}
    assert set(canal.values()) == {c.CANAL_LOJA, c.CANAL_ECOMMERCE, c.CANAL_DELIVERY, c.CANAL_CONVENIO}
    assert not any(i["id_produto"] in controlados for i in itens if canal[i["id_venda"]] == c.CANAL_ECOMMERCE)
    for pagamento in pagamentos:
        assert pagamento["forma_pagamento"] in c.PAGAMENTO_POR_CANAL[canal[pagamento["id_venda"]]][0]
    for venda in vendas:
        if venda["canal"] == c.CANAL_ECOMMERCE:
            assert venda["id_filial"] == 1 and venda["id_vendedor"] is None
        if venda["canal"] != c.CANAL_LOJA:
            assert venda["id_cliente"] is not None


def test_sujeira_aparece_no_movimento(gerador):
    vendas, itens = [], []
    for n in range(31):
        v, i, _ = gerador.vendas_do_dia(DIA + timedelta(days=n))
        vendas += v
        itens += i
    ids_vendas = [v["id_venda"] for v in vendas]
    assert len(ids_vendas) > len(set(ids_vendas)), "esperava vendas duplicadas"
    assert any("/" in v["data_hora_venda"] for v in vendas), "esperava datas em formato alternativo"
    assert any(v["canal"] not in c.PAGAMENTO_POR_CANAL for v in vendas), "esperava canal fora do padrão"
    assert any(i["quantidade"] <= 0 for i in itens)
    assert any(i["id_produto"] is None for i in itens)
    assert {i["id_venda"] for i in itens} - set(ids_vendas), "esperava itens órfãos"


def test_reajuste_anual_de_precos(gerador):
    assert fator_reajuste(date(2023, 3, 31)) == 1.0
    assert fator_reajuste(date(2023, 4, 1)) == pytest.approx(1.056)
    assert fator_reajuste(date(2024, 4, 1)) == pytest.approx(1.056 * 1.045)
    dia_reajuste = date(2025, 4, 1)
    alterados = gerador.cadastros_alterados(dia_reajuste)["produtos"]
    assert len(alterados) == len(gerador.cadastros(dia_reajuste)["produtos"])
    assert len(gerador.cadastros_alterados(DIA)["produtos"]) < 20


def test_cadastro_incremental_traz_clientes_novos_e_alterados(gerador):
    alterados = gerador.cadastros_alterados(DIA)["clientes"]
    novos = [cl for cl in alterados if cl["data_cadastro"] == DIA.isoformat()]
    antigos = [cl for cl in alterados if cl["data_cadastro"] < DIA.isoformat()]
    assert len(antigos) == 12
    assert all(cl["atualizado_em"].startswith(DIA.isoformat()) for cl in antigos)
    ids_ate_ontem = {cl["id_cliente"] for cl in gerador.cadastros(DIA - timedelta(days=1))["clientes"]}
    assert not {cl["id_cliente"] for cl in novos} & ids_ate_ontem


def test_estoque_respeita_filiais_abertas(gerador):
    antes_de_sumare = date(2023, 6, 1)
    assert 7 not in {p["id_filial"] for p in gerador.estoque_do_dia(antes_de_sumare)}
    posicoes = gerador.estoque_do_dia(DIA)
    chaves = [(p["id_filial"], p["id_produto"], p["lote"]) for p in posicoes]
    assert len(chaves) == len(set(chaves))
    assert any(p["data_validade"] < DIA.isoformat() for p in posicoes), "esperava lotes vencidos"


def test_backfill_e_diario_gravam_o_layout_esperado(tmp_path):
    gerador = Gerador(semente=42, vendas_dia=20, total_clientes=2_000)
    referencia = date(2025, 3, 10)
    fim = referencia - timedelta(days=1)

    contagem = main.executar_backfill(gerador, tmp_path, referencia, anos_historico=1)
    pasta = f"dt={fim.isoformat()}"
    arquivos_vendas = sorted(p.name for p in (tmp_path / "vendas" / pasta).iterdir())
    assert len(arquivos_vendas) == 13  # março de um ano a março do outro
    assert arquivos_vendas[-1] == "vendas_2025-03.json"
    linhas = [
        json.loads(linha) for arq in (tmp_path / "vendas" / pasta).iterdir() for linha in arq.open(encoding="utf-8")
    ]
    assert len(linhas) == contagem["vendas"]

    with (tmp_path / "produtos" / pasta / "produtos.csv").open(encoding="utf-8", newline="") as arquivo:
        produtos = list(csv.DictReader(arquivo, delimiter=";"))
    assert len(produtos) == contagem["produtos"]
    assert "," in produtos[0]["preco_venda"] and "." not in produtos[0]["preco_venda"]

    main.executar_diario(gerador, tmp_path, referencia)
    pasta_diaria = tmp_path / "vendas" / f"dt={referencia.isoformat()}"
    assert [p.name for p in pasta_diaria.iterdir()] == [f"vendas_{referencia.isoformat()}.json"]
    assert not (tmp_path / "fornecedores" / f"dt={referencia.isoformat()}").exists()
    assert (tmp_path / "estoque_lotes" / f"dt={referencia.isoformat()}").exists()
