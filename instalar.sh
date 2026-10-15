#!/usr/bin/env bash
# Instala o atalho do "NaView" no menu de aplicativos (KDE, GNOME e outros; só para o usuário atual)
# e avisa se falta alguma biblioteca do sistema. Não instala nada sozinho.
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

# Atualiza o cache de atalhos para o menu enxergar o novo atalho (KDE e GNOME/outros).
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null && update-desktop-database "$ATALHOS" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null \
  && gtk-update-icon-cache -q -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
echo "Atalho instalado: $ATALHOS/naview.desktop"

# Confere as bibliotecas usadas pelo app. Cada linha: módulo, versão, para que serve, pacote
# no Ubuntu/Debian e no Fedora.
faltando=0
while IFS='|' read -r modulo versao uso deb rpm; do
  if ! python3 -c "import gi; gi.require_version('$modulo', '$versao'); from gi.repository import $modulo" \
      >/dev/null 2>&1; then
    [ "$faltando" = 0 ] && echo && echo "Faltam bibliotecas:"
    faltando=1
    echo "  - $modulo $versao ($uso): Ubuntu/Debian: $deb | Fedora: $rpm"
  fi
done <<'LISTA'
Gtk|3.0|obrigatório|python3-gi gir1.2-gtk-3.0|python3-gobject gtk3
WebKit2|4.1|tela do jogo|gir1.2-webkit2-4.1|webkit2gtk4.1
Notify|0.7|avisos do jogo|gir1.2-notify-0.7|libnotify
Gst|1.0|sons do jogo|gir1.2-gstreamer-1.0 gstreamer1.0-plugins-good|gstreamer1 gstreamer1-plugins-good
LISTA
if ! command -v anydesk >/dev/null; then
  echo && echo "AnyDesk não encontrado: instale pelo site anydesk.com."
fi
if [ "$faltando" = 1 ]; then
  echo "Instale os pacotes acima (ex.: sudo apt install <pacotes>) e abra o NaView de novo."
fi
