"""Janela "Aparência" (versão Qt): galeria de temas e ajustes finos. Tudo é aplicado e salvo na hora."""
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QDialog, QFileDialog, QFrame, QGraphicsOpacityEffect,
                               QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSlider,
                               QToolButton, QVBoxLayout, QWidget)

import temas
import temas_qt

ESPERA_MS = 150  # o controle deslizante só aplica depois de parar de mexer (aplicar refaz o estilo todo)

QSS = """
QDialog#aparencia QLabel#secao { font-weight: bold; font-size: 11pt; margin-top: 6px; }
QDialog#aparencia QLabel#dica, QDialog#aparencia QLabel#previaDesc { color: palette(placeholder-text); }
QDialog#aparencia QLabel#mensagem { color: #d97706; }
QFrame#cartaoTema { border-radius: 14px; padding: 4px; border: 2px solid transparent; }
QFrame#cartaoTema:hover { background-color: rgba(127, 127, 127, 26); }
QFrame#cartaoTema[escolhido="1"] { border: 2px solid palette(highlight); background-color: rgba(127, 127, 127, 36); }
QPushButton#amostra { min-width: 56px; min-height: 26px; border-radius: 6px; border: 1px solid rgba(0,0,0,60); }
"""


class CartaoTema(QFrame):
    clicado = Signal(str)

    def __init__(self, chave, liberado):
        super().__init__()
        self.chave = chave
        self.setObjectName("cartaoTema")
        self.setCursor(Qt.PointingHandCursor)
        tema = temas.TEMAS[chave]
        caixa = QVBoxLayout(self)
        caixa.setContentsMargins(6, 6, 6, 6)
        caixa.setSpacing(6)

        previa = QFrame()
        previa.setProperty("previa", chave)
        linha = QHBoxLayout(previa)
        linha.setContentsMargins(12, 10, 10, 10)
        nome = QLabel(tema["nome"], objectName="previaNome")
        nome.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        ponto = QLabel(objectName="previaPonto")
        linha.addWidget(nome, 1, Qt.AlignBottom)
        linha.addWidget(ponto, 0, Qt.AlignTop)
        caixa.addWidget(previa)

        texto = tema["descricao"] if liberado else "Ganhe em baús ou na loja do jogo"
        desc = QLabel(texto, objectName="previaDesc", wordWrap=True)
        if liberado:
            caixa.addWidget(desc)
        else:
            linha_desc = QHBoxLayout()
            cadeado = QLabel()
            cadeado.setPixmap(temas_qt.icone("lock-simple", self.palette().text().color(), 14).pixmap(14, 14))
            linha_desc.addWidget(cadeado, 0, Qt.AlignTop)
            linha_desc.addWidget(desc, 1)
            caixa.addLayout(linha_desc)
            efeito = QGraphicsOpacityEffect(self)
            efeito.setOpacity(0.45)
            self.setGraphicsEffect(efeito)

    def escolher(self, sim):
        self.setProperty("escolhido", "1" if sim else "0")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self.clicado.emit(self.chave)


class JanelaAparencia(QDialog):
    def __init__(self, pai, cfg, ao_mudar, possui=lambda _chave: True):
        super().__init__(pai)
        self.setObjectName("aparencia")
        self.setWindowTitle("Aparência")
        self.setModal(True)
        self.resize(720, 700)
        # Estilo próprio, independente do tema do app (a janela segue o tema do sistema).
        self.setStyleSheet(QSS + temas_qt.qss_previas())
        self.cfg = cfg
        self.ao_mudar = ao_mudar
        self.possui = possui  # temas são cartas do jogo: só dá para usar os que você tem
        self._carregando = False
        self._espera = QTimer(self, singleShot=True, interval=ESPERA_MS, timeout=self._aplicar_intensidade)

        rolagem = QScrollArea(widgetResizable=True, frameShape=QFrame.NoFrame)
        corpo = QWidget()
        rolagem.setWidget(corpo)
        externo = QVBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        externo.addWidget(rolagem)
        lista = QVBoxLayout(corpo)
        lista.setContentsMargins(20, 20, 20, 20)
        lista.setSpacing(10)

        # ---- galeria de temas ----
        lista.addWidget(self._secao("Tema"))
        grade = QGridLayout()
        grade.setSpacing(4)
        self.cartoes = {}
        for i, chave in enumerate(temas.ORDEM):
            cartao = CartaoTema(chave, possui(chave))
            cartao.clicado.connect(self.on_tema)
            grade.addWidget(cartao, i // 3, i % 3)
            self.cartoes[chave] = cartao
        lista.addLayout(grade)
        self.mensagem = QLabel(objectName="mensagem", wordWrap=True)
        lista.addWidget(self.mensagem)

        # ---- ajustes ----
        lista.addWidget(self._secao("Ajustes do tema"))
        ajustes = QGridLayout()
        ajustes.setHorizontalSpacing(12)
        ajustes.setVerticalSpacing(10)
        ajustes.setColumnStretch(0, 1)
        linha = 0
        self.amostras = {}
        for chave, rotulo in (("destaque", "Cor de destaque"), ("fundo", "Cor de fundo"),
                              ("lateral", "Barra de contatos"), ("barra", "Barra de título e abas")):
            amostra = QPushButton(objectName="amostra", cursor=Qt.PointingHandCursor)
            amostra.clicked.connect(lambda _c=False, k=chave: self.escolher_cor(k))
            ajustes.addWidget(QLabel(rotulo), linha, 0)
            ajustes.addWidget(amostra, linha, 1)
            ajustes.addWidget(self._botao_voltar(lambda _c=False, k=chave: self.ajustar(k, None)), linha, 2)
            self.amostras[chave] = amostra
            linha += 1

        self.arquivo = QPushButton("Escolher imagem…")
        self.arquivo.clicked.connect(self.escolher_imagem)
        ajustes.addWidget(QLabel("Imagem de fundo da tela inicial"), linha, 0)
        ajustes.addWidget(self.arquivo, linha, 1)
        ajustes.addWidget(self._botao_voltar(self.remover_imagem, "Remover imagem"), linha, 2)
        linha += 1

        self.rotulo_intensidade = QLabel("Intensidade do vidro")
        if not temas.TEM_DESFOQUE:
            self.rotulo_intensidade.setToolTip(
                "Este sistema não desfoca o que fica atrás da janela. Por isso o vidro fica mais "
                "escuro, para o texto continuar legível.")
        self.intensidade = QSlider(Qt.Horizontal, minimum=0, maximum=100, singleStep=5, pageStep=10)
        self.intensidade.valueChanged.connect(lambda _v: self._carregando or self._espera.start())
        ajustes.addWidget(self.rotulo_intensidade, linha, 0)
        ajustes.addWidget(self.intensidade, linha, 1, 1, 2)
        linha += 1

        self.decoracoes = QCheckBox("Desenhos do tema na tela inicial")
        self.decoracoes.toggled.connect(lambda v: self.mudar("decoracoes", v))
        ajustes.addWidget(self.decoracoes, linha, 0, 1, 3)
        linha += 1
        self.animacoes = QCheckBox("Animações")
        self.animacoes.toggled.connect(lambda v: self.mudar("animacoes", v))
        ajustes.addWidget(self.animacoes, linha, 0, 1, 3)
        lista.addLayout(ajustes)

        restaurar = QPushButton("Restaurar o tema ao original")
        restaurar.clicked.connect(self.restaurar)
        lista.addWidget(restaurar, 0, Qt.AlignLeft)
        lista.addStretch(1)
        self.sincronizar()

    # ---- montagem ----

    @staticmethod
    def _secao(texto):
        return QLabel(texto, objectName="secao")

    def _botao_voltar(self, callback, dica="Voltar à cor do tema"):
        botao = QToolButton(toolTip=dica, autoRaise=True, text="↺")
        botao.clicked.connect(callback)
        return botao

    def sincronizar(self):
        """Mostra nos controles os valores atuais (sem disparar mudanças)."""
        self._carregando = True
        for chave, cartao in self.cartoes.items():
            cartao.escolher(chave == self.cfg["tema"])
        cores = temas.cores_do_tema(self.cfg)
        for chave, amostra in self.amostras.items():
            c = temas_qt.cor(cores[chave])
            amostra.setStyleSheet(f"background-color: {c.name()};")
            amostra.setProperty("cor", c.name())
        imagem = self.cfg.get("imagem")
        self.arquivo.setText(Path(imagem).name if imagem else "Escolher imagem…")
        vidro = bool(temas.TEMAS[self.cfg["tema"]].get("vidro"))
        self.intensidade.setValue(round(self.cfg.get("intensidade_vidro", 0.5) * 100))
        self.intensidade.setEnabled(vidro)
        self.rotulo_intensidade.setEnabled(vidro)
        self.decoracoes.setChecked(self.cfg.get("decoracoes", True))
        self.animacoes.setChecked(self.cfg.get("animacoes", True))
        self._carregando = False

    # ---- ações ----

    def mudar(self, chave, valor):
        if self._carregando:
            return
        self.cfg[chave] = valor
        self.ao_mudar()

    def _aplicar_intensidade(self):
        self.mudar("intensidade_vidro", round(self.intensidade.value() / 100, 2))

    def escolher_cor(self, chave):
        atual = QColor(self.amostras[chave].property("cor") or "#808080")
        escolhida = QColorDialog.getColor(atual, self, "Escolher cor")
        if escolhida.isValid():
            self.ajustar(chave, f"rgb({escolhida.red()},{escolhida.green()},{escolhida.blue()})")

    def ajustar(self, chave, valor):
        self.cfg["ajustes"][chave] = valor
        self.ao_mudar()
        self.sincronizar()

    def escolher_imagem(self):
        caminho, _filtro = QFileDialog.getOpenFileName(self, "Escolher imagem de fundo", str(Path.home()),
                                                       "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg)")
        if caminho:
            self.mudar("imagem", caminho)
            self.sincronizar()

    def on_tema(self, chave):
        if self.cfg["tema"] == chave:
            return
        if not self.possui(chave):
            nome = temas.TEMAS[chave]["nome"]
            self.mensagem.setText(f"Você ainda não tem o tema {nome}. Abra baús ou procure na loja "
                                  "(botão do jogo na barra de título).")
            return
        # Tema novo = cores do tema: descarta os ajustes de cor do anterior. A imagem de fundo é
        # escolha da pessoa e fica.
        self.mensagem.setText("Sua imagem de fundo continua por cima do tema. Use o botão ao lado dela "
                              "para ver o fundo do tema." if self.cfg.get("imagem") else "")
        self.cfg["tema"] = chave
        self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
        self.ao_mudar()
        self.sincronizar()

    def remover_imagem(self, *_a):
        self.mudar("imagem", None)
        self.sincronizar()

    def restaurar(self, *_a):
        self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
        self.cfg["imagem"] = None
        self.cfg["intensidade_vidro"] = 0.5
        self.cfg["decoracoes"] = True
        self.cfg["animacoes"] = True
        self.ao_mudar()
        self.sincronizar()
