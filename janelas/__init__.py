"""Conversa com o sistema sobre as janelas do AnyDesk, igual no Linux (X11) e no Windows.

Interface de Janelas (as duas versões têm os mesmos métodos):

- anydesk(): identificadores das janelas visíveis do AnyDesk.
- pid(j), titulo(j), existe(j).
- abrir(cid): abre a conexão no AnyDesk e devolve o PID do processo.
- encerrar(j, pid): fecha aquela sessão (sem derrubar as outras).
- FORCAR_FOCO: o app precisa mandar o teclado para a sessão (X11) ou o sistema já faz (Windows).
- foco(), dar_foco(j), contem(a, j), clicou_dentro(j): usados quando FORCAR_FOCO é True.
- Só fazem algo no Windows (no Linux o FORCAR_FOCO cuida do teclado): restaurar_foco(j) põe o teclado
  na sessão; e_sessao(h, j); devolver_ao_app(h) traz o teclado ao app; observar_foco(f) chama
  f(hwnd, clique) a cada mudança de foco ou clique do mouse (por eventos do Windows, sem timer);
  parar_observacao().
- desfoque(j, retangulos): desfoca o que está atrás da janela (tema vidro). None desliga.
"""
import plataforma

if plataforma.WINDOWS:
    from .win32 import Janelas
else:
    from .linux import Janelas

__all__ = ["Janelas"]
