"""Geração determinística das entidades do ERP fictício de farmácia.

O mesmo par (semente, data) sempre produz os mesmos registros, de modo que a
carga histórica (`backfill`) e a carga diária (`diario`) são consistentes entre
si: as vendas de um dia são idênticas nos dois modos.

Valores monetários são calculados em centavos (inteiros) e só viram reais no
registro final, para que os totais de venda batam exatamente com a soma dos itens.
"""

import bisect
import unicodedata
from datetime import date, datetime, time, timedelta
from itertools import accumulate
from random import Random

import catalogos as c

STATUS_CONCLUIDA = "CONCLUIDA"
STATUS_CANCELADA = "CANCELADA"

_SUFIXOS_MARCA = ["max", "cor", "dol", "flex", "vit", "tec", "pan", "zol", "lin", "prax"]
_CIDADES_FORNECEDORES = [
    ("São Paulo", "SP"), ("Hortolândia", "SP"), ("Anápolis", "GO"), ("Toledo", "PR"),
    ("Itapira", "SP"), ("Rio de Janeiro", "RJ"), ("Pouso Alegre", "MG"), ("Campinas", "SP"),
]  # fmt: skip
# Movimento de loja concentrado no horário comercial (7h às 22h).
_HORAS_LOJA = list(range(7, 23))
_PESOS_HORAS_LOJA = [2, 4, 6, 7, 7, 8, 8, 6, 6, 6, 7, 9, 10, 8, 5, 3]


def fator_reajuste(dia: date) -> float:
    """Reajuste acumulado de preços entre a DATA_BASE e `dia`."""
    fator = 1.0
    for ano, percentual in c.REAJUSTES_ANUAIS.items():
        if c.DATA_BASE < date(ano, 4, 1) <= dia:
            fator *= 1 + percentual
    return fator


def _ultimo_reajuste(dia: date) -> date | None:
    datas = [date(ano, 4, 1) for ano in c.REAJUSTES_ANUAIS if c.DATA_BASE < date(ano, 4, 1) <= dia]
    return max(datas) if datas else None


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def _nome_curto(fabricante: str) -> str:
    genericas = {"Laboratório", "Laboratórios", "Farmacêutica", "Indústria", "Pharma", "Brasil"}
    return " ".join(p for p in fabricante.split() if p not in genericas)


def _sn(valor: bool) -> str:
    return "S" if valor else "N"


def _ts(dia: date, hora: int = 0, minuto: int = 0, segundo: int = 0) -> str:
    return datetime.combine(dia, time(hora, minuto, segundo)).isoformat()


def _reais(centavos: int) -> float:
    return round(centavos / 100, 2)


def _data_entre(rng: Random, inicio: date, fim: date) -> date:
    return inicio + timedelta(days=rng.randrange((fim - inicio).days + 1))


def _ean_ficticio(rng: Random) -> str:
    # Prefixo 2 é de uso interno no GS1: nunca coincide com um produto real.
    corpo = "2" + "".join(str(rng.randrange(10)) for _ in range(11))
    soma = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(corpo))
    return corpo + str((10 - soma % 10) % 10)


def _cpf_ficticio(rng: Random) -> str:
    # O primeiro dígito verificador é propositalmente errado: não existe CPF real igual.
    base = [rng.randrange(10) for _ in range(9)]
    resto = sum(d * p for d, p in zip(base, range(10, 1, -1), strict=True)) * 10 % 11 % 10
    digitos = base + [(resto + 1) % 10, rng.randrange(10)]
    t = "".join(map(str, digitos))
    return f"{t[:3]}.{t[3:6]}.{t[6:9]}-{t[9:]}"


def _cnpj_ficticio(rng: Random) -> str:
    t = "".join(str(rng.randrange(10)) for _ in range(8))
    return f"{t[:2]}.{t[2:5]}.{t[5:8]}/0001-{rng.randrange(100):02d}"


class Gerador:
    def __init__(self, semente: int = 42, vendas_dia: int = 270, total_clientes: int = 30_000):
        self.semente = semente
        self.vendas_dia = vendas_dia
        self.fornecedores = self._criar_fornecedores()
        self.filiais = self._criar_filiais()
        self.produtos = self._criar_produtos()
        self.vendedores = self._criar_vendedores()
        self.clientes = self._criar_clientes(total_clientes)
        self._datas_cadastro_clientes = [cl["_data_cadastro"] for cl in self.clientes]
        self._vendedores_por_filial: dict[int, list[dict]] = {}
        for vendedor in self.vendedores:
            self._vendedores_por_filial.setdefault(vendedor["id_filial"], []).append(vendedor)
        self._pesos_acumulados_mes = {
            mes: list(
                accumulate(p["_peso"] * c.SAZONALIDADE.get(p["categoria"], {}).get(mes, 1.0) for p in self.produtos)
            )
            for mes in range(1, 13)
        }

    def _rng(self, *partes) -> Random:
        return Random("|".join(str(p) for p in (self.semente, *partes)))

    # ------------------------------------------------------------------
    # Cadastros mestres (estado interno; campos com "_" não são exportados)
    # ------------------------------------------------------------------

    def _criar_fornecedores(self) -> list[dict]:
        rng = self._rng("fornecedores")
        grupos = [
            (c.LABORATORIOS, "Laboratório"),
            (c.MARCAS_CONSUMO, "Indústria de Consumo"),
            (c.DISTRIBUIDORAS, "Distribuidora"),
        ]
        fornecedores = []
        for nomes, tipo in grupos:
            for nome in nomes:
                cidade, uf = rng.choice(_CIDADES_FORNECEDORES)
                fornecedores.append(
                    {
                        "id_fornecedor": len(fornecedores) + 1,
                        "razao_social": f"{nome} Ltda",
                        "cnpj": _cnpj_ficticio(rng),
                        "tipo_fornecedor": tipo,
                        "cidade": cidade,
                        "uf": uf,
                        "atualizado_em": _ts(c.DATA_BASE - timedelta(days=365)),
                        "_nome": nome,
                    }
                )
        return fornecedores

    def _criar_filiais(self) -> list[dict]:
        rng = self._rng("filiais")
        return [
            {
                "id_filial": i,
                "nome_filial": nome,
                "cnpj": _cnpj_ficticio(rng),
                "cidade": cidade,
                "uf": uf,
                "bairro": bairro,
                "tipo_loja": tipo,
                "data_abertura": abertura.isoformat(),
                "atualizado_em": _ts(abertura),
                "_data_abertura": abertura,
                "_peso": peso,
            }
            for i, (nome, cidade, uf, bairro, tipo, abertura, peso) in enumerate(c.FILIAIS, start=1)
        ]

    def _criar_produtos(self) -> list[dict]:
        rng = self._rng("produtos")
        id_por_nome = {f["_nome"]: f["id_fornecedor"] for f in self.fornecedores}
        ids_distribuidoras = [id_por_nome[n] for n in c.DISTRIBUIDORAS]
        produtos: list[dict] = []

        def adicionar(nome, principio, fabricante, categoria, tipo, tarja, controlado, preco, margem):
            lancamento_recente = rng.random() < 0.10
            data_cadastro = (
                _data_entre(rng, c.DATA_BASE, c.DATA_BASE + timedelta(days=4 * 365))
                if lancamento_recente
                else _data_entre(rng, c.DATA_BASE - timedelta(days=8 * 365), c.DATA_BASE - timedelta(days=1))
            )
            via_distribuidora = rng.random() < 0.30
            produtos.append(
                {
                    "id_produto": len(produtos) + 1,
                    "ean": _ean_ficticio(rng),
                    "nome_produto": nome,
                    "principio_ativo": principio,
                    "laboratorio": fabricante,
                    "categoria": categoria,
                    "tipo_produto": tipo,
                    "tarja": tarja,
                    "controlado": controlado,
                    "exige_receita": tarja != c.TARJA_SEM if tarja else False,
                    "id_fornecedor": rng.choice(ids_distribuidoras) if via_distribuidora else id_por_nome[fabricante],
                    "_preco_base": round(preco * 100),
                    "_custo_base": round(preco * margem * 100),
                    "_data_cadastro": data_cadastro,
                    "_peso": rng.lognormvariate(0, 0.9) * (1.5 if tipo == "Genérico" else 1.0),
                }
            )

        for principio, categoria, tarja, controlado, dosagens, apresentacoes, preco_base in c.MEDICAMENTOS:
            radical = _sem_acento(principio.split()[0])[:5].capitalize()
            for i_dos, dosagem in enumerate(dosagens):
                for i_apr, apresentacao in enumerate(apresentacoes):
                    preco = preco_base * (1 + 0.35 * i_dos + 0.5 * i_apr)
                    labs = rng.sample(c.LABORATORIOS, 6)
                    marca = radical + rng.choice(_SUFIXOS_MARCA)
                    adicionar(
                        f"{marca} {dosagem} {apresentacao}", principio, labs[0], categoria,
                        "Referência", tarja, controlado, preco * rng.uniform(1.9, 2.6), rng.uniform(0.50, 0.70),
                    )  # fmt: skip
                    for lab in labs[1 : 1 + rng.randint(2, 3)]:
                        adicionar(
                            f"{principio} {dosagem} {apresentacao} Genérico {_nome_curto(lab)}", principio, lab,
                            categoria, "Genérico", tarja, controlado, preco * rng.uniform(0.9, 1.1), rng.uniform(0.35, 0.55),
                        )  # fmt: skip
                    for lab in labs[4 : 4 + rng.randint(0, 2)]:
                        similar = radical + rng.choice(_SUFIXOS_MARCA)
                        adicionar(
                            f"{similar} {dosagem} {apresentacao} {_nome_curto(lab)}", principio, lab, categoria,
                            "Similar", tarja, controlado, preco * rng.uniform(1.2, 1.6), rng.uniform(0.40, 0.60),
                        )  # fmt: skip

        for item, categoria, tamanhos, preco_base in c.NAO_MEDICAMENTOS:
            for marca in rng.sample(c.MARCAS_CONSUMO, rng.randint(2, 3)):
                fator_marca = rng.uniform(0.85, 1.35)
                for i_tam, tamanho in enumerate(tamanhos):
                    adicionar(
                        f"{item} {marca} {tamanho}", None, marca, categoria, "Não medicamento",
                        None, False, preco_base * fator_marca * (1 + 0.6 * i_tam), rng.uniform(0.55, 0.75),
                    )  # fmt: skip

        # Normaliza a popularidade para que cada categoria tenha a fatia definida no catálogo.
        total_por_categoria: dict[str, float] = {}
        for p in produtos:
            total_por_categoria[p["categoria"]] = total_por_categoria.get(p["categoria"], 0) + p["_peso"]
        for p in produtos:
            p["_peso"] *= c.PESO_CATEGORIA[p["categoria"]] / total_por_categoria[p["categoria"]]
        return produtos

    def _criar_vendedores(self) -> list[dict]:
        rng = self._rng("vendedores")
        vendedores = []
        for filial in self.filiais:
            for _ in range(rng.randint(5, 8)):
                admissao = max(
                    filial["_data_abertura"],
                    _data_entre(rng, c.DATA_BASE - timedelta(days=6 * 365), c.DATA_BASE),
                )
                vendedores.append(
                    {
                        "id_vendedor": len(vendedores) + 1,
                        "nome_vendedor": f"{rng.choice(c.NOMES)} {rng.choice(c.SOBRENOMES)}",
                        "cargo": rng.choices(*c.CARGOS)[0],
                        "id_filial": filial["id_filial"],
                        "data_admissao": admissao.isoformat(),
                        "ativo": "S",
                        "atualizado_em": _ts(admissao),
                        "_data_admissao": admissao,
                    }
                )
        return vendedores

    def _criar_clientes(self, total: int) -> list[dict]:
        rng = self._rng("clientes")
        inicio_base = c.DATA_BASE - timedelta(days=5 * 365)
        fim_horizonte = c.DATA_BASE + timedelta(days=6 * 365)
        datas = sorted(
            _data_entre(rng, inicio_base, c.DATA_BASE - timedelta(days=1))
            if rng.random() < 0.55
            else _data_entre(rng, c.DATA_BASE, fim_horizonte)
            for _ in range(total)
        )
        clientes = []
        for i, data_cadastro in enumerate(datas, start=1):
            nome, sobrenome1, sobrenome2 = rng.choice(c.NOMES), rng.choice(c.SOBRENOMES), rng.choice(c.SOBRENOMES)
            usuario = _sem_acento(f"{nome}.{sobrenome2}").lower()
            clientes.append(
                {
                    "id_cliente": i,
                    "nome_cliente": f"{nome} {sobrenome1} {sobrenome2}",
                    "cpf": _cpf_ficticio(rng),
                    "data_nascimento": _data_entre(rng, date(1940, 1, 1), date(2005, 12, 31)).isoformat(),
                    "sexo": "F" if nome in c.NOMES_FEMININOS else "M",
                    "email": f"{usuario}{i}@exemplo.com.br",
                    "telefone": f"(19) 9{rng.randrange(10_000):04d}-{rng.randrange(10_000):04d}",
                    "cidade": rng.choices(*c.CIDADES_CLIENTES)[0],
                    "uf": "SP",
                    "programa_fidelidade": _sn(rng.random() < 0.55),
                    "data_cadastro": data_cadastro.isoformat(),
                    "atualizado_em": _ts(data_cadastro, 10),
                    "_data_cadastro": data_cadastro,
                }
            )
        return clientes

    # ------------------------------------------------------------------
    # Exportação de cadastros
    # ------------------------------------------------------------------

    @staticmethod
    def _publico(registro: dict) -> dict:
        return {k: v for k, v in registro.items() if not k.startswith("_")}

    def _registro_produto(self, produto: dict, ref: date, atualizado_em: str | None = None) -> dict:
        fator = fator_reajuste(ref)
        reajuste = _ultimo_reajuste(ref)
        atualizado = max(filter(None, [produto["_data_cadastro"], reajuste]))
        registro = self._publico(produto)
        registro.update(
            controlado=_sn(produto["controlado"]),
            exige_receita=_sn(produto["exige_receita"]),
            preco_custo=_reais(round(produto["_custo_base"] * fator)),
            preco_venda=_reais(round(produto["_preco_base"] * fator)),
            ativo="S",
            data_cadastro=produto["_data_cadastro"].isoformat(),
            atualizado_em=atualizado_em or _ts(atualizado),
        )
        return registro

    def cadastros(self, ref: date) -> dict[str, list[dict]]:
        """Fotografia completa dos cadastros na data de referência."""
        n_clientes = bisect.bisect_right(self._datas_cadastro_clientes, ref)
        return {
            "filiais": [self._publico(f) for f in self.filiais if f["_data_abertura"] <= ref],
            "fornecedores": [self._publico(f) for f in self.fornecedores],
            "produtos": [self._registro_produto(p, ref) for p in self.produtos if p["_data_cadastro"] <= ref],
            "vendedores": [self._publico(v) for v in self.vendedores if v["_data_admissao"] <= ref],
            "clientes": [self._publico(cl) for cl in self.clientes[:n_clientes]],
        }

    def cadastros_alterados(self, dia: date) -> dict[str, list[dict]]:
        """Somente os cadastros criados ou alterados em `dia` (carga incremental)."""
        rng = self._rng("delta", dia.isoformat())
        alterado_em = _ts(dia, 18, 30)

        if _ultimo_reajuste(dia) == dia:
            produtos = [self._registro_produto(p, dia) for p in self.produtos if p["_data_cadastro"] <= dia]
        else:
            produtos = [self._registro_produto(p, dia) for p in self.produtos if p["_data_cadastro"] == dia]
            # Renegociação de custo com o fornecedor em alguns produtos já existentes.
            existentes = [p for p in self.produtos if p["_data_cadastro"] < dia]
            for produto in rng.sample(existentes, 3):
                registro = self._registro_produto(produto, dia, alterado_em)
                registro["preco_custo"] = round(registro["preco_custo"] * rng.uniform(0.95, 1.05), 2)
                produtos.append(registro)

        n_antes = bisect.bisect_left(self._datas_cadastro_clientes, dia)
        n_ate_hoje = bisect.bisect_right(self._datas_cadastro_clientes, dia)
        clientes = [self._publico(cl) for cl in self.clientes[n_antes:n_ate_hoje]]
        for cliente in rng.sample(self.clientes[:n_antes], 12):
            registro = self._publico(cliente)
            registro["telefone"] = f"(19) 9{rng.randrange(10_000):04d}-{rng.randrange(10_000):04d}"
            registro["cidade"] = rng.choices(*c.CIDADES_CLIENTES)[0]
            registro["atualizado_em"] = alterado_em
            clientes.append(registro)

        return {
            "filiais": [self._publico(f) for f in self.filiais if f["_data_abertura"] == dia],
            "produtos": produtos,
            "vendedores": [self._publico(v) for v in self.vendedores if v["_data_admissao"] == dia],
            "clientes": clientes,
        }

    # ------------------------------------------------------------------
    # Movimento
    # ------------------------------------------------------------------

    def _quantidade_vendas(self, dia: date, rng: Random) -> int:
        crescimento = 1 + 0.08 * (dia - c.DATA_BASE).days / 365
        fator = c.FATOR_DIA_SEMANA[dia.weekday()] * c.FATOR_MES[dia.month] * crescimento
        return max(1, round(self.vendas_dia * fator * rng.uniform(0.92, 1.08)))

    def _sortear_canal(self, dia: date, rng: Random) -> str:
        # O e-commerce ganha participação ao longo do tempo, tirando da loja física.
        anos = max(0.0, (dia - c.DATA_BASE).days / 365)
        ecommerce = min(22.0, 9 + 2.5 * anos)
        canais = [c.CANAL_LOJA, c.CANAL_ECOMMERCE, c.CANAL_DELIVERY, c.CANAL_CONVENIO]
        return rng.choices(canais, [82 - ecommerce, ecommerce, 12, 6])[0]

    def vendas_do_dia(self, dia: date, sujeira: bool = True) -> tuple[list[dict], list[dict], list[dict]]:
        """Retorna (vendas, itens_venda, pagamentos) do dia."""
        rng = self._rng("vendas", dia.isoformat())
        fator_preco = fator_reajuste(dia)
        pesos = self._pesos_acumulados_mes[dia.month]
        filiais_abertas = [f for f in self.filiais if f["_data_abertura"] <= dia]
        pesos_filiais = [f["_peso"] for f in filiais_abertas]
        n_clientes = bisect.bisect_right(self._datas_cadastro_clientes, dia)
        extraido_em = _ts(dia + timedelta(days=1), 2)
        prefixo_id = int(dia.strftime("%Y%m%d")) * 100_000

        vendas, itens, pagamentos = [], [], []
        for seq in range(1, self._quantidade_vendas(dia, rng) + 1):
            id_venda = prefixo_id + seq
            canal = self._sortear_canal(dia, rng)
            online = canal == c.CANAL_ECOMMERCE
            filial = filiais_abertas[0] if online else rng.choices(filiais_abertas, pesos_filiais)[0]
            hora = rng.randrange(24) if online else rng.choices(_HORAS_LOJA, _PESOS_HORAS_LOJA)[0]

            cliente = None
            if canal != c.CANAL_LOJA or rng.random() < 0.45:
                cliente = self.clientes[int(n_clientes * rng.random() ** 1.3)]
            fidelidade = cliente is not None and cliente["programa_fidelidade"] == "S"

            vendedor = None
            if not online:
                equipe = [v for v in self._vendedores_por_filial[filial["id_filial"]] if v["_data_admissao"] <= dia]
                vendedor = rng.choice(equipe) if equipe else None

            escolhidos: dict[int, dict] = {}
            for produto in rng.choices(
                self.produtos, cum_weights=pesos, k=rng.choices([1, 2, 3, 4, 5, 6], [34, 28, 18, 10, 6, 4])[0]
            ):
                # Controlados exigem retenção de receita e não são vendidos online.
                if produto["_data_cadastro"] <= dia and not (online and produto["controlado"]):
                    escolhidos[produto["id_produto"]] = produto
            if not escolhidos:
                continue

            bruto_venda = desconto_venda = 0
            for numero_item, produto in enumerate(escolhidos.values(), start=1):
                quantidade = rng.choices([1, 2, 3], [80, 15, 5])[0]
                preco = round(produto["_preco_base"] * fator_preco)
                custo = round(produto["_custo_base"] * fator_preco)
                percentual = rng.choice([0, 0, 5, 10, 15, 20]) if produto["tipo_produto"] == "Genérico" else 0
                percentual += rng.choice([0, 5, 5, 10]) if fidelidade else 0
                percentual += 10 if canal == c.CANAL_CONVENIO else 0
                bruto = preco * quantidade
                desconto = round(bruto * min(percentual, 35) / 100)
                bruto_venda += bruto
                desconto_venda += desconto
                itens.append(
                    {
                        "id_venda": id_venda,
                        "numero_item": numero_item,
                        "id_produto": produto["id_produto"],
                        "quantidade": quantidade,
                        "preco_unitario": _reais(preco),
                        "custo_unitario": _reais(custo),
                        "valor_desconto": _reais(desconto),
                        "valor_total_item": _reais(bruto - desconto),
                        "extraido_em": extraido_em,
                    }
                )

            total = bruto_venda - desconto_venda
            cancelada = rng.random() < 0.015
            vendas.append(
                {
                    "id_venda": id_venda,
                    "numero_cupom": f"{filial['id_filial']:03d}-{id_venda % 10**11:011d}",
                    "data_hora_venda": _ts(dia, hora, rng.randrange(60), rng.randrange(60)),
                    "id_filial": filial["id_filial"],
                    "id_cliente": cliente["id_cliente"] if cliente else None,
                    "id_vendedor": vendedor["id_vendedor"] if vendedor else None,
                    "canal": canal,
                    "status": STATUS_CANCELADA if cancelada else STATUS_CONCLUIDA,
                    "valor_bruto": _reais(bruto_venda),
                    "valor_desconto": _reais(desconto_venda),
                    "valor_total": _reais(total),
                    "extraido_em": extraido_em,
                }
            )
            if cancelada:
                continue

            formas, pesos_formas = c.PAGAMENTO_POR_CANAL[canal]
            dividir = len(formas) > 1 and total > 5000 and rng.random() < 0.04
            partes = [total // 2, total - total // 2] if dividir else [total]
            for seq_pagamento, (forma, valor) in enumerate(
                zip(
                    rng.sample(formas, len(partes)) if dividir else rng.choices(formas, pesos_formas),
                    partes,
                    strict=True,
                ),
                start=1,
            ):
                cartao = forma in (c.PAG_CREDITO, c.PAG_DEBITO)
                parcelas = rng.randint(1, 6) if forma == c.PAG_CREDITO and valor >= 10_000 else 1
                pagamentos.append(
                    {
                        "id_pagamento": id_venda * 10 + seq_pagamento,
                        "id_venda": id_venda,
                        "forma_pagamento": forma,
                        "bandeira": rng.choice(c.BANDEIRAS) if cartao else None,
                        "parcelas": parcelas,
                        "valor_pago": _reais(valor),
                        "extraido_em": extraido_em,
                    }
                )

        if sujeira:
            self._sujar_movimento(rng, vendas, itens, pagamentos)
        return vendas, itens, pagamentos

    @staticmethod
    def _sujar_movimento(rng: Random, vendas: list[dict], itens: list[dict], pagamentos: list[dict]) -> None:
        """Imita os defeitos típicos de uma extração de ERP. Altera as listas no lugar."""
        for venda in vendas:
            sorteio = rng.random()
            if sorteio < 0.003:
                venda["data_hora_venda"] = datetime.fromisoformat(venda["data_hora_venda"]).strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
            elif sorteio < 0.0035:
                venda["data_hora_venda"] = "0000-00-00T00:00:00"
            if rng.random() < 0.01:
                venda["canal"] = rng.choice([f"  {venda['canal']} ", venda["canal"].upper(), venda["canal"].lower()])
        for item in itens:
            sorteio = rng.random()
            if sorteio < 0.001:
                item["quantidade"] = rng.choice([0, -1])
            elif sorteio < 0.002:
                item["id_produto"] = None
            elif sorteio < 0.0025:
                item["id_venda"] += 90_000  # item órfão: a venda não existe
        for pagamento in pagamentos:
            if rng.random() < 0.0005:
                pagamento["valor_pago"] = None
        for registros, taxa in ((vendas, 0.005), (itens, 0.005), (pagamentos, 0.003)):
            registros.extend([dict(r) for r in registros if rng.random() < taxa])

    def estoque_do_dia(self, dia: date) -> list[dict]:
        """Posição de estoque por filial, produto e lote ao fim de `dia`.

        É uma fotografia plausível, não um saldo reconciliado com as vendas.
        """
        rng = self._rng("estoque", dia.isoformat())
        fator = fator_reajuste(dia)
        extraido_em = _ts(dia + timedelta(days=1), 2)
        posicoes = []
        for filial in self.filiais:
            if filial["_data_abertura"] > dia:
                continue
            for produto in self.produtos:
                if produto["_data_cadastro"] > dia:
                    continue
                # O sortimento de cada filial é estável entre os dias.
                if self._rng("mix", filial["id_filial"], produto["id_produto"]).random() > 0.6:
                    continue
                for n_lote in range(rng.choices([1, 2], [65, 35])[0]):
                    validade = dia + timedelta(days=round(rng.triangular(-15, 720, 300)))
                    posicoes.append(
                        {
                            "data_posicao": dia.isoformat(),
                            "id_filial": filial["id_filial"],
                            "id_produto": produto["id_produto"],
                            "lote": f"L{validade:%y%m}{produto['id_produto'] % 1000:03d}{n_lote}",
                            "data_validade": validade.isoformat(),
                            "quantidade_disponivel": rng.randint(0, 120),
                            "custo_unitario": _reais(round(produto["_custo_base"] * fator)),
                            "extraido_em": extraido_em,
                        }
                    )
        return posicoes


def sujar_cadastro(rng: Random, registros: list[dict], campos_texto: list[str]) -> list[dict]:
    """Devolve cópia dos cadastros com espaços sobrando, UF em minúsculas, vazios e duplicatas."""
    sujos = []
    for registro in registros:
        registro = dict(registro)
        if rng.random() < 0.02:
            campo = rng.choice(campos_texto)
            if campo == "uf":
                registro[campo] = registro[campo].lower()
            elif registro.get(campo):
                registro[campo] = rng.choice([f"  {registro[campo]} ", registro[campo].replace(" ", "  ")])
        if "email" in registro and rng.random() < 0.01:
            registro["email"] = None
        sujos.append(registro)
        if rng.random() < 0.002:
            sujos.append(dict(registro))
    return sujos
