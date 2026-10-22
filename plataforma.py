"""O que muda entre Linux e Windows: pastas de dados, onde está o AnyDesk e o arquivo de contatos.

No Linux os caminhos são os mesmos de sempre (~/.config/naview, ~/.cache/naview,
~/.local/share/naview), para não perder nada de quem já usa o app.
"""
import os
import shutil
import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"
LINUX = sys.platform.startswith("linux")

if WINDOWS:
    _roaming = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    _local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    CONFIG = _roaming / "NaView"
    CACHE = _local / "NaView" / "cache"
    DADOS = _local / "NaView"
    ANYDESK_CONF = _roaming / "AnyDesk" / "user.conf"
    _dados_comuns = Path(os.environ.get("ProgramData") or "C:/ProgramData")
    ANYDESK_CONFS_ID = [_dados_comuns / "AnyDesk" / "system.conf", _roaming / "AnyDesk" / "system.conf",
                        _roaming / "AnyDesk" / "user.conf"]
else:
    CONFIG = Path.home() / ".config" / "naview"
    CACHE = Path.home() / ".cache" / "naview"
    DADOS = Path.home() / ".local" / "share" / "naview"
    ANYDESK_CONF = Path.home() / ".anydesk" / "user.conf"
    ANYDESK_CONFS_ID = [Path("/etc/anydesk/system.conf"), Path.home() / ".anydesk" / "system.conf",
                        Path.home() / ".anydesk" / "service.conf", ANYDESK_CONF]


def anydesk():
    """Caminho do programa do AnyDesk, ou None se não estiver instalado."""
    if not WINDOWS:
        return shutil.which("anydesk")
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base and Path(base, "AnyDesk", "AnyDesk.exe").is_file():
            return str(Path(base, "AnyDesk", "AnyDesk.exe"))
    # Versão portátil, baixada e aberta sem instalar.
    for pasta in (Path.home() / "Downloads", Path.home() / "Desktop"):
        if pasta.is_dir():
            for exe in sorted(pasta.glob("AnyDesk*.exe")):
                return str(exe)
    return shutil.which("AnyDesk")
