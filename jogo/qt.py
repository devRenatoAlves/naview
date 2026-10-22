"""Partes do jogo que aparecem no próprio app (versão Qt): pet no rodapé, sons e notificações."""
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QRect, QUrl, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

import plataforma

from . import catalogo as cat

RAIZ = Path(__file__).resolve().parent.parent
ARTE = RAIZ / "arte"
SONS = RAIZ / "sons"


def _desenho(caminho, w, h):
    imagem = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    imagem.fill(Qt.transparent)
    pintor = QPainter(imagem)
    QSvgRenderer(str(caminho)).render(pintor)
    pintor.end()
    return imagem


@lru_cache(maxsize=16)
def compor_pet(especie, acessorio, unidade=1):
    """Imagem do pet (ou do ovo) com o acessório, num quadro de PET_LADO x (PET_LADO + acima), acima = cat.acima_de(pet).

    As linhas de cima ficam livres para chapéus. unidade = tamanho de cada pixel do desenho.
    """
    lado, acima = cat.PET_LADO, cat.acima_de(especie)
    tela = QImage(lado * unidade, (lado + acima) * unidade, QImage.Format_ARGB32_Premultiplied)
    tela.fill(Qt.transparent)
    extra = cat.ALTURA_EXTRA.get(especie, 0)  # pet mais alto que o quadro: passa do topo
    camadas = [(ARTE / "pets" / f"{especie or 'ovo'}.svg", 0, acima - extra, lado, lado + extra)]
    if especie and acessorio:
        e = cat.encaixe_acessorio(especie, acessorio)
        camadas.append((ARTE / "acessorios" / f"{e['arquivo']}.svg", e["x"], e["y"], e["w"], e["h"]))
    pintor = QPainter(tela)
    pintor.setClipRect(tela.rect())  # recorta o que passar da borda do quadro
    for caminho, x, y, w, h in camadas:
        pintor.drawImage(x * unidade, y * unidade, _desenho(caminho, w * unidade, h * unidade))
    pintor.end()
    return tela


# Área do pet no rodapé, em px: o desenho é ampliado até caber em RODAPE_W x RODAPE_H, com
# RODAPE_FOLGA px livres em cima para a animação de flutuar não cortar a cabeça.
RODAPE_W, RODAPE_H, RODAPE_FOLGA = 72, 56, 8
RODAPE_ZOOM_MAX = 1.7


def _caixa_opaca(imagem):
    """QRect dos pixels não transparentes."""
    w, h = imagem.width(), imagem.height()
    linhas = [y for y in range(h) if any(imagem.pixelColor(x, y).alpha() for x in range(w))]
    if not linhas:
        return QRect(0, 0, w, h)
    colunas = [x for x in range(w) if any(imagem.pixelColor(x, y).alpha() for y in linhas)]
    return QRect(colunas[0], linhas[0], colunas[-1] - colunas[0] + 1, linhas[-1] - linhas[0] + 1)


@lru_cache(maxsize=16)
def pet_rodape(especie, acessorio, escala=1.0):
    """Pet do rodapé, sem o espaço vazio do quadro e ampliado para o mesmo tamanho na tela.

    No quadro, cada pet ocupa uma parte diferente (o slime tem 35 px de altura, o Gengar 56) e
    todos ficam encostados embaixo; sem recortar, os menores ficavam pequenos e baixos.
    escala: escala da tela (200% = 2.0), para o desenho sair nítido.
    """
    caixa = _caixa_opaca(compor_pet(especie, acessorio))
    zoom = min(RODAPE_W / caixa.width(), RODAPE_H / caixa.height(), RODAPE_ZOOM_MAX)
    # Amplia a partir da versão 4x e reduz com filtro: o pixel art fica nítido sem degraus tortos.
    grande = compor_pet(especie, acessorio, 4).copy(caixa.x() * 4, caixa.y() * 4,
                                                    caixa.width() * 4, caixa.height() * 4)
    pw, ph = round(caixa.width() * zoom * escala), round(caixa.height() * zoom * escala)
    desenho = grande.scaled(pw, ph, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    tela = QImage(round(RODAPE_W * escala), round((RODAPE_H + RODAPE_FOLGA) * escala),
                  QImage.Format_ARGB32_Premultiplied)
    tela.fill(Qt.transparent)
    pintor = QPainter(tela)
    pintor.drawImage((tela.width() - pw) // 2, round(RODAPE_FOLGA * escala) + (round(RODAPE_H * escala) - ph) // 2,
                     desenho)
    pintor.end()
    pixmap = QPixmap.fromImage(tela)
    pixmap.setDevicePixelRatio(escala)
    return pixmap


class Sons:
    """Toca os WAV de sons/ (QSoundEffect, carregado só na primeira vez)."""

    def __init__(self):
        self._efeitos = {}
        self._ok = None

    def preparar(self):
        if self._ok is None:
            try:
                from PySide6.QtMultimedia import QSoundEffect
                self._QSoundEffect = QSoundEffect
                self._ok = True
            except ImportError:
                self._ok = False  # sem QtMultimedia: segue sem som

    def tocar(self, nome):
        if not nome:
            return
        arquivo = SONS / f"{nome}.wav"
        if not arquivo.exists():
            return
        self.preparar()
        if not self._ok:
            return
        if nome not in self._efeitos:
            efeito = self._QSoundEffect()
            efeito.setSource(QUrl.fromLocalFile(str(arquivo)))
            self._efeitos[nome] = efeito
        self._efeitos[nome].play()


class Notificacoes:
    """Notificações do sistema: serviço de notificações do Linux (D-Bus) ou balão do Windows."""

    def __init__(self, nome_app="NaView", icone="naview", icone_qt=None):
        self.nome_app = nome_app
        self.icone = icone
        self.icone_qt = icone_qt  # QIcon, usado no Windows
        self._bandeja = None

    def mostrar(self, titulo, texto):
        try:
            if plataforma.WINDOWS:
                self._windows(titulo, texto)
            else:
                self._linux(titulo, texto)
        except Exception:  # noqa: BLE001 - serviço de notificação fora do ar não pode derrubar o app
            pass

    def _linux(self, titulo, texto):
        from PySide6.QtDBus import QDBusConnection, QDBusInterface

        servico = QDBusInterface("org.freedesktop.Notifications", "/org/freedesktop/Notifications",
                                 "org.freedesktop.Notifications", QDBusConnection.sessionBus())
        if servico.isValid():
            servico.call("Notify", self.nome_app, 0, self.icone, titulo, texto, [], {}, -1)

    def _windows(self, titulo, texto):
        from PySide6.QtWidgets import QSystemTrayIcon

        if self._bandeja is None:
            self._bandeja = QSystemTrayIcon(self.icone_qt)
            self._bandeja.setToolTip(self.nome_app)
        self._bandeja.show()  # o Windows só mostra o balão de um ícone que está na bandeja
        self._bandeja.showMessage(titulo, texto, self.icone_qt)
