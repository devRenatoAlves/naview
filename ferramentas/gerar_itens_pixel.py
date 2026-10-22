#!/usr/bin/env python3
"""Baús, moeda e petisco do jogo em pixel art (arte própria, desenhada por código).

Gera arte/baus/<tipo>.svg, arte/jogo/moeda.svg e arte/jogo/petisco.svg. Cada desenho é uma grade de
pixels: as formas são montadas por regras simples (tampa, corpo, cintas, fecho), o contorno é
calculado em volta e cada baú só troca a paleta. Rodar de novo só se mudar algum desenho.
"""
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "arte"


def retangulo(grade, x0, y0, x1, y1, cor):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grade[(x, y)] = cor


def contorno(grade, cor):
    """Pinta de 'cor' todo vizinho vazio de um pixel (por fora do desenho)."""
    novos = {}
    for (x, y) in grade:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = (x + dx, y + dy)
            if v not in grade:
                novos[v] = cor
    grade.update(novos)


def svg_pixels(grade, margem=0):
    xs = [x for x, _ in grade]
    ys = [y for _, y in grade]
    x0, y0 = min(xs) - margem, min(ys) - margem
    larg, alt = max(xs) - x0 + 1 + margem, max(ys) - y0 + 1 + margem
    retangulos = []
    for y in sorted({y for _, y in grade}):
        linha = sorted(x for x, yy in grade if yy == y)
        i = 0
        while i < len(linha):
            fim = i
            cor = grade[(linha[i], y)]
            while fim + 1 < len(linha) and linha[fim + 1] == linha[fim] + 1 and grade[(linha[fim + 1], y)] == cor:
                fim += 1
            retangulos.append(f'<rect x="{linha[i] - x0}" y="{y - y0}" width="{fim - i + 1}" height="1" fill="{cor}"/>')
            i = fim + 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {larg} {alt}" shape-rendering="crispEdges">'
            + "".join(retangulos) + "</svg>\n")


# tampa/corpo: (principal, luz, sombra); metal: (principal, luz, sombra); gema; brilho (estrelinhas);
# interior: cor do brilho de dentro do baú aberto
BAUS = {
    "madeira": dict(tampa=("#b06a30", "#d8903f", "#8a4e22"), corpo=("#9a5a28", "#b87a3a", "#6e3c1a"),
                    metal=("#aab2bd", "#e3e9f0", "#6f7884"), gema=None, brilho=None, interior="#ffe08a"),
    "prata": dict(tampa=("#8d99ad", "#c9d3e3", "#66728a"), corpo=("#7d899e", "#a3aec2", "#56627a"),
                  metal=("#e9eef5", "#ffffff", "#a3adbd"), gema="#4a8cff", brilho=None, interior="#cfe3ff"),
    "ouro": dict(tampa=("#e0a712", "#ffd95e", "#a97100"), corpo=("#cf9710", "#efbc34", "#8f6000"),
                 metal=("#fff0a8", "#ffffff", "#d9ad40"), gema="#e53935", brilho=None, interior="#fff2a0"),
    "magico": dict(tampa=("#7d4ccf", "#ab7df2", "#55309f"), corpo=("#6d3fba", "#8f64df", "#4a2889"),
                   metal=("#f5b81b", "#ffe38a", "#b07c00"), gema="#4de3ff", brilho="#e8d9ff", interior="#8ff0ff"),
    "lendario": dict(tampa=("#233a8f", "#4766dc", "#14215c"), corpo=("#1c3079", "#3350be", "#0f1a4a"),
                     metal=("#ffd45a", "#fff3b0", "#cf9610"), gema="#ff4d9a", brilho="#fff3b0", interior="#ffb0dd"),
}
L, A = 32, 28


def _ret(g, x0, y0, x1, y1, cor):
    retangulo(g, x0, y0, x1, y1, cor)


def _corpo_comum(p, aberto):
    """Corpo do baú (igual aberto ou fechado): tábuas, cantoneiras, pés e cintas."""
    g = {}
    corpo, metal = p["corpo"], p["metal"]
    _ret(g, 2, 13, 29, 24, corpo[0])
    _ret(g, 2, 13, 3, 24, corpo[1])                                   # luz na esquerda
    _ret(g, 28, 13, 29, 24, corpo[2])                                 # sombra na direita
    _ret(g, 2, 23, 29, 24, corpo[2])                                  # base escura
    for x in (10, 15, 20):                                            # frestas das tábuas
        _ret(g, x, 15, x, 22, corpo[2])
    _ret(g, 5, 25, 8, 26, corpo[2])                                   # pés
    _ret(g, 23, 25, 26, 26, corpo[2])
    for x0 in (2, 26):                                                # cantoneiras de metal
        _ret(g, x0, 13, x0 + 3, 17, metal[0])
        _ret(g, x0, 13, x0 + 3, 13, metal[1])
        _ret(g, x0, 17, x0 + 3, 17, metal[2])
        g[(x0 + 1, 15)] = metal[1]
    for x0 in (7, 22):                                                # cintas verticais do corpo
        _ret(g, x0, 13, x0 + 2, 24, metal[0])
        _ret(g, x0, 13, x0, 24, metal[1])
        _ret(g, x0 + 2, 13, x0 + 2, 24, metal[2])
        g[(x0 + 1, 15)] = metal[1]
        g[(x0 + 1, 21)] = metal[1]
    return g


def desenhar_bau(p, aberto=False):
    g = {}
    tampa, corpo, metal = p["tampa"], p["corpo"], p["metal"]
    if not aberto:
        # tampa abaulada fechada (y 2..12)
        for y in range(2, 13):
            recuo = {2: 6, 3: 3, 4: 2, 5: 1}.get(y, 0)
            _ret(g, 2 + recuo, y, 29 - recuo, y, tampa[0])
        _ret(g, 8, 3, 23, 3, tampa[1])
        _ret(g, 5, 4, 6, 4, tampa[1])
        _ret(g, 25, 4, 26, 4, tampa[1])
        _ret(g, 3, 5, 4, 11, tampa[1])
        _ret(g, 28, 7, 29, 11, tampa[2])
        for x in (10, 15, 20):                                         # frestas da tampa
            _ret(g, x, 5, x, 11, tampa[2])
        _ret(g, 2, 11, 29, 12, tampa[2])
        # aro de metal na junta
        _ret(g, 2, 11, 29, 12, metal[0])
        _ret(g, 2, 11, 29, 11, metal[1])
        _ret(g, 2, 12, 29, 12, metal[2])
        for x in range(4, 29, 4):
            g[(x, 11)] = "#ffffff" if metal[1] != "#ffffff" else metal[0]
        g.update(_corpo_comum(p, False))
        for x0 in (7, 22):                                             # cintas da tampa
            _ret(g, x0, 3, x0 + 2, 12, metal[0])
            _ret(g, x0, 4, x0, 12, metal[1])
            _ret(g, x0 + 2, 4, x0 + 2, 12, metal[2])
            g[(x0 + 1, 7)] = metal[1]
        fecho_y = 10
    else:
        # interior aberto: brilho + moedas/gemas saindo
        _ret(g, 3, 8, 28, 13, "#1c120c")
        _ret(g, 5, 9, 26, 12, p["interior"])
        _ret(g, 9, 8, 22, 10, "#ffffff")
        for x, y, c in ((7, 9, "#f5b81b"), (11, 8, "#f5b81b"), (15, 7, "#ffffff"), (19, 8, "#f5b81b"),
                        (23, 9, "#f5b81b"), (13, 9, p["gema"] or "#e53935"), (17, 9, "#f5b81b")):
            g[(x, y)] = c
            g[(x + 1, y)] = c
        g.update(_corpo_comum(p, True))
        _ret(g, 2, 13, 29, 13, metal[0])                               # aro da boca do baú
        _ret(g, 2, 13, 29, 13, metal[1])
        # tampa levantada, vista por trás (acima do interior)
        _ret(g, 5, 0, 26, 0, tampa[2])
        _ret(g, 4, 1, 27, 5, tampa[0])
        _ret(g, 4, 1, 27, 1, tampa[1])
        _ret(g, 4, 5, 27, 5, tampa[2])
        for x0 in (8, 21):
            _ret(g, x0, 1, x0 + 2, 5, metal[0])
        fecho_y = 15
    # fecho central
    _ret(g, 13, fecho_y, 18, fecho_y + 7, metal[0])
    _ret(g, 13, fecho_y, 18, fecho_y, metal[1])
    _ret(g, 13, fecho_y + 7, 18, fecho_y + 7, metal[2])
    _ret(g, 13, fecho_y, 13, fecho_y + 7, metal[1])
    if p["gema"]:
        _ret(g, 14, fecho_y + 2, 17, fecho_y + 5, p["gema"])
        g[(14, fecho_y + 2)] = "#ffffff"
        _ret(g, 17, fecho_y + 5, 17, fecho_y + 5, "#00000055" if False else metal[2])
    else:
        _ret(g, 15, fecho_y + 2, 16, fecho_y + 3, "#2c1b12")
        _ret(g, 15, fecho_y + 4, 16, fecho_y + 5, "#2c1b12")
    contorno(g, "#120a06")
    if p["brilho"]:
        for cx, cy in ((1, 5), (30, 3), (29, 20), (3, 22)):
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                g.setdefault((cx + dx, cy + dy), p["brilho"])
    return g


MOEDA = """
....KKKKKK....
..KKYYYYYYKK..
.KYYYWWYYYYYK.
.KYWYYYYYYDYK.
KYWYYYOOYYYDYK
KYYYYOYYOYYYDK
KYYYYOYYYYYYDK
KYYYYOYYOYYYDK
KYYYYYOOYYYDYK
.KYYYYYYYYDYK.
.KYYYYYYDDYYK.
..KKDDDDDDKK..
....KKKKKK....
"""
PALETA_MOEDA = {"K": "#120a06", "Y": "#f5b81b", "W": "#fff3b0", "D": "#c98a00", "O": "#a06500"}

PETISCO = """
....KKKKKK....
..KKCCCCCCKK..
.KCCCCDCCCCCK.
.KCDCCCCCCDCK.
KCCCCCCDCCCCCK
KCCDCCCCCCCDCK
KCCCCCCCCDCCCK
KCDCCCDCCCCCCK
KCCCCCCCCCDCCK
.KCCDCCCCCCCK.
.KCCCCCCDCCCK.
..KKCCCCCCKK..
....KKKKKK....
"""
PALETA_PETISCO = {"K": "#120a06", "C": "#d9964a", "D": "#6b3a1a"}


def de_mapa(mapa, paleta):
    g = {}
    for y, linha in enumerate(mapa.strip("\n").split("\n")):
        for x, c in enumerate(linha):
            if c != ".":
                g[(x, y)] = paleta[c]
    return g


def main():
    (SAIDA / "baus").mkdir(parents=True, exist_ok=True)
    (SAIDA / "jogo").mkdir(parents=True, exist_ok=True)
    for nome, paleta in BAUS.items():
        (SAIDA / "baus" / f"{nome}.svg").write_text(svg_pixels(desenhar_bau(paleta)))
        (SAIDA / "baus" / f"{nome}_aberto.svg").write_text(svg_pixels(desenhar_bau(paleta, aberto=True)))
    (SAIDA / "jogo" / "moeda.svg").write_text(svg_pixels(de_mapa(MOEDA, PALETA_MOEDA)))
    (SAIDA / "jogo" / "petisco.svg").write_text(svg_pixels(de_mapa(PETISCO, PALETA_PETISCO)))
    print(len(BAUS), "baús, moeda e petisco em", SAIDA)


if __name__ == "__main__":
    main()
