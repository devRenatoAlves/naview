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


def montar(camadas, contorno, largura=48, altura=48, detalhes=()):
    """camadas: [(trecho_svg, paleta, com_contorno)]. detalhes: [(cor, [(x, y), ...])] por cima de tudo."""
    grade = {}
    for trecho, paleta, com_contorno in camadas:
        pixels = rasterizar(trecho, paleta, largura, altura)
        if com_contorno:
            for x, y in pixels:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = (x + dx, y + dy)
                    if v not in pixels and 0 <= v[0] < largura and 0 <= v[1] < altura:
                        grade[v] = contorno
        grade.update(pixels)
    for cor, pontos in detalhes:
        for p in pontos:
            grade[p] = cor
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

    Devolve (svg, deslocamento): o deslocamento converte coordenadas do desenho para o quadro.
    """
    x0, y0, x1, y1 = caixa(grade)
    dx = (lado - (x1 - x0 + 1)) // 2 - x0
    dy = lado - 1 - y1
    rects = svg(grade, dx, dy)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" '
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
