"""Janela "Aparência": galeria de temas e ajustes finos. Tudo é aplicado e salvo na hora."""
from gi.repository import Gdk, GLib, Gtk

import fontes
import temas

fontes.registrar_icones()  # cadeado dos temas bloqueados (ph-lock-simple-symbolic)

CSS = b"""
.janela-aparencia .secao { font-weight: bold; font-size: 1.1em; margin-top: 6px; }
.janela-aparencia .dica { opacity: 0.6; font-size: 0.9em; }
.janela-aparencia flowboxchild { padding: 6px; border-radius: 14px; transition: background-color 150ms ease; }
.janela-aparencia flowboxchild:hover { background-color: alpha(@theme_fg_color, 0.06); }
.janela-aparencia flowbox flowboxchild:selected { background-color: alpha(@theme_selected_bg_color, 0.30);
  color: @theme_fg_color; box-shadow: inset 0 0 0 2px @theme_selected_bg_color; }
.janela-aparencia .previa-desc { opacity: 0.65; font-size: 0.85em; }
.janela-aparencia .bloqueado { opacity: 0.4; }
.janela-aparencia .mensagem { color: @warning_color; }
"""
ESPERA_MS = 150  # o controle deslizante só aplica depois de parar de mexer (aplicar refaz o CSS todo)
_estilo = None  # registrado uma vez só: cada provedor a mais deixa todo o GTK mais lento


def _registrar_estilo():
    global _estilo
    if _estilo is None:
        _estilo = Gtk.CssProvider()
        _estilo.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), _estilo, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class JanelaAparencia(Gtk.Window):
    def __init__(self, pai, cfg, ao_mudar, possui=lambda _chave: True):
        super().__init__(title="Aparência", transient_for=pai, modal=True,
                         type_hint=Gdk.WindowTypeHint.DIALOG, destroy_with_parent=True)
        self.cfg = cfg
        self.ao_mudar = ao_mudar
        self.possui = possui  # temas são cartas do jogo: só dá para usar os que você tem
        self.set_default_size(700, 680)
        self.get_style_context().add_class("janela-aparencia")
        _registrar_estilo()
        self._espera = None

        cabecalho = Gtk.HeaderBar(show_close_button=True, title="Aparência")
        self.set_titlebar(cabecalho)

        corpo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=20)
        rolagem = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        rolagem.add(corpo)
        self.add(rolagem)

        # ---- galeria de temas ----
        corpo.pack_start(self._secao("Tema"), False, False, 0)
        self.galeria = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.SINGLE, homogeneous=True,
                                   min_children_per_line=2, max_children_per_line=3,
                                   row_spacing=4, column_spacing=4)
        self.cartoes = {}
        for chave in temas.ORDEM:
            filho = Gtk.FlowBoxChild()
            filho.add(self._cartao(chave, possui(chave)))
            filho.chave = chave
            self.galeria.add(filho)
            self.cartoes[chave] = filho
        self.galeria.select_child(self.cartoes[cfg["tema"]])
        self.galeria.connect("child-activated", self.on_tema)
        corpo.pack_start(self.galeria, False, False, 0)
        self.mensagem = Gtk.Label(xalign=0, wrap=True)
        self.mensagem.get_style_context().add_class("mensagem")
        corpo.pack_start(self.mensagem, False, False, 0)

        # ---- ajustes ----
        corpo.pack_start(self._secao("Ajustes do tema"), False, False, 0)
        grade = Gtk.Grid(row_spacing=10, column_spacing=12)
        corpo.pack_start(grade, False, False, 0)
        linha = 0
        self.botoes_cor = {}
        for chave, rotulo in (("destaque", "Cor de destaque"), ("fundo", "Cor de fundo"),
                              ("lateral", "Barra de contatos"), ("barra", "Barra de título e abas")):
            botao = Gtk.ColorButton(use_alpha=False)
            botao.connect("color-set", lambda b, k=chave: self.ajustar(k, b.get_rgba().to_string()))
            voltar = self._botao_voltar(lambda _b, k=chave: self.ajustar(k, None))
            grade.attach(Gtk.Label(label=rotulo, xalign=0, hexpand=True), 0, linha, 1, 1)
            grade.attach(botao, 1, linha, 1, 1)
            grade.attach(voltar, 2, linha, 1, 1)
            self.botoes_cor[chave] = botao
            linha += 1

        self.arquivo = Gtk.FileChooserButton(title="Escolher imagem de fundo",
                                             action=Gtk.FileChooserAction.OPEN)
        filtro = Gtk.FileFilter()
        filtro.set_name("Imagens")
        filtro.add_mime_type("image/*")
        self.arquivo.add_filter(filtro)
        self.arquivo.connect("file-set", lambda f: self.mudar("imagem", f.get_filename()))
        grade.attach(Gtk.Label(label="Imagem de fundo da tela inicial", xalign=0), 0, linha, 1, 1)
        grade.attach(self.arquivo, 1, linha, 1, 1)
        grade.attach(self._botao_voltar(self.remover_imagem, "Remover imagem"), 2, linha, 1, 1)
        linha += 1

        self.intensidade = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.05)
        self.intensidade.set_draw_value(False)
        self.intensidade.connect("value-changed", self.on_intensidade)
        self.rotulo_intensidade = Gtk.Label(label="Intensidade do vidro", xalign=0)
        if not temas.TEM_DESFOQUE:
            self.rotulo_intensidade.set_tooltip_text(
                "Este sistema não desfoca o que fica atrás da janela. Por isso o vidro fica mais "
                "escuro, para o texto continuar legível.")
        grade.attach(self.rotulo_intensidade, 0, linha, 1, 1)
        grade.attach(self.intensidade, 1, linha, 2, 1)
        linha += 1

        self.decoracoes = Gtk.Switch(halign=Gtk.Align.START)
        self.decoracoes.connect("notify::active", lambda s, _p: self.mudar("decoracoes", s.get_active()))
        grade.attach(Gtk.Label(label="Desenhos do tema na tela inicial", xalign=0), 0, linha, 1, 1)
        grade.attach(self.decoracoes, 1, linha, 1, 1)
        linha += 1

        self.animacoes = Gtk.Switch(halign=Gtk.Align.START)
        self.animacoes.connect("notify::active", lambda s, _p: self.mudar("animacoes", s.get_active()))
        grade.attach(Gtk.Label(label="Animações", xalign=0), 0, linha, 1, 1)
        grade.attach(self.animacoes, 1, linha, 1, 1)
        linha += 1

        restaurar = Gtk.Button(label="Restaurar o tema ao original", halign=Gtk.Align.START,
                               margin_top=6)
        restaurar.connect("clicked", self.restaurar)
        corpo.pack_start(restaurar, False, False, 0)

        self._carregando = False
        self.sincronizar()
        self.show_all()

    # ---- montagem ----

    @staticmethod
    def _secao(texto):
        rotulo = Gtk.Label(label=texto, xalign=0)
        rotulo.get_style_context().add_class("secao")
        return rotulo

    @staticmethod
    def _botao_voltar(callback, dica="Voltar à cor do tema"):
        botao = Gtk.Button.new_from_icon_name("edit-undo-symbolic", Gtk.IconSize.BUTTON)
        botao.set_tooltip_text(dica)
        botao.set_relief(Gtk.ReliefStyle.NONE)
        botao.connect("clicked", callback)
        return botao

    @staticmethod
    def _cartao(chave, liberado=True):
        tema = temas.TEMAS[chave]
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if not liberado:
            caixa.get_style_context().add_class("bloqueado")
        previa = Gtk.Box(spacing=8)
        previa.get_style_context().add_class(f"previa-{chave}")
        nome = Gtk.Label(label=tema["nome"], xalign=0, hexpand=True, margin_start=12,
                         valign=Gtk.Align.END, margin_bottom=10)
        nome.get_style_context().add_class("previa-nome")
        ponto = Gtk.Box(valign=Gtk.Align.START, margin_top=10, margin_end=10)
        ponto.get_style_context().add_class("previa-ponto")
        previa.pack_start(nome, True, True, 0)
        previa.pack_start(ponto, False, False, 0)
        texto = tema["descricao"] if liberado else "Ganhe em baús ou na loja do jogo"
        desc = Gtk.Label(label=texto, xalign=0, wrap=True, max_width_chars=24)
        desc.get_style_context().add_class("previa-desc")
        caixa.pack_start(previa, False, False, 0)
        if liberado:
            caixa.pack_start(desc, False, False, 0)
        else:
            linha = Gtk.Box(spacing=4)
            linha.pack_start(Gtk.Image.new_from_icon_name("ph-lock-simple-symbolic", Gtk.IconSize.MENU),
                             False, False, 0)
            linha.pack_start(desc, False, False, 0)
            caixa.pack_start(linha, False, False, 0)
        return caixa

    def sincronizar(self):
        """Mostra nos controles os valores atuais (sem disparar mudanças)."""
        self._carregando = True
        cores = temas.cores_do_tema(self.cfg)
        for chave, botao in self.botoes_cor.items():
            rgba = Gdk.RGBA()
            if rgba.parse(cores[chave]):
                botao.set_rgba(rgba)
        if self.cfg.get("imagem"):
            self.arquivo.set_filename(self.cfg["imagem"])
        else:
            self.arquivo.unselect_all()
        vidro = bool(temas.TEMAS[self.cfg["tema"]].get("vidro"))
        self.intensidade.set_value(self.cfg.get("intensidade_vidro", 0.5))
        self.intensidade.set_sensitive(vidro)
        self.rotulo_intensidade.set_sensitive(vidro)
        self.decoracoes.set_active(self.cfg.get("decoracoes", True))
        self.animacoes.set_active(self.cfg.get("animacoes", True))
        self._carregando = False

    # ---- ações ----

    def mudar(self, chave, valor):
        if self._carregando:
            return
        self.cfg[chave] = valor
        self.ao_mudar()

    def on_intensidade(self, escala):
        if self._carregando:
            return
        if self._espera:
            GLib.source_remove(self._espera)

        def aplicar():
            self._espera = None
            self.mudar("intensidade_vidro", round(escala.get_value(), 2))
            return False

        self._espera = GLib.timeout_add(ESPERA_MS, aplicar)

    def ajustar(self, chave, valor):
        if self._carregando:
            return
        self.cfg["ajustes"][chave] = valor
        self.ao_mudar()
        if valor is None:
            self.sincronizar()

    def on_tema(self, _galeria, filho):
        if self.cfg["tema"] == filho.chave:
            return
        if not self.possui(filho.chave):
            nome = temas.TEMAS[filho.chave]["nome"]
            self.mensagem.set_text(f"Você ainda não tem o tema {nome}. Abra baús ou procure na loja "
                                   "(botão do jogo na barra de título).")
            self.galeria.select_child(self.cartoes[self.cfg["tema"]])
            return
        # Tema novo = cores do tema: descarta os ajustes de cor do anterior. A imagem de fundo é
        # escolha da pessoa e fica (antes sumia sem aviso).
        self.mensagem.set_text("Sua imagem de fundo continua por cima do tema. Use o botão ao lado dela "
                               "para ver o fundo do tema." if self.cfg.get("imagem") else "")
        self.cfg["tema"] = filho.chave
        self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
        self.ao_mudar()
        self.sincronizar()

    def remover_imagem(self, _botao):
        self.mudar("imagem", None)
        self.sincronizar()

    def restaurar(self, _botao):
        self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
        self.cfg["imagem"] = None
        self.cfg["intensidade_vidro"] = 0.5
        self.cfg["decoracoes"] = True
        self.cfg["animacoes"] = True
        self.ao_mudar()
        self.sincronizar()
