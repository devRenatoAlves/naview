# 01: App de abas

## Requisitos

- R1. Conectar a um cliente pelo ID ou pelo contato, e mostrar a sessão numa aba.
- R2. Várias sessões ao mesmo tempo, uma por aba, com troca rápida.
- R3. Fechar uma aba encerra a conexão. Fechar o app encerra todas, depois de pedir confirmação.
- R4. O teclado funciona normalmente dentro da sessão.
- R5. Contatos importados do AnyDesk, com busca, avatar e apelido próprio.
- R6. O nome da aba se atualiza sozinho: apelido, depois nome do computador, depois ID.
- R7. Barra de contatos retrátil.
- R8. Atalho no menu do KDE, com ícone próprio.

## Design

- **Encaixe:** o app GTK3 roda com `GDK_BACKEND=x11` e abre `anydesk <ID>` também com
  `GDK_BACKEND=x11`. A janela X11 nova é achada pelo PID (`_NET_WM_PID`) e pela classe, e
  encaixada com `Gtk.Socket.add_id` (`app.py`, `x11.py`).
- **Soltar a aba não é possível:** o AnyDesk fecha sozinho quando a janela sai do socket. Por
  isso, fechar uma aba envia SIGTERM ao PID da conexão.
- **Teclado:** o AnyDesk não usa XEMBED, então o `Gtk.Socket` não repassa bem as teclas.
  - O app manda o foco do X11 direto para a janela do AnyDesk, com `XSetInputFocus` a cada 80 ms
    (`manter_foco`).
  - Clicar num campo do app devolve o teclado ao app. Clicar na sessão (`clicked_inside`) devolve
    ao AnyDesk.
- **Contatos:** `contatos.py` lê `ad.roster.items` de `~/.anydesk/user.conf`. Os apelidos ficam em
  `~/.config/naview/contatos.json`.
- **Barra lateral:** um `Gtk.Revealer` num `Overlay` desliza por cima do conteúdo. A margem do
  conteúdo (`pilha.set_margin_start`) muda uma vez só, por desempenho. Ela acompanha a largura
  real da barra pelo sinal `size-allocate` (`_sincronizar_margem`), o que corrige a tela do jogo
  cortada quando o app abria com a barra aberta.
- **Atalhos:** F9 mostra ou esconde os contatos. Ctrl+F vai para a busca.
- **Inicialização:** `migrar_pastas_antigas()` renomeia `~/.config`, `~/.cache` e
  `~/.local/share/anydesk-tabs` para `naview` (só se a nova ainda não existir).
  `GLib.set_prgname("naview")` roda antes do Gtk. Depois vêm
  `fontes.carregar()` e `fontes.registrar_icones()`.
- **Instalação:** `instalar.sh` cria `~/.local/share/applications/naview.desktop` (com
  `StartupWMClass=naview`) e o ícone, e apaga o atalho e o ícone do nome antigo.

## Situação

- Pronto: R1 a R3 e R5 a R8.
- Pendente:
  - Testar com sessões remotas reais: teclado, atalhos, tela cheia e transferência de arquivos.
    Até agora só a janela principal do AnyDesk foi testada.
  - Conferir o formato do título da janela de sessão, de onde sai o nome do computador.
  - Atalhos para trocar de aba (Ctrl+Tab, Ctrl+1..9).
