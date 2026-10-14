"""Catálogo do jogo: cartas, raridades, baús, recompensas e regras de níveis.

Só dados. As regras que usam esses dados ficam em progresso.py.
"""

RARIDADES = {
    "comum": {"nome": "Comum", "cor": "#9aa5b1", "peso": 70},
    "rara": {"nome": "Rara", "cor": "#3b82f6", "peso": 22},
    "epica": {"nome": "Épica", "cor": "#a855f7", "peso": 6.5},
    "lendaria": {"nome": "Lendária", "cor": "#f5b81b", "peso": 1.2},
    # Acima da lendária: só os temas mais elaborados (fonte, arte e animações próprias).
    "mitica": {"nome": "Mítica", "cor": "#ff4d6d", "peso": 0.3},
}
ORDEM_RARIDADE = ["comum", "rara", "epica", "lendaria", "mitica"]

TIPOS = {
    "tema": "Tema",
    "pet": "Pet",
    "acessorio": "Acessório do pet",
    "moldura": "Moldura dos avatares",
    "som": "Som de conexão",
}

# Onde cada acessório encaixa em cada pet (linhas do desenho 16x16).
# topo = linha de cima da cabeça, olhos = linha dos olhos, pescoco = linha do pescoço.
ENCAIXE_PET = {
    "slime": {"topo": 0, "olhos": 6, "pescoco": 10},
    "fantasma": {"topo": 0, "olhos": 5, "pescoco": 9},
    "pintinho": {"topo": 2, "olhos": 5, "pescoco": 9},
    "gato": {"topo": 3, "olhos": 5, "pescoco": 10},
    "robo": {"topo": 3, "olhos": 6, "pescoco": 11},
    "dragao": {"topo": 2, "olhos": 4, "pescoco": 9},
    "pinscher": {"topo": 5, "olhos": 7, "pescoco": 11},
    "corgi": {"topo": 4, "olhos": 7, "pescoco": 12},
    "salsicha": {"topo": 4, "olhos": 6, "pescoco": 9},
    "passarinho": {"topo": 2, "olhos": 4, "pescoco": 8},
    "pikachu": {"topo": 4, "olhos": 7, "pescoco": 11},
    "eevee": {"topo": 4, "olhos": 7, "pescoco": 11},
    "jigglypuff": {"topo": 0, "olhos": 6, "pescoco": 11},
}
# Linha do desenho do acessório que encosta no ponto de encaixe.
ENCAIXE_ACESSORIO = {
    "laco": ("topo", 5), "bone": ("topo", 5), "mago": ("topo", 6), "coroa": ("topo", 6),
    "oculos": ("olhos", 5), "cachecol": ("pescoco", 5),
}


def deslocamento_acessorio(especie, acessorio):
    """Quantas linhas (no desenho de 16 px) o acessório fica abaixo do topo do pet."""
    ponto, linha = ENCAIXE_ACESSORIO[acessorio]
    ajuste = 1 if ponto == "topo" else 0  # chapéu "senta" uma linha para dentro da cabeça
    return ENCAIXE_PET[especie][ponto] - linha + ajuste


def _c(cid, tipo, nome, raridade, descricao, arte=None, **extra):
    return {"id": cid, "tipo": tipo, "nome": nome, "raridade": raridade,
            "descricao": descricao, "arte": arte, **extra}


CARTAS = [
    # temas (o "alvo" é a chave do tema em temas.py)
    _c("tema-padrao", "tema", "Padrão", "comum", "Segue o tema do sistema.", alvo="padrao"),
    _c("tema-grafite", "tema", "Grafite", "comum", "Escuro, sóbrio e sem distrações.", alvo="grafite"),
    _c("tema-claro", "tema", "Claro", "comum", "Limpo e luminoso.", alvo="claro"),
    _c("tema-oceano", "tema", "Oceano", "rara", "Azul profundo.", alvo="oceano"),
    _c("tema-terminal", "tema", "Terminal", "epica",
       "Fósforo verde, linhas de varredura e cursor piscando.", alvo="terminal"),
    _c("tema-vidro", "tema", "Vidro líquido", "epica", "Transparente com desfoque, estilo Apple.",
       alvo="vidro"),
    _c("tema-espaco", "tema", "Espaço", "lendaria",
       "Estrelas piscando, nebulosas, planeta e foguete, com fonte espacial.",
       "espaco/planeta.svg", alvo="espaco"),
    _c("tema-neon", "tema", "Neon 80s", "lendaria",
       "Sol retrô, montanhas e grade neon, com fonte dos anos 80.", "neon/sol.svg", alvo="neon"),
    _c("tema-mar", "tema", "Alto-mar", "lendaria",
       "O veleiro do NaView ao pôr do sol: farol piscando, gaivotas e ondas.",
       "mar/veleiro.svg", alvo="mar"),
    _c("tema-pixel", "tema", "Aventura Pixel", "mitica",
       "Monstrinhos animados, grama, nuvens e fonte de videogame.", "pixel/bola.svg", alvo="pixel"),
    _c("tema-hq", "tema", "Heróis HQ", "mitica",
       "Quadrinhos: retícula, explosões POW! e ZAP!, cidade e fonte de gibi.",
       "hq/emblema.svg", alvo="hq"),
    # pets (espécies)
    _c("pet-slime", "pet", "Slime", "comum", "Gosmento e muito carinhoso.", "pets/slime.svg", alvo="slime"),
    _c("pet-pintinho", "pet", "Pintinho", "comum", "Piu! Acorda cedo todo dia.", "pets/pintinho.svg",
       alvo="pintinho"),
    _c("pet-fantasma", "pet", "Fantasminha", "rara", "Assusta os bugs dos clientes.", "pets/fantasma.svg",
       alvo="fantasma"),
    _c("pet-gato", "pet", "Gatinho", "rara", "Dorme em cima do teclado.", "pets/gato.svg", alvo="gato"),
    _c("pet-robo", "pet", "Robô", "epica", "Bip bop. Reinicia o roteador por diversão.", "pets/robo.svg",
       alvo="robo"),
    _c("pet-dragao", "pet", "Dragãozinho", "lendaria", "Guarda as senhas num tesouro.", "pets/dragao.svg",
       alvo="dragao"),
    _c("pet-passarinho", "pet", "Passarinho", "comum", "Canta bom-dia para cada cliente.",
       "pets/passarinho.svg", alvo="passarinho"),
    _c("pet-pinscher", "pet", "Fredinho", "comum",
       "Pinscher caramelo: pequeno no tamanho, gigante na bravura.", "pets/pinscher.svg", alvo="pinscher"),
    _c("pet-salsicha", "pet", "Ronaldo", "rara", "Salsicha comprido o bastante para alcançar o cabo de rede.",
       "pets/salsicha.svg", alvo="salsicha"),
    _c("pet-corgi", "pet", "Corgi", "rara", "Patinhas curtas, coração enorme.", "pets/corgi.svg",
       alvo="corgi"),
    _c("pet-jigglypuff", "pet", "Jigglypuff", "epica", "Canta até o problema dormir.",
       "pets/jigglypuff.svg", alvo="jigglypuff"),
    _c("pet-eevee", "pet", "Eevee", "epica", "Pode evoluir para qualquer coisa. Até técnico.",
       "pets/eevee.svg", alvo="eevee"),
    _c("pet-pikachu", "pet", "Pikachu", "lendaria", "Pika! Reinicia o servidor no choque.",
       "pets/pikachu.svg", alvo="pikachu"),
    # acessórios
    _c("acc-laco", "acessorio", "Laço", "comum", "Um charme.", "acessorios/laco.svg", alvo="laco"),
    _c("acc-bone", "acessorio", "Boné", "comum", "Pronto para a visita técnica.", "acessorios/bone.svg",
       alvo="bone"),
    _c("acc-oculos", "acessorio", "Óculos escuros", "rara", "Estilo de quem resolve tudo.",
       "acessorios/oculos.svg", alvo="oculos"),
    _c("acc-cachecol", "acessorio", "Cachecol", "rara", "Para o ar-condicionado do escritório.",
       "acessorios/cachecol.svg", alvo="cachecol"),
    _c("acc-mago", "acessorio", "Chapéu de mago", "epica", "Para feitiços de suporte remoto.",
       "acessorios/mago.svg", alvo="mago"),
    _c("acc-coroa", "acessorio", "Coroa", "lendaria", "Majestade do atendimento.", "acessorios/coroa.svg",
       alvo="coroa"),
    # molduras dos avatares de contato
    _c("mold-simples", "moldura", "Anel simples", "comum", "Um anel discreto em volta dos avatares.",
       alvo="simples"),
    _c("mold-pontilhada", "moldura", "Pontilhada", "comum", "Borda tracejada.", alvo="pontilhada"),
    _c("mold-dupla", "moldura", "Anel duplo", "rara", "Dois anéis coloridos.", alvo="dupla"),
    _c("mold-neon", "moldura", "Neon", "epica", "Brilho neon em volta dos avatares.", alvo="neon"),
    _c("mold-dourada", "moldura", "Dourada", "lendaria", "Ouro puro em cada contato.", alvo="dourada"),
    # sons ao conectar
    _c("som-bip", "som", "Bip 8 bits", "comum", "Bip de videogame antigo ao conectar.", alvo="bip"),
    _c("som-moeda", "som", "Moedinha", "rara", "Plim! Uma moeda a cada conexão.", alvo="moeda"),
    _c("som-ding", "som", "Sino", "epica", "Um sino suave e elegante.", alvo="ding"),
    _c("som-fanfarra", "som", "Fanfarra", "lendaria", "Entrada triunfal em cada cliente.", alvo="fanfarra"),
]
CARTAS_POR_ID = {c["id"]: c for c in CARTAS}

# Começa com isso (o tema atual do usuário também é dado, para ninguém perder o que já usa).
INICIAIS = ["tema-padrao", "tema-grafite", "tema-claro", "mold-simples"]

# Cópias para subir de nível (índice = nível atual - 1) e custo em moedas.
NIVEL_MAX = 5
COPIAS_POR_NIVEL = [2, 4, 8, 16]
MOEDAS_POR_NIVEL = [20, 50, 120, 300]
XP_POR_NIVEL = [10, 25, 60, 150]

BAUS = {
    "madeira": {"nome": "Baú de Madeira", "minutos": 15, "cartas": 1, "moedas": (10, 20),
                "petiscos": (0, 1), "minimo": None},
    "prata": {"nome": "Baú de Prata", "minutos": 60, "cartas": 2, "moedas": (25, 45),
              "petiscos": (1, 2), "minimo": None},
    "ouro": {"nome": "Baú de Ouro", "minutos": 180, "cartas": 3, "moedas": (60, 100),
             "petiscos": (1, 3), "minimo": "rara"},
    "magico": {"nome": "Baú Mágico", "minutos": 480, "cartas": 5, "moedas": (150, 250),
               "petiscos": (2, 4), "minimo": "epica"},
    "lendario": {"nome": "Baú Lendário", "minutos": 0, "cartas": 3, "moedas": (100, 150),
                 "petiscos": (2, 3), "minimo": "lendaria"},
}
# Chance de cada baú de trabalho (ganho a cada ATENDIMENTOS_POR_BAU atendimentos).
SORTEIO_BAU_TRABALHO = {"madeira": 50, "prata": 35, "ouro": 12, "magico": 3}

ESPACOS_BAU = 4
ATENDIMENTOS_POR_BAU = 10  # ritmo lento de propósito: a demanda de atendimentos é alta
ATENDIMENTO_MINIMO_S = 180  # sessão mais curta que isso não conta (evita abrir/fechar à toa)
BAU_GRATIS_HORAS = 8
BAU_GRATIS_MAX = 1
GARANTIA_LENDARIA = 40  # baús seguidos sem lendária (ou mítica) -> uma carta vira lendária
MOEDAS_ATENDIMENTO = 3
XP_ATENDIMENTO = 10

# Calendário de 7 dias da recompensa diária (repete depois do 7º).
SEQUENCIA = [
    {"moedas": 10},
    {"petiscos": 1},
    {"moedas": 20},
    {"bau": "madeira"},
    {"moedas": 30, "petiscos": 2},
    {"bau": "madeira"},
    {"bau": "prata"},
]

# Loja: oferta do dia (3 cartas) e petiscos.
PRECO_CARTA = {"comum": 40, "rara": 150, "epica": 600, "lendaria": 3000, "mitica": 8000}
PRECO_PETISCO = 15
OFERTAS_POR_DIA = 3

# XP do perfil para cada nível: nível n exige 100 * n XP (acumulado cresce devagar).
def xp_para_nivel(nivel):
    return 100 * nivel



# ---- pet ----
PET_ESTAGIOS = [  # (xp mínimo, nome, tamanho relativo)
    (0, "Bebê", 0.75),
    (100, "Jovem", 0.9),
    (400, "Adulto", 1.0),
]
PET_QUEDA_POR_HORA = {"fome": 5, "alegria": 4, "energia": 3}
PET_SONO_POR_HORA = 12  # energia recuperada por hora dormindo (e com o app fechado)
PET_SONECA_MIN = 60
PET_ACOES = {
    "alimentar": {"fome": 35, "alegria": 5, "xp": 5},
    "brincar": {"alegria": 25, "energia": -12, "fome": -5, "xp": 5},
}
PET_BRINCAR_ESPERA_MIN = 20
