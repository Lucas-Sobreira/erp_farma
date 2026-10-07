"""Listas de referência usadas pelo gerador de dados sintéticos.

Tudo aqui é fictício: laboratórios, marcas, filiais e pessoas não correspondem a
empresas ou indivíduos reais. Os princípios ativos são reais apenas para que as
categorias e as regras de receita façam sentido para quem é do ramo.
"""

from datetime import date

# Marco zero do histórico: preços-base valem nesta data e os reajustes partem dela.
DATA_BASE = date(2023, 1, 1)

# Reajuste aplicado em 1º de abril de cada ano (valores ilustrativos).
REAJUSTES_ANUAIS = {2023: 0.056, 2024: 0.045, 2025: 0.051, 2026: 0.043, 2027: 0.040, 2028: 0.040}

CANAL_LOJA = "Loja Física"
CANAL_ECOMMERCE = "E-commerce"
CANAL_DELIVERY = "Delivery"
CANAL_CONVENIO = "Convênio"

PAG_PIX = "PIX"
PAG_CREDITO = "Cartão de Crédito"
PAG_DEBITO = "Cartão de Débito"
PAG_DINHEIRO = "Dinheiro"
PAG_CONVENIO = "Convênio"

# Formas de pagamento e pesos por canal.
PAGAMENTO_POR_CANAL = {
    CANAL_LOJA: ([PAG_PIX, PAG_CREDITO, PAG_DEBITO, PAG_DINHEIRO], [26, 30, 28, 16]),
    CANAL_ECOMMERCE: ([PAG_PIX, PAG_CREDITO], [45, 55]),
    CANAL_DELIVERY: ([PAG_PIX, PAG_CREDITO, PAG_DEBITO, PAG_DINHEIRO], [40, 32, 18, 10]),
    CANAL_CONVENIO: ([PAG_CONVENIO], [1]),
}

BANDEIRAS = ["Visa", "Mastercard", "Elo", "Hipercard"]

# (nome, cidade, uf, bairro, tipo de loja, data de abertura, peso nas vendas)
# A primeira filial é a matriz e fatura os pedidos do e-commerce.
FILIAIS = [
    ("Matriz Centro", "Campinas", "SP", "Centro", "Rua", date(2012, 3, 12), 1.6),
    ("Cambuí", "Campinas", "SP", "Cambuí", "Rua", date(2015, 8, 3), 1.3),
    ("Shopping Dom Pedro", "Campinas", "SP", "Jardim Santa Genebra", "Shopping", date(2017, 11, 20), 1.2),
    ("Barão Geraldo", "Campinas", "SP", "Barão Geraldo", "Rua", date(2019, 5, 6), 0.9),
    ("Valinhos Centro", "Valinhos", "SP", "Centro", "Rua", date(2018, 2, 19), 0.8),
    ("Vinhedo", "Vinhedo", "SP", "Centro", "Rua", date(2020, 9, 14), 0.7),
    ("Sumaré", "Sumaré", "SP", "Jardim Macarenko", "Rua", date(2023, 6, 5), 0.8),
    ("Hospital Paulínia", "Paulínia", "SP", "Santa Cecília", "Hospitalar", date(2024, 3, 4), 0.6),
]

CIDADES_CLIENTES = (
    ["Campinas", "Valinhos", "Vinhedo", "Sumaré", "Paulínia", "Hortolândia", "Indaiatuba"],
    [52, 10, 7, 11, 6, 9, 5],
)

LABORATORIOS = [
    "Aurora Farmacêutica",
    "Vale Verde Laboratórios",
    "Biosanta",
    "Farmoquímica Paulista",
    "Laboratório Ipê",
    "Medivida",
    "Novacura",
    "Prati Sul",
    "Genfar Brasil",
    "Laboratório Horizonte",
    "Sanavita",
    "Unifarma",
    "Cristal Pharma",
    "Laboratório Tupã",
    "Vitalis",
    "Farmabem Indústria",
]

MARCAS_CONSUMO = [
    "Dermaluz",
    "Bem Cuidar",
    "Florata",
    "Puro Toque",
    "Vida Leve",
    "Solare",
    "Ninar",
    "Fresh Care",
    "Naturalis",
    "Essenza",
]

DISTRIBUIDORAS = [
    "Distribuidora Bandeirantes",
    "Central Farma Distribuição",
    "Logmed Atacado",
    "Distribuidora Anhanguera",
]

CAT_ANALGESICOS = "Analgésicos e Antitérmicos"
CAT_ANTIINFLAMATORIOS = "Anti-inflamatórios"
CAT_ANTIBIOTICOS = "Antibióticos"
CAT_CARDIO = "Cardiovascular"
CAT_DIABETES = "Diabetes"
CAT_GASTRO = "Gastrointestinal"
CAT_ALERGIA = "Antialérgicos"
CAT_GRIPE = "Gripe e Resfriado"
CAT_RESPIRATORIO = "Respiratório"
CAT_SAUDE_MENTAL = "Saúde Mental"
CAT_HORMONIOS = "Hormônios e Anticoncepcionais"
CAT_VITAMINAS = "Vitaminas e Suplementos"
CAT_DERMO = "Dermocosméticos"
CAT_HIGIENE = "Higiene Pessoal"
CAT_INFANTIL = "Infantil"
CAT_CUIDADOS = "Primeiros Socorros e Cuidados"
CAT_CONVENIENCIA = "Conveniência"

TARJA_SEM = "Sem tarja"
TARJA_VERMELHA = "Vermelha"
TARJA_PRETA = "Preta"

# (princípio ativo, categoria, tarja, controlado [receita retida], dosagens,
#  apresentações, preço-base do genérico em R$)
MEDICAMENTOS = [
    ("Dipirona Sódica", CAT_ANALGESICOS, TARJA_SEM, False, ["500mg", "1g"], ["10 comprimidos", "20 comprimidos"], 7.9),
    ("Paracetamol", CAT_ANALGESICOS, TARJA_SEM, False, ["500mg", "750mg"], ["10 comprimidos", "20 comprimidos"], 8.5),
    (
        "Ácido Acetilsalicílico",
        CAT_ANALGESICOS,
        TARJA_SEM,
        False,
        ["100mg", "500mg"],
        ["20 comprimidos", "30 comprimidos"],
        9.9,
    ),
    (
        "Ibuprofeno",
        CAT_ANTIINFLAMATORIOS,
        TARJA_SEM,
        False,
        ["400mg", "600mg"],
        ["10 comprimidos", "20 comprimidos"],
        12.9,
    ),
    ("Nimesulida", CAT_ANTIINFLAMATORIOS, TARJA_VERMELHA, False, ["100mg"], ["12 comprimidos"], 11.5),
    ("Diclofenaco Sódico", CAT_ANTIINFLAMATORIOS, TARJA_VERMELHA, False, ["50mg"], ["20 comprimidos"], 10.9),
    ("Cetoprofeno", CAT_ANTIINFLAMATORIOS, TARJA_VERMELHA, False, ["100mg", "150mg"], ["20 comprimidos"], 24.9),
    ("Naproxeno", CAT_ANTIINFLAMATORIOS, TARJA_VERMELHA, False, ["250mg", "500mg"], ["20 comprimidos"], 22.5),
    ("Amoxicilina", CAT_ANTIBIOTICOS, TARJA_VERMELHA, True, ["500mg", "875mg"], ["14 cápsulas", "21 cápsulas"], 28.9),
    ("Azitromicina", CAT_ANTIBIOTICOS, TARJA_VERMELHA, True, ["500mg"], ["3 comprimidos", "5 comprimidos"], 26.5),
    ("Cefalexina", CAT_ANTIBIOTICOS, TARJA_VERMELHA, True, ["500mg"], ["8 comprimidos", "40 comprimidos"], 24.0),
    ("Ciprofloxacino", CAT_ANTIBIOTICOS, TARJA_VERMELHA, True, ["500mg"], ["7 comprimidos", "14 comprimidos"], 21.9),
    ("Losartana Potássica", CAT_CARDIO, TARJA_VERMELHA, False, ["50mg", "100mg"], ["30 comprimidos"], 14.9),
    ("Enalapril", CAT_CARDIO, TARJA_VERMELHA, False, ["10mg", "20mg"], ["30 comprimidos"], 12.5),
    ("Anlodipino", CAT_CARDIO, TARJA_VERMELHA, False, ["5mg", "10mg"], ["30 comprimidos"], 13.9),
    ("Atenolol", CAT_CARDIO, TARJA_VERMELHA, False, ["25mg", "50mg"], ["30 comprimidos"], 11.9),
    ("Hidroclorotiazida", CAT_CARDIO, TARJA_VERMELHA, False, ["25mg"], ["30 comprimidos"], 8.9),
    ("Sinvastatina", CAT_CARDIO, TARJA_VERMELHA, False, ["20mg", "40mg"], ["30 comprimidos"], 18.9),
    ("Atorvastatina", CAT_CARDIO, TARJA_VERMELHA, False, ["10mg", "20mg"], ["30 comprimidos"], 32.9),
    ("Rosuvastatina", CAT_CARDIO, TARJA_VERMELHA, False, ["10mg", "20mg"], ["30 comprimidos"], 38.5),
    ("Metformina", CAT_DIABETES, TARJA_VERMELHA, False, ["500mg", "850mg"], ["30 comprimidos", "60 comprimidos"], 12.9),
    ("Glibenclamida", CAT_DIABETES, TARJA_VERMELHA, False, ["5mg"], ["30 comprimidos"], 9.5),
    ("Gliclazida", CAT_DIABETES, TARJA_VERMELHA, False, ["30mg", "60mg"], ["30 comprimidos"], 27.9),
    ("Omeprazol", CAT_GASTRO, TARJA_VERMELHA, False, ["20mg", "40mg"], ["28 cápsulas", "56 cápsulas"], 16.9),
    ("Pantoprazol", CAT_GASTRO, TARJA_VERMELHA, False, ["20mg", "40mg"], ["28 comprimidos"], 24.9),
    ("Domperidona", CAT_GASTRO, TARJA_VERMELHA, False, ["10mg"], ["30 comprimidos"], 19.9),
    ("Simeticona", CAT_GASTRO, TARJA_SEM, False, ["75mg/ml", "125mg"], ["frasco 15ml", "10 cápsulas"], 11.9),
    ("Loperamida", CAT_GASTRO, TARJA_SEM, False, ["2mg"], ["12 comprimidos"], 9.9),
    ("Loratadina", CAT_ALERGIA, TARJA_SEM, False, ["10mg"], ["12 comprimidos"], 12.9),
    ("Desloratadina", CAT_ALERGIA, TARJA_VERMELHA, False, ["5mg"], ["10 comprimidos", "30 comprimidos"], 26.9),
    ("Cetirizina", CAT_ALERGIA, TARJA_SEM, False, ["10mg"], ["12 comprimidos"], 15.9),
    ("Dexclorfeniramina", CAT_ALERGIA, TARJA_SEM, False, ["2mg", "0,4mg/ml"], ["20 comprimidos", "frasco 120ml"], 10.9),
    ("Paracetamol + Fenilefrina", CAT_GRIPE, TARJA_SEM, False, ["400mg + 4mg"], ["20 cápsulas", "5 envelopes"], 16.9),
    ("Cloridrato de Nafazolina", CAT_GRIPE, TARJA_SEM, False, ["0,5mg/ml"], ["frasco 30ml"], 9.9),
    ("Guaifenesina", CAT_GRIPE, TARJA_SEM, False, ["13,3mg/ml"], ["frasco 120ml"], 18.9),
    ("Acetilcisteína", CAT_GRIPE, TARJA_SEM, False, ["200mg", "600mg"], ["16 envelopes"], 29.9),
    ("Salbutamol", CAT_RESPIRATORIO, TARJA_VERMELHA, False, ["100mcg"], ["aerossol 200 doses"], 21.9),
    ("Budesonida", CAT_RESPIRATORIO, TARJA_VERMELHA, False, ["32mcg", "64mcg"], ["spray 120 doses"], 34.9),
    ("Montelucaste", CAT_RESPIRATORIO, TARJA_VERMELHA, False, ["5mg", "10mg"], ["30 comprimidos"], 44.9),
    (
        "Prednisona",
        CAT_RESPIRATORIO,
        TARJA_VERMELHA,
        False,
        ["5mg", "20mg"],
        ["10 comprimidos", "20 comprimidos"],
        11.9,
    ),
    ("Sertralina", CAT_SAUDE_MENTAL, TARJA_VERMELHA, True, ["50mg", "100mg"], ["30 comprimidos"], 34.9),
    ("Fluoxetina", CAT_SAUDE_MENTAL, TARJA_VERMELHA, True, ["20mg"], ["30 cápsulas"], 19.9),
    ("Escitalopram", CAT_SAUDE_MENTAL, TARJA_VERMELHA, True, ["10mg", "20mg"], ["30 comprimidos"], 42.9),
    ("Clonazepam", CAT_SAUDE_MENTAL, TARJA_PRETA, True, ["0,5mg", "2mg"], ["30 comprimidos"], 14.9),
    ("Alprazolam", CAT_SAUDE_MENTAL, TARJA_PRETA, True, ["0,5mg", "1mg"], ["30 comprimidos"], 18.9),
    ("Zolpidem", CAT_SAUDE_MENTAL, TARJA_PRETA, True, ["10mg"], ["20 comprimidos", "30 comprimidos"], 29.9),
    ("Levotiroxina", CAT_HORMONIOS, TARJA_VERMELHA, False, ["25mcg", "50mcg", "100mcg"], ["30 comprimidos"], 15.9),
    (
        "Etinilestradiol + Levonorgestrel",
        CAT_HORMONIOS,
        TARJA_VERMELHA,
        False,
        ["0,03mg + 0,15mg"],
        ["21 comprimidos"],
        9.9,
    ),
    (
        "Drospirenona + Etinilestradiol",
        CAT_HORMONIOS,
        TARJA_VERMELHA,
        False,
        ["3mg + 0,03mg"],
        ["21 comprimidos", "63 comprimidos"],
        38.9,
    ),
    (
        "Ácido Ascórbico",
        CAT_VITAMINAS,
        TARJA_SEM,
        False,
        ["500mg", "1g"],
        ["10 comprimidos efervescentes", "30 comprimidos"],
        14.9,
    ),
    ("Colecalciferol", CAT_VITAMINAS, TARJA_SEM, False, ["2.000UI", "7.000UI"], ["30 cápsulas", "8 cápsulas"], 27.9),
    ("Sulfato Ferroso", CAT_VITAMINAS, TARJA_SEM, False, ["40mg"], ["50 comprimidos"], 12.9),
]

# (item, categoria, tamanhos/variações, preço-base em R$)
NAO_MEDICAMENTOS = [
    ("Protetor Solar FPS 50", CAT_DERMO, ["120ml", "200ml"], 49.9),
    ("Protetor Solar Facial FPS 70", CAT_DERMO, ["50g"], 69.9),
    ("Hidratante Corporal", CAT_DERMO, ["200ml", "400ml"], 29.9),
    ("Sabonete Líquido Facial", CAT_DERMO, ["150ml", "300ml"], 39.9),
    ("Água Micelar", CAT_DERMO, ["200ml"], 34.9),
    ("Sérum Vitamina C", CAT_DERMO, ["30ml"], 89.9),
    ("Creme Anti-idade", CAT_DERMO, ["40g"], 119.9),
    ("Shampoo Anticaspa", CAT_DERMO, ["200ml"], 32.9),
    ("Protetor Labial", CAT_DERMO, ["4g"], 14.9),
    ("Creme Dental", CAT_HIGIENE, ["90g", "180g"], 6.9),
    ("Escova Dental", CAT_HIGIENE, ["unidade", "leve 3"], 12.9),
    ("Enxaguante Bucal", CAT_HIGIENE, ["250ml", "500ml"], 18.9),
    ("Fio Dental", CAT_HIGIENE, ["50m", "100m"], 9.9),
    ("Sabonete em Barra", CAT_HIGIENE, ["90g"], 3.9),
    ("Desodorante Aerossol", CAT_HIGIENE, ["150ml"], 16.9),
    ("Shampoo", CAT_HIGIENE, ["350ml"], 19.9),
    ("Condicionador", CAT_HIGIENE, ["350ml"], 21.9),
    ("Absorvente", CAT_HIGIENE, ["8 unidades", "32 unidades"], 8.9),
    ("Papel Higiênico", CAT_HIGIENE, ["4 rolos", "12 rolos"], 9.9),
    ("Fralda Descartável", CAT_INFANTIL, ["P 30 unidades", "M 28 unidades", "G 26 unidades", "XG 24 unidades"], 42.9),
    ("Lenço Umedecido", CAT_INFANTIL, ["48 unidades", "96 unidades"], 11.9),
    ("Pomada para Assadura", CAT_INFANTIL, ["45g", "90g"], 22.9),
    ("Fórmula Infantil", CAT_INFANTIL, ["400g", "800g"], 54.9),
    ("Shampoo Infantil", CAT_INFANTIL, ["200ml"], 17.9),
    ("Mamadeira", CAT_INFANTIL, ["150ml", "260ml"], 29.9),
    ("Curativo Adesivo", CAT_CUIDADOS, ["10 unidades", "40 unidades"], 6.9),
    ("Gaze Estéril", CAT_CUIDADOS, ["10 unidades"], 4.9),
    ("Álcool 70%", CAT_CUIDADOS, ["500ml", "1L"], 8.9),
    ("Álcool em Gel", CAT_CUIDADOS, ["60g", "400g"], 7.9),
    ("Termômetro Digital", CAT_CUIDADOS, ["unidade"], 24.9),
    ("Máscara Descartável", CAT_CUIDADOS, ["10 unidades", "50 unidades"], 9.9),
    ("Soro Fisiológico", CAT_CUIDADOS, ["100ml", "500ml"], 5.9),
    ("Atadura Elástica", CAT_CUIDADOS, ["10cm", "15cm"], 7.9),
    ("Teste de Gravidez", CAT_CUIDADOS, ["unidade"], 13.9),
    ("Repelente", CAT_CUIDADOS, ["100ml", "200ml"], 23.9),
    ("Polivitamínico", CAT_VITAMINAS, ["30 comprimidos", "60 comprimidos"], 39.9),
    ("Ômega 3", CAT_VITAMINAS, ["60 cápsulas", "120 cápsulas"], 59.9),
    ("Colágeno Hidrolisado", CAT_VITAMINAS, ["250g"], 79.9),
    ("Whey Protein", CAT_VITAMINAS, ["450g", "900g"], 109.9),
    ("Barra de Cereal", CAT_CONVENIENCIA, ["unidade", "caixa 12"], 2.9),
    ("Água Mineral", CAT_CONVENIENCIA, ["500ml", "1,5L"], 2.5),
    ("Bala de Goma", CAT_CONVENIENCIA, ["pacote"], 5.9),
    ("Isotônico", CAT_CONVENIENCIA, ["500ml"], 6.9),
    ("Chá em Sachê", CAT_CONVENIENCIA, ["10 sachês"], 7.9),
]

# Fator multiplicador de demanda por categoria e mês (1 = janeiro). Categorias
# fora do dicionário não têm sazonalidade.
_INVERNO = {5: 1.4, 6: 1.9, 7: 2.0, 8: 1.6, 9: 1.2}
SAZONALIDADE = {
    CAT_GRIPE: _INVERNO,
    CAT_RESPIRATORIO: {5: 1.2, 6: 1.5, 7: 1.6, 8: 1.4},
    CAT_ANTIBIOTICOS: {6: 1.3, 7: 1.4, 8: 1.3},
    CAT_ALERGIA: {8: 1.4, 9: 1.7, 10: 1.5, 11: 1.2},
    CAT_DERMO: {12: 1.5, 1: 1.6, 2: 1.4, 6: 0.85, 7: 0.85},
    CAT_VITAMINAS: {1: 1.25, 5: 1.15, 6: 1.25, 7: 1.25},
}

# Peso relativo de cada categoria no mix de itens vendidos.
PESO_CATEGORIA = {
    CAT_ANALGESICOS: 1.8,
    CAT_ANTIINFLAMATORIOS: 1.2,
    CAT_ANTIBIOTICOS: 0.7,
    CAT_CARDIO: 1.5,
    CAT_DIABETES: 0.8,
    CAT_GASTRO: 1.0,
    CAT_ALERGIA: 0.8,
    CAT_GRIPE: 0.9,
    CAT_RESPIRATORIO: 0.5,
    CAT_SAUDE_MENTAL: 0.6,
    CAT_HORMONIOS: 0.7,
    CAT_VITAMINAS: 0.9,
    CAT_DERMO: 0.9,
    CAT_HIGIENE: 1.6,
    CAT_INFANTIL: 0.8,
    CAT_CUIDADOS: 0.7,
    CAT_CONVENIENCIA: 0.9,
}

# Vendas por dia da semana (0 = segunda) e por mês, relativas à média.
FATOR_DIA_SEMANA = [1.05, 1.0, 1.0, 1.02, 1.12, 1.15, 0.66]
FATOR_MES = {1: 0.97, 2: 0.93, 3: 1.0, 4: 0.99, 5: 1.03, 6: 1.07, 7: 1.08, 8: 1.04, 9: 1.0, 10: 0.99, 11: 1.0, 12: 1.06}

NOMES = [
    "Ana", "Maria", "Juliana", "Fernanda", "Patrícia", "Camila", "Aline", "Bruna", "Larissa",
    "Beatriz", "Mariana", "Carla", "Luciana", "Renata", "Vanessa", "Débora", "Simone", "Helena",
    "Sandra", "Rosana", "João", "José", "Carlos", "Paulo", "Lucas", "Pedro", "Marcos", "Rafael",
    "Bruno", "Felipe", "Gustavo", "Rodrigo", "Eduardo", "Thiago", "André", "Ricardo", "Fábio",
    "Leonardo", "Antônio", "Sérgio",
]  # fmt: skip
NOMES_FEMININOS = set(NOMES[:20])

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima",
    "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes",
    "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques",
    "Machado", "Mendes", "Freitas", "Cardoso", "Ramos", "Teixeira", "Araújo", "Pinto", "Correia",
]  # fmt: skip

CARGOS = (["Atendente", "Farmacêutico", "Gerente"], [70, 22, 8])
