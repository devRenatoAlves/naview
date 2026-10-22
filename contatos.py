"""Contatos: importados do AnyDesk (user.conf, ver plataforma.py) + apelidos salvos pelo app."""
import json
import subprocess

import plataforma

ANYDESK_CONF = plataforma.ANYDESK_CONF
ARQUIVO = plataforma.CONFIG / "contatos.json"


def formatar_id(anydesk_id):
    """'1270225788' -> '1 270 225 788' (mesmo formato que o AnyDesk mostra)."""
    if not anydesk_id.isdigit():
        return anydesk_id
    grupos = []
    while anydesk_id:
        grupos.insert(0, anydesk_id[-3:])
        anydesk_id = anydesk_id[:-3]
    return " ".join(grupos)


MAX_RECENTES = 5
_cache_anydesk = (None, [])  # (data de modificação do user.conf, itens lidos)


def ler_anydesk():
    """Lista de (id, apelido) do catálogo do AnyDesk.

    Só relê o arquivo quando ele muda: o nome das abas é consultado a cada 2 s.
    """
    global _cache_anydesk
    try:
        mtime = ANYDESK_CONF.stat().st_mtime_ns
    except OSError:
        return []
    if _cache_anydesk[0] != mtime:
        _cache_anydesk = (mtime, _ler_arquivo())
    return _cache_anydesk[1]


def _ler_arquivo():
    """Formato da chave ad.roster.items: 'id,endereço,apelido,...;id,endereço,apelido,...'"""
    try:
        linhas = ANYDESK_CONF.read_text(errors="replace").splitlines()
    except OSError:
        return []
    for linha in linhas:
        if linha.startswith("ad.roster.items="):
            itens = []
            for entrada in linha.split("=", 1)[1].split(";"):
                campos = entrada.split(",")
                if campos and campos[0].strip():
                    apelido = campos[2].strip() if len(campos) > 2 else ""
                    itens.append((campos[0].strip(), apelido))
            return itens
    return []


def meu_id():
    """ID do AnyDesk deste computador (chave ad.anynet.id dos arquivos de configuração), ou ''."""
    for arquivo in plataforma.ANYDESK_CONFS_ID:
        try:
            linhas = arquivo.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for linha in linhas:
            if linha.startswith("ad.anynet.id="):
                valor = linha.split("=", 1)[1].strip()
                if valor.isdigit():
                    return valor
    return ""


def meu_id_pelo_programa():
    """Pergunta o ID ao próprio AnyDesk (anydesk --get-id). Lento: chamar fora da interface."""
    exe = plataforma.anydesk()
    if not exe:
        return ""
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if plataforma.WINDOWS else {}
    try:
        saida = subprocess.run([exe, "--get-id"], capture_output=True, text=True, timeout=8,
                               **extra).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    return saida if saida.isdigit() else ""


class Contatos:
    def __init__(self):
        self.apelidos = {}  # id -> apelido definido no app
        self.recentes = []  # IDs das últimas conexões, o mais recente primeiro
        try:
            dados = json.loads(ARQUIVO.read_text())
            self.apelidos = dados.get("apelidos", {})
            self.recentes = dados.get("recentes", [])[:MAX_RECENTES]
        except (OSError, ValueError):
            pass

    def listar(self):
        """[(id, nome)] com AnyDesk + apelidos do app, sem repetir IDs."""
        vistos, saida = set(), []
        for cid, apelido in ler_anydesk():
            if cid not in vistos:
                vistos.add(cid)
                saida.append((cid, self.apelidos.get(cid) or apelido))
        # Contatos que só existem no app (ex.: ID digitado e renomeado aqui).
        for cid, apelido in self.apelidos.items():
            if cid not in vistos:
                saida.append((cid, apelido))
        return saida

    def nome(self, cid):
        return self.apelidos.get(cid) or dict(ler_anydesk()).get(cid) or ""

    def renomear(self, cid, apelido):
        if apelido:
            self.apelidos[cid] = apelido
        else:
            self.apelidos.pop(cid, None)
        self._salvar()

    def usar(self, cid):
        """Marca o contato como conectado agora (lista de recentes da tela inicial)."""
        self.recentes = [cid] + [r for r in self.recentes if r != cid][:MAX_RECENTES - 1]
        self._salvar()

    def _salvar(self):
        ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO.write_text(json.dumps({"apelidos": self.apelidos, "recentes": self.recentes},
                                      ensure_ascii=False, indent=2))
