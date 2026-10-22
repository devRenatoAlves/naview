"""Atualização do NaView: consulta o site, baixa a versão nova, confere o SHA-256 e aplica ao sair.

Sem GTK nem Qt (só biblioteca padrão), para servir aos dois. Ver docs/sdd/specs/07-atualizacao.md.

Fluxo:
  consultar()  -> Atualizacao ou None   (rede, rodar fora da thread da interface)
  preparar(a)  -> prepara a troca       (baixa e confere; rede, idem)
  agendar(p)   -> troca e reabre quando o programa terminar (atexit)

- Linux: o pacote .tar.gz é extraído numa pasta de preparo dentro da pasta do app; ao sair, as
  pastas e arquivos do pacote trocam de lugar com os atuais. Os dados do usuário ficam fora.
- Windows: o instalador baixado roda em modo silencioso depois que o NaView fecha.
- Pasta do app com .git (cópia de desenvolvimento) ou sem permissão de escrita: nada é trocado;
  a interface mostra o link da página de download (pode_atualizar_sozinho() == False).
"""
import atexit
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import plataforma

# Variável de ambiente só para testes: aponta o manifesto para um servidor local e libera http/file.
ENV_URL = "NAVIEW_URL_ATUALIZACAO"
URL_PADRAO = "https://naview.hunpe.com.br/download/versao.json"

TIMEOUT_S = 15
MANIFESTO_MAX = 100_000
PACOTE_MAX = 400 * 1024 * 1024
PREPARO = ".atualizacao"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class Atualizacao:
    versao: str
    url: str
    sha256: str
    tamanho: int
    obrigatoria: bool
    pagina: str


def url_manifesto():
    return os.environ.get(ENV_URL) or URL_PADRAO


def _esquemas_aceitos():
    return ("https", "http", "file") if os.environ.get(ENV_URL) else ("https",)


def pasta_app():
    """Pasta com o código do app (no Windows empacotado, a pasta de dados do PyInstaller)."""
    return Path(getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent)


def versao_atual():
    try:
        return (pasta_app() / "VERSAO").read_text().strip() or "0"
    except OSError:
        return "0"


def chave(versao):
    """'2026.10.22.1' -> (2026, 10, 22, 1); None se não for um número de versão."""
    try:
        return tuple(int(p) for p in str(versao).strip().split("."))
    except ValueError:
        return None


def interpretar(dados, base, atual):
    """Escolhe do manifesto a entrada desta plataforma; devolve Atualizacao se for mais nova."""
    if not isinstance(dados, dict):
        return None
    entrada = dados.get("windows" if plataforma.WINDOWS else "linux")
    if not isinstance(entrada, dict):
        return None
    nova, minima, em_uso = chave(entrada.get("versao")), chave(dados.get("minimo") or "0"), chave(atual) or (0,)
    if nova is None or minima is None or nova <= em_uso:
        return None
    sha = str(entrada.get("sha256", "")).lower()
    url = urljoin(base, str(entrada.get("arquivo", "")))
    if not _SHA256.match(sha) or urlparse(url).scheme not in _esquemas_aceitos():
        return None
    tamanho = entrada.get("tamanho")
    return Atualizacao(
        versao=str(entrada["versao"]).strip(), url=url, sha256=sha,
        tamanho=tamanho if isinstance(tamanho, int) and tamanho > 0 else 0,
        obrigatoria=em_uso < minima,
        pagina=urljoin(base, str(dados.get("pagina") or "/")),
    )


def consultar():
    """Atualizacao disponível para esta plataforma, ou None (sem versão nova, sem rede ou erro)."""
    url = url_manifesto()
    if urlparse(url).scheme not in _esquemas_aceitos():
        return None
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": f"NaView/{versao_atual()}",
                                                      "Cache-Control": "no-cache"})
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_S) as resposta:
            dados = json.loads(resposta.read(MANIFESTO_MAX).decode("utf-8"))
    except Exception:
        return None
    return interpretar(dados, url, versao_atual())


def pode_atualizar_sozinho():
    if plataforma.WINDOWS:
        return bool(getattr(sys, "frozen", False))
    pasta = pasta_app()
    return (pasta / "app.py").is_file() and not (pasta / ".git").exists() and os.access(pasta, os.W_OK)


def _baixar(url, sha256, destino):
    resumo = hashlib.sha256()
    lidos = 0
    pedido = urllib.request.Request(url, headers={"User-Agent": f"NaView/{versao_atual()}"})
    with urllib.request.urlopen(pedido, timeout=TIMEOUT_S) as resposta, open(destino, "wb") as saida:
        while True:
            bloco = resposta.read(1 << 20)
            if not bloco:
                break
            lidos += len(bloco)
            if lidos > PACOTE_MAX:
                raise ValueError("arquivo maior que o esperado")
            resumo.update(bloco)
            saida.write(bloco)
    if resumo.hexdigest() != sha256:
        destino.unlink(missing_ok=True)
        raise ValueError("SHA-256 diferente do esperado")


def _extrair(pacote, destino):
    """Extrai só arquivos e pastas comuns, sempre para dentro de destino."""
    base = destino.resolve()
    with tarfile.open(pacote, "r:gz") as tar:
        for item in tar.getmembers():
            alvo = (destino / item.name).resolve()
            if not (item.isfile() or item.isdir()) or (alvo != base and base not in alvo.parents):
                raise ValueError(f"item inválido no pacote: {item.name}")
        if hasattr(tarfile, "data_filter"):
            tar.extractall(destino, filter="data")
        else:
            tar.extractall(destino)


def preparar(atualizacao):
    """Baixa, confere e deixa tudo pronto para trocar ao sair. Devolve o que agendar() precisa.

    Levanta exceção se o download falhar, o hash não bater ou o pacote vier errado.
    """
    if plataforma.WINDOWS:
        pasta = Path(tempfile.mkdtemp(prefix="naview-atualizacao-"))
        instalador = pasta / "NaView-instalador.exe"
        _baixar(atualizacao.url, atualizacao.sha256, instalador)
        return {"tipo": "windows", "instalador": instalador}

    preparo = pasta_app() / PREPARO
    shutil.rmtree(preparo, ignore_errors=True)
    preparo.mkdir()
    try:
        pacote = preparo / "pacote.tar.gz"
        _baixar(atualizacao.url, atualizacao.sha256, pacote)
        _extrair(pacote, preparo)
        pacote.unlink()
        raiz = preparo / "naview"
        if not (raiz / "app.py").is_file() or chave((raiz / "VERSAO").read_text()) != chave(atualizacao.versao):
            raise ValueError("pacote não é a versão anunciada")
    except Exception:
        shutil.rmtree(preparo, ignore_errors=True)
        raise
    return {"tipo": "linux", "raiz": raiz, "preparo": preparo}


def trocar_arquivos(raiz, pasta, preparo):
    """Troca o que o pacote traz (pastas inteiras e arquivos da raiz); desfaz tudo se algo falhar."""
    velho = preparo / "velho"
    velho.mkdir(exist_ok=True)
    movidos = []
    try:
        for novo in sorted(raiz.iterdir()):
            atual = pasta / novo.name
            if atual.exists():
                os.replace(atual, velho / novo.name)
                movidos.append((novo.name, True))
            else:
                movidos.append((novo.name, False))
            os.replace(novo, atual)
    except Exception:
        for nome, existia in reversed(movidos):
            try:
                (pasta / nome).unlink() if (pasta / nome).is_file() else shutil.rmtree(pasta / nome, ignore_errors=True)
                if existia:
                    os.replace(velho / nome, pasta / nome)
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(preparo, ignore_errors=True)


def _comando_reabrir():
    if getattr(sys, "frozen", False):
        return [sys.executable]
    principal = getattr(sys.modules.get("__main__"), "__file__", None)
    return [sys.executable, os.path.abspath(principal)] if principal else None


def _no_fim(preparado, reabrir):
    """Roda quando o programa já terminou: troca os arquivos (Linux) ou chama o instalador."""
    try:
        if preparado["tipo"] == "windows":
            # Sem janela de console e desligado do NaView; o instalador reabre o app no final.
            flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            subprocess.Popen([str(preparado["instalador"]), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                             creationflags=flags, close_fds=True)
            return
        trocar_arquivos(preparado["raiz"], pasta_app(), preparado["preparo"])
    except Exception:
        pass  # sem troca, o app antigo continua valendo; reabrir abaixo o abre de novo
    if reabrir:
        try:
            subprocess.Popen(reabrir, start_new_session=True, close_fds=True)
        except OSError:
            pass


def agendar(preparado):
    """Faz a troca quando o NaView terminar (a interface só precisa fechar a janela normalmente)."""
    atexit.register(_no_fim, preparado, None if preparado["tipo"] == "windows" else _comando_reabrir())
