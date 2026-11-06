# NaView

Junta várias conexões do AnyDesk em abas, numa única janela (Linux; versão para Windows em teste).

## Como funciona

- O app e o AnyDesk rodam pelo X11/XWayland (`GDK_BACKEND=x11`). Isso permite encaixar a janela do
  AnyDesk dentro de uma aba (`Gtk.Socket`).
- **Contatos** (barra lateral): importados do catálogo do AnyDesk (`ad.roster.items` em
  `~/.anydesk/user.conf`), com busca e avatar colorido. O lápis renomeia num balão (na aba aberta, dois cliques rápidos na identificação abrem o mesmo balão); o nome fica
  salvo em `~/.config/naview/contatos.json` (o arquivo do AnyDesk não é alterado). A lista mostra
  primeiro os conectados, depois os usados recentemente.
- **Conectar**: dois cliques (ou Enter) no contato, ID na busca + Enter, o campo da tela inicial ou
  um dos **Recentes** (as 5 últimas conexões, abaixo do campo). Roda `anydesk <ID>` e encaixa a
  janela que esse processo abrir. Contato já conectado: só troca de aba. Se a busca achar vários
  contatos, o Enter seleciona o primeiro na lista em vez de conectar.
- **Abas**: bolinha com a cor do contato, nome atualizado a cada 2 s (apelido > nome do
  computador no título da janela > ID), arrastar para reordenar, **×** ou botão do meio do mouse
  encerra a conexão (sessão aberta há mais de 5 min pede confirmação), **+** abre a busca para uma
  nova conexão.
- **Teclado**: com uma sessão na tela, o foco do teclado do X11 vai direto para a janela do
  AnyDesk (o `Gtk.Socket` não repassa bem as teclas, porque o AnyDesk não usa XEMBED). Clicar num
  campo ou na lista de contatos devolve o teclado ao app; clicar na tela da sessão devolve ao AnyDesk.
- **Atalhos** (quando o teclado está no app): F9 mostra/esconde contatos, Ctrl+F vai para a busca.
- **Botão de janela na barra de título (Capturar janela do AnyDesk…)**: encaixa uma janela do AnyDesk já aberta (precisa ter
  sido aberta com `GDK_BACKEND=x11`).
- Fechar o app encerra todas as conexões, depois de pedir confirmação.

## Temas

O tema se escolhe no jogo (botão de presente na barra de título > Coleção > Usar). As opções de aparência (intensidade do vidro, desenhos e animações) saíram da tela; os valores salvos continuam valendo. Tudo aplica na hora e fica salvo em
`~/.config/naview/config.json`.

| Tema | O que muda |
|---|---|
| Padrão, Grafite, Claro, Oceano | Cores |
| Vidro líquido | Janela transparente com desfoque (quando o sistema oferece), painéis com brilho e borda clara; intensidade ajustável |
| Aventura Pixel | Fonte Press Start 2P, bordas grossas, monstrinhos em pixel art, grama e nuvens |
| Heróis HQ | Fonte Bangers, retícula de pontos, explosões "POW!"/"ZAP!", cidade e emblema |
| Espaço | Fonte Orbitron, estrelas, planeta e foguete |
| Terminal | Fonte VT323, fósforo verde, linhas de varredura e cursor piscando |
| Neon 80s | Fonte Audiowide, sol retrô, montanhas e grade neon |
| Mangá Noir | Preto e branco, fonte Zen Dots, wallpaper de anime em preto e branco e ícone do app próprio |
| Alto-mar | Fonte Fredoka, cores da logo, o veleiro do NaView balançando, farol piscando, sol poente, gaivotas e ondas |

Opções por cima de qualquer tema: desenhos e animações (podem ser desligados) e, no vidro, a
intensidade.

- Desenhos e animações só existem na tela inicial; com uma sessão aberta nada fica animando.
- Desempenho (GTK3 desenha tudo no processador): a barra lateral desliza por cima do conteúdo e
  o conteúdo muda de largura uma vez só; nada de `radial-gradient` nem sombras com desfoque
  grande no CSS (recalculados a cada quadro); a imagem de fundo é reduzida para no máximo
  1920x1080 em `~/.cache/naview`.
- Toda a arte é original e gerada por `ferramentas/gerar_arte.py` (saída em `arte/`).
- Fontes em `fonts/` (licença OFL, arquivos `OFL-*.txt`), carregadas só para o app por
  `fontes.py`, sem instalar no sistema.
- O desfoque do vidro usa `_KDE_NET_WM_BLUR_BEHIND_REGION`, e a força dele é uma configuração
  do sistema. Onde o sistema não desfoca, o vidro fica com o fundo mais escuro, para o texto
  continuar legível.

## Jogo: baús, coleção e pet

Botão de presente na barra de título (a bolinha vermelha conta as novidades). Abre dentro da
janela, sem fechar as sessões. Tudo local, em `~/.local/share/naview/progresso.db`. Fechado há
10 min, o jogo sai da memória (reabrir leva um instante a mais).

- **Cartas** (38): temas, pets, acessórios do pet, molduras dos avatares e sons de conexão, em 4
  raridades (Comum, Rara, Épica, Lendária) e a Mítica, só para os temas mais elaborados
  (Aventura Pixel, Heróis HQ e Mangá Noir; Espaço, Neon e Alto-mar são Lendários). Cópias repetidas + moedas sobem o nível (até 5). Tema
  no nível 5 ganha a versão dourada. Temas que você não tem ficam bloqueados na Coleção.
- **Baús**: 4 espaços; um baú de trabalho a cada 10 atendimentos (sessões de 3 min ou mais; o mesmo ID conta no máximo 2 vezes em 24 h). Cada
  baú leva um tempo para destravar (15 min a 8 h) ou abre na hora pagando moedas. Baú grátis a
  cada 8 h (acumula 1). Garantia de lendária a cada 40 baús.
- **Nível da conta**: sobe com XP (atendimentos, baús abertos, cartas melhoradas). Não dá prêmio:
  é só comemoração, como conquista de videogame.
- **Recompensa diária**: calendário de 7 dias; fim de semana não quebra a sequência.
- **Loja**: 3 ofertas por dia (comum, rara e uma especial), sorteadas aleatoriamente para cada
  usuário, com a ordem embaralhada a cada renovação; petiscos custam 15 moedas.
- **Pet (Tamagotchi)**: nasce de um ovo, tem comida, alegria e energia que caem com o tempo,
  dorme quando o app está fechado, come petiscos, brinca, tira soneca, cresce (bebê, jovem,
  adulto) e usa acessórios. Guarda-roupa separado em Espécies e Acessórios. O nome é sempre o da espécie (não dá para renomear). Fica no rodapé da barra de contatos.
  12 espécies: slime, galinha, Fredinho, gato preto, Jonatas, Ronaldo, astronauta, serpente de gelo e
  quatro Pokémon. Gato, Jonatas, astronauta e serpente de gelo andam (animação do GIF) na tela do pet.
- **Avisos**: notificação do sistema quando um baú fica pronto e para a recompensa diária.

Arquitetura: `jogo/progresso.py` guarda tudo e faz todos os sorteios; a tela (`web/jogo.html`,
`jogo.css`, `jogo.js`, com GSAP e canvas-confetti) só pede ações e desenha. Para levar a um
servidor da equipe, basta trocar `Progresso` por uma classe com os mesmos métodos que chame a API.

## Arquivos

- `app.py`: janela, abas, contatos, conexões e foco do teclado.
- `temas.py`: definição dos temas, preferências e geração do CSS.
- `janela_aparencia.py`: galeria de temas e opções.
- `contatos.py`: leitura dos contatos do AnyDesk e apelidos.
- `x11.py`: acesso à libX11 (listar janelas, PID, foco, desfoque).
- `fontes.py`, `fonts/`, `arte/`, `ferramentas/gerar_arte.py`: fontes e desenhos dos temas e do jogo
  (Fredinho e Ronaldo em `ferramentas/desenhos_pets.py`; os pets de GIF e PNG em
  `ferramentas/importar_pets.py`; sprites dos Pokémon por `ferramentas/baixar_sprites.py`).
- `jogo/catalogo.py` (cartas, baús, regras), `jogo/progresso.py` (motor e banco),
  `jogo/tela.py` (página do jogo no WebKitGTK), `jogo/gtk.py` (pet no rodapé, sons, notificações).
- `web/`: página do jogo; `web/vendor/`: GSAP 3.12.5 e canvas-confetti 1.9.3.
- `sons/`, `ferramentas/gerar_sons.py`: sons sintetizados do jogo.
- `ferramentas/simular_economia.py`: simula meses de uso para medir o ritmo das recompensas.
- `icones/phosphor/`: ícones Phosphor Icons 2.1.1 (licença MIT, `LICENSE`), estilo preenchido.
  `ferramentas/gerar_icones.py` gera `web/icones.js` (página do jogo) e `icones/gtk/ph-*-symbolic.svg`
  (app GTK, pintados com a cor do texto do tema). A interface não usa emojis.
- `VERSAO`: versão do app (formato `AAAA.MM.DD.N`, ex.: `2026.10.22.1`). Rode
  `python3 ferramentas/nova_versao.py` antes de cada push que deva chegar aos usuários.
- `atualizador.py`: consulta o site, baixa e aplica a atualização (ver abaixo).
- `site/fonte/`: página de apresentação com download. `python3 ferramentas/gerar_site.py` monta
  `site/publico/` (página + `download/naview-<versão>.tar.gz`); `site/Dockerfile` serve com nginx.

## Rodar

```bash
python3 app.py
```

Para criar o atalho no menu de aplicativos (com ícone), rode uma vez:

```bash
./instalar.sh
```

O script também avisa se falta alguma biblioteca e mostra o pacote para instalar.

### Versão nova (Qt, Linux e Windows), em teste

```bash
sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtsvg python3-pyside6.qtwebenginewidgets \
  python3-pyside6.qtwebchannel python3-pyside6.qtmultimedia python3-pyside6.qtdbus
python3 app_qt.py
```

Usa os mesmos contatos, temas e progresso do `app.py`; não abra os dois ao mesmo tempo. No
Windows, o instalador `NaView-instalador.exe` é montado pelo GitHub Actions
(`.github/workflows/windows.yml`) e baixado pela página, na aba Windows da seção de instalação.

Depois é só procurar "NaView" no menu. Para fixar na barra de tarefas, clique com o botão
direito no ícone e escolha a opção de fixar.

Requisitos: Python 3, PyGObject (GTK 3), libX11 e AnyDesk. O jogo usa também WebKit2GTK 4.1,
libnotify e GStreamer. No Ubuntu e derivados:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-notify-0.7 \
  gir1.2-gstreamer-1.0 gstreamer1.0-plugins-good
```

Sem o WebKit, o app funciona normalmente e só o jogo fica indisponível (aparece um aviso).

## Atualizações

O NaView confere o site 30 s depois de abrir e a cada 6 horas. Havendo versão nova, aparece o botão
**Atualizar** na barra: ele baixa, confere o arquivo, fecha o app e abre de novo já atualizado (no
Windows roda o instalador sozinho). Suas configurações e seu progresso não são tocados. Se a pasta
do NaView não permitir a troca, o botão abre a página de download. Quem tem uma versão anterior a
esta precisa baixar o NaView de novo uma vez.

## Limitações conhecidas

- Não dá para "soltar" a aba de volta como janela separada: o AnyDesk fecha sozinho quando a
  janela sai do encaixe (testado no AnyDesk 8.1.0).
- Testado só com a janela principal do AnyDesk. Falta testar com sessões remotas de verdade.
- Sem o pacote `python3-gi-cairo`, os desenhos não ficam mais nítidos em telas HiDPI.

## Documentação do projeto (SDD)

Especificações, decisões e tarefas ficam em [`docs/sdd/`](docs/sdd/README.md). A lista de tarefas
está em [`docs/sdd/tarefas.md`](docs/sdd/tarefas.md).
