"""Pixel art a partir de formas vetoriais: cada camada vira pixels sem suavização, com cores fixas.

Cada camada é um trecho de SVG (na grade final, 1 unidade = 1 pixel), a paleta da camada e se ela
ganha contorno. O contorno é desenhado por fora de cada camada, por cima das que vêm antes, o que
também separa as partes do corpo (cabeça sobre o corpo, braço sobre a barriga).
"""
import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gio, GLib  # noqa: E402


def _rgb(cor):
    return tuple(int(cor[i:i + 2], 16) for i in (1, 3, 5))


def rasterizar(fragmento, paleta, largura, altura):
    """{(x, y): cor} dos pixels opacos do trecho de SVG, cada um trocado pela cor mais próxima da paleta."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" width="{largura}" '
           f'height="{altura}" shape-rendering="crispEdges">{fragmento}</svg>').encode()
    fluxo = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(svg))
    pb = GdkPixbuf.Pixbuf.new_from_stream(fluxo, None)
    px, passo, canais = pb.get_pixels(), pb.get_rowstride(), pb.get_n_channels()
    cores = [(c, _rgb(c)) for c in paleta]
    pixels = {}
    for y in range(altura):
        for x in range(largura):
            i = y * passo + x * canais
            if canais == 4 and px[i + 3] < 128:
                continue
            rgb = (px[i], px[i + 1], px[i + 2])
            pixels[(x, y)] = min(cores, key=lambda c: sum((a - b) ** 2 for a, b in zip(c[1], rgb)))[0]
    return pixels


class Grade(dict):
    """{(x, y): cor} de um desenho, com o que o piscar precisa: o desenho sem os detalhes (base) e os
    olhos (cx, y, alto) registrados por desenhos_pets.olhos()."""
    base = None
    olhos = ()
    expressoes = None  # {"pisca": Grade, ...} quando as caras foram desenhadas à mão (ex.: Fredinho)


def escurecer(cor, fator, mistura, contorno):
    """Contorno seletivo: a cor do vizinho escurecida e misturada um pouco com o contorno fixo, para a
    borda acompanhar a cor de cada parte (laranja do pelo, verde do slime) em vez de um preto só."""
    c = _rgb(cor)
    k = _rgb(contorno)
    return "#%02x%02x%02x" % tuple(round(a * fator * (1 - mistura) + b * mistura) for a, b in zip(c, k))


def montar(camadas, contorno, largura=48, altura=48, detalhes=(), olhos=()):
    """camadas: [(trecho_svg, paleta, com_contorno)]. detalhes: [(cor, [(x, y), ...])] por cima de tudo."""
    grade = Grade()
    for trecho, paleta, com_contorno in camadas:
        pixels = rasterizar(trecho, paleta, largura, altura)
        if com_contorno:
            for (x, y), cor in pixels.items():
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = (x + dx, y + dy)
                    if v not in pixels and 0 <= v[0] < largura and 0 <= v[1] < altura:
                        grade[v] = escurecer(cor, 0.5, 0.35, contorno)
        grade.update(pixels)
    grade.base = Grade(grade)
    for cor, pontos in detalhes:
        for p in pontos:
            grade[p] = cor
    grade.olhos = tuple(olhos)
    return grade


def _olho(o):
    """Olho registrado como (cx, y, alto) ou (cx, y, alto, meia-largura); sempre devolve os quatro."""
    return o if len(o) == 4 else (*o, 1)


def _sem_olhos(grade):
    novo = Grade(grade)
    for cx, y, alto, meia in map(_olho, grade.olhos):
        for dy in range(alto):
            for dx in range(-meia, meia + 1):
                p = (cx + dx, y + dy)
                if p in grade.base:
                    novo[p] = grade.base[p]
                else:
                    novo.pop(p, None)
    return novo


def expressao(grade, tipo, cor="#1b1b1b"):
    """O mesmo desenho com outra cara (None se o pet não tem olhos registrados, como os Pokémon).

    pisca: olhos fechados em traço (também serve para dormindo); feliz: olhos em arco "^";
    triste: olhos normais com uma lágrima."""
    if grade.expressoes is not None:
        return grade.expressoes.get(tipo)
    if not grade.olhos:
        return None
    if tipo == "triste":
        novo = Grade(grade)
        for cx, y, alto, meia in map(_olho, grade.olhos):
            novo[(cx + meia, y + alto)] = "#6ec8ff"
            novo[(cx + meia, y + alto + 1)] = "#6ec8ff"
            novo[(cx - meia, y)] = cor  # canto de cima mais caído: olhar abatido
        return novo
    novo = _sem_olhos(grade)
    for cx, y, alto, meia in map(_olho, grade.olhos):
        if tipo == "pisca":
            for dx in range(-meia, meia + 1):
                novo[(cx + dx, y + alto - 2)] = cor
        elif tipo == "feliz":
            for p in ((cx - meia, y + alto - 2), (cx - meia + 1, y + alto - 3), (cx, y + alto - 3),
                      (cx + meia - 1, y + alto - 3), (cx + meia, y + alto - 2),
                      (cx - meia, y + alto - 1), (cx + meia, y + alto - 1)):
                novo[p] = cor
    return novo


def de_mapa(mapa, paleta):
    """{(x, y): cor} de um desenho em texto: um caractere por pixel, "." = vazio."""
    grade = {}
    for y, linha in enumerate(mapa.strip("\n").split("\n")):
        for x, c in enumerate(linha):
            if c != ".":
                grade[(x, y)] = paleta[c]
    return grade


def sombreado(forma, base, sombra, luz="", dx=-1.2, dy=-1.4, id_="s"):
    """Forma na cor da sombra com a cor base deslocada para cima e para a esquerda por dentro.

    O resultado é uma sombra em blocos embaixo e à direita, como nos sprites de videogame.
    luz: trecho de SVG extra (brilho), recortado pela forma.
    """
    def cor(c):
        return forma.replace("/>", f' fill="{c}"/>')
    return (f'<clipPath id="{id_}">{forma}</clipPath>{cor(sombra)}'
            f'<g clip-path="url(#{id_})" transform="translate({dx} {dy})">{cor(base)}</g>'
            + (f'<g clip-path="url(#{id_})">{luz}</g>' if luz else ""))


def svg(grade, dx=0, dy=0):
    """Retângulos SVG dos pixels (junta vizinhos da mesma cor na linha). dx, dy deslocam o desenho."""
    rects = []
    for y in sorted({y for _, y in grade}):
        xs = sorted(x for x, yy in grade if yy == y)
        i = 0
        while i < len(xs):
            x, cor = xs[i], grade[(xs[i], y)]
            fim = i
            while fim + 1 < len(xs) and xs[fim + 1] == xs[fim] + 1 and grade[(xs[fim + 1], y)] == cor:
                fim += 1
            rects.append(f'<rect x="{x + dx}" y="{y + dy}" width="{fim - i + 1}" height="1" fill="{cor}"/>')
            i = fim + 1
    return rects


def caixa(grade):
    xs = [x for x, _ in grade]
    ys = [y for _, y in grade]
    return min(xs), min(ys), max(xs), max(ys)


def no_quadro(grade, lado=64):
    """Coloca o desenho num quadro lado x lado, centrado na horizontal e encostado embaixo.

    Desenho mais alto que o quadro (ex.: Fredinho, com 71) passa do topo: o SVG ganha essas linhas a
    mais em cima (viewBox com y negativo) e a página o posiciona com ALTURA_EXTRA do catálogo.
    Devolve (svg, deslocamento): o deslocamento converte coordenadas do desenho para o quadro.
    """
    x0, y0, x1, y1 = caixa(grade)
    dx = (lado - (x1 - x0 + 1)) // 2 - x0
    dy = lado - 1 - y1
    extra = max(0, -(y0 + dy))
    rects = svg(grade, dx, dy)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-extra} {lado} {lado + extra}" '
            f'shape-rendering="crispEdges">{"".join(rects)}</svg>'), (dx, dy)


def de_imagem(caminho):
    """{(x, y): cor} dos pixels opacos de uma imagem (ex.: sprite PNG)."""
    pb = GdkPixbuf.Pixbuf.new_from_file(str(caminho)).add_alpha(False, 0, 0, 0)
    px, passo = pb.get_pixels(), pb.get_rowstride()
    grade = {}
    for y in range(pb.get_height()):
        for x in range(pb.get_width()):
            i = y * passo + x * 4
            if px[i + 3] >= 128:
                grade[(x, y)] = "#%02x%02x%02x" % (px[i], px[i + 1], px[i + 2])
    return grade


class Tela:
    """Pincel de pixels: formas preenchidas pixel a pixel (sem suavização), com luz no alto à esquerda,
    sombra embaixo à direita e contorno que acompanha a cor de cada parte. Cada forma é uma camada:
    desenha primeiro o contorno por fora dela (por cima do que já existe) e depois o preenchimento."""

    def __init__(self, contorno, largura=48, altura=48):
        self.g = Grade()
        self.contorno = contorno
        self.w, self.h = largura, altura

    def _camada(self, pixels, cor_contorno=True, cor_base=None):
        if cor_contorno:
            anel = {}
            for (x, y), c in pixels.items():
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = (x + dx, y + dy)
                    if v not in pixels and 0 <= v[0] < self.w and 0 <= v[1] < self.h:
                        anel[v] = escurecer(cor_base or c, 0.5, 0.35, self.contorno)
            self.g.update(anel)
        self.g.update(pixels)

    def elipse(self, cx, cy, rx, ry, base, luz=None, sombra=None, contorno=True):
        px = {}
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                r2 = nx * nx + ny * ny
                if r2 > 1:
                    continue
                s = nx * 0.55 + ny * 0.83
                cor = base
                if sombra and s > 0.42:
                    cor = sombra
                elif luz and s < -0.55 and r2 < 0.8:
                    cor = luz
                px[(x, y)] = cor
        self._camada(px, contorno, base)
        return px

    def poligono(self, pontos, base, luz=None, sombra=None, contorno=True):
        def dentro(x, y):
            dentro_ = False
            j = len(pontos) - 1
            for i in range(len(pontos)):
                xi, yi = pontos[i]
                xj, yj = pontos[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    dentro_ = not dentro_
                j = i
            return dentro_
        xs = [p[0] for p in pontos]
        ys = [p[1] for p in pontos]
        px = {}
        for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
            for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
                if dentro(x + 0.5, y + 0.5):
                    px[(x, y)] = base
        if sombra or luz:
            for (x, y) in list(px):
                if sombra and ((x + 1, y) not in px or (x, y + 1) not in px):
                    px[(x, y)] = sombra
                elif luz and ((x - 1, y) not in px and (x, y - 1) not in px):
                    px[(x, y)] = luz
        self._camada(px, contorno, base)
        return px

    def retangulo(self, x0, y0, x1, y1, base, sombra=None, contorno=True):
        px = {(x, y): (sombra if sombra and (x == x1 or y == y1) else base)
              for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}
        self._camada(px, contorno, base)
        return px

    def pontos(self, cor, lista):
        for p in lista:
            self.g[p] = cor

    def pronto(self, detalhes=(), olhos=()):
        """Grade final: 'base' é o desenho sem os detalhes (olhos, nariz) e 'olhos' guarda onde estão."""
        g = self.g
        g.base = Grade(g)
        for cor, lista in detalhes:
            for p in lista:
                g[p] = cor
        g.olhos = tuple(olhos)
        return g
