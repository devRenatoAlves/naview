#!/usr/bin/env python3
"""Monta a página de apresentação em site/publico, com o pacote de download do app.

Uso: python3 ferramentas/gerar_site.py

- Copia site/fonte (HTML, CSS, JS), as artes, as fontes e o confete do app.
- Gera download/naview-<versão>.tar.gz com os arquivos do app (pasta "naview/" dentro).
- Preenche no HTML a versão, o nome do arquivo, o tamanho e o SHA-256.
"""
import hashlib
import shutil
import tarfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "site" / "fonte"
SAIDA = RAIZ / "site" / "publico"

# O que vai no pacote do app (o resto, como docs/ e site/, fica de fora).
ARQUIVOS_APP = [
    "app.py", "contatos.py", "fontes.py", "janela_aparencia.py", "temas.py", "x11.py",
    "icone.svg", "instalar.sh", "README.md", "VERSAO",
]
PASTAS_APP = ["arte", "fonts", "icones", "jogo", "sons", "web"]

PASTAS_ARTE_SITE = ["mar", "neon", "espaco", "pixel", "hq", "pets", "acessorios", "baus"]
ICONES_SITE = ["sparkle.svg", "speaker-high.svg"]


def ignorar(_pasta, nomes):
    return [n for n in nomes if n == "__pycache__" or n.endswith(".pyc")]


def tamanho_legivel(n):
    for unidade in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidade == "GB":
            return f"{n:.0f} {unidade}" if unidade in ("B", "KB") else f"{n:.1f} {unidade}".replace(".", ",")
        n /= 1024
    return f"{n} B"


def filtro_tar(info):
    if "__pycache__" in info.name or info.name.endswith(".pyc"):
        return None
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def gerar_pacote(versao, destino):
    nome = f"naview-{versao}.tar.gz"
    caminho = destino / nome
    with tarfile.open(caminho, "w:gz") as tar:
        for arquivo in ARQUIVOS_APP:
            tar.add(RAIZ / arquivo, arcname=f"naview/{arquivo}", filter=filtro_tar)
        for pasta in PASTAS_APP:
            tar.add(RAIZ / pasta, arcname=f"naview/{pasta}", filter=filtro_tar)
    return caminho


def main():
    versao = (RAIZ / "VERSAO").read_text().strip()

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    shutil.copytree(FONTE, SAIDA)

    for pasta in PASTAS_ARTE_SITE:
        shutil.copytree(RAIZ / "arte" / pasta, SAIDA / "arte" / pasta)
    (SAIDA / "arte" / "icones").mkdir(parents=True)
    for icone in ICONES_SITE:
        shutil.copy2(RAIZ / "icones" / "phosphor" / icone, SAIDA / "arte" / "icones" / icone)
    shutil.copytree(RAIZ / "fonts", SAIDA / "fonts")
    (SAIDA / "vendor").mkdir()
    shutil.copy2(RAIZ / "web" / "vendor" / "confetti.browser.min.js", SAIDA / "vendor")
    shutil.copy2(RAIZ / "icone.svg", SAIDA / "icone.svg")

    (SAIDA / "download").mkdir()
    pacote = gerar_pacote(versao, SAIDA / "download")
    dados = pacote.read_bytes()
    sha256 = hashlib.sha256(dados).hexdigest()
    (SAIDA / "download" / f"{pacote.name}.sha256").write_text(f"{sha256}  {pacote.name}\n")

    html = (SAIDA / "index.html").read_text()
    for chave, valor in {
        "{{VERSAO}}": versao,
        "{{ARQUIVO}}": pacote.name,
        "{{TAMANHO}}": tamanho_legivel(len(dados)),
        "{{SHA256}}": sha256,
    }.items():
        html = html.replace(chave, valor)
    (SAIDA / "index.html").write_text(html)

    print(f"Site gerado em {SAIDA}")
    print(f"Pacote: {pacote.name} ({tamanho_legivel(len(dados))})")
    print(f"SHA-256: {sha256}")


if __name__ == "__main__":
    main()
