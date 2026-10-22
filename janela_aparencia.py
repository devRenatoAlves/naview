"""Janela "Opções de aparência": intensidade do vidro, desenhos e animações do tema.

O tema em si é escolhido no jogo (presente na barra de título > Coleção). Tudo é aplicado e salvo
na hora.
"""
from gi.repository import Gdk, GLib, Gtk

import temas

ESPERA_MS = 150  # o controle deslizante só aplica depois de parar de mexer (aplicar refaz o CSS todo)


class JanelaAparencia(Gtk.Window):
    def __init__(self, pai, cfg, ao_mudar):
        super().__init__(title="Opções de aparência", transient_for=pai, modal=True,
                         type_hint=Gdk.WindowTypeHint.DIALOG, destroy_with_parent=True)
        self.cfg = cfg
        self.ao_mudar = ao_mudar
        self.set_default_size(460, 280)
        self._espera = None

        self.set_titlebar(Gtk.HeaderBar(show_close_button=True, title="Opções de aparência"))
        corpo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=20)
        self.add(corpo)
        nome = temas.TEMAS[cfg["tema"]]["nome"]
        dica = Gtk.Label(label=f"Tema atual: {nome}. Para trocar de tema, abra o jogo (presente) "
                               "e escolha na Coleção.", xalign=0, wrap=True)
        dica.set_opacity(0.65)
        corpo.pack_start(dica, False, False, 0)

        grade = Gtk.Grid(row_spacing=10, column_spacing=12, margin_top=6)
        corpo.pack_start(grade, False, False, 0)
        linha = 0

        self.intensidade = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.05)
        self.intensidade.set_draw_value(False)
        self.intensidade.set_hexpand(True)
        self.intensidade.connect("value-changed", self.on_intensidade)
        self.rotulo_intensidade = Gtk.Label(label="Intensidade do vidro", xalign=0)
        if not temas.TEM_DESFOQUE:
            self.rotulo_intensidade.set_tooltip_text(
                "Este sistema não desfoca o que fica atrás da janela. Por isso o vidro fica mais "
                "escuro, para o texto continuar legível.")
        grade.attach(self.rotulo_intensidade, 0, linha, 1, 1)
        grade.attach(self.intensidade, 1, linha, 1, 1)
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

        restaurar = Gtk.Button(label="Restaurar opções", halign=Gtk.Align.START, margin_top=6)
        restaurar.connect("clicked", self.restaurar)
        corpo.pack_start(restaurar, False, False, 0)

        self._carregando = False
        self.sincronizar()
        self.show_all()

    def sincronizar(self):
        """Mostra nos controles os valores atuais (sem disparar mudanças)."""
        self._carregando = True
        vidro = bool(temas.TEMAS[self.cfg["tema"]].get("vidro"))
        self.intensidade.set_value(self.cfg.get("intensidade_vidro", 0.5))
        self.intensidade.set_sensitive(vidro)
        self.rotulo_intensidade.set_sensitive(vidro)
        self.decoracoes.set_active(self.cfg.get("decoracoes", True))
        self.animacoes.set_active(self.cfg.get("animacoes", True))
        self._carregando = False

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

    def restaurar(self, _botao):
        self.cfg["intensidade_vidro"] = 0.5
        self.cfg["decoracoes"] = True
        self.cfg["animacoes"] = True
        self.ao_mudar()
        self.sincronizar()
