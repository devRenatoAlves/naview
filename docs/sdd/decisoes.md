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
| D21 | (15/10/2026) No topo da página, trocar de tema muda só a aparência: a altura do título é reservada pelo JS (maior altura entre os temas) e a janela tem tamanho fixo | O layout pulava até 118 px a cada troca, e no celular a carta tocada saía do lugar |
