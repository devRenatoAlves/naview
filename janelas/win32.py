"""Janelas no Windows, pela API do Windows (user32 e kernel32 via ctypes).

O teste de viabilidade (16/10/2026, ver docs/sdd/specs/06-windows.md) mostrou que cada
"AnyDesk.exe <ID>" abre um processo próprio com uma janela só, que o encaixe do Qt funciona e que o
teclado vai para a sessão sem precisar forçar o foco.
"""
import ctypes
import subprocess
from ctypes import wintypes
from pathlib import Path

import plataforma

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WM_CLOSE = 0x0010
CREATE_NO_WINDOW = 0x08000000
GA_ROOT = 2
EVENT_SYSTEM_CAPTURESTART = 0x0008  # um botão do mouse foi apertado e a janela "pegou" o mouse
EVENT_OBJECT_FOCUS = 0x8005  # o foco do teclado mudou de janela
WINEVENT_OUTOFCONTEXT = 0x0000  # o aviso chega na nossa thread (pelo laço de mensagens do Qt)
OBJID_WINDOW = 0
OBJID_CLIENT = -4
WinEventProc = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG,
                                  wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.SetFocus.argtypes = [wintypes.HWND]
user32.SetFocus.restype = wintypes.HWND
user32.GetFocus.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsChild.argtypes = [wintypes.HWND, wintypes.HWND]
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.SetWinEventHook.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
user32.SetWinEventHook.restype = wintypes.HANDLE
user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]


def _exe_do_pid(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(32768)
        tamanho = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(tamanho)):
            return buf.value
        return ""
    finally:
        kernel32.CloseHandle(h)


class Janelas:
    FORCAR_FOCO = False  # o Windows já leva o teclado para a janela encaixada

    def __init__(self):
        self._exe = {}  # pid -> é AnyDesk? (o nome do programa não muda durante o processo)

    def _e_anydesk(self, pid):
        if pid not in self._exe:
            self._exe[pid] = Path(_exe_do_pid(pid)).name.lower().startswith("anydesk")
        return self._exe[pid]

    def anydesk(self):
        achadas = []

        def visitar(hwnd, _):
            if user32.IsWindowVisible(hwnd) and self._e_anydesk(self.pid(hwnd)):
                achadas.append(int(hwnd))
            return True

        user32.EnumWindows(EnumWindowsProc(visitar), 0)
        return achadas

    def pid(self, janela):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(janela, ctypes.byref(pid))
        return pid.value

    def titulo(self, janela):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(janela, buf, len(buf))
        return buf.value

    def existe(self, janela):
        return bool(user32.IsWindow(janela))

    def abrir(self, cid):
        exe = plataforma.anydesk()
        if not exe:
            raise FileNotFoundError("AnyDesk não encontrado")
        return subprocess.Popen([exe, cid], creationflags=CREATE_NO_WINDOW).pid

    def encerrar(self, janela, _pid):
        # WM_CLOSE fecha só a janela da sessão; o processo some sozinho (teste de 16/10/2026).
        if janela:
            user32.PostMessageW(janela, WM_CLOSE, 0, 0)

    def restaurar_foco(self, janela):
        """Põe o teclado na janela da sessão (SetFocus), se o NaView está em primeiro plano.

        O Windows deixa o foco na janela principal do NaView (Qt) depois de Alt+Tab, Win+V, um aviso ou
        um clique em área do Qt; aí Ctrl+V e outros atalhos caem no NaView e o AnyDesk não recebe nada.
        Teste de 22/10/2026: o foco ficava em "Qt683QWindowIcon" em vez de "ad_win". As filas de entrada
        das duas janelas já são unidas pelo próprio Windows (janela filha de outro processo), então basta
        SetFocus; não usar AttachThreadInput(..., False), que desfaria essa união.
        """
        if not janela or not user32.IsWindow(janela):
            return
        topo = user32.GetAncestor(janela, GA_ROOT)
        if not topo or user32.GetForegroundWindow() != topo:
            return  # outro programa está na frente: não roubar o foco dele
        atual = user32.GetFocus()
        # Foco já na sessão ou num controle dentro dela (ex.: campo de senha do AnyDesk): não mexer.
        # Puxar o foco para a janela-mãe tirava o cursor do campo logo depois do clique.
        if atual and (atual == janela or user32.IsChild(janela, atual)):
            return
        user32.SetFocus(janela)

    def e_sessao(self, hwnd, janela):
        """A janela hwnd é a da sessão (ou algo dentro dela)?"""
        return bool(hwnd and janela and (hwnd == janela or user32.IsChild(janela, hwnd)))

    def devolver_ao_app(self, janela_app):
        """Clicou num campo de texto do NaView com o teclado na sessão: o teclado vem para o NaView."""
        if janela_app and user32.GetFocus() != janela_app:
            user32.SetFocus(janela_app)

    def observar_foco(self, ao_mudar):
        """Avisa ao_mudar(hwnd, clique) quando o foco do teclado muda de janela ou um botão do mouse é
        apertado numa janela. Só reage a eventos do Windows (nada de timer); com o app parado não custa
        nada. O aviso chega no laço de mensagens do Qt, então roda na thread da interface."""
        self.parar_observacao()

        def aviso(_gancho, evento, hwnd, objeto, _filho, _thread, _tempo):
            try:
                if evento == EVENT_OBJECT_FOCUS and objeto == OBJID_CLIENT:
                    ao_mudar(int(hwnd or 0), False)
                elif evento == EVENT_SYSTEM_CAPTURESTART and objeto == OBJID_WINDOW:
                    ao_mudar(int(hwnd or 0), True)
            except Exception:
                pass  # um erro aqui nunca pode chegar ao Windows

        self._aviso = WinEventProc(aviso)  # precisa ficar guardado, senão o Python o apaga
        self._ganchos = [h for h in (
            user32.SetWinEventHook(EVENT_OBJECT_FOCUS, EVENT_OBJECT_FOCUS, None, self._aviso, 0, 0,
                                   WINEVENT_OUTOFCONTEXT),
            user32.SetWinEventHook(EVENT_SYSTEM_CAPTURESTART, EVENT_SYSTEM_CAPTURESTART, None, self._aviso,
                                   0, 0, WINEVENT_OUTOFCONTEXT)) if h]

    def parar_observacao(self):
        for h in getattr(self, "_ganchos", []):
            user32.UnhookWinEvent(h)
        self._ganchos = []

    # ---- teclado (FORCAR_FOCO é False: no Windows valem restaurar_foco, e_sessao, devolver_ao_app e observar_foco) ----

    def foco(self):
        return None

    def dar_foco(self, _janela):
        pass

    def contem(self, _ancestral, _janela):
        return True

    def clicou_dentro(self, _janela):
        return False

    def desfoque(self, _janela, _retangulos):
        pass  # no Windows o tema vidro fica sem desfoque, como fora do KDE
