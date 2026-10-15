"""Baixa os sprites oficiais dos Pokémon (Black/White, via PokeAPI) e salva em arte/pets/ como SVG.

Pokémon são da Nintendo / Game Freak: arte usada só dentro da equipe (ver decisão D18).
Rodar só quando entrar um Pokémon novo; os SVGs ficam no projeto.
"""
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pixel_vetor import de_imagem, no_quadro  # noqa: E402

URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/{}.png"
POKEMON = {"pikachu": 25, "eevee": 133, "jigglypuff": 39, "gengar": 94}
SAIDA = Path(__file__).resolve().parent.parent / "arte" / "pets"


def main():
    with tempfile.TemporaryDirectory() as pasta:
        for nome, numero in POKEMON.items():
            png = Path(pasta) / f"{numero}.png"
            urllib.request.urlretrieve(URL.format(numero), png)
            desenho, (dx, dy) = no_quadro(de_imagem(png))
            (SAIDA / f"{nome}.svg").write_text(desenho)
            print(f"{nome}: deslocamento no quadro {dx}, {dy}")


if __name__ == "__main__":
    main()
