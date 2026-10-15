#!/usr/bin/env python3
"""Teste de viabilidade do NaView no Windows (fase 0, ver docs/sdd/specs/06-windows.md).

Encaixa janelas do AnyDesk em abas de uma janela Qt e gera um relatório do que funcionou.
Rodar num PC com Windows 10 ou 11 e o AnyDesk instalado:

    py -m pip install PySide6
    py teste_windows.py

Conecte num PC de teste seu, nunca num cliente. O relatório sai em relatorio-windows.txt, na
mesma pasta deste arquivo (ou do .exe, na versão empacotada pelo GitHub Actions).

--verificar: abre, confere que tudo carregou e fecha sozinho (usado pelo GitHub Actions).
"""
import ctypes
import os
import platform
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import PySide6
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QWindow
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
                               QTabWidget, QVBoxLayout, QWidget)

EMPACOTADO = getattr(sys, "frozen", False)
# Pasta do .exe (versão empacotada) ou deste arquivo: é onde o relatório é salvo.
PASTA = Path(sys.executable).parent if EMPACOTADO else Path(__file__).resolve().parent
# Arquivos que o PyInstaller junta ao .exe ficam em sys._MEIPASS.
RECURSOS = Path(getattr(sys, "_MEIPASS", PASTA))

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32")

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_QUERY = 0x0008
TOKEN_ELEVATION = 20
WM_CLOSE = 0x0010
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsChild.argtypes = [wintypes.HWND, wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.SetFocus.argtypes = [wintypes.HWND]
user32.SetFocus.restype = wintypes.HWND
user32.GetFocus.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                         ctypes.POINTER(wintypes.DWORD)]

PERGUNTAS = [
    "A sessão aparece dentro da aba, sem a moldura própria do AnyDesk",
    "Teclado: digitar texto na sessão funciona",
    "Atalhos (Ctrl+C, Ctrl+V, Win, Alt+Tab do lado remoto) funcionam",
    "Mouse e rolagem funcionam",
    "Redimensionar e maximizar a janela ajustam a sessão",
    "Imagem nítida (sem borrão) com a escala de tela atual",
    "Duas sessões ao mesmo tempo, cada uma na sua aba",
    "Trocar de aba leva o teclado para a sessão certa",
    "Digitar no campo de ID deste app funciona com uma sessão aberta",
    "Fechar a aba encerra só aquela sessão",
    "Tudo acima funciona sem marcar 'Forçar foco'",
]


# ---- Windows ------------------------------------------------------------------

def texto_janela(hwnd, funcao):
    buf = ctypes.create_unicode_buffer(512)
    funcao(hwnd, buf, len(buf))
    return buf.value


def pid_da_janela(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def exe_do_pid(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(32768)
        tamanho = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(tamanho)):
            return buf.value
        return None
    finally:
        kernel32.CloseHandle(h)


def elevado(pid):
    """True/False se o processo roda como administrador; None se não deu para saber."""
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return None
    token = wintypes.HANDLE()
    try:
        if not advapi32.OpenProcessToken(h, TOKEN_QUERY, ctypes.byref(token)):
            return None
        valor, tamanho = wintypes.DWORD(), wintypes.DWORD()
        ok = advapi32.GetTokenInformation(token, TOKEN_ELEVATION, ctypes.byref(valor),
                                          ctypes.sizeof(valor), ctypes.byref(tamanho))
        kernel32.CloseHandle(token)
        return bool(valor.value) if ok else None
    finally:
        kernel32.CloseHandle(h)


def dpi(hwnd):
    try:
        return user32.GetDpiForWindow(wintypes.HWND(hwnd))
    except AttributeError:  # Windows antigo
        return None


def janelas_anydesk():
    """Janelas visíveis de primeiro nível cujo programa é o AnyDesk."""
    achadas = []

    def visitar(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            pid = pid_da_janela(hwnd)
            exe = exe_do_pid(pid) or ""
            if Path(exe).name.lower().startswith("anydesk"):
                achadas.append({"hwnd": int(hwnd), "pid": pid, "exe": exe,
                                "titulo": texto_janela(hwnd, user32.GetWindowTextW),
                                "classe": texto_janela(hwnd, user32.GetClassNameW)})
        return True

    user32.EnumWindows(EnumWindowsProc(visitar), 0)
    return achadas


def achar_anydesk():
    for janela in janelas_anydesk():
        return janela["exe"]
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base and Path(base, "AnyDesk", "AnyDesk.exe").is_file():
            return str(Path(base, "AnyDesk", "AnyDesk.exe"))
    return shutil.which("AnyDesk")


# ---- janela de teste -------------------------------------------------------------

class Teste(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NaView: teste no Windows")
        self.resize(1280, 820)
        self.encaixadas = {}  # widget da aba -> {"hwnd", "janela", ...}

        self.abas = QTabWidget(tabsClosable=True, movable=True)
        self.abas.tabCloseRequested.connect(self.fechar_aba)

        lateral = QVBoxLayout()
        self.id = QLineEdit(placeholderText="ID de um PC de teste (não de cliente)")
        conectar = QPushButton("Conectar")
        conectar.clicked.connect(self.conectar)
        linha = QHBoxLayout()
        linha.addWidget(self.id)
        linha.addWidget(conectar)
        lateral.addLayout(linha)

        lateral.addWidget(QLabel("Janelas do AnyDesk abertas:"))
        self.lista = QListWidget()
        lateral.addWidget(self.lista)
        botoes = QHBoxLayout()
        for texto, acao in (("Atualizar", self.atualizar_lista), ("Encaixar", self.encaixar_escolhida),
                            ("Soltar aba", self.soltar_aba)):
            botao = QPushButton(texto)
            botao.clicked.connect(acao)
            botoes.addWidget(botao)
        lateral.addLayout(botoes)
        self.forcar_foco = QCheckBox("Forçar foco do teclado na sessão")
        lateral.addWidget(self.forcar_foco)

        lateral.addWidget(QLabel("Marque o que funcionou:"))
        self.respostas = [QCheckBox(p) for p in PERGUNTAS]
        for caixa in self.respostas:
            lateral.addWidget(caixa)
        self.notas = QPlainTextEdit(placeholderText="Observações (o que travou, piscou, ficou estranho...)")
        self.notas.setMaximumHeight(90)
        lateral.addWidget(self.notas)
        salvar = QPushButton("Salvar relatório")
        salvar.clicked.connect(self.salvar_relatorio)
        lateral.addWidget(salvar)
        self.log = QPlainTextEdit(readOnly=True)
        lateral.addWidget(self.log)

        painel = QWidget()
        painel.setLayout(lateral)
        painel.setFixedWidth(380)
        corpo = QHBoxLayout()
        corpo.addWidget(painel)
        corpo.addWidget(self.abas, 1)
        central = QWidget()
        central.setLayout(corpo)
        self.setCentralWidget(central)

        self.relogio_foco = QTimer(self, interval=120, timeout=self.manter_foco)
        self.relogio_foco.start()
        self.anotar(f"Este app como administrador: {bool(shell32.IsUserAnAdmin())}")
        self.anotar(f"AnyDesk: {achar_anydesk() or 'não encontrado'}")
        self.atualizar_lista()

    def anotar(self, texto):
        self.log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {texto}")

    def descrever(self, j):
        return (f"hwnd={j['hwnd']:#x} pid={j['pid']} classe={j['classe']!r} titulo={j['titulo']!r} "
                f"admin={elevado(j['pid'])} dpi={dpi(j['hwnd'])}")

    def atualizar_lista(self):
        self.lista.clear()
        encaixadas = {e["hwnd"] for e in self.encaixadas.values()}
        for j in janelas_anydesk():
            if j["hwnd"] in encaixadas:
                continue
            item = QListWidgetItem(f"{j['titulo'] or '(sem título)'}  [{j['classe']}]")
            item.setData(Qt.UserRole, j)
            self.lista.addItem(item)

    def encaixar_escolhida(self):
        item = self.lista.currentItem()
        if item:
            self.encaixar(item.data(Qt.UserRole))

    def encaixar(self, j):
        self.anotar("Encaixando " + self.descrever(j))
        janela = QWindow.fromWinId(j["hwnd"])
        if janela is None:
            self.anotar("QWindow.fromWinId falhou")
            return
        caixa = QWidget.createWindowContainer(janela)
        caixa.setFocusPolicy(Qt.StrongFocus)
        self.encaixadas[caixa] = dict(j, janela=janela)
        self.abas.setCurrentIndex(self.abas.addTab(caixa, (j["titulo"] or "AnyDesk")[:28]))
        self.anotar(f"dpi deste app={dpi(int(self.winId()))} escala Qt={self.devicePixelRatioF()}")
        self.atualizar_lista()

    def conectar(self):
        cid = self.id.text().replace(" ", "")
        exe = achar_anydesk()
        if not cid or not exe:
            self.anotar("Falta o ID ou o AnyDesk não foi encontrado")
            return
        antes = {j["hwnd"] for j in janelas_anydesk()}
        subprocess.Popen([exe, cid])
        self.anotar(f"Rodando: {exe} {cid}")
        inicio = time.monotonic()

        def procurar():
            novas = [j for j in janelas_anydesk() if j["hwnd"] not in antes]
            if novas:
                procura.stop()
                for j in novas:
                    self.anotar("Janela nova: " + self.descrever(j))
                self.encaixar(novas[-1])
            elif time.monotonic() - inicio > 60:
                procura.stop()
                self.anotar("Nenhuma janela nova em 60 s. A sessão pode ter aberto como aba dentro "
                            "da janela do AnyDesk: confira a opção de abrir sessões em janela nova "
                            "nas configurações do AnyDesk e tente de novo.")

        procura = QTimer(self, interval=300, timeout=procurar)
        procura.start()

    def aba_atual(self):
        return self.encaixadas.get(self.abas.currentWidget())

    def manter_foco(self):
        """Mesmo truque do Linux: o teclado vai direto para a janela da sessão."""
        alvo = self.aba_atual()
        if not (self.forcar_foco.isChecked() and alvo and self.isActiveWindow()):
            return
        if isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit)):
            return  # digitando neste app
        hwnd = alvo["hwnd"]
        meu, dele = kernel32.GetCurrentThreadId(), user32.GetWindowThreadProcessId(hwnd, None)
        user32.AttachThreadInput(meu, dele, True)
        foco = user32.GetFocus()
        if foco != hwnd and not user32.IsChild(hwnd, foco):
            user32.SetFocus(hwnd)
        user32.AttachThreadInput(meu, dele, False)

    def soltar_aba(self):
        alvo = self.aba_atual()
        if not alvo:
            return
        caixa = self.abas.currentWidget()
        alvo["janela"].setParent(None)
        alvo["janela"].show()
        self.abas.removeTab(self.abas.indexOf(caixa))
        del self.encaixadas[caixa]
        QTimer.singleShot(1500, lambda: self.anotar(
            f"Soltar aba: janela ainda existe? {bool(user32.IsWindow(alvo['hwnd']))}"))

    def fechar_aba(self, indice):
        caixa = self.abas.widget(indice)
        alvo = self.encaixadas.pop(caixa, None)
        self.abas.removeTab(indice)
        if alvo:
            # WM_CLOSE fecha só a janela; matar o processo poderia derrubar outras sessões.
            user32.PostMessageW(alvo["hwnd"], WM_CLOSE, 0, 0)
            self.anotar(f"Aba fechada (WM_CLOSE em {alvo['hwnd']:#x})")
            QTimer.singleShot(1500, lambda: self.anotar(
                f"Janela ainda existe? {bool(user32.IsWindow(alvo['hwnd']))}; "
                f"outras sessões: {len(self.encaixadas)}"))

    def salvar_relatorio(self):
        linhas = [
            "NaView: teste no Windows",
            f"Data: {time.strftime('%d/%m/%Y %H:%M')}",
            f"Sistema: {platform.platform()} ({platform.machine()})",
            f"Python {sys.version.split()[0]}, PySide6 {PySide6.__version__}",
            f"Este app como administrador: {bool(shell32.IsUserAnAdmin())}",
            f"AnyDesk: {achar_anydesk()}",
            "",
            "Janelas do AnyDesk agora:",
            *("  " + self.descrever(j) for j in janelas_anydesk()),
            "",
            "Resultado:",
            *(f"  [{'x' if c.isChecked() else ' '}] {c.text()}" for c in self.respostas),
            "",
            "Observações:",
            self.notas.toPlainText(),
            "",
            "Registro:",
            self.log.toPlainText(),
        ]
        arquivo = PASTA / "relatorio-windows.txt"
        try:
            arquivo.write_text("\n".join(linhas), encoding="utf-8")
        except OSError:  # pasta sem permissão de escrita: vai para a pasta do usuário
            arquivo = Path.home() / "relatorio-windows.txt"
            arquivo.write_text("\n".join(linhas), encoding="utf-8")
        self.anotar(f"Relatório salvo em {arquivo}")
        QMessageBox.information(self, "Relatório salvo",
                                f"O relatório foi salvo em:\n{arquivo}\n\nA pasta vai abrir agora. "
                                "Envie o arquivo relatorio-windows.txt para quem te mandou o link.")
        os.startfile(arquivo.parent)


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("Este teste é só para Windows.")
    app = QApplication(sys.argv)
    if (RECURSOS / "icone.ico").is_file():
        app.setWindowIcon(QIcon(str(RECURSOS / "icone.ico")))
    janela = Teste()
    janela.show()
    if "--verificar" in sys.argv:
        QTimer.singleShot(2000, app.quit)
    sys.exit(app.exec())
