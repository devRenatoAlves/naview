"""Catálogo do jogo: cartas, raridades, baús, recompensas e regras de níveis.

Só dados. As regras que usam esses dados ficam em progresso.py.
"""

from pathlib import Path

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

# Pets em pixel art num quadro de PET_LADO x PET_LADO (1 unidade = 1 pixel do desenho). Acima dele
# ficam PET_ACIMA linhas livres para os chapéus: o pet com acessório ocupa PET_LADO x (PET_LADO + PET_ACIMA).
PET_LADO = 64
ARTE_PETS = Path(__file__).resolve().parent.parent / "arte" / "pets"
PET_ACIMA = 16
# Pets desenhados mais altos que o quadro de PET_LADO: linhas a mais em cima (o desenho fica
# encostado embaixo e invade o espaço dos chapéus). Vem de ferramentas/pixel_vetor.no_quadro e de
# ferramentas/importar_pets.py.
ALTURA_EXTRA = {"pinscher": 7, "galinha": 2, "dragao": 50}
# O dragão é bem mais alto que os outros: o espaço de cima do quadro dele cabe o corpo extra e o chapéu.
ACIMA_PET = {"dragao": 64}
# Tamanho do pet na página do jogo, em relação aos outros (o dragão tem o dobro dos pixels).
ESCALA_PAGINA = {"dragao": 0.5}
# Pets próprios com outras caras desenhadas (arte/pets/<especie>_<cara>.svg): pisca (olhos fechados,
# também no sono), feliz e triste. Os Pokémon e os pets sem olhos de grade ficam de fora.
PETS_COM_EXPRESSAO = ["pinscher", "salsicha"]
EXPRESSOES = ["pisca", "feliz", "triste"]
# Pets que vieram como GIF: arte/pets/<pet>.svg é o quadro 0 e arte/pets/<pet>_q<i>.svg os outros.
# Para cada quadro, quanto a cabeça se mexe (x, y) em relação ao quadro 0, para os acessórios acompanharem.
QUADROS = {
    "gato": [(0, 0), (0, -1), (0, -1), (0, 0), (0, 0), (0, -1), (0, 0), (0, 0)],
    "jonatas": [(0, 0), (0, 1), (0, 2), (0, 0), (0, 0), (0, 1), (0, 2), (0, 0)],
    "astronauta": [(0, 0), (0, 0), (0, 0), (0, -1), (0, 0), (0, 0), (0, 0), (0, -1)],
    "dragao": [(0, 0), (-1, 1), (0, 3), (-1, 4), (-1, 4), (-2, 2), (-1, 1), (0, 0)],
}
QUADRO_MS = 130  # tempo de cada quadro dos GIFs

# Pontos de encaixe de cada pet, (x, y) no quadro do pet: topo = alto da cabeça (onde o chapéu
# assenta), olhos = meio entre os olhos, pescoco = meio do pescoço.
ENCAIXE_PET = {
    "slime": {"topo": (31, 30), "olhos": (31, 41), "pescoco": (31, 50)},
    "galinha": {"topo": (17, 8), "olhos": (16, 12), "pescoco": (21, 24)},
    "gato": {"topo": (26, 20), "olhos": (22, 32), "pescoco": (24, 40)},
    "jonatas": {"topo": (32, 9), "olhos": (31, 24), "pescoco": (31, 33)},
    "astronauta": {"topo": (32, 13), "olhos": (32, 22), "pescoco": (32, 36)},
    "dragao": {"topo": (26, -36), "olhos": (21, -26), "pescoco": (38, -6)},
    "pinscher": {"topo": (20, 9), "olhos": (18, 21), "pescoco": (25, 32)},
    "salsicha": {"topo": (25, 20), "olhos": (25, 25), "pescoco": (24, 37)},
    "pikachu": {"topo": (23, 29), "olhos": (21, 33), "pescoco": (24, 45)},
    "eevee": {"topo": (24, 33), "olhos": (22, 40), "pescoco": (24, 46)},
    "jigglypuff": {"topo": (32, 32), "olhos": (31, 44), "pescoco": (31, 52)},
    "gengar": {"topo": (30, 16), "olhos": (26, 34), "pescoco": (28, 48)},
}
# Cada acessório: (ponto do pet, âncora x, âncora y, largura, altura). A âncora é o pixel do
# desenho do acessório que encosta no ponto do pet.
ENCAIXE_ACESSORIO = {
    "laco": ("topo", 7, 9, 15, 11), "bone": ("topo", 11, 10, 26, 13),
    "mago": ("topo", 13, 17, 27, 20), "coroa": ("topo", 9, 12, 19, 13),
    "cachecol": ("pescoco", 15, 2, 30, 15),
}


# Ajuste de um acessório num pet específico (quando o encaixe padrão não serve, como nos pets de lado):
# (pet, acessório) -> (arquivo do desenho, (x, y) do ponto no quadro do pet, âncora x, âncora y, largura, altura).
# "arquivo" é uma variante de arte/acessorios/ (cachecol_estreito).
AJUSTE_ACESSORIO = {
    # Fredinho: cabeça de frente com olhos bem afastados (15 px), pescoço curto sob o queixo.
    ("pinscher", "cachecol"): ("cachecol_estreito", (25, 32), 9, 2, 19, 15),
    # Ronaldo: de lado, olhando para a esquerda; pescoço entre a cabeça e o peito.
    ("salsicha", "cachecol"): ("cachecol_estreito", (24, 37), 9, 2, 19, 15),
    # Serpente de gelo: de perfil, olhando para a esquerda; o chapéu assenta na crina.
    ("dragao", "cachecol"): ("cachecol_estreito", (38, -6), 9, 2, 19, 15),
    # Galinha: de lado, olhando para a esquerda.
    ("galinha", "cachecol"): ("cachecol_estreito", (21, 24), 9, 2, 19, 15),
    # Pikachu e Eevee: corpo de ~22 px; o cachecol de 30 px passava 4 px para cada lado.
    ("pikachu", "cachecol"): ("cachecol_estreito", (24, 45), 9, 2, 19, 15),
    ("eevee", "cachecol"): ("cachecol_estreito", (24, 46), 9, 2, 19, 15),
}


def acima_de(especie):
    """Linhas livres em cima do quadro do pet (para chapéus e para o corpo que passa do quadro)."""
    return ACIMA_PET.get(especie, PET_ACIMA)


def encaixe_acessorio(especie, acessorio):
    """Posição, tamanho e arquivo do acessório no quadro do pet com o espaço de cima (x, y, w, h, arquivo)."""
    ponto, ax, ay, w, h = ENCAIXE_ACESSORIO[acessorio]
    arquivo = acessorio
    acima = acima_de(especie)
    if (especie, acessorio) in AJUSTE_ACESSORIO:
        arquivo, (px, py), ax, ay, w, h = AJUSTE_ACESSORIO[(especie, acessorio)]
    else:
        px, py = ENCAIXE_PET[especie][ponto]
    return {"x": px - ax, "y": acima + py - ay, "w": w, "h": h, "arquivo": arquivo}


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
    _c("tema-manga", "tema", "Mangá Noir", "mitica",
       "Preto e branco de mangá: retrato em tinta e ícone próprio.", "manga/icone.png", alvo="manga"),
    _c("tema-hq", "tema", "Heróis HQ", "mitica",
       "Quadrinhos: retícula, explosões POW! e ZAP!, cidade e fonte de gibi.",
       "hq/emblema.svg", alvo="hq"),
    # pets (espécies)
    _c("pet-slime", "pet", "Slime", "comum", "Gosmento e muito carinhoso.", "pets/slime.svg", alvo="slime"),
    _c("pet-galinha", "pet", "Galinha", "comum", "Cocoricó! Bota ovo e acorda a equipe cedo.",
       "pets/galinha.svg", alvo="galinha"),
    _c("pet-pinscher", "pet", "Fredinho", "lendaria",
       "Pinscher caramelo: pequeno no tamanho, gigante na bravura.", "pets/pinscher.svg", alvo="pinscher"),
    _c("pet-gato", "pet", "Gatinho preto", "rara", "Dorme em cima do teclado.", "pets/gato.svg", alvo="gato"),
    _c("pet-jonatas", "pet", "Jonatas", "epica", "Sempre com pressa para o próximo atendimento.",
       "pets/jonatas.svg", alvo="jonatas"),
    _c("pet-salsicha", "pet", "Ronaldo", "rara", "Salsicha comprido o bastante para alcançar o cabo de rede.",
       "pets/salsicha.svg", alvo="salsicha"),
    _c("pet-astronauta", "pet", "Astronauta", "epica", "Suporte remoto de verdade: atende de órbita.",
       "pets/astronauta.svg", alvo="astronauta"),
    _c("pet-jigglypuff", "pet", "Jigglypuff", "epica", "Canta até o problema dormir.",
       "pets/jigglypuff.svg", alvo="jigglypuff"),
    _c("pet-eevee", "pet", "Eevee", "epica", "Pode evoluir para qualquer coisa. Até técnico.",
       "pets/eevee.svg", alvo="eevee"),
    _c("pet-dragao", "pet", "Serpente de gelo", "lendaria", "Congela os bugs antes que eles se espalhem.",
       "pets/dragao.svg", alvo="dragao"),
    _c("pet-pikachu", "pet", "Pikachu", "lendaria", "Pika! Reinicia o servidor no choque.",
       "pets/pikachu.svg", alvo="pikachu"),
    _c("pet-gengar", "pet", "Gengar", "lendaria", "Sorri no escuro e assombra os bugs.",
       "pets/gengar.svg", alvo="gengar"),
    # acessórios
    _c("acc-laco", "acessorio", "Laço", "comum", "Um charme.", "acessorios/laco.svg", alvo="laco"),
    _c("acc-bone", "acessorio", "Boné", "comum", "Pronto para a visita técnica.", "acessorios/bone.svg",
       alvo="bone"),
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
# Anti-trapaça: o mesmo ID conta no máximo N vezes dentro de uma janela de H horas (deslizante).
ATENDIMENTOS_MAX_POR_ID = 2
ATENDIMENTOS_JANELA_H = 24
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
