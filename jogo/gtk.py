"""Partes do jogo que aparecem no próprio app GTK: pet no rodapé, sons e notificações."""
from functools import lru_cache
from pathlib import Path

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

from . import catalogo as cat  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ARTE = RAIZ / "arte"
SONS = RAIZ / "sons"


@lru_cache(maxsize=16)
def compor_pet(especie, acessorio, unidade=1):
    """Imagem do pet (ou do ovo) com o acessório, num quadro de PET_LADO x (PET_LADO + PET_ACIMA).

    As PET_ACIMA linhas de cima ficam livres para chapéus. unidade = tamanho de cada pixel do desenho.
    Fica em cache: o rodapé pede a mesma imagem a cada minuto. Quem usa não deve alterar a imagem.
    """
    lado, acima = cat.PET_LADO, cat.PET_ACIMA
    tela = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, lado * unidade, (lado + acima) * unidade)
    tela.fill(0x00000000)
    camadas = [(ARTE / "pets" / f"{especie or 'ovo'}.svg", 0, acima, lado, lado)]
    if especie and acessorio:
        e = cat.encaixe_acessorio(especie, acessorio)
        camadas.append((ARTE / "acessorios" / f"{acessorio}.svg", e["x"], e["y"], e["w"], e["h"]))
    for caminho, x, y, w, h in camadas:
        desenho = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(caminho), w * unidade, h * unidade, False)
        # Recorta o que passar da borda do quadro.
        x0, y0 = max(0, x * unidade), max(0, y * unidade)
        x1 = min(tela.get_width(), (x + w) * unidade)
        y1 = min(tela.get_height(), (y + h) * unidade)
        if x1 > x0 and y1 > y0:
            desenho.composite(tela, x0, y0, x1 - x0, y1 - y0, x * unidade, y * unidade, 1, 1,
                              GdkPixbuf.InterpType.NEAREST, 255)
    return tela


class Sons:
    """Toca os WAV de sons/ com o GStreamer (carregado só na primeira vez)."""

    def __init__(self):
        self._player = None

    def preparar(self):
        """Carrega o GStreamer antes do primeiro som (senão a sessão nova trava um instante)."""
        if self._player is None:
            try:
                gi.require_version("Gst", "1.0")
                from gi.repository import Gst
                Gst.init(None)
                self._Gst = Gst
                self._player = Gst.ElementFactory.make("playbin", "som")
            except (ValueError, ImportError, AttributeError):
                self._player = None
        return False  # para uso com GLib.timeout_add

    def tocar(self, nome):
        if not nome:
            return
        arquivo = SONS / f"{nome}.wav"
        if not arquivo.exists():
            return
        try:
            self.preparar()
            if self._player is None:
                return  # sem GStreamer: segue sem som
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
