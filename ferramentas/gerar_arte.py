#!/usr/bin/env python3
"""Gera os desenhos (SVG) dos temas em arte/. Rodar de novo só se mudar algum desenho.

Toda a arte é original: pixel art desenhada aqui, e formas geométricas.
"""
import math
import random
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "arte"


def salvar(nome, svg):
    caminho = SAIDA / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(svg.strip() + "\n")


# ---- pixel art ---------------------------------------------------------------

PALETA = {
    "K": "#1b1b1b", "W": "#ffffff", "G": "#5ac54f", "D": "#2f8f3a", "P": "#9b6bd6",
    "Q": "#6a3fa8", "O": "#ff8c2e", "Y": "#ffd23f", "R": "#e8402a", "L": "#cfd8dc",
    "B": "#8fd3ff", "N": "#8b5a2b", "n": "#6b4220", "S": "#b0bec5",
}


def pixel_svg(linhas, paleta=PALETA):
    largura = max(len(l) for l in linhas)
    linhas = [l.ljust(largura, ".") for l in linhas]
    rects = []
    for y, linha in enumerate(linhas):
        x = 0
        while x < largura:
            c = linha[x]
            if c == ".":
                x += 1
                continue
            fim = x
            while fim + 1 < largura and linha[fim + 1] == c:
                fim += 1  # junta pixels iguais vizinhos num retângulo só (SVG menor)
            rects.append(f'<rect x="{x}" y="{y}" width="{fim - x + 1}" height="1" fill="{paleta[c]}"/>')
            x = fim + 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {len(linhas)}" '
            f'shape-rendering="crispEdges">{"".join(rects)}</svg>')


def bola_captura(t=16):
    c = (t - 1) / 2
    linhas = []
    for y in range(t):
        linha = ""
        for x in range(t):
            d = math.hypot(x - c, y - c)
            if d > c + 0.5:
                ch = "."
            elif d > c - 0.6:
                ch = "K"
            elif d <= 1.6:
                ch = "W"
            elif d <= 2.7:
                ch = "K"
            elif round(y) in (int(c), int(c) + 1):
                ch = "K"
            elif y < c:
                ch = "W" if (x, y) in {(4, 3), (5, 3), (4, 4), (3, 4)} else "R"
            else:
                ch = "L" if x + y > t + 4 else "W"
            linha += ch
        linhas.append(linha)
    return linhas


SLIME = """
......KKKK......
....KKGGGGKK....
...KGGGGGGGGK...
..KGGWGGGGGGGK..
..KGWWGGGGGGGK..
.KGGGGGGGGGGGGK.
.KGGKWGGGGKWGGK.
.KGGKKGGGGKKGGK.
.KGGGGGGGGGGGGK.
.KGGGGGKKGGGGGK.
KGGDGGGGGGGGDGGK
KGDDDGGGGGGDDDGK
.KKKKKKKKKKKKKK.
"""

FANTASMA = """
.....KKKKKK.....
...KKPPPPPPKK...
..KPPPPPPPPPPK..
.KPPWPPPPPPPPPK.
.KPWWPPPPPPPPPK.
.KPPPKWPPPKWPPK.
.KPPPKKPPPKKPPK.
.KPPPPPPPPPPPPK.
.KPPPPPKKPPPPPK.
.KPPPPPPPPPPPPK.
.KQPPPPPPPPPPQK.
.KQQKPPPKPPPKQK.
.KQK.KPK.KPK.KK.
..K...K...K.....
"""

PINTINHO = """
......RR........
.....RYR........
....KKKKKK......
...KOOOOOOK.....
..KOOOOOOOOK....
..KOWKOOOOOOK...
..KOKKOOOOOOK...
.KYYOOOOOOOOK...
.KYYOOOOOOOOOK..
..KKOOOWWOOOOK..
...KOOWWWWOOK...
...KOOOWWOOOK...
....KOOOOOOK....
....KKKKKKKK....
.....K....K.....
....KK...KK.....
"""

GRAMA = """
....G.......G...
...GG..G...GG.G.
.G.GGG.GG.GGG.GG
GGGGGGGGGGGGGGGG
DGGDGGGDGGGDGGGD
DDDDDDDDDDDDDDDD
NNNNNNNNNNNNNNNN
NNnNNNNNNnNNNNNN
NNNNNnNNNNNNNnNN
NNNNNNNNNNNNNNNN
"""

NUVEM = """
.......WWWW.........
.....WWWWWWWW.......
...WWWWWWWWWWWW.....
..WWWWWWWWWWWWWWWW..
.WWWWWWWWWWWWWWWWWW.
WWWWWWWWWWWWWWWWWWWW
.BBBBBBBBBBBBBBBBBB.
"""


def mapa(texto):
    return [l for l in texto.strip("\n").split("\n")]


def gerar_pixel():
    salvar("pixel/bola.svg", pixel_svg(bola_captura()))
    salvar("pixel/slime.svg", pixel_svg(mapa(SLIME)))
    salvar("pixel/fantasma.svg", pixel_svg(mapa(FANTASMA)))
    salvar("pixel/pintinho.svg", pixel_svg(mapa(PINTINHO)))
    salvar("pixel/grama.svg", pixel_svg(mapa(GRAMA)))
    salvar("pixel/nuvem.svg", pixel_svg(mapa(NUVEM)))


# ---- heróis (quadrinhos) -----------------------------------------------------

def estrela(cx, cy, pontas, r_ext, r_int, jitter, semente):
    rnd = random.Random(semente)
    pts = []
    for i in range(pontas * 2):
        ang = math.pi * i / pontas - math.pi / 2
        r = (r_ext if i % 2 == 0 else r_int) * (1 + rnd.uniform(-jitter, jitter))
        pts.append(f"{cx + r * math.cos(ang):.1f},{cy + r * math.sin(ang):.1f}")
    return " ".join(pts)


def gerar_hq():
    salvar("hq/pontos.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 14 14" width="14" height="14">
  <circle cx="3.5" cy="3.5" r="2" fill="#000" fill-opacity="0.13"/>
  <circle cx="10.5" cy="10.5" r="2" fill="#000" fill-opacity="0.13"/>
</svg>""")
    for nome, fora, dentro, semente in (("explosao", "#e53935", "#ffd600", 3),
                                        ("explosao_azul", "#1e40af", "#7dd3fc", 7)):
        salvar(f"hq/{nome}.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
  <polygon points="{estrela(120, 120, 14, 112, 74, 0.12, semente)}" fill="{fora}"
           stroke="#111" stroke-width="7" stroke-linejoin="round"/>
  <polygon points="{estrela(120, 120, 12, 84, 58, 0.1, semente + 1)}" fill="{dentro}"
           stroke="#111" stroke-width="5" stroke-linejoin="round"/>
</svg>""")
    rnd = random.Random(42)
    predios, janelas, x = [], [], 0
    while x < 800:
        w, h = rnd.randint(40, 90), rnd.randint(50, 150)
        predios.append(f'<rect x="{x}" y="{160 - h}" width="{w}" height="{h}"/>')
        for jy in range(160 - h + 10, 150, 16):
            for jx in range(x + 8, x + w - 8, 14):
                if rnd.random() < 0.45:
                    janelas.append(f'<rect x="{jx}" y="{jy}" width="6" height="8"/>')
        x += w + rnd.randint(0, 6)
    salvar("hq/cidade.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 160" preserveAspectRatio="none">
  <g fill="#1e2a5a">{"".join(predios)}</g>
  <g fill="#ffd600" fill-opacity="0.85">{"".join(janelas)}</g>
</svg>""")
    salvar("hq/emblema.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 220">
  <path d="M100 8 L188 40 C188 120 150 180 100 212 C50 180 12 120 12 40 Z"
        fill="#e53935" stroke="#111" stroke-width="8" stroke-linejoin="round"/>
  <path d="M100 26 L170 52 C170 118 138 166 100 192 C62 166 30 118 30 52 Z"
        fill="none" stroke="#ffd600" stroke-width="6"/>
  <path d="M112 50 L64 122 L98 122 L84 178 L140 98 L104 98 L124 50 Z"
        fill="#ffd600" stroke="#111" stroke-width="6" stroke-linejoin="round"/>
</svg>""")


# ---- espaço ------------------------------------------------------------------

def gerar_espaco():
    rnd = random.Random(7)
    pontos = "".join(
        f'<circle cx="{rnd.uniform(0, 300):.1f}" cy="{rnd.uniform(0, 300):.1f}" '
        f'r="{rnd.choice([0.6, 0.8, 1, 1.3]):.1f}" fill="#fff" fill-opacity="{rnd.uniform(0.3, 1):.2f}"/>'
        for _ in range(70))
    salvar("espaco/estrelas.svg",
           f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="300" height="300">{pontos}</svg>')
    salvar("espaco/planeta.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 200">
  <defs>
    <radialGradient id="p" cx="35%" cy="30%" r="75%">
      <stop offset="0" stop-color="#ffb86b"/><stop offset="0.55" stop-color="#e2557a"/>
      <stop offset="1" stop-color="#4b1d6b"/>
    </radialGradient>
  </defs>
  <ellipse cx="130" cy="104" rx="122" ry="30" fill="none" stroke="#f9d9ff" stroke-opacity="0.5" stroke-width="9"/>
  <circle cx="130" cy="100" r="70" fill="url(#p)"/>
  <path d="M8 104 A122 30 0 0 0 252 104" fill="none" stroke="#f9d9ff" stroke-opacity="0.9" stroke-width="9"/>
  <circle cx="104" cy="74" r="9" fill="#fff" fill-opacity="0.18"/>
  <circle cx="150" cy="122" r="13" fill="#000" fill-opacity="0.12"/>
</svg>""")
    salvar("espaco/foguete.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 200">
  <path d="M60 170 C48 186 52 198 60 200 C68 198 72 186 60 170 Z" fill="#ffb02e"/>
  <path d="M60 176 C55 186 57 193 60 195 C63 193 65 186 60 176 Z" fill="#fff3b0"/>
  <path d="M34 120 L10 160 L36 152 Z M86 120 L110 160 L84 152 Z" fill="#e2557a"/>
  <path d="M60 8 C30 40 30 120 38 160 L82 160 C90 120 90 40 60 8 Z" fill="#eef2ff"/>
  <path d="M60 8 C48 22 42 36 40 48 L80 48 C78 36 72 22 60 8 Z" fill="#e2557a"/>
  <circle cx="60" cy="84" r="15" fill="#7dd3fc" stroke="#94a3b8" stroke-width="5"/>
  <rect x="50" y="150" width="20" height="14" rx="3" fill="#94a3b8"/>
</svg>""")
    # Nebulosas em tamanho fixo: o GTK3 só copia a imagem pronta. Um radial-gradient no CSS
    # seria recalculado a cada quadro e deixava as animações lentas.
    # O centro fica no canto da imagem (cx, cy), que o CSS encosta no canto da tela.
    for nome, cor, opacidade, cx, cy in (("nebulosa_roxa", "#7c3aed", 0.45, 600, 100),
                                         ("nebulosa_azul", "#0ea5e9", 0.30, 100, 600)):
        salvar(f"espaco/{nome}.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 700" width="700" height="700">
  <defs>
    <radialGradient id="n" cx="{cx}" cy="{cy}" r="420" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{cor}" stop-opacity="{opacidade}"/>
      <stop offset="1" stop-color="{cor}" stop-opacity="0"/></radialGradient>
  </defs>
  <rect width="700" height="700" fill="url(#n)"/>
</svg>""")
    salvar("espaco/brilho.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 C18 26 14 22 0 20 C14 18 18 14 20 0 Z" fill="#fff"/>
</svg>""")


# ---- neon (synthwave) --------------------------------------------------------

def gerar_neon():
    faixas = "".join(f'<rect x="0" y="{y}" width="300" height="{h}" fill="#000"/>'
                     for y, h in ((160, 4), (178, 6), (196, 8), (214, 10), (234, 12), (256, 14)))
    salvar("neon/sol.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
  <defs>
    <linearGradient id="s" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe259"/><stop offset="0.5" stop-color="#ff7a59"/>
      <stop offset="1" stop-color="#ff2bd6"/>
    </linearGradient>
    <mask id="m"><rect width="300" height="300" fill="#fff"/>{faixas}</mask>
  </defs>
  <circle cx="150" cy="150" r="140" fill="url(#s)" mask="url(#m)"/>
</svg>""")
    linhas = []
    for i in range(1, 14):
        y = 260 * (i / 13) ** 2.2
        linhas.append(f'<line x1="0" y1="{y:.1f}" x2="1000" y2="{y:.1f}"/>')
    for i in range(-14, 15):
        linhas.append(f'<line x1="500" y1="0" x2="{500 + i * 90}" y2="260"/>')
    salvar("neon/grade.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 260" preserveAspectRatio="none">
  <g stroke="#ff2bd6" stroke-width="2" stroke-opacity="0.75">{"".join(linhas)}</g>
</svg>""")
    salvar("neon/montanhas.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 200" preserveAspectRatio="none">
  <polygon points="0,200 0,150 90,70 170,140 260,40 360,150 440,90 520,160 610,50 700,130 790,80 880,140 1000,60 1000,200"
           fill="#1a0b2e" stroke="#22d3ee" stroke-width="3" stroke-linejoin="round"/>
</svg>""")


# ---- jogo: pets, acessórios, baús, moeda -----------------------------------------

PALETA_PET = dict(PALETA, **{
    "C": "#f4a259", "c": "#d9822b", "E": "#9aa5b1", "e": "#6b7785", "T": "#3fb8af",
    "V": "#4caf50", "v": "#2e7d32", "A": "#ffd166", "H": "#ff8fab", "M": "#5b4bc4",
    "m": "#3d2f9e", "U": "#ffe08a", "Z": "#ff595e", "F": "#4cc9f0",
    "y": "#e0a800", "g": "#e8963d", "b": "#3b82f6", "d": "#1d4ea8", "X": "#b5793a",
    "x": "#7a4a1c", "a": "#f6e7c8", "J": "#ffb3c7", "j": "#f08aa8", "p": "#c06a2b", "q": "#8a4519",
})

GATO = """
..K..........K..
.KCK........KCK.
.KCCK......KCCK.
.KCCCKKKKKKCCCK.
.KCCCCCCCCCCCCK.
KCCCWKCCCCWKCCCK
KCCCKKCCCCKKCCCK
KCHCCCCKKCCCCHCK
KCCCCCKCCKCCCCCK
.KCCCCCCCCCCCCK.
..KCCCCCCCCCCK..
..KcCCCCCCCCcK..
..KccKKccKKccK..
...KK..KK..KK...
"""

ROBO = """
.......KK.......
.......KZK......
.......KK.......
...KKKKKKKKKK...
..KEEEEEEEEEEK..
..KEKKKKKKKKEK..
..KEKFFKKFFKEK..
..KEKFFKKFFKEK..
..KEKKKKKKKKEK..
..KEEEEKKEEEEK..
..KEEEEEEEEEEK..
.KKKeeeeeeeeKKK.
.KEKeTTeeTTeKEK.
.KKKeeeeeeeeKKK.
...KeeK..KeeK...
...KKKK..KKKK...
"""

DRAGAO = """
...K......K.....
..KAK....KAK....
..KVVKKKKKVVK...
.KVVVVVVVVVVVK..
.KVVWKVVVVWKVK..
.KVVKKVVVVKKVK..
KVVVVVVVVVVVVVK.
KVVVZVVVVVZVVVK.
.KVVVVVVVVVVVK..
..KVUUUUUUUUK.KK
.KVKUUUUUUUUKKVK
KVVKUUUUUUUUKVK.
KVK.KUUUUUUKKK..
.K..KVVKKVVK....
....KKK..KKK....
"""

OVO = """
......KKKK......
....KKWWWWKK....
...KWWWWWWWWK...
..KWWWTWWWWWWK..
..KWWTTTWWWWWK..
.KWWWWTWWWWWWWK.
.KWWWWWWWWTWWWK.
.KWWWWWWWTTTWWK.
.KWWTWWWWWTWWWK.
.KWTTTWWWWWWWWK.
..KWTWWWWWWWWK..
..KLWWWWWWWWLK..
...KLLWWWWLLK...
....KKKKKKKK....
"""

PINSCHER = """
.K............K.
.KK..........KK.
.KpK........KpK.
.KpqK......KqpK.
.KpqqK....KqqpK.
..KpppKKKKpppK..
..KppppppppppK..
..KpWKppppWKpK..
..KpKKppppKKpK..
...KpppqqpppK...
....KpqKKqpK....
.....KpHHpK.....
....KppKKppK....
....KppppppK....
....KpK..KpK....
....KK....KK....
"""

CORGI = """
.KK..........KK.
.KgK........KgK.
.KgHK......KHgK.
.KgHgK....KgHgK.
..KggKKKKKKggK..
.KgggggWWgggggK.
KgggggWWWWgggggK
KggWKgWWWWgWKggK
KggKKWWWWWWKKggK
.KgWWWWKKWWWWgK.
..KWWWKWWKWWWK..
...KWWWHHWWWK...
..KgggWWWWgggK..
.KggggWWWWggggK.
.KWWKKKKKKKKWWK.
..KK........KK..
"""

# Salsicha de lado, olhando para a direita (cabeça perto do centro, para os chapéus).
SALSICHA = """
................
................
................
................
........KKKK....
.......KNNNNK...
......KNNNNWKK..
......KnNNNNNNKK
......KnnNNNNNK.
K.....KnnKNNKK..
.KKKKKKKKNNNK...
KNNNNNNNNNNNNK..
KNNNNNNNNNNNNK..
.KNnNNNNNNNnNK..
.KnK.......KnK..
.KK........KK...
"""

PASSARINHO = """
................
................
.....KKKKK......
....KbbbbbK.....
...KbbbbWKbbK...
...KbbbbKKbbKAK.
..KbbbbbbbbbbAAK
.KdbbbbbbbbbbKK.
KddbbbbbbbbbbK..
KdddbbWWWWWbbK..
.KdddbWWWWWWbK..
..KddbWWWWWWbK..
.KdKKbbWWWWbK...
KdK..KKbbbbK....
......KAK.KAK...
"""

PIKACHU = """
.K............K.
.KK..........KK.
.KYK........KYK.
..KYK......KYK..
..KYYKKKKKKYYK..
..KYYYYYYYYYYK..
.KYYYYYYYYYYYYK.
.KYYWKYYYYWKYYK.
.KYYKKYYYYKKYYK.
.KRRYYYKKYYYRRK.
.KRRYYKYYKYYRRK.
..KYYYYYYYYYYK..
..KYYYYYYYYYYK..
.KyYYYYYYYYYYyK.
.KyyKyyyyyyKyyK.
..KK.KKKKKK.KK..
"""

EEVEE = """
.KK..........KK.
.KXK........KXK.
.KXXK......KXXK.
.KXxXK....KXxXK.
..KXxXKKKKXxXK..
..KXXXXXXXXXXK..
.KXXXXXXXXXXXXK.
.KXXWKXXXXWKXXK.
.KXXKKXXXXKKXXK.
.KXXXXXKKXXXXXK.
..KXXXXXXXXXXK..
.KaaKXXXXXXKaaK.
KaaaaaKXXKaaaaaK
.KaaaaaaaaaaaaK.
..KXXKaaaaKXXK..
...KK.KKKK.KK...
"""

JIGGLYPUFF = """
..KK..KKKK..KK..
..KJKKJJJJKKJK..
..KJJJJJJjJJJK..
.KJJJJJJjjJJJJK.
.KJJJJJJJjJJJJK.
KJJKKKJJJJKKKJJK
KJKWFFKJJKWFFKJK
KJKFFFKJJKFFFKJK
KJJKKKJJJJKKKJJK
KJHJJJJJJJJJJHJK
KJJJJJJKKJJJJJJK
.KJJJJJJJJJJJJK.
.KJJJJJJJJJJJJK.
..KJJJJJJJJJJK..
..KjjK....KjjK..
...KK......KK...
"""

ACESSORIOS = {
    "laco": """
................
................
.....KK..KK.....
....KHHKKHHK....
....KHHHHHHK....
.....KKHHKK.....
................
................
""",
    "bone": """
................
................
.....KKKKKK.....
....KZZZZZZK....
...KZZZWZZZZK...
...KKKKKKKKKKKK.
................
................
""",
    "oculos": """
................
................
................
................
..KKKKK..KKKKK..
..KKFKKKKKKFKK..
..KKKKK..KKKKK..
................
""",
    "cachecol": """
................
................
................
................
................
..KKKKKKKKKKKK..
..KZWZWZWZWZWK..
..KKKKKKKZWK....
""",
    "mago": """
.......KK.......
......KMMK......
.....KMMAMK.....
....KMMMMMMK....
...KMMAMMMMMK...
..KmmmmmmmmmmK..
.KKKKKKKKKKKKKK.
................
""",
    "coroa": """
................
..K...K..K...K..
..KAK.KAAK.KAK..
..KAAKAAAAKAAK..
..KAZAAFAAAZAK..
..KAAAAAAAAAAK..
...KKKKKKKKKK...
................
""",
}

PETISCO = """
....KKKKKK....
..KKUUUUUUKK..
.KUUCUUUCUUUK.
KUUUUUUUUCUUUK
KUCUUUCUUUUUUK
KUUUUUUUUUCUUK
.KUUCUUUUUUUK.
..KKUUUUUCKK..
....KKKKKK....
"""


def bau(cor, faixa, brilho, gema):
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 170">
  <defs>
    <linearGradient id="t" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{brilho}"/><stop offset="1" stop-color="{cor}"/>
    </linearGradient>
  </defs>
  <ellipse cx="100" cy="158" rx="80" ry="9" fill="#000" fill-opacity="0.25"/>
  <rect x="22" y="72" width="156" height="82" rx="10" fill="url(#t)" stroke="#1b1b1b" stroke-width="6"/>
  <path d="M22 76 C22 30 178 30 178 76 Z" fill="url(#t)" stroke="#1b1b1b" stroke-width="6" stroke-linejoin="round"/>
  <rect x="22" y="70" width="156" height="14" fill="{faixa}" stroke="#1b1b1b" stroke-width="5"/>
  <rect x="44" y="40" width="16" height="114" fill="{faixa}" stroke="#1b1b1b" stroke-width="5"/>
  <rect x="140" y="40" width="16" height="114" fill="{faixa}" stroke="#1b1b1b" stroke-width="5"/>
  <rect x="84" y="64" width="32" height="40" rx="6" fill="{faixa}" stroke="#1b1b1b" stroke-width="5"/>
  <circle cx="100" cy="82" r="7" fill="{gema}" stroke="#1b1b1b" stroke-width="3"/>
  <path d="M34 92 C60 86 80 86 84 88" fill="none" stroke="#fff" stroke-opacity="0.35" stroke-width="5" stroke-linecap="round"/>
</svg>"""


def gerar_jogo():
    salvar("pets/slime.svg", pixel_svg(mapa(SLIME)))
    salvar("pets/fantasma.svg", pixel_svg(mapa(FANTASMA)))
    salvar("pets/pintinho.svg", pixel_svg(mapa(PINTINHO)))
    salvar("pets/gato.svg", pixel_svg(mapa(GATO), PALETA_PET))
    salvar("pets/robo.svg", pixel_svg(mapa(ROBO), PALETA_PET))
    salvar("pets/dragao.svg", pixel_svg(mapa(DRAGAO), PALETA_PET))
    salvar("pets/ovo.svg", pixel_svg(mapa(OVO), PALETA_PET))
    for nome, desenho in (("pinscher", PINSCHER), ("corgi", CORGI), ("salsicha", SALSICHA),
                          ("passarinho", PASSARINHO), ("pikachu", PIKACHU), ("eevee", EEVEE),
                          ("jigglypuff", JIGGLYPUFF)):
        salvar(f"pets/{nome}.svg", pixel_svg(mapa(desenho), PALETA_PET))
    for nome, desenho in ACESSORIOS.items():
        salvar(f"acessorios/{nome}.svg", pixel_svg(mapa(desenho), PALETA_PET))
    salvar("jogo/petisco.svg", pixel_svg(mapa(PETISCO), PALETA_PET))
    baus = {
        "madeira": ("#8b5a2b", "#5d3a17", "#c48a4a", "#e0c08a"),
        "prata": ("#8a96a3", "#5d6873", "#dfe6ee", "#7dd3fc"),
        "ouro": ("#d99a1e", "#8a5a00", "#ffe08a", "#ff595e"),
        "magico": ("#7b3fe4", "#3d1a8f", "#c4a5ff", "#4cc9f0"),
        "lendario": ("#ff7a1a", "#7a1fa2", "#ffd166", "#ffffff"),
    }
    for nome, (cor, faixa, brilho, gema) in baus.items():
        salvar(f"baus/{nome}.svg", bau(cor, faixa, brilho, gema))
    salvar("jogo/moeda.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="18" fill="#f5b81b" stroke="#8a5a00" stroke-width="3"/>
  <circle cx="20" cy="20" r="12" fill="none" stroke="#ffe08a" stroke-width="3"/>
  <path d="M14 12 Q18 9 22 12" stroke="#fff" stroke-opacity="0.7" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>""")


# ---- alto-mar (marca do NaView) ----------------------------------------------
#
# Cores da logo: índigo #6366f1, azul-céu #0ea5e9, marinho #1e1b4b, âmbar #f59e0b e branco.

def ondas_svg(largura, altura, crista, amplitude, periodo, topo, base, espuma):
    """Faixa de ondas que se repete na horizontal (largura múltipla do período)."""
    meio = periodo / 2
    caminho = f"M0 {crista}" + "".join(
        f" q{meio / 2} {-amplitude} {meio} 0 t{meio} 0" for _ in range(int(largura // periodo)))
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" preserveAspectRatio="none">
  <defs>
    <linearGradient id="o" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{topo}"/><stop offset="1" stop-color="{base}"/>
    </linearGradient>
  </defs>
  <path d="{caminho} V{altura} H0 Z" fill="url(#o)"/>
  <path d="{caminho}" fill="none" stroke="{espuma}" stroke-width="3" stroke-opacity="0.7"/>
</svg>"""


def gerar_mar():
    # Veleiro da logo, sem o fundo: mastro, vela grande e vela da frente formam o R.
    salvar("mar/veleiro.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="8 5 48 50">
  <path d="M20 6 h9 l-3 2.5 3 2.5 h-9 z" fill="#f59e0b"/>
  <path fill-rule="evenodd" fill="#ffffff"
        d="M20 9 h15 a10.5 10.5 0 0 1 0 21 h-9 v14 h-6 z
           M26 15 h8.5 a4.5 4.5 0 0 1 0 9 h-8.5 z"/>
  <path d="M30 30 h7 l11 14 h-7 z" fill="#ffffff"/>
  <path d="M9 44 h46 l-6.5 9 a3 3 0 0 1 -2.4 1.2 h-28.2 a3 3 0 0 1 -2.4 -1.2 z" fill="#1e1b4b"/>
  <rect x="14" y="47" width="36" height="1.6" rx="0.8" fill="#f59e0b"/>
</svg>""")
    # Farol listrado de branco e marinho; a lâmpada fica em (45, 42), onde o CSS põe a luz.
    salvar("mar/farol.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 200">
  <defs>
    <clipPath id="torre"><path d="M31 62 H59 L68 186 H22 Z"/></clipPath>
  </defs>
  <path d="M6 200 C10 182 28 176 45 178 C64 176 82 184 86 200 Z" fill="#1e1b4b"/>
  <g clip-path="url(#torre)">
    <rect x="0" y="62" width="90" height="124" fill="#ffffff"/>
    <rect x="0" y="80" width="90" height="18" fill="#1e1b4b"/>
    <rect x="0" y="118" width="90" height="18" fill="#1e1b4b"/>
    <rect x="0" y="156" width="90" height="18" fill="#1e1b4b"/>
  </g>
  <rect x="24" y="54" width="42" height="8" rx="2" fill="#1e1b4b"/>
  <rect x="33" y="32" width="24" height="22" rx="2" fill="#f59e0b"/>
  <rect x="33" y="32" width="24" height="22" rx="2" fill="none" stroke="#1e1b4b" stroke-width="3"/>
  <line x1="45" y1="32" x2="45" y2="54" stroke="#1e1b4b" stroke-width="2"/>
  <path d="M29 33 L45 14 L61 33 Z" fill="#1e1b4b"/>
  <circle cx="45" cy="12" r="3" fill="#f59e0b"/>
</svg>""")
    salvar("mar/luz.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
  <defs>
    <radialGradient id="l">
      <stop offset="0" stop-color="#fff7d6" stop-opacity="1"/>
      <stop offset="0.35" stop-color="#fcd34d" stop-opacity="0.75"/>
      <stop offset="1" stop-color="#f59e0b" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="30" cy="30" r="30" fill="url(#l)"/>
</svg>""")
    # Sol poente em âmbar, com halo pronto na imagem (sem radial-gradient no CSS do GTK).
    salvar("mar/sol.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
  <defs>
    <radialGradient id="h">
      <stop offset="0.35" stop-color="#fbbf24" stop-opacity="0.45"/>
      <stop offset="1" stop-color="#f59e0b" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="s" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fde68a"/><stop offset="1" stop-color="#f59e0b"/>
    </linearGradient>
  </defs>
  <circle cx="120" cy="120" r="120" fill="url(#h)"/>
  <circle cx="120" cy="120" r="56" fill="url(#s)"/>
</svg>""")
    salvar("mar/gaivota.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 16">
  <path d="M2 12 Q11 1 20 11 Q29 1 38 12" fill="none" stroke="#ffffff" stroke-width="3"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>""")
    salvar("mar/brilho.svg", """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 C18 26 14 22 0 20 C14 18 18 14 20 0 Z" fill="#ffffff"/>
</svg>""")
    salvar("mar/ondas_fundo.svg", ondas_svg(1000, 70, 18, 10, 125, "#38bdf8", "#0284c7", "#e0f2fe"))
    salvar("mar/ondas_frente.svg", ondas_svg(1000, 80, 20, 14, 200, "#0369a1", "#172554", "#7dd3fc"))


if __name__ == "__main__":
    gerar_jogo()
    gerar_pixel()
    gerar_hq()
    gerar_espaco()
    gerar_neon()
    gerar_mar()
    print("arte gerada em", SAIDA)
