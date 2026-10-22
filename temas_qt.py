"""Temas na versão Qt: as cores de temas.py viram folha de estilo do Qt (QSS) e o fundo da tela
inicial vira camadas pintadas à mão (QSS não tem gradiente inclinado, sombra nem animação).

temas.py continua sendo a fonte das cores, frases, desenhos e preferências. Aqui fica só o que
é do Qt: as camadas do fundo, os detalhes de cada tema e a tradução das cores do GTK
(alpha(), shade(), @theme_*).
"""
import hashlib
import math
from pathlib import Path
from string import Template

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFontDatabase, QImage, QImageReader, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

import temas

FONTES = Path(__file__).resolve().parent / "fonts"


def carregar_fontes():
    for arquivo in sorted(FONTES.glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(arquivo))


# ---- cores ---------------------------------------------------------------------

_PALETA = {
    "@theme_bg_color": QPalette.Window, "@theme_base_color": QPalette.Base,
    "@theme_selected_bg_color": QPalette.Highlight, "@theme_fg_color": QPalette.WindowText,
    "@theme_selected_fg_color": QPalette.HighlightedText,
}


def _argumentos(texto):
    """'alpha(#fff, 0.5), 2' -> ['alpha(#fff, 0.5)', '2'] (vírgulas de fora dos parênteses)."""
    partes, nivel, atual = [], 0, ""
    for c in texto:
        if c == "," and nivel == 0:
            partes.append(atual.strip())
            atual = ""
            continue
        nivel += (c == "(") - (c == ")")
        atual += c
    partes.append(atual.strip())
    return partes


def cor(expr):
    """QColor de uma cor no formato do GTK: #hex, rgb(), rgba(), nome, @theme_*, alpha(), shade()."""
    expr = (expr or "").strip()
    if expr in _PALETA:
        return QColor(QApplication.palette().color(_PALETA[expr]))
    for funcao in ("alpha", "shade"):
        if expr.startswith(funcao + "(") and expr.endswith(")"):
            base, valor = _argumentos(expr[len(funcao) + 1:-1])
            c, v = cor(base), float(valor)
            if funcao == "alpha":
                c.setAlphaF(max(0.0, min(1.0, c.alphaF() * v)))
            else:  # shade: multiplica a luminosidade, como o GTK
                h, s, l, a = c.getHslF()
                c = QColor.fromHslF(max(0.0, h), s, max(0.0, min(1.0, l * v)), a)
            return c
    rgba = temas.ler_cor(expr)
    if rgba:
        return QColor.fromRgbF(*rgba)
    if expr == "transparent":
        return QColor(0, 0, 0, 0)
    return QColor(expr)


def qss(expr):
    c = cor(expr)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {c.alpha()})"


# ---- fundo da tela inicial ---------------------------------------------------------
#
# Camadas de baixo para cima. "linear": ângulo como no CSS (0 = para cima, 90 = para a direita);
# "radial": centro em fração da tela, raio até o canto mais longe; "imagem": arte repetida
# (lado a lado) ou solta num canto; "linhas": listras de monitor antigo.

FUNDOS = {
    "oceano": [{"linear": 160, "paradas": [(0, "alpha(#1fa2ff, 0.16)"), (0.45, "transparent"),
                                           (0.65, "transparent"), (1, "alpha(#14b8a6, 0.12)")]}],
    "pixel": [{"linear": 180, "paradas": [(0, "#6ec3ff"), (0.7, "#b9e6ff"), (1, "#b9e6ff")]}],
    "hq": [{"radial": (0.5, 0.45), "paradas": [(0, "#fff59d"), (0.6, "#ffd600"), (1, "#ffd600")]},
           {"imagem": "hq/pontos.svg", "tamanho": (14, 14), "repetir": True}],
    "espaco": [{"imagem": "espaco/nebulosa_azul.svg", "tamanho": (700, 700), "canto": "baixo-esquerda"},
               {"imagem": "espaco/nebulosa_roxa.svg", "tamanho": (700, 700), "canto": "cima-direita"},
               {"imagem": "espaco/estrelas.svg", "tamanho": (300, 300), "repetir": True}],
    "terminal": [{"radial": (0.5, 0.5), "paradas": [(0, "alpha(#33ff66, 0.08)"), (0.7, "transparent")]},
                 {"linhas": "alpha(#33ff66, 0.05)", "passo": 3}],
    "neon": [{"linear": 180, "paradas": [(0, "#14052b"), (0.55, "#2a0845"), (1, "#6a0d6b")]}],
    "mar": [{"linear": 180, "paradas": [(0, "#1e1b4b"), (0.35, "#3730a3"), (0.65, "#6366f1"), (1, "#7dd3fc")]}],
    "manga": [{"linear": 180, "paradas": [(0, "#000000"), (1, "#0a0a0a")]},
              {"capa": "manga/fundo.jpg"}],
}

# Detalhes de cada tema que o CSS do GTK fazia (bordas, sombras, tamanho do título).
# sombra: (dx, dy, desfoque, cor). titulo: tamanho em relação à fonte do tema.
PADRAO_EXTRA = {"titulo": 1.9, "titulo_cor": None, "titulo_sombra": None,
                "cartao_sombra": (0, 2, 6, "alpha(#000000, 0.18)"), "texto_decor": None, "qss": ""}
EXTRAS = {
    "vidro": {
        "cartao_sombra": (0, 3, 8, "alpha(#000000, 0.25)"),
        "qss": """
#lateral { margin: 0 0 10px 10px; border-radius: 20px; border: 1px solid rgba(255,255,255,56);
  background-color: $lateral; }
#cartao { border: 1px solid rgba(255,255,255,71); }
QLineEdit { border: 1px solid rgba(255,255,255,64); }
#abas QTabBar::tab:selected { border: 1px solid rgba(255,255,255,64); }
""",
    },
    "pixel": {
        "titulo": 1.5, "cartao_sombra": (6, 6, 0, "alpha(#1b1b1b, 0.35)"),
        "qss": """
#lateral { border-right: 4px solid #1b1b1b; }
#barra { border-bottom: 4px solid #1b1b1b; }
QLineEdit { border: 3px solid #1b1b1b; }
#raiz QLabel[avatar] { border: 2px solid #1b1b1b; }
#cartao { border: 4px solid #1b1b1b; }
QPushButton#conectar { border: 3px solid #1b1b1b; border-bottom-width: 5px; border-right-width: 5px; }
#abas QTabBar { border-bottom: 4px solid #1b1b1b; }
#abas QTabBar::tab:selected { border: 3px solid #1b1b1b; border-bottom: none; }
#contatos::item:selected { background-color: #ffd23f; }
""",
    },
    "hq": {
        "titulo": 2.4, "titulo_cor": "#e53935", "titulo_sombra": (2, 2, 0, "#111111"),
        "cartao_sombra": (10, 10, 0, "#111111"), "texto_decor": (3.2, "#ffffff", (3, 3, "#111111")),
        "qss": """
#lateral { border-right: 4px solid #111111; }
#barra { border-bottom: 4px solid #111111; }
QLineEdit { border: 3px solid #111111; }
#raiz QLabel[avatar] { border: 2px solid #111111; }
#cartao { border: 4px solid #111111; }
QPushButton#conectar { border: 3px solid #111111; }
#abas QTabBar { border-bottom: 4px solid #111111; }
#abas QTabBar::tab:selected { border: 3px solid #111111; border-bottom: none; }
#contatos::item:selected { background-color: #ffd600; }
""",
    },
    "espaco": {
        "titulo_sombra": (0, 0, 12, "alpha(#a78bfa, 0.8)"),
        "cartao_sombra": (0, 0, 14, "alpha(#7c3aed, 0.45)"),
        "qss": "#cartao { border: 1px solid rgba(167,139,250,89); }",
    },
    "terminal": {
        "titulo": 2.2, "titulo_sombra": (0, 0, 6, "alpha(#33ff66, 0.6)"), "cartao_sombra": None,
        "qss": """
#raiz QLabel[avatar] { color: #33ff66; border: 1px solid rgba(51,255,102,153); }
QLineEdit, #cartao { border: 1px solid rgba(51,255,102,115); }
#lateral { border-right: 1px solid rgba(51,255,102,77); }
#barra { border-bottom: 1px solid rgba(51,255,102,77); }
""",
    },
    "neon": {
        "titulo_cor": "#ffe0fb", "titulo_sombra": (0, 0, 18, "#ff2bd6"),
        "cartao_sombra": (0, 0, 12, "alpha(#ff2bd6, 0.6)"),
        "qss": "#cartao { background-color: rgba(20,5,43,209); border: 1px solid #ff2bd6; }",
    },
    "mar": {
        "titulo_cor": "#ffffff", "titulo_sombra": (0, 2, 8, "alpha(#1e1b4b, 0.8)"),
        "cartao_sombra": (0, 4, 14, "alpha(#1e1b4b, 0.55)"),
        "qss": """
#cartao { background-color: rgba(14,22,56,217); border: 1px solid rgba(125,211,252,115); }
#lateral { border-right: 2px solid rgba(245,158,11,128); }
""",
    },
    "manga": {
        "titulo_cor": "#ffffff", "titulo_sombra": (3, 3, 0, "alpha(#ffffff, 0.18)"),
        "cartao_sombra": (6, 6, 0, "alpha(#f5f5f5, 0.9)"),
        "qss": """
#lateral { border-right: 2px solid #f5f5f5; }
#barra { border-bottom: 2px solid #f5f5f5; }
QLineEdit { border: 1px solid rgba(245,245,245,178); }
#raiz QLabel[avatar] { border: 1px solid #f5f5f5; }
#cartao { background-color: rgba(0,0,0,217); border: 2px solid #f5f5f5; }
QPushButton#conectar { border: 2px solid #f5f5f5; }
#abas QTabBar { border-bottom: 2px solid #f5f5f5; }
#abas QTabBar::tab:selected { border: 1px solid #f5f5f5; border-bottom: none; }
#contatos::item:selected { background-color: #f5f5f5; color: #0a0a0a; }
""",
    },
}

# Molduras dos avatares (cartas do jogo). No GTK eram anéis de sombra; no QSS, bordas.
MOLDURAS = {
    "simples": "border: 2px solid $destaque;",
    "pontilhada": "border: 2px dashed $destaque;",
    "dupla": "border: 3px double #a855f7;",
    "neon": "border: 2px solid #ff2bd6;",
    "dourada": "border: 2px solid #f5b81b;",
}


def extra(chave):
    return {**PADRAO_EXTRA, **EXTRAS.get(chave, {})}


def _svg(caminho, w, h):
    imagem = QImage(int(w), int(h), QImage.Format_ARGB32_Premultiplied)
    imagem.fill(Qt.transparent)
    pintor = QPainter(imagem)
    QSvgRenderer(str(caminho)).render(pintor)
    pintor.end()
    return imagem


_cache_svg = {}


def arte_svg(nome, w, h):
    """Arte de arte/ renderizada no tamanho pedido (guardada: repintar não refaz o SVG)."""
    chave = (nome, int(w), int(h))
    if chave not in _cache_svg:
        _cache_svg[chave] = QPixmap.fromImage(_svg(temas.ARTE / nome, w, h))
    return _cache_svg[chave]


def imagem_reduzida(caminho):
    """Imagem de fundo com no máximo 1920x1080 (cópia em cache): imagens enormes pesam a cada repintura."""
    origem = Path(caminho)
    info = origem.stat()
    chave = hashlib.sha1(f"{origem.resolve()}:{info.st_mtime_ns}:{info.st_size}".encode()).hexdigest()[:16]
    destino = temas.CACHE / f"fundo-{chave}.png"
    if destino.exists():
        return destino
    leitor = QImageReader(str(origem))
    tamanho = leitor.size()
    if tamanho.width() <= temas.MAX_FUNDO[0] and tamanho.height() <= temas.MAX_FUNDO[1]:
        return origem
    leitor.setScaledSize(tamanho.scaled(*temas.MAX_FUNDO, Qt.KeepAspectRatio))
    imagem = leitor.read()
    if imagem.isNull():
        return origem
    temas.CACHE.mkdir(parents=True, exist_ok=True)
    imagem.save(str(destino), "PNG")
    return destino


def _paradas(gradiente, paradas):
    for pos, c in paradas:
        gradiente.setColorAt(pos, cor(c))


def pintar_fundo(pintor, rect, cfg):
    """Fundo da tela inicial: cor do tema + camadas (ou a imagem escolhida pela pessoa)."""
    tema = temas.TEMAS[cfg["tema"]]
    cores = temas.cores_do_tema(cfg)
    if not tema.get("vidro"):  # no vidro a tela inicial é transparente (o fundo é a janela)
        pintor.fillRect(rect, cor(cores["fundo"]))
    if cfg.get("imagem") and Path(cfg["imagem"]).is_file():
        _pintar_imagem_cobrindo(pintor, rect, cfg["imagem"])
        return
    for camada in FUNDOS.get(cfg["tema"], []):
        if "linear" in camada:
            a = math.radians(camada["linear"])
            dx, dy = math.sin(a), -math.cos(a)
            meio = abs(rect.width() * dx) / 2 + abs(rect.height() * dy) / 2
            centro = QPointF(rect.center())
            g = QLinearGradient(centro - QPointF(dx, dy) * meio, centro + QPointF(dx, dy) * meio)
            _paradas(g, camada["paradas"])
            pintor.fillRect(rect, QBrush(g))
        elif "radial" in camada:
            fx, fy = camada["radial"]
            centro = QPointF(rect.x() + rect.width() * fx, rect.y() + rect.height() * fy)
            raio = max(math.hypot(centro.x() - x, centro.y() - y)
                       for x in (rect.left(), rect.right()) for y in (rect.top(), rect.bottom()))
            g = QRadialGradient(centro, raio)
            _paradas(g, camada["paradas"])
            pintor.fillRect(rect, QBrush(g))
        elif "linhas" in camada:
            c, passo = cor(camada["linhas"]), camada["passo"]
            for y in range(rect.top(), rect.bottom(), passo):
                pintor.fillRect(rect.left(), y, rect.width(), 1, c)
        elif "capa" in camada:  # imagem de arte/ cobrindo a tela inteira
            _pintar_imagem_cobrindo(pintor, rect, temas.ARTE / camada["capa"])
        elif "imagem" in camada:
            w, h = camada["tamanho"]
            arte = arte_svg(camada["imagem"], w, h)
            if camada.get("repetir"):
                pintor.fillRect(rect, QBrush(arte))
            else:
                vertical, horizontal = camada["canto"].split("-")
                x = rect.left() if horizontal == "esquerda" else rect.right() - w
                y = rect.top() if vertical == "cima" else rect.bottom() - h
                pintor.drawPixmap(x, y, arte)


_cache_imagem = {}


def _pintar_imagem_cobrindo(pintor, rect, caminho):
    arquivo = imagem_reduzida(caminho)
    if arquivo not in _cache_imagem:
        _cache_imagem.clear()
        _cache_imagem[arquivo] = QPixmap(str(arquivo))
    imagem = _cache_imagem[arquivo]
    if imagem.isNull():
        return
    escala = max(rect.width() / imagem.width(), rect.height() / imagem.height())
    w, h = imagem.width() * escala, imagem.height() * escala
    alvo = QRectF(rect.x() + (rect.width() - w) / 2, rect.y() + (rect.height() - h) / 2, w, h)
    pintor.setRenderHint(QPainter.SmoothPixmapTransform)
    pintor.drawPixmap(alvo, imagem, QRectF(imagem.rect()))


# ---- QSS ---------------------------------------------------------------------------

BASE = Template("""
#raiz { background-color: $fundo; border-radius: 10px; }
#janela[translucida="0"] { background-color: $barra; }
#raiz[maximizada="1"], #barra[maximizada="1"] { border-radius: 0; }
QWidget#janela, QWidget#raiz QLabel { color: $texto; }

#barra { background-color: $barra; color: $texto_barra; border-top-left-radius: 10px;
  border-top-right-radius: 10px; }
#barra QLabel { color: $texto_barra; }
#barra QLabel#titulo { font-weight: bold; }
#barra QLabel#subtitulo { color: $texto_barra_fraco; font-size: ${fonte_peq}pt; }
#barra QToolButton { color: $texto_barra; background: transparent; border: none;
  border-radius: $raio_peq; min-width: 32px; min-height: 32px; }
#barra QToolButton:hover { background-color: $barra_hover; }
#barra QToolButton:checked, #barra QToolButton:pressed { background-color: $barra_marcado; }
#barra QToolButton#fecharJanela:hover { background-color: #e5484d; }

#lateral { background-color: $lateral; }
#lateral QLabel { color: $texto_lateral; }
#lateral QLabel#tituloLateral { font-weight: bold; font-size: ${fonte_lateral}pt; }
#lateral QLabel#contagem, #lateral QLabel#contatoId, #lateral QLabel#petFala { color: $texto_lateral_fraco;
  font-size: ${fonte_peq}pt; }
#lateral QLabel#contatoNome, #lateral QLabel#petNome { font-weight: bold; }
#lateral QLabel#vazio { color: $texto_lateral_fraco; padding: 24px 16px; }
#lateral QLabel#pontoOnline { color: #22c55e; font-size: ${fonte_peq}pt; }
#petRodape { border-top: 1px solid $linha_lateral; }

QLineEdit { background-color: $superficie; color: $texto; border: 1px solid $borda_campo;
  border-radius: $raio_peq; min-height: 34px; padding: 0 10px; selection-background-color: $destaque;
  selection-color: $texto_destaque; }
QLineEdit:focus { border-color: $destaque; }

#contatos { background: transparent; border: none; outline: none; }
#contatos::item { border-radius: $raio_peq; margin: 1px 8px; padding: 0; }
#contatos::item:hover { background-color: $hover_lateral; }
#contatos::item:selected { background-color: $selecao_lateral; }
#contatos QToolButton { background: transparent; border: none; border-radius: $raio_peq; }
#contatos QToolButton:hover { background-color: $hover_lateral; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: $barra_rolagem; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page { background: none;
  height: 0; }

#raiz QLabel[avatar] { border-radius: $raio_avatar; min-width: 34px; max-width: 34px; min-height: 34px;
  max-height: 34px; font-weight: bold; font-size: ${fonte_peq}pt; color: #ffffff; }
$avatares
#raiz QLabel[mini="1"] { min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px;
  border-radius: $raio_mini; border: none; }

#cartao { background-color: $superficie; border-radius: $raio; }
#cartao QLabel#tituloInicio { font-weight: bold; font-size: ${fonte_titulo}pt; color: $texto_titulo; }
#cartao QLabel#subInicio { color: $texto_fraco; }
#cartao QLabel#recentesTitulo { color: $texto_mais_fraco; font-size: ${fonte_peq}pt; font-weight: bold; }
QPushButton#conectar { background-color: $destaque; color: $texto_destaque; border: none;
  border-radius: $raio_peq; font-weight: bold; padding: 0 18px; min-height: 36px; }
QPushButton#conectar:hover { background-color: $destaque_hover; }
QPushButton[recente="1"] { background-color: $recente; color: $texto; border: none;
  border-radius: $raio_peq; padding: 4px 12px; }
QPushButton[recente="1"]:hover { background-color: $recente_hover; }

#abas::pane { border: none; background: #000000; }
#abas QTabBar { background-color: $barra; }
#abas QTabBar::tab { background: transparent; color: $texto_aba; border: none;
  border-top-left-radius: $raio_peq; border-top-right-radius: $raio_peq; padding: 6px 4px 6px 12px;
  margin: 6px 2px 0 2px; min-height: 22px; }
#abas QTabBar::tab:hover { background-color: $aba_hover; }
#abas QTabBar::tab:selected { background-color: $aba_ativa; color: $texto_aba_ativa;
  border-bottom: 2px solid $destaque; }
#abas QTabBar QLabel { color: palette(text); }
#abas QTabBar QToolButton { background: transparent; border: none; border-radius: 11px;
  min-width: 22px; min-height: 22px; }
#abas QTabBar QToolButton:hover { background-color: $aba_botao_hover; }
#abas QToolButton#novaConexao { background-color: transparent; border: none; border-radius: $raio_peq; margin: 4px; }
#abas QToolButton#novaConexao:hover { background-color: $aba_hover; }

#selo { background-color: #e53935; color: #ffffff; border-radius: 9px; font-size: 7pt; font-weight: bold;
  border: 2px solid #ffffff; min-width: 14px; padding: 0 3px; }

#aviso { background-color: $aviso; color: $texto; border-radius: 20px; }
#aviso QLabel { color: $texto; }

QMenu { background-color: $superficie; color: $texto; border: 1px solid $borda_campo; padding: 6px;
  border-radius: $raio_peq; }
QMenu::item { padding: 6px 18px; border-radius: $raio_peq; }
QMenu::item:selected { background-color: $selecao_lateral; }
QToolTip { background-color: $superficie; color: $texto; border: 1px solid $borda_campo; }
""")


def _tamanho_fonte(tema):
    tamanho = tema.get("tamanho")
    if tamanho and tamanho.endswith("pt"):
        return float(tamanho[:-2])
    return QApplication.font().pointSizeF() or 10.0


def fonte_do_tema(cfg):
    tema = temas.TEMAS[cfg["tema"]]
    return tema.get("fonte"), _tamanho_fonte(tema)


def gerar_qss(cfg, dourado=False, moldura=None):
    tema = temas.TEMAS[cfg["tema"]]
    cores = temas.cores_do_tema(cfg)
    if dourado and not cfg["ajustes"].get("destaque"):
        cores["destaque"], cores["texto_destaque"] = temas.DOURADO, "#3a2400"
    ex = extra(cfg["tema"])
    base = _tamanho_fonte(tema)
    avatares = tema.get("avatares", temas.PADRAO_AVATARES)
    v = {k: qss(c) for k, c in cores.items()}
    v.update(
        texto_barra_fraco=qss(f"alpha({cores['texto_barra']}, 0.6)"),
        barra_hover=qss(f"alpha({cores['texto_barra']}, 0.12)"),
        barra_marcado=qss(f"alpha({cores['texto_barra']}, 0.18)"),
        texto_lateral_fraco=qss(f"alpha({cores['texto_lateral']}, 0.55)"),
        linha_lateral=qss(f"alpha({cores['texto_lateral']}, 0.08)"),
        borda_campo=qss(f"alpha({cores['texto_lateral']}, 0.14)"),
        hover_lateral=qss(f"alpha({cores['texto_lateral']}, 0.07)"),
        selecao_lateral=qss(f"alpha({cores['destaque']}, 0.25)"),
        barra_rolagem=qss(f"alpha({cores['texto_lateral']}, 0.25)"),
        texto_titulo=qss(ex["titulo_cor"] or cores["texto"]),
        texto_fraco=qss(f"alpha({cores['texto']}, 0.7)"),
        texto_mais_fraco=qss(f"alpha({cores['texto']}, 0.55)"),
        destaque_hover=qss(f"shade({cores['destaque']}, 1.08)"),
        recente=qss(f"alpha({cores['destaque']}, 0.12)"),
        recente_hover=qss(f"alpha({cores['destaque']}, 0.24)"),
        texto_aba=qss(f"alpha({cores['texto_barra']}, 0.7)"),
        aba_hover=qss(f"alpha({cores['texto_barra']}, 0.07)"),
        aba_botao_hover=qss(f"alpha({cores['texto_barra']}, 0.15)"),
        aviso=qss(f"shade({cores['superficie']}, 0.92)"),
        raio=tema.get("raio", "14px"), raio_peq=tema.get("raio_peq", "8px"),
        raio_avatar="0px" if tema.get("raio") == "0px" else "17px",
        raio_mini="0px" if tema.get("raio") == "0px" else "5px",
        fonte_peq=f"{base * 0.85:.1f}", fonte_lateral=f"{base * 1.1:.1f}",
        fonte_titulo=f"{base * ex['titulo']:.1f}",
        avatares="\n".join(f'#raiz QLabel[avatar="{i}"] {{ background-color: {qss(c)}; }}'
                           for i, c in enumerate(avatares)),
    )
    partes = [BASE.substitute(v), Template(ex["qss"]).safe_substitute(v)]
    if moldura in MOLDURAS:
        partes.append('#raiz #lateral QLabel[avatar] { '
                      + Template(MOLDURAS[moldura]).safe_substitute(v) + " }")
    return "\n".join(partes)


def qss_previas():
    """Cartões de tema na janela de aparência (cada um com as cores do seu tema)."""
    regras = []
    for chave, tema in temas.TEMAS.items():
        fundo, lateral, destaque = tema["previa"]
        fonte = f'font-family: "{tema["fonte"]}";' if tema.get("fonte") else ""
        texto = temas.cor_texto(fundo) or "#ffffff"
        regras.append(
            f'QFrame[previa="{chave}"] {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
            f' stop:0 {lateral}, stop:0.3 {lateral}, stop:0.3001 {fundo}, stop:1 {fundo});'
            f' border-radius: 10px; min-height: 64px; }}\n'
            f'QFrame[previa="{chave}"] QLabel#previaNome {{ {fonte} color: {texto}; }}\n'
            f'QFrame[previa="{chave}"] QLabel#previaPonto {{ background-color: {destaque}; border-radius: 7px;'
            f' min-width: 14px; max-width: 14px; min-height: 14px; max-height: 14px; }}')
    return "\n".join(regras)


# ---- ícones Phosphor ------------------------------------------------------------------

ICONES = Path(__file__).resolve().parent / "icones" / "gtk"
_cache_icone = {}


def icone(nome, cor_icone, tamanho=18):
    """QIcon do Phosphor (icones/gtk/ph-<nome>-symbolic.svg) pintado na cor pedida."""
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QIcon

    c = cor(cor_icone) if isinstance(cor_icone, str) else QColor(cor_icone)
    chave = (nome, c.rgba(), tamanho)
    if chave not in _cache_icone:
        svg = (ICONES / f"ph-{nome}-symbolic.svg").read_text().replace("currentColor", c.name())
        render = QSvgRenderer(QByteArray(svg.encode()))
        escala = 2  # nítido em telas com escala de 200%
        imagem = QImage(tamanho * escala, tamanho * escala, QImage.Format_ARGB32_Premultiplied)
        imagem.fill(Qt.transparent)
        pintor = QPainter(imagem)
        pintor.setOpacity(c.alphaF())
        render.render(pintor)
        pintor.end()
        pixmap = QPixmap.fromImage(imagem)
        pixmap.setDevicePixelRatio(escala)
        _cache_icone[chave] = QIcon(pixmap)
    return _cache_icone[chave]
