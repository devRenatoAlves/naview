#!/usr/bin/env python3
"""Monta a página de apresentação em site/publico, com o pacote de download do app.

Uso: python3 ferramentas/gerar_site.py

- Copia site/fonte (HTML, CSS, JS), as artes, as fontes e o confete do app.
- Gera download/naview-<versão>.tar.gz com os arquivos do app (pasta "naview/" dentro).
- Preenche no HTML a versão, o nome do arquivo, o tamanho e o SHA-256.
- Piloto Windows: se o GitHub Actions já guardou site/piloto-windows/naview-piloto-windows.zip,
  copia para download/ e preenche a página piloto/ (não divulgada, ver specs/06-windows.md).
- Windows: se o GitHub Actions já guardou site/windows/NaView-instalador.exe, copia para
  download/windows/ com o windows.json (versão, tamanho, SHA-256) que a página lê.
"""
import hashlib
import json
import shutil
import tarfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "site" / "fonte"
SAIDA = RAIZ / "site" / "publico"

# O que vai no pacote do app (o resto, como docs/ e site/, fica de fora).
ARQUIVOS_APP = [
    "app.py", "contatos.py", "fontes.py", "janela_aparencia.py", "plataforma.py", "temas.py", "x11.py",
    "app_qt.py", "aparencia_qt.py", "temas_qt.py",
    "icone.svg", "instalar.sh", "README.md", "VERSAO",
]
PASTAS_APP = ["arte", "fonts", "icones", "janelas", "jogo", "sons", "web"]

PILOTO_WINDOWS = RAIZ / "site" / "piloto-windows" / "naview-piloto-windows.zip"
# Guardados pelo GitHub Actions (.github/workflows/windows.yml).
INSTALADOR_WINDOWS = RAIZ / "site" / "windows" / "NaView-instalador.exe"
VERSAO_WINDOWS = RAIZ / "site" / "windows" / "VERSAO"

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


def preencher_piloto():
    """Página do piloto Windows: com o pacote, mostra o download; sem ele, um aviso."""
    pagina = SAIDA / "piloto" / "index.html"
    html = pagina.read_text()
    valores = {"{{WIN_DISPONIVEL}}": "nao", "{{WIN_ARQUIVO}}": "", "{{WIN_TAMANHO}}": "",
               "{{WIN_SHA256}}": "", "{{WIN_DATA}}": ""}
    if PILOTO_WINDOWS.is_file():
        destino = SAIDA / "download" / PILOTO_WINDOWS.name
        shutil.copy2(PILOTO_WINDOWS, destino)
        dados = destino.read_bytes()
        # Data da montagem: a dos arquivos dentro do zip (a do arquivo muda a cada clone do git).
        with zipfile.ZipFile(destino) as z:
            ano, mes, dia = max(i.date_time for i in z.infolist())[:3]
        valores.update({
            "{{WIN_DISPONIVEL}}": "sim",
            "{{WIN_ARQUIVO}}": destino.name,
            "{{WIN_TAMANHO}}": tamanho_legivel(len(dados)),
            "{{WIN_SHA256}}": hashlib.sha256(dados).hexdigest(),
            "{{WIN_DATA}}": f"{dia:02d}/{mes:02d}/{ano}",
        })
    for chave, valor in valores.items():
        html = html.replace(chave, valor)
    pagina.write_text(html)
    return valores["{{WIN_DISPONIVEL}}"] == "sim"


def preencher_windows():
    """Instalador do Windows em download/windows/, com o windows.json que a página lê."""
    if not INSTALADOR_WINDOWS.is_file():
        return None
    pasta = SAIDA / "download" / "windows"
    pasta.mkdir(parents=True)
    destino = pasta / INSTALADOR_WINDOWS.name
    shutil.copy2(INSTALADOR_WINDOWS, destino)
    dados = destino.read_bytes()
    versao = VERSAO_WINDOWS.read_text().strip() if VERSAO_WINDOWS.is_file() else ""
    info = {"versao": versao, "arquivo": destino.name, "tamanho": tamanho_legivel(len(dados)),
            "sha256": hashlib.sha256(dados).hexdigest()}
    (pasta / "windows.json").write_text(json.dumps(info, ensure_ascii=False))
    return info


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

    valores = {
        "{{VERSAO}}": versao,
        "{{ARQUIVO}}": pacote.name,
        "{{TAMANHO}}": tamanho_legivel(len(dados)),
        "{{SHA256}}": sha256,
    }
    html = (SAIDA / "index.html").read_text()
    for chave, valor in valores.items():
        html = html.replace(chave, valor)
    # O nginx guarda CSS e JS no navegador por 7 dias: o ?v= muda junto com o conteúdo.
    for arquivo in ("estilo.css", "pagina.js"):
        codigo = hashlib.sha256((SAIDA / arquivo).read_bytes()).hexdigest()[:10]
        assert html.count(f'"{arquivo}"') == 1, arquivo
        html = html.replace(f'"{arquivo}"', f'"{arquivo}?v={codigo}"')
    (SAIDA / "index.html").write_text(html)
    piloto = preencher_piloto()
    windows = preencher_windows()

    print(f"Site gerado em {SAIDA}")
    print(f"Pacote: {pacote.name} ({tamanho_legivel(len(dados))})")
    print(f"SHA-256: {sha256}")
    print("Piloto Windows: " + ("incluído" if piloto else "sem pacote ainda"))
    print("Windows: " + (f"{windows['versao']} ({windows['tamanho']})" if windows else "sem instalador ainda"))


if __name__ == "__main__":
    main()
