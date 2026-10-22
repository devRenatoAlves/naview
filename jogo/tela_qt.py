"""Tela do jogo dentro do app (versão Qt): a página web/jogo.html num QWebEngineView.

A página foi feita para o WebKitGTK: pede ações com window.webkit.messageHandlers.jogo.postMessage
e recebe as respostas por window.__resposta(...). Um script injetado antes da página cria esse mesmo
window.webkit em cima do QWebChannel, então jogo.js não muda. Toda regra e todo sorteio ficam no
Python (progresso.py).
"""
import json

from PySide6.QtCore import QFile, QIODevice, QObject, Qt, QUrl, Slot
from PySide6.QtGui import QColor
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView

from .progresso import ErroJogo
from .pagina import PAGINA, catalogo_para_web, executar_acao

PONTE_JS = """
(() => {
  const fila = [];
  let ponte = null;
  window.webkit = { messageHandlers: { jogo: { postMessage: (m) => ponte ? ponte.receber(m) : fila.push(m) } } };
  new QWebChannel(qt.webChannelTransport, (canal) => {
    ponte = canal.objects.ponte;
    fila.splice(0).forEach((m) => ponte.receber(m));
  });
})();
"""


def _qwebchannel_js():
    arquivo = QFile(":/qtwebchannel/qwebchannel.js")
    arquivo.open(QIODevice.ReadOnly)
    texto = bytes(arquivo.readAll()).decode()
    arquivo.close()
    return texto


class _Ponte(QObject):
    def __init__(self, tela):
        super().__init__()
        self.tela = tela

    @Slot(str)
    def receber(self, mensagem):
        self.tela._mensagem(mensagem)


class TelaJogo(QWebEngineView):
    """ao_mudar(acao, resultado): avisa o app (para aplicar tema, moldura, som, pet...)."""

    def __init__(self, progresso, tema_atual, ao_mudar, ao_fechar, pai=None):
        super().__init__(pai)
        self.progresso = progresso
        self.tema_atual = tema_atual  # função: chave do tema em uso
        self.ao_mudar = ao_mudar
        self.ao_fechar = ao_fechar
        self._pronta = False
        self._pausada = False
        self._tela_inicial = None

        self.setContextMenuPolicy(Qt.NoContextMenu)  # sem menu "Recarregar/Inspecionar"
        self.page().setBackgroundColor(QColor(20, 26, 51))  # evita piscar branco ao abrir

        script = QWebEngineScript()
        script.setName("ponte")
        script.setSourceCode(_qwebchannel_js() + PONTE_JS)
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        self.page().scripts().insert(script)

        self._ponte = _Ponte(self)
        self._canal = QWebChannel(self.page())
        self._canal.registerObject("ponte", self._ponte)
        self.page().setWebChannel(self._canal)

        self.loadFinished.connect(self._carregou)
        self.load(QUrl.fromLocalFile(str(PAGINA)))

    # ---- comunicação ----

    def _js(self, codigo):
        self.page().runJavaScript(codigo)

    def estado(self):
        estado = self.progresso.estado()
        estado["tema"] = self.tema_atual()
        return estado

    def _carregou(self, ok):
        if not ok:
            return
        self._pronta = True
        self._js(f"window.__iniciar({json.dumps(catalogo_para_web())}, {json.dumps(self.estado())},"
                 f" {json.dumps(self._tela_inicial)})")
        if self._pausada:
            self._js("window.__pausar(true)")

    def atualizar(self):
        """O app chama quando algo mudou fora da página (ex.: terminou um atendimento)."""
        if self._pronta:
            self._js(f"window.__estado({json.dumps(self.estado())})")

    def pausar(self, sim):
        """Com o jogo escondido, a página para as animações e o relógio (não gasta CPU à toa)."""
        self._pausada = sim
        if self._pronta:
            self._js(f"window.__pausar({json.dumps(sim)})")

    def mostrar(self, tela):
        if self._pronta:
            self._js(f"window.__mostrar({json.dumps(tela)})")
        else:
            self._tela_inicial = tela

    def _mensagem(self, texto):
        pedido = json.loads(texto)
        try:
            resposta = executar_acao(self.progresso, pedido["acao"], pedido.get("dados") or {},
                                     self.estado, self.ao_mudar, self.ao_fechar)
            ok = True
        except ErroJogo as erro:
            resposta, ok = str(erro), False
        self._js(f"window.__resposta({pedido['id']}, {json.dumps(ok)}, {json.dumps(resposta)},"
                 f" {json.dumps(self.estado())})")
