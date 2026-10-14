#!/usr/bin/env bash
# Instala o atalho do "NaView" no menu do KDE (só para o usuário atual).
set -euo pipefail

PASTA="$(cd "$(dirname "$0")" && pwd)"
ICONES="$HOME/.local/share/icons/hicolor/scalable/apps"
ATALHOS="$HOME/.local/share/applications"

mkdir -p "$ICONES" "$ATALHOS"
# Remove o atalho e o ícone do nome antigo (AnyDesk em abas), se existirem.
rm -f "$ICONES/anydesk-tabs.svg" "$ATALHOS/anydesk-tabs.desktop"
cp "$PASTA/icone.svg" "$ICONES/naview.svg"

cat > "$ATALHOS/naview.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=NaView
Comment=Várias conexões do AnyDesk em abas numa única janela
Exec=python3 "$PASTA/app.py"
Path=$PASTA
Icon=naview
Terminal=false
Categories=Network;RemoteAccess;
StartupWMClass=naview
EOF

# Atualiza o cache de atalhos do KDE para o menu enxergar o novo atalho.
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
echo "Atalho instalado: $ATALHOS/naview.desktop"
