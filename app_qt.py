#!/usr/bin/env python3
"""NaView (versão Qt): várias conexões do AnyDesk em abas numa única janela, no Linux e no Windows.

No Linux, o app e o AnyDesk rodam pelo X11/XWayland, o que permite encaixar a janela do AnyDesk
dentro de uma aba. No Windows, o encaixe usa a própria API do Windows (ver janelas/).
"""
import math
import os
import re
import sys
import time
from pathlib import Path

import plataforma

if plataforma.LINUX:
    # O encaixe precisa do X11: no Wayland um programa não consegue prender a janela de outro.
    os.environ["QT_QPA_PLATFORM"] = "xcb"


def migrar_pastas_antigas():
    """Renomeia as pastas de dados do nome antigo (anydesk-tabs) para naview, uma vez só."""
    if not plataforma.LINUX:
        return
    for base in (".config", ".cache", ".local/share"):
        antiga, nova = Path.home() / base / "anydesk-tabs", Path.home() / base / "naview"
        if antiga.is_dir() and not nova.exists():
            antiga.rename(nova)


migrar_pastas_antigas()  # antes de temas, contatos e progresso lerem os arquivos

from PySide6.QtCore import (QEasingCurve, QEvent, QPoint, QPointF, QRect, QSize, Qt,  # noqa: E402
                            QTimer, QVariantAnimation)
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QGuiApplication, QIcon, QKeySequence,  # noqa: E402
                           QPainter, QPen, QShortcut, QWindow)
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QFrame,  # noqa: E402
                               QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QLayout,
                               QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton,
                               QSizePolicy, QStackedWidget, QTabBar, QTabWidget, QToolButton, QVBoxLayout,
                               QWidget)

import temas  # noqa: E402
import temas_qt  # noqa: E402
from contatos import Contatos, formatar_id  # noqa: E402
from janelas import Janelas  # noqa: E402
from jogo import catalogo as cat_jogo  # noqa: E402
from jogo.progresso import Progresso  # noqa: E402
from jogo.qt import Notificacoes, Sons, pet_rodape  # noqa: E402

PASTA = Path(__file__).resolve().parent
DETECT_TIMEOUT_MS = 60_000
POLL_RAPIDO_MS = 250  # procura a janela nova da conexão rápido no começo...
POLL_LENTO_MS = 1_000  # ...e devagar depois (cada procura varre as janelas do sistema)
POLL_RAPIDO_ATE_MS = 3_000
TITULO_MS = 2_000
EXISTE_MS = 1_000  # confere se a janela da sessão ainda existe (sessão encerrada do outro lado)
FOCO_MS = 120
AVISO_MS = 4_000
CONFIRMAR_FECHAR_S = 300  # sessão aberta há mais tempo que isso pede confirmação para fechar
JOGO_LIBERAR_S = 600  # jogo fechado há 10 min: libera a memória do navegador embutido
QUADRO_MS = 40  # animações da tela inicial: 25 quadros por segundo
BORDA_REDIMENSIONAR = 6  # px na beirada da janela (sem moldura) que servem para redimensionar
N_CORES_AVATAR = 6


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


def repolir(widget):
    """Reaplica o estilo depois de mudar uma propriedade usada na folha de estilo."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# ---- peças pequenas ------------------------------------------------------------------

class FluxoLayout(QLayout):
    """Itens lado a lado, quebrando linha quando não cabem (os botões "Recentes")."""

    def __init__(self, espaco=6):
        super().__init__()
        self._itens = []
        self._espaco = espaco
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._itens.append(item)

    def count(self):
        return len(self._itens)

    def itemAt(self, i):
        return self._itens[i] if 0 <= i < len(self._itens) else None

    def takeAt(self, i):
        return self._itens.pop(i) if 0 <= i < len(self._itens) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, largura):
        return self._arrumar(QRect(0, 0, largura, 0), testar=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrumar(rect, testar=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        tamanho = QSize()
        for item in self._itens:
            tamanho = tamanho.expandedTo(item.minimumSize())
        return tamanho

    def _arrumar(self, rect, testar):
        x, y, altura_linha = rect.x(), rect.y(), 0
        for item in self._itens:
            dica = item.sizeHint()
            if x + dica.width() > rect.right() + 1 and altura_linha:
                x, y = rect.x(), y + altura_linha + self._espaco
                altura_linha = 0
            if not testar:
                item.setGeometry(QRect(QPoint(x, y), dica))
            x += dica.width() + self._espaco
            altura_linha = max(altura_linha, dica.height())
        return y + altura_linha - rect.y()


class Girando(QWidget):
    """Indicador de "conectando" (um arco girando). Só anima enquanto está visível."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(16, 16)
        self._angulo = 0
        self.cor = QColor("#888888")
        self._relogio = QTimer(self, interval=60, timeout=self._girar)

    def showEvent(self, evento):
        self._relogio.start()
        super().showEvent(evento)

    def hideEvent(self, evento):
        self._relogio.stop()
        super().hideEvent(evento)

    def _girar(self):
        self._angulo = (self._angulo + 30) % 360
        self.update()

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)
        caneta = QPen(self.cor, 2)
        caneta.setCapStyle(Qt.RoundCap)
        pintor.setPen(caneta)
        pintor.drawArc(QRect(2, 2, 12, 12), -self._angulo * 16, 270 * 16)


class PetImagem(QWidget):
    """Desenho do pet no rodapé, que flutua devagar quando ele está feliz e não há sessão aberta."""

    def __init__(self):
        super().__init__()
        self._pixmap = None
        self._dy = 0.0
        self.setFixedSize(pet_rodape_tamanho())
        self._anim = QVariantAnimation(self, startValue=0.0, endValue=0.0, duration=8000, loopCount=-1)
        self._anim.setKeyValueAt(0.5, -10.0)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.valueChanged.connect(self._mover)

    def definir(self, pixmap, flutuar):
        self._pixmap = pixmap
        if flutuar and self._anim.state() != QVariantAnimation.Running:
            self._anim.start()
        elif not flutuar:
            self._anim.stop()
            self._dy = 0.0
        self.update()

    def _mover(self, valor):
        self._dy = valor
        self.update()

    def paintEvent(self, _evento):
        if self._pixmap:
            QPainter(self).drawPixmap(QPointF(0, self._dy), self._pixmap)


def pet_rodape_tamanho():
    from jogo.qt import RODAPE_FOLGA, RODAPE_H, RODAPE_W
    return QSize(RODAPE_W, RODAPE_H + RODAPE_FOLGA)


class Clicavel(QWidget):
    """Área que reage a clique (o rodapé do pet)."""

    def __init__(self, ao_clicar):
        super().__init__()
        self.ao_clicar = ao_clicar
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self.ao_clicar()


# ---- tela inicial ----------------------------------------------------------------------

def _vai_e_volta(t, duracao):
    """0 -> 1 -> 0 ao longo de 2 x duração (como "animation-direction: alternate" do CSS)."""
    fase = (t / duracao) % 2
    return fase if fase < 1 else 2 - fase


def _suave(x):
    return (1 - math.cos(math.pi * x)) / 2


def _degraus(x, n=2):
    return math.floor(x * n) / n


# nome: (duração em s, curva, deslocamento y, rotação de/até, escala até, opacidade até)
ANIMACOES = {
    "flutuar": (2.2, _suave, -10, None, None, None),
    "flutuar-lento": (4.0, _suave, -10, None, None, None),
    "balancar": (1.8, _suave, 0, (-12, 12), None, None),
    "pular": (0.5, _degraus, -8, None, None, None),
    "pular-lento": (0.8, _degraus, -8, None, None, None),
    "pulsar": (0.9, _suave, 0, None, 1.08, None),
    "pulsar-lento": (2.5, _suave, 0, None, 1.08, None),
    "navegar": (3.0, _suave, -5, (-3, 3), None, None),
    "piscar": (1.4, _suave, 0, None, None, 0.2),
    "piscar-lento": (2.6, _suave, 0, None, None, 0.2),
}


class TelaInicio(QWidget):
    """Fundo do tema, desenhos (animados) e o cartão "Conectar" no meio.

    Fundo e desenhos são pintados aqui mesmo, num paintEvent só: mais leve que um widget por desenho.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("inicio")
        self._fundo = None  # fundo pintado uma vez por tamanho/tema (as camadas paradas)
        self._relogio = QTimer(self, interval=QUADRO_MS, timeout=self.update)
        self._t0 = time.monotonic()
        self.decor = []

    def tema_mudou(self):
        self._fundo = None
        cfg = self.app.cfg
        tema = temas.TEMAS[cfg["tema"]]
        self.decor = tema.get("decor", []) if cfg.get("decoracoes", True) else []
        self.ex = temas_qt.extra(cfg["tema"])
        self.cor_texto = temas_qt.cor(f"alpha({temas.cores_do_tema(cfg)['texto']}, 0.6)")
        self.atualizar_relogio()
        self.update()

    def atualizar_relogio(self):
        animado = (self.app.cfg.get("animacoes", True) and self.isVisible()
                   and any(d.get("anim") for d in self.decor) and not self.app.isMinimized())
        if animado and not self._relogio.isActive():
            self._relogio.start()
        elif not animado:
            self._relogio.stop()

    def showEvent(self, evento):
        self.atualizar_relogio()
        super().showEvent(evento)

    def hideEvent(self, evento):
        self._relogio.stop()
        super().hideEvent(evento)

    def resizeEvent(self, evento):
        self._fundo = None
        super().resizeEvent(evento)

    def paintEvent(self, _evento):
        pintor = QPainter(self)
        if self._fundo is None or self._fundo.size() != self.size() * self.devicePixelRatioF():
            from PySide6.QtGui import QPixmap
            self._fundo = QPixmap(self.size() * self.devicePixelRatioF())
            self._fundo.setDevicePixelRatio(self.devicePixelRatioF())
            self._fundo.fill(Qt.transparent)
            p = QPainter(self._fundo)
            temas_qt.pintar_fundo(p, self.rect(), self.app.cfg)
            p.end()
        pintor.drawPixmap(0, 0, self._fundo)
        pintor.setRenderHint(QPainter.SmoothPixmapTransform)
        pintor.setRenderHint(QPainter.Antialiasing)
        animar = self.app.cfg.get("animacoes", True)
        t = time.monotonic() - self._t0
        for d in self.decor:
            tipo = d.get("tipo", "imagem")
            if tipo == "faixa":
                self._faixa(pintor, d)
            elif tipo == "texto":
                self._texto_decor(pintor, d)
            else:
                self._imagem(pintor, d, t if animar else None)

    def _posicao(self, d, w, h):
        cima, direita, baixo, esquerda = d.get("margem", (0, 0, 0, 0))
        horizontal, vertical = d.get("halign", "start"), d.get("valign", "start")
        x = {"start": esquerda, "end": self.width() - direita - w,
             "center": (self.width() - w) / 2 + esquerda - direita}[horizontal]
        y = {"start": cima, "end": self.height() - baixo - h,
             "center": (self.height() - h) / 2 + cima - baixo}[vertical]
        return x, y

    def _faixa(self, pintor, d):
        w, h = d["tile"]
        altura = d["altura"]
        y = self.height() - d.get("margem_baixo", 0) - altura
        area = QRect(0, int(y), self.width(), altura)
        if d.get("fundo"):
            pintor.fillRect(area, temas_qt.cor(d["fundo"]))
        arte = temas_qt.arte_svg(d["arte"], w, h)
        # Centralizada e encostada embaixo, repetida na horizontal (como o CSS do GTK).
        x0 = (self.width() - w) / 2
        while x0 > 0:
            x0 -= w
        topo = area.bottom() + 1 - h
        x = x0
        while x < self.width():
            pintor.drawPixmap(int(x), int(topo), arte)
            x += w

    def _fonte_decor(self, escala=1.0):
        familia, tamanho = temas_qt.fonte_do_tema(self.app.cfg)
        fonte = QFont(familia) if familia else QFont(self.font())
        fonte.setPointSizeF(tamanho * escala)
        return fonte

    def _texto_decor(self, pintor, d, rect=None):
        if self.ex["texto_decor"]:
            escala, cor_texto, (sx, sy, cor_sombra) = self.ex["texto_decor"]
        else:
            escala, cor_texto, sx, sy, cor_sombra = 1.0, None, 0, 0, None
        fonte = self._fonte_decor(escala)
        pintor.setFont(fonte)
        if rect is None:
            metricas = QFontMetrics(fonte)
            w, h = metricas.horizontalAdvance(d["texto"]) + 4, metricas.height()
            x, y = self._posicao(d, w, h)
            rect = QRect(int(x), int(y), w, h)
        if cor_sombra:
            pintor.setPen(temas_qt.cor(cor_sombra))
            pintor.drawText(rect.translated(sx, sy), Qt.AlignCenter, d["texto"])
        pintor.setPen(temas_qt.cor(cor_texto) if cor_texto else self.cor_texto)
        pintor.drawText(rect, Qt.AlignCenter, d["texto"])

    def _imagem(self, pintor, d, t):
        w, h = d["w"], d["h"]
        arte = temas_qt.arte_svg(d["arte"], w, h)
        x, y = self._posicao(d, w, h)
        dy, angulo, escala, opacidade = 0.0, 0.0, 1.0, 1.0
        if t is not None and d.get("anim") in ANIMACOES:
            duracao, curva, desloc, rotacao, escala_max, opac_min = ANIMACOES[d["anim"]]
            p = curva(_vai_e_volta(t, duracao))
            dy = desloc * p
            if rotacao:
                angulo = rotacao[0] + (rotacao[1] - rotacao[0]) * p
            if escala_max:
                escala = 1 + (escala_max - 1) * p
            if opac_min is not None:
                opacidade = 1 - (1 - opac_min) * p
        pintor.save()
        pintor.setOpacity(opacidade)
        pintor.translate(x + w / 2, y + h / 2 + dy)
        pintor.rotate(angulo)
        pintor.scale(escala, escala)
        pintor.drawPixmap(QPointF(-w / 2, -h / 2), arte)
        if d.get("texto"):  # ex.: "POW!" por cima da explosão
            self._texto_decor(pintor, d, QRect(int(-w / 2), int(-h / 2), w, h))
        pintor.restore()


# ---- abas e contatos -----------------------------------------------------------------

class Aba:
    """Uma conexão: a janela do AnyDesk dentro de uma aba."""

    def __init__(self, cid):
        self.cid = cid  # ID ou apelido usado para conectar (None se capturada sem ID no título)
        self.janela = None  # identificador da janela do AnyDesk (X11 ou Windows)
        self.pid = None
        self.inicio = None  # quando a sessão foi encaixada (para contar o atendimento)
        self.pagina = QWidget()
        self.pagina.setStyleSheet("background: #000000;")
        QVBoxLayout(self.pagina).setContentsMargins(0, 0, 0, 0)
        self.caixa = None  # container do Qt com a janela do AnyDesk
        self.qjanela = None

        self.cabeca = QWidget()
        linha = QHBoxLayout(self.cabeca)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(7)
        self.girando = Girando()
        self.ponto = QLabel()
        self.ponto.setProperty("avatar", str(cor_avatar(cid)))
        self.ponto.setProperty("mini", "1")
        self.ponto.hide()
        self.rotulo = QLabel()
        self.rotulo.setMinimumWidth(110)
        self.rotulo.setMaximumWidth(200)
        self.fechar = QToolButton(toolTip="Encerrar esta conexão")
        linha.addWidget(self.girando)
        linha.addWidget(self.ponto)
        linha.addWidget(self.rotulo)
        linha.addWidget(self.fechar)

    def mostrar_nome(self, texto):
        metricas = QFontMetrics(self.rotulo.font())
        self.rotulo.setText(metricas.elidedText(texto, Qt.ElideRight, self.rotulo.maximumWidth()))


class LinhaContato(QWidget):
    def __init__(self, cid, nome, ao_renomear, ordem):
        super().__init__()
        self.cid = cid
        self.nome = nome
        self.ordem = ordem  # posição na lista do AnyDesk (desempate da ordenação)
        self.setToolTip("Clique duas vezes (ou Enter) para conectar")

        caixa = QHBoxLayout(self)
        caixa.setContentsMargins(8, 6, 8, 6)
        caixa.setSpacing(10)
        avatar = QLabel(iniciais(nome, cid), alignment=Qt.AlignCenter)
        avatar.setProperty("avatar", str(cor_avatar(cid)))
        caixa.addWidget(avatar)

        textos = QVBoxLayout()
        textos.setSpacing(1)
        principal = QLabel(nome or formatar_id(cid), objectName="contatoNome")
        principal.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        textos.addWidget(principal)
        if nome:
            textos.addWidget(QLabel(formatar_id(cid), objectName="contatoId"))
        caixa.addLayout(textos, 1)

        self.ponto = QLabel("●", objectName="pontoOnline", toolTip="Conectado")
        self.ponto.hide()
        caixa.addWidget(self.ponto)
        self.editar = QToolButton(toolTip="Renomear")
        self.editar.clicked.connect(lambda: ao_renomear(cid, self.editar))
        self.editar.setVisible(False)  # aparece ao passar o mouse
        caixa.addWidget(self.editar)

    def enterEvent(self, evento):
        self.editar.setVisible(True)
        super().enterEvent(evento)

    def leaveEvent(self, evento):
        self.editar.setVisible(False)
        super().leaveEvent(evento)

    def combina(self, busca):
        busca = busca.lower().replace(" ", "")
        return not busca or busca in (self.nome or "").lower().replace(" ", "") or busca in self.cid


class Aviso(QFrame):
    """Mensagem curta no rodapé da janela. É uma janela própria (sem moldura) para ficar por cima
    também da sessão do AnyDesk, que é uma janela nativa e cobriria um widget comum."""

    def __init__(self, pai):
        super().__init__(pai, Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setObjectName("aviso")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.janela = pai
        externo = QHBoxLayout(self)
        externo.setContentsMargins(0, 0, 0, 0)
        self.fundo = QFrame(objectName="aviso")
        externo.addWidget(self.fundo)
        linha = QHBoxLayout(self.fundo)
        linha.setContentsMargins(18, 10, 18, 10)
        linha.setSpacing(8)
        self.icone = QLabel()
        self.texto = QLabel(wordWrap=True)
        self.texto.setMaximumWidth(520)
        linha.addWidget(self.icone)
        linha.addWidget(self.texto)
        self._relogio = QTimer(self, singleShot=True, interval=AVISO_MS, timeout=self.hide)

    def mostrar(self, texto, icone, cor_icone):
        self.texto.setText(texto)
        self.icone.setVisible(bool(icone))
        if icone:
            self.icone.setPixmap(temas_qt.icone(icone, cor_icone, 22).pixmap(22, 22))
        self.adjustSize()
        janela = self.janela.geometry()
        self.move(janela.x() + (janela.width() - self.width()) // 2, janela.bottom() - self.height() - 20)
        if self.janela.isVisible() and not self.janela.isMinimized():
            self.show()
            self.raise_()
        self._relogio.start()


class BarraTitulo(QWidget):
    """Barra de título própria (a janela não tem moldura do sistema): arrasta, maximiza e fecha."""

    def __init__(self, janela):
        super().__init__()
        self.janela = janela
        self.setObjectName("barra")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedHeight(46)

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton and self.janela.windowHandle():
            self.janela.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self.janela.alternar_maximizar()


# ---- janela principal --------------------------------------------------------------------

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("janela")
        self.setWindowTitle("NaView")
        self.setWindowIcon(QIcon(str(PASTA / "icone.svg")))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        # Fundo transparente só no Linux: é o que permite o tema "Vidro líquido". No Windows, uma
        # janela transparente não mostra a sessão encaixada; lá o vidro fica sem desfoque.
        self.translucida = plataforma.LINUX
        if self.translucida:
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1280, 820)
        self.setMouseTracking(True)

        self.j = Janelas()
        self.contatos = Contatos()
        self.abas = []
        self._lista_atual = None
        self._regiao_vidro = ()  # () = ainda não enviada; None = desfoque desligado
        self.cfg = temas.carregar()
        self.progresso = Progresso(tema_atual=self.cfg["tema"], liberar_tudo=self.cfg["liberar_tudo"])
        self.sons = Sons()
        self.notificacoes = Notificacoes(icone_qt=self.windowIcon())
        self.tela_jogo = None  # criada só na primeira vez que o jogo abre (o navegador é pesado)
        self._antes_do_jogo = "inicio"
        self._baus_prontos = set()
        self._diario_avisado = None
        self._foco_ok = None  # (sessão, janela com foco) já conferido: evita subir a árvore do X11
        self._conectados = set()
        self._cor_icones = "#ffffff"
        self._liberar_jogo = QTimer(self, singleShot=True, interval=JOGO_LIBERAR_S * 1000,
                                    timeout=self.liberar_jogo)

        # Faixa de BORDA_REDIMENSIONAR px em volta da raiz: é por ela que a janela (sem moldura do
        # sistema) é redimensionada. No Linux ela é transparente.
        self.externo = externo = QVBoxLayout(self)
        externo.setContentsMargins(*[BORDA_REDIMENSIONAR] * 4)
        self.setProperty("translucida", "1" if self.translucida else "0")
        self.raiz = QWidget(objectName="raiz")
        self.raiz.setAttribute(Qt.WA_StyledBackground)
        externo.addWidget(self.raiz)
        coluna = QVBoxLayout(self.raiz)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(0)
        coluna.addWidget(self.montar_barra())

        corpo = QHBoxLayout()
        corpo.setContentsMargins(0, 0, 0, 0)
        corpo.setSpacing(0)
        self.lateral = self.montar_lateral()
        corpo.addWidget(self.lateral)
        self.pilha = QStackedWidget()
        self.inicio = self.montar_inicio()
        self.pilha.addWidget(self.inicio)
        self.abas_widget = self.montar_abas()
        self.pilha.addWidget(self.abas_widget)
        corpo.addWidget(self.pilha, 1)
        coluna.addLayout(corpo, 1)
        self.lateral.setVisible(self.cfg["lateral_visivel"])

        self.aviso = Aviso(self)
        # Clique num campo de texto ou na lista: o teclado volta da sessão para o app. Precisa ser no
        # clique: com o teclado na sessão o Qt acha que a janela está inativa e não avisa a troca de foco.
        for widget in (self.busca, self.entrada_rapida, self.lista.viewport()):
            widget.installEventFilter(self)
        QShortcut(QKeySequence("F9"), self, activated=lambda: self.bt_lateral.toggle())
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.ir_para_busca)
        QApplication.instance().focusChanged.connect(self.on_foco_widget)

        self.aplicar_tema()
        self.carregar_contatos()
        self.atualizar_recentes()
        self.atualizar_pet_mini()
        self.atualizar_selo()
        QTimer(self, interval=TITULO_MS, timeout=self.atualizar_titulos).start()
        QTimer(self, interval=EXISTE_MS, timeout=self.conferir_sessoes).start()
        if self.j.FORCAR_FOCO:
            QTimer(self, interval=FOCO_MS, timeout=self.manter_foco).start()
        QTimer(self, interval=60_000, timeout=self.batimento).start()
        if self.progresso.equipados().get("som"):
            QTimer.singleShot(3000, self.sons.preparar)

    # ---- montagem da interface -------------------------------------------------

    def montar_barra(self):
        self.barra = BarraTitulo(self)
        linha = QHBoxLayout(self.barra)
        linha.setContentsMargins(8, 0, 8, 0)
        linha.setSpacing(4)

        self.bt_lateral = QToolButton(checkable=True, checked=self.cfg["lateral_visivel"],
                                      toolTip="Mostrar/esconder contatos (F9)")
        self.bt_lateral.toggled.connect(self.on_alternar_lateral)
        linha.addWidget(self.bt_lateral)
        linha.addStretch(1)

        titulos = QVBoxLayout()
        titulos.setSpacing(0)
        self.titulo = QLabel("NaView", objectName="titulo", alignment=Qt.AlignCenter)
        self.subtitulo = QLabel(objectName="subtitulo", alignment=Qt.AlignCenter)
        self.subtitulo.hide()
        titulos.addStretch(1)
        titulos.addWidget(self.titulo)
        titulos.addWidget(self.subtitulo)
        titulos.addStretch(1)
        linha.addLayout(titulos)
        linha.addStretch(1)

        self.bt_jogo = QToolButton(checkable=True, toolTip="Baús, coleção e pet")
        self.bt_jogo.clicked.connect(self.on_alternar_jogo)
        self.selo_jogo = QLabel(self.bt_jogo, objectName="selo", alignment=Qt.AlignCenter)
        self.selo_jogo.hide()
        linha.addWidget(self.bt_jogo)

        self.bt_menu = QToolButton(toolTip="Mais opções", popupMode=QToolButton.InstantPopup)
        menu = QMenu(self.bt_menu)
        menu.addAction("Aparência e temas…", self.abrir_aparencia)
        menu.addAction("Capturar janela do AnyDesk…", self.on_capturar)
        self.bt_menu.setMenu(menu)
        linha.addWidget(self.bt_menu)

        linha.addSpacing(8)
        self.bt_minimizar = QToolButton(toolTip="Minimizar")
        self.bt_minimizar.clicked.connect(self.showMinimized)
        self.bt_maximizar = QToolButton(toolTip="Maximizar")
        self.bt_maximizar.clicked.connect(self.alternar_maximizar)
        self.bt_fechar_janela = QToolButton(objectName="fecharJanela", toolTip="Fechar")
        self.bt_fechar_janela.clicked.connect(self.close)
        for botao in (self.bt_minimizar, self.bt_maximizar, self.bt_fechar_janela):
            linha.addWidget(botao)
        # Título sempre no meio da janela, não no meio do espaço que sobra entre os botões.
        self.barra.installEventFilter(self)
        return self.barra

    def montar_lateral(self):
        lateral = QWidget(objectName="lateral")
        lateral.setAttribute(Qt.WA_StyledBackground)
        lateral.setFixedWidth(290)
        coluna = QVBoxLayout(lateral)
        coluna.setContentsMargins(0, 0, 0, 0)
        coluna.setSpacing(0)

        cabeca = QHBoxLayout()
        cabeca.setContentsMargins(16, 14, 16, 8)
        cabeca.addWidget(QLabel("Contatos", objectName="tituloLateral"), 1)
        self.contagem = QLabel(objectName="contagem")
        cabeca.addWidget(self.contagem)
        coluna.addLayout(cabeca)

        self.busca = QLineEdit(placeholderText="Buscar ou digitar um ID", clearButtonEnabled=True)
        self.busca.textChanged.connect(self.filtrar_contatos)
        self.busca.returnPressed.connect(self.on_busca_enter)
        linha_busca = QHBoxLayout()
        linha_busca.setContentsMargins(12, 0, 12, 8)
        linha_busca.addWidget(self.busca)
        coluna.addLayout(linha_busca)

        self.lista = QListWidget(objectName="contatos")
        self.lista.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista.itemActivated.connect(lambda item: self.abrir(self.lista.itemWidget(item).cid))
        coluna.addWidget(self.lista, 1)
        self.vazio = QLabel("Nenhum contato encontrado.\nAperte Enter para conectar no ID digitado.",
                            objectName="vazio", alignment=Qt.AlignCenter, wordWrap=True)
        self.vazio.hide()
        coluna.addWidget(self.vazio, 1)
        coluna.addWidget(self.montar_pet_mini())
        return lateral

    def montar_pet_mini(self):
        """Pet no rodapé da barra de contatos; clicar abre a aba do pet no jogo."""
        caixa = Clicavel(lambda: self.abrir_jogo("pet"))
        caixa.setObjectName("petRodape")
        caixa.setAttribute(Qt.WA_StyledBackground)
        caixa.setToolTip("Cuidar do pet")
        linha = QHBoxLayout(caixa)
        linha.setContentsMargins(14, 6, 14, 10)
        linha.setSpacing(10)
        self.pet_imagem = PetImagem()
        linha.addWidget(self.pet_imagem)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        linha_nome = QHBoxLayout()
        linha_nome.setSpacing(6)
        self.pet_nome = QLabel(objectName="petNome")
        self.pet_humor = QLabel()
        linha_nome.addWidget(self.pet_nome)
        linha_nome.addWidget(self.pet_humor)
        linha_nome.addStretch(1)
        self.pet_fala = QLabel(objectName="petFala")
        self.pet_fala.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        textos.addStretch(1)
        textos.addLayout(linha_nome)
        textos.addWidget(self.pet_fala)
        textos.addStretch(1)
        linha.addLayout(textos, 1)
        return caixa

    def montar_inicio(self):
        inicio = TelaInicio(self)
        grade = QGridLayout(inicio)
        self.cartao = QFrame(objectName="cartao")
        self.cartao.setMinimumWidth(440)
        coluna = QVBoxLayout(self.cartao)
        coluna.setContentsMargins(28, 26, 28, 26)
        coluna.setSpacing(6)

        linha_titulo = QHBoxLayout()
        linha_titulo.setSpacing(4)
        linha_titulo.addStretch(1)
        self.titulo_inicio = QLabel(objectName="tituloInicio", alignment=Qt.AlignCenter)
        self.cursor = QLabel("█", objectName="tituloInicio")
        self._piscar_cursor = QTimer(self, interval=600,
                                     timeout=lambda: self.cursor.setText(" " if self.cursor.text() == "█" else "█"))
        linha_titulo.addWidget(self.titulo_inicio)
        linha_titulo.addWidget(self.cursor)
        linha_titulo.addStretch(1)
        coluna.addLayout(linha_titulo)
        self.sub_inicio = QLabel(objectName="subInicio", alignment=Qt.AlignCenter, wordWrap=True)
        coluna.addWidget(self.sub_inicio)

        linha = QHBoxLayout()
        linha.setContentsMargins(0, 16, 0, 0)
        linha.setSpacing(8)
        self.entrada_rapida = QLineEdit(placeholderText="ID do AnyDesk")
        self.entrada_rapida.returnPressed.connect(self.on_conectar_rapido)
        botao = QPushButton("Conectar", objectName="conectar", cursor=Qt.PointingHandCursor)
        botao.clicked.connect(self.on_conectar_rapido)
        linha.addWidget(self.entrada_rapida, 1)
        linha.addWidget(botao)
        coluna.addLayout(linha)

        self.titulo_recentes = QLabel("Recentes", objectName="recentesTitulo")
        self.titulo_recentes.setContentsMargins(0, 12, 0, 0)
        coluna.addWidget(self.titulo_recentes)
        self.recentes = QWidget()
        self.recentes_layout = FluxoLayout()
        self.recentes.setLayout(self.recentes_layout)
        coluna.addWidget(self.recentes)
        grade.addWidget(self.cartao, 0, 0, Qt.AlignCenter)
        return inicio

    def montar_abas(self):
        self.notebook = QTabWidget(objectName="abas", documentMode=True, movable=True)
        self.notebook.tabBar().setExpanding(False)
        self.notebook.tabBar().setDrawBase(False)
        self.notebook.tabBar().installEventFilter(self)  # botão do meio do mouse fecha a aba
        # Trocou de aba: o teclado vai para a sessão dessa aba (ver manter_foco).
        self.notebook.currentChanged.connect(lambda _i: self.devolver_teclado_a_sessao())
        self.bt_mais = QToolButton(objectName="novaConexao", toolTip="Nova conexão (Ctrl+F)")
        self.bt_mais.setFixedSize(34, 34)
        self.bt_mais.clicked.connect(self.ir_para_busca)
        self.notebook.setCornerWidget(self.bt_mais, Qt.TopRightCorner)
        return self.notebook

    def atualizar_recentes(self):
        """Botões com as últimas conexões no cartão da tela inicial."""
        while self.recentes_layout.count():
            item = self.recentes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for cid in self.contatos.recentes:
            nome = self.contatos.nome(cid) or formatar_id(cid)
            botao = QPushButton(QFontMetrics(self.font()).elidedText(nome, Qt.ElideRight, 130),
                                toolTip=f"Conectar em {formatar_id(cid)}", cursor=Qt.PointingHandCursor)
            botao.setProperty("recente", "1")
            botao.clicked.connect(lambda _c=False, c=cid: self.abrir(c))
            self.recentes_layout.addWidget(botao)
        tem = bool(self.contatos.recentes)
        self.titulo_recentes.setVisible(tem)
        self.recentes.setVisible(tem)

    # ---- tema e aparência -------------------------------------------------------

    def aplicar_tema(self):
        cfg = self.cfg
        tema = temas.TEMAS[cfg["tema"]]
        # Tema no nível máximo da coleção ganha a versão dourada; a moldura vem do jogo.
        dourado = self.progresso.nivel_carta(f"tema-{cfg['tema']}") >= cat_jogo.NIVEL_MAX
        familia, tamanho = temas_qt.fonte_do_tema(cfg)
        fonte = QFont(familia) if familia else QFont(QApplication.font())
        fonte.setPointSizeF(tamanho)
        self.setFont(fonte)
        self.setStyleSheet(temas_qt.gerar_qss(cfg, dourado=dourado, moldura=self.progresso.equipados()["moldura"]))
        cores = temas.cores_do_tema(cfg)
        self._cor_icones = cores["texto"]
        self._cor_icones_barra = cores["texto_barra"]
        self._cor_icones_lateral = cores["texto_lateral"]
        self.atualizar_icones()

        titulo, sub = tema.get("frases", ("Nenhuma conexão aberta",
                                          "Digite um ID ou escolha um contato à esquerda"))
        self.titulo_inicio.setText(titulo)
        self.sub_inicio.setText(sub)
        self.cursor.setVisible(bool(tema.get("cursor")))
        if tema.get("cursor") and cfg.get("animacoes", True):
            self._piscar_cursor.start()
        else:
            self._piscar_cursor.stop()
            self.cursor.setText("█")
        ex = temas_qt.extra(cfg["tema"])
        self._sombra(self.titulo_inicio, ex["titulo_sombra"])
        self._sombra(self.cursor, ex["titulo_sombra"])
        self._sombra(self.cartao, ex["cartao_sombra"])
        self.inicio.tema_mudou()
        self.atualizar_pet_mini()
        self.agendar_vidro()

    @staticmethod
    def _sombra(widget, sombra):
        if not sombra:
            widget.setGraphicsEffect(None)
            return
        dx, dy, desfoque, cor = sombra
        efeito = QGraphicsDropShadowEffect(widget)
        efeito.setOffset(dx, dy)
        efeito.setBlurRadius(desfoque * 2)  # o desfoque do Qt é mais curto que o do CSS
        efeito.setColor(temas_qt.cor(cor))
        widget.setGraphicsEffect(efeito)

    def atualizar_icones(self):
        barra, lateral = self._cor_icones_barra, self._cor_icones_lateral
        self.bt_lateral.setIcon(temas_qt.icone("sidebar-simple", barra))
        self.bt_jogo.setIcon(temas_qt.icone("gift", barra))
        self.bt_menu.setIcon(temas_qt.icone("dots-three-vertical", barra))
        self.bt_minimizar.setIcon(temas_qt.icone("minus", barra, 14))
        self.bt_maximizar.setIcon(temas_qt.icone("copy-simple" if self.isMaximized() else "square", barra, 14))
        self.bt_fechar_janela.setIcon(temas_qt.icone("x", barra, 14))
        self.bt_mais.setIcon(temas_qt.icone("plus", barra))
        self.bt_menu.setStyleSheet("QToolButton::menu-indicator { image: none; }")
        for aba in self.abas:
            self.estilizar_cabeca(aba)
        for i in range(self.lista.count()):
            linha = self.lista.itemWidget(self.lista.item(i))
            linha.editar.setIcon(temas_qt.icone("pencil-simple", lateral, 14))

    def abrir_aparencia(self):
        from aparencia_qt import JanelaAparencia

        def ao_mudar():
            self.aplicar_tema()
            temas.salvar(self.cfg)

        JanelaAparencia(self, self.cfg, ao_mudar, possui=self.progresso.possui_tema).exec()

    def on_alternar_lateral(self, visivel):
        self.lateral.setVisible(visivel)
        self.cfg["lateral_visivel"] = visivel
        temas.salvar(self.cfg)

    def alternar_maximizar(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def changeEvent(self, evento):
        if evento.type() == QEvent.WindowStateChange:
            maximizada = "1" if self.isMaximized() else "0"
            for widget in (self.raiz, self.barra):
                widget.setProperty("maximizada", maximizada)
                repolir(widget)
            self.externo.setContentsMargins(*[0 if self.isMaximized() else BORDA_REDIMENSIONAR] * 4)
            self.atualizar_icones()
            self.agendar_vidro()
            self.inicio.atualizar_relogio()
        elif evento.type() == QEvent.ActivationChange and self.isActiveWindow():
            self.carregar_contatos()  # o AnyDesk pode ter ganhado contatos novos
        super().changeEvent(evento)

    def resizeEvent(self, evento):
        self.agendar_vidro()
        super().resizeEvent(evento)

    def showEvent(self, evento):
        self.agendar_vidro()
        super().showEvent(evento)

    def agendar_vidro(self):
        if not getattr(self, "_vidro_agendado", False):
            self._vidro_agendado = True
            QTimer.singleShot(0, self.atualizar_vidro)

    def atualizar_vidro(self):
        """Tema vidro: pede ao sistema para desfocar o que está atrás da janela inteira."""
        self._vidro_agendado = False
        if not self.isVisible() or not self.translucida:
            return
        janela = int(self.winId())
        if not temas.TEMAS[self.cfg["tema"]].get("vidro"):
            if self._regiao_vidro is not None:
                self.j.desfoque(janela, None)
                self._regiao_vidro = None
            return
        escala = self.devicePixelRatioF()
        raio = 0 if self.isMaximized() else round(10 * escala)
        g = self.raiz.geometry()  # sem a faixa transparente de redimensionar
        regiao = retangulos_arredondados(round(g.x() * escala), round(g.y() * escala), round(g.width() * escala),
                                         round(g.height() * escala), raio)
        if regiao != self._regiao_vidro:  # evita avisar o sistema à toa
            self.j.desfoque(janela, regiao)
            self._regiao_vidro = regiao

    # ---- redimensionar pelas beiradas (janela sem moldura) e outros eventos ----------------

    def _beirada(self, pos):
        if self.isMaximized():
            return Qt.Edges()
        b, w, h = BORDA_REDIMENSIONAR + 2, self.width(), self.height()
        bordas = Qt.Edges()
        if pos.x() < b:
            bordas |= Qt.LeftEdge
        if pos.x() >= w - b:
            bordas |= Qt.RightEdge
        if pos.y() < b:
            bordas |= Qt.TopEdge
        if pos.y() >= h - b:
            bordas |= Qt.BottomEdge
        return bordas

    def mousePressEvent(self, evento):
        bordas = self._beirada(evento.position().toPoint())
        if bordas and evento.button() == Qt.LeftButton and self.windowHandle():
            self.windowHandle().startSystemResize(bordas)
            return
        super().mousePressEvent(evento)

    def mouseMoveEvent(self, evento):
        bordas = self._beirada(evento.position().toPoint())
        if not bordas:
            self.unsetCursor()
        elif bordas in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif bordas in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif bordas & (Qt.LeftEdge | Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.SizeVerCursor)
        super().mouseMoveEvent(evento)

    def eventFilter(self, objeto, evento):
        if "notebook" not in self.__dict__:
            return False  # ainda montando a janela
        tipo = evento.type()
        if tipo == QEvent.MouseButtonPress and objeto in (self.busca, self.entrada_rapida, self.lista.viewport()):
            self.trazer_teclado_ao_app()
        elif objeto is self.barra and tipo == QEvent.Resize:
            self._centralizar_titulo()
        elif objeto is self.notebook.tabBar() and tipo == QEvent.MouseButtonRelease \
                and evento.button() == Qt.MiddleButton:
            indice = self.notebook.tabBar().tabAt(evento.position().toPoint())
            aba = self.aba_do_indice(indice)
            if aba:
                self.pedir_fechar(aba)
                return True
        return super().eventFilter(objeto, evento)

    def _centralizar_titulo(self):
        """Mantém o título no centro da barra, com espaços iguais dos dois lados."""
        linha = self.barra.layout()
        esquerda = self.bt_lateral.sizeHint().width()
        direita = sum(b.sizeHint().width() for b in (self.bt_jogo, self.bt_menu, self.bt_minimizar,
                                                     self.bt_maximizar, self.bt_fechar_janela)) + 8
        diferenca = direita - esquerda
        linha.setContentsMargins(8 + max(0, diferenca), 0, 8 + max(0, -diferenca), 0)

    # ---- jogo (baús, coleção e pet) ----------------------------------------------

    def on_alternar_jogo(self, ativo):
        if ativo:
            self.abrir_jogo()
        else:
            self.fechar_jogo()

    def mostrar_tela(self, widget):
        self.pilha.setCurrentWidget(widget)

    def tela_visivel(self):
        atual = self.pilha.currentWidget()
        if atual is self.inicio:
            return "inicio"
        if atual is self.abas_widget:
            return "abas"
        return "jogo"

    def abrir_jogo(self, tela=None):
        self._liberar_jogo.stop()
        if self.tela_jogo is None:
            try:
                from jogo.tela_qt import TelaJogo  # navegador embutido só é carregado quando precisa
            except ImportError:
                self.bt_jogo.setChecked(False)
                self.avisar("O jogo precisa do navegador embutido do Qt (pacote "
                            "python3-pyside6.qtwebenginewidgets no Ubuntu).")
                return
            self.tela_jogo = TelaJogo(self.progresso, lambda: self.cfg["tema"], self.ao_mudar_jogo,
                                      self.fechar_jogo)
            self.pilha.addWidget(self.tela_jogo)
        if tela:
            self.tela_jogo.mostrar(tela)
        visivel = self.tela_visivel()
        if visivel != "jogo":
            self._antes_do_jogo = visivel
        self.tela_jogo.atualizar()
        self.mostrar_tela(self.tela_jogo)
        self.bt_jogo.setChecked(True)
        if self.j.FORCAR_FOCO:
            self.j.dar_foco(int(self.winId()))  # teclado sai da sessão e vem para o jogo
        self.tela_jogo.setFocus()

    def fechar_jogo(self):
        if self.tela_visivel() == "jogo":
            self.mostrar_tela(self.abas_widget if self.abas else self.inicio)
        self.bt_jogo.setChecked(False)
        self.devolver_teclado_a_sessao()
        if self.tela_jogo:
            self._liberar_jogo.start()

    def liberar_jogo(self):
        """Jogo fechado há um tempo: destrói o navegador embutido (100 MB ou mais). Reabrir recria."""
        if self.tela_jogo and self.tela_visivel() != "jogo":
            self.pilha.removeWidget(self.tela_jogo)
            self.tela_jogo.deleteLater()
            self.tela_jogo = None

    def ao_mudar_jogo(self, acao, resultado):
        """A tela do jogo mudou algo que o app mostra (tema, moldura, pet, moedas...)."""
        if acao == "equipar" and resultado and resultado["tipo"] == "tema":
            self.cfg["tema"] = resultado["alvo"]
            self.cfg["ajustes"] = {k: None for k in temas.AJUSTES}
            temas.salvar(self.cfg)
        if acao == "equipar" and resultado and resultado["tipo"] == "som":
            QTimer.singleShot(0, self.sons.preparar)
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
            if not self.isActiveWindow():
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

    def atualizar_selo(self, estado=None):
        n = self.progresso.novidades(estado)
        self.selo_jogo.setText(str(n))
        self.selo_jogo.setVisible(n > 0)
        self.selo_jogo.adjustSize()
        self.selo_jogo.move(self.bt_jogo.width() - self.selo_jogo.width(), 0)

    def atualizar_pet_mini(self, pet=None):
        pet = pet or self.progresso.pet()
        flutuar = pet["chocado"] and pet["humor"] == "feliz" and not self.abas and self.cfg.get("animacoes", True)
        self.pet_imagem.definir(pet_rodape(pet["especie"], pet["acessorio"], self.devicePixelRatioF()), flutuar)
        humor = {"feliz": "smiley", "normal": "smiley-meh", "triste": "smiley-sad", "dormindo": "moon-stars"}
        nome_icone = humor.get(pet["humor"], "smiley") if pet["chocado"] else "egg"
        self.pet_nome.setText(pet["nome"])
        self.pet_humor.setPixmap(temas_qt.icone(nome_icone, self._cor_icones_lateral, 16).pixmap(16, 16))
        dicas = {"feliz": "Feliz", "normal": "Tranquilo", "triste": "Precisa de você", "dormindo": "Dormindo"}
        self.pet_humor.setToolTip(dicas.get(pet["humor"], "") if pet["chocado"] else "Ovo")
        self.pet_fala.setText(pet["fala"])
        self.pet_fala.setToolTip(pet["fala"])

    def batimento(self):
        """A cada minuto: pet acordado, avisos de baú pronto e da recompensa diária."""
        self.progresso.pet_batimento()
        estado = self.progresso.estado()
        prontos = {(b["espaco"], b["tipo"]) for b in estado["baus"] if b and b["situacao"] == "pronto"}
        for _espaco, tipo in prontos - self._baus_prontos:
            nome = cat_jogo.BAUS[tipo]["nome"]
            if self.isActiveWindow():
                self.avisar(f"{nome} pronto para abrir!", "gift")
            else:
                self.notificacoes.mostrar("Baú pronto!", f"Seu {nome} já pode ser aberto.")
        self._baus_prontos = prontos
        hoje = time.strftime("%Y-%m-%d")
        if estado["diario"]["disponivel"] and self._diario_avisado != hoje:
            self._diario_avisado = hoje
            self.notificacoes.mostrar("Recompensa diária", "Sua recompensa de hoje está esperando!")
        self.atualizar_selo(estado)
        self.atualizar_pet_mini(estado["pet"])
        if self.tela_jogo and self.tela_visivel() == "jogo":
            self.tela_jogo.atualizar()

    # ---- teclado -------------------------------------------------------------
    #
    # No Linux, a janela do AnyDesk não fala o protocolo XEMBED, então o teclado não chega direito
    # nela (atalhos e teclas especiais se perdem). Solução: enquanto uma sessão está na tela, o
    # foco do teclado do X11 fica direto na janela do AnyDesk. No Windows isso não é preciso.

    def aba_atual(self):
        if self.tela_visivel() != "abas":
            return None  # jogo aberto: o teclado fica no app
        return next((a for a in self.abas if a.pagina is self.notebook.currentWidget() and a.janela), None)

    def aba_do_indice(self, indice):
        pagina = self.notebook.widget(indice)
        return next((a for a in self.abas if a.pagina is pagina), None)

    def usa_teclado(self, widget):
        """Campo de texto ou lista de contatos (setas e Enter): o teclado precisa ficar no app."""
        return isinstance(widget, QLineEdit) or bool(widget and self.lateral.isAncestorOf(widget))

    def on_foco_widget(self, _antigo, novo):
        # Foco foi para um campo de texto ou para a lista do app (Tab, Ctrl+F...): teclado no app.
        if self.usa_teclado(novo) and novo.window() is self:
            self.trazer_teclado_ao_app()

    def trazer_teclado_ao_app(self):
        if self.j.FORCAR_FOCO:
            self.j.dar_foco(int(self.winId()))
            self._foco_ok = None

    def devolver_teclado_a_sessao(self):
        foco = self.focusWidget()
        if foco and foco.window() is self:
            foco.clearFocus()
        self._foco_ok = None

    def janela_ativa(self):
        if self.isActiveWindow():
            return True
        # O foco do X11 dentro da sessão encaixada também conta como janela ativa.
        return self.j.contem(int(self.winId()), self.j.foco())

    def manter_foco(self):
        aba = self.aba_atual()
        if not aba or not self.janela_ativa():
            return
        if self.usa_teclado(self.focusWidget()):
            # Clicou na tela da sessão enquanto digitava: devolve o teclado ao AnyDesk.
            if not self.j.clicou_dentro(aba.janela):
                return
            self.devolver_teclado_a_sessao()
        foco = self.j.foco()
        if (aba.janela, foco) == self._foco_ok:
            return
        if self.j.contem(aba.janela, foco):
            self._foco_ok = (aba.janela, foco)
        else:
            self._foco_ok = None
            self.j.dar_foco(aba.janela)

    def ir_para_busca(self):
        self.bt_lateral.setChecked(True)
        self.trazer_teclado_ao_app()
        self.busca.setFocus()

    # ---- avisos ----------------------------------------------------------------

    def avisar(self, texto, icone=None):
        """icone: nome de um ícone Phosphor (ex.: "gift")."""
        self.aviso.setStyleSheet(self.styleSheet())
        self.aviso.setFont(self.font())
        self.aviso.mostrar(texto, icone, self._cor_icones)

    # ---- contatos --------------------------------------------------------------

    def carregar_contatos(self):
        itens = self.contatos.listar()
        if itens == self._lista_atual:
            return  # nada mudou; evita perder a seleção
        self._lista_atual = itens
        self.lista.clear()
        for ordem, (cid, nome) in enumerate(itens):
            linha = LinhaContato(cid, nome, self.on_renomear, ordem)
            linha.editar.setIcon(temas_qt.icone("pencil-simple", self._cor_icones_lateral
                                                if hasattr(self, "_cor_icones_lateral") else "#888888", 14))
            item = QListWidgetItem()
            item.setSizeHint(linha.sizeHint())
            self.lista.addItem(item)
            self.lista.setItemWidget(item, linha)
        self.contagem.setText(str(len(itens)))
        self.marcar_conectados()
        self.filtrar_contatos()

    def linhas(self):
        return [(self.lista.item(i), self.lista.itemWidget(self.lista.item(i))) for i in range(self.lista.count())]

    def marcar_conectados(self):
        self._conectados = {a.cid for a in self.abas}
        for _item, linha in self.linhas():
            linha.ponto.setVisible(linha.cid in self._conectados)
        self.ordenar_contatos()

    def ordenar_contatos(self):
        """Conectados primeiro, depois os usados recentemente, depois a ordem do AnyDesk."""
        recentes = self.contatos.recentes

        def chave(linha):
            recente = recentes.index(linha.cid) if linha.cid in recentes else len(recentes)
            return (linha.cid not in self._conectados, recente, linha.ordem)

        atuais = [linha for _item, linha in self.linhas()]
        ordenadas = sorted(atuais, key=chave)
        if [l.cid for l in atuais] == [l.cid for l in ordenadas]:
            return
        dados = [(l.cid, l.nome, l.ordem) for l in ordenadas]
        selecionado = self.lista.currentItem() and self.lista.itemWidget(self.lista.currentItem()).cid
        self.lista.clear()
        for cid, nome, ordem in dados:
            linha = LinhaContato(cid, nome, self.on_renomear, ordem)
            linha.editar.setIcon(temas_qt.icone("pencil-simple", self._cor_icones_lateral, 14))
            linha.ponto.setVisible(cid in self._conectados)
            item = QListWidgetItem()
            item.setSizeHint(linha.sizeHint())
            self.lista.addItem(item)
            self.lista.setItemWidget(item, linha)
            if cid == selecionado:
                self.lista.setCurrentItem(item)
        self.filtrar_contatos()

    def filtrar_contatos(self, *_a):
        busca = self.busca.text()
        visiveis = 0
        for item, linha in self.linhas():
            mostra = linha.combina(busca)
            item.setHidden(not mostra)
            visiveis += mostra
        self.vazio.setVisible(visiveis == 0)
        self.lista.setVisible(visiveis > 0)

    def on_renomear(self, cid, botao):
        balao = QDialog(self, Qt.Popup)
        balao.setStyleSheet(self.styleSheet())
        coluna = QVBoxLayout(balao)
        coluna.setContentsMargins(12, 12, 12, 12)
        coluna.setSpacing(8)
        coluna.addWidget(QLabel(f"Nome para {formatar_id(cid)}"))
        entrada = QLineEdit(self.contatos.nome(cid), placeholderText="Ex.: Padaria – caixa 1")
        entrada.setMinimumWidth(240)
        coluna.addWidget(entrada)
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        remover = QPushButton("Sem nome")
        salvar = QPushButton("Salvar", objectName="conectar", default=True)
        botoes.addWidget(remover)
        botoes.addWidget(salvar)
        coluna.addLayout(botoes)

        def gravar(nome):
            self.contatos.renomear(cid, nome)
            balao.accept()
            self._lista_atual = None
            self.carregar_contatos()
            self.atualizar_titulos()
            self.atualizar_recentes()

        salvar.clicked.connect(lambda: gravar(entrada.text().strip()))
        entrada.returnPressed.connect(lambda: gravar(entrada.text().strip()))
        remover.clicked.connect(lambda: gravar(""))
        balao.adjustSize()
        canto = botao.mapToGlobal(QPoint(botao.width() + 4, -balao.height() // 2 + botao.height() // 2))
        balao.move(canto)
        entrada.setFocus()
        balao.exec()

    def on_busca_enter(self):
        texto = self.busca.text().strip()
        if not texto:
            return
        sem_espacos = texto.replace(" ", "")
        visiveis = [(item, linha) for item, linha in self.linhas() if linha.combina(texto)]
        exato = next((linha for _item, linha in visiveis if linha.cid == sem_espacos), None)
        if exato or len(visiveis) == 1:
            self.abrir((exato or visiveis[0][1]).cid)
        elif sem_espacos.isdigit() or "@" in texto:  # ID ou endereço (ex.: nome@ad)
            self.abrir_texto(texto)
        elif visiveis:
            # Vários contatos com esse nome: escolhe com as setas e Enter, sem conectar às cegas.
            self.lista.setCurrentItem(visiveis[0][0])
            self.lista.setFocus()
            self.avisar(f"{len(visiveis)} contatos encontrados: escolha com as setas e Enter.")
            return
        else:
            self.avisar("Nenhum contato com esse nome. Para conectar, digite o ID.")
            return
        self.busca.clear()

    def on_conectar_rapido(self):
        texto = self.entrada_rapida.text().strip()
        if texto:
            self.abrir_texto(texto)
            self.entrada_rapida.clear()

    def abrir_texto(self, texto):
        sem_espacos = texto.replace(" ", "")
        self.abrir(sem_espacos if sem_espacos.isdigit() else texto)

    # ---- conexões --------------------------------------------------------------

    def janelas_livres(self):
        """Janelas do AnyDesk visíveis que ainda não estão em nenhuma aba."""
        encaixadas = {a.janela for a in self.abas}
        return [w for w in self.j.anydesk() if w not in encaixadas]

    def abrir(self, cid):
        # Já conectado: só mostra a aba.
        for aba in self.abas:
            if aba.cid == cid:
                self.notebook.setCurrentWidget(aba.pagina)
                self.mostrar_tela(self.abas_widget)
                return
        antes = set(self.janelas_livres())
        try:
            pid = self.j.abrir(cid)
        except OSError:
            self.avisar("AnyDesk não encontrado. Instale pelo site anydesk.com.")
            return
        aba = self.nova_aba(cid)
        aba.pid = pid
        inicio = time.monotonic()

        def procurar():
            if aba not in self.abas:
                return  # aba fechada enquanto conectava
            passou_ms = (time.monotonic() - inicio) * 1000
            livres = self.janelas_livres()
            # Cada "anydesk <ID>" sobe um processo próprio; se não achar pelo PID,
            # cai para "qualquer janela do AnyDesk que surgiu depois do clique".
            novas = ([w for w in livres if self.j.pid(w) == pid] or [w for w in livres if w not in antes])
            if novas:
                self.encaixar(aba, novas[0])
            elif passou_ms > DETECT_TIMEOUT_MS:
                self.fechar(aba)
                self.avisar(f"A janela de {formatar_id(cid)} não apareceu.")
            else:
                QTimer.singleShot(POLL_RAPIDO_MS if passou_ms < POLL_RAPIDO_ATE_MS else POLL_LENTO_MS, procurar)

        QTimer.singleShot(POLL_RAPIDO_MS, procurar)

    def on_capturar(self):
        livres = self.janelas_livres()
        if not livres:
            dica = " Ela precisa ter sido aberta com GDK_BACKEND=x11." if plataforma.LINUX else ""
            self.avisar("Nenhuma janela do AnyDesk livre." + dica)
            return
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Capturar janela")
        coluna = QVBoxLayout(dialogo)
        lista = QListWidget()
        for w in livres:
            item = QListWidgetItem(self.j.titulo(w) or hex(w))
            item.setData(Qt.UserRole, w)
            lista.addItem(item)
        lista.setCurrentRow(0)
        coluna.addWidget(lista)
        botoes = QDialogButtonBox()
        botoes.addButton("Cancelar", QDialogButtonBox.RejectRole)
        botoes.addButton("Capturar", QDialogButtonBox.AcceptRole)
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        coluna.addWidget(botoes)
        if dialogo.exec() == QDialog.Accepted and lista.currentItem():
            w = lista.currentItem().data(Qt.UserRole)
            aba = self.nova_aba(id_no_titulo(self.j.titulo(w)))
            aba.pid = self.j.pid(w)
            self.encaixar(aba, w)

    # ---- abas ------------------------------------------------------------------

    def nova_aba(self, cid):
        self.fechar_jogo()  # conectou em alguém: mostra a conexão
        aba = Aba(cid)
        self.abas.append(aba)
        self.estilizar_cabeca(aba)
        aba.fechar.clicked.connect(lambda: self.pedir_fechar(aba))
        aba.mostrar_nome(f"Conectando {self.nome_aba(aba)}…")
        indice = self.notebook.addTab(aba.pagina, "")
        self.notebook.tabBar().setTabButton(indice, QTabBar.LeftSide, aba.cabeca)
        self.atualizar_tela()
        self.notebook.setCurrentIndex(indice)
        self.marcar_conectados()
        return aba

    def estilizar_cabeca(self, aba):
        # O rótulo da aba não herda a fonte da janela (o QTabBar usa a dele): define na mão.
        aba.cabeca.setFont(self.font())
        aba.rotulo.setFont(self.font())
        aba.fechar.setIcon(temas_qt.icone("x", self._cor_icones_barra, 12))
        aba.girando.cor = temas_qt.cor(self._cor_icones_barra)

    def encaixar(self, aba, janela):
        aba.janela = janela
        aba.girando.hide()
        aba.ponto.show()
        aba.qjanela = QWindow.fromWinId(janela)
        aba.caixa = QWidget.createWindowContainer(aba.qjanela, aba.pagina)
        aba.caixa.setFocusPolicy(Qt.StrongFocus)
        aba.pagina.layout().addWidget(aba.caixa)
        aba.inicio = time.monotonic()
        if aba.cid:
            self.contatos.usar(aba.cid)
            self.atualizar_recentes()
            self.marcar_conectados()  # reordena a lista (recentes)
        self.sons.tocar(self.progresso.equipados().get("som"))
        self.atualizar_titulos()
        self.atualizar_pet_mini()  # com sessão aberta o pet do rodapé para de animar
        self.devolver_teclado_a_sessao()  # sessão nova: teclado vai para ela, não para a busca

    def nome_aba(self, aba):
        """Apelido do contato > nome do computador no título da janela > ID formatado."""
        if aba.cid and self.contatos.nome(aba.cid):
            return self.contatos.nome(aba.cid)
        if aba.janela:
            titulo = self.j.titulo(aba.janela)
            if not aba.cid:
                aba.cid = id_no_titulo(titulo)
            limpo = limpar_titulo(titulo)
            if limpo and limpo.replace(" ", "") != (aba.cid or ""):
                return limpo
        return formatar_id(aba.cid) if aba.cid else "AnyDesk"

    def atualizar_titulos(self):
        for aba in self.abas:
            if aba.janela:
                aba.mostrar_nome(self.nome_aba(aba))
                dica = self.j.titulo(aba.janela)
                if aba.cid:
                    dica = f"{dica}\nID: {formatar_id(aba.cid)}"
                aba.cabeca.setToolTip(dica)

    def conferir_sessoes(self):
        """A janela do AnyDesk sumiu (conexão encerrada do outro lado, etc.): fecha a aba."""
        for aba in list(self.abas):
            if aba.janela and not self.j.existe(aba.janela):
                self.remover_aba(aba)

    def atualizar_tela(self):
        destino = self.abas_widget if self.abas else self.inicio
        if self.tela_visivel() == "jogo":
            self._antes_do_jogo = "abas" if self.abas else "inicio"  # não tira a pessoa do jogo
        else:
            self.mostrar_tela(destino)
        n = len(self.abas)
        self.subtitulo.setText(f"{n} conexão aberta" if n == 1 else f"{n} conexões abertas")
        self.subtitulo.setVisible(n > 0)

    def remover_aba(self, aba):
        if aba not in self.abas:
            return
        self.registrar_atendimento(aba)
        self.abas.remove(aba)
        indice = self.notebook.indexOf(aba.pagina)
        if indice >= 0:
            self.notebook.removeTab(indice)
        if aba.caixa:
            # Solta a janela antes de apagar a aba: senão o Qt tenta destruir a janela do AnyDesk.
            aba.qjanela.setParent(None)
        aba.pagina.deleteLater()
        self.atualizar_tela()
        self.marcar_conectados()
        self.atualizar_pet_mini()

    def confirmar(self, titulo, texto, acao):
        """Pergunta antes de algo que não dá para desfazer. acao: texto do botão de confirmar."""
        caixa = QMessageBox(QMessageBox.Question, titulo, titulo, parent=self)
        caixa.setInformativeText(texto)
        cancelar = caixa.addButton("Cancelar", QMessageBox.RejectRole)
        caixa.addButton(acao, QMessageBox.DestructiveRole)
        caixa.setDefaultButton(cancelar)
        caixa.exec()
        return caixa.clickedButton() is not cancelar

    def pedir_fechar(self, aba):
        """Fechar pela aba (X ou botão do meio). Sessão longa pede confirmação: derruba o cliente."""
        if aba.inicio and time.monotonic() - aba.inicio > CONFIRMAR_FECHAR_S:
            if not self.confirmar(f"Encerrar a conexão com {self.nome_aba(aba)}?",
                                  "O cliente será desconectado.", "Encerrar"):
                return
        self.fechar(aba)

    def fechar(self, aba):
        self.j.encerrar(aba.janela, aba.pid)
        self.remover_aba(aba)

    def closeEvent(self, evento):
        if self.abas:
            n = len(self.abas)
            texto = ("A conexão aberta será encerrada." if n == 1 else
                     f"As {n} conexões abertas serão encerradas.")
            if not self.confirmar("Fechar o NaView?", texto, "Encerrar e sair"):
                evento.ignore()
                return
        for aba in list(self.abas):
            self.fechar(aba)
        self.aviso.hide()
        evento.accept()


def main():
    # Nome do programa para o sistema: liga a janela ao atalho naview.desktop (StartupWMClass) e
    # faz a barra de tarefas mostrar o ícone certo.
    sys.argv[0] = "naview"
    QGuiApplication.setDesktopFileName("naview")
    app = QApplication(sys.argv)
    app.setApplicationName("naview")
    app.setApplicationDisplayName("NaView")
    temas_qt.carregar_fontes()
    janela = App()
    janela.show()
    if "--verificar" in sys.argv:
        # Usado pelo GitHub Actions: abre, abre o jogo (confere o navegador embutido) e fecha.
        QTimer.singleShot(1500, janela.abrir_jogo)
        QTimer.singleShot(6000, app.quit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
