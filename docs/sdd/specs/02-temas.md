# 02: Temas e aparência

## Requisitos

- R1. Vários temas que aplicam na hora e ficam salvos.
- R2. Opções por cima de qualquer tema: desenhos e animações (que podem
  ser desligados).
- R3. Tema de vidro líquido com desfoque do KWin e intensidade ajustável.
- R4. Os temas são cartas do jogo: o tema que o usuário não tem aparece bloqueado, com cadeado.
- R5. Tema no nível 5 da carta ganha a versão dourada.
- R6. Nada pode pesar com uma sessão aberta.

## Design

- **`temas.py`:**
  - `TEMAS` tem os temas padrao, grafite, claro, oceano, vidro, pixel, hq, espaco, terminal,
    neon, mar (Alto-mar) e manga (Mangá Noir). Cada um define cores, fonte, desenhos (`decor`), frases e CSS próprio.
  - `carregar` e `salvar` usam `~/.config/naview/config.json`.
  - `gerar_css(cfg, dourado, moldura)` monta o CSS.
  - `imagem_reduzida` reduz as imagens de fundo (as dos temas), com cache em `~/.cache/naview` e
    no máximo 1920x1080.
  - Desde 22/10/2026 não há ajuste de cores nem imagem de fundo escolhida pela pessoa: `carregar`
    ignora `ajustes` e `imagem` de configs antigos.
- **`janela_aparencia.py` / `aparencia_qt.py`:** "Opções de aparência" (menu ⋮): intensidade do
  vidro e interruptores (desenhos e animações). Desde 22/10/2026 não tem galeria de temas: o tema
  é escolhido só no jogo (presente > Coleção > Usar), para não haver dois lugares.
  - O estilo da janela é registrado uma vez só. O controle da intensidade aplica 150 ms depois de
    parar de mexer (aplicar refaz o CSS do app todo e grava o config).
- **Vidro:** a propriedade X `_KDE_NET_WM_BLUR_BEHIND_REGION` recebe os retângulos arredondados.
  A força do desfoque é uma configuração global do KDE, que o app não altera.
  Só o KWin desfoca. `temas.TEM_DESFOQUE` olha `XDG_CURRENT_DESKTOP`; fora do KDE, o fundo
  do vidro vai de 0,70 a 0,95 de opacidade (no KDE, de 0,08 a 0,53), e o rótulo da intensidade
  explica isso numa dica.
- **Desempenho:** sem `radial-gradient` e sem sombras com desfoque grande no CSS do GTK. Desenhos
  e animações só na tela inicial.
- **Recursos:**
  - Fontes em `fonts/`, com licença OFL.
  - Arte gerada por `ferramentas/gerar_arte.py`.
  - Ícones Phosphor 2.1.1 (licença MIT) convertidos por `ferramentas/gerar_icones.py`, só para o GTK.
    A página do jogo tem ícones pixel art próprios (`ferramentas/gerar_icones_pixel.py`).

## Situação

- Pronto: R1 a R6.
- Alto-mar (14/10/2026): tema lendário com a marca do NaView. Arte em `arte/mar/`
  (`gerar_mar()`), fonte Fredoka e animação `navegar` (barco balançando). Testado fora da tela
  em 1280x820 e 900x640.
- Mangá Noir (21/10/2026): tema mítico preto e branco, sem cor de destaque, fonte Zen Dots (OFL,
  `fonts/ZenDots-Regular.ttf`). Arte fornecida pelo usuário (22/10/2026), em `arte/manga/`:
  `fundo.jpg` (garota de anime em preto e branco, wallpaper de 22/10/2026, 1920x1080, cobrindo a
  tela inicial; o primeiro fundo, de lírios-aranha, foi trocado) e `icone.png` (retrato em tinta, quadrado arredondado de 512 px). A arte desenhada por
  mim antes foi removida. Uso interno da equipe: a origem das imagens é de terceiros, então elas
  não devem ir para a página pública nem para o instalador sem decisão do usuário (como D18).
  Qt: camada de fundo `{"capa": arquivo}` em `temas_qt.FUNDOS`.
  - **Ícone por tema:** a chave opcional `"icone"` do tema (caminho em `arte/`) troca o ícone da
    janela e da barra de tarefas; `temas.icone_do_tema()` devolve o arquivo, e sem a chave vale o
    `icone.svg` do NaView. GTK: `App.aplicar_icone` (`set_icon_from_file`; para voltar ao padrão
    limpa a lista de ícones, que tem prioridade sobre o nome). Qt: `setWindowIcon` em `aplicar_tema`.
  - Testado fora da tela no GTK (1280x820). A parte Qt (`temas_qt.py`, `app_qt.py`) só passou na
    checagem de sintaxe: o PySide6 não está instalado nesta máquina.
  - **Dock/barra de tarefas (Linux):** GNOME e KDE mostram o ícone do atalho `.desktop`, não o da
    janela, e guardam o ícone pelo nome (reescrever o arquivo não atualiza). Por isso
    `temas.instalar_icone_do_tema()` grava o ícone do tema como `naview-<tema>.svg` (PNG vira um SVG
    que o embute) em `$XDG_DATA_HOME/icons/hicolor/scalable/apps` e troca a linha `Icon=` do
    `naview.desktop` do usuário; sem ícone próprio volta a `Icon=naview`. Só age se o atalho foi
    instalado pelo `instalar.sh`; roda em todo `aplicar_tema`, uma vez por tema. Atualiza os caches
    com `gtk-update-icon-cache`, `update-desktop-database` e `kbuildsycoca6`, se existirem.
  - **Windows:** a janela em execução troca de ícone pelo `setWindowIcon`; o atalho do instalador
    (Inno Setup) continua com o ícone fixo. Sem teste no Windows desta vez.
