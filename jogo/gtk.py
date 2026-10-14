"""Partes do jogo que aparecem no próprio app GTK: pet no rodapé, sons e notificações."""
from pathlib import Path

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

from . import catalogo as cat  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ARTE = RAIZ / "arte"
SONS = RAIZ / "sons"


def _desenho(caminho, largura):
    """Carrega um desenho de pixel art com a largura pedida (altura proporcional, sem borrar)."""
    _, w, h = GdkPixbuf.Pixbuf.get_file_info(str(caminho))
    return GdkPixbuf.Pixbuf.new_from_file_at_scale(str(caminho), largura, round(h / w * largura), False)


def compor_pet(especie, acessorio, unidade=3):
    """Imagem do pet (ou do ovo) com o acessório, numa grade de 16 x 24 'pixels' do desenho.

    As 8 linhas de cima ficam livres para chapéus; o pet começa na linha 8.
    """
    largura = 16 * unidade
    tela = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, largura, 24 * unidade)
    tela.fill(0x00000000)
    camadas = [(ARTE / "pets" / f"{especie or 'ovo'}.svg", 8)]
    if especie and acessorio:
        camadas.append((ARTE / "acessorios" / f"{acessorio}.svg",
                        8 + cat.deslocamento_acessorio(especie, acessorio)))
    for caminho, linha in camadas:
        desenho = _desenho(caminho, largura)
        y = linha * unidade
        altura = min(desenho.get_height(), tela.get_height() - y)
        desenho.composite(tela, 0, y, largura, altura, 0, y, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)
    return tela


class Sons:
    """Toca os WAV de sons/ com o GStreamer (carregado só na primeira vez)."""

    def __init__(self):
        self._player = None

    def tocar(self, nome):
        if not nome:
            return
        arquivo = SONS / f"{nome}.wav"
        if not arquivo.exists():
            return
        try:
            if self._player is None:
                gi.require_version("Gst", "1.0")
                from gi.repository import Gst
                Gst.init(None)
                self._Gst = Gst
                self._player = Gst.ElementFactory.make("playbin", "som")
            Gst = self._Gst
            self._player.set_state(Gst.State.NULL)
            self._player.set_property("uri", arquivo.as_uri())
            self._player.set_state(Gst.State.PLAYING)
        except (ValueError, ImportError, AttributeError):
            self._player = None  # sem GStreamer: segue sem som


class Notificacoes:
    """Notificações do sistema (libnotify), se disponível."""

    def __init__(self, nome_app="NaView", icone="naview"):
        self.icone = icone
        try:
            gi.require_version("Notify", "0.7")
            from gi.repository import Notify
            Notify.init(nome_app)
            self._Notify = Notify
        except (ValueError, ImportError):
            self._Notify = None

    def mostrar(self, titulo, texto):
        if not self._Notify:
            return
        try:
            self._Notify.Notification.new(titulo, texto, self.icone).show()
        except Exception:  # noqa: BLE001 - serviço de notificação fora do ar não pode derrubar o app
            pass
