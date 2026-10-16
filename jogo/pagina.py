"""Parte do jogo que não depende da tela: o catálogo mandado à página e as ações que ela pede.

Usada pelas duas telas do jogo: tela.py (WebKitGTK) e tela_qt.py (QWebEngine).
"""
from pathlib import Path

import temas

from . import catalogo as cat
from .progresso import ErroJogo

PAGINA = Path(__file__).resolve().parent.parent / "web" / "jogo.html"
NOMES_CURTOS_BAU = {"madeira": "Madeira", "prata": "Prata", "ouro": "Ouro", "magico": "Mágico",
                    "lendario": "Lendário"}


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
        "pet": {"lado": cat.PET_LADO, "acima": cat.PET_ACIMA},
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
        "pet_renomear": lambda: p.pet_renomear(dados.get("nome")),
    }
    if acao not in acoes:
        raise ErroJogo("Ação desconhecida.")
    resultado = acoes[acao]()
    ao_mudar(acao, resultado)
    return resultado
