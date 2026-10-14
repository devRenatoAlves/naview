"""Tela do jogo dentro do app: uma página web (web/jogo.html) num WebKitGTK.

A página pede ações com window.webkit.messageHandlers.jogo.postMessage(...) e recebe as respostas
por window.__resposta(...). Toda regra e todo sorteio ficam no Python (progresso.py).
"""
import json
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, WebKit2  # noqa: E402

import temas  # noqa: E402

from . import catalogo as cat  # noqa: E402
from .progresso import ErroJogo  # noqa: E402

PAGINA = Path(__file__).resolve().parent.parent / "web" / "jogo.html"
NOMES_CURTOS_BAU = {"madeira": "Madeira", "prata": "Prata", "ouro": "Ouro", "magico": "Mágico",
                    "lendario": "Lendário"}


def catalogo_para_web():
    return {
        "cartas": cat.CARTAS,
        "cartas_por_id": cat.CARTAS_POR_ID,
        "raridades": cat.RARIDADES,
        "ordem_raridade": cat.ORDEM_RARIDADE,
        "tipos": cat.TIPOS,
        "baus": {t: {"nome": b["nome"], "curto": NOMES_CURTOS_BAU[t], "minutos": b["minutos"]}
                 for t, b in cat.BAUS.items()},
        "temas": {chave: {"nome": t["nome"], "previa": t["previa"], "fonte": t.get("fonte"),
                          "texto": temas.cor_texto(t["previa"][0]) or "#ffffff"}
                  for chave, t in temas.TEMAS.items()},
        "deslocamentos": {e: {a: cat.deslocamento_acessorio(e, a) for a in cat.ENCAIXE_ACESSORIO}
                          for e in cat.ENCAIXE_PET},
        "nivel_max": cat.NIVEL_MAX,
        "copias_por_nivel": cat.COPIAS_POR_NIVEL,
        "moedas_por_nivel": cat.MOEDAS_POR_NIVEL,
        "atendimentos_por_bau": cat.ATENDIMENTOS_POR_BAU,
        "atendimento_minimo_s": cat.ATENDIMENTO_MINIMO_S,
    }


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
            resposta = self._executar(pedido["acao"], pedido.get("dados") or {})
            ok = True
        except ErroJogo as erro:
            resposta, ok = str(erro), False
        self._js(f"window.__resposta({pedido['id']}, {json.dumps(ok)}, {json.dumps(resposta)},"
                 f" {json.dumps(self.estado())})")

    def _executar(self, acao, dados):
        p = self.progresso
        if acao == "estado":
            return self.estado()
        if acao == "fechar":
            self.ao_fechar()
            return None
        if acao == "equipar":
            carta = cat.CARTAS_POR_ID.get(dados["id"])
            if carta and carta["tipo"] == "tema":
                if not p.possui(carta["id"]):
                    raise ErroJogo("Você ainda não tem esse tema.")
                resultado = None
            else:
                resultado = p.equipar(dados["id"])
            self.ao_mudar("equipar", carta)
            return resultado
        acoes = {
            "destravar_bau": lambda: p.destravar_bau(dados["espaco"]),
            "abrir_bau": lambda: p.abrir_bau(dados["espaco"], dados.get("pagar", False)),
            "abrir_bau_gratis": p.abrir_bau_gratis,
            "resgatar_diario": p.resgatar_diario,
            "melhorar_carta": lambda: p.melhorar_carta(dados["id"]),
            "comprar_oferta": lambda: p.comprar_oferta(dados["indice"]),
            "comprar_petiscos": lambda: p.comprar_petiscos(dados.get("quantidade", 1)),
            "pet_acao": lambda: p.pet_acao(dados["acao"]),
            "pet_chocar": p.pet_chocar,
            "pet_renomear": lambda: p.pet_renomear(dados.get("nome")),
        }
        if acao not in acoes:
            raise ErroJogo("Ação desconhecida.")
        resultado = acoes[acao]()
        self.ao_mudar(acao, resultado)
        return resultado
