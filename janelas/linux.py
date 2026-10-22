"""Janelas no Linux: o app e o AnyDesk rodam pelo X11 (ou XWayland), ver x11.py."""
import os
import signal
import subprocess

import plataforma
from x11 import X11

CLASSE_ANYDESK = "anydesk"


class Janelas:
    # O AnyDesk não fala o protocolo XEMBED: sem o app mandar o foco do X11 para a janela da
    # sessão, atalhos e teclas especiais se perdem.
    FORCAR_FOCO = True

    def __init__(self):
        self.x = X11()

    def anydesk(self):
        return self.x.find_windows(CLASSE_ANYDESK)

    def pid(self, janela):
        return self.x.pid(janela)

    def titulo(self, janela):
        return self.x.title(janela)

    def existe(self, janela):
        attr = self.x.geometry(janela)
        return bool(attr)

    def abrir(self, cid):
        exe = plataforma.anydesk()
        if not exe:
            raise FileNotFoundError("AnyDesk não encontrado")
        # O AnyDesk precisa abrir pelo X11, mesmo numa sessão Wayland, para poder ser encaixado.
        env = dict(os.environ, GDK_BACKEND="x11")
        proc = subprocess.Popen([exe, cid], env=env, start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc.pid

    def encerrar(self, _janela, pid):
        # O AnyDesk fecha sozinho quando a janela sai da aba, então não dá para devolvê-la à
        # área de trabalho: fechar a aba é encerrar o processo daquela conexão.
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    # ---- teclado ----

    def foco(self):
        return self.x.focused()

    def dar_foco(self, janela):
        self.x.set_focus(janela)

    def restaurar_foco(self, _janela):
        pass  # no Linux o manter_foco já devolve o teclado à sessão

    def contem(self, ancestral, janela):
        return self.x.contains(ancestral, janela)

    def clicou_dentro(self, janela):
        return self.x.clicked_inside(janela)

    # ---- vidro ----

    def desfoque(self, janela, retangulos):
        """Pede ao KWin para desfocar o que está atrás. Fora do KDE o pedido é ignorado."""
        self.x.set_blur(janela, retangulos)
