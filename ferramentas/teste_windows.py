#!/usr/bin/env python3
"""Teste de viabilidade do NaView no Windows (fase 0, ver docs/sdd/specs/06-windows.md).

Encaixa janelas do AnyDesk em abas de uma janela Qt e gera um relatório do que funcionou.
Rodar num PC com Windows 10 ou 11 e o AnyDesk instalado:

    py -m pip install PySide6
    py teste_windows.py

Conecte num PC de teste seu, nunca num cliente. O relatório sai em relatorio-windows.txt, na
mesma pasta deste arquivo (ou do .exe, na versão empacotada pelo GitHub Actions). O registro de
tudo o que acontece vai sendo gravado em naview-piloto-log.txt, na mesma pasta: se a janela
travar, é esse arquivo que mostra onde.

--verificar: abre, confere que tudo carregou e fecha sozinho (usado pelo GitHub Actions).
"""
import ctypes
import faulthandler
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback
from ctypes import wintypes
from pathlib import Path

import PySide6
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QWindow
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit,
                               QPushButton, QTabWidget, QVBoxLayout, QWidget)

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
GWL_STYLE = -16
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_MOLDURA = 0x00C00000 | 0x00040000 | 0x00080000 | 0x00020000 | 0x00010000  # título, borda, botões
SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_NOACTIVATE = 0x1, 0x2, 0x4, 0x10
SWP_FRAMECHANGED, SWP_ASYNCWINDOWPOS = 0x20, 0x4000
SW_HIDE, SW_SHOWNA, SW_RESTORE = 0, 8, 9
GW_HWNDPREV = 3
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindow.argtypes = [wintypes.HWND]
user32.IsIconic.argtypes = [wintypes.HWND]
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
user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
user32.SetParent.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, wintypes.UINT]
user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetWindow.restype = wintypes.HWND
# GetWindowLongPtrW só existe no Windows 64 bits; no de 32 bits o nome é GetWindowLongW.
_ler_estilo = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
_ler_estilo.argtypes = [wintypes.HWND, ctypes.c_int]
_ler_estilo.restype = ctypes.c_ssize_t
_gravar_estilo = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
_gravar_estilo.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
_gravar_estilo.restype = ctypes.c_ssize_t
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                         ctypes.POINTER(wintypes.DWORD)]

# Modos de encaixe. "qt" é o planejado para o app; os outros dois existem porque o "qt" pode
# travar: prender a janela de outro programa junta a fila de teclado e mouse dos dois, e se o
# AnyDesk fica ocupado (conectando, por exemplo) o NaView congela junto.
MODOS = [
    ("qt", "Qt (createWindowContainer)"),
    ("setparent", "SetParent direto (sem esperar o AnyDesk)"),
    ("sobrepor", "Sobrepor (a sessão fica por cima da aba, sem prender)"),
]

PERGUNTAS = [
    "Conectar pelo ID abre a sessão normalmente",
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
    "A janela não travou em nenhum momento",
]


# ---- registro em arquivo ----------------------------------------------------------
# Gravado linha a linha: se o app travar ou fechar sozinho, o que aconteceu até ali fica salvo.

LOG = None
_trava_log = threading.Lock()


def abrir_log():
    global LOG
    for pasta in (PASTA, Path.home()):
        try:
            LOG = open(pasta / "naview-piloto-log.txt", "a", encoding="utf-8", buffering=1)
            return
        except OSError:
            continue


def registrar(texto):
    if LOG is None:
        return
    with _trava_log:
        LOG.write(f"[{time.strftime('%H:%M:%S')}] {texto}\n")
        LOG.flush()


def erro_nao_tratado(tipo, valor, rastro):
    registrar("ERRO: " + "".join(traceback.format_exception(tipo, valor, rastro)))


class Vigia(threading.Thread):
    """Percebe quando a janela para de responder e grava no registro onde o programa parou."""

    def __init__(self):
        super().__init__(daemon=True)
        self.batida = time.monotonic()  # atualizada pela janela a cada 250 ms
        self.acao = "abrindo"
        self.travou_em = None

    def run(self):
        while True:
            time.sleep(1)
            parado = time.monotonic() - self.batida
            if parado > 3 and self.travou_em is None:
                self.travou_em = self.batida
                registrar(f"JANELA TRAVADA há {parado:.0f} s. Última ação: {self.acao}")
                if LOG is not None:
                    with _trava_log:
                        LOG.write("Onde o programa está parado:\n")
                        LOG.flush()
                        faulthandler.dump_traceback(LOG, all_threads=True)
                        LOG.flush()
            elif parado < 1 and self.travou_em is not None:
                registrar(f"Janela voltou a responder depois de {self.batida - self.travou_em:.0f} s")
                self.travou_em = None


VIGIA = Vigia()


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


def retangulo(hwnd, funcao=user32.GetWindowRect):
    r = wintypes.RECT()
    funcao(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def estilo(hwnd):
    return _ler_estilo(hwnd, GWL_STYLE) & 0xFFFFFFFF


def mudar_estilo(hwnd, valor):
    # O valor é um DWORD; o ctypes espera número com sinal.
    _gravar_estilo(hwnd, GWL_STYLE, ctypes.c_long(valor).value)


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
    # Versão portátil, baixada e aberta sem instalar.
    for pasta in (Path.home() / "Downloads", Path.home() / "Desktop", Path.home() / "Área de Trabalho"):
        if pasta.is_dir():
            for exe in sorted(pasta.glob("AnyDesk*.exe")):
                return str(exe)
    return shutil.which("AnyDesk")


# ---- janela de teste -------------------------------------------------------------

class Teste(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NaView: teste no Windows")
        self.resize(1280, 820)
        self.encaixadas = {}  # widget da aba -> {"hwnd", "modo", ...}
        self.procura = None

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
        self.auto = QCheckBox("Encaixar sozinho quando a sessão abrir")
        lateral.addWidget(self.auto)

        lateral.addWidget(QLabel("Modo de encaixe:"))
        self.modo = QComboBox()
        for chave, nome in MODOS:
            self.modo.addItem(nome, chave)
        self.modo.currentIndexChanged.connect(
            lambda: self.anotar(f"Modo de encaixe: {self.modo.currentData()}"))
        lateral.addWidget(self.modo)

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
        # Acompanha tamanho e posição das sessões nos modos "setparent" e "sobrepor".
        self.relogio_posicao = QTimer(self, interval=100, timeout=self.posicionar)
        self.relogio_posicao.start()
        self.relogio_vigia = QTimer(self, interval=250, timeout=self.bater)
        self.relogio_vigia.start()
        self.anotar(f"Sistema: {platform.platform()}, Python {sys.version.split()[0]}, "
                    f"PySide6 {PySide6.__version__}")
        self.anotar(f"Este app como administrador: {bool(shell32.IsUserAnAdmin())}")
        self.anotar(f"AnyDesk: {achar_anydesk() or 'não encontrado'}")
        self.anotar(f"Registro gravado em: {Path(LOG.name) if LOG else 'nenhum arquivo (sem permissão)'}")
        self.atualizar_lista()

    def bater(self):
        VIGIA.batida = time.monotonic()

    def anotar(self, texto):
        VIGIA.acao = texto
        registrar(texto)
        self.log.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {texto}")

    def descrever(self, j):
        x, y, w, h = retangulo(j["hwnd"])
        return (f"hwnd={j['hwnd']:#x} pid={j['pid']} classe={j['classe']!r} titulo={j['titulo']!r} "
                f"tamanho={w}x{h} admin={elevado(j['pid'])} dpi={dpi(j['hwnd'])}")

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
        else:
            self.anotar("Escolha uma janela na lista antes de clicar em Encaixar")

    def encaixar(self, j):
        hwnd, modo = j["hwnd"], self.modo.currentData()
        if not user32.IsWindow(hwnd):
            self.anotar(f"A janela {hwnd:#x} já fechou; clique em Atualizar")
            self.atualizar_lista()
            return
        self.anotar(f"Encaixando ({modo}) " + self.descrever(j))
        if modo == "qt":
            janela = QWindow.fromWinId(hwnd)
            if janela is None:
                self.anotar("QWindow.fromWinId falhou")
                return
            caixa = QWidget.createWindowContainer(janela)
            info = dict(j, modo=modo, janela=janela)
        else:
            caixa = QWidget()
            caixa.setAttribute(Qt.WA_NativeWindow)  # precisa de janela própria do Windows
            if modo == "sobrepor":
                aviso = QLabel("A sessão fica por cima desta área.", alignment=Qt.AlignCenter)
                QVBoxLayout(caixa).addWidget(aviso)
            info = dict(j, modo=modo, estilo=estilo(hwnd), ultimo=None, visivel=True)
        caixa.setFocusPolicy(Qt.StrongFocus)
        self.encaixadas[caixa] = info
        self.abas.setCurrentIndex(self.abas.addTab(caixa, (j["titulo"] or "AnyDesk")[:28]))

        if modo != "qt":
            if user32.IsIconic(hwnd):
                user32.ShowWindowAsync(hwnd, SW_RESTORE)
            sem_moldura = info["estilo"] & ~WS_MOLDURA
            if modo == "setparent":
                mudar_estilo(hwnd, (sem_moldura | WS_CHILD) & ~WS_POPUP)
                self.anotar("SetParent...")
                antigo = user32.SetParent(hwnd, int(caixa.winId()))
                self.anotar(f"SetParent terminou (erro={ctypes.get_last_error() if not antigo else 0})")
            else:
                mudar_estilo(hwnd, sem_moldura)
            self.posicionar()
        self.anotar(f"dpi deste app={dpi(int(self.winId()))} escala Qt={self.devicePixelRatioF()}")
        self.atualizar_lista()

    def posicionar(self):
        """Ajusta as sessões dos modos "setparent" e "sobrepor" à área da aba.

        Só usa chamadas que não esperam o AnyDesk responder (SWP_ASYNCWINDOWPOS e
        ShowWindowAsync): se ele estiver ocupado, este app continua andando.
        """
        atual = self.abas.currentWidget()
        visivel_app = self.isVisible() and not self.isMinimized()
        for caixa, info in list(self.encaixadas.items()):
            hwnd = info["hwnd"]
            if info["modo"] == "qt":
                continue
            if not user32.IsWindow(hwnd):
                self.anotar(f"A janela {hwnd:#x} fechou sozinha")
                self.abas.removeTab(self.abas.indexOf(caixa))
                del self.encaixadas[caixa]
                continue
            mostrar = caixa is atual and visivel_app
            if info["modo"] == "sobrepor" and mostrar != info["visivel"]:
                user32.ShowWindowAsync(hwnd, SW_SHOWNA if mostrar else SW_HIDE)
                info["visivel"] = mostrar
            if not mostrar:
                continue
            flags = SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS
            if info["modo"] == "setparent":
                x, y, w, h = retangulo(int(caixa.winId()), user32.GetClientRect)
                depois = None
                flags |= SWP_NOZORDER
            else:
                x, y, w, h = retangulo(int(caixa.winId()))
                # Logo acima deste app: entra depois da janela que estiver acima dele.
                acima = user32.GetWindow(int(self.winId()), GW_HWNDPREV)
                if acima and int(acima) == hwnd:
                    depois, flags = None, flags | SWP_NOZORDER
                else:
                    depois = acima  # None = HWND_TOP
            alvo = (x, y, w, h, depois)
            if alvo == info["ultimo"]:
                continue
            if info["ultimo"] is None:
                flags |= SWP_FRAMECHANGED
            info["ultimo"] = alvo
            user32.SetWindowPos(hwnd, depois, x, y, w, h, flags)

    def conectar(self):
        cid = self.id.text().replace(" ", "")
        exe = achar_anydesk()
        if not cid or not exe:
            self.anotar("Falta o ID ou o AnyDesk não foi encontrado")
            return
        if self.procura:
            self.procura.stop()
        antes = {j["hwnd"] for j in janelas_anydesk()}
        try:
            subprocess.Popen([exe, cid])
        except OSError as e:
            self.anotar(f"Não deu para abrir o AnyDesk: {e}")
            return
        self.anotar(f"Rodando: {exe} {cid}")
        inicio = time.monotonic()
        vistas = {}  # hwnd -> momento em que apareceu

        def procurar():
            agora = time.monotonic()
            atuais = {j["hwnd"]: j for j in janelas_anydesk() if j["hwnd"] not in antes}
            for hwnd, j in atuais.items():
                if hwnd not in vistas:
                    vistas[hwnd] = agora
                    self.anotar("Janela nova: " + self.descrever(j))
                    self.atualizar_lista()
            for hwnd in [h for h in vistas if h not in atuais]:
                self.anotar(f"Janela {hwnd:#x} sumiu")
                del vistas[hwnd]
            # Só encaixa sozinho uma janela que já está aberta há 3 s: as primeiras que aparecem
            # costumam ser avisos de "conectando" ou de senha, que somem logo.
            firmes = [atuais[h] for h, t in vistas.items() if agora - t >= 3]
            if self.auto.isChecked() and firmes:
                self.procura.stop()
                maior = max(firmes, key=lambda j: retangulo(j["hwnd"])[2] * retangulo(j["hwnd"])[3])
                self.encaixar(maior)
            elif agora - inicio > 90:
                self.procura.stop()
                if not vistas:
                    self.anotar("Nenhuma janela nova em 90 s. A sessão pode ter aberto como aba dentro "
                                "da janela do AnyDesk: confira a opção de abrir sessões em janela nova "
                                "nas configurações do AnyDesk e tente de novo.")
                else:
                    self.anotar("Escolha a janela da sessão na lista e clique em Encaixar.")

        self.procura = QTimer(self, interval=300, timeout=procurar)
        self.procura.start()

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

    def liberar(self, info):
        """Devolve a janela ao AnyDesk como era antes de encaixar."""
        hwnd = info["hwnd"]
        if info["modo"] == "qt":
            info["janela"].setParent(None)
            info["janela"].show()
            return
        if info["modo"] == "setparent":
            user32.SetParent(hwnd, None)
        mudar_estilo(hwnd, info["estilo"])
        user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                            SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_ASYNCWINDOWPOS)
        user32.ShowWindowAsync(hwnd, SW_SHOWNA)

    def soltar_aba(self):
        alvo = self.aba_atual()
        if not alvo:
            return
        caixa = self.abas.currentWidget()
        self.anotar(f"Soltando {alvo['hwnd']:#x}")
        del self.encaixadas[caixa]
        self.abas.removeTab(self.abas.indexOf(caixa))
        self.liberar(alvo)
        QTimer.singleShot(1500, lambda: self.anotar(
            f"Soltar aba: janela ainda existe? {bool(user32.IsWindow(alvo['hwnd']))}"))

    def fechar_aba(self, indice):
        caixa = self.abas.widget(indice)
        alvo = self.encaixadas.pop(caixa, None)
        self.abas.removeTab(indice)
        if alvo:
            if alvo["modo"] != "qt":
                self.liberar(alvo)  # se o AnyDesk não fechar, a janela volta a aparecer solta
            # WM_CLOSE fecha só a janela; matar o processo poderia derrubar outras sessões.
            user32.PostMessageW(alvo["hwnd"], WM_CLOSE, 0, 0)
            self.anotar(f"Aba fechada (WM_CLOSE em {alvo['hwnd']:#x})")
            QTimer.singleShot(1500, lambda: self.anotar(
                f"Janela ainda existe? {bool(user32.IsWindow(alvo['hwnd']))}; "
                f"outras sessões: {len(self.encaixadas)}"))

    def closeEvent(self, evento):
        # Ao fechar o teste, as sessões voltam a ser janelas normais do AnyDesk.
        for info in list(self.encaixadas.values()):
            if info["modo"] != "qt":
                self.liberar(info)
        self.encaixadas.clear()
        registrar("Teste fechado")
        super().closeEvent(evento)

    def salvar_relatorio(self):
        linhas = [
            "NaView: teste no Windows",
            f"Data: {time.strftime('%d/%m/%Y %H:%M')}",
            f"Sistema: {platform.platform()} ({platform.machine()})",
            f"Python {sys.version.split()[0]}, PySide6 {PySide6.__version__}",
            f"Este app como administrador: {bool(shell32.IsUserAnAdmin())}",
            f"AnyDesk: {achar_anydesk()}",
            f"Modo de encaixe escolhido: {self.modo.currentData()}",
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
                                "Envie o arquivo relatorio-windows.txt (e também o "
                                "naview-piloto-log.txt) para quem te mandou o link.")
        os.startfile(arquivo.parent)


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("Este teste é só para Windows.")
    abrir_log()
    registrar("==== Teste aberto ====")
    sys.excepthook = erro_nao_tratado
    VIGIA.start()
    app = QApplication(sys.argv)
    if (RECURSOS / "icone.ico").is_file():
        app.setWindowIcon(QIcon(str(RECURSOS / "icone.ico")))
    janela = Teste()
    janela.show()
    if "--verificar" in sys.argv:
        QTimer.singleShot(2000, app.quit)
    sys.exit(app.exec())
