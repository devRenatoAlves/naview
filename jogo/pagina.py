"""Parte do jogo que não depende da tela: o catálogo mandado à página e as ações que ela pede.

Usada pelas duas telas do jogo: tela.py (WebKitGTK) e tela_qt.py (QWebEngine).
"""
import re
from functools import lru_cache
from pathlib import Path

import temas

from . import catalogo as cat
from .progresso import ErroJogo

PAGINA = Path(__file__).resolve().parent.parent / "web" / "jogo.html"
NOMES_CURTOS_BAU = {"madeira": "Madeira", "prata": "Prata", "ouro": "Ouro", "magico": "Mágico",
                    "lendario": "Lendário"}


@lru_cache(maxsize=None)
def caixa_do_pet(especie):
    """[x, y, largura, altura] do desenho do pet dentro da imagem dele (pixels do SVG, y já contado a partir
    do alto do viewBox). A página recorta por aqui para o pet encher o espaço das cartas e dos botões."""
    texto = (cat.ARTE_PETS / f"{especie}.svg").read_text()
    topo = -int(re.search(r'viewBox="0 (-?\d+) ', texto).group(1))  # linhas a mais em cima
    retas = [(int(x), int(y) + topo, int(w)) for x, y, w in
             re.findall(r'<rect x="(-?\d+)" y="(-?\d+)" width="(\d+)"', texto)]
    x0, x1 = min(r[0] for r in retas), max(r[0] + r[2] for r in retas)
    y0, y1 = min(r[1] for r in retas), max(r[1] for r in retas) + 1
    return [x0, y0, x1 - x0, y1 - y0]


def catalogo_para_web():
    return {
        "cartas": cat.CARTAS,
        "cartas_por_id": cat.CARTAS_POR_ID,
        "raridades": cat.RARIDADES,
        "ordem_raridade": cat.ORDEM_RARIDADE,
        "tipos": cat.TIPOS,
        "baus": {t: {"nome": b["nome"], "curto": NOMES_CURTOS_BAU[t], "minutos": b["minutos"]}
                 for t, b in cat.BAUS.items()},
        "temas": {chave: {"nome": t["nome"], "previa": t["previa"], "fonte": t.get("fonte"),
                          "texto": temas.cor_texto(t["previa"][0]) or "#ffffff"}
                  for chave, t in temas.TEMAS.items()},
        "pet": {"lado": cat.PET_LADO, "acima": cat.PET_ACIMA, "expressoes": cat.PETS_COM_EXPRESSAO,
                "extra": cat.ALTURA_EXTRA, "acima_pet": cat.ACIMA_PET, "escala": cat.ESCALA_PAGINA,
                "quadros": cat.QUADROS,
                "caixas": {c["alvo"]: caixa_do_pet(c["alvo"]) for c in cat.CARTAS if c["tipo"] == "pet"}, "quadro_ms": cat.QUADRO_MS},
        "encaixes": {e: {a: cat.encaixe_acessorio(e, a) for a in cat.ENCAIXE_ACESSORIO}
                     for e in cat.ENCAIXE_PET},
        "nivel_max": cat.NIVEL_MAX,
        "copias_por_nivel": cat.COPIAS_POR_NIVEL,
        "moedas_por_nivel": cat.MOEDAS_POR_NIVEL,
        "atendimentos_por_bau": cat.ATENDIMENTOS_POR_BAU,
        "atendimento_minimo_s": cat.ATENDIMENTO_MINIMO_S,
    }


def executar_acao(p, acao, dados, estado, ao_mudar, ao_fechar):
    """Faz o que a página pediu. estado(): estado mandado à página; ao_mudar(acao, resultado) avisa o
    app; ErroJogo vira mensagem na página."""
    if acao == "estado":
        return estado()
    if acao == "fechar":
        ao_fechar()
        return None
    if acao == "equipar":
        carta = cat.CARTAS_POR_ID.get(dados["id"])
        if carta and carta["tipo"] == "tema":
            if not p.possui(carta["id"]):
                raise ErroJogo("Você ainda não tem esse tema.")
            resultado = None
        else:
            resultado = p.equipar(dados["id"])
        ao_mudar("equipar", carta)
        return resultado
    acoes = {
        "destravar_bau": lambda: p.destravar_bau(dados["espaco"]),
        "abrir_bau": lambda: p.abrir_bau(dados["espaco"], dados.get("pagar", False)),
        "abrir_bau_gratis": p.abrir_bau_gratis,
        "resgatar_diario": p.resgatar_diario,
        "melhorar_carta": lambda: p.melhorar_carta(dados["id"]),
        "comprar_oferta": lambda: p.comprar_oferta(dados["indice"]),
        "comprar_petiscos": lambda: p.comprar_petiscos(dados.get("quantidade", 1)),
        "pet_acao": lambda: p.pet_acao(dados["acao"]),
        "pet_chocar": p.pet_chocar,
    }
    if acao not in acoes:
        raise ErroJogo("Ação desconhecida.")
    resultado = acoes[acao]()
    ao_mudar(acao, resultado)
    return resultado
