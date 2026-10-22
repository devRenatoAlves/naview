"""Conversa com o sistema sobre as janelas do AnyDesk, igual no Linux (X11) e no Windows.

Interface de Janelas (as duas versões têm os mesmos métodos):

- anydesk(): identificadores das janelas visíveis do AnyDesk.
- pid(j), titulo(j), existe(j).
- abrir(cid): abre a conexão no AnyDesk e devolve o PID do processo.
- encerrar(j, pid): fecha aquela sessão (sem derrubar as outras).
- FORCAR_FOCO: o app precisa mandar o teclado para a sessão (X11) ou o sistema já faz (Windows).
- foco(), dar_foco(j), contem(a, j), clicou_dentro(j): usados quando FORCAR_FOCO é True.
- restaurar_foco(j): ao reativar o app, devolve o teclado à sessão (só faz algo no Windows).
- desfoque(j, retangulos): desfoca o que está atrás da janela (tema vidro). None desliga.
"""
import plataforma

if plataforma.WINDOWS:
    from .win32 import Janelas
else:
    from .linux import Janelas

__all__ = ["Janelas"]
