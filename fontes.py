"""Recursos do app: fontes de fonts/ e ícones de icones/gtk/ (sem instalar nada no sistema).

carregar() precisa rodar antes do Gtk/Pango criar o mapa de fontes, ou seja, antes de abrir a janela.
"""
import ctypes
import ctypes.util
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "fonts"
ICONES = Path(__file__).resolve().parent / "icones" / "gtk"


def carregar():
    nome = ctypes.util.find_library("fontconfig") or "libfontconfig.so.1"
    try:
        fc = ctypes.cdll.LoadLibrary(nome)
    except OSError:
        return
    fc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    for arquivo in sorted(PASTA.glob("*.ttf")):
        # config=None: adiciona à configuração atual, a mesma que o Pango vai usar.
        fc.FcConfigAppFontAddFile(None, str(arquivo).encode())


def registrar_icones():
    """Deixa o GTK achar os ícones Phosphor (ph-<nome>-symbolic). Pode ser chamada várias vezes."""
    from gi.repository import Gtk

    tema = Gtk.IconTheme.get_default()
    if str(ICONES) not in tema.get_search_path():
        tema.append_search_path(str(ICONES))
