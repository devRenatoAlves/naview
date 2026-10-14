#!/usr/bin/env python3
"""Gera os sons do jogo (WAV) em sons/. Todos sintetizados aqui, sem arquivos de terceiros."""
import math
import random
import struct
import wave
from pathlib import Path

SAIDA = Path(__file__).resolve().parent.parent / "sons"
TAXA = 22050


def quadrada(f, t):
    return 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0


def seno(f, t):
    return math.sin(2 * math.pi * f * t)


def nota(onda, freq, dur, volume=0.3, decaimento=0.0, freq_final=None):
    """Uma nota; freq_final faz a frequência deslizar até ela (efeito 'piu')."""
    amostras = []
    n = int(TAXA * dur)
    fase = 0.0
    for i in range(n):
        t = i / TAXA
        f = freq if freq_final is None else freq + (freq_final - freq) * i / n
        fase += f / TAXA
        env = math.exp(-decaimento * t) if decaimento else 1.0
        env *= min(1.0, i / (TAXA * 0.004), (n - i) / (TAXA * 0.01))  # sem estalos nas pontas
        amostras.append(volume * env * onda(1, fase))
    return amostras


def silencio(dur):
    return [0.0] * int(TAXA * dur)


def mistura(*faixas):
    tamanho = max(len(f) for f in faixas)
    return [sum(f[i] for f in faixas if i < len(f)) for i in range(tamanho)]


def salvar(nome, amostras):
    SAIDA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(SAIDA / f"{nome}.wav"), "wb") as arq:
        arq.setnchannels(1)
        arq.setsampwidth(2)
        arq.setframerate(TAXA)
        arq.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, a)) * 32000)) for a in amostras))


def arpejo(onda, notas, dur, volume=0.25, ultima=0.4):
    sons = []
    for i, f in enumerate(notas):
        sons += nota(onda, f, ultima if i == len(notas) - 1 else dur, volume,
                     decaimento=3 if i == len(notas) - 1 else 0)
    return sons


def main():
    # sons de conexão (cartas)
    salvar("bip", nota(quadrada, 880, 0.06, 0.2) + nota(quadrada, 1320, 0.09, 0.2))
    salvar("moeda", nota(quadrada, 988, 0.07, 0.2) + nota(quadrada, 1319, 0.35, 0.2, decaimento=6))
    salvar("ding", mistura(nota(seno, 1046, 1.4, 0.35, decaimento=3),
                           nota(seno, 2093, 1.0, 0.12, decaimento=5),
                           nota(seno, 3136, 0.6, 0.05, decaimento=7)))
    salvar("fanfarra", arpejo(quadrada, [523, 659, 784, 1046], 0.11, 0.18, ultima=0.5))
    # sons do jogo
    rnd = random.Random(3)
    ruido = [0.15 * rnd.uniform(-1, 1) * (1 - i / (TAXA * 0.45)) for i in range(int(TAXA * 0.45))]
    salvar("abrir", mistura(nota(seno, 180, 0.45, 0.35, freq_final=900), ruido))
    salvar("carta", nota(seno, 500, 0.09, 0.35, freq_final=1200))
    salvar("lendaria", mistura(arpejo(quadrada, [523, 659, 784, 1046, 1318], 0.09, 0.14, ultima=0.7),
                               silencio(0.36) + nota(seno, 2637, 0.6, 0.08, decaimento=4)))
    salvar("clique", nota(seno, 1500, 0.03, 0.2))
    salvar("nhac", nota(quadrada, 220, 0.05, 0.15) + silencio(0.04) + nota(quadrada, 196, 0.06, 0.15))
    salvar("pet_feliz", nota(seno, 900, 0.08, 0.25, freq_final=1400) + nota(seno, 1400, 0.1, 0.25,
                                                                           freq_final=1800))
    salvar("melhorar", arpejo(seno, [659, 784, 988, 1318], 0.07, 0.25, ultima=0.35))
    print("sons gerados em", SAIDA)


if __name__ == "__main__":
    main()
