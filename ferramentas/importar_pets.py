"""Gera os pets que vieram como imagens (GIFs animados e PNGs de pixel art) em arte/pets/.

Os originais ficam em ferramentas/originais_pets/. Para cada pet:
  arte/pets/<pet>.svg        quadro parado (o primeiro do GIF), usado no rodapé, nas cartas e na primeira imagem
  arte/pets/<pet>_q<i>.png   todos os quadros da animação (só nos GIFs), que a página troca no ritmo do GIF;
                             PNG decodifica bem mais leve que SVG a cada troca

Todos os quadros de um pet usam o mesmo deslocamento no quadro de 64 x 64 (caixa que cobre todos
eles), para o pet não tremer quando a página troca de quadro. Imprime o que o catálogo precisa
(ALTURA_EXTRA, QUADROS e o deslocamento da cabeça em cada quadro, para os acessórios acompanharem).

Rodar com /usr/bin/python3 (precisa do gi) e Pillow: python3 ferramentas/importar_pets.py
"""
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel_vetor import caixa, svg  # noqa: E402

RAIZ = Path(__file__).resolve().parent
ORIGINAIS = RAIZ / "originais_pets"
SAIDA = RAIZ.parent / "arte" / "pets"
LADO = 64

# nome -> (arquivo, passo da célula, fase x, fase y) para PNGs em células; GIFs não precisam.
PETS = {
    "gato": ("gato.gif",),
    "jonatas": ("jonatas.gif",),
    "astronauta": ("astronauta.gif",),
    "dragao": ("dragao.gif",),
    "galinha": ("galinha.png", 10, 5, 0),
    "slime": ("slime.png", 18, 6, 6),
}
# Cores que são só ruído do GIF original (pixels soltos): cada pixel vira a cor mais comum dos vizinhos,
# ou some se estiver quase todo cercado de transparência.
RUIDO = {"gato": {"#97119d", "#340b45"}}
# Colunas a cortar (x_min, x_max do desenho original) quando o desenho passa de 64 de largura.
RECORTE_X = {"dragao": (29, 92)}


def hexa(rgb):
    return "#%02x%02x%02x" % tuple(rgb[:3])


def quadros_gif(caminho):
    gif = Image.open(caminho)
    quadros = []
    for i in range(gif.n_frames):
        gif.seek(i)
        rgba = gif.convert("RGBA")
        px = rgba.load()
        quadros.append({(x, y): hexa(px[x, y]) for y in range(rgba.height) for x in range(rgba.width)
                        if px[x, y][3] >= 128})
    return quadros


def quadro_png(caminho, passo, fx, fy):
    """Uma célula = um pixel. Tira a moldura rosa e o fundo branco de fora; o branco de dentro fica."""
    img = Image.open(caminho).convert("RGB")
    px = img.load()
    cols, linhas = (img.width - fx) // passo, (img.height - fy) // passo
    celulas = {}
    for j in range(linhas):
        for i in range(cols):
            cor = px[fx + i * passo + passo // 2, fy + j * passo + passo // 2]
            celulas[(i, j)] = cor
    branco = (255, 255, 255)
    # a moldura rosa é a cor que domina as bordas da imagem
    borda = Counter(celulas[(i, j)] for (i, j) in celulas if i in (0, cols - 1) or j in (0, linhas - 1))
    moldura = [c for c, _ in borda.most_common(3) if c != branco]
    fora, fila = set(), [(1, 1)]
    while fila:  # inunda o branco ligado ao canto (o de fora do desenho)
        p = fila.pop()
        if p in fora or p not in celulas or celulas[p] != branco and celulas[p] not in moldura:
            continue
        fora.add(p)
        fila += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
    grade = {p: hexa(c) for p, c in celulas.items() if p not in fora and c not in moldura}
    return [grade]


def tirar_ruido(grade, cores):
    novo = dict(grade)
    for (x, y), cor in grade.items():
        if cor not in cores:
            continue
        viz = [grade.get((x + i, y + j)) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)]
        boas = [c for c in viz if c and c not in cores]
        if len(boas) < 4:
            del novo[(x, y)]
        else:
            novo[(x, y)] = Counter(boas).most_common(1)[0][0]
    return novo


def cabeca(grade):
    """(x do centro do alto, y do alto) do desenho: onde o chapéu assenta."""
    x0, y0, x1, y1 = caixa(grade)
    xs = [x for (x, y) in grade if y <= y0 + 6]
    return sum(xs) / len(xs), y0


def importar(nome):
    arquivo, *celula = PETS[nome]
    caminho = ORIGINAIS / arquivo
    quadros = quadro_png(caminho, *celula) if celula else quadros_gif(caminho)
    if nome in RUIDO:
        quadros = [tirar_ruido(q, RUIDO[nome]) for q in quadros]
    if nome in RECORTE_X:
        a, b = RECORTE_X[nome]
        quadros = [{p: c for p, c in q.items() if a <= p[0] <= b} for q in quadros]
    caixas = [caixa(q) for q in quadros]
    x0, y0 = min(c[0] for c in caixas), min(c[1] for c in caixas)
    x1, y1 = max(c[2] for c in caixas), max(c[3] for c in caixas)
    if x1 - x0 + 1 > LADO:
        raise SystemExit(f"{nome}: {x1 - x0 + 1} px de largura, passa do quadro de {LADO}")
    dx = (LADO - (x1 - x0 + 1)) // 2 - x0
    dy = LADO - 1 - y1
    extra = max(0, -(y0 + dy))
    for i, q in enumerate(quadros):
        corpo = "".join(svg(q, dx, dy))
        texto = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-extra} {LADO} {LADO + extra}" '
                 f'shape-rendering="crispEdges">{corpo}</svg>')
        if i == 0:
            (SAIDA / f"{nome}.svg").write_text(texto)
        if len(quadros) > 1:  # a página troca de quadro 8 vezes por segundo: PNG decodifica bem mais leve que SVG
            png = Image.new("RGBA", (LADO, LADO + extra), (0, 0, 0, 0))
            for (x, y), cor in q.items():
                png.putpixel((x + dx, y + dy + extra), tuple(int(cor[k:k + 2], 16) for k in (1, 3, 5)) + (255,))
            png.save(SAIDA / f"{nome}_q{i}.png", optimize=True)
    base = cabeca(quadros[0])
    desloc = [(round(cabeca(q)[0] - base[0]), cabeca(q)[1] - base[1]) for q in quadros]
    print(f"{nome}: {len(quadros)} quadro(s), desenho {x1 - x0 + 1}x{y1 - y0 + 1}, deslocamento {dx},{dy}, "
          f"altura extra {extra}")
    print(f"  topo do quadro 0 no quadro do pet: x={base[0] + dx:.1f} y={base[1] + dy}")
    if len(quadros) > 1:
        print(f"  deslocamento da cabeça por quadro: {desloc}")
    return quadros, (dx, dy)


if __name__ == "__main__":
    for nome in (sys.argv[1:] or PETS):
        importar(nome)
