# Decisões

Registro curto: o que foi decidido, por quê e quando. As mais novas ficam no fim.

| # | Decisão | Por quê |
|---|---|---|
| D1 | App e AnyDesk rodam pelo XWayland (`GDK_BACKEND=x11`) | No Wayland puro não dá para encaixar a janela de outro programa |
| D2 | Fechar aba = SIGTERM no PID da conexão; sem "soltar aba" | O AnyDesk 8.1.0 fecha sozinho quando a janela sai do socket |
| D3 | Foco do X11 forçado na janela do AnyDesk a cada 80 ms | O AnyDesk não usa XEMBED, e o `Gtk.Socket` não repassa as teclas |
| D4 | Animações só na tela inicial; sem `radial-gradient` nem sombras grandes no CSS do GTK | O GTK3 desenha no processador e pesava com sessão aberta |
| D5 | Barra lateral sobreposta (Overlay + Revealer), margem do conteúdo aplicada uma vez | Mudar a largura do conteúdo a cada quadro travava a animação |
| D6 | Fontes e ícones carregados só para o app, sem instalar no sistema | Não mexer no sistema do usuário |
| D7 | Ícones Phosphor (MIT) e nenhum emoji na interface | Visual consistente; pedido do usuário |
| D8 | Tela do jogo em WebKit (HTML, CSS e JS), regras em Python | Animações ricas são mais fáceis na web; as regras ficam num só lugar |
| D9 | `Progresso` concentra todas as regras e sorteios, com métodos públicos estáveis | Permite trocar por um servidor sem mexer na tela |
| D10 | (14/10/2026) Ritmo lento: baú a cada 10 atendimentos, menos cartas por baú, loja mais cara | A demanda de trabalho é alta; com o ritmo antigo, a coleção acabava em 3 a 6 semanas |
| D11 | (14/10/2026) Nível da conta sem prêmio, só comemoração | Pedido do usuário: "igual conquista de videogame" |
| D12 | (14/10/2026) Servidor com regras e sorteios no servidor (não só backup) | Haverá prêmios reais e ranking; cópia em pasta ou backup permitiria trapaça |
| D13 | (14/10/2026) Servidor em Python reaproveitando `jogo/progresso.py`, na VPS do usuário | Não reescrever as regras; 10 usuários cabem num SQLite |
| D14 | (14/10/2026) Atendimentos conferidos pela API do AnyDesk (se o plano permitir) | O app sozinho pode ser enganado abrindo e fechando sessões |
| D15 | (14/10/2026) Projeto renomeado de "AnyDesk em abas" (`anydesk-tabs`) para NaView (`naview`); o app renomeia as pastas de dados antigas na primeira abertura | Pedido do usuário; a migração evita perder contatos, configuração e progresso |
| D16 | (14/10/2026) Ícone: letra R formada por um veleiro (mastro = haste, vela grande = curva, vela da frente = perna) sobre casco e ondas | Pedido do usuário; combina com o nome NaView |
| D17 | (14/10/2026) Página de apresentação estática, com o download servido pelo próprio site, publicada pelo Coolify | Pedido do usuário; site estático é leve e não precisa de servidor com lógica |
| D17 | (14/10/2026) Tema lendário Alto-mar com as cores da logo e fonte Fredoka (OFL) | Pedido do usuário: tema de barco e mar com a marca; Fredoka é arredondada como o R da logo |
| D18 | (14/10/2026) Versão do app no arquivo `VERSAO`, no formato data (`2026.10.14`); pacote `.tar.gz` gerado por `ferramentas/gerar_site.py` | O app não tinha versão; data é simples e mostra quando foi gerado |
| D19 | (14/10/2026) Página no tema Alto-mar, com a janela de demonstração e as cartas de tema como destaque | Mostra o app de verdade e liga os temas ao jogo; a sugestão laranja e creme do `ui-ux-pro-max` foi descartada por ser genérica |
| D18 | (14/10/2026) 7 pets novos: 3 cachorros (pinscher caramelo, corgi, salsicha), passarinho e 3 Pokémon (Pikachu lendário; Eevee e Jigglypuff épicos) | Pedido do usuário. Pokémon são da Nintendo: arte de fã só para uso interno da equipe, sem divulgar o app |
| D20 | (14/10/2026) Página hospedada na VPS pelo Coolify, a partir de repositório privado no GitHub; o contêiner gera o site ao ser montado | Pedido do usuário; o plano gratuito do Vercel não permite uso comercial e a VPS já existe |
| D19 | (14/10/2026) Pets em pixel art 64 x 64 (antes 16 x 16): Pokémon com os sprites oficiais e os demais desenhados em camadas vetoriais convertidas em pixels; acessórios com encaixe em (x, y) | O usuário achou a arte 16 x 16 fraca e pediu algo como os sprites dos jogos; os sprites oficiais são os mais fiéis (uso interno, ver D18) |
| D20 | (14/10/2026) Opção `liberar_tudo` no config.json: todas as cartas ao abrir o app | Pedido do usuário para testar. Só vale para o progresso local; com o servidor (fase 1), quem decide as cartas é o servidor, e essa opção não pode valer lá |
| D21 | (15/10/2026) No topo da página, trocar de tema muda só a aparência: a altura do título é reservada pelo JS (maior altura entre os temas) e a janela tem tamanho fixo | O layout pulava até 118 px a cada troca, e no celular a carta tocada saía do lugar |
| D22 | (15/10/2026) Foco forçado a cada 120 ms (antes 80, ver D3), sem consultar o X11 de novo quando o foco não mudou | Menos consultas por segundo; 120 ms ainda é imperceptível ao clicar na sessão |
| D23 | (15/10/2026) Trocar de tema mantém a imagem de fundo escolhida, com aviso | A imagem sumia sem aviso (o usuário usa o tema pixel com imagem própria) |
| D24 | (15/10/2026) Jogo destruído após 10 min fechado; a página desenha só a tela visível | Leveza: o WebKit ocupa 100 MB ou mais, e redesenhar 4 telas a cada minuto era desperdício |
| D25 | (15/10/2026) Fechar aba de sessão com mais de 5 min pede confirmação; Aparência só no menu ⋮ | Fechar derruba o cliente; o botão de paleta repetia o item do menu |
| D26 | (15/10/2026) Windows: programa idêntico, com um código só em Qt (PySide6) para os dois sistemas, depois de um teste de viabilidade no Windows | Pedido do usuário. O GTK3 não tem WebKit no Windows e o `Gtk.Socket` só existe no X11; o Qt encaixa janelas e mostra páginas web nos dois. O encaixe no Windows não tem suporte oficial, então ele é testado antes de reescrever |
| D27 | (15/10/2026) Piloto Windows montado pelo GitHub Actions e servido pelo próprio site, numa página não divulgada (`/piloto/`); o zip fica no repositório | O PyInstaller não monta `.exe` a partir do Linux; o repositório é privado, então um arquivo publicado nele não pode ser baixado; a arte de Pokémon é só para uso interno (D18) |
| D28 | (15/10/2026) App para qualquer ambiente Linux, não só o KDE: continua no X11/XWayland; fora do KDE o vidro fica sem desfoque e mais opaco; o instalador só avisa o que falta, sem instalar | Pedido do usuário. GNOME e os outros também têm XWayland, então o encaixe não muda; só o desfoque é do KWin. Instalar pacotes exigiria senha de administrador e varia por distribuição |
| D29 | (15/10/2026) Uma página e um pacote só para qualquer Linux; textos dizem só "Linux" | O teste no GNOME funcionou; separar por ambiente não traz nada ao usuário |
| D30 | (16/10/2026) Fase 0 do Windows aprovada: o encaixe será o do Qt (`QWindow.fromWinId` + `createWindowContainer`), uma sessão por processo do AnyDesk, fechar com `WM_CLOSE` e sem foco forçado no Windows | O piloto passou em todos os itens no Windows 11 do usuário, sem "Forçar foco". Faltam testar escala acima de 100% e o NaView sem administrador |
