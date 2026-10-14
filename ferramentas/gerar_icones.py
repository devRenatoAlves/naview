#!/usr/bin/env python3
"""Prepara os ícones Phosphor (icones/phosphor/, licença MIT) para a página do jogo e para o GTK.

- web/icones.js: os desenhos embutidos no JavaScript (a página não depende de fonte de ícones).
- icones/gtk/ph-<nome>-symbolic.svg: o GTK pinta ícones "-symbolic" com a cor do texto do tema.
"""
import json
import re
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "icones" / "phosphor"
GTK = RAIZ / "icones" / "gtk"


def main():
    icones = {}
    GTK.mkdir(parents=True, exist_ok=True)
    # Apaga as cópias antigas: ícone removido da origem não pode continuar só no GTK.
    for antigo in GTK.glob("ph-*-symbolic.svg"):
        antigo.unlink()
    # A licença MIT precisa acompanhar as cópias.
    shutil.copy(ORIGEM / "LICENSE", GTK / "LICENSE")
    for arquivo in sorted(ORIGEM.glob("*.svg")):
        svg = arquivo.read_text()
        miolo = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()
        icones[arquivo.stem] = miolo
        (GTK / f"ph-{arquivo.stem}-symbolic.svg").write_text(svg)
    (RAIZ / "web" / "icones.js").write_text(
        "// Gerado por ferramentas/gerar_icones.py a partir de Phosphor Icons (MIT).\n"
        f"window.ICONES = {json.dumps(icones, indent=0)};\n"
        "window.ic = (nome, classe = \"\") => {\n"
        "  if (!(nome in window.ICONES)) console.warn(`Ícone desconhecido: ${nome}`);\n"
        "  return `<svg class=\"ic ${classe}\" viewBox=\"0 0 256 256\" fill=\"currentColor\" aria-hidden=\"true\">"
        "${window.ICONES[nome] || \"\"}</svg>`;\n"
        "};\n")
    print(len(icones), "ícones")


if __name__ == "__main__":
    main()
