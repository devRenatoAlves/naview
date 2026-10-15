"""Pets e acessórios desenhados em pixel art (grade de 48 x 48 para os pets).

Cada desenho é feito de camadas vetoriais (ver pixel_vetor.py). Os Pokémon não estão aqui: usam os
sprites oficiais, baixados por baixar_sprites.py.
"""
import re

from pixel_vetor import montar, sombreado as sb


def espelho_x(d, lado=48):
    """Espelha um caminho simples "M x y L x y Q x y x y ..." na horizontal."""
    partes = re.findall(r"[A-Za-z]|-?[\d.]+", d)
    saida, eixo_x = [], True
    for p in partes:
        if p.isalpha():
            saida.append(p)
            eixo_x = True
            continue
        saida.append(f"{lado - float(p):g}" if eixo_x else p)
        eixo_x = not eixo_x
    return " ".join(saida)


def olhos(x_esq, x_dir, y, cor="#1b1b1b", brilho="#ffffff", alto=4):
    """Dois olhos de 3 x alto pixels (cantos arredondados) com brilho no alto à esquerda."""
    pontos = []
    for cx in (x_esq, x_dir):
        for dy in range(alto):
            larg = (0,) if dy in (0, alto - 1) else (-1, 0, 1)
            pontos += [(cx + dx, y + dy) for dx in larg]
    return [(cor, pontos), (brilho, [(x_esq - 1, y + 1), (x_dir - 1, y + 1)])]


def bochechas(x_esq, x_dir, y, cor):
    return (cor, [(x, y) for x in (x_esq, x_esq + 1, x_dir, x_dir + 1)])


# ---- cachorros ----------------------------------------------------------------

def pinscher():
    CA, CAs, CAl, BG, BGs, RO = "#c06a2b", "#8a4519", "#e08a45", "#e8a565", "#c9864a", "#f0a487"
    orelha = "M11 22 Q7 10 9 1 Q19 6 22 13 Z"
    interna = "M12.5 17 Q10.5 10 11.5 5 Q17 8.5 19 13 Z"
    return montar([
        (sb(f'<path d="{orelha}"/>', CA, CAs, id_="o1") + f'<path d="{interna}" fill="{RO}"/>', [CA, CAs, RO], True),
        (sb(f'<path d="{espelho_x(orelha)}"/>', CA, CAs, id_="o2")
         + f'<path d="{espelho_x(interna)}" fill="{RO}"/>', [CA, CAs, RO], True),
        (sb('<ellipse cx="24" cy="39" rx="10" ry="8"/>', CA, CAs, id_="b")
         + f'<ellipse cx="24" cy="39.5" rx="4.5" ry="6" fill="{BG}"/>', [CA, CAs, BG], True),
        (f'<ellipse cx="20" cy="45" rx="2.6" ry="2.4" fill="{CA}"/><ellipse cx="28" cy="45" rx="2.6" ry="2.4" fill="{CA}"/>',
         [CA], True),
        (sb('<ellipse cx="24" cy="23" rx="14" ry="10.5"/>', CA, CAs,
            f'<ellipse cx="17" cy="15.5" rx="4.5" ry="1.8" fill="{CAl}"/>', id_="h"), [CA, CAs, CAl], True),
        (sb('<ellipse cx="24" cy="29" rx="6.5" ry="4.3"/>', BG, BGs, dx=-0.8, dy=-1, id_="f"), [BG, BGs], True),
    ], "#3a200c", detalhes=[
        (BG, [(15, 18), (16, 18), (31, 18), (32, 18)]),
        *olhos(16, 31, 20, "#2b1a0e"),
        ("#1b1b1b", [(22, 26), (23, 26), (24, 26), (25, 26), (23, 27), (24, 27)]),
        ("#2b1a0e", [(23, 28), (24, 28), (22, 29), (25, 29)]),
        ("#ff8fa3", [(23, 30), (24, 30)]),
    ])


def corgi():
    LA, LAs, LAl, BR, BRs, RO = "#e8963d", "#b86a1c", "#f7b46a", "#ffffff", "#dfe3ea", "#f0a487"
    orelha = "M8 24 Q5 12 8 3 Q18 7 21 15 Z"
    interna = "M10 19 Q8.5 12 10 7 Q16 10 18 15 Z"
    return montar([
        (sb(f'<path d="{orelha}"/>', LA, LAs, id_="o1") + f'<path d="{interna}" fill="{RO}"/>', [LA, LAs, RO], True),
        (sb(f'<path d="{espelho_x(orelha)}"/>', LA, LAs, id_="o2")
         + f'<path d="{espelho_x(interna)}" fill="{RO}"/>', [LA, LAs, RO], True),
        (sb('<ellipse cx="24" cy="39" rx="12" ry="7.5"/>', LA, LAs, id_="b")
         + f'<ellipse cx="24" cy="40" rx="6" ry="6.5" fill="{BR}"/>', [LA, LAs, BR], True),
        (f'<ellipse cx="18" cy="45.5" rx="3" ry="2" fill="{BR}"/><ellipse cx="30" cy="45.5" rx="3" ry="2" fill="{BR}"/>',
         [BR], True),
        (sb('<ellipse cx="24" cy="24" rx="15" ry="11"/>', LA, LAs,
            f'<ellipse cx="16" cy="17" rx="4.5" ry="1.8" fill="{LAl}"/>'
            f'<path d="M21.5 13 H26.5 L28 22 Q32 26 31 32 Q24 37 17 32 Q16 26 20 22 Z" fill="{BR}"/>', id_="h"),
         [LA, LAs, LAl, BR], True),
    ], "#4a2608", detalhes=[
        *olhos(16, 31, 22, "#2b1a0e"),
        ("#1b1b1b", [(22, 27), (23, 27), (24, 27), (25, 27), (23, 28), (24, 28)]),
        ("#2b1a0e", [(23, 29), (24, 29), (21, 30), (22, 31), (25, 31), (26, 30)]),
        ("#ff8fa3", [(23, 31), (24, 31), (23, 32), (24, 32)]),
        bochechas(12, 34, 27, "#f6a38a"),
    ])


def salsicha():
    MA, MAs, MAl, OR = "#8b5a2b", "#6b4220", "#a8743e", "#5a3518"
    return montar([
        (f'<path d="M7 34 Q2 30 3 24 L5 24 Q5 29 9 32 Z" fill="{MA}"/>', [MA], True),
        (sb('<ellipse cx="21" cy="37" rx="16" ry="6.5"/>', MA, MAs, id_="b"), [MA, MAs], True),
        (f'<rect x="8" y="40" width="4" height="6" rx="1" fill="{MAs}"/><rect x="29" y="40" width="4" height="6" rx="1" fill="{MAs}"/>',
         [MAs], True),
        (f'<rect x="12" y="40" width="4" height="7" rx="1" fill="{MA}"/><rect x="33" y="40" width="4" height="7" rx="1" fill="{MA}"/>',
         [MA], True),
        (sb('<path d="M28 34 Q24 26 28 19 Q34 14 40 18 Q44 21 46 26 Q47 30 42 31 Q38 32 36 34 Z"/>', MA, MAs,
            f'<ellipse cx="31" cy="18.5" rx="3.5" ry="1.4" fill="{MAl}"/>', id_="h"), [MA, MAs, MAl], True),
        (f'<path d="M28 21 Q24 24 25 33 Q27 36 30 33 Q31 27 31 22 Z" fill="{OR}"/>', [OR], True),
    ], "#2e1a0a", detalhes=[
        ("#1b1b1b", [(35, 21), (36, 21), (35, 22), (36, 22), (35, 23), (36, 23)]),
        ("#ffffff", [(35, 21)]),
        ("#1b1b1b", [(45, 25), (46, 25), (45, 26), (46, 26)]),
        ("#2e1a0a", [(41, 29), (42, 29), (43, 29)]),
        ("#ff8fa3", [(42, 30), (43, 30)]),
    ])


# ---- outros pets ------------------------------------------------------------------

def passarinho():
    AZ, AZs, AZl, AS, BR, LJ = "#3b82f6", "#1d4ea8", "#7fb2ff", "#2a5fc0", "#ffffff", "#ffa630"
    return montar([
        (f'<path d="M12 36 L2 40 L4 34 L1 30 L12 31 Z" fill="{AS}"/>', [AS], True),
        (f'<path d="M20 44 L20 47 M28 44 L28 47" stroke="{LJ}" stroke-width="2"/>'
         f'<rect x="17" y="46" width="5" height="2" fill="{LJ}"/><rect x="26" y="46" width="5" height="2" fill="{LJ}"/>',
         [LJ], False),
        (sb('<ellipse cx="24" cy="31" rx="14" ry="13"/>', AZ, AZs,
            f'<ellipse cx="18" cy="22" rx="5" ry="2" fill="{AZl}"/>'
            f'<ellipse cx="26" cy="37" rx="8" ry="6.5" fill="{BR}"/>', id_="c"), [AZ, AZs, AZl, BR], True),
        (f'<path d="M23 16 Q22 10 26 8 Q25 12 28 14 Z" fill="{AZ}"/>', [AZ], True),
        (sb('<path d="M10 30 Q14 26 20 30 Q20 38 13 40 Q9 36 10 30 Z"/>', AS, "#1d4ea8", id_="a"), [AS, "#1d4ea8"], True),
        (f'<path d="M37 24 L44 27 L37 30 Z" fill="{LJ}"/>', [LJ, "#d9821a"], True),
    ], "#13306b", detalhes=[
        ("#1b1b1b", [(31, 22), (32, 22), (30, 23), (31, 23), (32, 23), (31, 24), (32, 24)]),
        ("#ffffff", [(31, 22)]),
        ("#ff9fb5", [(33, 27), (34, 27)]),
    ])


def slime():
    VE, VEs, VEl = "#5ac54f", "#2f8f3a", "#a6e89a"
    return montar([
        (sb('<path d="M4 47 C3 36 10 23 21 21 Q23 18 24 14 Q25 18 27 21 C38 23 45 36 44 47 Z"/>',
            VE, VEs, f'<ellipse cx="14" cy="30" rx="2.2" ry="3.5" fill="{VEl}"/><circle cx="18" cy="26" r="1.4" fill="{VEl}"/>',
            id_="s"), [VE, VEs, VEl], True),
    ], "#1e5a24", detalhes=[
        *olhos(18, 30, 32, "#1b1b1b", alto=5),
        ("#1e5a24", [(22, 39), (23, 40), (24, 40), (25, 39)]),
        bochechas(13, 34, 37, "#8fe08a"),
    ])


def pintinho():
    AM, AMs, AMl, LJ = "#ffd23f", "#e0a800", "#fff1a6", "#ff8c2e"
    return montar([
        (f'<path d="M18 45 V47 M30 45 V47" stroke="{LJ}" stroke-width="2"/>'
         f'<rect x="15" y="46" width="6" height="2" fill="{LJ}"/><rect x="27" y="46" width="6" height="2" fill="{LJ}"/>',
         [LJ], False),
        (f'<path d="M21 15 L22 8 L24 13 L26 7 L27 15 Z" fill="{AM}"/>', [AM], True),
        (sb('<ellipse cx="24" cy="31" rx="14" ry="14"/>', AM, AMs,
            f'<ellipse cx="17" cy="22" rx="4.5" ry="2" fill="{AMl}"/>', id_="c"), [AM, AMs, AMl], True),
        (sb('<ellipse cx="11" cy="33" rx="3.5" ry="5.5"/><ellipse cx="37" cy="33" rx="3.5" ry="5.5"/>',
            AM, AMs, id_="a"), [AM, AMs], True),
        (f'<path d="M20 30 L28 30 L24 35 Z" fill="{LJ}"/>', [LJ, "#d9661a"], True),
    ], "#6b4a00", detalhes=[
        *olhos(18, 30, 25),
        bochechas(13, 33, 31, "#ffa98a"),
    ])


def fantasma():
    BR, BRs, BRl = "#f4f1ff", "#c9c0ef", "#ffffff"
    corpo = "M10 46 L10 24 Q10 7 24 7 Q38 7 38 24 L38 46 L34 42 L30 46 L26 42 L22 46 L18 42 L14 46 Z"
    return montar([
        (sb(f'<path d="{corpo}"/>', BR, BRs, f'<ellipse cx="17" cy="14" rx="4" ry="2" fill="{BRl}"/>', id_="c"),
         [BR, BRs, BRl], True),
        (sb('<ellipse cx="8" cy="30" rx="3" ry="4"/><ellipse cx="40" cy="30" rx="3" ry="4"/>', BR, BRs, id_="m"),
         [BR, BRs], True),
    ], "#4b3f8a", detalhes=[
        *olhos(19, 29, 20, "#2a2350", alto=5),
        ("#2a2350", [(23, 28), (24, 28), (22, 29), (25, 29), (23, 30), (24, 30)]),
        ("#ff8fb8", [(23, 29), (24, 29)]),
        bochechas(15, 32, 26, "#ffb3cf"),
    ])


def gato():
    LA, LAs, LAl, BR, RO = "#f4a259", "#d9822b", "#ffc58a", "#fff4e6", "#f0a487"
    orelha = "M10 22 L8 6 L20 14 Z"
    interna = "M11.5 18 L10.5 10 L17 14.5 Z"
    return montar([
        (sb('<path d="M34 44 Q46 42 44 30 Q43 25 40 27 Q41 37 32 40 Z"/>', LA, LAs, id_="r"), [LA, LAs], True),
        (sb(f'<path d="{orelha}"/>', LA, LAs, id_="o1") + f'<path d="{interna}" fill="{RO}"/>', [LA, LAs, RO], True),
        (sb(f'<path d="{espelho_x(orelha)}"/>', LA, LAs, id_="o2")
         + f'<path d="{espelho_x(interna)}" fill="{RO}"/>', [LA, LAs, RO], True),
        (sb('<ellipse cx="24" cy="39" rx="11" ry="7.5"/>', LA, LAs, id_="b")
         + f'<ellipse cx="24" cy="40" rx="5" ry="5.5" fill="{BR}"/>', [LA, LAs, BR], True),
        (f'<ellipse cx="19" cy="45.5" rx="3" ry="2" fill="{BR}"/><ellipse cx="29" cy="45.5" rx="3" ry="2" fill="{BR}"/>',
         [BR], True),
        (sb('<ellipse cx="24" cy="24" rx="15" ry="11"/>', LA, LAs,
            f'<ellipse cx="16" cy="17" rx="4" ry="1.6" fill="{LAl}"/>'
            f'<ellipse cx="24" cy="29.5" rx="6.5" ry="4.3" fill="{BR}"/>', id_="h"), [LA, LAs, LAl, BR], True),
    ], "#5a2e0e", detalhes=[
        (LAs, [(23, 14), (23, 15), (23, 16), (20, 15), (20, 16), (26, 15), (26, 16)]),
        *olhos(17, 31, 21, "#2b1a0e"),
        ("#ff7b8f", [(23, 27), (24, 27), (23, 28), (24, 28)]),
        ("#5a2e0e", [(22, 30), (23, 29), (24, 29), (25, 30)]),
        ("#c7a58a", [(10, 27), (11, 27), (12, 27), (10, 29), (11, 29), (36, 27), (37, 27), (38, 27), (36, 29), (37, 29)]),
    ])


def robo():
    CI, CIs, CIl, TE, CY, VM = "#b8c2cc", "#7f8b98", "#e2e8ef", "#1f2a37", "#4cc9f0", "#ff595e"
    return montar([
        (f'<rect x="23" y="4" width="2" height="7" fill="{CIs}"/>', [CIs], True),
        (f'<circle cx="24" cy="4" r="2.5" fill="{VM}"/>', [VM], True),
        (sb('<rect x="13" y="36" width="5" height="10" rx="1"/><rect x="30" y="36" width="5" height="10" rx="1"/>',
            CI, CIs, id_="p"), [CI, CIs], True),
        (sb('<rect x="6" y="31" width="5" height="10" rx="2"/><rect x="37" y="31" width="5" height="10" rx="2"/>',
            CI, CIs, id_="m"), [CI, CIs], True),
        (sb('<rect x="12" y="29" width="24" height="12" rx="3"/>', CI, CIs, id_="b")
         + f'<rect x="18" y="32" width="12" height="5" rx="1" fill="{TE}"/>'
         + f'<rect x="20" y="34" width="2" height="1" fill="{CY}"/><rect x="23" y="34" width="2" height="1" fill="{VM}"/>'
           f'<rect x="26" y="34" width="2" height="1" fill="#ffd23f"/>', [CI, CIs, TE, CY, VM, "#ffd23f"], True),
        (sb('<rect x="9" y="10" width="30" height="19" rx="5"/>', CI, CIs,
            f'<rect x="12" y="12" width="8" height="2" fill="{CIl}"/>', id_="h")
         + f'<rect x="13" y="14" width="22" height="11" rx="3" fill="{TE}"/>', [CI, CIs, CIl, TE], True),
    ], "#2b3440", detalhes=[
        (CY, [(17, 17), (18, 17), (19, 17), (17, 18), (18, 18), (19, 18), (17, 19), (18, 19), (19, 19),
              (28, 17), (29, 17), (30, 17), (28, 18), (29, 18), (30, 18), (28, 19), (29, 19), (30, 19)]),
        ("#ffffff", [(17, 17), (28, 17)]),
        (CY, [(21, 22), (22, 23), (23, 23), (24, 23), (25, 23), (26, 22)]),
    ])


def dragao():
    VE, VEs, VEl, BA, BAs, AS, CH = "#4caf50", "#2e7d32", "#8bdc8e", "#ffe08a", "#e8b84a", "#7e57c2", "#fff4c2"
    return montar([
        (sb('<path d="M14 30 Q2 22 3 12 Q9 18 16 18 Z"/>', AS, "#5a3a9a", id_="a1"), [AS, "#5a3a9a"], True),
        (sb('<path d="M34 30 Q46 22 45 12 Q39 18 32 18 Z"/>', AS, "#5a3a9a", id_="a2"), [AS, "#5a3a9a"], True),
        (sb('<path d="M33 42 Q44 44 46 34 L43 33 Q41 39 33 38 Z"/>', VE, VEs, id_="r"), [VE, VEs], True),
        (sb('<ellipse cx="24" cy="38" rx="11" ry="8.5"/>', VE, VEs, id_="b")
         + f'<ellipse cx="24" cy="39" rx="6" ry="6.5" fill="{BA}"/>'
         + f'<path d="M19 37 H29 M19 41 H29" stroke="{BAs}" stroke-width="1"/>', [VE, VEs, BA, BAs], True),
        (sb('<ellipse cx="18" cy="45.5" rx="3.5" ry="2"/><ellipse cx="30" cy="45.5" rx="3.5" ry="2"/>', VE, VEs, id_="p"),
         [VE, VEs], True),
        (f'<path d="M15 14 L13 5 L19 11 Z M33 14 L35 5 L29 11 Z" fill="{CH}"/>', [CH, "#e8c86a"], True),
        (sb('<ellipse cx="24" cy="22" rx="13" ry="10"/>', VE, VEs,
            f'<ellipse cx="17" cy="15.5" rx="4" ry="1.6" fill="{VEl}"/>', id_="h")
         + f'<ellipse cx="24" cy="27" rx="7" ry="4" fill="{VEl}"/>', [VE, VEs, VEl], True),
    ], "#1b4d1e", detalhes=[
        *olhos(18, 30, 19),
        ("#1b4d1e", [(22, 26), (25, 26)]),
        ("#1b4d1e", [(21, 29), (22, 30), (23, 30), (24, 30), (25, 30), (26, 29)]),
        ("#ffffff", [(23, 31)]),
    ])


def ovo():
    BR, BRs, BRl, MA, MAs = "#fbfaf5", "#d6d9dc", "#ffffff", "#3fb8af", "#2b8f88"
    return montar([
        (sb('<path d="M24 6 C35 6 40 24 40 32 C40 42 33 47 24 47 C15 47 8 42 8 32 C8 24 13 6 24 6 Z"/>', BR, BRs,
            f'<ellipse cx="17" cy="18" rx="2.5" ry="5" fill="{BRl}"/>'
            f'<ellipse cx="27" cy="16" rx="3" ry="2.5" fill="{MA}"/><ellipse cx="17" cy="32" rx="3.5" ry="3" fill="{MA}"/>'
            f'<ellipse cx="31" cy="30" rx="2.5" ry="2" fill="{MA}"/><ellipse cx="26" cy="41" rx="3.5" ry="2.5" fill="{MA}"/>'
            f'<ellipse cx="36" cy="38" rx="2" ry="3" fill="{MAs}"/>', id_="o"), [BR, BRs, BRl, MA, MAs], True),
    ], "#4a5560")


PETS = {"pinscher": pinscher, "corgi": corgi, "salsicha": salsicha, "passarinho": passarinho,
        "slime": slime, "pintinho": pintinho, "fantasma": fantasma, "gato": gato, "robo": robo,
        "dragao": dragao, "ovo": ovo}


# ---- acessórios: (desenho, largura, altura, âncora x, âncora y) --------------------
# A âncora é o pixel do acessório que encosta no ponto do pet (topo, olhos ou pescoço).

def laco():
    RO, ROs = "#ff6fa8", "#d6437f"
    g = montar([
        (sb('<path d="M7 5 L1 1 L1 9 Z"/><path d="M7 5 L13 1 L13 9 Z"/>', RO, ROs, id_="l"), [RO, ROs], True),
        (f'<rect x="5" y="3" width="4" height="4" rx="1" fill="{ROs}"/>', [ROs], True),
    ], "#6b1d3d", 15, 11)
    return g, 15, 11, 7, 9


def bone():
    VM, VMs, BR = "#e8402a", "#a82a18", "#ffffff"
    g = montar([
        (f'<rect x="12" y="9" width="12" height="2" rx="1" fill="{VMs}"/>', [VMs], True),
        (sb('<path d="M2 10 Q2 2 11 2 Q20 2 20 10 Z"/>', VM, VMs,
            f'<rect x="9" y="4" width="4" height="3" fill="{BR}"/>', id_="b"), [VM, VMs, BR], True),
    ], "#4a120a", 26, 13)
    return g, 26, 13, 11, 10


def oculos():
    PR, LE = "#1b1b1b", "#3a4a6b"
    g = montar([
        (f'<rect x="1" y="1" width="10" height="7" rx="2" fill="{LE}"/><rect x="15" y="1" width="10" height="7" rx="2" fill="{LE}"/>'
         f'<rect x="10" y="2" width="6" height="2" fill="{PR}"/>', [LE, PR], True),
    ], "#111111", 26, 9, detalhes=[("#9fb3d9", [(3, 3), (4, 3), (3, 4), (17, 3), (18, 3), (17, 4)])])
    return g, 26, 9, 13, 4


def cachecol():
    VM, VMs, BR = "#ff595e", "#c23a3f", "#ffffff"
    listras = "".join(f'<rect x="{x}" y="1" width="2" height="5" fill="{BR}"/>' for x in (5, 11, 17, 23))
    g = montar([
        (sb('<rect x="1" y="1" width="28" height="5" rx="2"/>', VM, VMs, id_="c") + listras, [VM, VMs, BR], True),
        (sb('<rect x="19" y="4" width="5" height="9" rx="1"/>', VM, VMs, id_="p")
         + f'<rect x="19" y="8" width="5" height="2" fill="{BR}"/>', [VM, VMs, BR], True),
    ], "#5a1418", 30, 15)
    return g, 30, 15, 15, 2


def mago():
    RX, RXs, AM = "#5b4bc4", "#3d2f9e", "#ffd166"
    g = montar([
        (sb('<path d="M13 1 Q16 10 20 15 L6 15 Q10 9 13 1 Z"/>', RX, RXs, id_="m"), [RX, RXs], True),
        (sb('<ellipse cx="13" cy="16" rx="12" ry="2.5"/>', RX, RXs, id_="a"), [RX, RXs], True),
    ], "#1f1660", 27, 20, detalhes=[(AM, [(12, 7), (11, 8), (12, 8), (13, 8), (12, 9), (15, 12), (10, 13)])])
    return g, 27, 20, 13, 17


def coroa():
    OU, OUs, VM, CY = "#f5b81b", "#b8860b", "#ff595e", "#4cc9f0"
    g = montar([
        (sb('<path d="M1 11 L1 2 L5 6 L9 1 L13 6 L17 2 L17 11 Z"/>', OU, OUs, id_="c"), [OU, OUs], True),
    ], "#5a3d00", 19, 13, detalhes=[(VM, [(8, 8), (9, 8)]), (CY, [(4, 8), (13, 8)]), ("#fff3b0", [(3, 4), (9, 3)])])
    return g, 19, 13, 9, 12


ACESSORIOS = {"laco": laco, "bone": bone, "oculos": oculos, "cachecol": cachecol, "mago": mago, "coroa": coroa}
