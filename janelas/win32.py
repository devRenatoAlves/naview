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
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
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
        """Devolve o teclado à sessão depois que o NaView é reativado.

        Ao voltar de outro programa (Alt+Tab, clique na barra de tarefas) o Windows põe o foco na janela
        principal do NaView, não na do AnyDesk dentro dela; aí o Ctrl+V cai no NaView e o AnyDesk não
        recebe o texto. Teste de 22/10/2026: o foco ficava em "Qt683QWindowIcon" em vez de "ad_win".
        """
        if not janela or not user32.IsWindow(janela):
            return
        if user32.GetFocus() == janela:
            return
        eu = kernel32.GetCurrentThreadId()
        dele = user32.GetWindowThreadProcessId(janela, None)
        juntou = bool(dele and dele != eu and user32.AttachThreadInput(eu, dele, True))
        try:
            user32.SetFocus(janela)
        finally:
            if juntou:
                user32.AttachThreadInput(eu, dele, False)

    # ---- teclado (FORCAR_FOCO é False: só restaurar_foco é usado no Windows) ----

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
