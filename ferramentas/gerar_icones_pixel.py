#!/usr/bin/env python3
"""Ícones em pixel art da página do jogo (web/icones.js). Arte própria, desenhada pixel a pixel.

Cada ícone é um desenho em texto: "X" pinta com a cor do texto em volta, "o" com a mesma cor mais
fraca (sombra/detalhe) e "." deixa vazio. A página usa window.ic("nome", "classe") e a cor vem do
CSS (currentColor), como acontecia com os ícones Phosphor, que continuam só no GTK
(ferramentas/gerar_icones.py).
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
L = 11  # lado da grade


def circulo(raio=5.0, buraco=None):
    """Disco (ou anel, se 'buraco' for o raio de dentro) na grade L x L."""
    c = (L - 1) / 2
    linhas = []
    for y in range(L):
        linha = ""
        for x in range(L):
            d = math.hypot(x - c, y - c)
            linha += "X" if d <= raio and (buraco is None or d >= buraco) else "."
        linhas.append(linha)
    return linhas


def _marcar(linhas, pontos, c):
    g = [list(l) for l in linhas]
    for x, y in pontos:
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            g[y][x] = c
    return ["".join(l) for l in g]


def _proibido():
    return _marcar(circulo(5.2, 3.7), [(i, i) for i in range(1, 10)], "X")


def _lua():
    c = (L - 1) / 2
    linhas = []
    for y in range(L):
        linha = ""
        for x in range(L):
            dentro = math.hypot(x - c + 0.3, y - c) <= 5.0 and math.hypot(x - c - 2.4, y - c + 1.6) > 4.0
            linha += "X" if dentro else "."
        linhas.append(linha)
    return _marcar(linhas, [(8, 2), (8, 1), (8, 3), (7, 2), (9, 2), (9, 7), (9, 8), (9, 6)], "X")


ICONES = {
    "x": """
...........
.XX.....XX.
..XX...XX..
...XX.XX...
....XXX....
.....X.....
....XXX....
...XX.XX...
..XX...XX..
.XX.....XX.
...........""",
    "check": """
...........
...........
.........XX
........XXX
.......XXX.
XX....XXX..
XXX..XXX...
.XXXXXXX...
..XXXXX....
...XXX.....
...........""",
    "heart": """
...........
.XXX...XXX.
XXXXX.XXXXX
XXXXXXXXXXX
XXXXXXXXXXX
XXXXXXXXXXX
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...
....XXX....
.....X.....""",
    "star": """
.....X.....
.....X.....
....XXX....
XXXXXXXXXXX
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...
..XXXXXXX..
..XXX.XXX..
.XXX...XXX.
.XX.....XX.""",
    "coins": """
...XXXXX...
..XXXXXXX..
.XXoooooXX.
XXXoXXXoXXX
XXXoXXXoXXX
XXXoXXXoXXX
XXXoXXXoXXX
XXXoXXXoXXX
.XXoooooXX.
..XXXXXXX..
...XXXXX...""",
    "fire": """
.....X.....
....XX.....
....XXX..X.
...XXXX.XX.
..XXXXXXXX.
..XXXooXXXX
.XXXXooXXXX
.XXXXoooXXX
.XXXXoooXXX
..XXXoooXX.
...XXXXXX..""",
    "lightning": """
......XXX..
.....XXX...
....XXX....
...XXX.....
..XXXXXXX..
.....XXX...
....XXX....
...XX......
...X.......
..X........
...........""",
    "smiley": """
...XXXXX...
..X.....X..
.X.......X.
X..X...X..X
X..X...X..X
X.........X
X.X.....X.X
.X.XXXXX.X.
..X.....X..
...XXXXX...""",
    "smiley-meh": """
...XXXXX...
..X.....X..
.X.......X.
X..X...X..X
X..X...X..X
X.........X
X.........X
.X..XXX..X.
..X.....X..
...XXXXX...""",
    "smiley-sad": """
...XXXXX...
..X.....X..
.X.......X.
X..X...X..X
X..X...X..X
X.........X
X..XXXXX..X
.X.X...X.X.
..X.....X..
...XXXXX...""",
    "cookie": """
...XXXXX...
..XXXXXXX..
.XX.XXXX.XX
XXXXXXXXXXX
XXXXX.XXXXX
XX.XXXXXXXX
XXXXXXX.XXX
.XXX.XXXXX.
..XXXXXXX..
...XXXXX...""",
    "tennis-ball": """
...XXXXX...
..XXXXXXX..
.XooXXXXXX.
XXoXXXXXXXX
XXXXXXXXXXX
XXXXXXXXXXX
XXXXXXXXXXX
XXXXXXXXXXX
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...""",
    "gift": """
..XXX.XXX..
.XX.XXX.XX.
..XXXXXXX..
XXXXXXXXXXX
XXXXX.XXXXX
XXXXX.XXXXX
.XXXX.XXXX.
.XXXX.XXXX.
.XXXX.XXXX.
.XXXXXXXXX.""",
    "cards": """
...XXXXXXXX
...X......X
...X......X
XXXXXXXX..X
X......X..X
X..XX..X..X
X.XXXX.X..X
X..XX..X..X
X......XXXX
XXXXXXXX...""",
    "paw-print": """
...XX.XX...
..XXX.XXX..
..XXX.XXX..
XX.XXXXX.XX
XX.XXXXX.XX
...XXXXX...
..XXXXXXX..
.XXXXXXXXX.
.XXX...XXX.
..XX...XX..""",
    "storefront": """
.XXXXXXXXX.
XXXXXXXXXXX
XoXoXoXoXoX
XoXoXoXoXoX
.XXXXXXXXX.
.X.......X.
.X.XXXXX.X.
.X.X...X.X.
.X.X...X.X.
.X.X...X.X.
XXXXXXXXXXX""",
    "pencil-simple": """
........XX.
.......XXXX
......XXXX.
.....XXXX..
....XXXX...
...XXXX....
..XXXX.....
.XXXX......
.XXX.......
XXX........""",
    "play": """
.XX........
.XXXX......
.XXXXXX....
.XXXXXXXX..
.XXXXXXXXXX
.XXXXXXXX..
.XXXXXX....
.XXXX......
.XX........""",
    "lock-simple": """
...XXXXX...
..XX...XX..
..X.....X..
..X.....X..
.XXXXXXXXX.
.XXXXXXXXX.
.XXXX.XXXX.
.XXXX.XXXX.
.XXXXXXXXX.
.XXXXXXXXX.""",
    "crown": """
X....X....X
XX..XXX..XX
XXX.XXX.XXX
XXXXXXXXXXX
XXXXXXXXXXX
.XXXXXXXXX.
XXXXXXXXXXX""",
    "egg": """
....XXX....
...XXXXX...
..XXXXXXX..
..XXXXXXX..
.XXXXXXXXX.
.XXXXXXXXX.
.XXXXXXXXX.
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...""",
    "egg-crack": """
....XXX....
...XXXXX...
..XXXXXXX..
..XXX.XXX..
.XXX.X.XXX.
.XX.XXX.XX.
.XXXXXXXXX.
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...""",
    "hand-tap": """
....XX.....
....XX.....
....XX.....
....XXXX...
..XXXXXXXX.
.XXXXXXXXXX
.XXXXXXXXXX
.XXXXXXXXX.
..XXXXXXX..
...XXXXX...""",
    "arrow-fat-up": """
.....X.....
....XXX....
...XXXXX...
..XXXXXXX..
.XXXXXXXXX.
...XXXXX...
...XXXXX...
...XXXXX...
...XXXXX...""",
    "sparkle": """
.....X.....
.....X.....
....XXX....
....XXX....
..XXXXXXX..
XXXXXXXXXXX
..XXXXXXX..
....XXX....
....XXX....
.....X.....
.....X.....""",
    "sun": """
.....X.....
.X...X...X.
..X.....X..
...XXXXX...
...XXXXX...
XX.XXXXX.XX
...XXXXX...
...XXXXX...
..X.....X..
.X...X...X.
.....X.....""",
    "speaker-high": """
.....X.....
....XX..X..
..XXXX...X.
XXXXXX.X.X.
XXXXXX.X.X.
XXXXXX.X.X.
..XXXX...X.
....XX..X..
.....X.....""",
    "speaker-slash": """
.....X.....
....XX.....
..XXXX.X.X.
XXXXXX..X..
XXXXXX.X.X.
XXXXXX.....
..XXXX.....
....XX.....
.....X.....""",
}
ICONES["prohibit"] = "\n".join(_proibido())
ICONES["moon-stars"] = "\n".join(_lua())


def svg_icone(mapa):
    linhas = mapa.strip("\n").split("\n")
    larg = max(len(l) for l in linhas)
    retangulos = []
    for y, linha in enumerate(linhas):
        for tom, atributo in (("X", ""), ("o", ' opacity="0.55"')):
            x = 0
            while x < len(linha):
                if linha[x] == tom:
                    fim = x
                    while fim + 1 < len(linha) and linha[fim + 1] == tom:
                        fim += 1
                    retangulos.append(f'<rect x="{x}" y="{y}" width="{fim - x + 1}" height="1"{atributo}/>')
                    x = fim + 1
                else:
                    x += 1
    return larg, len(linhas), "".join(retangulos)


def main():
    saida = {}
    for nome, mapa in ICONES.items():
        larg, alt, corpo = svg_icone(mapa)
        saida[nome] = [larg, alt, corpo]
    (RAIZ / "web" / "icones.js").write_text(
        "// Gerado por ferramentas/gerar_icones_pixel.py (arte própria, pixel art).\n"
        f"window.ICONES = {json.dumps(saida, indent=0)};\n"
        "window.ic = (nome, classe = \"\") => {\n"
        "  const i = window.ICONES[nome];\n"
        "  if (!i) { console.warn(`Ícone desconhecido: ${nome}`); return \"\"; }\n"
        "  return `<svg class=\"ic ${classe}\" viewBox=\"0 0 ${i[0]} ${i[1]}\" fill=\"currentColor\" "\
        "shape-rendering=\"crispEdges\" aria-hidden=\"true\">${i[2]}</svg>`;\n"
        "};\n")
    print(len(saida), "ícones")


if __name__ == "__main__":
    main()
