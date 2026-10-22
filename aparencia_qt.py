"""Janela "Opções de aparência" (versão Qt): intensidade do vidro, desenhos e animações do tema.

O tema em si é escolhido no jogo (presente na barra de título > Coleção). Tudo é aplicado e salvo
na hora.
"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QCheckBox, QDialog, QGridLayout, QLabel, QPushButton, QSlider, QVBoxLayout

import temas

ESPERA_MS = 150  # o controle deslizante só aplica depois de parar de mexer (aplicar refaz o estilo todo)


class JanelaAparencia(QDialog):
    def __init__(self, pai, cfg, ao_mudar):
        super().__init__(pai)
        self.setObjectName("aparencia")
        self.setWindowTitle("Opções de aparência")
        self.setModal(True)
        self.resize(480, 280)
        self.cfg = cfg
        self.ao_mudar = ao_mudar
        self._carregando = False
        self._espera = QTimer(self, singleShot=True, interval=ESPERA_MS, timeout=self._aplicar_intensidade)

        lista = QVBoxLayout(self)
        lista.setContentsMargins(20, 20, 20, 20)
        lista.setSpacing(10)
        nome = temas.TEMAS[cfg["tema"]]["nome"]
        dica = QLabel(f"Tema atual: {nome}. Para trocar de tema, abra o jogo (presente) e escolha na Coleção.",
                      wordWrap=True)
        lista.addWidget(dica)

        ajustes = QGridLayout()
        ajustes.setHorizontalSpacing(12)
        ajustes.setVerticalSpacing(10)
        ajustes.setColumnStretch(1, 1)
        self.rotulo_intensidade = QLabel("Intensidade do vidro")
        if not temas.TEM_DESFOQUE:
            self.rotulo_intensidade.setToolTip(
                "Este sistema não desfoca o que fica atrás da janela. Por isso o vidro fica mais "
                "escuro, para o texto continuar legível.")
        self.intensidade = QSlider(Qt.Horizontal, minimum=0, maximum=100, singleStep=5, pageStep=10)
        self.intensidade.valueChanged.connect(lambda _v: self._carregando or self._espera.start())
        ajustes.addWidget(self.rotulo_intensidade, 0, 0)
        ajustes.addWidget(self.intensidade, 0, 1)
        self.decoracoes = QCheckBox("Desenhos do tema na tela inicial")
        self.decoracoes.toggled.connect(lambda v: self.mudar("decoracoes", v))
        ajustes.addWidget(self.decoracoes, 1, 0, 1, 2)
        self.animacoes = QCheckBox("Animações")
        self.animacoes.toggled.connect(lambda v: self.mudar("animacoes", v))
        ajustes.addWidget(self.animacoes, 2, 0, 1, 2)
        lista.addLayout(ajustes)

        restaurar = QPushButton("Restaurar opções")
        restaurar.clicked.connect(self.restaurar)
        lista.addWidget(restaurar, 0, Qt.AlignLeft)
        lista.addStretch(1)
        self.sincronizar()

    def sincronizar(self):
        """Mostra nos controles os valores atuais (sem disparar mudanças)."""
        self._carregando = True
        vidro = bool(temas.TEMAS[self.cfg["tema"]].get("vidro"))
        self.intensidade.setValue(round(self.cfg.get("intensidade_vidro", 0.5) * 100))
        self.intensidade.setEnabled(vidro)
        self.rotulo_intensidade.setEnabled(vidro)
        self.decoracoes.setChecked(self.cfg.get("decoracoes", True))
        self.animacoes.setChecked(self.cfg.get("animacoes", True))
        self._carregando = False

    def mudar(self, chave, valor):
        if self._carregando:
            return
        self.cfg[chave] = valor
        self.ao_mudar()

    def _aplicar_intensidade(self):
        self.mudar("intensidade_vidro", round(self.intensidade.value() / 100, 2))

    def restaurar(self, *_a):
        self.cfg["intensidade_vidro"] = 0.5
        self.cfg["decoracoes"] = True
        self.cfg["animacoes"] = True
        self.ao_mudar()
        self.sincronizar()
