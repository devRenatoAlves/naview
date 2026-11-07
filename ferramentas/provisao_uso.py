#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provisão do uso do computador: NaView vs AnyDesk.

Cenários
  S1 - AnyDesk só (daemon/tray, sem sessão ativa): CPU, RAM, portas abertas, fds.
  S2 - Jogo do NaView isolado: web/jogo.html num navegador headless (modo TESTE),
       em curso e pausado (mede-se o grupo de processos do navegador).
       O JOGO NÃO é o WebKit do NaView; é o mesmo conteúdo/animacoes que o NaView
       carrega quando abre o jogo. Serve para isolar o peso da parte mais pesada.
  S3 - Arquitetura de processos: NaView (app + N processos anydesk + WebKit no jogo)
       vs AnyDesk (1 processo por sessão). No desktop REAL do usuário:
         python3 ferramentas/provisao_uso.py --escenario S3 --segundos 60
  S4 - Disco: tamanho do programa e quantidade de arquivos.

Requisitos: psutil (pip install psutil). Nenhum dado real do usuário é alterado:
nenhum contato, progresso, configuração ou sessão é modificada. O S3 exige o app
aberto no seu desktop (veja docs/sdd/testes.md: Gtk.OffscreenWindow, sem capturar a
tela inteira).
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    import psutil
except ImportError:
    psutil = None

CHROMES = [shutil.which("google-chrome"), shutil.which("chromium")]


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def mem_mb(size):
    return round(size / (1024 * 1024), 1)


def processos_por_nome(nomes):
    """Todos os processos cujo cmdline corresponde a algum destes nomes."""
    achados = []
    if psutil is None:
        return achados
    for p in psutil.process_iter(["pid", "name", "cmdline", "ppid"]):
        try:
            cmd = " ".join(p.info["cmdline"] or [])
            if any(n == p.info["name"] or n in cmd for n in nomes):
                achados.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return achados


def processos_anydesk():
    """Processos do AnyDesk (exclui o proprio processo e o shell que invocou)."""
    aim = []
    for p in processos_por_nome(["anydesk"]):
        try:
            cmd = " ".join(p.cmdline() or [])
            if p.pid == os.getpid():
                continue
            if p.name() != "anydesk":
                continue
            # ignorar processos temporarios/erros do proprio teste
            if "timeout" in cmd or "bash" in cmd:
                continue
            aim.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return aim


def grupo_pid(p, recursivo=True):
    """Todos os descendentes de um processo (pode incluir o proprio)."""
    relativo = []
    try:
        for c in p.children(recursive=recursivo):
            relativo.append(c)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return relativo


def ProcessoGrupo(p):
    """Processo do chrome + todos os descendentes (renderer, gpu, etc.), psutil.Process."""
    relativo = [psutil.Process(p.pid)] if p else []
    try:
        relativo.extend(psutil.Process(p.pid).children(recursive=True))
    except Exception:
        pass
    return relativo


def rss_grupo(processos, segundos=5):
    """Média de RSS (MB) e soma do CPU (em % de um nucleo) de um grupo, durante `segundos`.

    A soma do CPU é feita sobre os processos do grupo (utime+stime de /proc/<pid>/stat),
    expressa em percentagem do tempo de um nucleo: 100 = um nucleo inteiro gasto
    (somatório dos processos). Eficiente: pega utime/stime de /proc e dorme uma
    unica vez, sem poluir os processos a cada segundo.
    """
    if not processos:
        return {"rss_mb": None, "cpu_pct": None}
    ticks = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
    def _utime_stime(p):
        try:
            data = open(f"/proc/{p.pid}/stat", encoding="utf-8").read()
            # "pid (comm) state ppid ...": o comm pode conter espacos e parenteses,
            # por isso devolvemos o que vem DEPOIS do ultimo ") ".
            tail = data.rsplit(") ", 1)[1]
            campos = tail.split()
            return int(campos[11]) + int(campos[12])  # utime, stime
        except Exception:
            return None

    inicio = time.monotonic()
    # RSS amostra rapida durante o intervalo; CPU somada em todo o grupo.
    rss_amostras = []
    t0 = sum((_utime_stime(p) or 0) for p in processos)
    while time.monotonic() - inicio < segundos:
        rss = []
        for p in processos:
            try:
                rss.append(mem_mb(p.memory_info().rss))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if rss:
            rss_amostras.append(sum(rss) / len(rss))
        time.sleep(1)
    t1 = sum((_utime_stime(p) or 0) for p in processos)
    wall = time.monotonic() - inicio
    if wall <= 0 or t0 == 0 or t1 == 0:
        return {"rss_mb": round(sum(rss_amostras) / len(rss_amostras), 1) if rss_amostras else None,
                "cpu_pct": None}
    cpu_delta = t1 - t0
    cpu_pct = round(cpu_delta / ticks / max(wall, 1e-6) * 100, 1)
    return {"rss_mb": round(sum(rss_amostras) / len(rss_amostras), 1),
            "cpu_pct": cpu_pct}


def portas_do_pid(pid):
    portas = set()
    if psutil is None:
        return sorted(portas)
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.pid == pid:
                portas.add(conn.laddr.port if conn.laddr else None)
                if conn.raddr:
                    portas.add(conn.raddr.port)
    except Exception:
        pass
    return sorted(int(p) for p in portas if p)


def ficheiros_do_pid(pid):
    contagem = 0
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            try:
                os.readlink(f"/proc/{pid}/fd/{fd}")
                contagem += 1
            except OSError:
                pass
    except OSError:
        pass
    return contagem


def disco(dirs):
    total = 0
    arquivos = 0
    for d in dirs:
        d = Path(d)
        if not d.exists():
            continue
        for dp, _, fns in os.walk(d):
            arquivos += len(fns)
            for f in fns:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
    return {"mb": round(total / 1024 / 1024, 1), "arquivos": arquivos}


def sistema():
    return {"cpu": psutil.cpu_count() or 0,
            "mem_total_mb": mem_mb(psutil.virtual_memory().total) if psutil else None,
            "sistema": os.uname().sysname if hasattr(os, "uname") else sys.platform}


# --------------------------------------------------------------------------- #
#  S1 - AnyDesk sozinho
# --------------------------------------------------------------------------- #
def run_s1(segundos=30):
    print("[S1] AnyDesk sozinho (daemon/tray, sem sessao ativa)...", flush=True)
    selecionados = processos_anydesk()
    if not selecionados:
        return {"erro": "Nenhum processo anydesk encontrado", "processos": []}
    print("  processos:", [(p.pid, " ".join(p.cmdline())) for p in selecionados], flush=True)
    amostras = rss_grupo(selecionados, segundos)
    resultado = {
        "escenario": "S1",
        "media_rss_mb": amostras["rss_mb"],
        "media_cpu_pct": amostras["cpu_pct"],
        "tempo_segundos": segundos,
        "processos": [{"pid": p.pid, "cmdline": " ".join(p.cmdline()),
                       "rss_mb": mem_mb(p.memory_info().rss),
                       "portas": portas_do_pid(p.pid),
                       "fds": ficheiros_do_pid(p.pid)}
                      for p in selecionados],
        "nota": "Qualquerco sozinho, sem sessao aberta. Sessao ativa exige janela X11 "
                "(medida no seu desktop, veja testes.md).",
    }
    print("  media rss %.1f MB, media cpu %.1f%%" % (
        resultado["media_rss_mb"] or 0, resultado["media_cpu_pct"] or 0), flush=True)
    return resultado


# --------------------------------------------------------------------------- #
#  S2 - Jogo do NaView isolado (navegador headless)
# --------------------------------------------------------------------------- #
def gerar_teste():
    """Gera web/jogo_teste.html (com window.TESTE) num temp dir. Volta (caminho, teste)."""
    sys.path.insert(0, str(ROOT))
    from jogo import catalogo as cat
    from jogo.pagina import catalogo_para_web

    tmp = Path("/tmp/naview-provisao")
    tmp.mkdir(exist_ok=True)

    estado = {
        "perfil": {"nivel": 1, "experiencia": 0, "nivel_proximo": 100,
                   "moedas": 0, "petiscos": 0, "baules_abertos": 0},
        "baus": [],
        "gratis": {"qtd": 1, "max": 1, "proximo_s": None},
        "diario": {"disponivel": True, "sequencia": 1, "dia": 1,
                   "calendario": [{"moedas": 10, "bau": None, "petiscos": None} for _ in range(7)],
                   "proximo_s": None},
        "pet": {"especie": "fredinho", "acessorio": None, "humor": "normal", "chocado": False,
                "fala": "Pet pronto", "enjelado": False},
        "cartas": {},
        "colecao": {"total": 0, "melhoradas": 0},
        "loja": {"itens": [], "ofertas": []},
    }
    catalogo = catalogo_para_web()
    teste = {"catalogo": catalogo, "estado": estado, "recompensa": {"moedas": 10, "bau": "madeira"}}
    (tmp / "teste.json").write_text(json.dumps(teste, ensure_ascii=False), encoding="utf-8")

    jogo_html = (ROOT / "web" / "jogo.html").read_text(encoding="utf-8")
    cabecalho = jogo_html.split("<body>")[0] + '<script>window.TESTE=' + json.dumps(teste) + "</script>"
    corpo = jogo_html.split("<body>")[1].rsplit("</body>", 1)[0]
    # A classe "pausado" sobre o <html> pausa TODAS as animacoes CSS (jogo.css regra
    # .pausado *), que e o mecanismo de pausa do app. Sem elevacao de prioridade.
    corpo_pausado = corpo.replace("<body",
                                  '<body class="pausado"><style>.pausado *{animation-play-state:paused!important}</style>')
    (tmp / "jogo_correndo.html").write_text(cabecalho + "<body>" + corpo + "\n</body></html>",
                                            encoding="utf-8")
    (tmp / "jogo_pausado.html").write_text(cabecalho + corpo_pausado + "\n</body></html>",
                                            encoding="utf-8")
    return tmp / "jogo_correndo.html", tmp / "jogo_pausado.html"


def lance_chrome(pagina):
    """Lanca o chrome headless com o jogo aberto; devolve o Popen (session leader)."""
    chrome = next((c for c in CHROMES if c), None)
    if not chrome:
        return None
    user_data = "/tmp/naview-bench-chrome-{}".format(int(time.time()) % 100000)
    args = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--disable-dev-shm-usage", "--virtual-time-budget=0",
            "--user-data-dir=" + user_data, "--no-first-run", "--no-referrers",
            "--disable-extensions", "--window-size=1280,820"]
    if pagina is not None:
        args.append(str(pagina))
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)


def matar_chrome(p):
    if p is None:
        return
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            p.kill()
        except Exception:
            pass
    try:
        p.wait(timeout=5)
    except Exception:
        pass


def run_s2(segundos=30):
    print("[S2] Jogo do NaView num navegador headless (em curso / pausado)...", flush=True)
    if not CHROMES:
        return {"erro": "Navegador nao encontrado (procure google-chrome ou chromium)",
                "escenario": "S2"}
    correndo, pausado = gerar_teste()
    print("  paginas geradas: %s / %s" % (correndo, pausado), flush=True)

    resultado = {"escenario": "S2", "paginas": [str(correndo), str(pausado)]}
    grupo = []

    # (a) navegador sozinho (baseline)
    p = lance_chrome(None)
    time.sleep(3)
    baseline = rss_grupo(ProcessoGrupo(p), segundos)
    resultado["chrome_solo"] = baseline
    matar_chrome(p)

    # (b) jogo em curso
    p = lance_chrome(correndo)
    time.sleep(3)
    em_curso = rss_grupo(ProcessoGrupo(p), segundos)
    resultado["em_curso"] = em_curso
    matar_chrome(p)

    # (c) jogo pausado
    p = lance_chrome(pausado)
    time.sleep(3)
    paus = rss_grupo(ProcessoGrupo(p), segundos)
    resultado["pausado"] = paus
    matar_chrome(p)

    resultado["diferenca_correndo_versus_pausado"] = {
        "rss_mb": round(em_curso["rss_mb"] - paus["rss_mb"], 1) if em_curso["rss_mb"] and paus["rss_mb"] else None,
        "cpu_pct": round(em_curso["cpu_pct"] - paus["cpu_pct"], 1) if em_curso["cpu_pct"] and paus["cpu_pct"] else None,
    }
    print("  chrome solo rss %s CPU %s | jogo correndo rss %s CPU %s | pausado rss %s CPU %s" % (
        baseline["rss_mb"], baseline["cpu_pct"],
        em_curso["rss_mb"], em_curso["cpu_pct"],
        paus["rss_mb"], paus["cpu_pct"]), flush=True)
    return resultado


# --------------------------------------------------------------------------- #
#  S3 - Arquitetura de processos (NaView vs AnyDesk) - no desktop do usuario
# --------------------------------------------------------------------------- #
def run_s3(segundos=60):
    print("[S3] Arquitetura de processos (NaView vs AnyDesk) - no desktop do usuario...", flush=True)
    return {"erro": "S3 exige o app aberto no desktop do usuario (testes.md).",
            "comando": "python3 ferramentas/provisao_uso.py --escenario S3 --segundos 60",
            "nota": "NaView = 1 processo app + N processos anydesk + WebKit no jogo. "
                    "AnyDesk = 1 processo por sessao. Medir no seu desktop."}


# --------------------------------------------------------------------------- #
#  S4 - Disco
# --------------------------------------------------------------------------- #
def run_s4(segundos=30):
    print("[S4] Disco do programa...", flush=True)
    return {
        "escenario": "S4",
        "disco": [
            {"rotulo": "repositorio de desenvolvimento (tudo)",
             "mb": round(disco([ROOT])["mb"], 1),
             "arquivos": sum(len(fns) for _, _, fns in os.walk(ROOT))},
            {"rotulo": "programa do Linux (fonte + arte + sons + fonts + web + icones)",
             "mb": round(disco([ROOT / "app.py", ROOT / "jogo", ROOT / "arte", ROOT / "sons",
                                ROOT / "fonts", ROOT / "icones", ROOT / "janelas",
                                ROOT / "plataforma.py", ROOT / "x11.py", ROOT / "contatos.py",
                                ROOT / "temas.py", ROOT / "jogo/progresso.py",
                                ROOT / "jogo/pagina.py", ROOT / "jogo/tela.py"])["mb"], 1),
             "arquivos": sum(len(fns) for d in (ROOT / "app.py", ROOT / "jogo", ROOT / "arte",
                                                ROOT / "sons", ROOT / "fonts", ROOT / "icones",
                                                ROOT / "janelas") for _, _, fns in os.walk(d))},
        ],
        "nota": "O programa distribuível e menor que o repositorio. No Windows o "
                "instalador e enxugado para caber nos 100 MB do GitHub (92,7 MB)."
    }


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Provisao do uso: NaView vs AnyDesk")
    ap.add_argument("--escenario", choices=["S1", "S2", "S3", "S4"], default="S1")
    ap.add_argument("--segundos", type=int, default=30)
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    resultado = {"S1": run_s1, "S2": run_s2, "S3": run_s3, "S4": run_s4}[args.escenario](args.segundos)

    relatorio = {
        "gerado_em": now_iso(),
        "maquina": sistema(),
        "escenario": args.escenario,
        "resultado": resultado,
        "comandos": {
            "S1": "python3 ferramentas/provisao_uso.py --escenario S1 --segundos 60",
            "S2": "python3 ferramentas/provisao_uso.py --escenario S2 --segundos 60",
            "S3": "python3 ferramentas/provisao_uso.py --escenario S3 --segundos 60  (no desktop do usuario)",
            "S4": "python3 ferramentas/provisao_uso.py --escenario S4",
        },
        "observacoes": [
            "Nenhum contato, progresso ou configuracao do usuario foi alterada.",
            "S1: mede o anydesk em daemon/tray (sem sessao). Sessao ativa exige "
            "janela X11 (medida no seu desktop).",
            "S2: jogo isolado num navegador headless, nao o WebKit do NaView. "
            "O .pausado pausa as animacoes CSS (o mecanismo do app).",
            "S3: mede o NaView aberto no seu desktop (veja testes.md).",
        ],
    }
    texto = json.dumps(relatorio, ensure_ascii=False, indent=2)
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
        print("salvo em", args.saida)
    else:
        print(texto)


if __name__ == "__main__":
    main()
