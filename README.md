# NaView

Junta várias conexões do AnyDesk em abas, numa única janela (Linux / KDE Wayland).

## Como funciona

- O app e o AnyDesk rodam pelo XWayland (`GDK_BACKEND=x11`). Isso permite encaixar a janela do
  AnyDesk dentro de uma aba (`Gtk.Socket`).
- **Contatos** (barra lateral): importados do catálogo do AnyDesk (`ad.roster.items` em
  `~/.anydesk/user.conf`), com busca e avatar colorido. O lápis renomeia num balão; o nome fica
  salvo em `~/.config/naview/contatos.json` (o arquivo do AnyDesk não é alterado).
- **Conectar**: dois cliques no contato, ID na busca + Enter, ou o campo da tela inicial. Roda
  `anydesk <ID>` e encaixa a janela que esse processo abrir. Contato já conectado: só troca de aba.
- **Abas**: bolinha com a cor do contato, nome atualizado a cada 2 s (apelido > nome do
  computador no título da janela > ID), arrastar para reordenar, **×** ou botão do meio do mouse
  encerra a conexão, **+** abre a busca para uma nova conexão.
- **Teclado**: com uma sessão na tela, o foco do teclado do X11 vai direto para a janela do
  AnyDesk (o `Gtk.Socket` não repassa bem as teclas, porque o AnyDesk não usa XEMBED). Clicar num
  campo do app devolve o teclado ao app; clicar na tela da sessão devolve ao AnyDesk.
- **Atalhos** (quando o teclado está no app): F9 mostra/esconde contatos, Ctrl+F vai para a busca.
- **Menu > Capturar janela do AnyDesk…**: encaixa uma janela do AnyDesk já aberta (precisa ter
  sido aberta com `GDK_BACKEND=x11`).
- Fechar o app encerra todas as conexões, depois de pedir confirmação.

## Temas

Botão de aparência na barra de título (ou Menu > Aparência e temas…). Tudo aplica na hora e fica
salvo em `~/.config/naview/config.json`.

| Tema | O que muda |
|---|---|
| Padrão, Grafite, Claro, Oceano | Cores |
| Vidro líquido | Janela transparente com o desfoque do KWin (`_KDE_NET_WM_BLUR_BEHIND_REGION`), painéis com brilho e borda clara; intensidade ajustável |
| Aventura Pixel | Fonte Press Start 2P, bordas grossas, monstrinhos em pixel art, grama e nuvens |
| Heróis HQ | Fonte Bangers, retícula de pontos, explosões "POW!"/"ZAP!", cidade e emblema |
| Espaço | Fonte Orbitron, estrelas, planeta e foguete |
| Terminal | Fonte VT323, fósforo verde, linhas de varredura e cursor piscando |
| Neon 80s | Fonte Audiowide, sol retrô, montanhas e grade neon |
| Alto-mar | Fonte Fredoka, cores da logo, o veleiro do NaView balançando, farol piscando, sol poente, gaivotas e ondas |

Ajustes por cima de qualquer tema: cores (destaque, fundo, barra de contatos, barra de título),
imagem de fundo da tela inicial, desenhos e animações (podem ser desligados).

- Desenhos e animações só existem na tela inicial; com uma sessão aberta nada fica animando.
- Desempenho (GTK3 desenha tudo no processador): a barra lateral desliza por cima do conteúdo e
  o conteúdo muda de largura uma vez só; nada de `radial-gradient` nem sombras com desfoque
  grande no CSS (recalculados a cada quadro); a imagem de fundo é reduzida para no máximo
  1920x1080 em `~/.cache/naview`.
- Toda a arte é original e gerada por `ferramentas/gerar_arte.py` (saída em `arte/`).
- Fontes em `fonts/` (licença OFL, arquivos `OFL-*.txt`), carregadas só para o app por
  `fontes.py`, sem instalar no sistema.
- A força do desfoque é uma configuração global do KDE (Configurações do sistema > Efeitos da
  área de trabalho > Desfoque).

## Jogo: baús, coleção e pet

Botão de presente na barra de título (a bolinha vermelha conta as novidades). Abre dentro da
janela, sem fechar as sessões. Tudo local, em `~/.local/share/naview/progresso.db`.

- **Cartas** (31): temas, pets, acessórios do pet, molduras dos avatares e sons de conexão, em 4
  raridades (Comum, Rara, Épica, Lendária) e a Mítica, só para os temas mais elaborados
  (Aventura Pixel e Heróis HQ; Espaço, Neon e Alto-mar são Lendários). Cópias repetidas + moedas sobem o nível (até 5). Tema
  no nível 5 ganha a versão dourada. Temas que você não tem ficam bloqueados na Aparência.
- **Baús**: 4 espaços; um baú de trabalho a cada 10 atendimentos (sessões de 3 min ou mais). Cada
  baú leva um tempo para destravar (15 min a 8 h) ou abre na hora pagando moedas. Baú grátis a
  cada 8 h (acumula 1). Garantia de lendária a cada 40 baús.
- **Nível da conta**: sobe com XP (atendimentos, baús abertos, cartas melhoradas). Não dá prêmio:
  é só comemoração, como conquista de videogame.
- **Recompensa diária**: calendário de 7 dias; fim de semana não quebra a sequência.
- **Loja**: 3 ofertas por dia e petiscos.
- **Pet (Tamagotchi)**: nasce de um ovo, tem comida, alegria e energia que caem com o tempo,
  dorme quando o app está fechado, come petiscos, brinca, tira soneca, cresce (bebê, jovem,
  adulto) e usa acessórios. Guarda-roupa separado em Espécies e Acessórios; botão de renomear. Fica no rodapé da barra de contatos.
- **Avisos**: notificação do KDE quando um baú fica pronto e para a recompensa diária.

Arquitetura: `jogo/progresso.py` guarda tudo e faz todos os sorteios; a tela (`web/jogo.html`,
`jogo.css`, `jogo.js`, com GSAP e canvas-confetti) só pede ações e desenha. Para levar a um
servidor da equipe, basta trocar `Progresso` por uma classe com os mesmos métodos que chame a API.

## Arquivos

- `app.py`: janela, abas, contatos, conexões e foco do teclado.
- `temas.py`: definição dos temas, preferências e geração do CSS.
- `janela_aparencia.py`: galeria de temas e ajustes.
- `contatos.py`: leitura dos contatos do AnyDesk e apelidos.
- `x11.py`: acesso à libX11 (listar janelas, PID, foco, desfoque).
- `fontes.py`, `fonts/`, `arte/`, `ferramentas/gerar_arte.py`: fontes e desenhos dos temas.
- `jogo/catalogo.py` (cartas, baús, regras), `jogo/progresso.py` (motor e banco),
  `jogo/tela.py` (página do jogo no WebKitGTK), `jogo/gtk.py` (pet no rodapé, sons, notificações).
- `web/`: página do jogo; `web/vendor/`: GSAP 3.12.5 e canvas-confetti 1.9.3.
- `sons/`, `ferramentas/gerar_sons.py`: sons sintetizados do jogo.
- `ferramentas/simular_economia.py`: simula meses de uso para medir o ritmo das recompensas.
- `icones/phosphor/`: ícones Phosphor Icons 2.1.1 (licença MIT, `LICENSE`), estilo preenchido.
  `ferramentas/gerar_icones.py` gera `web/icones.js` (página do jogo) e `icones/gtk/ph-*-symbolic.svg`
  (app GTK, pintados com a cor do texto do tema). A interface não usa emojis.
- `VERSAO`: versão do app (formato data, ex.: `2026.10.14`).
- `site/fonte/`: página de apresentação com download. `python3 ferramentas/gerar_site.py` monta
  `site/publico/` (página + `download/naview-<versão>.tar.gz`); `site/Dockerfile` serve com nginx.

## Rodar

```bash
python3 app.py
```

Para criar o atalho no menu do KDE (com ícone), rode uma vez:

```bash
./instalar.sh
```

Depois é só procurar "NaView" no menu e, para fixar na barra de tarefas, clicar com o
botão direito no ícone > "Fixar no Gerenciador de tarefas".

Requisitos: Python 3, PyGObject (GTK 3), libX11 e AnyDesk. Não precisa instalar nada além disso.

## Limitações conhecidas

- Não dá para "soltar" a aba de volta como janela separada: o AnyDesk fecha sozinho quando a
  janela sai do encaixe (testado no AnyDesk 8.1.0).
- Testado só com a janela principal do AnyDesk. Falta testar com sessões remotas de verdade.
- Sem o pacote `python3-gi-cairo`, os desenhos não ficam mais nítidos em telas HiDPI.

## Documentação do projeto (SDD)

Especificações, decisões e tarefas ficam em [`docs/sdd/`](docs/sdd/README.md). A lista de tarefas
está em [`docs/sdd/tarefas.md`](docs/sdd/tarefas.md).
