#!/usr/bin/env python3
"""Prepara os ícones Phosphor (icones/phosphor/, licença MIT) para o GTK.

Os ícones da página do jogo são pixel art própria (gerar_icones_pixel.py, web/icones.js).

- icones/gtk/ph-<nome>-symbolic.svg: o GTK pinta ícones "-symbolic" com a cor do texto do tema.
"""
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
    print(len(icones), "ícones")


if __name__ == "__main__":
    main()
