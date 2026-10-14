#!/usr/bin/env python3
"""NaView: várias conexões do AnyDesk em abas numa única janela.

Funciona no KDE Wayland porque tanto este app quanto o AnyDesk rodam via XWayland
(GDK_BACKEND=x11), o que permite encaixar a janela do AnyDesk dentro de uma aba.
"""
import math
import os
import re
import signal
import subprocess
import time
from pathlib import Path

os.environ["GDK_BACKEND"] = "x11"  # precisa vir antes de importar o Gtk

import fontes  # noqa: E402

fontes.carregar()  # antes do Gtk: as fontes dos temas precisam existir quando o Pango iniciar

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GLib  # noqa: E402

# Nome da janela para o KDE: liga ela ao atalho naview.desktop (StartupWMClass)
# e faz a barra de tarefas mostrar o ícone certo. Precisa vir antes de importar o Gtk,
# que fixa esse nome ao ser importado.
GLib.set_prgname("naview")

from gi.repository import Gdk, GdkPixbuf, Gtk, Pango  # noqa: E402

# Ícones Phosphor (icones/gtk/ph-*-symbolic.svg): o GTK pinta com a cor do texto do tema.
fontes.registrar_icones()


def migrar_pastas_antigas():
    """Renomeia as pastas de dados do nome antigo (anydesk-tabs) para naview, uma vez só."""
    for base in (".config", ".cache", ".local/share"):
        antiga, nova = Path.home() / base / "anydesk-tabs", Path.home() / base / "naview"
        if antiga.is_dir() and not nova.exists():
            antiga.rename(nova)


migrar_pastas_antigas()  # antes de temas, contatos e progresso lerem os arquivos

import temas  # noqa: E402
from contatos import Contatos, formatar_id  # noqa: E402
from jogo import catalogo as cat_jogo  # noqa: E402
from jogo.gtk import Notificacoes, Sons, compor_pet  # noqa: E402
from jogo.progresso import Progresso  # noqa: E402
from janela_aparencia import JanelaAparencia  # noqa: E402
from x11 import X11  # noqa: E402

ANYDESK_CLASS = "anydesk"
DETECT_TIMEOUT_MS = 60_000
POLL_MS = 500
TITULO_MS = 2_000
FOCO_MS = 80
AVISO_MS = 4_000
N_CORES_AVATAR = 6

ALINHAMENTO = {"start": Gtk.Align.START, "end": Gtk.Align.END, "center": Gtk.Align.CENTER}


def limpar_titulo(titulo):
    """Tira o 'AnyDesk' do título da janela da sessão, deixando o nome do computador."""
    texto = re.sub(r"\s*[-–|]?\s*AnyDesk\s*[-–|]?\s*", " ", titulo or "", flags=re.I)
    return texto.strip(" -–|")


def id_no_titulo(titulo):
    """Acha um ID do AnyDesk (9-10 dígitos, com ou sem espaços) no título."""
    achado = re.search(r"\d[\d ]{7,12}\d", titulo or "")
    return achado.group().replace(" ", "") if achado else None


def iniciais(nome, cid):
    if nome:
        partes = nome.split()
        letras = partes[0][0] + (partes[1][0] if len(partes) > 1 else partes[0][1:2])
        return letras.upper()
    return (cid or "?")[-2:]


def cor_avatar(cid):
    """Mesma cor sempre para o mesmo contato."""
    return sum(map(ord, cid or "")) % N_CORES_AVATAR


def icone(nome, tamanho=Gtk.IconSize.BUTTON):
    return Gtk.Image.new_from_icon_name(nome, tamanho)


def classes(widget, *nomes):
    contexto = widget.get_style_context()
    for nome in nomes:
        contexto.add_class(nome)
    return widget


def retangulos_arredondados(x, y, w, h, r):
    """Aproxima um retângulo de cantos arredondados com faixas horizontais (região de desfoque)."""
    if r <= 0:
        return [(x, y, w, h)]
    rects = [(x, y + r, w, h - 2 * r)]
    for i in range(0, r, 2):
        recuo = int(round(r - math.sqrt(r * r - (r - i - 1) ** 2)))
        rects.append((x + recuo, y + i, w - 2 * recuo, 2))
        rects.append((x + recuo, y + h - i - 2, w - 2 * recuo, 2))
    return rects


class Aba:
    """Uma conexão: a janela X11 do AnyDesk dentro de um Gtk.Socket."""

    def __init__(self, cid):
        self.cid = cid  # ID ou apelido usado para conectar (None se capturada sem ID no título)
        self.xid = None
        self.pid = None
        self.socket = Gtk.Socket()
        # width_chars = largura mínima; sem isso o GTK encolhe o nome da aba para "…".
        self.rotulo = Gtk.Label(ellipsize=Pango.EllipsizeMode.END, width_chars=16, max_width_chars=26)
        self.spinner = Gtk.Spinner(active=True)
        self.ponto = classes(Gtk.Box(valign=Gtk.Align.CENTER, no_show_all=True),
                             "avatar", "mini", f"avatar-{cor_avatar(cid)}")
        self.cabeca = Gtk.EventBox(visible_window=False)  # o "rótulo" da aba inteiro
        self.inicio = None  # quando a sessão foi encaixada (para contar o atendimento)


class LinhaContato(Gtk.ListBoxRow):
    def __init__(self, cid, nome, ao_renomear):
        super().__init__()
        self.cid = cid
        self.nome = nome

        caixa = Gtk.Box(spacing=10)
        avatar = classes(Gtk.Label(label=iniciais(nome, cid)), "avatar", f"avatar-{cor_avatar(cid)}")
        avatar.set_valign(Gtk.Align.CENTER)

        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1, valign=Gtk.Align.CENTER)
        principal = classes(Gtk.Label(label=nome or formatar_id(cid), xalign=0,
                                      ellipsize=Pango.EllipsizeMode.END), "contato-nome")
        textos.pack_start(principal, False, False, 0)
        if nome:
            textos.pack_start(classes(Gtk.Label(label=formatar_id(cid), xalign=0), "contato-id"),
                              False, False, 0)

        self.ponto = classes(Gtk.Label(label="●", no_show_all=True, tooltip_text="Conectado"),
                             "ponto-online")
        editar = Gtk.Button(image=icone("ph-pencil-simple-symbolic"), tooltip_text="Renomear",
                            relief=Gtk.ReliefStyle.NONE, valign=Gtk.Align.CENTER)
        classes(editar, "bt-editar")
        editar.connect("clicked", lambda b: ao_renomear(cid, b))

        caixa.pack_start(avatar, False, False, 0)
        caixa.pack_start(textos, True, True, 0)
        caixa.pack_start(self.ponto, False, False, 0)
        caixa.pack_start(editar, False, False, 0)
        self.add(caixa)

    def combina(self, busca):
        busca = busca.lower().replace(" ", "")
        return not busca or busca in (self.nome or "").lower().replace(" ", "") or busca in self.cid


class App(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_default_size(1280, 820)
        self.set_icon_name("naview")
        classes(self, "janela-principal")
        # Visual com canal alfa: permite o tema "Vidro líquido" (janela transparente com desfoque).
        visual = self.get_screen().get_rgba_visual()
        if visual and self.get_screen().is_composited():
            self.set_visual(visual)

        self.x = X11()
        self.contatos = Contatos()
        self.abas = []
        self._lista_atual = None
        self._aviso_timer = None
        self._decor = []
        self._regiao_vidro = ()  # () = ainda não enviada; None = desfoque desligado
        self.cfg = temas.carregar()
        self.progresso = Progresso(tema_atual=self.cfg["tema"])
        self.sons = Sons()
        self.notificacoes = Notificacoes()
        self.tela_jogo = None  # criada só na primeira vez que o jogo abre (o WebKit é pesado)
        self._antes_do_jogo = "inicio"
        self._sincronizando_jogo = False
        self._baus_prontos = set()
        self._diario_avisado = None

        tela = Gdk.Screen.get_default()
        fixo = Gtk.CssProvider()
        fixo.load_from_data(temas.css_previas())
        Gtk.StyleContext.add_provider_for_screen(tela, fixo, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.estilo_tema = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(tela, self.estilo_tema,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)

        self.set_titlebar(self.montar_cabecalho())
        self.lateral = self.montar_lateral()
        # A barra desliza POR CIMA do conteúdo (Overlay). Se ela empurrasse o conteúdo, a área
        # principal (e a sessão do AnyDesk) seria redimensionada e redesenhada a cada quadro da
        # animação, o que travava tudo. Assim o conteúdo muda de largura uma vez só.
        self.revelador = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_RIGHT,
                                      transition_duration=200, reveal_child=self.cfg["lateral_visivel"],
                                      halign=Gtk.Align.START)
        self.revelador.add(self.lateral)
        # Ao abrir o app a barra ainda não tem tamanho quando a margem é calculada (dava 0 e o
        # jogo ficava por baixo dela). Então a margem acompanha a largura real da barra.
        self.revelador.connect("size-allocate", self._sincronizar_margem)

        self.notebook = classes(Gtk.Notebook(scrollable=True, show_border=False), "abas")
        # Trocou de aba: o teclado vai para a sessão dessa aba (ver manter_foco).
        self.notebook.connect("switch-page", lambda *_a: self.set_focus(None))
        mais = Gtk.Button(image=icone("ph-plus-symbolic"), tooltip_text="Nova conexão (Ctrl+F)",
                          relief=Gtk.ReliefStyle.NONE)
        mais.connect("clicked", lambda _b: self.ir_para_busca())
        mais.show()
        self.notebook.set_action_widget(mais, Gtk.PackType.END)

        self.pilha = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE,
                               transition_duration=180)
        self.pilha.add_named(self.montar_inicio(), "inicio")
        self.pilha.add_named(self.notebook, "abas")

        conteudo = Gtk.Overlay()
        conteudo.add(self.pilha)
        conteudo.add_overlay(self.revelador)
        self.raiz = classes(Gtk.Box(), "raiz")
        self.raiz.pack_start(conteudo, True, True, 0)
        self.raiz.connect("size-allocate", lambda *_a: self.agendar_vidro())

        sobreposicao = Gtk.Overlay()
        sobreposicao.add(self.raiz)
        sobreposicao.add_overlay(self.montar_aviso())
        sobreposicao.set_overlay_pass_through(self.aviso, True)
        self.add(sobreposicao)

        self.aplicar_tema()
        self.carregar_contatos()
        self.atualizar_pet_mini()
        self.atualizar_selo()
        self.connect("focus-in-event", lambda *_a: self.carregar_contatos())
        self.connect("delete-event", self.on_sair)
        self.connect("set-focus", self.on_foco_widget)
        self.connect("key-press-event", self.on_tecla)
        self.connect("realize", lambda *_a: self.agendar_vidro())
        GLib.timeout_add(TITULO_MS, self.atualizar_titulos)
        GLib.timeout_add(FOCO_MS, self.manter_foco)
        GLib.timeout_add_seconds(60, self.batimento)

    # ---- montagem da interface -------------------------------------------------

    def montar_cabecalho(self):
        self.cabecalho = Gtk.HeaderBar(show_close_button=True, title="NaView")
        self.bt_lateral = Gtk.ToggleButton(image=icone("ph-sidebar-simple-symbolic"),
                                           active=self.cfg["lateral_visivel"],
                                           tooltip_text="Mostrar/esconder contatos (F9)")
        self.bt_lateral.connect("toggled", self.on_alternar_lateral)
        self.cabecalho.pack_start(self.bt_lateral)

        menu = Gtk.Popover()
        itens = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=8)
        for texto, acao in (("Aparência e temas…", self.abrir_aparencia),
                            ("Capturar janela do AnyDesk…", self.on_capturar)):
            item = Gtk.ModelButton(text=texto)
            item.connect("clicked", lambda _b, a=acao: a())
            itens.pack_start(item, False, False, 0)
        itens.show_all()
        menu.add(itens)
        self.cabecalho.pack_end(Gtk.MenuButton(image=icone("ph-dots-three-vertical-symbolic"), popover=menu,
                                               tooltip_text="Menu"))

        aparencia = Gtk.Button(image=icone("ph-palette-symbolic"), tooltip_text="Aparência e temas")
        aparencia.connect("clicked", lambda _b: self.abrir_aparencia())
        self.cabecalho.pack_end(aparencia)

        self.bt_jogo = Gtk.ToggleButton(image=icone("ph-gift-symbolic"), tooltip_text="Baús, coleção e pet")
        self.bt_jogo.connect("toggled", self.on_alternar_jogo)
        self.selo_jogo = classes(Gtk.Label(halign=Gtk.Align.END, valign=Gtk.Align.START,
                                           no_show_all=True), "selo")
        caixa_jogo = Gtk.Overlay()
        caixa_jogo.add(self.bt_jogo)
        caixa_jogo.add_overlay(self.selo_jogo)
        caixa_jogo.set_overlay_pass_through(self.selo_jogo, True)
        self.cabecalho.pack_end(caixa_jogo)
        return self.cabecalho

    def montar_lateral(self):
        cabeca = Gtk.Box(margin_start=16, margin_end=16, margin_top=14, margin_bottom=8)
        cabeca.pack_start(classes(Gtk.Label(label="Contatos", xalign=0), "titulo-lateral"),
                          True, True, 0)
        self.contagem = classes(Gtk.Label(), "contagem")
        cabeca.pack_end(self.contagem, False, False, 0)

        self.busca = Gtk.SearchEntry(placeholder_text="Buscar ou digitar um ID",
                                     margin_start=12, margin_end=12, margin_bottom=8)
        self.busca.connect("search-changed", lambda _e: self.lista.invalidate_filter())
        self.busca.connect("activate", self.on_busca_enter)

        self.lista = Gtk.ListBox(activate_on_single_click=False)
        self.lista.set_filter_func(lambda linha: linha.combina(self.busca.get_text()))
        self.lista.connect("row-activated", lambda _l, linha: self.abrir(linha.cid))
        vazio = classes(Gtk.Label(label="Nenhum contato encontrado.\n"
                                        "Aperte Enter para conectar no ID digitado.",
                                  justify=Gtk.Justification.CENTER, wrap=True), "vazio")
        vazio.show()
        self.lista.set_placeholder(vazio)
        rolagem = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        rolagem.add(self.lista)

        lateral = classes(Gtk.Box(orientation=Gtk.Orientation.VERTICAL), "sidebar")
        lateral.set_size_request(290, -1)
        lateral.pack_start(cabeca, False, False, 0)
        lateral.pack_start(self.busca, False, False, 0)
        lateral.pack_start(rolagem, True, True, 0)
        lateral.pack_start(self.montar_pet_mini(), False, False, 0)
        return lateral

    def montar_pet_mini(self):
        """Pet no rodapé da barra de contatos; clicar abre a aba do pet no jogo."""
        self.pet_imagem = Gtk.Image(valign=Gtk.Align.END)
        self.pet_nome = classes(Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END), "pet-nome")
        self.pet_humor = Gtk.Image()  # ícone do humor ao lado do nome
        self.pet_fala = classes(Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END), "pet-fala")
        linha_nome = Gtk.Box(spacing=6)
        linha_nome.pack_start(self.pet_nome, False, False, 0)
        linha_nome.pack_start(self.pet_humor, False, False, 0)
        textos = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, valign=Gtk.Align.CENTER)
        textos.pack_start(linha_nome, False, False, 0)
        textos.pack_start(self.pet_fala, False, False, 0)
        linha = classes(Gtk.Box(spacing=10), "pet-rodape")
        linha.pack_start(self.pet_imagem, False, False, 0)
        linha.pack_start(textos, True, True, 0)
        caixa = Gtk.EventBox(visible_window=False, tooltip_text="Cuidar do pet")
        caixa.add(linha)
        caixa.connect("button-press-event", lambda *_a: self.abrir_jogo("pet"))
        return caixa

    def montar_inicio(self):
        self.inicio = Gtk.Overlay()
        self.inicio.add(classes(Gtk.Box(), "inicio"))

        # Sem quebra de linha: com fontes grandes de tema, a quebra sobrepunha o subtítulo.
        self.titulo_inicio = classes(Gtk.Label(justify=Gtk.Justification.CENTER), "titulo-inicio")
        self.cursor = classes(Gtk.Label(label="█", no_show_all=True), "titulo-inicio", "cursor")
        linha_titulo = Gtk.Box(halign=Gtk.Align.CENTER, spacing=4)
        linha_titulo.pack_start(self.titulo_inicio, False, False, 0)
        linha_titulo.pack_start(self.cursor, False, False, 0)
        self.sub_inicio = classes(Gtk.Label(justify=Gtk.Justification.CENTER, wrap=True), "sub-inicio")

        self.entrada_rapida = Gtk.Entry(placeholder_text="ID do AnyDesk", hexpand=True)
        self.entrada_rapida.connect("activate", self.on_conectar_rapido)
        botao = classes(Gtk.Button(label="Conectar"), "conectar")
        botao.connect("clicked", self.on_conectar_rapido)
        linha = Gtk.Box(spacing=8, margin_top=16)
        linha.pack_start(self.entrada_rapida, True, True, 0)
        linha.pack_start(botao, False, False, 0)

        self.cartao = classes(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                                      halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER), "cartao-conectar")
        self.cartao.set_size_request(440, -1)
        self.cartao.pack_start(linha_titulo, False, False, 0)
        self.cartao.pack_start(self.sub_inicio, False, False, 0)
        self.cartao.pack_start(linha, False, False, 0)
        self.inicio.add_overlay(self.cartao)
        return self.inicio

    def montar_aviso(self):
        self.aviso = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_UP,
                                  halign=Gtk.Align.CENTER, valign=Gtk.Align.END)
        self.icone_aviso = Gtk.Image(no_show_all=True)
        self.texto_aviso = Gtk.Label(wrap=True, max_width_chars=60)
        caixa = classes(Gtk.Box(spacing=8), "aviso")
        caixa.pack_start(self.icone_aviso, False, False, 0)
        caixa.pack_start(self.texto_aviso, False, False, 0)
        self.aviso.add(caixa)
        return self.aviso

    def montar_decor(self):
        """Desenhos do tema na tela inicial (por cima do fundo, por baixo do cartão)."""
        for widget in self._decor:
            widget.destroy()
        self._decor = []
        tema = temas.TEMAS[self.cfg["tema"]]
        if not self.cfg.get("decoracoes", True):
            return
        for i, d in enumerate(tema.get("decor", [])):
            tipo = d.get("tipo", "imagem")
            if tipo == "faixa":
                widget = classes(Gtk.Box(valign=Gtk.Align.END, hexpand=True,
                                         margin_bottom=d.get("margem_baixo", 0)), f"decor-faixa-{i}")
                widget.set_size_request(-1, d["altura"])
            elif tipo == "texto":
                widget = classes(Gtk.Label(label=d["texto"]), "decor-texto")
            else:
                caminho = str(temas.ARTE / d["arte"])
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(caminho, d["w"], d["h"], True)
                imagem = Gtk.Image.new_from_pixbuf(pixbuf)
                if d.get("anim"):
                    classes(imagem, f"anim-{d['anim']}")
                widget = imagem
                if d.get("texto"):  # ex.: "POW!" por cima da explosão
                    widget = Gtk.Overlay()
                    widget.add(imagem)
                    widget.add_overlay(classes(Gtk.Label(label=d["texto"]), "decor-texto"))
            if tipo != "faixa":
                widget.set_halign(ALINHAMENTO[d.get("halign", "start")])
                widget.set_valign(ALINHAMENTO[d.get("valign", "start")])
                cima, direita, baixo, esquerda = d.get("margem", (0, 0, 0, 0))
                widget.set_margin_top(cima)
                widget.set_margin_end(direita)
                widget.set_margin_bottom(baixo)
                widget.set_margin_start(esquerda)
            self.inicio.add_overlay(widget)
            self.inicio.set_overlay_pass_through(widget, True)
            widget.show_all()
            self._decor.append(widget)
        self.inicio.reorder_overlay(self.cartao, -1)  # cartão sempre por cima dos desenhos

    # ---- tema e aparência -------------------------------------------------------

    def aplicar_tema(self):
        # Tema no nível máximo da coleção ganha a versão dourada; a moldura vem do jogo.
        dourado = self.progresso.nivel_carta(f"tema-{self.cfg['tema']}") >= cat_jogo.NIVEL_MAX
        self.estilo_tema.load_from_data(temas.gerar_css(
            self.cfg, dourado=dourado, moldura=self.progresso.equipados()["moldura"]))
        tema = temas.TEMAS[self.cfg["tema"]]
        titulo, sub = tema.get("frases", ("Nenhuma conexão aberta",
                                          "Digite um ID ou escolha um contato à esquerda"))
        self.titulo_inicio.set_text(titulo)
        self.sub_inicio.set_text(sub)
        self.cursor.set_visible(bool(tema.get("cursor")))
        self.montar_decor()
        self.ajustar_margem_conteudo()  # o tema pode mudar a largura da barra (ex.: vidro)
        self.agendar_vidro()

    def abrir_aparencia(self):
        def ao_mudar():
            self.aplicar_tema()
            temas.salvar(self.cfg)

        JanelaAparencia(self, self.cfg, ao_mudar, possui=self.progresso.possui_tema).present()

    def ajustar_margem_conteudo(self):
        """Abre espaço para a barra lateral (de uma vez, não a cada quadro da animação)."""
        largura = self.lateral.get_preferred_width()[1] if self.bt_lateral.get_active() else 0
        self.pilha.set_margin_start(largura)

    def _sincronizar_margem(self, revelador, alocacao):
        if not (self.bt_lateral.get_active() and revelador.get_child_revealed()):
            return  # durante a animação a largura muda a cada quadro: espera terminar
        if self.pilha.get_margin_start() != alocacao.width:
            # Fora do size-allocate: mudar a margem aqui dentro pediria outro layout no meio deste.
            GLib.idle_add(lambda: self.pilha.set_margin_start(alocacao.width) or False)

    def on_alternar_lateral(self, botao):
        self.ajustar_margem_conteudo()
        self.revelador.set_reveal_child(botao.get_active())
        self.cfg["lateral_visivel"] = botao.get_active()
        temas.salvar(self.cfg)

    def agendar_vidro(self):
        if not getattr(self, "_vidro_agendado", False):
            self._vidro_agendado = True
            GLib.idle_add(self.atualizar_vidro)

    def atualizar_vidro(self, *_args):
        """Tema vidro: pede ao KWin para desfocar o que está atrás da janela inteira."""
        self._vidro_agendado = False
        janela = self.get_window()
        if not janela:
            return False
        if not temas.TEMAS[self.cfg["tema"]].get("vidro"):
            if self._regiao_vidro is not None:
                self.x.set_blur(janela.get_xid(), None)
                self._regiao_vidro = None
            return False
        # Área útil = barra de título + conteúdo (sem a sombra da janela, que fica em volta).
        cx, cy = self.cabecalho.translate_coordinates(self, 0, 0) or (0, 0)
        rx, ry = self.raiz.translate_coordinates(self, 0, 0) or (0, 0)
        largura = self.raiz.get_allocated_width()
        altura = ry + self.raiz.get_allocated_height() - cy
        maximizada = bool(janela.get_state() & Gdk.WindowState.MAXIMIZED)
        regiao = retangulos_arredondados(rx, cy, largura, altura, 0 if maximizada else 10)
        if regiao != self._regiao_vidro:  # evita avisar o KDE à toa
            self.x.set_blur(janela.get_xid(), regiao)
            self._regiao_vidro = regiao
        return False

    # ---- jogo (baús, coleção e pet) ----------------------------------------------

    def on_alternar_jogo(self, botao):
        if self._sincronizando_jogo:
            return
        if botao.get_active():
            self.abrir_jogo()
        else:
            self.fechar_jogo()

    def _marcar_botao_jogo(self, ativo):
        self._sincronizando_jogo = True
        self.bt_jogo.set_active(ativo)
        self._sincronizando_jogo = False

    def abrir_jogo(self, tela=None):
        if self.tela_jogo is None:
            from jogo.tela import TelaJogo  # WebKit só é carregado quando precisa
            self.tela_jogo = TelaJogo(self.progresso, lambda: self.cfg["tema"], self.ao_mudar_jogo,
                                      self.fechar_jogo)
            self.tela_jogo.show()
            self.pilha.add_named(self.tela_jogo, "jogo")
        if tela:
            self.tela_jogo.mostrar(tela)
        visivel = self.pilha.get_visible_child_name()
        if visivel != "jogo":
            self._antes_do_jogo = visivel
        self.tela_jogo.atualizar()
        self.pilha.set_visible_child_name("jogo")
        self._marcar_botao_jogo(True)
        if self.get_window():
            self.x.set_focus(self.get_window().get_xid())  # teclado sai da sessão e vem para o jogo
        self.tela_jogo.grab_focus()
        return True

    def fechar_jogo(self):
        if self.pilha.get_visible_child_name() == "jogo":
            self.pilha.set_visible_child_name("abas" if self.abas else "inicio")
        self._marcar_botao_jogo(False)
        self.set_focus(None)

    def ao_mudar_jogo(self, acao, resultado):
        """A tela do jogo mudou algo que o app mostra (tema, moldura, pet, moedas...)."""
        if acao == "equipar" and resultado and resultado["tipo"] == "tema":
            self.cfg["tema"] = resultado["alvo"]
            self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
            self.cfg["imagem"] = None
            temas.salvar(self.cfg)
        if acao in ("equipar", "melhorar_carta"):
            self.aplicar_tema()
        self.atualizar_pet_mini()
        self.atualizar_selo()

    def registrar_atendimento(self, aba):
        if not aba.inicio:
            return
        nivel_antes = self.progresso.perfil()["nivel"]
        resultado = self.progresso.registrar_atendimento(aba.cid, time.monotonic() - aba.inicio)
        aba.inicio = None
        if not resultado:
            return  # sessão curta demais
        nivel = self.progresso.perfil()["nivel"]
        # Subir de nível é só comemoração, sem prêmio (como conquista de videogame).
        subiu = f"Você chegou ao nível {nivel}! " if nivel > nivel_antes else ""
        if resultado["bau"]:
            nome = cat_jogo.BAUS[resultado["bau"]]["nome"]
            self.avisar(f"{subiu}Você ganhou um {nome}! Abra no botão do jogo.", "gift")
            if not self.is_active():
                self.notificacoes.mostrar("Novo baú!", f"Você ganhou um {nome}.")
        elif subiu:
            self.avisar(subiu.strip(), "star")
        else:
            self.avisar(f"+{resultado['moedas']} moedas · {resultado['rumo_ao_bau']}/"
                        f"{cat_jogo.ATENDIMENTOS_POR_BAU} atendimentos para o próximo baú", "coins")
        self.atualizar_selo()
        self.atualizar_pet_mini()
        if self.tela_jogo:
            self.tela_jogo.atualizar()

    def atualizar_selo(self):
        n = self.progresso.novidades()
        self.selo_jogo.set_text(str(n))
        self.selo_jogo.set_visible(n > 0)

    def atualizar_pet_mini(self, pet=None):
        pet = pet or self.progresso.pet()
        self.pet_imagem.set_from_pixbuf(compor_pet(pet["especie"], pet["acessorio"], 3))
        humor = {"feliz": "smiley", "normal": "smiley-meh", "triste": "smiley-sad", "dormindo": "moon-stars"}
        icone = humor.get(pet["humor"], "smiley") if pet["chocado"] else "egg"
        self.pet_nome.set_text(pet["nome"])
        self.pet_humor.set_from_icon_name(f"ph-{icone}-symbolic", Gtk.IconSize.MENU)
        dicas = {"feliz": "Feliz", "normal": "Tranquilo", "triste": "Precisa de você", "dormindo": "Dormindo"}
        self.pet_humor.set_tooltip_text(dicas.get(pet["humor"], "") if pet["chocado"] else "Ovo")
        self.pet_fala.set_text(pet["fala"])
        # Animação só sem sessão aberta (com sessão, nada fica animando).
        contexto = self.pet_imagem.get_style_context()
        if pet["chocado"] and pet["humor"] == "feliz" and not self.abas:
            contexto.add_class("anim-flutuar-lento")
        else:
            contexto.remove_class("anim-flutuar-lento")

    def batimento(self):
        """A cada minuto: pet acordado, avisos de baú pronto e da recompensa diária."""
        self.progresso.pet_batimento()
        estado = self.progresso.estado()
        prontos = {(b["espaco"], b["tipo"]) for b in estado["baus"] if b and b["situacao"] == "pronto"}
        for _espaco, tipo in prontos - self._baus_prontos:
            nome = cat_jogo.BAUS[tipo]["nome"]
            if self.is_active():
                self.avisar(f"{nome} pronto para abrir!", "gift")
            else:
                self.notificacoes.mostrar("Baú pronto!", f"Seu {nome} já pode ser aberto.")
        self._baus_prontos = prontos
        hoje = time.strftime("%Y-%m-%d")
        if estado["diario"]["disponivel"] and self._diario_avisado != hoje:
            self._diario_avisado = hoje
            self.notificacoes.mostrar("Recompensa diária", "Sua recompensa de hoje está esperando!")
        self.atualizar_selo()
        self.atualizar_pet_mini(estado["pet"])
        if self.tela_jogo and self.pilha.get_visible_child_name() == "jogo":
            self.tela_jogo.atualizar()
        return True

    # ---- teclado -------------------------------------------------------------
    #
    # A janela do AnyDesk não fala o protocolo XEMBED, então o Gtk.Socket não repassa o
    # teclado direito para ela (atalhos e teclas especiais se perdem). Solução: enquanto
    # uma sessão está na tela, o foco do teclado do X11 fica direto na janela do AnyDesk.

    def aba_atual(self):
        if self.pilha.get_visible_child_name() != "abas":
            return None  # jogo aberto: o teclado fica no app
        pagina = self.notebook.get_nth_page(self.notebook.get_current_page())
        return next((a for a in self.abas if a.socket is pagina and a.xid), None)

    def digitando_no_app(self):
        return isinstance(self.get_focus(), Gtk.Entry)

    def on_foco_widget(self, _janela, widget):
        # Clicou num campo de texto do app: o teclado volta para o app.
        if isinstance(widget, Gtk.Entry) and self.get_window():
            self.x.set_focus(self.get_window().get_xid())

    def manter_foco(self):
        aba = self.aba_atual()
        if not aba or not self.is_active():
            return True
        if self.digitando_no_app():
            # Clicou na tela da sessão enquanto digitava: devolve o teclado ao AnyDesk.
            if not self.x.clicked_inside(aba.xid):
                return True
            self.set_focus(None)
        if not self.x.contains(aba.xid, self.x.focused()):
            self.x.set_focus(aba.xid)
        return True

    def on_tecla(self, _janela, evento):
        # Só chega aqui quando o teclado está no app (não numa sessão).
        if evento.keyval == Gdk.KEY_F9:
            self.bt_lateral.set_active(not self.bt_lateral.get_active())
            return True
        if evento.state & Gdk.ModifierType.CONTROL_MASK and evento.keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.ir_para_busca()
            return True
        return False

    def ir_para_busca(self):
        self.bt_lateral.set_active(True)
        self.busca.grab_focus()

    # ---- avisos ----------------------------------------------------------------

    def avisar(self, texto, icone=None):
        """icone: nome de um ícone Phosphor (ex.: "gift"), sem o prefixo ph-."""
        self.texto_aviso.set_text(texto)
        if icone:
            self.icone_aviso.set_from_icon_name(f"ph-{icone}-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.icone_aviso.set_visible(bool(icone))
        self.aviso.set_reveal_child(True)
        if self._aviso_timer:
            GLib.source_remove(self._aviso_timer)

        def esconder():
            self._aviso_timer = None
            self.aviso.set_reveal_child(False)
            return False

        self._aviso_timer = GLib.timeout_add(AVISO_MS, esconder)

    # ---- contatos --------------------------------------------------------------

    def carregar_contatos(self):
        itens = self.contatos.listar()
        if itens == self._lista_atual:
            return False  # nada mudou; evita perder a seleção
        self._lista_atual = itens
        for linha in self.lista.get_children():
            self.lista.remove(linha)
        for cid, nome in itens:
            self.lista.add(LinhaContato(cid, nome, self.on_renomear))
        self.lista.show_all()
        self.contagem.set_text(str(len(itens)))
        self.marcar_conectados()
        return False

    def marcar_conectados(self):
        conectados = {a.cid for a in self.abas}
        for linha in self.lista.get_children():
            linha.ponto.set_visible(linha.cid in conectados)

    def on_renomear(self, cid, botao):
        balao = Gtk.Popover(relative_to=botao, position=Gtk.PositionType.RIGHT)
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=12)
        caixa.pack_start(Gtk.Label(label=f"Nome para {formatar_id(cid)}", xalign=0), False, False, 0)
        entrada = Gtk.Entry(text=self.contatos.nome(cid), placeholder_text="Ex.: Padaria – caixa 1",
                            width_chars=26)
        caixa.pack_start(entrada, False, False, 0)
        botoes = Gtk.Box(spacing=6, halign=Gtk.Align.END)
        remover = Gtk.Button(label="Sem nome")
        salvar = classes(Gtk.Button(label="Salvar"), "suggested-action")
        botoes.pack_start(remover, False, False, 0)
        botoes.pack_start(salvar, False, False, 0)
        caixa.pack_start(botoes, False, False, 0)
        balao.add(caixa)

        def gravar(nome):
            self.contatos.renomear(cid, nome)
            balao.popdown()
            self.carregar_contatos()
            self.atualizar_titulos()

        salvar.connect("clicked", lambda _b: gravar(entrada.get_text().strip()))
        entrada.connect("activate", lambda _e: gravar(entrada.get_text().strip()))
        remover.connect("clicked", lambda _b: gravar(""))
        caixa.show_all()
        balao.popup()
        entrada.grab_focus()

    def on_busca_enter(self, _entrada):
        texto = self.busca.get_text().strip()
        visiveis = [linha for linha in self.lista.get_children() if linha.combina(texto)]
        if texto and len(visiveis) == 1:
            self.abrir(visiveis[0].cid)
        elif texto:
            self.abrir_texto(texto)
        self.busca.set_text("")

    def on_conectar_rapido(self, _widget):
        texto = self.entrada_rapida.get_text().strip()
        if texto:
            self.abrir_texto(texto)
            self.entrada_rapida.set_text("")

    def abrir_texto(self, texto):
        sem_espacos = texto.replace(" ", "")
        self.abrir(sem_espacos if sem_espacos.isdigit() else texto)

    # ---- conexões --------------------------------------------------------------

    def janelas_livres(self):
        """Janelas do AnyDesk visíveis que ainda não estão em nenhuma aba."""
        encaixadas = {a.xid for a in self.abas}
        return [w for w in self.x.find_windows(ANYDESK_CLASS) if w not in encaixadas]

    def abrir(self, cid):
        # Já conectado: só mostra a aba.
        for aba in self.abas:
            if aba.cid == cid:
                self.notebook.set_current_page(self.notebook.page_num(aba.socket))
                return

        antes = set(self.janelas_livres())
        env = dict(os.environ, GDK_BACKEND="x11")
        proc = subprocess.Popen(["anydesk", cid], env=env, start_new_session=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        aba = self.nova_aba(cid)
        aba.pid = proc.pid
        inicio = GLib.get_monotonic_time()

        def procurar():
            if aba not in self.abas:
                return False  # aba fechada enquanto conectava
            livres = self.janelas_livres()
            # Cada "anydesk <ID>" sobe um processo próprio; se não achar pelo PID,
            # cai para "qualquer janela do AnyDesk que surgiu depois do clique".
            novas = ([w for w in livres if self.x.pid(w) == proc.pid]
                     or [w for w in livres if w not in antes])
            if novas:
                self.encaixar(aba, novas[0])
                return False
            if (GLib.get_monotonic_time() - inicio) / 1000 > DETECT_TIMEOUT_MS:
                self.fechar(aba)
                self.avisar(f"A janela de {formatar_id(cid)} não apareceu.")
                return False
            return True

        GLib.timeout_add(POLL_MS, procurar)

    def on_capturar(self):
        livres = self.janelas_livres()
        if not livres:
            self.avisar("Nenhuma janela do AnyDesk livre. Ela precisa ter sido aberta "
                        "com GDK_BACKEND=x11.")
            return
        dialogo = Gtk.Dialog(title="Capturar janela", transient_for=self, modal=True)
        dialogo.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Capturar", Gtk.ResponseType.OK)
        lista = Gtk.ListBox()
        for w in livres:
            linha = Gtk.ListBoxRow()
            linha.xid = w
            linha.add(Gtk.Label(label=self.x.title(w) or hex(w), xalign=0, margin=8))
            lista.add(linha)
        lista.select_row(lista.get_row_at_index(0))
        dialogo.get_content_area().add(lista)
        dialogo.show_all()
        if dialogo.run() == Gtk.ResponseType.OK and lista.get_selected_row():
            w = lista.get_selected_row().xid
            aba = self.nova_aba(id_no_titulo(self.x.title(w)))
            aba.pid = self.x.pid(w)
            self.encaixar(aba, w)
        dialogo.destroy()

    # ---- abas ------------------------------------------------------------------

    def nova_aba(self, cid):
        self.fechar_jogo()  # conectou em alguém: mostra a conexão
        aba = Aba(cid)
        self.abas.append(aba)

        rotulo = Gtk.Box(spacing=7)
        rotulo.pack_start(aba.spinner, False, False, 0)
        rotulo.pack_start(aba.ponto, False, False, 0)
        rotulo.pack_start(aba.rotulo, False, False, 0)
        fechar = Gtk.Button(image=icone("ph-x-symbolic", Gtk.IconSize.MENU),
                            tooltip_text="Encerrar esta conexão", relief=Gtk.ReliefStyle.NONE)
        fechar.connect("clicked", lambda _b: self.fechar(aba))
        rotulo.pack_start(fechar, False, False, 0)
        aba.cabeca.add(rotulo)
        # Botão do meio do mouse na aba fecha a conexão, como no navegador.
        aba.cabeca.connect("button-press-event",
                           lambda _w, e: e.button == 2 and (self.fechar(aba) or True))
        aba.cabeca.show_all()

        aba.rotulo.set_text(f"Conectando {self.nome_aba(aba)}…")
        indice = self.notebook.append_page(aba.socket, aba.cabeca)
        self.notebook.set_tab_reorderable(aba.socket, True)
        aba.socket.show()
        self.atualizar_tela()
        self.notebook.set_current_page(indice)
        self.marcar_conectados()
        return aba

    def encaixar(self, aba, xid):
        aba.xid = xid
        aba.spinner.stop()
        aba.spinner.hide()
        aba.ponto.show()
        # O socket precisa estar realizado (ter janela X11 própria) antes de receber a janela.
        aba.socket.add_id(xid)
        # Disparado quando a janela do AnyDesk some (conexão encerrada do outro lado, etc.).
        aba.socket.connect("plug-removed", lambda _s: self.remover_aba(aba) or True)
        aba.inicio = time.monotonic()
        self.sons.tocar(self.progresso.equipados().get("som"))
        self.atualizar_titulos()
        self.atualizar_pet_mini()  # com sessão aberta o pet do rodapé para de animar
        self.set_focus(None)  # sessão nova: teclado vai para ela, não para a busca

    def nome_aba(self, aba):
        """Apelido do contato > nome do computador no título da janela > ID formatado."""
        if aba.cid and self.contatos.nome(aba.cid):
            return self.contatos.nome(aba.cid)
        if aba.xid:
            titulo = self.x.title(aba.xid)
            if not aba.cid:
                aba.cid = id_no_titulo(titulo)
            limpo = limpar_titulo(titulo)
            if limpo and limpo.replace(" ", "") != (aba.cid or ""):
                return limpo
        return formatar_id(aba.cid) if aba.cid else "AnyDesk"

    def atualizar_titulos(self):
        for aba in self.abas:
            if aba.xid:
                aba.rotulo.set_text(self.nome_aba(aba))
                dica = self.x.title(aba.xid)
                if aba.cid:
                    dica = f"{dica}\nID: {formatar_id(aba.cid)}"
                aba.cabeca.set_tooltip_text(dica)
        return True  # continua rodando periodicamente

    def atualizar_tela(self):
        destino = "abas" if self.abas else "inicio"
        if self.pilha.get_visible_child_name() == "jogo":
            self._antes_do_jogo = destino  # não tira a pessoa do jogo
        else:
            self.pilha.set_visible_child_name(destino)
        n = len(self.abas)
        self.cabecalho.set_subtitle(f"{n} conexão aberta" if n == 1 else
                                    f"{n} conexões abertas" if n else None)

    def remover_aba(self, aba):
        if aba not in self.abas:
            return
        self.registrar_atendimento(aba)
        self.abas.remove(aba)
        indice = self.notebook.page_num(aba.socket)
        if indice >= 0:
            self.notebook.remove_page(indice)
        self.atualizar_tela()
        self.marcar_conectados()
        self.atualizar_pet_mini()

    def fechar(self, aba):
        # Não dá para devolver a janela à área de trabalho: o AnyDesk fecha sozinho quando
        # ela sai do socket. Então fechar a aba = encerrar o processo daquela conexão.
        if aba.pid:
            try:
                os.kill(aba.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.remover_aba(aba)

    def on_sair(self, *_args):
        if self.abas:
            dialogo = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Fechar o app encerra {len(self.abas)} conexão(ões). Continuar?")
            resposta = dialogo.run()
            dialogo.destroy()
            if resposta != Gtk.ResponseType.YES:
                return True  # cancela o fechamento da janela
        for aba in list(self.abas):
            self.fechar(aba)
        Gtk.main_quit()
        return False


def main():
    app = App()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
