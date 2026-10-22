"""Temas do app: cores, fonte, frases da tela inicial, desenhos e o CSS de tudo isso.

Cada tema é só dados. gerar_css() junta o CSS base (estrutura comum a todos) com os
valores do tema, os ajustes do usuário e o CSS extra que cada tema quiser.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from string import Template

import plataforma

PASTA = Path(__file__).resolve().parent
ARTE = PASTA / "arte"
ARQUIVO = plataforma.CONFIG / "config.json"
CACHE = plataforma.CACHE
MAX_FUNDO = (1920, 1080)

AJUSTES = ("destaque", "fundo", "lateral", "barra")

# Só o KWin (KDE) desfoca o que fica atrás da janela. Nos outros ambientes (GNOME, XFCE etc.)
# o vidro fica sem desfoque, e o fundo precisa ser mais escuro para o texto continuar legível.
TEM_DESFOQUE = "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()


def arte(nome):
    return (ARTE / nome).as_uri()


# ---- definição dos temas ----------------------------------------------------
#
# Cores aceitam qualquer valor de CSS do GTK3 (#hex, alpha(), shade(), @theme_*).
# "decor": desenhos da tela inicial. tipo "imagem" (padrão), "faixa" (repete na horizontal,
# encostada embaixo) ou "texto". anim: flutuar, flutuar-lento, balancar, pular, piscar,
# piscar-lento, pulsar, navegar.

PADRAO_AVATARES = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899"]

TEMAS = {
    "padrao": {
        "nome": "Padrão", "descricao": "Segue o tema do sistema",
        "cores": {
            "fundo": "@theme_bg_color", "lateral": "shade(@theme_bg_color, 0.94)",
            "barra": "shade(@theme_bg_color, 0.94)", "superficie": "@theme_base_color",
            "destaque": "@theme_selected_bg_color", "texto": "@theme_fg_color",
            "texto_lateral": "@theme_fg_color", "texto_barra": "@theme_fg_color",
            "texto_destaque": "@theme_selected_fg_color", "aba_ativa": "@theme_bg_color",
        },
        "previa": ("#3a3d44", "#2c2e33", "#4f8cff"),
    },
    "grafite": {
        "nome": "Grafite", "descricao": "Escuro, sóbrio e sem distrações",
        "cores": {
            "fundo": "#1f2125", "lateral": "#18191c", "barra": "#18191c", "superficie": "#2a2c31",
            "destaque": "#7c8cff", "texto": "#e8e9ed", "texto_lateral": "#e8e9ed",
            "texto_barra": "#e8e9ed", "texto_destaque": "#ffffff", "aba_ativa": "#1f2125",
        },
        "previa": ("#1f2125", "#18191c", "#7c8cff"),
    },
    "claro": {
        "nome": "Claro", "descricao": "Limpo e luminoso",
        "cores": {
            "fundo": "#f6f7f9", "lateral": "#eceef2", "barra": "#ffffff", "superficie": "#ffffff",
            "destaque": "#2563eb", "texto": "#1f2937", "texto_lateral": "#1f2937",
            "texto_barra": "#1f2937", "texto_destaque": "#ffffff", "aba_ativa": "#f6f7f9",
        },
        "previa": ("#f6f7f9", "#eceef2", "#2563eb"),
    },
    "oceano": {
        "nome": "Oceano", "descricao": "Azul profundo",
        "cores": {
            "fundo": "#0f2537", "lateral": "#0b1c2a", "barra": "#0b1c2a", "superficie": "#15324a",
            "destaque": "#1fa2ff", "texto": "#e6f1fa", "texto_lateral": "#e6f1fa",
            "texto_barra": "#e6f1fa", "texto_destaque": "#ffffff", "aba_ativa": "#0f2537",
        },
        "inicio": "background-image: linear-gradient(160deg, alpha(#1fa2ff, 0.16), transparent 45%,"
                  " transparent 65%, alpha(#14b8a6, 0.12));",
        "previa": ("#0f2537", "#0b1c2a", "#1fa2ff"),
    },
    "vidro": {
        "nome": "Vidro líquido", "descricao": "Transparente com desfoque, estilo Apple",
        "vidro": True,
        "cores": {
            "fundo": "alpha(#0b1020, {tinta})", "lateral": "alpha(#ffffff, {painel})",
            "barra": "alpha(#ffffff, {barra})", "superficie": "alpha(#ffffff, {campo})",
            "destaque": "#8be9ff", "texto": "#ffffff", "texto_lateral": "#ffffff",
            "texto_barra": "#ffffff", "texto_destaque": "#04202b", "aba_ativa": "alpha(#ffffff, {campo})",
        },
        "avatares": ["alpha(#ff6b8b, 0.75)", "alpha(#ffb347, 0.75)", "alpha(#4ade80, 0.75)",
                     "alpha(#60a5fa, 0.75)", "alpha(#c084fc, 0.75)", "alpha(#f472b6, 0.75)"],
        "raio": "18px", "raio_peq": "12px",
        "css": """
.janela-principal { background-color: transparent; }
.janela-principal .raiz { background-color: $fundo; }
.janela-principal .sidebar {
  margin: 0 0 10px 10px; border-radius: 20px; border: 1px solid alpha(#ffffff, 0.22);
  background-image: linear-gradient(160deg, alpha(#ffffff, 0.16), alpha(#ffffff, 0.03) 45%, alpha(#ffffff, 0.08));
  box-shadow: inset 0 1px alpha(#ffffff, 0.45), inset 0 -1px alpha(#000000, 0.18), 0 2px 6px alpha(#000000, 0.22);
}
.janela-principal .inicio { background-color: transparent; }
.janela-principal .cartao-conectar {
  border: 1px solid alpha(#ffffff, 0.28);
  background-image: linear-gradient(160deg, alpha(#ffffff, 0.22), alpha(#ffffff, 0.04) 50%, alpha(#ffffff, 0.10));
  box-shadow: inset 0 1px alpha(#ffffff, 0.6), inset 0 -1px alpha(#000000, 0.2), 0 3px 8px alpha(#000000, 0.25);
}
.janela-principal label { text-shadow: 0 1px 2px alpha(#000000, 0.35); }
.janela-principal entry { border: 1px solid alpha(#ffffff, 0.25); box-shadow: inset 0 1px alpha(#ffffff, 0.25); }
.janela-principal notebook.abas > header { background-color: transparent; box-shadow: none; }
.janela-principal notebook.abas > header > tabs > tab:checked {
  box-shadow: inset 0 1px alpha(#ffffff, 0.5); border: 1px solid alpha(#ffffff, 0.25);
}
""",
        "previa": ("#6f86b8", "#a9b8d8", "#8be9ff"),
    },
    "pixel": {
        "nome": "Aventura Pixel", "descricao": "Monstrinhos, grama e fonte de videogame",
        "fonte": "Press Start 2P", "tamanho": "7.5pt",
        "cores": {
            "fundo": "#8fd3ff", "lateral": "#fff8e1", "barra": "#e8402a", "superficie": "#ffffff",
            "destaque": "#e8402a", "texto": "#1b1b1b", "texto_lateral": "#1b1b1b",
            "texto_barra": "#ffffff", "texto_destaque": "#ffffff", "aba_ativa": "#fff8e1",
            "texto_aba_ativa": "#1b1b1b",
        },
        "avatares": ["#e8402a", "#3b82f6", "#5ac54f", "#ffb02e", "#9b6bd6", "#ff6fa8"],
        "raio": "0px", "raio_peq": "0px",
        "frases": ("Nenhum cliente por perto...", "Digite um ID para começar a aventura!"),
        "inicio": "background-image: linear-gradient(to bottom, #6ec3ff, #b9e6ff 70%);",
        "css": """
.janela-principal .sidebar { border-right: 4px solid #1b1b1b; }
.janela-principal headerbar { border-bottom: 4px solid #1b1b1b; }
.janela-principal entry { border: 3px solid #1b1b1b; box-shadow: inset 2px 2px #d7d7d7; }
.janela-principal .avatar { border: 2px solid #1b1b1b; }
.janela-principal .cartao-conectar {
  border: 4px solid #1b1b1b; box-shadow: inset 0 0 0 3px #ffffff, inset 0 0 0 6px #6b6b6b, 6px 6px 0 alpha(#1b1b1b, 0.35);
}
.janela-principal button.conectar { border: 3px solid #1b1b1b; box-shadow: inset -3px -3px #a82a18; }
.janela-principal button.conectar:active { box-shadow: inset 3px 3px #a82a18; }
.janela-principal notebook.abas > header { border-bottom: 4px solid #1b1b1b; }
.janela-principal notebook.abas > header > tabs > tab:checked { border: 3px solid #1b1b1b; border-bottom: none; }
.janela-principal .sidebar row:selected { background-color: #ffd23f; }
.janela-principal .contato-id { margin-top: 4px; }
.janela-principal .titulo-inicio { font-size: 1.5em; }
""",
        "decor": [
            {"arte": "pixel/nuvem.svg", "w": 160, "h": 56, "halign": "start", "valign": "start",
             "margem": (70, 0, 0, 70), "anim": "flutuar-lento"},
            {"arte": "pixel/nuvem.svg", "w": 120, "h": 42, "halign": "end", "valign": "start",
             "margem": (150, 180, 0, 0), "anim": "flutuar"},
            {"arte": "pixel/bola.svg", "w": 80, "h": 80, "halign": "end", "valign": "start",
             "margem": (40, 50, 0, 0), "anim": "balancar"},
            {"tipo": "faixa", "arte": "pixel/grama.svg", "altura": 70, "tile": (64, 40)},
            {"arte": "pixel/slime.svg", "w": 96, "h": 78, "halign": "start", "valign": "end",
             "margem": (0, 0, 52, 90), "anim": "pular"},
            {"arte": "pixel/pintinho.svg", "w": 80, "h": 80, "halign": "end", "valign": "end",
             "margem": (0, 250, 52, 0), "anim": "pular-lento"},
            {"arte": "pixel/fantasma.svg", "w": 84, "h": 74, "halign": "end", "valign": "end",
             "margem": (0, 90, 120, 0), "anim": "flutuar"},
        ],
        "previa": ("#8fd3ff", "#fff8e1", "#e8402a"),
    },
    "hq": {
        "nome": "Heróis HQ", "descricao": "Quadrinhos: cores fortes, pontos e explosões",
        "fonte": "Bangers", "tamanho": "12pt",
        "cores": {
            "fundo": "#ffd600", "lateral": "#ffffff", "barra": "#e53935", "superficie": "#ffffff",
            "destaque": "#1e40af", "texto": "#111111", "texto_lateral": "#111111",
            "texto_barra": "#ffffff", "texto_destaque": "#ffffff", "aba_ativa": "#ffffff",
            "texto_aba_ativa": "#111111",
        },
        "avatares": ["#e53935", "#1e40af", "#16a34a", "#f59e0b", "#7c3aed", "#db2777"],
        "raio": "4px", "raio_peq": "3px",
        "frases": ("Nenhuma missão em andamento!", "Qual cliente vamos salvar hoje?"),
        "inicio": f'background-image: url("{arte("hq/pontos.svg")}"),'
                  " radial-gradient(circle at 50% 45%, #fff59d, #ffd600 60%);"
                  " background-size: 14px 14px, cover; background-repeat: repeat, no-repeat;",
        "css": """
.janela-principal .sidebar { border-right: 4px solid #111111; }
.janela-principal headerbar { border-bottom: 4px solid #111111; }
.janela-principal entry { border: 3px solid #111111; }
.janela-principal .avatar { border: 2px solid #111111; }
.janela-principal .cartao-conectar { border: 4px solid #111111; box-shadow: 10px 10px 0 #111111; }
.janela-principal button.conectar { border: 3px solid #111111; box-shadow: 4px 4px 0 #111111; }
.janela-principal button.conectar:active { box-shadow: 1px 1px 0 #111111; }
.janela-principal notebook.abas > header { border-bottom: 4px solid #111111; }
.janela-principal notebook.abas > header > tabs > tab:checked { border: 3px solid #111111; border-bottom: none; }
.janela-principal .sidebar row:selected { background-color: #ffd600; }
.janela-principal .titulo-inicio { font-size: 2.4em; color: #e53935; text-shadow: 2px 2px 0 #111111; }
.decor-texto { font-size: 3.2em; color: #ffffff; text-shadow: 3px 3px 0 #111111; }
""",
        "decor": [
            {"tipo": "faixa", "arte": "hq/cidade.svg", "altura": 130, "tile": (800, 130)},
            {"arte": "hq/explosao.svg", "w": 190, "h": 190, "halign": "start", "valign": "start",
             "margem": (30, 0, 0, 40), "anim": "pulsar", "texto": "POW!"},
            {"arte": "hq/explosao_azul.svg", "w": 150, "h": 150, "halign": "end", "valign": "end",
             "margem": (0, 60, 150, 0), "anim": "pulsar-lento", "texto": "ZAP!"},
            {"arte": "hq/emblema.svg", "w": 100, "h": 110, "halign": "end", "valign": "start",
             "margem": (40, 70, 0, 0), "anim": "flutuar"},
        ],
        "previa": ("#ffd600", "#ffffff", "#e53935"),
    },
    "espaco": {
        "nome": "Espaço", "descricao": "Estrelas, planetas e um foguete",
        "fonte": "Orbitron", "tamanho": "9pt",
        "cores": {
            "fundo": "#070b1f", "lateral": "#0b1029", "barra": "#0b1029", "superficie": "#141a3d",
            "destaque": "#a78bfa", "texto": "#e0e7ff", "texto_lateral": "#e0e7ff",
            "texto_barra": "#e0e7ff", "texto_destaque": "#0b1029", "aba_ativa": "#141a3d",
        },
        "avatares": ["#a78bfa", "#38bdf8", "#f472b6", "#fbbf24", "#34d399", "#fb7185"],
        "frases": ("Nenhuma nave acoplada", "Informe as coordenadas (ID) para decolar"),
        "inicio": f'background-image: url("{arte("espaco/estrelas.svg")}"),'
                  f' url("{arte("espaco/nebulosa_roxa.svg")}"), url("{arte("espaco/nebulosa_azul.svg")}");'
                  " background-size: 300px 300px, 700px 700px, 700px 700px;"
                  " background-position: 0 0, right top, left bottom;"
                  " background-repeat: repeat, no-repeat, no-repeat;",
        "css": """
.janela-principal .titulo-inicio { text-shadow: 0 0 12px alpha(#a78bfa, 0.8); }
.janela-principal .cartao-conectar { border: 1px solid alpha(#a78bfa, 0.35); box-shadow: 0 0 14px alpha(#7c3aed, 0.45); }
""",
        "decor": [
            {"arte": "espaco/planeta.svg", "w": 230, "h": 177, "halign": "end", "valign": "start",
             "margem": (40, 50, 0, 0), "anim": "flutuar-lento"},
            {"arte": "espaco/foguete.svg", "w": 70, "h": 117, "halign": "start", "valign": "end",
             "margem": (0, 0, 60, 90), "anim": "flutuar"},
            {"arte": "espaco/brilho.svg", "w": 26, "h": 26, "halign": "start", "valign": "start",
             "margem": (90, 0, 0, 160), "anim": "piscar"},
            {"arte": "espaco/brilho.svg", "w": 18, "h": 18, "halign": "end", "valign": "end",
             "margem": (0, 200, 110, 0), "anim": "piscar-lento"},
            {"arte": "espaco/brilho.svg", "w": 14, "h": 14, "halign": "start", "valign": "end",
             "margem": (0, 0, 240, 300), "anim": "piscar"},
        ],
        "previa": ("#070b1f", "#141a3d", "#a78bfa"),
    },
    "terminal": {
        "nome": "Terminal", "descricao": "Fósforo verde de monitor antigo",
        "fonte": "VT323", "tamanho": "14pt",
        "cores": {
            "fundo": "#050805", "lateral": "#070b07", "barra": "#0a120a", "superficie": "#0b140b",
            "destaque": "#33ff66", "texto": "#33ff66", "texto_lateral": "#33ff66",
            "texto_barra": "#33ff66", "texto_destaque": "#001a00", "aba_ativa": "#0b140b",
        },
        "avatares": ["#0f3d1a", "#14532d", "#166534", "#15803d", "#0f3d1a", "#14532d"],
        "raio": "0px", "raio_peq": "0px",
        "frases": ("> nenhuma_sessao_ativa", "digite o ID e pressione ENTER"),
        "inicio": "background-image: repeating-linear-gradient(to bottom, alpha(#33ff66, 0.05) 0px,"
                  " alpha(#33ff66, 0.05) 1px, transparent 1px, transparent 3px),"
                  " radial-gradient(circle at 50% 50%, alpha(#33ff66, 0.08), transparent 70%);",
        "css": """
.janela-principal label, .janela-principal entry { text-shadow: 0 0 6px alpha(#33ff66, 0.6); }
.janela-principal .avatar { color: #33ff66; border: 1px solid alpha(#33ff66, 0.6); }
.janela-principal entry, .janela-principal .cartao-conectar { border: 1px solid alpha(#33ff66, 0.45); }
.janela-principal .sidebar { border-right: 1px solid alpha(#33ff66, 0.3); }
.janela-principal headerbar { border-bottom: 1px solid alpha(#33ff66, 0.3); }
.janela-principal .titulo-inicio { font-size: 2.2em; }
""",
        "cursor": True,
        "decor": [
            {"tipo": "texto", "texto": "NAVIEW v1.0   [ SISTEMA OK ]", "halign": "start",
             "valign": "start", "margem": (24, 0, 0, 28)},
            {"tipo": "texto", "texto": "MEM 640K OK   CONEXOES: PRONTAS", "halign": "end",
             "valign": "end", "margem": (0, 28, 24, 0)},
        ],
        "previa": ("#050805", "#0b140b", "#33ff66"),
    },
    "neon": {
        "nome": "Neon 80s", "descricao": "Pôr do sol retrô e grade neon",
        "fonte": "Audiowide", "tamanho": "9.5pt",
        "cores": {
            "fundo": "#14052b", "lateral": "#12041f", "barra": "#12041f", "superficie": "#22093d",
            "destaque": "#ff2bd6", "texto": "#fdf2ff", "texto_lateral": "#fdf2ff",
            "texto_barra": "#fdf2ff", "texto_destaque": "#ffffff", "aba_ativa": "#22093d",
        },
        "avatares": ["#ff2bd6", "#22d3ee", "#ffb02e", "#a855f7", "#f43f5e", "#22c55e"],
        "frases": ("Pronto para conectar", "Digite um ID e aperte Enter"),
        "inicio": "background-image: linear-gradient(to bottom, #14052b, #2a0845 55%, #6a0d6b);",
        "css": """
.janela-principal .titulo-inicio { color: #ffe0fb; text-shadow: 0 0 6px #ff2bd6, 0 0 18px #ff2bd6; }
.janela-principal .cartao-conectar { background-color: alpha(#14052b, 0.82); border: 1px solid #ff2bd6;
  box-shadow: 0 0 12px alpha(#ff2bd6, 0.6), inset 0 0 8px alpha(#ff2bd6, 0.15); }
.janela-principal button.conectar { box-shadow: 0 0 14px alpha(#ff2bd6, 0.7); }
""",
        "decor": [
            {"arte": "neon/sol.svg", "w": 300, "h": 300, "halign": "center", "valign": "end",
             "margem": (0, 0, 110, 0), "anim": "pulsar-lento"},
            {"tipo": "faixa", "arte": "neon/montanhas.svg", "altura": 90, "tile": (1000, 90),
             "margem_baixo": 140},
            {"tipo": "faixa", "arte": "neon/grade.svg", "altura": 150, "tile": (1000, 150),
             "fundo": "#14052b"},
        ],
        "previa": ("#14052b", "#2a0845", "#ff2bd6"),
    },
    "mar": {
        "nome": "Alto-mar", "descricao": "O veleiro do NaView, farol e ondas ao pôr do sol",
        "fonte": "Fredoka", "tamanho": "10pt",
        "cores": {
            "fundo": "#111a44", "lateral": "#0e1638", "barra": "#0e1638", "superficie": "#1b2659",
            "destaque": "#38bdf8", "texto": "#e0f2fe", "texto_lateral": "#e0f2fe",
            "texto_barra": "#e0f2fe", "texto_destaque": "#0b1430", "aba_ativa": "#1b2659",
        },
        "avatares": ["#6366f1", "#0ea5e9", "#f59e0b", "#14b8a6", "#a78bfa", "#f472b6"],
        "frases": ("Mar calmo, nenhum cliente a bordo", "Informe o ID para zarpar"),
        "inicio": "background-image: linear-gradient(to bottom, #1e1b4b, #3730a3 35%, #6366f1 65%, #7dd3fc);",
        "css": """
.janela-principal .titulo-inicio { color: #ffffff; text-shadow: 0 2px 8px alpha(#1e1b4b, 0.8); }
.janela-principal .cartao-conectar { background-color: alpha(#0e1638, 0.85); border: 1px solid alpha(#7dd3fc, 0.45);
  box-shadow: 0 4px 14px alpha(#1e1b4b, 0.55); }
.janela-principal button.conectar { box-shadow: 0 0 10px alpha(#38bdf8, 0.6); }
.janela-principal .sidebar { border-right: 2px solid alpha(#f59e0b, 0.5); }
""",
        # Ordem = camadas: o sol se põe atrás das ondas do fundo; o farol e o barco ficam
        # entre as duas faixas de ondas. A luz fica sobre a lâmpada do farol (45, 42 de 90x200).
        "decor": [
            {"arte": "mar/sol.svg", "w": 200, "h": 200, "halign": "end", "valign": "end",
             "margem": (0, 190, 40, 0), "anim": "pulsar-lento"},
            {"arte": "mar/brilho.svg", "w": 16, "h": 16, "halign": "start", "valign": "start",
             "margem": (60, 0, 0, 180), "anim": "piscar"},
            {"arte": "mar/brilho.svg", "w": 12, "h": 12, "halign": "end", "valign": "start",
             "margem": (110, 160, 0, 0), "anim": "piscar-lento"},
            {"arte": "mar/gaivota.svg", "w": 40, "h": 16, "halign": "start", "valign": "start",
             "margem": (130, 0, 0, 320), "anim": "flutuar-lento"},
            {"arte": "mar/gaivota.svg", "w": 28, "h": 11, "halign": "start", "valign": "start",
             "margem": (100, 0, 0, 380), "anim": "flutuar"},
            {"tipo": "faixa", "arte": "mar/ondas_fundo.svg", "altura": 85, "tile": (1000, 85),
             "margem_baixo": 45},
            {"arte": "mar/farol.svg", "w": 90, "h": 200, "halign": "end", "valign": "end",
             "margem": (0, 80, 50, 0)},
            {"arte": "mar/luz.svg", "w": 60, "h": 60, "halign": "end", "valign": "end",
             "margem": (0, 95, 178, 0), "anim": "piscar"},
            {"arte": "mar/veleiro.svg", "w": 120, "h": 125, "halign": "start", "valign": "end",
             "margem": (0, 0, 42, 90), "anim": "navegar"},
            {"tipo": "faixa", "arte": "mar/ondas_frente.svg", "altura": 80, "tile": (1000, 80)},
            {"arte": "mar/brilho.svg", "w": 14, "h": 14, "halign": "center", "valign": "end",
             "margem": (0, 0, 30, 0), "anim": "piscar-lento"},
        ],
        "previa": ("#3730a3", "#0e1638", "#f59e0b"),
    },
    "manga": {
        "nome": "Mangá Noir", "descricao": "Preto e branco de mangá: retrato em tinta, sombras fortes",
        "fonte": "Zen Dots", "tamanho": "10pt",
        # Ícone da janela enquanto o tema estiver ativo (relativo a arte/).
        "icone": "manga/icone.png",
        "cores": {
            "fundo": "#0a0a0a", "lateral": "#000000", "barra": "#000000", "superficie": "#161616",
            "destaque": "#f5f5f5", "texto": "#f2f2f2", "texto_lateral": "#f2f2f2",
            "texto_barra": "#f2f2f2", "texto_destaque": "#0a0a0a", "aba_ativa": "#161616",
        },
        "avatares": ["#f5f5f5", "#d4d4d4", "#a3a3a3", "#737373", "#525252", "#e5e5e5"],
        "raio": "2px", "raio_peq": "2px",
        "frases": ("Nenhuma missão em andamento", "Informe o ID do cliente para começar"),
        # Wallpaper preto e branco (arte/manga/fundo.jpg), cobrindo a tela inicial.
        "inicio": f'background-image: url("{arte("manga/fundo.jpg")}");'
                  " background-size: cover; background-position: center; background-repeat: no-repeat;",
        "css": """
.janela-principal .titulo-inicio { color: #ffffff; text-shadow: 3px 3px 0 #000000; }
.janela-principal .cartao-conectar { background-color: alpha(#000000, 0.85); border: 2px solid #f5f5f5;
  box-shadow: 6px 6px 0 alpha(#f5f5f5, 0.9); }
.janela-principal button.conectar { border: 2px solid #f5f5f5; box-shadow: 3px 3px 0 alpha(#f5f5f5, 0.6); }
.janela-principal button.conectar:active { box-shadow: 1px 1px 0 alpha(#f5f5f5, 0.6); }
.janela-principal .sidebar { border-right: 2px solid #f5f5f5; }
.janela-principal headerbar { border-bottom: 2px solid #f5f5f5; }
.janela-principal entry { border: 1px solid alpha(#f5f5f5, 0.7); }
.janela-principal .avatar { border: 1px solid #f5f5f5; }
.janela-principal notebook.abas > header { border-bottom: 2px solid #f5f5f5; }
.janela-principal notebook.abas > header > tabs > tab:checked { border: 1px solid #f5f5f5; border-bottom: none; }
.janela-principal .sidebar row:selected { background-color: #f5f5f5; color: #0a0a0a; }
""",
        "previa": ("#0a0a0a", "#000000", "#f5f5f5"),
    },
}

ORDEM = ["padrao", "grafite", "claro", "oceano", "vidro", "pixel", "hq", "espaco", "terminal", "neon", "mar", "manga"]


# ---- preferências ----------------------------------------------------------

def carregar():
    cfg = {"tema": "padrao", "ajustes": {k: None for k in AJUSTES}, "imagem": None,
           "intensidade_vidro": 0.5, "decoracoes": True, "animacoes": True, "lateral_visivel": True,
           # Só para testes: entrega todas as cartas do jogo ao abrir (ligado à mão no config.json).
           "liberar_tudo": False}
    try:
        dados = json.loads(ARQUIVO.read_text())
    except (OSError, ValueError):
        return cfg
    if "aparencia" in dados:  # formato antigo (antes dos temas)
        antigo = dados["aparencia"]
        cfg["tema"] = "vidro" if antigo.get("vidro") else "padrao"
        cfg["ajustes"].update({k: antigo.get(k) for k in AJUSTES})
        cfg["imagem"] = antigo.get("imagem")
        cfg["lateral_visivel"] = dados.get("lateral_visivel", True)
        # Cores iguais às de um tema pronto: vira esse tema (ex.: quem usava "Oceano").
        for chave, tema in TEMAS.items():
            if all(cfg["ajustes"].get(k) == tema["cores"].get(k) for k in AJUSTES):
                cfg["tema"], cfg["ajustes"] = chave, {k: None for k in AJUSTES}
        return cfg
    for chave in cfg:
        if chave in dados:
            cfg[chave] = dados[chave]
    if cfg["tema"] not in TEMAS:
        cfg["tema"] = "padrao"
    # Cores e imagem de fundo escolhidas à mão não existem mais: o tema vale como ele é.
    cfg["ajustes"], cfg["imagem"] = {k: None for k in AJUSTES}, None
    return cfg


def salvar(cfg):
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def imagem_reduzida(caminho):
    """Cópia da imagem de fundo com no máximo 1920x1080 (guardada em ~/.cache).

    Imagens enormes deixam cada redesenho lento, porque o GTK3 reescala a imagem toda vez.
    """
    origem = Path(caminho)
    info = origem.stat()
    chave = hashlib.sha1(f"{origem.resolve()}:{info.st_mtime_ns}:{info.st_size}".encode()).hexdigest()[:16]
    destino = CACHE / f"fundo-{chave}.png"
    if destino.exists():
        return destino
    import gi  # só a versão GTK usa; a do Qt reduz a imagem em temas_qt.py

    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf, GLib

    try:
        _, largura, altura = GdkPixbuf.Pixbuf.get_file_info(str(origem))
        if largura <= MAX_FUNDO[0] and altura <= MAX_FUNDO[1]:
            return origem
        escala = min(MAX_FUNDO[0] / largura, MAX_FUNDO[1] / altura)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(origem), int(largura * escala), int(altura * escala), True)
        CACHE.mkdir(parents=True, exist_ok=True)
        pixbuf.savev(str(destino), "png", [], [])
        return destino
    except (GLib.Error, TypeError):
        return origem


def ler_cor(cor):
    """(r, g, b, a) de 0 a 1 para "#rgb", "#rrggbb", "#rrggbbaa", "rgb(...)" e "rgba(...)"; ou None."""
    cor = (cor or "").strip().lower()
    if cor.startswith("#"):
        h = cor[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        try:
            valores = [int(h[i:i + 2], 16) / 255 for i in range(0, len(h), 2)]
        except ValueError:
            return None
        return tuple(valores) if len(valores) == 4 else (*valores, 1.0)
    if cor.startswith(("rgb(", "rgba(")) and cor.endswith(")"):
        try:
            partes = [float(v) for v in cor[cor.index("(") + 1:-1].split(",")]
        except ValueError:
            return None
        if len(partes) in (3, 4):
            return (partes[0] / 255, partes[1] / 255, partes[2] / 255, partes[3] if len(partes) == 4 else 1.0)
    return None


def cor_texto(cor):
    """Preto ou branco, o que tiver mais contraste com a cor (só para cores #hex/rgb)."""
    rgba = ler_cor(cor)
    if not rgba:
        return None
    luminancia = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
    return "#1a1a1a" if luminancia > 0.55 else "#f2f2f2"


# ---- CSS -------------------------------------------------------------------

BASE = Template("""
.janela-principal { color: $texto; $fonte }
.janela-principal .raiz { background-color: $fundo; }

/* barra de título */
.janela-principal headerbar {
  background-image: none; background-color: $barra; color: $texto_barra;
  border: none; box-shadow: inset 0 -1px alpha($texto_barra, 0.08); min-height: 44px; padding: 0 8px;
}
.janela-principal headerbar .title { color: $texto_barra; font-weight: bold; }
.janela-principal headerbar .subtitle { color: alpha($texto_barra, 0.6); }
.janela-principal headerbar button {
  color: $texto_barra; background: none; border: none; box-shadow: none; text-shadow: none;
  -gtk-icon-shadow: none; border-radius: $raio_peq; min-width: 32px; min-height: 32px;
  transition: background-color 150ms ease;
}
.janela-principal headerbar button:hover { background-color: alpha($texto_barra, 0.12); }
.janela-principal headerbar button:checked { background-color: alpha($texto_barra, 0.18); }

/* barra de contatos */
.janela-principal .sidebar { background-color: $lateral; color: $texto_lateral; }
.janela-principal .sidebar .titulo-lateral { font-weight: bold; font-size: 1.1em; }
.janela-principal .sidebar .contagem { color: alpha($texto_lateral, 0.55); font-size: 0.85em; }
.janela-principal entry {
  background-color: $superficie; color: $texto; caret-color: $destaque; background-image: none;
  border: 1px solid alpha($texto_lateral, 0.14); border-radius: $raio_peq; box-shadow: none;
  min-height: 36px; padding: 0 10px;
}
.janela-principal entry:focus { border-color: $destaque; box-shadow: 0 0 0 2px alpha($destaque, 0.3); }
.janela-principal entry image { color: alpha($texto, 0.55); }
.janela-principal .sidebar list { background-color: transparent; }
.janela-principal .sidebar row {
  padding: 6px 8px; margin: 1px 8px; border-radius: $raio_peq; background-color: transparent;
  color: $texto_lateral; transition: background-color 120ms ease;
}
.janela-principal .sidebar row:hover { background-color: alpha($texto_lateral, 0.07); }
.janela-principal .sidebar row:selected { background-color: alpha($destaque, 0.25); color: $texto_lateral; }
.janela-principal .sidebar row .bt-editar { opacity: 0; transition: opacity 120ms ease; }
.janela-principal .sidebar row:hover .bt-editar { opacity: 0.75; }
.janela-principal .sidebar row button { background: none; border: none; box-shadow: none; color: $texto_lateral; }
.janela-principal .contato-nome { font-weight: bold; }
.janela-principal .contato-id { color: alpha($texto_lateral, 0.55); font-size: 0.85em; }
.janela-principal .vazio { color: alpha($texto_lateral, 0.55); padding: 24px 16px; }
.janela-principal .ponto-online { color: #22c55e; font-size: 0.8em; }
.janela-principal scrollbar slider { background-color: alpha($texto_lateral, 0.25); min-width: 6px; border-radius: 99px; }
.janela-principal scrollbar { background: none; border: none; }

.avatar { border-radius: $raio_avatar; min-width: 34px; min-height: 34px; font-weight: bold;
          font-size: 0.85em; color: #ffffff; text-shadow: none; }
.avatar.mini { min-width: 10px; min-height: 10px; font-size: 0; }
$avatares

/* tela inicial */
.janela-principal .inicio { background-color: $fundo; $inicio }
.janela-principal .titulo-inicio { font-size: 1.9em; font-weight: bold; color: $texto; }
.janela-principal .sub-inicio { color: alpha($texto, 0.7); }
.janela-principal .cartao-conectar {
  background-color: $superficie; border-radius: $raio; padding: 26px 28px;
  /* Sombra com desfoque pequeno: o GTK3 recalcula o desfoque a cada quadro. */
  box-shadow: 0 2px 6px alpha(#000000, 0.18), 0 0 0 1px alpha(#000000, 0.04);
}
.janela-principal button.conectar {
  background-image: none; background-color: $destaque; color: $texto_destaque; border: none;
  border-radius: $raio_peq; font-weight: bold; padding: 0 18px; min-height: 36px; text-shadow: none;
  transition: background-color 150ms ease;
}
.janela-principal button.conectar:hover { background-color: shade($destaque, 1.08); }
.janela-principal .recentes-titulo { color: alpha($texto, 0.55); font-size: 0.85em; font-weight: bold; }
.janela-principal .recentes flowboxchild { padding: 0; background: none; }
.janela-principal button.recente {
  background-image: none; background-color: alpha($destaque, 0.12); color: $texto; border: none;
  box-shadow: none; border-radius: $raio_peq; padding: 2px 12px; min-height: 28px; text-shadow: none;
  transition: background-color 150ms ease;
}
.janela-principal button.recente:hover { background-color: alpha($destaque, 0.24); }
.decor-texto { color: alpha($texto, 0.6); }

/* abas */
.janela-principal notebook.abas > header {
  background-color: $barra; border: none; box-shadow: inset 0 -1px alpha($texto_barra, 0.08);
  padding: 6px 8px 0 8px;
}
.janela-principal notebook.abas > header > tabs > tab {
  background-color: transparent; color: alpha($texto_barra, 0.7); border: none; outline: none;
  border-radius: $raio_peq $raio_peq 0 0; padding: 4px 6px 4px 12px; margin: 0 2px; min-height: 30px;
  transition: background-color 150ms ease, color 150ms ease;
}
.janela-principal notebook.abas > header > tabs > tab label { color: inherit; }
.janela-principal notebook.abas > header > tabs > tab:hover { background-color: alpha($texto_barra, 0.07); }
.janela-principal notebook.abas > header > tabs > tab:checked {
  background-color: $aba_ativa; color: $texto_aba_ativa; box-shadow: inset 0 -2px $destaque;
}
.janela-principal notebook.abas > header button {
  background: none; border: none; box-shadow: none; color: inherit; min-width: 22px; min-height: 22px;
  padding: 0; border-radius: 99px;
}
.janela-principal notebook.abas > header button:hover { background-color: alpha($texto_barra, 0.15); }
.janela-principal notebook.abas > stack { background-color: #000000; }

/* selo de novidades do jogo e pet no rodapé da barra de contatos */
.selo {
  background-color: #e53935; color: #ffffff; border-radius: 99px; font-size: 0.7em; font-weight: bold;
  padding: 0 5px; min-width: 10px; margin: 1px; text-shadow: none; border: 2px solid #ffffff;
}
.janela-principal .pet-rodape { padding: 6px 14px 10px 14px; border-top: 1px solid alpha($texto_lateral, 0.08); }
.janela-principal .pet-nome { font-weight: bold; }
.janela-principal .pet-fala { font-size: 0.85em; color: alpha($texto_lateral, 0.6); }

/* aviso no rodapé */
.aviso {
  background-color: shade($superficie, 0.92); color: $texto; border-radius: 999px; padding: 10px 18px;
  margin-bottom: 20px; box-shadow: 0 4px 12px alpha(#000000, 0.3);
}
""")

ANIMACOES = """
@keyframes flutuar { from { -gtk-icon-transform: translateY(0); } to { -gtk-icon-transform: translateY(-10px); } }
@keyframes balancar { from { -gtk-icon-transform: rotate(-12deg); } to { -gtk-icon-transform: rotate(12deg); } }
@keyframes pular { from { -gtk-icon-transform: translateY(0); } to { -gtk-icon-transform: translateY(-8px); } }
@keyframes pulsar { from { -gtk-icon-transform: scale(1); } to { -gtk-icon-transform: scale(1.08); } }
@keyframes navegar { from { -gtk-icon-transform: rotate(-3deg) translateY(0); } to { -gtk-icon-transform: rotate(3deg) translateY(-5px); } }
@keyframes piscar { from { opacity: 1; } to { opacity: 0.2; } }
@keyframes cursor { from { opacity: 1; } to { opacity: 0; } }
.anim-flutuar { animation: flutuar 2.2s ease-in-out infinite alternate; }
.anim-flutuar-lento { animation: flutuar 4s ease-in-out infinite alternate; }
.anim-balancar { animation: balancar 1.8s ease-in-out infinite alternate; }
.anim-pular { animation: pular 0.5s steps(2) infinite alternate; }
.anim-pular-lento { animation: pular 0.8s steps(2) infinite alternate; }
.anim-pulsar { animation: pulsar 0.9s ease-in-out infinite alternate; }
.anim-pulsar-lento { animation: pulsar 2.5s ease-in-out infinite alternate; }
.anim-navegar { animation: navegar 3s ease-in-out infinite alternate; }
.anim-piscar { animation: piscar 1.4s ease-in-out infinite alternate; }
.anim-piscar-lento { animation: piscar 2.6s ease-in-out infinite alternate; }
.cursor { animation: cursor 0.6s steps(1) infinite alternate; }
"""


def icone_do_tema(chave):
    """Arquivo SVG do ícone do app: o do tema, se ele tiver um (\"icone\"), senão o do NaView."""
    arquivo = TEMAS.get(chave, {}).get("icone")
    return ARTE / arquivo if arquivo else PASTA / "icone.svg"


_icone_instalado = None


def instalar_icone_do_tema(chave):
    """Faz o ícone do atalho instalado (dock/barra de tarefas) acompanhar o tema.

    No GNOME e no KDE a barra de tarefas mostra o ícone do atalho (.desktop), não o da janela.
    Reescrever o arquivo do ícone não adianta: o shell guarda o ícone pelo nome. Por isso cada
    tema com ícone próprio ganha um ícone de nome novo (naview-<tema>) e a linha Icon= do atalho
    passa a apontar para ele; sem ícone próprio, volta ao "naview" instalado pelo instalar.sh.
    Só mexe nos arquivos do usuário (~/.local/share) e só se o atalho foi instalado.
    """
    global _icone_instalado
    if not plataforma.LINUX or _icone_instalado == chave:
        return
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    atalho = base / "applications" / "naview.desktop"
    if not atalho.is_file():
        return
    try:
        nome = "naview"
        if TEMAS.get(chave, {}).get("icone"):
            nome = f"naview-{chave}"
            pasta = base / "icons/hicolor/scalable/apps"
            pasta.mkdir(parents=True, exist_ok=True)
            origem = icone_do_tema(chave)
            if origem.suffix == ".svg":
                conteudo = origem.read_bytes()
            else:  # PNG vira um SVG que o embute, para ficar na pasta de ícones escaláveis
                png = base64.b64encode(origem.read_bytes()).decode()
                conteudo = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                            'viewBox="0 0 512 512"><image width="512" height="512" '
                            f'xlink:href="data:image/png;base64,{png}"/></svg>\n').encode()
            arquivo = pasta / f"{nome}.svg"
            if not arquivo.is_file() or arquivo.read_bytes() != conteudo:
                arquivo.write_bytes(conteudo)
                _rodar(["gtk-update-icon-cache", "-q", "-t", "-f", str(base / "icons/hicolor")])
        texto = atalho.read_text()
        novo = re.sub(r"(?m)^Icon=.*$", f"Icon={nome}", texto)
        if novo != texto:
            atalho.write_text(novo)
            _rodar(["update-desktop-database", "-q", str(atalho.parent)])
            _rodar(["kbuildsycoca6"])  # KDE; sem efeito nos outros ambientes
        _icone_instalado = chave
    except OSError:
        pass


def _rodar(comando):
    """Roda uma ferramenta opcional do sistema, sem esperar nem falhar se ela não existir."""
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def cores_do_tema(cfg):
    tema = TEMAS[cfg["tema"]]
    cores = dict(tema["cores"])
    cores.setdefault("texto_aba_ativa", cores["texto_barra"])
    if tema.get("vidro"):
        # Intensidade 0 = quase sem tinta (mais vidro); 1 = painéis mais opacos.
        i = max(0.0, min(1.0, cfg.get("intensidade_vidro", 0.5)))
        tinta = 0.08 + 0.45 * i if TEM_DESFOQUE else 0.70 + 0.25 * i
        valores = {"tinta": f"{tinta:.2f}", "painel": f"{0.06 + 0.22 * i:.2f}",
                   "barra": f"{0.03 + 0.15 * i:.2f}", "campo": f"{0.10 + 0.18 * i:.2f}"}
        cores = {k: v.format(**valores) for k, v in cores.items()}
    for chave in AJUSTES:
        valor = cfg["ajustes"].get(chave)
        if valor:
            cores[chave] = valor
            if chave == "lateral":
                cores["texto_lateral"] = cor_texto(valor) or cores["texto_lateral"]
            elif chave == "barra":
                cores["texto_barra"] = cor_texto(valor) or cores["texto_barra"]
                cores["aba_ativa"] = cores["fundo"]
                cores["texto_aba_ativa"] = cores["texto"]
            elif chave == "fundo":
                cores["texto"] = cor_texto(valor) or cores["texto"]
            elif chave == "destaque":
                cores["texto_destaque"] = cor_texto(valor) or cores["texto_destaque"]
    return cores


# Molduras dos avatares (cartas do jogo).
MOLDURAS = {
    "simples": "box-shadow: 0 0 0 2px $lateral, 0 0 0 4px alpha($destaque, 0.8);",
    "pontilhada": "border: 2px dashed $destaque;",
    "dupla": "box-shadow: 0 0 0 2px $lateral, 0 0 0 4px #3b82f6, 0 0 0 6px #a855f7;",
    "neon": "box-shadow: 0 0 0 2px #ff2bd6, 0 0 6px #ff2bd6;",
    "dourada": "box-shadow: 0 0 0 2px #f5b81b, 0 0 0 4px #8a5a00, 0 0 6px alpha(#f5b81b, 0.8);",
}
DOURADO = "#f5b81b"


def gerar_css(cfg, dourado=False, moldura=None):
    """dourado: tema no nível máximo da coleção (destaque dourado). moldura: chave de MOLDURAS."""
    tema = TEMAS[cfg["tema"]]
    cores = cores_do_tema(cfg)
    if dourado and not cfg["ajustes"].get("destaque"):
        cores["destaque"], cores["texto_destaque"] = DOURADO, "#3a2400"
    avatares = tema.get("avatares", PADRAO_AVATARES)
    fonte = ""
    if tema.get("fonte"):
        fonte = f'font-family: "{tema["fonte"]}"; font-size: {tema.get("tamanho", "10pt")};'
    inicio = tema.get("inicio", "")
    if cfg.get("imagem") and Path(cfg["imagem"]).is_file():
        inicio = (f'background-image: url("{imagem_reduzida(cfg["imagem"]).as_uri()}");'
                  " background-size: cover; background-position: center; background-repeat: no-repeat;")
    valores = dict(
        cores, fonte=fonte, inicio=inicio,
        raio=tema.get("raio", "14px"), raio_peq=tema.get("raio_peq", "8px"),
        raio_avatar="0px" if tema.get("raio") == "0px" else "999px",
        avatares="\n".join(f".avatar-{i} {{ background-color: {c}; }}" for i, c in enumerate(avatares)),
    )
    partes = [BASE.substitute(valores), Template(tema.get("css", "")).safe_substitute(valores)]
    if moldura in MOLDURAS:
        partes.append(".janela-principal .sidebar .avatar { "
                      + Template(MOLDURAS[moldura]).safe_substitute(valores) + " }")
    if cfg.get("animacoes", True):
        partes.append(ANIMACOES)
    for i, d in enumerate(tema.get("decor", [])):
        if d.get("tipo") == "faixa":
            w, h = d["tile"]
            partes.append(
                f'.decor-faixa-{i} {{ background-image: url("{arte(d["arte"])}");'
                f" background-repeat: repeat-x; background-size: {w}px {h}px;"
                f" background-position: center bottom; background-color: {d.get('fundo', 'transparent')}; }}")
    return "\n".join(partes).encode()


def css_previas():
    """Estilo dos cartões de tema na janela de aparência (cada um com as cores do seu tema)."""
    regras = []
    for chave, tema in TEMAS.items():
        fundo, lateral, destaque = tema["previa"]
        fonte = f'font-family: "{tema["fonte"]}";' if tema.get("fonte") else ""
        texto = cor_texto(fundo) or "#ffffff"
        regras.append(
            f".previa-{chave} {{ background-image: linear-gradient(to right, {lateral} 30%, {fundo} 30%);"
            f" border-radius: 10px; min-height: 64px; }}\n"
            f".previa-{chave} .previa-nome {{ {fonte} color: {texto}; font-size: 1.05em; }}\n"
            f".previa-{chave} .previa-ponto {{ background-color: {destaque}; border-radius: 99px;"
            f" min-width: 14px; min-height: 14px; }}")
    return "\n".join(regras).encode()
