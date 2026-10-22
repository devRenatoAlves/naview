"""Pets e acessórios desenhados em pixel art (grade de 48 x 48 para os pets).

Cada desenho é feito de camadas vetoriais (ver pixel_vetor.py). Os Pokémon não estão aqui: usam os
sprites oficiais, baixados por baixar_sprites.py.
"""
import re

from pixel_vetor import Grade, Tela, de_mapa, montar as _montar, sombreado as sb


def montar(*args, **kwargs):
    """pixel_vetor.montar com os olhos que olhos() desenhou desde o último pet."""
    grade = _montar(*args, olhos=tuple(_OLHOS), **kwargs)
    _OLHOS.clear()
    return grade


def pronto(tela, detalhes=()):
    """Fecha um desenho feito com Tela, levando os olhos que olhos() registrou."""
    grade = tela.pronto(detalhes, olhos=tuple(_OLHOS))
    _OLHOS.clear()
    return grade


def espelho_pontos(pontos, eixo=24):
    return [(2 * eixo - x, y) for x, y in pontos]


def espelho_x(d, lado=48):
    """Espelha um caminho simples "M x y L x y Q x y x y ..." na horizontal."""
    partes = re.findall(r"[A-Za-z]|-?[\d.]+", d)
    saida, eixo_x = [], True
    for p in partes:
        if p.isalpha():
            saida.append(p)
            eixo_x = True
            continue
        saida.append(f"{lado - float(p):g}" if eixo_x else p)
        eixo_x = not eixo_x
    return " ".join(saida)


_OLHOS = []  # olhos desenhados no pet atual (montar() leva para o quadro de olhos fechados)


def olhos(x_esq, x_dir, y, cor="#1b1b1b", brilho="#ffffff", alto=5, meia=1):
    """Dois olhos grandes de (2*meia+1) x alto pixels, de cantos arredondados, com brilho duplo: um
    grande no alto à esquerda e um pequeno embaixo à direita. meia=2 dá olhos redondos de 5 pixels."""
    pontos = []
    for cx in (x_esq, x_dir):
        _OLHOS.append((cx, y, alto, meia))
        for dy in range(alto):
            m = meia - 1 if dy in (0, alto - 1) else meia
            pontos += [(cx + dx, y + dy) for dx in range(-m, m + 1)]
    if meia == 1:
        brilhos = [(x - 1, y + k) for x in (x_esq, x_dir) for k in (1, 2)]
    else:
        brilhos = [(x + dx, y + dy) for x in (x_esq, x_dir) for dx, dy in ((-1, 1), (0, 1), (-1, 2))]
    brilhos += [(x + 1, y + alto - 2) for x in (x_esq, x_dir)]
    return [(cor, pontos), (brilho, brilhos)]


def bochechas(x_esq, x_dir, y, cor):
    return (cor, [(x, y) for x in (x_esq, x_esq + 1, x_dir, x_dir + 1)])


# ---- cachorros ----------------------------------------------------------------

# Fredinho: sprite de 57 x 71 pixels copiado do modelo que o usuário escolheu (chihuahua de lado, orelhas
# enormes e cauda levantada) e recolorido com o caramelo do cachorro real: corpo caramelo, focinho,
# sobrancelhas e peito cremes, patinhas claras, orelhas rosadas por dentro e contorno marrom-escuro.
FREDINHO_PALETA = {
    "A": "#2e1b0f",
    "B": "#d58a3b",
    "C": "#bd742f",
    "D": "#e8a290",
    "E": "#e6a459",
    "F": "#f2b9a8",
    "G": "#dfa662",
    "H": "#cf8f4a",
    "I": "#faead0",
    "J": "#f1d4a4",
    "K": "#e4bb82",
    "L": "#fcf0d8",
    "M": "#f6e0b8",
    "N": "#ecbd80",
    "O": "#ffffff",
    "P": "#ecca98"
}
FREDINHO = """
..................................AA.....................
................................AAFA.....................
AAAA...........................AFFFFA....................
AFFBAA.......................AAFFFFFA....................
AFFDFBA.....................AFFFFFDDA....................
ADDDDDBA...................ADFFFFFDDA....................
ADDDDDDBA.................ACDFFFFDDDA....................
ADFFFDDDBA...............ACFFFFFFDDDA....................
ADFFFDDDBA..............AAFFFFFFFDDDAA...................
ADFDDDDDDBA............AAFDDDDDDDDDDCA...................
ADFDDDDDDBBA..........AAFDDDDDDDDDDDCA...................
ADFDDDDDDDBA..........ACDDDDDDDDDDFFCA...................
AFFDDDDDDDBBA........ACDDDDDDDDDDDFFCA...................
AFFDDDDDDDBBA.AAAAAA.AADDDDDDDDDDDDDCA...................
AFFFDDDDDDACAAACACCAACCFFDDDDDDDDDDDAA...................
AFFFDDDDDACCCCCBBCCCACAFFFFFFDDDDDDFCA...................
AFFFFDDDACCCBBBBBBBBBCACFFFFFFFDDDFFCA...................
AFFFFDDABBBBBBBBBBBBBBCCADFFFFFDDDFCCA...................
ADDDDDABBBBBBBEEEEJKBBCCAAFFFFFFFFFBAA...................
ADDDDAJJBBEEEBEEEJJJJBBCCAAFFFFFFFFBAA...................
.ADDDJJJEEEEEBBEEJJJJJBBACCAFFFFFFBBA....................
.ADDAJIIBEEEBBBBEJJIIIBBCCCCADDDDBBBA....................
..ADABBBBEBBBBBBBBBBBBBBCCCCADDDBBBBA....................
..AACBBEEEBBBBBBBBBAAABBBCACADDEBBBA.....................
...ACAAEEEBBBBBBBCAAAAABBBCCAEEBBBBA.....................
...AAOOAEBBBCCBBBKAAOOAABBBBBBBBBBA...........AAA........
..AKAOOABBBBCCCCCKAAOOAABBBBABCCAA.............AAA.......
..AKAAAABBBBBBBBBKAAAAAABBCCACAA................ACA......
..AKAAAACCBBBBBBBKAAAAAABBCCAA...................ACA.....
..AKKAAACCBBBBBBBKKAAAAABBCAAA...................ABBA....
...AKKAABBBBBBBBBKKKAAABBACAAA....................ABA....
...AKKKBBBBBBBBEEEKKKKBBBAKCAA....................ABBA...
....ACBBBBBEEEEEEBBBBBBBJJJCA.....................ABBA...
.....ABBBBBEIIIJJIBABABAKKCAA.....................ABBA...
.....ABAAAAIIIIJJIIJJJKKKKAA......................ABBA...
.....AIIAAIIIIIIIIIJJJKKKAAA.....................ABBBA...
.....AIICAIIIIIIIAIJJJKKAAAA.....................ABBA....
......AAIIAAAAAAAIJJJJKACCACAAAAAA..............AABKA....
........AIIIIIIIIIJJKCCCCACACACACAAAAAAAAAAAAA.AAEEKA....
.........AAAAAAIIJJJBBCCCCACACACACACACACACACACAAAEKA.....
..............AIJJJBBBBCCCCCCCCCCCCCACCCACCCACCBBKA......
..............AJJJJBCCCCCCCCCCCCCCCCCCCAACCAAACCCA.......
..............AEKKBBCCCCCCCCCCCCCCCCCCCCCACCCCCCCCA......
..............AEEKBBBBBBCCBBCCBBCCBBCCBBCBBBCCCCACCA.....
..............AEEEEBBBBBCCBBBBBBBBBBBBBBBBBBCCCCACCA.....
..............AEEEEBBBBBCCBBBBBBBBBBBBBBBBBBBCCCCCCCA....
..............AEEEEEBBBBCCCCCCCCCCCCCCCCCCCCCCCCCCCCA....
.............AAEEBBEEBBBCBBBBBBBCCBBCCBBBBBBBBBCCCCCAA...
.............AGGGBBEGGHHHBBBBBBBBBBBCCBBBBBBBBBCCCCCCA...
.............AGGGGEGGGGHHHBBBBBBBBBBBBBBBBBBBBBBBBBBAA...
.............AGGGNEGGGGGHHEEBBBBBBBBBBBBBBBBBBBBBBBBBA...
..............AGNBEENNGGGHEEEEEBBBBBBBBBBBEEEEBBBBBBBA...
..............ANBBEEEEGGGHEEEAEEEEEEEEAAAAAAEEEEEEBBAA...
..............ABBAEEEEGAGEEEEAEEEEEEEAHHHHHHAEEEEEEEHA...
...............ABEAEBBBBAEEEEHAEBBEAAHHHHHHHAHEEEEEEHA...
...............ABEEAABBBBAEEEHAEBAA.AHHHHHHAAHHEEEBHHA...
................AEEHHAABBAEEHHAAA...AHHHHHHAAAHHHGGGGGA..
................AEHHHA.AAAEEHHA......AHHHHHHAAAHHHGGGGGA.
................AHHHHA...AEHHHA.......AHHHHHHA.AAHGGGGGHA
................AGGGGA...AGHHHA........AHHHHHA...AGGGGGGA
................AGGGGA...AGGGHA.........AHHHHA....AHGGGGA
................AANGGA...AGGGGA..........AHGGA.....AHGGGA
.................ANGGA...AGGGGA..........AGGA.......AGGGA
.................ANNA....ANNGGA.........AHGGA.......AGGGA
.................ANNA....ANNGAA.........AGGGA.......ANGGA
................ALLLA....ALLLA........AAMMMA........ALMMA
..............AALLLLA....AMLLA.......APPAMLA......AAAMMMA
.............ALLALLA...AAMMLLA......APPAMLLA.....ALLAMMPA
.............ALALLLA..ALLALLLA......AAAAAAAA.....ALAMMPPA
.............AAAAAA...ALALLLA....................AAAAAAAA
.......................AAAAAA............................
"""
FREDINHO_ALTURA = 71  # mais alto que o quadro de 64: passa 7 pixels para cima (ver ALTURA_EXTRA)


def pinscher():
    grade = de_mapa(FREDINHO, FREDINHO_PALETA)
    grade = Grade(grade)
    grade.base = Grade(grade)
    # Outras caras: troca só as células dos olhos (esquerdo x 4..7 e direito x 18..23, y 23..30).
    corpo, linha, claro = FREDINHO_PALETA["B"], FREDINHO_PALETA["A"], FREDINHO_PALETA["O"]

    def olhos_fechados(grade, ex, tipo):
        novo = Grade(grade)
        for (x, y), c in grade.items():
            if (4 <= x <= 7 or 18 <= x <= 23) and 23 <= y <= 30 and c in (linha, claro):
                novo[(x, y)] = corpo
        for x0, x1 in ((4, 7), (19, 22)):
            if tipo == "pisca":
                for x in range(x0, x1 + 1):
                    novo[(x, 27)] = linha
            else:  # feliz: olho em arco
                novo[(x0, 28)] = novo[(x1, 28)] = linha
                novo[(x0 + 1, 27)] = novo[(x1 - 1, 27)] = linha
        return novo

    def triste(grade):
        novo = Grade(grade)
        for x in (5, 21):
            novo[(x, 31)] = novo[(x, 32)] = "#6ec8ff"
        return novo

    grade.expressoes = {"pisca": olhos_fechados(grade, None, "pisca"), "feliz": olhos_fechados(grade, None, "feliz"),
                        "triste": triste(grade)}
    return grade


RONALDO_PALETA = {
    "A": "#a14b29",
    "B": "#bd6038",
    "C": "#8a4023",
    "D": "#3b1b0f",
    "E": "#341810",
    "F": "#5e372a",
    "G": "#4a2010",
    "H": "#14100e",
    "I": "#bd6139",
    "J": "#40200f",
    "K": "#d27b50",
    "L": "#80503f",
    "M": "#b0572f",
    "N": "#7c3820",
    "O": "#6c4235",
    "P": "#ffffff",
    "Q": "#57524d",
    "R": "#e9b9a6",
    "S": "#2e2a27"
}
RONALDO = """
..............DDDDDDD.........................
............DEAAAAAAAEDD......................
..........ADIIIIAIIAAAAAAD....................
.........EIIIIIAAAAAAAEDEEDD..................
.........EDIIIDEEEAAAADAAAADD.................
........DABBAAAKKEEAFEDOOFFFDD................
.......DDABBAAHHHAAAFEOOLLFFFFD...............
.......HHBBBAHRHPHHADEOEFLFFFDD...............
.......HQBBBAHRHHAHAEELFFFFFFFDD..............
......NNBBBBAPPPHIHAEELFFFFFFFFD..............
....CCBBBKBBAAPPREAAEFLFFFFFFFFD..............
.SSHCRRBKKBBBAAAAAAAEOLFFFFFFFFD..........DD..
SQQQHKRBBBBBBBBBBBBAELLFFFFFFFFD..........DAD.
SHHHHCBBBBBBBBBBBBBBELFFFFFFFFD...........EME.
HHHHCKKBBBBBBBBBBBBEFLFFFFFFFFE..........EMME.
.HSCBBBBBBBBCHCBBBBEFFFFFFFFFFE..........EEME.
..CBBBBBBBQQHHBBBBBDFFFFFFFFFFE..........EAAE.
..CCCCCGGGHHBBBBBBCEFFFFFFFFFFE..........EIAE.
....JCCCCCCCCCCCCCCEFFFFFFFFFD..........DIIAE.
.....GGGGGGGGGGJGCCDFFFFFFFFDE..........EIAED.
............GGCCCCCEFFFFFFDDDD.........EDAAD..
.............GGCCCCEEFFFDEEEH.....DDDDDDDEAD..
.............GGCCCCCEEDDDDHH....DDDDDAAAADD...
.............GGCBCCCCDHHHHEDEEDDDAAAAAAAAAD...
.............GCCBCCCCEEEEEEDDEAAAAAAAAAIIAAE..
.............JCCBCCCCEEEEEEEDAAAAAAAAAAIIAAAD.
.............ECCBBBCCEEEEEEEAAAAAAAAAAAAAAAAE.
............DECCBBBCCEEEEAAAAAAAAAAAAEAAAAAAE.
...........DDECBBBBCCAAAAAAAAAAAAAAAAEAAAAAAAD
...........DDGBBBBBBCAAAAIIAAADAAAAAAEAAAAAAAD
...........EAJBBBBBBCAAAIMMIAADAAAADDDAAAAAAAD
...........EACBBBBBBBAAAIIIIMADEEEDDDDDAAAAAAD
...........EABBBBKBBBDAAIIIIMADEEDEEEDDDAAAAAD
...........DECBBBKKBBDDAAIIIAAEEEDDDCCDDDDEEAD
............DCBBBBBBBCDAAAIIAAEEEDCCCCCCDDDDE.
............DEBBBBBBBJDAAAAAAAEECCCGGGGCCDDDE.
.............ECBBBBBCCDAAAAAAADCCGGG..GGGCDDCG
.............EJCCBCCCCDEAAAAADDJJCG.....GCCCCG
.............EDDCCCCCCCDAAAAADCGCCG.....GGBBCG
.............EDDDJJCNNNDAAAADJJCCCG.....GCBBCG
..............DDDCJGGGJDAAAACGCCCG......GBBBCG
..............EBCCJ....EAAAACGCCG......CBBBBJ.
............CCBBCCJ....EABBBCGGG......GBBCBBJ.
...........GKKKCCCJ....DBBBBE.........GCCHBCJ.
...........GCKHCCCJ...NCBBBBJ.........GGGHGG..
............GGHHGG...GBBBCBBJ.................
.....................GCBHCCCJ.................
......................GGHHGG..................
"""


def salsicha():
    grade = Grade(de_mapa(RONALDO, RONALDO_PALETA))
    grade.base = Grade(grade)
    corpo, linha = RONALDO_PALETA["A"], RONALDO_PALETA["H"]
    olho = [(x, y) for y in range(6, 11) for x in range(13, 20)
            if grade[(x, y)] in (RONALDO_PALETA[k] for k in "HRPQ")]

    def sem_olho():
        novo = Grade(grade)
        for p in olho:
            novo[p] = corpo
        return novo

    fechado, feliz, triste = sem_olho(), sem_olho(), Grade(grade)
    for x in range(14, 19):
        fechado[(x, 8)] = linha
    for p in ((14, 8), (15, 7), (16, 7), (17, 7), (18, 8)):
        feliz[p] = linha
    for p in ((15, 11), (15, 12)):
        triste[p] = "#6ec8ff"
    grade.expressoes = {"pisca": fechado, "feliz": feliz, "triste": triste}
    return grade


# ---- outros pets ------------------------------------------------------------------

def ovo():
    BR, BRs, BRl, MA, MAs = "#fbfaf5", "#d6d9dc", "#ffffff", "#3fb8af", "#2b8f88"
    return montar([
        (sb('<path d="M24 6 C35 6 40 24 40 32 C40 42 33 47 24 47 C15 47 8 42 8 32 C8 24 13 6 24 6 Z"/>', BR, BRs,
            f'<ellipse cx="17" cy="18" rx="2.5" ry="5" fill="{BRl}"/>'
            f'<ellipse cx="27" cy="16" rx="3" ry="2.5" fill="{MA}"/><ellipse cx="17" cy="32" rx="3.5" ry="3" fill="{MA}"/>'
            f'<ellipse cx="31" cy="30" rx="2.5" ry="2" fill="{MA}"/><ellipse cx="26" cy="41" rx="3.5" ry="2.5" fill="{MA}"/>'
            f'<ellipse cx="36" cy="38" rx="2" ry="3" fill="{MAs}"/>', id_="o"), [BR, BRs, BRl, MA, MAs], True),
    ], "#4a5560")


PETS = {"pinscher": pinscher, "salsicha": salsicha, "ovo": ovo}


# ---- acessórios: (desenho, largura, altura, âncora x, âncora y) --------------------
# A âncora é o pixel do acessório que encosta no ponto do pet (topo, olhos ou pescoço).
# Desenhados pixel a pixel (um caractere por pixel, "." = vazio), com contorno, cor base, sombra
# embaixo à direita e luz em cima à esquerda.

LACO = """
.KK.........KK.
KLRKK.....KKRrK
KLRRRKK.KKRRRrK
KLRRRRKKKRRRRrK
KRRRrKLLRKrRRrK
KRRrrKLRrKrrRrK
KRrrKKRrrKKrrrK
.KKKKKKKKKKKKK.
....KRK.KrK....
...KRK...KrK...
...KK.....KK...
"""

BONE = """
.......KKKKKKK............
.....KKLLRRRRRKK..........
....KLLRRRRRRRRRK.........
...KLRRRRWWWRRRRrK........
..KLRRRRWWWWWRRRRrK.......
..KLRRRRRWWWRRRRRrK.......
.KLRRRRRRRRRRRRRRrrK......
.KRRRRRRRRRRRRRRRrrK......
.KRRRRRRRRRRRRRRrrrKKKK...
.KrrrrrrrrrrrrrrrKKrrrrKK.
.KKKKKKKKKKKKKKKKrrrrrrrrK
...............KKrrrrrrrK.
................KKKKKKKKK.
"""

OCULOS = """
.KKKKKKKKKK....KKKKKKKKKK.
KWWdDDDDDDDKKKKKWWdDDDDDDK
KWdDDDDDDDDKFFKKWdDDDDDDDK
KdDDDDDDDDDK....KdDDDDDDDK
KDDDDDDDDDdK....KDDDDDDDdK
KDDDDDDDDdlK....KDDDDDDdlK
.KDDDDdlllK......KDDDdllK.
..KKKKKKKK........KKKKKK..
"""

MAGO = """
...............KKK.........
.............KKPMK.........
............KPMMK..........
...........KPMMmK..........
..........KPMMMmK..........
..........KPMYMmK..........
.........KPMYYYmmK.........
.........KPMMYMMmK.........
........KPMMMMMMmmK........
........KPMMMMMMMmK........
.......KPMMMMMyMMmmK.......
.......KPMMMMMMMMMmK.......
......KKKKKKKKKKKKKKK......
......KYYYYYYYYYYYYYK......
......KyyyyyyyyyyyyyK......
..KKKKKKKKKKKKKKKKKKKKKKK..
.KPPMMMMMMMMMMMMMMMMMMMmmK.
KMMMMMMMMMMMMMMMMMMMMMMmmmK
.KmmmmmmmmmmmmmmmmmmmmmmmK.
..KKKKKKKKKKKKKKKKKKKKKKK..
"""

COROA = """
.KKK....KKK....KKK.
KWOoK..KWOoK..KWOoK
.KOK....KOK....KOK.
.KOK...KOOOK...KOK.
.KOOK.KLOOOoK.KOoK.
.KLOOOKOOOOOKOOOoK.
.KLOOOOOOOOOOOOOoK.
.KKKKKKKKKKKKKKKKK.
.KOOCOOORRROOOCOoK.
.KOCWcOORWrOOCWcoK.
.KOOcOOOrrrOOOcOoK.
.KoooooooooooooooK.
.KKKKKKKKKKKKKKKKK.
"""


def laco():
    return de_mapa(LACO, {"K": "#6b1d3d", "R": "#ff6fa8", "r": "#d6437f", "L": "#ffc2da"}), 15, 11, 7, 9


def bone():
    paleta = {"K": "#4a120a", "R": "#e8402a", "r": "#a82a18", "L": "#ff8a6a", "W": "#ffffff"}
    return de_mapa(BONE, paleta), 26, 13, 11, 10


def oculos():
    paleta = {"K": "#111111", "F": "#3a3a3a", "D": "#22304f", "d": "#3b5a8c", "l": "#6fa0e0", "W": "#ffffff"}
    return de_mapa(OCULOS, paleta), 26, 9, 13, 4


def cachecol(largura=30):
    """Faixa listrada com uma leve curva, nó e a ponta caindo com franja. 'largura' é o tamanho da faixa em
    volta do pescoço (30 para pets de frente, 18 para os de cabeça estreita ou de lado)."""
    K, VM, VMs, VMl, BR, BRs = "#5a1418", "#ff595e", "#c23a3f", "#ff9a9c", "#ffffff", "#e8d2d2"
    fim = largura - 1
    no_x = largura // 2 + 1  # coluna do nó

    def tricô(x, linha, ultima):
        """Listras na diagonal; linha 1 = luz, última = sombra."""
        if (x + linha) // 2 % 3 == 0:
            return BR if linha < ultima else BRs
        return VMl if linha == 1 else (VMs if linha == ultima else VM)

    g = {}
    for x in range(largura):  # faixa em volta do pescoço
        topo = (0 if 3 < x < fim - 3 else 1) + (x in (0, fim))
        base = topo + (3 if x in (0, fim) else 5)
        for y in range(topo, base + 1):
            borda = y in (topo, base) or x in (0, fim)
            g[(x, y)] = K if borda else tricô(x, y - topo, base - topo - 1)
    for y in range(6, 13):  # ponta que cai, inclinada para a direita
        x0 = no_x + 1 + (y >= 10)
        for x in range(x0, x0 + 7):
            borda = x in (x0, x0 + 6) or y == 12
            g[(x, y)] = K if borda else tricô(y, x - x0, 5)
    for y in range(2, 7):  # nó
        for x in range(no_x, no_x + 6):
            if x in (no_x, no_x + 5) or y in (2, 6):
                g[(x, y)] = K
            else:
                g[(x, y)] = VMl if x == no_x + 1 and y < 5 else (VMs if x == no_x + 4 or y == 5 else VM)
    for x in range(no_x + 2, no_x + 9):  # franja
        g[(x, 13)] = VM if x % 2 == 0 else K
        if x % 2 == 0:
            g[(x, 14)] = K
    return g, max(largura, no_x + 9), 15, largura // 2, 2


def cachecol_estreito():
    return cachecol(18)


def oculos_lado(espelhado=False):
    """Óculos de perfil (para pets que olham de lado): uma lente e a haste para trás. Âncora = centro da lente.
    Olhando para a esquerda; espelhado=True para os que olham para a direita."""
    K, D, d, l, W, F = "#111111", "#22304f", "#3b5a8c", "#6fa0e0", "#ffffff", "#3a3a3a"
    mapa = """
..KKKKKKKK......
.KWWdDDDDDK.....
KWdDDDDDDDDKKKKK
KdDDDDDDDDDK....
KDDDDDDDDDdK....
KDDDDDDDDdlK....
.KDDDDddllK.....
..KKKKKKKK......
"""
    grade = de_mapa(mapa, {"K": K, "D": D, "d": d, "l": l, "W": W})
    ax = 5
    if espelhado:
        grade = {(15 - x, y): c for (x, y), c in grade.items()}
        ax = 10
    return grade, 16, 8, ax, 3


def oculos_lado_dir():
    return oculos_lado(True)


def oculos_lado_mini():
    """Óculos de perfil pequenos, para cabeças pequenas e cheias de detalhe (serpente de gelo): lente de
    7 x 6 e haste para trás. Olhando para a esquerda. Âncora = centro da lente."""
    K, D, d, l, W = "#111111", "#22304f", "#3b5a8c", "#6fa0e0", "#ffffff"
    mapa = """
.KKKKK......
KWWDDDKKKKKK
KWDDDDK.....
KDDDDdK.....
.KDDdlK.....
..KKKK......
"""
    return de_mapa(mapa, {"K": K, "D": D, "d": d, "l": l, "W": W}), 12, 6, 3, 2


def mago():
    paleta = {"K": "#1f1660", "M": "#6a5ae0", "m": "#4434b0", "P": "#9d8ff5", "Y": "#ffd166", "y": "#e0a030"}
    return de_mapa(MAGO, paleta), 27, 20, 13, 17


def coroa():
    paleta = {"K": "#5a3d00", "O": "#f5b81b", "o": "#c98a0b", "L": "#fff1a8", "W": "#ffffff",
              "R": "#ff3b5c", "r": "#b0123a", "C": "#4cc9f0", "c": "#1f8fb8"}
    return de_mapa(COROA, paleta), 19, 13, 9, 12


ACESSORIOS = {"laco": laco, "bone": bone, "oculos": oculos, "cachecol": cachecol, "mago": mago, "coroa": coroa,
              # variantes para pets de lado ou de pescoço estreito (ver AJUSTE_ACESSORIO no catálogo)
              "oculos_lado": oculos_lado, "oculos_lado_dir": oculos_lado_dir,
              "oculos_lado_mini": oculos_lado_mini, "cachecol_estreito": cachecol_estreito}
