#!/usr/bin/env python3
"""Simula meses de uso do jogo para medir o ritmo das recompensas (economia).

Usa as regras reais de jogo/progresso.py e jogo/catalogo.py, num banco temporário (não toca no
progresso de ninguém). Mostra em quantos dias corridos cada marco acontece: mediana e faixa de
vários sorteios, para dois perfis de demanda.

    python3 ferramentas/simular_economia.py            # 20 sorteios, 400 dias
    python3 ferramentas/simular_economia.py 5 200      # 5 sorteios, 200 dias (mais rápido)

O jogador simulado: trabalha de segunda a sexta, das 9h às 18h; abre o jogo em horários fixos;
pega a recompensa diária e o baú grátis; abre e destrava baús; compra na loja só cartas que não
tem; melhora toda carta que puder (temas primeiro).
"""
import datetime
import os
import random
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jogo import catalogo as cat  # noqa: E402
from jogo.progresso import ErroJogo, Progresso  # noqa: E402

INICIAIS = tuple(cat.INICIAIS)
POR_RARIDADE = {r: {c["id"] for c in cat.CARTAS if c["raridade"] == r} for r in cat.ORDEM_RARIDADE}
PERFIS = [  # (nome, atendimentos por dia, horas em que abre o jogo)
    ("25 atendimentos/dia, abre o jogo 4x", 25, (9, 12, 15, 18)),
    ("15 atendimentos/dia, abre o jogo 2x", 15, (9, 14)),
]
MARCOS = ["1a rara", "1a epica", "1a lendaria", "1a mitica", "metade", "todas comum", "todas rara",
          "todas epica", "todas lendaria", "todas mitica", "tudo", "conta 5", "conta 10", "conta 15",
          "tema dourado", "tema lendario/mitico dourado"]


def _olhar_jogo(p):
    try:
        p.resgatar_diario()
    except ErroJogo:
        pass
    while True:
        try:
            p.abrir_bau_gratis()
        except ErroJogo:
            break
    for b in p.estado()["baus"]:
        if b and b["situacao"] == "pronto":
            p.abrir_bau(b["espaco"])
    baus = p.estado()["baus"]
    if not any(b and b["situacao"] == "destravando" for b in baus):
        for b in baus:
            if b and b["situacao"] == "trancado":
                p.destravar_bau(b["espaco"])
                break
    for o in p.estado()["loja"]["ofertas"]:
        if not o["comprada"] and not p.possui(o["carta"]) and p.perfil()["moedas"] >= o["preco"]:
            p.comprar_oferta(o["indice"])
    for cid in sorted(p.cartas(), key=lambda c: not c.startswith("tema")):
        try:
            p.melhorar_carta(cid)
        except ErroJogo:
            pass


def rodar(semente, atendimentos, olhadas, dias, pasta):
    relogio = [0.0]
    banco = Path(pasta) / f"sim{semente}.db"
    banco.unlink(missing_ok=True)
    p = Progresso(banco, agora=lambda: relogio[0],
                  hoje=lambda: datetime.date.fromtimestamp(relogio[0]), rnd=random.Random(semente))
    # Banco descartável: sem esperar o disco gravar a cada commit (era ~90% do tempo da simulação).
    p.db.execute("PRAGMA synchronous=OFF")
    p.db.execute("PRAGMA journal_mode=MEMORY")
    marcos = {}
    contador = [0]
    for d in range(dias):
        base = datetime.datetime(2026, 1, 5) + datetime.timedelta(days=d)
        if base.weekday() >= 5:
            continue
        for hora in range(9, 19):
            relogio[0] = base.replace(hour=hora).timestamp()
            if hora in olhadas:
                _olhar_jogo(p)
            # Espalha os atendimentos do dia pelas 10 horas de trabalho.
            for _ in range(atendimentos // 10 + (1 if hora - 9 < atendimentos % 10 else 0)):
                p.registrar_atendimento(f"cliente{contador[0]}", 600)  # IDs sempre diferentes
                contador[0] += 1
        dia = d + 1
        cartas = p.cartas()
        for r, ids in POR_RARIDADE.items():
            tem = ids & cartas.keys()
            if tem - set(INICIAIS):
                marcos.setdefault(f"1a {r}", dia)
            if tem == ids:
                marcos.setdefault(f"todas {r}", dia)
        if len(cartas) >= len(cat.CARTAS) / 2:
            marcos.setdefault("metade", dia)
        if len(cartas) == len(cat.CARTAS):
            marcos.setdefault("tudo", dia)
        nivel = p.perfil()["nivel"]
        for n in (5, 10, 15):
            if nivel >= n:
                marcos.setdefault(f"conta {n}", dia)
        for cid, info in cartas.items():
            if cid.startswith("tema-") and info["nivel"] >= cat.NIVEL_MAX:
                marcos.setdefault("tema dourado", dia)
                if cat.CARTAS_POR_ID[cid]["raridade"] in ("lendaria", "mitica"):
                    marcos.setdefault("tema lendario/mitico dourado", dia)
    p.db.close()
    return marcos


def main():
    sorteios = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    dias = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    with tempfile.TemporaryDirectory() as pasta:
        for nome, atendimentos, olhadas in PERFIS:
            resultados = [rodar(s, atendimentos, olhadas, dias, pasta) for s in range(sorteios)]
            print(f"== {nome}")
            for marco in MARCOS:
                valores = [r[marco] for r in resultados if marco in r]
                if not valores:
                    print(f"  {marco:30} não aconteceu em {dias} dias")
                    continue
                falta = f"  [{len(valores)}/{sorteios} chegaram]" if len(valores) < sorteios else ""
                print(f"  {marco:30} dia {statistics.median(valores):.0f} "
                      f"(faixa {min(valores)}-{max(valores)}){falta}")


if __name__ == "__main__":
    main()
