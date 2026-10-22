"""Diagnóstico do "colar para de funcionar depois de ~30 s" no Windows.

Rode num PC com Windows, com o NaView aberto e uma sessão encaixada:

    python ferramentas/diagnostico_colar_windows.py

A cada 5 s mostra: janela em primeiro plano, janela com foco de teclado dentro da sessão do AnyDesk,
dono da área de transferência e quem a mantém aberta. Deixe rodando, copie um texto, tente colar na
sessão (funciona no começo, falha depois) e mande a saída. Só lê; não muda nada.
"""
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetFocus.restype = wintypes.HWND
user32.GetOpenClipboardWindow.restype = wintypes.HWND
user32.GetClipboardOwner.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetParent.argtypes = [wintypes.HWND]
user32.GetParent.restype = wintypes.HWND
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


def descrever(hwnd):
    if not hwnd:
        return "nenhuma"
    classe, titulo = ctypes.create_unicode_buffer(256), ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, classe, 256)
    user32.GetWindowTextW(hwnd, titulo, 256)
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pai = user32.GetParent(hwnd)
    return f"hwnd={int(hwnd):#x} pid={pid.value} classe={classe.value!r} titulo={titulo.value[:40]!r} pai={int(pai) if pai else 0:#x}"


def foco_do_primeiro_plano():
    """GetFocus só vale na própria fila: junta a fila da janela em primeiro plano por um instante."""
    frente = user32.GetForegroundWindow()
    if not frente:
        return None
    tid = user32.GetWindowThreadProcessId(frente, None)
    eu = kernel32.GetCurrentThreadId()
    if tid == eu:
        return user32.GetFocus()
    if not user32.AttachThreadInput(eu, tid, True):
        return None
    try:
        return user32.GetFocus()
    finally:
        user32.AttachThreadInput(eu, tid, False)


inicio = time.monotonic()
while True:
    t = int(time.monotonic() - inicio)
    print(f"[{t:4d}s] primeiro plano: {descrever(user32.GetForegroundWindow())}")
    print(f"        foco teclado:  {descrever(foco_do_primeiro_plano())}")
    print(f"        clipboard: seq={user32.GetClipboardSequenceNumber()} "
          f"dono={descrever(user32.GetClipboardOwner())} aberta_por={descrever(user32.GetOpenClipboardWindow())}")
    time.sleep(5)
