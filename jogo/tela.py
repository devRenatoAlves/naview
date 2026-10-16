"""Tela do jogo dentro do app: uma página web (web/jogo.html) num WebKitGTK.

A página pede ações com window.webkit.messageHandlers.jogo.postMessage(...) e recebe as respostas
por window.__resposta(...). Toda regra e todo sorteio ficam no Python (progresso.py).
"""
import json

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, WebKit2  # noqa: E402

from .pagina import PAGINA, catalogo_para_web, executar_acao  # noqa: E402
from .progresso import ErroJogo  # noqa: E402


class TelaJogo(WebKit2.WebView):
    """ao_mudar(acao, resultado): avisa o app (para aplicar tema, moldura, som, pet...)."""

    def __init__(self, progresso, tema_atual, ao_mudar, ao_fechar):
        gerente = WebKit2.UserContentManager()
        super().__init__(user_content_manager=gerente)
        self.progresso = progresso
        self.tema_atual = tema_atual  # função: chave do tema em uso
        self.ao_mudar = ao_mudar
        self.ao_fechar = ao_fechar
        self._pronta = False
        self._tela_inicial = None

        config = self.get_settings()
        config.set_allow_file_access_from_file_urls(True)
        config.set_enable_developer_extras(False)
        config.set_enable_back_forward_navigation_gestures(False)
        self.set_background_color(Gdk.RGBA(0.08, 0.10, 0.20, 1))  # evita piscar branco ao abrir

        gerente.register_script_message_handler("jogo")
        gerente.connect("script-message-received::jogo", self._mensagem)
        self.connect("context-menu", lambda *_a: True)  # sem menu "Recarregar/Inspecionar"
        self.connect("load-changed", self._carregou)
        self.load_uri(PAGINA.as_uri())

    # ---- comunicação ----

    def _js(self, codigo):
        if hasattr(self, "evaluate_javascript"):
            self.evaluate_javascript(codigo, -1, None, None, None, None, None)
        else:
            self.run_javascript(codigo, None, None, None)

    def estado(self):
        estado = self.progresso.estado()
        estado["tema"] = self.tema_atual()
        return estado

    def _carregou(self, _view, evento):
        if evento != WebKit2.LoadEvent.FINISHED:
            return
        self._pronta = True
        self._js(f"window.__iniciar({json.dumps(catalogo_para_web())}, {json.dumps(self.estado())},"
                 f" {json.dumps(self._tela_inicial)})")

    def atualizar(self):
        """O app chama quando algo mudou fora da página (ex.: terminou um atendimento)."""
        if self._pronta:
            self._js(f"window.__estado({json.dumps(self.estado())})")

    def mostrar(self, tela):
        if self._pronta:
            self._js(f"window.__mostrar({json.dumps(tela)})")
        else:
            self._tela_inicial = tela

    def _mensagem(self, _gerente, resultado):
        valor = resultado.get_js_value() if hasattr(resultado, "get_js_value") else resultado
        pedido = json.loads(valor.to_string())
        try:
            resposta = executar_acao(self.progresso, pedido["acao"], pedido.get("dados") or {},
                                     self.estado, self.ao_mudar, self.ao_fechar)
            ok = True
        except ErroJogo as erro:
            resposta, ok = str(erro), False
        self._js(f"window.__resposta({pedido['id']}, {json.dumps(ok)}, {json.dumps(resposta)},"
                 f" {json.dumps(self.estado())})")
